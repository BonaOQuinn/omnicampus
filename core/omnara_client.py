"""
Omnara SDK wrapper — handles status logging and human-in-the-loop (HITL).
Falls back to terminal I/O if the SDK is unavailable or unconfigured.
"""
import os
from dotenv import load_dotenv

load_dotenv()

_SDK_AVAILABLE = False
_omnara_client = None

try:
    from omnara import OmnaraClient  # type: ignore
    _api_key = os.getenv("OMNARA_API_KEY", "")
    if _api_key:
        _omnara_client = OmnaraClient(api_key=_api_key)
        _SDK_AVAILABLE = True
except ImportError:
    pass


def send_status(
    agent_name: str,
    message: str,
    instance_id: str,
    requires_input: bool = False,
) -> str | None:
    """
    Stream a status update to the Omnara dashboard.
    If requires_input=True, pauses for supervisor response (HITL).
    Returns the supervisor reply, or None for fire-and-forget.
    """
    if _SDK_AVAILABLE and _omnara_client:
        try:
            result = _omnara_client.send_message(
                agent_type="claude-code",
                content=f"[{agent_name}] {message}",
                agent_instance_id=instance_id,
                requires_user_input=requires_input,
            )
            if requires_input:
                msgs = result.queued_user_messages
                return msgs[0] if msgs else ""
            return None
        except Exception as exc:
            print(f"[Omnara] send_status failed: {exc}")

    # Fallback — local logging / terminal HITL
    tag = "HITL" if requires_input else "STATUS"
    print(f"[{tag}][{agent_name}][{instance_id}] {message}")

    if requires_input:
        try:
            return input(f"  >> Supervisor reply for {agent_name}: ")
        except EOFError:
            return "No supervisor input available."

    return None


def log_event(agent_name: str, event: str, instance_id: str) -> None:
    """Fire-and-forget event log — never blocks."""
    send_status(agent_name, event, instance_id, requires_input=False)
