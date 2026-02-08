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


def before_model_modifier(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Inject deal state and enable Google Search grounding."""
    state = callback_context.state
    deal = state.get("deal", {})
    
    # Build a concise deal summary for context
    deal_context = f"""
Current Deal:
- Customer: {deal.get('customer_name', 'Not set')}
- Segment: {deal.get('segment', 'Not set')}
- Products: {', '.join(deal.get('products', [])) if deal.get('products') else 'None'}
- Value: {deal.get('estimated_value', 'Not set')}
- Stage: {deal.get('stage', 'Not set')}
- Next Steps: {', '.join(deal.get('next_steps', [])) if deal.get('next_steps') else 'None'}
"""
    
    # Enable Google Search grounding
    grounding_config = types.GoogleSearchRetrieval()
    
    # Modify the request in-place
    llm_request.config = llm_request.config or types.GenerateContentConfig()
    llm_request.config.tools = llm_request.config.tools or []
    
    # Add grounding tool if not already present
    if not any(hasattr(tool, 'google_search_retrieval') for tool in llm_request.config.tools):
        llm_request.config.tools.append(types.Tool(google_search_retrieval=grounding_config))
    
    # Add deal context to system instruction
    if llm_request.config.system_instruction:
        orig_inst = llm_request.config.system_instruction
        if isinstance(orig_inst, str):
            llm_request.config.system_instruction = deal_context + "\n" + orig_inst
        elif isinstance(orig_inst, types.Content):
            if orig_inst.parts and orig_inst.parts[0].text:
                orig_inst.parts[0].text = deal_context + "\n" + orig_inst.parts[0].text
    else:
        llm_request.config.system_instruction = deal_context
    
    # Return None to continue with the modified request
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
        "You have access to Google Search grounding to search the web for real products and company information. "
        "When a user mentions a company or asks for product suggestions, search for relevant information. "
        "For example, search for 'Google Cloud products for enterprise' or 'Microsoft Azure services'. "
        "Extract product names from the search results and use update_deal to add them to the recommended products list. "
        "Always use the update_deal tool when suggesting or applying changes to customer, segment, products, value, stage, or next steps. "
        "After a successful update, briefly summarize what you changed. Be concise and practical."
    ),
    tools=_tools,
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
)
