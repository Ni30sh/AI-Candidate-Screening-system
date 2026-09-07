from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.database import SessionLocal
from app.models.interview import InterviewSession
from app.realtime.websocket_manager import manager
from app.services.interview_service import token_matches

router = APIRouter()


@router.websocket("/ws/interviews/{session_id}")
async def interview_socket(websocket: WebSocket, session_id: str, token: str = "") -> None:
    db = SessionLocal()
    session = db.get(InterviewSession, session_id)
    if not session or not token_matches(session, token):
        await websocket.close(code=1008, reason="Valid session token required")
        db.close()
        return
    await manager.connect(session_id, websocket)
    await manager.send(session_id, "connection_established", {"session_id": session_id, "status": session.status})
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            if event in {"question_started", "tts_started", "tts_completed", "listening_started", "listening_stopped", "transcript_received", "answer_evaluating"}:
                await manager.send(session_id, event, {"status": session.status})
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    finally:
        db.close()
