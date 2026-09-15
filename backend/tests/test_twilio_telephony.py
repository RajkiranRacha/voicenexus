import json
import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.telephony_audio import telephony_audio

def test_twilio_voice_webhook_get():
    client = TestClient(app)
    response = client.get("/api/twilio/voice")
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    xml = response.text
    assert "<Response>" in xml
    assert "<Connect>" in xml
    assert "<Stream" in xml
    assert "/ws/twilio" in xml

def test_twilio_voice_webhook_post_with_caller():
    client = TestClient(app)
    response = client.post(
        "/api/twilio/voice",
        data={
            "From": "+919876543210",
            "To": "+18005550199",
            "CallSid": "CA1234567890abcdef"
        }
    )
    assert response.status_code == 200
    xml = response.text
    assert "+919876543210" in xml
    assert "CA1234567890abcdef" in xml

def test_telephony_audio_mulaw_to_wav():
    # 160 bytes of silence in mulaw
    mulaw = b"\xff" * 160
    wav = telephony_audio.mulaw_to_wav(mulaw)
    assert len(wav) > 160
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"

def test_telephony_audio_chunking():
    mulaw = b"\x00" * 480
    chunks = telephony_audio.chunk_mulaw(mulaw, chunk_size=160)
    assert len(chunks) == 3
    assert all(len(c) == 160 for c in chunks)

def test_telephony_audio_rms():
    silence = b"\xff" * 160
    rms_silence = telephony_audio.calculate_rms(silence)
    assert rms_silence < 250

@pytest.mark.asyncio
async def test_twilio_websocket_handshake_and_start():
    client = TestClient(app)
    with client.websocket_connect("/ws/twilio") as ws:
        # 1. Connected event
        ws.send_text(json.dumps({"event": "connected", "protocol": "Call", "version": "1.0.0"}))

        # 2. Start event
        ws.send_text(json.dumps({
            "event": "start",
            "sequenceNumber": "1",
            "start": {
                "streamSid": "MZ_TEST_STREAM_123",
                "callSid": "CA_TEST_CALL_456",
                "customParameters": {
                    "caller": "+919876543210"
                }
            },
            "streamSid": "MZ_TEST_STREAM_123"
        }))

        # Wait for first media frame of greeting
        first_frame = json.loads(ws.receive_text())
        assert first_frame["event"] == "media"
        assert first_frame["streamSid"] == "MZ_TEST_STREAM_123"
        assert len(first_frame["media"]["payload"]) > 0

        # 3. Test instant barge-in by sending speech audio
        loud_audio = b"\x00" * 320
        b64_loud = base64.b64encode(loud_audio).decode("utf-8")
        ws.send_text(json.dumps({
            "event": "media",
            "streamSid": "MZ_TEST_STREAM_123",
            "media": {
                "payload": b64_loud
            }
        }))

        # 4. Stop event
        ws.send_text(json.dumps({
            "event": "stop",
            "streamSid": "MZ_TEST_STREAM_123"
        }))
