import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.engine.orchestrator import DialogueOrchestrator
from app.services.agent_hub import agent_hub
from app.config import config

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
                ani = data.get("ani", config.DEFAULT_DEMO_ANI)
                orchestrator = DialogueOrchestrator(session_id, ani)
                agent_hub.register_caller(session_id, websocket)
                welcome_resp = await orchestrator.start_session()
                await websocket.send_text(json.dumps(welcome_resp))

            elif msg_type == "CALLER_UTTERANCE":
                if not orchestrator:
                    ani = data.get("ani", config.DEFAULT_DEMO_ANI)
                    orchestrator = DialogueOrchestrator(session_id, ani)
                    agent_hub.register_caller(session_id, websocket)
                
                user_text = data.get("text", "")
                stt_ms = data.get("stt_latency_ms", 140.0)
                resp = await orchestrator.process_caller_utterance(user_text, stt_ms)
                await websocket.send_text(json.dumps(resp))

            elif msg_type in ["RTC_OFFER", "RTC_ANSWER", "RTC_ICE_CANDIDATE", "CALLER_VOICE_STREAM", "CALLER_LIVE_SPEECH"]:
                # Relay WebRTC signaling and audio data directly to live agent
                data["session_id"] = session_id
                await agent_hub.relay_caller_to_agent(session_id, data)

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
                # A call ending without ever reaching a contained resolution or an
                # agent escalation is an abandoned call (PRD business-impact
                # metric "Abandonment rate"), not a silent success.
                if orchestrator and orchestrator.fsm.state.value not in ["RESOLVED_CONTAINED", "ESCALATING_TO_AGENT"]:
                    orchestrator._finalize_telemetry(is_escalated=False, is_abandoned=True)
                await agent_hub.relay_caller_to_agent(session_id, {"type": "CALL_ENDED", "session_id": session_id})
                agent_hub.unregister_caller(session_id)
                await websocket.send_text(json.dumps({"type": "CALL_ENDED", "session_id": session_id}))
                break

    except WebSocketDisconnect:
        if orchestrator and orchestrator.fsm.state.value not in ["RESOLVED_CONTAINED", "ESCALATING_TO_AGENT"]:
            orchestrator._finalize_telemetry(is_escalated=False, is_abandoned=True)
        await agent_hub.relay_caller_to_agent(session_id, {"type": "CALL_ENDED", "session_id": session_id})
        agent_hub.unregister_caller(session_id)
    finally:
        agent_hub.unregister_caller(session_id)
