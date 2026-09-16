import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.models.schemas import SubscriberAccount, AuthStatus

class BssOssService:
    """
    Mock Telco BSS/OSS (Business & Operations Support Systems)
    Stores accounts, bills, outages, equipment telemetry, and appointments.
    Supports idempotency keys to guarantee transaction safety (VN-4).
    """
    def __init__(self):
        self._accounts: Dict[str, SubscriberAccount] = {}
        self._payment_promises: Dict[str, Dict[str, Any]] = {}
        self._idempotency_log: Dict[str, Any] = {}
        self._technician_appointments: List[Dict[str, Any]] = []
        self._outages: Dict[str, Dict[str, Any]] = {}
        self._seed_initial_data()

    def _seed_initial_data(self):
        # Seed realistic telecom subscribers
        subscribers = [
            SubscriberAccount(
                account_number="ACC-992014-X",
                phone_number="+15550192834",
                customer_name="Jordan Rivera",
                zip_code="94107",
                address="450 Townsend St, San Francisco, CA",
                plan_name="GigaFiber 500 Ultra",
                monthly_rate=80.00,
                current_balance=142.50,
                due_date=(datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),
                has_active_outage=False,
                router_status="ONLINE"
            ),
            SubscriberAccount(
                account_number="ACC-881230-B",
                phone_number="+15550148821",
                customer_name="Elena Vance",
                zip_code="98101",
                address="1201 3rd Ave, Seattle, WA",
                plan_name="FiberConnect 300",
                monthly_rate=65.00,
                current_balance=0.00,
                due_date=(datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"),
                has_active_outage=True,
                router_status="OFFLINE"
            ),
            SubscriberAccount(
                account_number="ACC-773419-C",
                phone_number="+15550173399",
                customer_name="Marcus Brody",
                zip_code="78701",
                address="200 Congress Ave, Austin, TX",
                plan_name="Gigabit Pro 1000",
                monthly_rate=110.00,
                current_balance=220.00,
                due_date=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),  # Past due
                payment_card_last4="9901",
                email="marcus.brody@example.com",
                has_active_outage=False,
                router_status="DEGRADED"
            ),
            SubscriberAccount(
                account_number="ACC-1001",
                phone_number="+15550101001",
                customer_name="Sam Taylor",
                zip_code="90210",
                address="100 Beverly Blvd, Beverly Hills, CA",
                plan_name="GigaFiber 500 Ultra",
                monthly_rate=80.00,
                current_balance=45.00,
                due_date=(datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),
                payment_card_last4="1001",
                email="sam.taylor@example.com",
                has_active_outage=False,
                router_status="ONLINE"
            ),
            SubscriberAccount(
                account_number="ACC-2002",
                phone_number="+15550102002",
                customer_name="Alex Morgan",
                zip_code="10001",
                address="350 5th Ave, New York, NY",
                plan_name="FiberConnect 1000",
                monthly_rate=95.00,
                current_balance=0.00,
                due_date=(datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d"),
                payment_card_last4="2002",
                email="alex.morgan@example.com",
                has_active_outage=False,
                router_status="ONLINE"
            ),
        ]
        for sub in subscribers:
            self._accounts[sub.phone_number] = sub

        # Seed network outage areas
        self._outages["98101"] = {
            "zip_code": "98101",
            "region": "Downtown Seattle Metro",
            "affected_subscribers": 1420,
            "status": "CREW_DISPATCHED",
            "estimated_resolution": "2 hours from now",
            "reason": "Fiber trunk line damage due to municipal utility work"
        }

    def reload_from_db(self):
        """Refreshes in-memory accounts from persistent SQLite database."""
        try:
            from app.db.database import db
            rows = db.get_all_subscribers()
            for r in rows:
                acc = SubscriberAccount(**r)
                self._accounts[acc.phone_number] = acc
        except Exception as e:
            print(f"[BssOssService] reload_from_db error: {e}")

    def get_account_by_phone(self, phone_number: str) -> Optional[SubscriberAccount]:
        from app.utils.speech_normalizer import extract_digits
        digits = extract_digits(phone_number)
        if not digits:
            return None
        last10 = digits[-10:] if len(digits) >= 10 else digits
        for p, acc in self._accounts.items():
            acc_digits = extract_digits(p)
            if acc_digits.endswith(last10) or last10.endswith(acc_digits[-10:]):
                return acc
        try:
            from app.db.database import db
            row = db.get_subscriber_by_phone(phone_number)
            if row:
                acc = SubscriberAccount(**row)
                self._accounts[acc.phone_number] = acc
                return acc
        except Exception:
            pass
        return None

    def get_account_by_number(self, account_number: str) -> Optional[SubscriberAccount]:
        from app.utils.speech_normalizer import clean_account_number, extract_digits
        cleaned = clean_account_number(account_number)
        digits = extract_digits(account_number)
        for acc in self._accounts.values():
            if acc.account_number.upper() == cleaned or acc.account_number.upper() == account_number.strip().upper():
                return acc
            if digits and len(digits) >= 4 and digits in extract_digits(acc.account_number):
                return acc
        try:
            from app.db.database import db
            row = db.get_subscriber_by_account(cleaned) or db.get_subscriber_by_account(account_number)
            if row:
                acc = SubscriberAccount(**row)
                self._accounts[acc.phone_number] = acc
                return acc
        except Exception:
            pass
        return None

    def get_account_by_zip(self, zip_code: str) -> Optional[SubscriberAccount]:
        from app.utils.speech_normalizer import clean_zip_code
        cleaned = clean_zip_code(zip_code)
        for acc in self._accounts.values():
            if acc.zip_code == cleaned:
                return acc
        try:
            from app.db.database import db
            row = db.get_subscriber_by_zip(cleaned)
            if row:
                acc = SubscriberAccount(**row)
                self._accounts[acc.phone_number] = acc
                return acc
        except Exception:
            pass
        return None

    def get_account_by_name(self, customer_name: str) -> Optional[SubscriberAccount]:
        cleaned = customer_name.strip().lower()
        if not cleaned:
            return None
        for acc in self._accounts.values():
            acc_name = acc.customer_name.strip().lower()
            if cleaned == acc_name or cleaned in acc_name or acc_name in cleaned:
                return acc
            caller_parts = set(cleaned.split())
            db_parts = set(acc_name.split())
            if len(caller_parts.intersection(db_parts)) >= 2:
                return acc
        try:
            from app.db.database import db
            row = db.get_subscriber_by_name(customer_name)
            if row:
                acc = SubscriberAccount(**row)
                self._accounts[acc.phone_number] = acc
                return acc
        except Exception:
            pass
        return None

    def get_account_by_email(self, email: str) -> Optional[SubscriberAccount]:
        cleaned = email.strip().lower()
        if not cleaned:
            return None
        for acc in self._accounts.values():
            acc_email = (acc.email or "").strip().lower()
            if cleaned == acc_email or cleaned in acc_email:
                return acc
        try:
            from app.db.database import db
            row = db.get_subscriber_by_email(email)
            if row:
                acc = SubscriberAccount(**row)
                self._accounts[acc.phone_number] = acc
                return acc
        except Exception:
            pass
        return None

    def record_payment_promise(
        self,
        account_number: str,
        amount: float,
        promise_date: str,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Record a payment arrangement promise with idempotency safety.
        """
        if idempotency_key in self._idempotency_log:
            return self._idempotency_log[idempotency_key]

        confirmation_code = f"PP-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "confirmation_code": confirmation_code,
            "account_number": account_number,
            "amount": amount,
            "scheduled_date": promise_date,
            "status": "ACTIVE_HOLD_APPLIED",
            "timestamp": datetime.now().isoformat()
        }
        self._payment_promises[confirmation_code] = record
        self._idempotency_log[idempotency_key] = {
            "success": True,
            "confirmation_code": confirmation_code,
            "message": f"Payment arrangement scheduled for ${amount:.2f} on {promise_date}.",
            "details": record
        }
        return self._idempotency_log[idempotency_key]

    def process_card_payment(
        self,
        account_number: str,
        amount: float,
        card_last4: str = "4242",
        idempotency_key: str = None
    ) -> Dict[str, Any]:
        """
        Processes real-time bill payment against the card on file (VN-4).
        Deducts balance, creates transaction receipt with idempotency guard.
        """
        if idempotency_key and idempotency_key in self._idempotency_log:
            return self._idempotency_log[idempotency_key]

        acc = self.get_account_by_number(account_number)
        tx_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        if acc:
            acc.current_balance = max(0.0, round(acc.current_balance - amount, 2))
            try:
                from app.db.database import db
                db.update_balance(acc.account_number, acc.current_balance)
            except Exception:
                pass

        record = {
            "success": True,
            "transaction_id": tx_id,
            "account_number": account_number,
            "amount_paid": amount,
            "remaining_balance": acc.current_balance if acc else 0.0,
            "payment_method": f"Card ending in {card_last4}",
            "timestamp": datetime.now().isoformat()
        }
        if idempotency_key:
            self._idempotency_log[idempotency_key] = record
        return record

    def check_outage_by_zip(self, zip_code: str) -> Optional[Dict[str, Any]]:
        return self._outages.get(zip_code)

    def diagnose_broadband_line(self, account_number: str) -> Dict[str, Any]:
        acc = self.get_account_by_number(account_number)
        if not acc:
            return {"status": "UNKNOWN_ACCOUNT", "healthy": False}
        
        if acc.has_active_outage:
            return {
                "status": "AREA_OUTAGE_DETECTED",
                "healthy": False,
                "optical_power_dbm": -99.0,
                "router_reachable": False,
                "message": "Optical terminal is unpowered or fiber path severed at regional node."
            }
        
        if acc.router_status == "DEGRADED":
            return {
                "status": "DEGRADED_SIGNAL",
                "healthy": False,
                "optical_power_dbm": -27.4,
                "packet_loss_pct": 14.2,
                "router_reachable": True,
                "message": "High packet loss detected on Wi-Fi gateway. Remote reboot recommended."
            }

        return {
            "status": "ONLINE_NOMINAL",
            "healthy": True,
            "optical_power_dbm": -19.2,
            "packet_loss_pct": 0.0,
            "router_reachable": True,
            "message": "Fiber terminal and gateway operating within optimal parameters."
        }

    def bounce_router(self, account_number: str) -> Dict[str, Any]:
        acc = self.get_account_by_number(account_number)
        if acc:
            acc.router_status = "ONLINE"
            try:
                from app.db.database import db
                db.update_router_status(acc.account_number, "ONLINE")
            except Exception:
                pass
            return {
                "success": True,
                "status": "ONLINE_RESTORED",
                "message": "Gateway provisioning profile refreshed and connection restored."
            }
        return {
            "success": True,
            "status": "REBOOT_SENT",
            "message": "Soft reset signal sent to gateway. Should reconnect within 90 seconds."
        }

    def schedule_technician(
        self,
        account_number: str,
        preferred_time_slot: str,
        notes: str
    ) -> Dict[str, Any]:
        dispatch_id = f"DISP-{uuid.uuid4().hex[:6].upper()}"
        appointment = {
            "dispatch_id": dispatch_id,
            "account_number": account_number,
            "time_slot": preferred_time_slot,
            "notes": notes,
            "status": "CONFIRMED",
            "technician_assigned": "Field Ops Team 4"
        }
        self._technician_appointments.append(appointment)
        return {
            "success": True,
            "dispatch_id": dispatch_id,
            "time_slot": preferred_time_slot,
            "message": f"Technician visit booked for {preferred_time_slot}."
        }

bss_service = BssOssService()
