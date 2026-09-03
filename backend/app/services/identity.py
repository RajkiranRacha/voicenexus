import random
import re
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

    def get_active_otp(self, phone_number: str) -> Optional[str]:
        return self._active_otps.get(phone_number)

    def verify_step_up_otp(self, phone_number: str, submitted_code: str) -> bool:
        expected = self._active_otps.get(phone_number)
        # Also allow universal test code 1234 for easy interactive testing
        clean_sub = submitted_code.strip()
        if clean_sub == expected or clean_sub == "1234":
            acc = bss_service.get_account_by_phone(phone_number)
            if acc:
                acc.auth_status = AuthStatus.OTP_VERIFIED
            return True
        return False

    def verify_knowledge_based(self, identifier: str, zip_code: Optional[str] = None) -> Optional[SubscriberAccount]:
        """
        KBA lookup: caller can provide account number, zip code, or natural sentence containing them.
        """
        clean_id = identifier.strip()
        acc = bss_service.get_account_by_number(clean_id)
        if not acc and zip_code:
            acc = bss_service.get_account_by_zip(zip_code.strip())
        if not acc:
            acc = bss_service.get_account_by_zip(clean_id)
        if not acc:
            # Extract 5-digit zip code if embedded in natural sentence
            zip_match = re.search(r'\b\d{5}\b', clean_id)
            if zip_match:
                acc = bss_service.get_account_by_zip(zip_match.group(0))
        if not acc:
            # Extract account number format like ACC-XXXX or 6+ digits
            acc_match = re.search(r'\bACC-[\w-]+\b', clean_id, re.IGNORECASE)
            if acc_match:
                acc = bss_service.get_account_by_number(acc_match.group(0))
        if not acc:
            digits = "".join(filter(str.isdigit, clean_id))
            if len(digits) >= 5:
                acc = bss_service.get_account_by_zip(digits[:5]) or bss_service.get_account_by_number(digits)
        if not acc:
            acc = bss_service.get_account_by_phone(clean_id)

        if acc:
            acc.auth_status = AuthStatus.KBA_VERIFIED
            return acc
        return None

identity_service = IdentityService()
