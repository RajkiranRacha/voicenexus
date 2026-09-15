import pytest
import tempfile
import os
from app.db.database import TelecomDatabase
from app.services.sms_service import sms_service
from app.services.bss_oss import bss_service
from app.services.telemetry import telemetry_service

def test_database_crud():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_db_path = f.name

    try:
        test_db = TelecomDatabase(db_path=tmp_db_path)
        # 1. Check seeded data
        sub = test_db.get_subscriber_by_phone("+15550192834")
        assert sub is not None
        assert sub["customer_name"] == "Jordan Rivera"

        # 2. Update balance
        updated = test_db.update_balance("ACC-992014-X", 99.00)
        assert updated is True
        sub2 = test_db.get_subscriber_by_account("ACC-992014-X")
        assert sub2["current_balance"] == 99.00

        # 3. Insert and retrieve CDR
        test_db.insert_cdr(
            session_id="session-test-42",
            ani="+19876543210",
            account_number="ACC-992014-X",
            customer_name="Jordan Rivera",
            intent="PAY_BILL_NOW",
            duration_sec=65,
            final_state="RESOLVED_CONTAINED",
            escalation_reason=None,
            avg_latency_ms=420.0,
            turns_count=3,
            transcript=[{"speaker": "caller", "text": "I want to pay my bill"}]
        )
        cdrs = test_db.get_recent_cdrs(10)
        assert len(cdrs) >= 1
        assert cdrs[0]["session_id"] == "session-test-42"
        assert cdrs[0]["intent"] == "PAY_BILL_NOW"

        # 4. Record CSAT
        assert test_db.record_csat("session-test-42", 5) is True
        cdrs_updated = test_db.get_recent_cdrs(10)
        assert cdrs_updated[0]["csat_rating"] == 5
    finally:
        import gc
        gc.collect()
        try:
            if os.path.exists(tmp_db_path):
                os.remove(tmp_db_path)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_sms_service_mock():
    resp = await sms_service.send_sms("+19876543210", "Test message from VoiceNexus")
    assert resp["success"] is True
