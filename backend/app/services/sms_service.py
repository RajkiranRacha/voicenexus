import os
import logging
import urllib.request
import urllib.parse
import base64
from typing import Dict, Any

logger = logging.getLogger("voicenexus.sms")

class SmsService:
    """
    Automated Post-Call & Transactional SMS Dispatcher.
    Sends confirmation links (eSIM guides, payment receipts, ticket numbers)
    directly to caller mobile phones via Twilio REST API.
    """
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER", "")

    async def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        if not self.account_sid or not self.auth_token or not self.from_number:
            logger.info(f"[SMS Auto-Dispatch Simulated] To: {to_number} | Body: {message}")
            return {"success": True, "simulated": True, "to": to_number, "message": message}

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = urllib.parse.urlencode({
            "To": to_number,
            "From": self.from_number,
            "Body": message
        }).encode("utf-8")

        auth_header = "Basic " + base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode("utf-8")).decode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Authorization": auth_header})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_body = resp.read().decode("utf-8")
                logger.info(f"[SMS Auto-Dispatch Sent] To: {to_number}")
                return {"success": True, "simulated": False, "status": resp.status, "response": res_body}
        except Exception as e:
            logger.error(f"[SMS Auto-Dispatch Failed] To: {to_number} | Error: {e}")
            return {"success": False, "error": str(e)}

sms_service = SmsService()
