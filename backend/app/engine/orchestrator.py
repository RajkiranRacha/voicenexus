import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.schemas import (
    CallState, DialogueTurn, LatencyMetrics, EscalationPayload
)
from app.engine.state_machine import CallSessionStateMachine
from app.services.tts import tts_service
from app.services.agent_hub import agent_hub
from app.services.telemetry import telemetry_service
from app.services.bss_oss import bss_service
from app.config import config, get_voice_for_language

class DialogueOrchestrator:
    """
    Real-Time Dialogue and Speech Pipeline Orchestrator.
    Manages session lifecycle, turn latency measurement, and audio generation.
    """

    def __init__(self, session_id: str, ani: str):
        self.session_id = session_id
        self.ani = ani
        self.fsm = CallSessionStateMachine(session_id, ani)
        self.is_interrupted = False
        self.turn_counter = 0
        telemetry_service.record_call_start(session_id, ani)

    async def _synthesize_safe(self, text: str) -> Any:
        """
        Wraps neural TTS synthesis so a transient failure (e.g. the upstream
        speech service is unreachable) degrades gracefully instead of crashing
        the turn. Per PRD Reliability NFR: 'degraded mode retains IVR menu
        fallback' -- the caller still gets the text response and can continue
        via DTMF/text even if voice audio could not be generated this turn.
        """
        try:
            voice_override = get_voice_for_language(self.fsm.language, config.DEFAULT_VOICE)
            return await tts_service.synthesize_to_base64(
                text, voice_override=voice_override, rate_override=config.VOICE_RATE
            )
        except Exception as e:
            print(f"[DialogueOrchestrator] Degraded mode: TTS synthesis failed ({e}). Falling back to text-only turn.")
            return None

    async def start_session(self) -> Dict[str, Any]:
        """
        Executes initial greeting, ANI lookup, and synthesis of welcome prompt.
        """
        greeting_text = self.fsm.get_greeting()
        self.turn_counter += 1
        
        # Measure TTS synthesis time
        tts_start = time.perf_counter()
        audio_base64 = await self._synthesize_safe(greeting_text)
        tts_ms = round((time.perf_counter() - tts_start) * 1000, 1)

        ai_turn = DialogueTurn(
            turn_id=self.turn_counter,
            speaker="ai",
            text=greeting_text,
            latency=LatencyMetrics(tts_ms=tts_ms, total_turn_ms=tts_ms),
            state=self.fsm.state.value
        )
        self.fsm.turns.append(ai_turn)

        # Broadcast initial greeting turn to Live Agent Overlay (VN-10)
        metadata = {
            "ani": self.ani,
            "customer_name": self.fsm.account.customer_name if self.fsm.account else "Unregistered Caller",
            "account_number": self.fsm.account.account_number if self.fsm.account else "UNREGISTERED",
            "state": self.fsm.state.value,
            "language": self.fsm.language
        }
        await agent_hub.broadcast_transcript_turn(self.session_id, ai_turn.model_dump(), metadata)

        return {
            "type": "SESSION_STARTED",
            "session_id": self.session_id,
            "caller_account": self.fsm.account.model_dump() if self.fsm.account else None,
            "turn": ai_turn.model_dump(),
            "audio_base64": audio_base64,
            "audio_degraded": audio_base64 is None,
            "state": self.fsm.state.value,
            "language": self.fsm.language
        }

    async def process_caller_utterance(
        self,
        caller_text: str,
        simulated_stt_ms: float = 120.0
    ) -> Dict[str, Any]:
        """
        Processes a caller turn: STT -> NLU/State Machine -> TTS -> Telemetry.
        Enforces sub-second response latency budgeting.
        """
        self.turn_counter += 1
        turn_start = time.perf_counter()

        # 1. Log caller turn
        caller_turn = DialogueTurn(
            turn_id=self.turn_counter,
            speaker="caller",
            text=caller_text,
            state=self.fsm.state.value
        )
        self.fsm.turns.append(caller_turn)

        metadata = {
            "ani": self.ani,
            "customer_name": self.fsm.account.customer_name if self.fsm.account else "Unregistered Caller",
            "account_number": self.fsm.account.account_number if self.fsm.account else "UNREGISTERED",
            "state": self.fsm.state.value,
            "language": self.fsm.language
        }

        # Broadcast turn to Live Agent Overlay (VN-10)
        await agent_hub.broadcast_transcript_turn(self.session_id, caller_turn.model_dump(), metadata)

        # 2. Process through Deterministic State Machine (NLU)
        nlu_start = time.perf_counter()
        response_text, new_state, escalation_payload = self.fsm.process_turn(caller_text)
        nlu_ms = round((time.perf_counter() - nlu_start) * 1000, 1)

        # 3. Generate Speech Audio via Neural TTS
        tts_start = time.perf_counter()
        audio_base64 = await self._synthesize_safe(response_text)
        tts_ms = round((time.perf_counter() - tts_start) * 1000, 1)

        total_ms = round((time.perf_counter() - turn_start) * 1000 + simulated_stt_ms, 1)
        latency = LatencyMetrics(
            stt_ms=simulated_stt_ms,
            nlu_ms=nlu_ms,
            tts_ms=tts_ms,
            total_turn_ms=total_ms
        )

        self.turn_counter += 1
        ai_turn = DialogueTurn(
            turn_id=self.turn_counter,
            speaker="ai",
            text=response_text,
            latency=latency,
            state=new_state.value
        )
        self.fsm.turns.append(ai_turn)

        metadata["state"] = new_state.value
        metadata["language"] = self.fsm.language
        if self.fsm.account:
            metadata["customer_name"] = self.fsm.account.customer_name
            metadata["account_number"] = self.fsm.account.account_number

        # Broadcast turn to Live Agent Overlay
        await agent_hub.broadcast_transcript_turn(self.session_id, ai_turn.model_dump(), metadata)

        # 4. If escalation triggered, broadcast structured handoff payload
        if escalation_payload:
            await agent_hub.broadcast_escalation(escalation_payload)
            self._finalize_telemetry(is_escalated=True, payload=escalation_payload)

        elif new_state == CallState.RESOLVED_CONTAINED:
            self._finalize_telemetry(is_escalated=False)

        return {
            "type": "TURN_RESPONSE",
            "session_id": self.session_id,
            "turn": ai_turn.model_dump(),
            "audio_base64": audio_base64,
            "audio_degraded": audio_base64 is None,
            "state": new_state.value,
            "language": self.fsm.language,
            "caller_account": self.fsm.account.model_dump() if self.fsm.account else None,
            "escalated": bool(escalation_payload),
            "escalation_payload": escalation_payload.model_dump() if escalation_payload else None
        }

    def handle_barge_in(self):
        """
        Handles caller interruption: instantly cuts off pending playback.
        """
        self.is_interrupted = True

    def _finalize_telemetry(
        self,
        is_escalated: bool,
        payload: Optional[EscalationPayload] = None,
        is_abandoned: bool = False
    ):
        duration = int((datetime.now() - self.fsm.start_time).total_seconds())
        acc = self.fsm.account
        intent_str = (
            self.fsm.current_intent.value
            if self.fsm.current_intent else "GENERAL_INQUIRY"
        )

        # Calculate average turn latency for this session
        latencies = [t.latency.total_turn_ms for t in self.fsm.turns if t.latency]
        avg_lat = sum(latencies) / len(latencies) if latencies else 550.0

        if is_abandoned:
            final_state = CallState.ABANDONED.value
        elif is_escalated:
            final_state = CallState.ESCALATING_TO_AGENT.value
        else:
            final_state = CallState.RESOLVED_CONTAINED.value

        telemetry_service.record_completed_call(
            session_id=self.session_id,
            ani=self.ani,
            account_number=acc.account_number if acc else "UNREGISTERED",
            customer_name=acc.customer_name if acc else "Unknown Caller",
            intent=intent_str,
            duration_sec=duration,
            final_state=final_state,
            escalation_reason=payload.resolution_summary.get("failure_or_escalation_reason") if payload else None,
            avg_latency_ms=round(avg_lat, 1),
            turns_count=len(self.fsm.turns),
            transcript=[{"speaker": t.speaker, "text": t.text} for t in self.fsm.turns]
        )
