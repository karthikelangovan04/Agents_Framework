"""
DatabaseSessionService for Postgres (adk_db_new). Shared by all agents.

Workaround: ADK passes timezone-aware datetimes to Postgres TIMESTAMP WITHOUT TIME ZONE,
which causes asyncpg "can't subtract offset-naive and offset-aware datetimes".
We replace the ADK session module's datetime with a shim whose now() returns naive UTC.
"""
from datetime import datetime, timezone

from google.adk.sessions import DatabaseSessionService
import google.adk.sessions.database_session_service as _dss
from config import DATABASE_URL

# Shim so ADK's datetime.now(timezone.utc) returns naive UTC (datetime type is immutable in 3.13)
def _naive_utc_now(tz=None):
    t = datetime.now(tz)
    return t.replace(tzinfo=None) if t.tzinfo else t

class _DateTimeShim(type(datetime)):
    now = staticmethod(_naive_utc_now)

_dss.datetime = _DateTimeShim(
    "datetime",
    (datetime,),
    {k: getattr(datetime, k) for k in dir(datetime) if not k.startswith("_") and k != "now"},
)
_dss.datetime.now = staticmethod(_naive_utc_now)

# Wrap so tool-updated state (e.g. deal_builder's update_deal) is persisted and sent to the UI
from session_persistence_wrapper import SessionStatePersistenceWrapper
session_service = SessionStatePersistenceWrapper(db_url=DATABASE_URL)
