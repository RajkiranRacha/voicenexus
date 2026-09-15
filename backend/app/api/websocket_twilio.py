import json
import uuid
import base64
import asyncio
import time
from typing import Optional
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect

from app.config import config
from app.engine.orchestrator import DialogueOrchestrator
from app.services.agent_hub import agent_hub
from app.services.stt import stt_service
from app.services.tts import tts_service
from app.services.telephony_audio import telephony_audio

router = APIRouter()


import urllib.parse

@router.api_route("/api/twilio/voice", methods=["GET", "POST"])
async def twilio_voice_webhook(request: Request):
    """
    Twilio Voice Incoming Call Webhook (VN-TWILIO).
    Receives incoming cellular/PSTN phone calls, captures caller ANI,
    and returns TwiML instructions directing bidirectional audio into /ws/twilio.
    """
    caller_ani = config.DEFAULT_DEMO_ANI
    call_sid = f"CA{uuid.uuid4().hex[:16]}"

    # 1. Check query parameters
    if "From" in request.query_params:
        caller_ani = request.query_params["From"]
    if "CallSid" in request.query_params:
        call_sid = request.query_params["CallSid"]

    # 2. Check urlencoded body for standard Twilio POST
    if request.method == "POST":
        try:
            raw_body = await request.body()
            parsed = urllib.parse.parse_qs(raw_body.decode("utf-8", errors="ignore"))
            if "From" in parsed and parsed["From"]:
                caller_ani = parsed["From"][0]
            if "CallSid" in parsed and parsed["CallSid"]:
                call_sid = parsed["CallSid"][0]
        except Exception as e:
            print(f"[TwilioWebhook] Parse body error: {e}")

    # Extract host header for constructing WebSocket URL
    host = request.headers.get("host", f"localhost:{config.PORT}")
    ws_protocol = "wss" if request.url.scheme == "https" or "render.com" in host or "ngrok" in host else "ws"
    ws_url = f"{ws_protocol}://{host}/ws/twilio"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="caller" value="{caller_ani}" />
            <Parameter name="callSid" value="{call_sid}" />
        </Stream>
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


class TwilioCallerAdapter:
    """
    Adapter enabling the Live Agent Web Portal to communicate bi-directionally
    with a phone caller connected via Twilio Media Streams.
    """
    def __init__(self, handler: "TwilioMediaStreamHandler"):
        self.handler = handler

    async def send_text(self, text: str):
        try:
            data = json.loads(text)
            msg_type = data.get("type")
            if msg_type == "AGENT_CONNECTED":
                agent_name = data.get("agent_name", "Sarah J.")
                announcement = f"You are now connected with agent {agent_name}. Go ahead, how can we help?"
                mp3 = await tts_service.synthesize_to_bytes(announcement)
                mulaw = telephony_audio.mp3_to_mulaw(mp3)
                self.handler.active_playback_task = asyncio.create_task(self.handler.stream_ai_audio(mulaw))
            elif msg_type == "AGENT_LIVE_SPEECH":
                agent_msg = data.get("text", "").strip()
                if agent_msg:
                    mp3 = await tts_service.synthesize_to_bytes(agent_msg)
                    mulaw = telephony_audio.mp3_to_mulaw(mp3)
                    self.handler.active_playback_task = asyncio.create_task(self.handler.stream_ai_audio(mulaw))
            elif msg_type in ("AGENT_DISCONNECT", "CALL_ENDED"):
                bye = "The agent has ended the session. Thank you for calling VoiceNexus. Goodbye!"
                mp3 = await tts_service.synthesize_to_bytes(bye)
                mulaw = telephony_audio.mp3_to_mulaw(mp3)
                await self.handler.stream_ai_audio(mulaw)
        except Exception as e:
            logger.error(f"[TwilioAdapter] Error processing agent event: {e}")


