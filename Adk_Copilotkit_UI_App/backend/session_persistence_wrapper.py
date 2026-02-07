"""
Wraps DatabaseSessionService so that after each append_event, in-memory session state
(e.g. updated by tools like update_deal) is persisted to the DB. Without this, tool
updates to session.state are never written, so get_session_state returns stale data
and the frontend never sees agent-updated state (e.g. next_steps from the deal builder).
"""
import time
import logging
from google.adk.events import Event, EventActions
from google.adk.sessions import Session
from google.adk.sessions.database_session_service import DatabaseSessionService

logger = logging.getLogger(__name__)


class SessionStatePersistenceWrapper(DatabaseSessionService):
    """Wraps DatabaseSessionService to persist in-memory session.state after each append_event."""

    async def append_event(self, session: Session, event: Event) -> Event:
        # Check if this is our own synthetic persistence event to avoid recursion
        is_synthetic = (
            getattr(event, "invocation_id", None) == "state_persist"
            and event.author == "user"
            and not event.content
        )
        
        result = await super().append_event(session, event)
        
        if is_synthetic:
            logger.debug("Synthetic state persistence event processed, skipping re-persist")
            return result
        
        # If this event did not already carry state_delta but session.state was updated
        # (e.g. by a tool like update_deal), persist it so get_session_state returns it.
        has_delta = (
            event.actions is not None
            and getattr(event.actions, "state_delta", None)
            and len(getattr(event.actions, "state_delta", {})) > 0
        )
        
        if has_delta:
            logger.debug(f"Event already has state_delta, skipping synthetic persist")
            return result
            
        if not session.state or not isinstance(session.state, dict):
            logger.debug("Session state is None or not dict, skipping persist")
            return result
        
        # Filter out internal AG-UI keys from state_delta (only persist app-specific state)
        state_to_persist = {
            k: v for k, v in session.state.items()
            if not k.startswith("_ag_ui_")
        }
        
        if not state_to_persist:
            logger.debug("No app state to persist (only _ag_ui_ keys), skipping")
            return result
        
        logger.info(f"Persisting tool-updated state for session {session.id}: keys={list(state_to_persist.keys())}")
        
        # Append a synthetic event so DB storage gets session.state (merge into storage).
        try:
            synthetic = Event(
                invocation_id="state_persist",
                timestamp=time.time(),
                author="user",
                actions=EventActions(state_delta=state_to_persist),
            )
            await super().append_event(session, synthetic)
            logger.info(f"✅ State persisted successfully for session {session.id}")
        except Exception as e:
            logger.error(f"Failed to persist state for session {session.id}: {e}", exc_info=True)
        
        return result
