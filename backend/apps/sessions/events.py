from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

EVENT_NAMES = {
    "signal_created": "signal.created",
    "cluster_updated": "cluster.updated",
    "response_created": "response.created",
    "feedback_updated": "feedback.updated",
    "session_status_changed": "session.status_changed",
}


def session_group_name(session_id: int) -> str:
    return f"creator_session_{session_id}"


def publish_session_event(session_id: int, event_type: str, data: dict) -> None:
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(session_group_name(session_id), {"type": event_type, "payload": {"type": EVENT_NAMES[event_type], **data}})
