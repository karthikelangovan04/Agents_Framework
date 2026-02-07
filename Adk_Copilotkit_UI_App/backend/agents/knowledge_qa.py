"""
Knowledge Q&A agent: persistent chat with Postgres sessions. No shared-state tool.
"""
from config import GEMINI_MODEL
from google.adk.agents import LlmAgent

knowledge_qa_agent = LlmAgent(
    name="knowledge_qa",
    model=GEMINI_MODEL,
    instruction=(
        "You are a helpful knowledge assistant. Answer questions about products, pricing, and playbooks. "
        "Remember context from earlier in the conversation. Be concise but thorough."
    ),
    tools=[],
)
