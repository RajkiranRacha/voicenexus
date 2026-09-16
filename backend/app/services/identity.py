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
        KBA lookup: caller can provide account number, zip code, phone number,
        customer name, email address, or a natural sentence containing them.
        """
        if not identifier:
            return None

        clean_id = identifier.strip()

        # 1. Direct checks
        acc = bss_service.get_account_by_number(clean_id)
        if not acc and zip_code:
            acc = bss_service.get_account_by_zip(zip_code.strip())
        if not acc:
            acc = bss_service.get_account_by_phone(clean_id)
        if not acc:
            acc = bss_service.get_account_by_zip(clean_id)
        if not acc:
            acc = bss_service.get_account_by_email(clean_id)
        if not acc:
            acc = bss_service.get_account_by_name(clean_id)

        # 2. Extract email embedded in sentence
        if not acc:
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', clean_id)
            if email_match:
                acc = bss_service.get_account_by_email(email_match.group(0))

        # 3. Extract ACC- format account number
        if not acc:
            acc_match = re.search(r'\bACC-[\w-]+\b', clean_id, re.IGNORECASE)
            if acc_match:
                acc = bss_service.get_account_by_number(acc_match.group(0))

        # 4. Check known customer names mentioned in sentence
        if not acc:
            try:
                from app.db.database import db
                all_subs = db.get_all_subscribers()
                clean_id_lower = clean_id.lower()
                for sub in all_subs:
                    name_lower = sub["customer_name"].lower()
                    if name_lower in clean_id_lower:
                        acc = bss_service.get_account_by_number(sub["account_number"])
                        break
                    parts = name_lower.split()
                    if len(parts) >= 2 and all(p in clean_id_lower for p in parts):
                        acc = bss_service.get_account_by_number(sub["account_number"])
                        break
            except Exception:
                pass

        # 5. Extract "my name is <X>" pattern if not matched yet
        if not acc:
            name_match = re.search(r'(?:my name is|i am|i\'m|this is|name\'s)\s+([A-Za-z\s]+?)(?:\.|\,|$|\b(?:and|my|please)\b)', clean_id, re.IGNORECASE)
            if name_match:
                candidate_name = name_match.group(1).strip()
                if candidate_name and len(candidate_name) >= 3:
                    acc = bss_service.get_account_by_name(candidate_name)

        # 6. Extract 10-digit phone number embedded in sentence
        if not acc:
            digits = "".join(filter(str.isdigit, clean_id))
            if len(digits) == 10 or (len(digits) == 11 and digits.startswith("1")):
                acc = bss_service.get_account_by_phone(digits)

        # 7. Extract 5-digit zip code embedded in natural sentence
        if not acc:
            zip_match = re.search(r'\b\d{5}\b', clean_id)
            if zip_match:
                acc = bss_service.get_account_by_zip(zip_match.group(0))

        # 8. Extract 4+ digit numeric account number (e.g. "1001", "2002", "992014")
        if not acc:
            digits = "".join(filter(str.isdigit, clean_id))
            if digits and len(digits) >= 4:
                acc = bss_service.get_account_by_number(digits) or (bss_service.get_account_by_zip(digits[:5]) if len(digits) >= 5 else None)

        if acc:
            acc.auth_status = AuthStatus.KBA_VERIFIED
            return acc
        return None

identity_service = IdentityService()
