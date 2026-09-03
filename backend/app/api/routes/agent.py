import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.services.agent_hub import agent_hub

router = APIRouter(prefix="/api/agent", tags=["Agent Desktop"])

class AcceptCallRequest(BaseModel):
    session_id: str
    agent_id: str = "agent-sarah-j"

@router.get("/pending")
def get_pending_escalations():
    return agent_hub.get_pending()

@router.post("/accept")
async def accept_escalated_call(req: AcceptCallRequest):
    payload = await agent_hub.accept_escalation(req.session_id, req.agent_id)
    if payload:
        return {"success": True, "payload": payload.model_dump()}
    return {"success": False, "message": "Call no longer available or already accepted."}

@router.websocket("/ws")
async def agent_desktop_websocket(websocket: WebSocket):
    await agent_hub.connect(websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                msg_type = data.get("type")
                session_id = data.get("session_id")
                if msg_type == "ACCEPT_CALL":
                    agent_id = data.get("agent_id", "agent-sarah-j")
                    await agent_hub.accept_escalation(session_id, agent_id)
                elif msg_type in [
                    "RTC_OFFER", "RTC_ANSWER", "RTC_ICE_CANDIDATE",
                    "AGENT_VOICE_STREAM", "AGENT_LIVE_SPEECH", "AGENT_DISCONNECT"
                ]:
                    if session_id:
                        await agent_hub.relay_agent_to_caller(session_id, data)
            except Exception:
                pass
    except WebSocketDisconnect:
        agent_hub.disconnect(websocket)
