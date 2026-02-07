"""
Deal Builder agent: shared state pattern. Tool updates deal in session state; UI syncs via useCoAgent.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types

try:
    from ag_ui_adk import AGUIToolset
except ImportError:
    AGUIToolset = None

from config import GEMINI_MODEL


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


def on_before_agent(callback_context: CallbackContext) -> None:
    """Initialize deal state if missing."""
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


def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inject current deal state into system instruction."""
    if callback_context.agent_name != "deal_builder":
        return None
    deal_json = "No deal yet"
    if "deal" in callback_context.state and callback_context.state["deal"]:
        try:
            deal_json = json.dumps(callback_context.state["deal"], indent=2)
        except Exception:
            deal_json = str(callback_context.state["deal"])
    prefix = f"""You are a helpful deal/opportunity assistant. Current deal state:
{deal_json}
Use the update_deal tool to suggest or apply changes. After updating, give a brief summary."""
    orig = llm_request.config.system_instruction or types.Content(role="system", parts=[])
    if not isinstance(orig, types.Content):
        orig = types.Content(role="system", parts=[types.Part(text=str(orig))])
    if not orig.parts:
        orig.parts.append(types.Part(text=""))
    orig.parts[0].text = prefix + (orig.parts[0].text or "")
    llm_request.config.system_instruction = orig
    return None


def after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop consecutive tool loops after a final text response."""
    if callback_context.agent_name != "deal_builder":
        return None
    if (
        llm_response.content
        and llm_response.content.parts
        and getattr(llm_response.content, "role", None) == "model"
        and (llm_response.content.parts[0].text or "").strip()
    ):
        try:
            inv = getattr(callback_context, "_invocation_context", None)
            if inv is not None:
                inv.end_invocation = True
        except Exception:
            pass
    return None


_tools: List[Any] = [update_deal]
if AGUIToolset is not None:
    _tools.insert(0, AGUIToolset())

deal_builder_agent = LlmAgent(
    name="deal_builder",
    model=GEMINI_MODEL,
    instruction=(
        "You help users build and improve deals (opportunities). "
        "Always use the update_deal tool when suggesting or applying changes to customer, segment, products, value, stage, or next steps. "
        "After a successful update, briefly summarize what you changed. Be concise and practical."
    ),
    tools=_tools,
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
)
