import json
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
from app.models.schemas import EscalationPayload

class AgentHub:
    """
    Live Agent Escalation and Context Distribution Hub (VN-5, VN-10).
    Broadcasts real-time escalation events and transcript feeds to connected Agent Desktops.
    """

    def __init__(self):
        self._active_connections: List[WebSocket] = []
        self._pending_escalations: Dict[str, EscalationPayload] = {}
        self._active_assigned: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.append(websocket)
        # Send current queue of pending escalations
        for payload in self._pending_escalations.values():
            await websocket.send_text(json.dumps({
                "type": "NEW_ESCALATION",
                "payload": payload.model_dump()
            }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)

    async def broadcast_escalation(self, payload: EscalationPayload):
        """
        Deliver structured context to all logged-in agent desktops with zero-latency screen-pop.
        """
        self._pending_escalations[payload.session_id] = payload
        message = json.dumps({
            "type": "NEW_ESCALATION",
            "payload": payload.model_dump()
        })
        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[AgentHub] Error broadcasting to agent: {e}")
                self.disconnect(connection)

    async def broadcast_transcript_turn(self, session_id: str, turn: Dict[str, Any]):
        """
        Real-time agent-assist transcription overlay (VN-10).
        """
        message = json.dumps({
            "type": "TRANSCRIPT_STREAM",
            "session_id": session_id,
            "turn": turn
        })
        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                pass

    def accept_escalation(self, session_id: str, agent_id: str) -> Optional[EscalationPayload]:
        if session_id in self._pending_escalations:
            payload = self._pending_escalations.pop(session_id)
            self._active_assigned[session_id] = {
                "payload": payload,
                "agent_id": agent_id
            }
            return payload
        return None

    def get_pending(self) -> List[Dict[str, Any]]:
        return [p.model_dump() for p in self._pending_escalations.values()]

agent_hub = AgentHub()
