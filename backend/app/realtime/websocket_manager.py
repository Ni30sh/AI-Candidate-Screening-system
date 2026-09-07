import logging
from collections import defaultdict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        self.connections[session_id].discard(websocket)
        if not self.connections[session_id]:
            self.connections.pop(session_id, None)

    async def send(self, session_id: str, event: str, payload: dict) -> None:
        message = {"event": event, "payload": payload}
        for websocket in tuple(self.connections.get(session_id, ())):
            try:
                await websocket.send_json(message)
            except Exception:
                logger.info("WebSocket disconnected during event delivery", extra={"session_id": session_id})
                self.disconnect(session_id, websocket)


manager = WebSocketManager()
