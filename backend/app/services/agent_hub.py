import json
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
from app.models.schemas import EscalationPayload

class AgentHub:
    """
    Live Agent Escalation and Context Distribution Hub (VN-5, VN-10).
    Broadcasts real-time escalation events, WebRTC voice signaling, and transcript feeds.
    """

    def __init__(self):
        self._active_connections: List[WebSocket] = []
        self._caller_websockets: Dict[str, WebSocket] = {}
        self._pending_escalations: Dict[str, EscalationPayload] = {}
        self._active_assigned: Dict[str, Dict[str, Any]] = {}

    def register_caller(self, session_id: str, websocket: WebSocket):
        self._caller_websockets[session_id] = websocket

    def unregister_caller(self, session_id: str):
        self._caller_websockets.pop(session_id, None)
        self._pending_escalations.pop(session_id, None)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.append(websocket)
        # Send current queue of pending escalations
        for payload in self._pending_escalations.values():
            await websocket.send_text(json.dumps({
                "type": "NEW_ESCALATION",
                "payload": payload.model_dump()
            }))
        # Also inform of already accepted sessions
        for session_id, assign in self._active_assigned.items():
            await websocket.send_text(json.dumps({
                "type": "CALL_ACCEPTED",
                "session_id": session_id,
                "agent_id": assign.get("agent_id")
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

    async def broadcast_transcript_turn(self, session_id: str, turn: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """
        Real-time agent-assist transcription overlay (VN-10).
        """
        message = json.dumps({
            "type": "TRANSCRIPT_STREAM",
            "session_id": session_id,
            "turn": turn,
            "metadata": metadata or {}
        })
        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def accept_escalation(self, session_id: str, agent_id: str, agent_name: str = "Sarah J.") -> Optional[EscalationPayload]:
        payload = None
        if session_id in self._pending_escalations:
            payload = self._pending_escalations.pop(session_id)
            self._active_assigned[session_id] = {
                "payload": payload,
                "agent_id": agent_id,
                "agent_name": agent_name
            }
        elif session_id in self._active_assigned:
            payload = self._active_assigned[session_id]["payload"]

        # 1. Notify the caller that an agent has answered & connected
        caller_ws = self._caller_websockets.get(session_id)
        if caller_ws:
            try:
                await caller_ws.send_text(json.dumps({
                    "type": "AGENT_CONNECTED",
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "agent_name": agent_name
                }))
            except Exception as e:
                print(f"[AgentHub] Error notifying caller of agent connect: {e}")

        # 2. Broadcast acceptance to all agent desktops
        accept_msg = json.dumps({
            "type": "CALL_ACCEPTED",
            "session_id": session_id,
            "agent_id": agent_id,
            "agent_name": agent_name
        })
        for conn in list(self._active_connections):
            try:
                await conn.send_text(accept_msg)
            except Exception:
                pass

        return payload

    async def relay_caller_to_agent(self, session_id: str, message_dict: Dict[str, Any]):
        msg = json.dumps(message_dict)
        for conn in list(self._active_connections):
            try:
                await conn.send_text(msg)
            except Exception:
                pass

    async def relay_agent_to_caller(self, session_id: str, message_dict: Dict[str, Any]):
        caller_ws = self._caller_websockets.get(session_id)
        if caller_ws:
            try:
                await caller_ws.send_text(json.dumps(message_dict))
            except Exception as e:
                print(f"[AgentHub] Error relaying to caller {session_id}: {e}")

    def get_pending(self) -> List[Dict[str, Any]]:
        return [p.model_dump() for p in self._pending_escalations.values()]

agent_hub = AgentHub()
