import pytest
from app.models.schemas import CallState, IntentEnum
from app.engine.intent_classifier import intent_classifier
from app.engine.state_machine import CallSessionStateMachine

def test_basic_responses_intent_mapping():
    # Issue 2: Verify speech-recognition/NLU layer maps basic responses to correct intents
    # Confirmation: "Yes", "Yeah", "Yep"
    for phrase in ["Yes", "yes", "Yeah", "yeah", "Yep", "yep", "Sure", "Sounds good"]:
        intent, conf, _ = intent_classifier.classify(phrase)
        assert intent in [IntentEnum.CONFIRMATION, IntentEnum.CONFIRMATION_YES], f"Failed on '{phrase}', got {intent}"
        assert intent_classifier.get_intent_category(intent) == "Confirmation"

    # Rejection: "No", "Nope"
    for phrase in ["No", "no", "Nope", "nope", "Nah", "Cancel"]:
        intent, conf, _ = intent_classifier.classify(phrase)
        assert intent in [IntentEnum.REJECTION, IntentEnum.CONFIRMATION_NO], f"Failed on '{phrase}', got {intent}"
        assert intent_classifier.get_intent_category(intent) == "Rejection"

    # Gratitude: "Thank you", "Thanks"
    for phrase in ["Thank you", "thank you", "Thanks", "thanks", "Thank you so much", "Many thanks"]:
        intent, conf, _ = intent_classifier.classify(phrase)
        assert intent == IntentEnum.GRATITUDE, f"Failed on '{phrase}', got {intent}"
        assert intent_classifier.get_intent_category(intent) == "Gratitude"

    # Acknowledgement: "Okay", "Alright"
    for phrase in ["Okay", "okay", "Ok", "ok", "Alright", "alright", "All right"]:
        intent, conf, _ = intent_classifier.classify(phrase)
        assert intent == IntentEnum.ACKNOWLEDGEMENT, f"Failed on '{phrase}', got {intent}"
        assert intent_classifier.get_intent_category(intent) == "Acknowledgement"

def test_conversational_response_does_not_transfer():
    # Issue 3: Caller says "I am good, thank you" after greeting -> must NOT escalate to agent
    session = CallSessionStateMachine(session_id="test-conv-1", ani="+15550192834")
    greeting = session.get_greeting()
    assert "How can I help you today?" in greeting

    resp, state, esc = session.process_turn("I am good, thank you.")
    # Must NOT transfer to human agent
    assert esc is None, "Expected NO escalation for 'I am good, thank you.'"
    assert state == CallState.RESOLVED_CONTAINED
    assert "You're very welcome!" in resp
    assert session.consecutive_unrecognized == 0

def test_multiple_conversational_turns_do_not_escalate():
    # Caller has multiple conversational turns without task requests
    session = CallSessionStateMachine(session_id="test-conv-2", ani="+15550192834")
    session.get_greeting()

    # Turn 1: "Okay"
    resp1, state1, esc1 = session.process_turn("Okay")
    assert esc1 is None
    assert state1 == CallState.INTENT_ROUTING
    assert session.consecutive_unrecognized == 0

    # Turn 2: "Thank you"
    resp2, state2, esc2 = session.process_turn("Thank you")
    assert esc2 is None
    assert state2 == CallState.INTENT_ROUTING
    assert session.consecutive_unrecognized == 0

    # Turn 3: "I'm good, thanks"
    resp3, state3, esc3 = session.process_turn("I'm good, thanks")
    assert esc3 is None
    assert state3 == CallState.RESOLVED_CONTAINED
    assert session.consecutive_unrecognized == 0

def test_admin_config_persistence():
    # Issue 5 & 7: Test voice and rate configuration persistence
    from app.config import config, save_persisted_config, load_persisted_config, CONFIG_FILE
    import os

    orig_voice = config.DEFAULT_VOICE
    orig_rate = config.VOICE_RATE
    orig_lang = config.LANGUAGE

    try:
        # Set new configuration
        config.DEFAULT_VOICE = "en-US-GuyNeural"
        config.VOICE_RATE = "-25%"
        config.LANGUAGE = "en-US"
        save_persisted_config()
        assert os.path.exists(CONFIG_FILE)

        # Mutate in-memory to something else
        config.DEFAULT_VOICE = "dummy-voice"
        config.VOICE_RATE = "+99%"

        # Reload from file
        load_persisted_config()
        assert config.DEFAULT_VOICE == "en-US-GuyNeural"
        assert config.VOICE_RATE == "-25%"
    finally:
        # Restore
        config.DEFAULT_VOICE = orig_voice
        config.VOICE_RATE = orig_rate
        config.LANGUAGE = orig_lang
        save_persisted_config()

def test_language_switching_english_spanish_hindi_english():
    # Issue 6: English -> Spanish -> Hindi -> English repeated switching
    session = CallSessionStateMachine(session_id="test-lang-switch", ani="+15550192834")
    
    # 1. Start in English
    greeting_en = session.get_greeting()
    assert "Jordan Rivera" in greeting_en
    assert session.language == "en-US"

    # 2. Switch to Spanish
    resp_es, state_es, _ = session.process_turn("Switch to Spanish")
    assert session.language == "es-US"
    assert "español" in resp_es.lower()

    # Spanish conversational check
    resp_es2, state_es2, _ = session.process_turn("gracias")
    assert "placer" in resp_es2.lower() or "factura" in resp_es2.lower()

    # 3. Switch to Hindi
    resp_hi, state_hi, _ = session.process_turn("Switch to Hindi")
    assert session.language == "hi-IN"
    assert "हिंदी" in resp_hi

    # Hindi conversational check
    resp_hi2, state_hi2, _ = session.process_turn("theek hai")
    assert "समझ गया" in resp_hi2 or "सहायता" in resp_hi2

    # 4. Switch back to English
    resp_en, state_en, _ = session.process_turn("Switch back to English")
    assert session.language == "en-US"
    assert "English" in resp_en

    # English conversational check
    resp_en2, state_en2, esc = session.process_turn("I am good, thank you")
    assert esc is None
    assert state_en2 == CallState.RESOLVED_CONTAINED

@pytest.mark.asyncio
async def test_agent_hub_caller_notification_on_accept():
    from app.services.agent_hub import agent_hub
    import json
    
    received_caller_messages = []
    
    class FakeCallerWS:
        async def send_text(self, text: str):
            received_caller_messages.append(json.loads(text))

    fake_ws = FakeCallerWS()
    test_sess = "test-call-1234"
    agent_hub.register_caller(test_sess, fake_ws)

    # Trigger accept
    await agent_hub.accept_escalation(test_sess, "agent-sarah-j", "Sarah J.")

    assert len(received_caller_messages) == 1
    assert received_caller_messages[0]["type"] == "AGENT_CONNECTED"
    assert received_caller_messages[0]["session_id"] == test_sess
    assert received_caller_messages[0]["agent_id"] == "agent-sarah-j"
    assert received_caller_messages[0]["agent_name"] == "Sarah J."

    # Test relay from caller to agent
    await agent_hub.relay_caller_to_agent(test_sess, {"type": "RTC_OFFER", "sdp": "fake-sdp"})
    
    # Test relay from agent to caller
    await agent_hub.relay_agent_to_caller(test_sess, {"type": "RTC_ANSWER", "sdp": "fake-sdp-answer"})
    assert len(received_caller_messages) == 2
    assert received_caller_messages[1]["type"] == "RTC_ANSWER"

    agent_hub.unregister_caller(test_sess)

