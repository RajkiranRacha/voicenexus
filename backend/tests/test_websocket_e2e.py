import json
import pytest
from fastapi.testclient import TestClient
from app.main import app

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
