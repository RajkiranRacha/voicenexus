import pytest
from app.models.schemas import CallState, IntentEnum
from app.engine.intent_classifier import intent_classifier
from app.engine.state_machine import CallSessionStateMachine
from app.services.telecom_kb import telecom_kb_service
from app.services.bss_oss import bss_service
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_bss_singleton():
    bss_service._seed_initial_data()
    yield
    bss_service._seed_initial_data()

class TestDefect1CallWrapUp:
    """
    Tests for Defect-1: Call closing after issue resolved.
    Verifies that polite wrap-up terms ('No, Thanks for resolving',
    'There is no more concerns good to drop now', etc.) properly close the call.
    """

    @pytest.mark.parametrize("utterance", [
        "No, Thanks for resolving",
        "no thanks for resolving",
        "Thanks for resolving",
        "thank you for resolving",
        "There is no more concerns good to drop now",
        "no more concerns good to drop now",
        "good to drop now",
        "good to hang up",
        "all good thanks",
        "all set thanks",
        "that's all, thank you",
        "nothing else thanks",
        "issue is resolved",
        "that resolves it",
        "no thanks",
        "no thank you"
    ])
    def test_classifier_identifies_call_wrapup(self, utterance):
        intent, conf, _ = intent_classifier.classify(utterance)
        assert intent == IntentEnum.CALL_WRAPUP, f"Expected CALL_WRAPUP for '{utterance}', got {intent}"
        assert conf >= 0.90

    def test_state_machine_closes_call_on_wrapup(self):
        fsm = CallSessionStateMachine("test-session-1", "+15550192834")
        resp, state, esc = fsm.process_turn("No, Thanks for resolving")

        assert state == CallState.RESOLVED_CONTAINED
        assert fsm.should_close_call is True
        assert "glad" in resp.lower() or "welcome" in resp.lower() or "goodbye" in resp.lower()
        assert esc is None

    def test_state_machine_closes_call_on_good_to_drop(self):
        fsm = CallSessionStateMachine("test-session-2", "+15550192834")
        resp, state, esc = fsm.process_turn("There is no more concerns good to drop now")

        assert state == CallState.RESOLVED_CONTAINED
        assert fsm.should_close_call is True
        assert esc is None

    def test_state_machine_auto_wrapup_after_transaction(self):
        """
        After an action has been resolved (e.g. bill payment), saying 'thank you'
        or 'that's all' must automatically wrap up and close the call.
        """
        fsm = CallSessionStateMachine("test-session-3", "+15550192834")
        # 1. Caller asks to pay bill
        fsm.process_turn("Pay bill now")
        # 2. Caller confirms payment
        resp, state, _ = fsm.process_turn("yes please")
        assert state == CallState.RESOLVED_CONTAINED
        assert fsm.has_resolved_action is True

        # 3. Caller says simple 'thank you'
        resp, state, _ = fsm.process_turn("thank you")
        assert state == CallState.RESOLVED_CONTAINED
        assert fsm.should_close_call is True
        assert "welcome" in resp.lower() or "goodbye" in resp.lower()


class TestDefect2TelecomKnowledgeBase:
    """
    Tests for Defect-2: Telecom Domain Knowledge Base & Ingestion.
    Verifies matching across eSIM, Roaming, Router LEDs, MNP, APN, etc.
    """

    def test_esim_activation_retrieval(self):
        match = telecom_kb_service.find_match("How do I activate eSIM on my phone?", language="en-US")
        assert match is not None
        assert match["article_id"] == "esim_activation"
        assert "QR code" in match["answer"] or "eSIM" in match["answer"]
        assert match["confidence"] >= 0.70

    def test_roaming_pass_retrieval(self):
        match = telecom_kb_service.find_match("What roaming pass do I need while traveling abroad?", language="en-US")
        assert match is not None
        assert match["article_id"] == "international_roaming"
        assert "$10" in match["answer"] or "Roaming" in match["answer"]

    def test_router_lights_retrieval(self):
        match = telecom_kb_service.find_match("Why is my router red light blinking?", language="en-US")
        assert match is not None
        assert match["article_id"] == "router_lights_diagnostic"
        assert "LOS" in match["answer"] or "fiber" in match["answer"]

    def test_mnp_port_retrieval(self):
        match = telecom_kb_service.find_match("How do I get a transfer PIN to port my number?", language="en-US")
        assert match is not None
        assert match["article_id"] == "number_portability_mnp"
        assert "PIN" in match["answer"] or "PORT" in match["answer"]

    def test_multilingual_kb_retrieval(self):
        # Spanish match
        match_es = telecom_kb_service.find_match("Cómo activo mi eSIM?", language="es-US")
        assert match_es is not None
        assert "¿Puedo ayudarle con algo más hoy?" in match_es["answer"] or "eSIM" in match_es["answer"]

    def test_fsm_integrates_telecom_kb(self):
        fsm = CallSessionStateMachine("test-session-kb", "+15550192834")
        resp, state, esc = fsm.process_turn("How do I change my wifi password?")

        assert state == CallState.RESOLVED_CONTAINED
        assert fsm.current_intent == IntentEnum.TELECOM_KNOWLEDGE
        assert fsm.has_resolved_action is True
        assert "192.168.1.1" in resp or "password" in resp.lower() or "app" in resp.lower()
        assert esc is None

        # And follow up with call wrap-up
        resp_close, state_close, _ = fsm.process_turn("No, Thanks for resolving")
        assert state_close == CallState.RESOLVED_CONTAINED
        assert fsm.should_close_call is True


class TestAdminKnowledgeApi:
    """
    Tests for Admin Knowledge Base REST API endpoints.
    """

    def test_get_knowledge_base(self):
        response = client.get("/api/admin/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 8

    def test_knowledge_test_endpoint(self):
        response = client.post("/api/admin/knowledge/test", json={
            "query": "How do I activate eSIM on my phone?",
            "language": "en-US"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is True
        assert data["article_id"] == "esim_activation"

    def test_upsert_and_delete_article(self):
        article_payload = {
            "id": "test_voicemail_setup",
            "topic": "Voicemail Password Reset",
            "category": "Account & Porting",
            "keywords": ["voicemail", "reset voicemail pin", "voicemail password"],
            "questions": ["How do I reset my voicemail PIN?"],
            "answers": {
                "en": "To reset your voicemail PIN, dial *86 from your phone. Can I help you with anything else today?"
            }
        }
        # Create
        create_res = client.post("/api/admin/knowledge", json=article_payload)
        assert create_res.status_code == 200
        assert create_res.json()["success"] is True

        # Test retrieval
        test_res = client.post("/api/admin/knowledge/test", json={
            "query": "reset voicemail pin",
            "language": "en-US"
        })
        assert test_res.status_code == 200
        assert test_res.json()["matched"] is True
        assert test_res.json()["article_id"] == "test_voicemail_setup"

        # Delete
        del_res = client.delete("/api/admin/knowledge/test_voicemail_setup")
        assert del_res.status_code == 200
        assert del_res.json()["success"] is True
