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
def accept_escalated_call(req: AcceptCallRequest):
    payload = agent_hub.accept_escalation(req.session_id, req.agent_id)
    if payload:
        return {"success": True, "payload": payload.model_dump()}
    return {"success": False, "message": "Call no longer available or already accepted."}

@router.websocket("/ws")
async def agent_desktop_websocket(websocket: WebSocket):
    await agent_hub.connect(websocket)
    try:
        while True:
            # Keep socket alive and receive any agent desktop ack signals
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        agent_hub.disconnect(websocket)
