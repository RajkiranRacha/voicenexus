import io
import json
import base64
import pytest
import numpy as np
import av
from fastapi.testclient import TestClient
from app.main import app
from app.services.stt import stt_service


def _make_webm_opus_clip(seconds: float = 1.0) -> bytes:
    sample_rate = 48000
    t = np.linspace(0, seconds, int(sample_rate * seconds), endpoint=False)
    samples = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="webm")
    stream = container.add_stream("libopus", rate=sample_rate)
    frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="fltp", layout="mono")
    frame.rate = sample_rate
    for packet in stream.encode(frame):
        container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()
    return buf.getvalue()

def test_websocket_caller_ai_and_live_agent_voice_bridge():
    client = TestClient(app)

    with client.websocket_connect('/ws/call') as caller_ws:
        caller_ws.send_text(json.dumps({
            'type': 'START_CALL',
            'ani': '+15550192834'
        }))
        session_resp = json.loads(caller_ws.receive_text())
        assert session_resp['type'] == 'SESSION_STARTED'
        session_id = session_resp['session_id']
        assert session_id is not None

        caller_ws.send_text(json.dumps({
            'type': 'CALLER_UTTERANCE',
            'text': 'I am good, thank you'
        }))
        conv_resp = json.loads(caller_ws.receive_text())
        assert conv_resp['type'] == 'TURN_RESPONSE'
        assert conv_resp['state'] == 'RESOLVED_CONTAINED'
        assert conv_resp['escalated'] is False

        caller_ws.send_text(json.dumps({
            'type': 'CALLER_UTTERANCE',
            'text': 'I want to speak with a human representative please'
        }))
        esc_resp = json.loads(caller_ws.receive_text())
        assert esc_resp['type'] == 'TURN_RESPONSE'
        assert esc_resp['escalated'] is True
        assert esc_resp['state'] == 'ESCALATING_TO_AGENT'

        with client.websocket_connect('/api/agent/ws') as agent_ws:
            agent_init = json.loads(agent_ws.receive_text())
            assert agent_init['type'] == 'NEW_ESCALATION'
            assert agent_init['payload']['session_id'] == session_id

            accept_resp = client.post('/api/agent/accept', json={
                'session_id': session_id,
                'agent_id': 'agent-sarah-j'
            })
            assert accept_resp.status_code == 200
            assert accept_resp.json()['success'] is True

            agent_accepted = json.loads(agent_ws.receive_text())
            assert agent_accepted['type'] == 'CALL_ACCEPTED'
            assert agent_accepted['session_id'] == session_id

            caller_notif = json.loads(caller_ws.receive_text())
            assert caller_notif['type'] == 'AGENT_CONNECTED'
            assert caller_notif['session_id'] == session_id
            assert caller_notif['agent_id'] == 'agent-sarah-j'

            agent_ws.send_text(json.dumps({
                'type': 'RTC_OFFER',
                'session_id': session_id,
                'sdp': {'type': 'offer', 'sdp': 'v=0 o=agent...'}
            }))

            caller_offer = json.loads(caller_ws.receive_text())
            assert caller_offer['type'] == 'RTC_OFFER'
            assert caller_offer['session_id'] == session_id

            caller_ws.send_text(json.dumps({
                'type': 'RTC_ANSWER',
                'session_id': session_id,
                'sdp': {'type': 'answer', 'sdp': 'v=0 o=caller...'}
            }))

            agent_answer = json.loads(agent_ws.receive_text())
            assert agent_answer['type'] == 'RTC_ANSWER'
            assert agent_answer['session_id'] == session_id

            caller_ws.send_text(json.dumps({
                'type': 'CALLER_LIVE_SPEECH',
                'session_id': session_id,
                'text': 'Hello Sarah, can you hear me?'
            }))
            agent_speech_rcvd = json.loads(agent_ws.receive_text())
            assert agent_speech_rcvd['type'] == 'CALLER_LIVE_SPEECH'
            assert agent_speech_rcvd['text'] == 'Hello Sarah, can you hear me?'

            agent_ws.send_text(json.dumps({
                'type': 'AGENT_LIVE_SPEECH',
                'session_id': session_id,
                'text': 'Yes Jordan, I hear you clearly. How can I help?'
            }))
            caller_speech_rcvd = json.loads(caller_ws.receive_text())
            assert caller_speech_rcvd['type'] == 'AGENT_LIVE_SPEECH'
            assert caller_speech_rcvd['text'] == 'Yes Jordan, I hear you clearly. How can I help?'

            caller_ws.send_text(json.dumps({
                'type': 'END_CALL'
            }))
            caller_end = json.loads(caller_ws.receive_text())
            assert caller_end['type'] == 'CALL_ENDED'

            agent_end = json.loads(agent_ws.receive_text())
            assert agent_end['type'] == 'CALL_ENDED'


@pytest.mark.skipif(not stt_service.available, reason="Local Whisper model unavailable in this environment")
def test_websocket_caller_audio_chunk_returns_stt_result():
    client = TestClient(app)

    with client.websocket_connect('/ws/call') as caller_ws:
        caller_ws.send_text(json.dumps({'type': 'START_CALL', 'ani': '+15550192834'}))
        session_resp = json.loads(caller_ws.receive_text())
        assert session_resp['type'] == 'SESSION_STARTED'

        clip_base64 = base64.b64encode(_make_webm_opus_clip()).decode('utf-8')

        caller_ws.send_text(json.dumps({
            'type': 'CALLER_AUDIO_CHUNK',
            'audio_base64': clip_base64,
            'mime_type': 'audio/webm;codecs=opus',
            'is_final': False
        }))
        partial_resp = json.loads(caller_ws.receive_text())
        assert partial_resp['type'] == 'STT_PARTIAL_RESULT'
        assert 'text' in partial_resp
        assert 0.0 <= partial_resp['confidence'] <= 1.0
        assert partial_resp['stt_ms'] > 0.0

        caller_ws.send_text(json.dumps({
            'type': 'CALLER_AUDIO_CHUNK',
            'audio_base64': clip_base64,
            'mime_type': 'audio/webm;codecs=opus',
            'is_final': True
        }))
        final_resp = json.loads(caller_ws.receive_text())
        assert final_resp['type'] == 'STT_RESULT'
        assert final_resp['degraded'] is False


def test_websocket_caller_audio_chunk_before_start_call_returns_stt_error():
    client = TestClient(app)

    with client.websocket_connect('/ws/call') as caller_ws:
        caller_ws.send_text(json.dumps({
            'type': 'CALLER_AUDIO_CHUNK',
            'audio_base64': base64.b64encode(b'not-real-audio').decode('utf-8'),
            'mime_type': 'audio/webm;codecs=opus',
            'is_final': True
        }))
        resp = json.loads(caller_ws.receive_text())
        assert resp['type'] == 'STT_ERROR'
        assert resp['degraded'] is True
