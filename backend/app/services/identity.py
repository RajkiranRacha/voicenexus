import random
from typing import Dict, Optional, Tuple
from app.models.schemas import AuthStatus, SubscriberAccount
from app.services.bss_oss import bss_service

class IdentityService:
    """
    Caller Identity and Verification Service (VN-3).
    Provides Tier 1 (ANI Passive Match) and Tier 2 (Step-up SMS OTP) authentication.
    """
    def __init__(self):
        # Maps phone_number -> OTP code
        self._active_otps: Dict[str, str] = {}

    def verify_ani(self, phone_number: str) -> Tuple[AuthStatus, Optional[SubscriberAccount]]:
        """
        Passive Tier 1 Auth: Checks if incoming calling line identification (ANI)
        matches a subscriber in the BSS/OSS system.
        """
        acc = bss_service.get_account_by_phone(phone_number)
        if acc:
            acc.auth_status = AuthStatus.ANI_MATCHED
            return AuthStatus.ANI_MATCHED, acc
        return AuthStatus.UNAUTHENTICATED, None

    def issue_step_up_otp(self, phone_number: str) -> str:
        """
        Generates and 'transmits' a 4-digit verification code to the caller's mobile.
        """
        code = str(random.randint(1000, 9999))
        self._active_otps[phone_number] = code
        print(f"[IdentityService] SMS sent to {phone_number}: Your NexusFiber verification code is {code}")
        return code

    def verify_step_up_otp(self, phone_number: str, submitted_code: str) -> bool:
        expected = self._active_otps.get(phone_number)
        # Also allow universal test code 1234 for easy interactive testing
        if submitted_code == expected or submitted_code == "1234":
            acc = bss_service.get_account_by_phone(phone_number)
            if acc:
                acc.auth_status = AuthStatus.OTP_VERIFIED
            return True
        return False

    def verify_knowledge_based(self, account_number: str, zip_code: str) -> bool:
        acc = bss_service.get_account_by_number(account_number)
        if acc and acc.zip_code == zip_code.strip():
            acc.auth_status = AuthStatus.ANI_MATCHED
            return True
        return False

identity_service = IdentityService()
