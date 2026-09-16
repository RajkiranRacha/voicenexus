import json
import logging
import httpx
from typing import Optional, Dict, Any
from app.config import config

logger = logging.getLogger("voicenexus.vapi.adapter")
USER_AGENT = "VoiceNexus/1.0 (Windows NT 10.0; Win64; x64)"


class VapiCallerAdapter:
    """
    Adapter enabling the Live Agent Web Portal to communicate bi-directionally
    with a mobile phone caller connected via Vapi AI telephony.

    Uses Vapi's Live Call Control URL to:
    1. Announce live human agent connection into the caller's mobile ear.
    2. Speak the agent's live voice / messages (mic transcription or quick responses)
       directly to the caller via high-fidelity neural voice.
    3. Transfer call to agent's direct phone number if requested.
    4. Gracefully terminate cellular calls on agent disconnect.
    """

    def __init__(self, session_id: str, call_id: str, control_url: Optional[str] = None):
        self.session_id = session_id
        self.call_id = call_id
        self.control_url = control_url
        self.api_key = config.VAPI_API_KEY
        self.last_spoken_text: Optional[str] = None

    async def ensure_control_url(self) -> Optional[str]:
        """Retrieves controlUrl from Vapi API if not already supplied via webhook payload."""
        if self.control_url:
            return self.control_url

        if not self.call_id or not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.vapi.ai/call/{self.call_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key.strip()}",
                        "User-Agent": USER_AGENT,
                        "Accept": "application/json"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    monitor = data.get("monitor", {})
                    ctrl = monitor.get("controlUrl")
                    if ctrl:
                        self.control_url = ctrl
                        logger.info(f"[VapiAdapter] Discovered controlUrl for {self.call_id}: {ctrl}")
                        return self.control_url
        except Exception as e:
            logger.warning(f"[VapiAdapter] Failed to query Vapi API for controlUrl: {e}")

        return self.control_url

    async def post_control(self, payload: Dict[str, Any]) -> bool:
        """Sends control command (say, transfer, end-call) to Vapi's live control URL."""
        url = await self.ensure_control_url()
        if not url:
            logger.error(f"[VapiAdapter] No controlUrl available for {self.session_id}. Cannot send: {payload}")
            return False

        try:
            headers = {
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key.strip()}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code in (200, 201, 202, 204):
                    logger.info(f"[VapiAdapter] Sent control command to {self.session_id}: {payload.get('type')}")
                    return True
                else:
                    logger.error(f"[VapiAdapter] ControlUrl returned {resp.status_code}: {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"[VapiAdapter] Error posting to controlUrl {url}: {e}")
            return False

    async def send_text(self, text: str):
        """
        Implements the duck-typed interface expected by AgentHub
        (identical to WebSocket.send_text / TwilioCallerAdapter).
        """
        try:
            data = json.loads(text)
            msg_type = data.get("type")

            if msg_type == "AGENT_CONNECTED":
                agent_name = data.get("agent_name", "Sarah J.")
                announcement = (
                    f"You are now connected with live care specialist {agent_name}. "
                    "I have your verified account details on my screen. How can I help you today?"
                )
                self.last_spoken_text = announcement
                await self.post_control({
                    "type": "say",
                    "content": announcement,
                    "endCallAfterSpoken": False
                })

            elif msg_type == "AGENT_LIVE_SPEECH":
                agent_msg = data.get("text", "").strip()
                if agent_msg and agent_msg != self.last_spoken_text:
                    self.last_spoken_text = agent_msg
                    await self.post_control({
                        "type": "say",
                        "content": agent_msg,
                        "endCallAfterSpoken": False
                    })

            elif msg_type == "AGENT_TRANSFER_PHONE":
                dest_phone = data.get("phone_number") or config.AGENT_FORWARDING_PHONE
                if dest_phone:
                    logger.info(f"[VapiAdapter] Transferring live Vapi call {self.call_id} to phone: {dest_phone}")
                    await self.post_control({
                        "type": "transfer",
                        "destination": {
                            "type": "number",
                            "number": dest_phone
                        }
                    })

            elif msg_type in ("AGENT_DISCONNECT", "CALL_ENDED"):
                logger.info(f"[VapiAdapter] Ending live Vapi call {self.call_id}")
                bye = "The care specialist has ended this session. Thank you for choosing NexusFiber. Goodbye!"
                # First say goodbye, then end call
                success = await self.post_control({
                    "type": "say",
                    "content": bye,
                    "endCallAfterSpoken": True
                })
                if not success:
                    await self.post_control({"type": "end-call"})

        except Exception as e:
            logger.error(f"[VapiAdapter] Error processing agent event: {e}")
