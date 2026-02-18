"""
Deal Builder agent: shared state pattern. Tool updates deal in session state; UI syncs via useCoAgent.
Enhanced with all callbacks and detailed state flow logging.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import local

from google.adk.agents import Agent, LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import AgentTool, FunctionTool, ToolContext, google_search
from google.genai import types

try:
    from ag_ui_adk import AGUIToolset
except ImportError:
    AGUIToolset = None

from config import GEMINI_MODEL

# ---------------------------------------------------------------------------
# File Logging Setup
# ---------------------------------------------------------------------------

# Thread-local storage for per-invocation log files
_thread_local = local()

# Output directory for callback logs
CALLBACK_LOG_DIR = Path(__file__).parent.parent / "callback_logs"
CALLBACK_LOG_DIR.mkdir(exist_ok=True)


class TeeOutput:
    """Write to both console and file."""
    
    def __init__(self, file_handle, stream):
        self.terminal = stream
        self.log_file = file_handle
    
    def write(self, message):
        self.terminal.write(message)
        if self.log_file:
            self.log_file.write(message)
            self.log_file.flush()
    
    def flush(self):
        self.terminal.flush()
        if self.log_file:
            self.log_file.flush()


# Global storage for log files (keyed by session_id + invocation_id)
# This persists across async boundaries
_log_file_cache: Dict[str, Any] = {}


def get_invocation_key(callback_context: CallbackContext) -> str:
    """Get a unique key for this invocation (session_id + invocation_id)."""
    try:
        session_id = callback_context.session.id[:16] if callback_context.session else "unknown"
        
        # Try to get invocation_id
        invocation_id = None
        if hasattr(callback_context, "_invocation_context"):
            invocation_context = callback_context._invocation_context
            if hasattr(invocation_context, "invocation_id"):
                invocation_id = invocation_context.invocation_id
        
        if invocation_id:
            return f"{session_id}_{invocation_id[:16]}"
        else:
            # Fallback: use session_id only (less ideal, but works)
            return f"{session_id}_no_inv_id"
    except Exception:
        return "unknown"


def get_invocation_log_file(callback_context: CallbackContext) -> Optional[Path]:
    """Get or create log file for current invocation."""
    try:
        invocation_key = get_invocation_key(callback_context)
        
        # Check if we already have a log file for this invocation
        if invocation_key in _log_file_cache:
            # Return existing file path (we'll need to track this)
            # For now, create a consistent filename
            filename = f"deal_builder_callback_{invocation_key}.txt"
            return CALLBACK_LOG_DIR / filename
        
        # Create new filename (no timestamp to avoid duplicates)
        filename = f"deal_builder_callback_{invocation_key}.txt"
        log_file = CALLBACK_LOG_DIR / filename
        
        return log_file
    except Exception as e:
        print(f"⚠️  Error creating log file: {e}")
        return None


def setup_invocation_logging(callback_context: CallbackContext) -> Optional[TeeOutput]:
    """Setup logging for this invocation. Returns TeeOutput if successful."""
    try:
        invocation_key = get_invocation_key(callback_context)
        
        # Check if we already have a log file for this invocation
        if invocation_key in _log_file_cache:
            return _log_file_cache[invocation_key]
        
        log_file_path = get_invocation_log_file(callback_context)
        if not log_file_path:
            return None
        
        # Get invocation_id for header
        invocation_id = None
        if hasattr(callback_context, "_invocation_context"):
            invocation_context = callback_context._invocation_context
            if hasattr(invocation_context, "invocation_id"):
                invocation_id = invocation_context.invocation_id
        
        # Check if file already exists (append mode) or create new
        file_exists = log_file_path.exists()
        log_file_handle = open(log_file_path, "a" if file_exists else "w", encoding="utf-8")
        tee = TeeOutput(log_file_handle, sys.stdout)
        
        # Store in global cache
        _log_file_cache[invocation_key] = tee
        
        # Write header only if file is new
        if not file_exists:
            tee.write("=" * 80 + "\n")
            tee.write("DEAL BUILDER AGENT - CALLBACK LOG\n")
            tee.write("=" * 80 + "\n")
            tee.write(f"Log file: {log_file_path}\n")
            tee.write(f"Timestamp: {datetime.now().isoformat()}\n")
            tee.write(f"Agent: {getattr(callback_context, 'agent_name', 'unknown')}\n")
            tee.write(f"Session ID: {callback_context.session.id if callback_context.session else 'unknown'}\n")
            if invocation_id:
                tee.write(f"Invocation ID: {invocation_id}\n")
            tee.write(f"Invocation Key: {invocation_key}\n")
            tee.write("=" * 80 + "\n\n")
        else:
            # Add separator for continuation
            tee.write("\n" + "=" * 80 + "\n")
            tee.write(f"CONTINUED - {datetime.now().isoformat()}\n")
            tee.write("=" * 80 + "\n\n")
        
        return tee
    except Exception as e:
        print(f"⚠️  Error setting up logging: {e}")
        return None


def get_log_writer(callback_context: CallbackContext):
    """Get the log writer (TeeOutput) for current invocation, or None."""
    try:
        invocation_key = get_invocation_key(callback_context)
        
        # Check global cache first
        if invocation_key in _log_file_cache:
            return _log_file_cache[invocation_key]
        
        # Try to setup if not exists
        return setup_invocation_logging(callback_context)
    except Exception:
        return None


def log_print(callback_context: CallbackContext, *args, **kwargs):
    """Print that writes to both console and log file."""
    tee = get_log_writer(callback_context)
    if tee:
        # Write to both console and file
        message = ' '.join(str(arg) for arg in args)
        if kwargs.get('end', '\n') != '\n':
            message += kwargs.get('end', '')
        else:
            message += '\n'
        tee.write(message)
    else:
        # Fallback to regular print
        print(*args, **kwargs)

# ---------------------------------------------------------------------------
# Formatting helpers for callback output (from callback_exploration.py)
# ---------------------------------------------------------------------------

def _safe_repr(obj: Any, max_len: int = 2000) -> str:
    """Raw representation - safe for complex objects."""
    try:
        s = repr(obj)
        return s[:max_len] + "..." if len(s) > max_len else s
    except Exception as e:
        return f"<repr error: {e}>"


def _format_for_display(obj: Any) -> str:
    """Formatted display - human-readable."""
    if obj is None:
        return "None"
    if isinstance(obj, dict):
        try:
            return json.dumps(obj, indent=2, default=str)[:1500]
        except Exception:
            return _safe_repr(obj, 500)
    if hasattr(obj, "model_dump"):
        try:
            return json.dumps(obj.model_dump(), indent=2, default=str)[:1500]
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            d = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            return json.dumps(d, indent=2, default=str)[:1500]
        except Exception:
            pass
    return _safe_repr(obj, 500)


def _format_callback_context(ctx: CallbackContext) -> Dict[str, Any]:
    """Extract key fields from CallbackContext for display."""
    try:
        state = ctx.state
        state_keys = []
        state_preview = {}
        
        # Safely extract state keys and values
        if state:
            try:
                if hasattr(state, "keys"):
                    state_keys = list(state.keys())
                    # Access values safely - State object supports dict-like access
                    for k in state_keys:
                        try:
                            v = state[k]
                            if isinstance(v, dict):
                                # Show summary for nested dicts
                                state_preview[k] = {
                                    "keys": list(v.keys()) if isinstance(v, dict) else None,
                                    "preview": str(v)[:200] if not isinstance(v, dict) else None
                                }
                            else:
                                state_preview[k] = str(v)[:200] if v is not None else None
                        except (KeyError, TypeError) as e:
                            state_preview[k] = f"<access error: {e}>"
            except Exception as e:
                state_preview["_error"] = f"Error reading state: {e}"
        
        return {
            "agent_name": getattr(ctx, "agent_name", "?"),
            "session_id": ctx.session.id if ctx.session else "?",
            "state_keys": state_keys,
            "state_preview": state_preview,
        }
    except Exception as e:
        return {"error": str(e)}


def _format_llm_request(req: LlmRequest) -> Dict[str, Any]:
    """Extract key fields from LlmRequest."""
    try:
        out = {}
        if hasattr(req, "contents") and req.contents:
            out["contents_count"] = len(req.contents)
            out["contents_preview"] = []
            for c in req.contents[:3]:
                role = getattr(c, "role", "?")
                parts = getattr(c, "parts", []) or []
                texts = []
                for p in parts[:2]:
                    if hasattr(p, "text") and p.text:
                        texts.append(p.text[:80])
                    elif hasattr(p, "function_call"):
                        texts.append(f"<function_call: {getattr(p.function_call, 'name', '?')}>")
                    elif hasattr(p, "function_response"):
                        texts.append("<function_response>")
                out["contents_preview"].append({"role": role, "texts": texts or ["(no text)"]})
        if hasattr(req, "config") and req.config:
            cfg = req.config
            if hasattr(cfg, "system_instruction") and cfg.system_instruction:
                si = cfg.system_instruction
                if isinstance(si, str):
                    txt = si
                elif hasattr(si, "parts") and si.parts:
                    txt = getattr(si.parts[0], "text", "") or str(si)
                else:
                    txt = str(si)
                out["system_instruction_preview"] = (txt or "")[:300]
        return out
    except Exception as e:
        return {"error": str(e)}


def _format_llm_response(resp: LlmResponse) -> Dict[str, Any]:
    """Extract key fields from LlmResponse."""
    try:
        out = {}
        if hasattr(resp, "content") and resp.content:
            c = resp.content
            role = getattr(c, "role", "?")
            parts = getattr(c, "parts", []) or []
            texts = []
            for p in parts[:3]:
                if hasattr(p, "text") and p.text:
                    texts.append(p.text[:150])
                elif hasattr(p, "function_call"):
                    texts.append(f"<function_call: {getattr(p.function_call, 'name', '?')}>")
            out["content_role"] = role
            out["content_texts"] = texts or ["(function_call or other)"]
        if hasattr(resp, "usage_metadata") and resp.usage_metadata:
            um = resp.usage_metadata
            out["usage"] = {
                "prompt_tokens": getattr(um, "prompt_token_count", None),
                "output_tokens": getattr(um, "candidates_token_count", None),
                "total_tokens": getattr(um, "total_token_count", None),
            }
        return out
    except Exception as e:
        return {"error": str(e)}


def update_deal(
    tool_context: ToolContext,
    customer_name: str = "",
    segment: str = "",
    products: List[str] = None,
    estimated_value: str = "",
    stage: str = "",
    next_steps: List[str] = None,
    changes: str = "",
) -> Dict[str, str]:
    """
    Update the current deal. Call this for any deal-related suggestion or change.

    Args:
        customer_name: Customer or account name.
        segment: Segment (e.g. Enterprise, SMB).
        products: List of product names.
        estimated_value: Estimated deal value (e.g. "$50k").
        stage: Deal stage (e.g. Discovery, Proposal, Negotiation, Closed).
        next_steps: Recommended next steps.
        changes: Brief description of what was changed (optional).
    """
    if products is None:
        products = []
    if next_steps is None:
        next_steps = []

    try:
        # Build the update object
        deal = {
            "customer_name": customer_name or "",
            "segment": segment or "",
            "products": products,
            "estimated_value": estimated_value or "",
            "stage": stage or "",
            "next_steps": next_steps,
            "changes": changes or "",
        }
        
        # Get current deal from state and merge updates
        current = dict(tool_context.state.get("deal") or {})
        for k, v in deal.items():
            if k in ("products", "next_steps"):
                if v:
                    current[k] = list(v)
            elif v is not None and v != "":
                current[k] = v
        
        # Update state
        tool_context.state["deal"] = current
        print(f"✅ update_deal: updated state['deal']: {current}")
        return {"status": "success", "message": "Deal updated successfully"}
    except Exception as e:
        print(f"❌ update_deal exception: {e}")
        return {"status": "error", "message": str(e)}


def generate_proposal(
    tool_context: ToolContext,
    executive_summary: str = "",
    solution_overview: str = "",
    benefits: List[str] = None,
    pricing: str = "",
    timeline: str = "",
    terms: str = "",
) -> Dict[str, Any]:
    """
    Generate or update a proposal document for the current deal.

    Args:
        executive_summary: Brief executive summary of the proposal.
        solution_overview: Detailed description of the proposed solution.
        benefits: List of key benefits and value propositions.
        pricing: Pricing structure and costs.
        timeline: Project timeline and milestones.
        terms: Terms and conditions.
    
    Returns:
        Status message indicating success or failure.
    """
    if benefits is None:
        benefits = []
    
    try:
        # Get current deal info
        deal = tool_context.state.get("deal", {})
        
        # Build proposal document
        proposal = {
            "executive_summary": executive_summary or "",
            "solution_overview": solution_overview or "",
            "benefits": benefits,
            "pricing": pricing or "",
            "timeline": timeline or "",
            "terms": terms or "",
            "generated_at": "",  # Could add timestamp
        }
        
        # Get current proposal from state and merge updates
        current_proposal = dict(tool_context.state.get("proposal") or {})
        for k, v in proposal.items():
            if k == "benefits":
                if v:
                    current_proposal[k] = list(v)
            elif v is not None and v != "":
                current_proposal[k] = v
        
        # Store proposal in state
        tool_context.state["proposal"] = current_proposal
        
        # Also update deal stage to Proposal if not already
        if deal.get("stage") != "Proposal":
            deal["stage"] = "Proposal"
            tool_context.state["deal"] = deal
        
        print(f"✅ generate_proposal: created/updated proposal")
        return {
            "status": "success",
            "message": "Proposal generated successfully",
            "proposal": current_proposal
        }
    except Exception as e:
        print(f"❌ generate_proposal exception: {e}")
        return {"status": "error", "message": str(e)}


def on_before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    """Initialize deal and proposal state if missing."""
    # Setup logging for this invocation
    setup_invocation_logging(callback_context)
    
    sep = "=" * 80
    log_print(callback_context, f"\n{sep}")
    log_print(callback_context, "🔵 CALLBACK: before_agent_callback [DEAL BUILDER]")
    log_print(callback_context, f"{sep}")
    
    # Show current state before initialization
    log_print(callback_context, "\n[STATE BEFORE INIT]")
    log_print(callback_context, json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    
    # Initialize state
    if "deal" not in callback_context.state:
        callback_context.state["deal"] = {
            "customer_name": "",
            "segment": "",
            "products": [],
            "estimated_value": "",
            "stage": "Discovery",
            "next_steps": [],
            "changes": "",
        }
        log_print(callback_context, "\n✅ Initialized 'deal' state")
    
    if "proposal" not in callback_context.state:
        callback_context.state["proposal"] = {
            "executive_summary": "",
            "solution_overview": "",
            "benefits": [],
            "pricing": "",
            "timeline": "",
            "terms": "",
        }
        log_print(callback_context, "\n✅ Initialized 'proposal' state")
    
    # Show state after initialization
    log_print(callback_context, "\n[STATE AFTER INIT]")
    log_print(callback_context, json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    
    # Show deal and proposal details if they exist
    if "deal" in callback_context.state:
        deal = callback_context.state["deal"]
        log_print(callback_context, "\n[DEAL STATE DETAILS]")
        log_print(callback_context, json.dumps(deal, indent=2, default=str))
    
    if "proposal" in callback_context.state:
        proposal = callback_context.state["proposal"]
        log_print(callback_context, "\n[PROPOSAL STATE DETAILS]")
        log_print(callback_context, json.dumps(proposal, indent=2, default=str))
    
    log_print(callback_context, f"{sep}\n")
    return None


def on_after_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    """After agent: runs after agent's main logic completes."""
    sep = "=" * 80
    log_print(callback_context, f"\n{sep}")
    log_print(callback_context, "🟢 CALLBACK: after_agent_callback [DEAL BUILDER]")
    log_print(callback_context, f"{sep}")
    log_print(callback_context, "\n[FORMATTED] callback_context:")
    log_print(callback_context, json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    
    # Show final state
    if "deal" in callback_context.state:
        deal = callback_context.state["deal"]
        log_print(callback_context, "\n[FINAL DEAL STATE]")
        log_print(callback_context, json.dumps(deal, indent=2, default=str))
    
    if "proposal" in callback_context.state:
        proposal = callback_context.state["proposal"]
        log_print(callback_context, "\n[FINAL PROPOSAL STATE]")
        log_print(callback_context, json.dumps(proposal, indent=2, default=str))
    
    log_print(callback_context, f"{sep}\n")
    log_print(callback_context, "\n" + "=" * 80)
    log_print(callback_context, "INVOCATION COMPLETE")
    log_print(callback_context, "=" * 80 + "\n")
    return None


def before_model_modifier(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Inject deal and proposal state into system instruction."""
    sep = "=" * 80
    log_print(callback_context, f"\n{sep}")
    log_print(callback_context, "🟡 CALLBACK: before_model_callback [DEAL BUILDER]")
    log_print(callback_context, f"{sep}")
    
    log_print(callback_context, "\n[FORMATTED] callback_context:")
    log_print(callback_context, json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    
    log_print(callback_context, "\n[FORMATTED] llm_request (before modification):")
    log_print(callback_context, json.dumps(_format_llm_request(llm_request), indent=2, default=str))
    
    state = callback_context.state
    deal = state.get("deal", {})
    proposal = state.get("proposal", {})
    
    log_print(callback_context, "\n[CURRENT STATE SUMMARY]")
    log_print(callback_context, f"  Deal: {deal.get('customer_name', 'Not set')} | Stage: {deal.get('stage', 'Not set')}")
    log_print(callback_context, f"  Products: {len(deal.get('products', []))} items")
    log_print(callback_context, f"  Proposal: {'Has content' if any(proposal.values()) else 'Empty'}")
    
    # Build a concise deal summary for context
    deal_context = f"""
Current Deal:
- Customer: {deal.get('customer_name', 'Not set')}
- Segment: {deal.get('segment', 'Not set')}
- Products: {', '.join(deal.get('products', [])) if deal.get('products') else 'None'}
- Value: {deal.get('estimated_value', 'Not set')}
- Stage: {deal.get('stage', 'Not set')}
- Next Steps: {', '.join(deal.get('next_steps', [])) if deal.get('next_steps') else 'None'}

Current Proposal Status:
- Has Proposal: {'Yes' if any(proposal.values()) else 'No'}
- Executive Summary: {'Present' if proposal.get('executive_summary') else 'Not set'}
- Solution Overview: {'Present' if proposal.get('solution_overview') else 'Not set'}
- Benefits: {len(proposal.get('benefits', []))} items
- Pricing: {'Present' if proposal.get('pricing') else 'Not set'}
- Timeline: {'Present' if proposal.get('timeline') else 'Not set'}
"""
    
    log_print(callback_context, "\n[INJECTING DEAL CONTEXT INTO PROMPT]")
    log_print(callback_context, deal_context[:300] + "..." if len(deal_context) > 300 else deal_context)
    
    # Add context to system instruction
    if llm_request.config.system_instruction:
        orig_inst = llm_request.config.system_instruction
        if isinstance(orig_inst, str):
            llm_request.config.system_instruction = deal_context + "\n" + orig_inst
        elif isinstance(orig_inst, types.Content):
            if orig_inst.parts and orig_inst.parts[0].text:
                orig_inst.parts[0].text = deal_context + "\n" + orig_inst.parts[0].text
    else:
        llm_request.config.system_instruction = deal_context
    
    log_print(callback_context, "\n[FORMATTED] llm_request (after modification):")
    log_print(callback_context, json.dumps(_format_llm_request(llm_request), indent=2, default=str))
    
    log_print(callback_context, f"{sep}\n")
    return None


def after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop consecutive tool loops after a final text response, but allow multi-step workflows."""
    sep = "=" * 80
    log_print(callback_context, f"\n{sep}")
    log_print(callback_context, "🟠 CALLBACK: after_model_callback [DEAL BUILDER]")
    log_print(callback_context, f"{sep}")
    
    log_print(callback_context, "\n[FORMATTED] callback_context:")
    log_print(callback_context, json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    
    log_print(callback_context, "\n[FORMATTED] llm_response:")
    log_print(callback_context, json.dumps(_format_llm_response(llm_response), indent=2, default=str))
    
    if callback_context.agent_name != "deal_builder":
        log_print(callback_context, "\n⚠️  Agent name mismatch, skipping end_invocation logic")
        log_print(callback_context, f"{sep}\n")
        return None
    
    # Check if there are function calls in the response (agent wants to call tools)
    has_function_calls = False
    function_call_names = []
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                has_function_calls = True
                func_name = getattr(part.function_call, 'name', 'unknown')
                function_call_names.append(func_name)
    
    log_print(callback_context, f"\n[FUNCTION CALL ANALYSIS]")
    log_print(callback_context, f"  Has function calls: {has_function_calls}")
    if function_call_names:
        log_print(callback_context, f"  Function names: {', '.join(function_call_names)}")
    
    # Only stop if we have a text response AND no pending tool calls
    # This allows the agent to: search -> process results -> update_deal -> respond
    should_end = False
    if (
        llm_response.content
        and llm_response.content.parts
        and getattr(llm_response.content, "role", None) == "model"
        and (llm_response.content.parts[0].text or "").strip()
        and not has_function_calls
    ):
        should_end = True
        try:
            inv = getattr(callback_context, "_invocation_context", None)
            if inv is not None:
                inv.end_invocation = True
                log_print(callback_context, "\n✅ Setting end_invocation = True (final text response, no tool calls)")
        except Exception as e:
            log_print(callback_context, f"\n⚠️  Error setting end_invocation: {e}")
    else:
        log_print(callback_context, "\n⏭️  Continuing (has function calls or no final text)")
    
    # Show current state
    if "deal" in callback_context.state:
        deal = callback_context.state["deal"]
        log_print(callback_context, "\n[CURRENT DEAL STATE]")
        log_print(callback_context, json.dumps(deal, indent=2, default=str))
    
    log_print(callback_context, f"{sep}\n")
    return None


def before_tool_callback(
    tool: Any, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict[str, Any]]:
    """Before tool: runs before tool execution."""
    # Get callback context from tool_context
    callback_context = None
    if hasattr(tool_context, "_invocation_context"):
        inv_context = tool_context._invocation_context
        if hasattr(inv_context, "session"):
            # Create a minimal callback context for logging
            class MinimalCallbackContext:
                def __init__(self, session, state):
                    self.session = session
                    self.state = state
                    self.agent_name = "deal_builder"
            callback_context = MinimalCallbackContext(inv_context.session, tool_context.state)
    
    sep = "=" * 80
    log_print(callback_context, f"\n{sep}")
    log_print(callback_context, "🟣 CALLBACK: before_tool_callback [DEAL BUILDER]")
    log_print(callback_context, f"{sep}")
    
    tool_name = getattr(tool, "name", str(tool))
    tool_type = type(tool).__name__
    
    log_print(callback_context, f"\n[TOOL INFO]")
    log_print(callback_context, f"  Tool name: {tool_name}")
    log_print(callback_context, f"  Tool type: {tool_type}")
    
    # Detect AGUIToolset/ClientProxyTool
    is_client_tool = False
    if "ClientProxy" in tool_type or "AGUI" in tool_type:
        is_client_tool = True
        log_print(callback_context, f"  ⚠️  CLIENT-SIDE TOOL DETECTED (AGUIToolset)")
        log_print(callback_context, f"     This tool will execute on the frontend")
        log_print(callback_context, f"     Events will be sent via SSE to CopilotKit")
    
    log_print(callback_context, "\n[TOOL ARGUMENTS]")
    log_print(callback_context, json.dumps(args, indent=2, default=str))
    
    log_print(callback_context, "\n[TOOL CONTEXT STATE]")
    st = tool_context.state
    state_keys = list(st.keys()) if st and hasattr(st, "keys") else []
    log_print(callback_context, f"  State keys: {state_keys}")
    
    # Show deal and proposal state
    if "deal" in st:
        log_print(callback_context, "\n[DEAL STATE BEFORE TOOL]")
        log_print(callback_context, json.dumps(st["deal"], indent=2, default=str))
    
    if "proposal" in st:
        log_print(callback_context, "\n[PROPOSAL STATE BEFORE TOOL]")
        log_print(callback_context, json.dumps(st["proposal"], indent=2, default=str))
    
    if is_client_tool:
        log_print(callback_context, "\n[CLIENT TOOL FLOW]")
        log_print(callback_context, "  → Tool call will be sent to frontend via SSE")
        log_print(callback_context, "  → Frontend will execute via useCopilotAction")
        log_print(callback_context, "  → Result will be sent back to agent")
    
    log_print(callback_context, f"{sep}\n")
    return None


def after_tool_callback(
    tool: Any, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """After tool: runs after tool execution."""
    # Get callback context from tool_context
    callback_context = None
    if hasattr(tool_context, "_invocation_context"):
        inv_context = tool_context._invocation_context
        if hasattr(inv_context, "session"):
            # Create a minimal callback context for logging
            class MinimalCallbackContext:
                def __init__(self, session, state):
                    self.session = session
                    self.state = state
                    self.agent_name = "deal_builder"
            callback_context = MinimalCallbackContext(inv_context.session, tool_context.state)
    
    sep = "=" * 80
    log_print(callback_context, f"\n{sep}")
    log_print(callback_context, "🔴 CALLBACK: after_tool_callback [DEAL BUILDER]")
    log_print(callback_context, f"{sep}")
    
    tool_name = getattr(tool, "name", str(tool))
    tool_type = type(tool).__name__
    
    log_print(callback_context, f"\n[TOOL INFO]")
    log_print(callback_context, f"  Tool name: {tool_name}")
    log_print(callback_context, f"  Tool type: {tool_type}")
    
    # Detect AGUIToolset/ClientProxyTool
    is_client_tool = False
    if "ClientProxy" in tool_type or "AGUI" in tool_type:
        is_client_tool = True
        log_print(callback_context, f"  ⚠️  CLIENT-SIDE TOOL (AGUIToolset)")
        log_print(callback_context, f"     Tool executed on frontend, result received")
    
    log_print(callback_context, "\n[TOOL RESPONSE]")
    log_print(callback_context, json.dumps(tool_response, indent=2, default=str))
    
    log_print(callback_context, "\n[TOOL CONTEXT STATE AFTER EXECUTION]")
    st = tool_context.state
    state_keys = list(st.keys()) if st and hasattr(st, "keys") else []
    log_print(callback_context, f"  State keys: {state_keys}")
    
    # Show deal and proposal state after tool execution
    if "deal" in st:
        log_print(callback_context, "\n[DEAL STATE AFTER TOOL]")
        log_print(callback_context, json.dumps(st["deal"], indent=2, default=str))
    
    if "proposal" in st:
        log_print(callback_context, "\n[PROPOSAL STATE AFTER TOOL]")
        log_print(callback_context, json.dumps(st["proposal"], indent=2, default=str))
    
    # Detect state changes
    if tool_name in ["update_deal", "generate_proposal"]:
        log_print(callback_context, "\n[STATE CHANGE DETECTED]")
        log_print(callback_context, f"  Tool '{tool_name}' modified state")
        if tool_name == "update_deal" and "deal" in st:
            log_print(callback_context, f"  Deal stage: {st['deal'].get('stage', 'N/A')}")
            log_print(callback_context, f"  Products count: {len(st['deal'].get('products', []))}")
        elif tool_name == "generate_proposal" and "proposal" in st:
            log_print(callback_context, f"  Proposal has content: {any(st['proposal'].values())}")
    
    if is_client_tool:
        log_print(callback_context, "\n[CLIENT TOOL COMPLETION]")
        log_print(callback_context, "  ✓ Frontend tool execution completed")
        log_print(callback_context, "  ✓ Result received from frontend")
        log_print(callback_context, "  → Agent continues with tool response")
    
    log_print(callback_context, f"{sep}\n")
    return None


# Create a specialized Google Search agent with a lighter model
# Using gemini-2.5-flash-lite - optimized for cost-efficiency and high throughput
# This reduces rate limiting issues and costs for simple search operations
search_agent = Agent(
    model="gemini-2.5-flash-lite",  # Lighter model for search operations
    name="SearchAgent",
    instruction=(
        "You're a specialist in Google Search and product identification. "
        "When asked to search for products, services, or information:\n"
        "1. Use Google Search to find comprehensive, up-to-date information\n"
        "2. Extract ALL relevant product names and services mentioned in the search results\n"
        "3. Include main products AND related sub-products, tools, and components\n"
        "4. Provide detailed summaries with clear product lists\n\n"
        "IMPORTANT: Be thorough in identifying products. If search results mention:\n"
        "- 'Vertex AI' - also note sub-products like 'Vertex AI Agent Builder', 'Vertex AI Conversation', 'Vertex AI Search'\n"
        "- Platform names - include specific tools and features within those platforms\n"
        "- Service ecosystems - capture the full ecosystem of related products\n\n"
        "Format your response to clearly list ALL products found, organized by category if applicable."
    ),
    tools=[google_search],
)

# Create AgentTool wrapper for the search agent
# AgentTool automatically derives name and description from the agent
search_agent_tool = AgentTool(agent=search_agent)

# Build tools list for the main deal builder agent
_tools: List[Any] = [update_deal, generate_proposal, search_agent_tool]
if AGUIToolset is not None:
    _tools.insert(0, AGUIToolset())

deal_builder_agent = LlmAgent(
    name="deal_builder",
    model=GEMINI_MODEL,
    instruction=(
        "You help users build and improve deals (opportunities) and generate professional proposals. "
        "You have access to three key tools:\n"
        "1. update_deal: REQUIRED - use this to update the deal with customer info, products, value, stage, or next steps.\n"
        "2. generate_proposal: Use this to create or update a formal proposal document with executive summary, solution overview, benefits, pricing, timeline, and terms.\n"
        "3. SearchAgent tool: Optional - use this to search Google for products, companies, or information when needed.\n\n"
        "IMPORTANT WORKFLOWS:\n\n"
        "For deal updates with products:\n"
        "- When a user asks to add products or find product recommendations, FIRST use the SearchAgent to get comprehensive information.\n"
        "- When you receive search results, be THOROUGH in extracting product names:\n"
        "  * Extract ALL product and service names mentioned\n"
        "  * Include main products AND sub-products (e.g., 'Vertex AI' AND 'Vertex AI Agent Builder', 'Vertex AI Conversation', etc.)\n"
        "  * Capture related tools, platforms, and components mentioned in the search results\n"
        "  * Don't be conservative - include the full ecosystem of products found\n"
        "- After extracting products, call update_deal with the COMPLETE list of products found.\n"
        "- If search fails or is unavailable, use your knowledge or the user's direct input.\n"
        "- ALWAYS call update_deal to actually update the deal state.\n\n"
        "PRODUCT EXTRACTION EXAMPLES:\n"
        "If SearchAgent returns info about 'Google Cloud Gen AI products' mentioning:\n"
        "- Vertex AI, Vertex AI Agent Builder, Vertex AI Conversation, Vertex AI Search, Agent Development Kit, Vertex AI Agent Engine, Google AI Studio, Dialogflow\n"
        "Then update_deal should include ALL of these products, not just 2-3.\n\n"
        "For proposal generation:\n"
        "- When a user asks for a proposal, review the current deal information (customer, products, value, etc.).\n"
        "- Call generate_proposal with comprehensive sections: executive summary, solution overview, benefits, pricing, timeline, and terms.\n"
        "- Base the proposal content on the deal information, focusing on the customer's needs and the proposed solution.\n"
        "- The proposal should be professional, persuasive, and tailored to the specific customer and segment.\n"
        "- Automatically update the deal stage to 'Proposal' when generating a proposal.\n\n"
        "Example workflows:\n"
        "1. Product search: SearchAgent → extract ALL products → update_deal with complete list → confirm\n"
        "2. Direct update: use knowledge → update_deal → confirm\n"
        "3. Proposal generation: review deal → generate_proposal with all sections → confirm\n\n"
        "The most important rules:\n"
        "- Be COMPREHENSIVE when extracting products from search results (include ALL relevant products, not just top 3)\n"
        "- ALWAYS call update_deal when the user wants to modify the deal\n"
        "- Never let search failures prevent updates\n"
        "- Be thorough but practical."
    ),
    tools=_tools,
    before_agent_callback=on_before_agent,
    after_agent_callback=on_after_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
