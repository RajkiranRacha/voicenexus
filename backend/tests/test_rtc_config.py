import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import config, get_ice_servers

client = TestClient(app)

def test_default_rtc_config():
    """Verify GET /api/rtc-config returns standard STUN servers by default."""
    res = client.get("/api/rtc-config")
    assert res.status_code == 200
    data = res.json()
    assert "iceServers" in data
    assert isinstance(data["iceServers"], list)
    assert len(data["iceServers"]) >= 1
    # Check that google and cloudflare STUN are included
    stun_urls = data["iceServers"][0]["urls"]
    assert any("stun.l.google.com" in u for u in stun_urls)
    assert any("stun.cloudflare.com" in u for u in stun_urls)

def test_admin_rtc_config_update_and_get():
    """Verify admin RTC config can be retrieved and updated with TURN details."""
    # 1. Update TURN settings
    update_payload = {
        "turn_server_url": "turn:global.relay.metered.ca:80,turns:global.relay.metered.ca:443",
        "turn_username": "test-user-123",
        "turn_credential": "test-credential-xyz",
        "ice_servers_json": ""
    }
    post_res = client.post("/api/admin/rtc", json=update_payload)
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["success"] is True
    assert len(post_data["effective_ice_servers"]) == 2

    # Check the TURN entry
    turn_entry = post_data["effective_ice_servers"][1]
    assert "turn:global.relay.metered.ca:80" in turn_entry["urls"]
    assert "turns:global.relay.metered.ca:443" in turn_entry["urls"]
    assert turn_entry["username"] == "test-user-123"
    assert turn_entry["credential"] == "test-credential-xyz"

    # 2. Verify GET /api/rtc-config reflects the new TURN settings
    rtc_res = client.get("/api/rtc-config")
    assert rtc_res.status_code == 200
    rtc_data = rtc_res.json()
    assert len(rtc_data["iceServers"]) == 2

    # 3. Clean up back to default
    clean_res = client.post("/api/admin/rtc", json={
        "turn_server_url": "",
        "turn_username": "",
        "turn_credential": "",
        "ice_servers_json": ""
    })
    assert clean_res.status_code == 200
