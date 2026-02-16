"""
Agent for adk web with memory (InMemoryMemoryService).

How memory works (library behavior):

1) save_session_to_memory (after_agent_callback)
   - Runs after each agent turn.
   - Calls memory_service.add_session_to_memory(session).
   - Stores RAW SESSION EVENTS: the full list of events (user messages, model
     messages, tool calls, etc.) for this session, keyed by app_name/user_id
     and session_id. No "fact extraction" – it's the raw conversation.

2) load_memory (tool)
   - Agent calls it with a query string (e.g. "I'm", "Karthik", "name").
   - Under the hood: tool_context.search_memory(query) → MemoryService
     does keyword match (InMemory: query words vs. words in stored event text).
   - Returns RAW CONVERSATION SNIPPETS from OTHER SESSIONS: a list of
     MemoryEntry items, each with content = one past event (e.g. user said
     "Hi I'm Karthik"), plus author/timestamp. No separate "facts" – it's
     the actual message content from previous sessions.

3) Who answers?
   - The TOOL loads raw past messages and returns them as the tool result.
   - The AGENT (LLM) receives that tool result in the conversation, then
     interprets it and answers (e.g. "Your name is Karthik"). So: tool
     fetches raw conversations from other sessions → model reads them and
     replies. No intermediate "fact" store – the model does the reasoning.

4) Token usage
   - Yes: loading raw previous messages means the tool result can be large.
   - Each MemoryEntry is full event content (full message text). That entire
     tool result is sent to the model as part of the conversation, so it
     consumes input tokens. InMemoryMemoryService returns ALL matching events
     (no limit), so many sessions → many matches → large tool result → high
     token use. For production, consider a memory service that limits or
     summarizes (e.g. VertexAiRagMemoryService with similarity_top_k).

You do NOT need to import InMemoryMemoryService here; adk web injects it.
"""
from google.adk.agents.llm_agent import Agent
from google.adk.tools import load_memory
from google.adk.tools import preload_memory


async def save_session_to_memory(*, callback_context):
    """After each turn, save this session to memory so future sessions can recall it."""
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        pass  # No memory service (e.g. in tests)
    return None


# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}


root_agent = Agent(
    model='gemini-3-flash-preview',
    name='root_agent',
    description="Tells the current time in cities and can recall information from memory (adk web uses InMemoryMemoryService).",
    instruction="""You are a helpful assistant that tells the current time in cities and can recall information from past conversations (long-term memory).

- Use get_current_time for the time in a city.
- When the user asks about themselves (e.g. "what is my name?", "do you remember me?") use load_memory to search. Memory search is keyword-based: the query must contain words that appear in past messages. For name recall, try queries like: "Karthik", "I'm", "introduced", "call me", "name", "my name" (try one; if memories are empty, try another). Then answer from the returned memories.
- For other "do you remember X?" questions, use load_memory with words that would appear in the kind of thing they said (e.g. "Chennai", "time", "preference").
- Memory is saved automatically after each turn, so you can remember the same user across sessions.""",
    tools=[get_current_time, load_memory, preload_memory],
    after_agent_callback=save_session_to_memory,
)