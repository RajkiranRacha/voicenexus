import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.telemetry import telemetry_service


def test_disconnect_mid_call_is_recorded_as_abandoned_not_resolved():
    # A caller who disconnects mid-flow (never reaching RESOLVED_CONTAINED or
    # ESCALATING_TO_AGENT) must be counted as an abandoned call, not silently
    # rolled up into the "contained" success metric.
    client = TestClient(app)
    with client.websocket_connect('/ws/call') as caller_ws:
        caller_ws.send_text(json.dumps({'type': 'START_CALL', 'ani': '+15550192834'}))
        session_resp = json.loads(caller_ws.receive_text())
        session_id = session_resp['session_id']

        # Ask a question that starts a subflow but never resolves or confirms it.
        caller_ws.send_text(json.dumps({'type': 'CALLER_UTTERANCE', 'text': 'What is my bill?'}))
        json.loads(caller_ws.receive_text())
        # Caller hangs up here (context manager exit triggers WebSocketDisconnect).

    record = next(r for r in telemetry_service.get_recent_cdrs(100) if r["session_id"] == session_id)
    assert record["final_state"] == "ABANDONED"

    summary = telemetry_service.get_summary()
    assert summary.abandoned_calls >= 1
    assert summary.abandonment_rate_pct > 0.0


def test_csat_submission_updates_summary_average():
    client = TestClient(app)
    with client.websocket_connect('/ws/call') as caller_ws:
        caller_ws.send_text(json.dumps({'type': 'START_CALL', 'ani': '+15550192834'}))
        json.loads(caller_ws.receive_text())
        caller_ws.send_text(json.dumps({'type': 'CALLER_UTTERANCE', 'text': 'thank you, nothing else'}))
        resp = json.loads(caller_ws.receive_text())
        session_id = resp['session_id']
        assert resp['state'] == 'RESOLVED_CONTAINED'

    csat_resp = client.post("/api/telemetry/csat", json={"session_id": session_id, "rating": 5})
    assert csat_resp.status_code == 200
    assert csat_resp.json()["success"] is True

    summary = telemetry_service.get_summary()
    assert summary.csat_response_count >= 1
    assert summary.avg_csat is not None


def test_csat_submission_unknown_session_returns_404():
    client = TestClient(app)
    resp = client.post("/api/telemetry/csat", json={"session_id": "does-not-exist", "rating": 3})
    assert resp.status_code == 404


def test_export_endpoint_returns_csv_with_header_row():
    client = TestClient(app)
    resp = client.get("/api/telemetry/export?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    first_line = resp.text.splitlines()[0]
    assert "session_id" in first_line
    assert "final_state" in first_line


def test_export_endpoint_json_format_matches_cdrs_shape():
    client = TestClient(app)
    resp = client.get("/api/telemetry/export?format=json&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "session_id" in data[0]


def test_latency_slo_breach_pct_present_in_summary():
    summary = telemetry_service.get_summary()
    assert summary.latency_slo_target_ms == 1000.0
    assert 0.0 <= summary.latency_slo_breach_pct <= 100.0
