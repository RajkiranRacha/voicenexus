import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.engine.orchestrator import DialogueOrchestrator

router = APIRouter()

@router.websocket("/ws/call")
async def call_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = f"call-{uuid.uuid4().hex[:8]}"
    orchestrator: DialogueOrchestrator = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type")

            if msg_type == "START_CALL":
                ani = data.get("ani", "+15550192834")
                orchestrator = DialogueOrchestrator(session_id, ani)
                welcome_resp = await orchestrator.start_session()
                await websocket.send_text(json.dumps(welcome_resp))

            elif msg_type == "CALLER_UTTERANCE":
                if not orchestrator:
                    ani = data.get("ani", "+15550192834")
                    orchestrator = DialogueOrchestrator(session_id, ani)
                
                user_text = data.get("text", "")
                stt_ms = data.get("stt_latency_ms", 140.0)
                resp = await orchestrator.process_caller_utterance(user_text, stt_ms)
                await websocket.send_text(json.dumps(resp))

            elif msg_type == "DTMF_KEY":
                if orchestrator:
                    digit = data.get("digit", "0")
                    resp = await orchestrator.process_caller_utterance(digit, simulated_stt_ms=10.0)
                    await websocket.send_text(json.dumps(resp))

            elif msg_type == "BARGE_IN":
                if orchestrator:
                    orchestrator.handle_barge_in()
                    await websocket.send_text(json.dumps({"type": "BARGE_IN_ACK"}))

            elif msg_type == "END_CALL":
                if orchestrator and orchestrator.fsm.state.value not in ["RESOLVED_CONTAINED", "ESCALATING_TO_AGENT"]:
                    orchestrator._finalize_telemetry(is_escalated=False)
                await websocket.send_text(json.dumps({"type": "CALL_ENDED", "session_id": session_id}))
                break

    except WebSocketDisconnect:
        if orchestrator and orchestrator.fsm.state.value not in ["RESOLVED_CONTAINED", "ESCALATING_TO_AGENT"]:
            orchestrator._finalize_telemetry(is_escalated=False)
