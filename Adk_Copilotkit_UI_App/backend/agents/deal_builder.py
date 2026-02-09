"""
Deal Builder agent: shared state pattern. Tool updates deal in session state; UI syncs via useCoAgent.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

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


def on_before_agent(callback_context: CallbackContext) -> None:
    """Initialize deal and proposal state if missing."""
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
    
    if "proposal" not in callback_context.state:
        callback_context.state["proposal"] = {
            "executive_summary": "",
            "solution_overview": "",
            "benefits": [],
            "pricing": "",
            "timeline": "",
            "terms": "",
        }


def before_model_modifier(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Inject deal and proposal state into system instruction."""
    state = callback_context.state
    deal = state.get("deal", {})
    proposal = state.get("proposal", {})
    
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
    
    # Return None to continue with the modified request
    return None


def after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop consecutive tool loops after a final text response, but allow multi-step workflows."""
    if callback_context.agent_name != "deal_builder":
        return None
    
    # Check if there are function calls in the response (agent wants to call tools)
    has_function_calls = False
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                has_function_calls = True
                break
    
    # Only stop if we have a text response AND no pending tool calls
    # This allows the agent to: search -> process results -> update_deal -> respond
    if (
        llm_response.content
        and llm_response.content.parts
        and getattr(llm_response.content, "role", None) == "model"
        and (llm_response.content.parts[0].text or "").strip()
        and not has_function_calls
    ):
        try:
            inv = getattr(callback_context, "_invocation_context", None)
            if inv is not None:
                inv.end_invocation = True
        except Exception:
            pass
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
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
)
