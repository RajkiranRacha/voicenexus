import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import db

client = TestClient(app)

def test_vapi_tool_calls_lookup_account():
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-test-1", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-101",
                    "type": "function",
                    "function": {
                        "name": "lookup_account",
                        "arguments": {"account_number": "ACC-992014-X"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["toolCallId"] == "tc-101"
    assert "Jordan Rivera" in data["results"][0]["result"]
    assert "Current Balance:" in data["results"][0]["result"]

def test_vapi_tool_calls_process_payment():
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-test-2", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-102",
                    "type": "function",
                    "function": {
                        "name": "process_bill_payment",
                        "arguments": {"account_number": "ACC-992014-X", "amount": 20.0}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "Payment successful" in data["results"][0]["result"]

def test_vapi_tool_calls_telecom_knowledge():
    payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "call-vapi-test-3", "customer": {"number": "+15550192834"}},
            "toolCallList": [
                {
                    "id": "tc-103",
                    "type": "function",
                    "function": {
                        "name": "search_telecom_knowledge",
                        "arguments": {"query": "how to activate esim"}
                    }
                }
            ]
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "eSIM" in data["results"][0]["result"]

def test_vapi_end_of_call_report():
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "call-vapi-test-4", "customer": {"number": "+19876543210"}},
            "durationSeconds": 75,
            "transcript": "Caller asked about bill balance and paid 20 dollars.",
            "summary": "Bill paid successfully"
        }
    }
    response = client.post("/api/vapi/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "completed"}

    # Verify written to SQLite
    cdrs = db.get_recent_cdrs(10)
    found = any("vapi-call-vapi" in c["session_id"] for c in cdrs)
    assert found is True