class TwilioMediaStreamHandler:
    """
    Full-Duplex Twilio Media Stream Session Coordinator.
    Manages continuous 8kHz μ-law audio exchange, voice activity detection (VAD),
    end-of-utterance pause detection, instant phone-level barge-in, and agent escalation.
    """

    def __init__(self, websocket: WebSocket):
        self.ws = websocket
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.session_id: Optional[str] = None
        self.ani: str = config.DEFAULT_DEMO_ANI
        self.orchestrator: Optional[DialogueOrchestrator] = None
        self.adapter = TwilioCallerAdapter(self)

        self.audio_buffer = bytearray()
        self.is_user_speaking = False
        self.silence_frames = 0
        self.ai_is_playing = False
        self.active_playback_task: Optional[asyncio.Task] = None

    async def send_twiml_media(self, mulaw_chunk: bytes):
        """Sends a single 20ms μ-law audio frame to Twilio."""
        if not self.stream_sid:
            return
        payload = base64.b64encode(mulaw_chunk).decode("utf-8")
        msg = {
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {
                "payload": payload
            }
        }
        await self.ws.send_text(json.dumps(msg))

    async def stream_ai_audio(self, mulaw_audio: bytes):
        """Streams synthesized speech to the caller's mobile phone in 20ms chunks."""
        self.ai_is_playing = True
        chunks = telephony_audio.chunk_mulaw(mulaw_audio, chunk_size=160)
        try:
            for chunk in chunks:
                if not self.ai_is_playing:
                    break
                await self.send_twiml_media(chunk)
                # 20ms pacing between frames
                await asyncio.sleep(0.019)
        except asyncio.CancelledError:
            pass
        finally:
            self.ai_is_playing = False

    async def interrupt_playback(self):
        """Instant Barge-In: Flushes audio buffer on caller's mobile phone."""
        if self.ai_is_playing:
            self.ai_is_playing = False
            if self.active_playback_task and not self.active_playback_task.done():
                self.active_playback_task.cancel()
            if self.stream_sid:
                clear_msg = {
                    "event": "clear",
                    "streamSid": self.stream_sid
                }
                await self.ws.send_text(json.dumps(clear_msg))
            if self.orchestrator:
                self.orchestrator.handle_barge_in()

    async def handle_start(self, data: dict):
        start_data = data.get("start", {})
        self.stream_sid = start_data.get("streamSid")
        self.call_sid = start_data.get("callSid")
        custom_params = start_data.get("customParameters", {})
        self.ani = custom_params.get("caller", self.ani)

        self.session_id = f"twilio-{self.call_sid[:10] if self.call_sid else uuid.uuid4().hex[:8]}"
        self.orchestrator = DialogueOrchestrator(self.session_id, self.ani)
        agent_hub.register_caller(self.session_id, self.adapter)

        welcome_resp = await self.orchestrator.start_session()
        greeting_text = welcome_resp["turn"]["text"]

        # Synthesize greeting and stream to phone
        voice = welcome_resp.get("language")
        mp3_bytes = await tts_service.synthesize_to_bytes(greeting_text)
        mulaw_bytes = telephony_audio.mp3_to_mulaw(mp3_bytes)
        self.active_playback_task = asyncio.create_task(self.stream_ai_audio(mulaw_bytes))

    async def handle_media(self, data: dict):
        raw_payload = data.get("media", {}).get("payload", "")
        if not raw_payload:
            return

        chunk = base64.b64decode(raw_payload)
        rms = telephony_audio.calculate_rms(chunk)

        # 1. Instant Barge-In detection
        if self.ai_is_playing and rms > 550:
            await self.interrupt_playback()

        # 2. Voice Activity & End-of-Utterance Detection
        if rms > 450:
            self.is_user_speaking = True
            self.silence_frames = 0
            self.audio_buffer.extend(chunk)
        else:
            if self.is_user_speaking:
                self.silence_frames += 1
                self.audio_buffer.extend(chunk)
                # 30 frames * 20ms = ~600ms pause (human finished speaking)
                if self.silence_frames >= 30:
                    self.is_user_speaking = False
                    self.silence_frames = 0
                    await self._process_utterance_turn()

    async def _process_utterance_turn(self):
        if len(self.audio_buffer) < 4000:  # Less than 0.5s audio
            self.audio_buffer.clear()
            return

        mulaw_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()

        # Convert to WAV for Whisper transcription
        wav_data = telephony_audio.mulaw_to_wav(mulaw_data)
        stt_result = await stt_service.transcribe(wav_data)
        text = stt_result.get("text", "").strip()

        if not text or not self.orchestrator:
            return

        # Process with LLM Agent
        stt_ms = stt_result.get("stt_ms", 120.0)
        turn_resp = await self.orchestrator.process_caller_utterance(text, simulated_stt_ms=stt_ms)
        reply_text = turn_resp["turn"]["text"]

        # Synthesize response & stream to phone
        mp3_bytes = await tts_service.synthesize_to_bytes(reply_text)
        mulaw_reply = telephony_audio.mp3_to_mulaw(mp3_bytes)
        self.active_playback_task = asyncio.create_task(self.stream_ai_audio(mulaw_reply))

    async def handle_stop(self):
        if self.session_id:
            agent_hub.unregister_caller(self.session_id)
            if self.orchestrator:
                self.orchestrator._finalize_telemetry(is_escalated=False)

            # Automated Post-Call SMS Dispatch
            if self.ani:
                try:
                    from app.services.sms_service import sms_service
                    call_ref = self.call_sid[:8] if self.call_sid else "NXF"
                    sms_body = (
                        f"NexusFiber Care: Thank you for calling! (Ref #{call_ref}). "
                        f"Your request has been logged. For digital self-service & eSIM guides, "
                        f"visit: https://nexusfiber.telco/myaccount"
                    )
                    asyncio.create_task(sms_service.send_sms(self.ani, sms_body))
                except Exception as e:
                    logger.error(f"[Twilio] Post-call SMS dispatch error: {e}")


@router.websocket("/ws/twilio")
async def twilio_websocket_endpoint(websocket: WebSocket):
    """
    Twilio Media Streams Full-Duplex Audio Gateway.
    Receives raw 8kHz μ-law frames, coordinates VAD, and streams AI speech back to phone.
    """
    await websocket.accept()
    handler = TwilioMediaStreamHandler(websocket)

    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            event = data.get("event")

            if event == "connected":
                pass
            elif event == "start":
                await handler.handle_start(data)
            elif event == "media":
                await handler.handle_media(data)
            elif event == "stop":
                await handler.handle_stop()
                break
    except WebSocketDisconnect:
        await handler.handle_stop()
    except Exception as e:
        print(f"[TwilioMediaStream] Error: {e}")
        await handler.handle_stop()
