import time
import uuid
from threading import Lock
from config import SESSION_TTL_MINUTES, MAX_MESSAGES_PER_SESSION

_sessions: dict = {}
_lock = Lock()


def _now() -> float:
    return time.time()


def _ttl_seconds() -> float:
    return SESSION_TTL_MINUTES * 60


def create_session() -> str:
    session_id = str(uuid.uuid4())
    with _lock:
        _sessions[session_id] = {
            "messages": [],
            "last_active": _now(),
        }
    return session_id


def get_history(session_id: str) -> list:
    """Return conversation history for a session, creating it if absent."""
    with _lock:
        _purge_expired()
        if session_id not in _sessions:
            _sessions[session_id] = {
                "messages": [],
                "last_active": _now(),
            }
        _sessions[session_id]["last_active"] = _now()
        return list(_sessions[session_id]["messages"])


def get_active_language(session_id: str) -> str:
    with _lock:
        _purge_expired()
        if session_id not in _sessions:
            _sessions[session_id] = {
                "messages": [],
                "last_active": _now(),
                "active_language": "hinglish",
            }
        _sessions[session_id]["last_active"] = _now()
        return _sessions[session_id].get("active_language", "hinglish")


def set_active_language(session_id: str, language: str) -> None:
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = {
                "messages": [],
                "last_active": _now(),
            }
        _sessions[session_id]["active_language"] = language
        _sessions[session_id]["last_active"] = _now()


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message and apply the sliding-window cap."""
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = {
                "messages": [],
                "last_active": _now(),
            }
        msgs = _sessions[session_id]["messages"]
        msgs.append({"role": role, "content": content})
        # Sliding window — keep the most recent MAX_MESSAGES_PER_SESSION
        if len(msgs) > MAX_MESSAGES_PER_SESSION:
            _sessions[session_id]["messages"] = msgs[-MAX_MESSAGES_PER_SESSION:]
        _sessions[session_id]["last_active"] = _now()


def delete_session(session_id: str) -> bool:
    with _lock:
        if session_id in _sessions:
            del _sessions[session_id]
            return True
        return False


def _purge_expired() -> None:
    """Remove sessions inactive longer than TTL. Must be called under lock."""
    cutoff = _now() - _ttl_seconds()
    expired = [sid for sid, data in _sessions.items() if data["last_active"] < cutoff]
    for sid in expired:
        del _sessions[sid]
