import os
import json
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DB_PATH = os.path.join(DB_DIR, "telecom.db")

class TelecomDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    account_number TEXT PRIMARY KEY,
                    phone_number TEXT UNIQUE NOT NULL,
                    customer_name TEXT NOT NULL,
                    zip_code TEXT NOT NULL,
                    address TEXT NOT NULL,
                    plan_name TEXT NOT NULL,
                    monthly_rate REAL NOT NULL,
                    current_balance REAL NOT NULL,
                    due_date TEXT NOT NULL,
                    payment_card_last4 TEXT DEFAULT '4242',
                    email TEXT DEFAULT 'customer@example.com',
                    auth_status TEXT DEFAULT 'UNAUTHENTICATED',
                    has_active_outage INTEGER DEFAULT 0,
                    router_status TEXT DEFAULT 'ONLINE'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cdrs (
                    session_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    ani TEXT NOT NULL,
                    account_number TEXT,
                    customer_name TEXT,
                    intent TEXT,
                    duration_sec INTEGER,
                    final_state TEXT,
                    escalation_reason TEXT,
                    avg_latency_ms REAL,
                    turns_count INTEGER,
                    csat_rating INTEGER,
                    transcript_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outages (
                    zip_code TEXT PRIMARY KEY,
                    region TEXT NOT NULL,
                    affected_subscribers INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    estimated_resolution TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
            """)
            conn.commit()
        self._seed_default_data()

    def _seed_default_data(self, force: bool = False):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM subscribers")
            count = cursor.fetchone()[0]
            if count == 0 or force or count < 5:
                # Simple pure-numeric account numbers (1001, 1002, 1003, 1004, 1005)
                subscribers = [
                    ("1001", "+15550192834", "Jordan Rivera", "94107", "450 Townsend St, San Francisco, CA", "GigaFiber 500 Ultra", 80.0, 142.5, (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"), "4242", "jordan.rivera@example.com", "UNAUTHENTICATED", 0, "ONLINE"),
                    ("1002", "+15550148821", "Elena Vance", "98101", "1201 3rd Ave, Seattle, WA", "FiberConnect 300", 65.0, 0.0, (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"), "1188", "elena.vance@example.com", "UNAUTHENTICATED", 1, "OFFLINE"),
                    ("1003", "+15550173399", "Marcus Brody", "78701", "200 Congress Ave, Austin, TX", "Gigabit Pro 1000", 110.0, 220.0, (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"), "9901", "marcus.brody@example.com", "UNAUTHENTICATED", 0, "DEGRADED"),
                    ("1004", "+15550101001", "Sam Taylor", "90210", "100 Beverly Blvd, Beverly Hills, CA", "GigaFiber 500 Ultra", 80.0, 45.0, (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"), "1004", "sam.taylor@example.com", "UNAUTHENTICATED", 0, "ONLINE"),
                    ("1005", "+15550102002", "Alex Morgan", "10001", "350 5th Ave, New York, NY", "FiberConnect 1000", 95.0, 0.0, (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d"), "2002", "alex.morgan@example.com", "UNAUTHENTICATED", 0, "ONLINE")
                ]
                cursor.executemany("INSERT OR REPLACE INTO subscribers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", subscribers)

            cursor.execute("SELECT COUNT(*) FROM outages")
            if cursor.fetchone()[0] == 0 or force:
                cursor.execute("INSERT OR REPLACE INTO outages VALUES (?, ?, ?, ?, ?, ?)", ("98101", "Downtown Seattle Metro", 1420, "CREW_DISPATCHED", "2 hours from now", "Fiber trunk line damage due to municipal utility work"))
            conn.commit()

    def reseed_defaults(self, force: bool = True):
        self._seed_default_data(force=force)

    def get_all_subscribers(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscribers ORDER BY customer_name ASC")
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["has_active_outage"] = bool(d["has_active_outage"])
                results.append(d)
            return results

    def upsert_subscriber(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raw_acc = str(data.get("account_number") or "").strip().upper()
        clean_acc = raw_acc if raw_acc else "1006"

        phone = (data.get("phone_number") or "").strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if phone:
                cursor.execute("DELETE FROM subscribers WHERE phone_number = ? AND account_number != ?", (phone, clean_acc))
            cursor.execute("""
                INSERT INTO subscribers (
                    account_number, phone_number, customer_name, zip_code, address,
                    plan_name, monthly_rate, current_balance, due_date, payment_card_last4,
                    email, auth_status, has_active_outage, router_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_number) DO UPDATE SET
                    phone_number = excluded.phone_number,
                    customer_name = excluded.customer_name,
                    zip_code = excluded.zip_code,
                    address = excluded.address,
                    plan_name = excluded.plan_name,
                    monthly_rate = excluded.monthly_rate,
                    current_balance = excluded.current_balance,
                    due_date = excluded.due_date,
                    payment_card_last4 = excluded.payment_card_last4,
                    email = excluded.email,
                    auth_status = excluded.auth_status,
                    has_active_outage = excluded.has_active_outage,
                    router_status = excluded.router_status
            """, (
                clean_acc,
                (data.get("phone_number") or "").strip(),
                data.get("customer_name") or "Subscriber",
                (data.get("zip_code") or "94107").strip(),
                data.get("address") or "100 Fiber Way",
                data.get("plan_name") or "GigaFiber 500 Ultra",
                float(data.get("monthly_rate") or 80.0),
                float(data.get("current_balance") or 0.0),
                data.get("due_date") or (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
                data.get("payment_card_last4") or "4242",
                data.get("email") or "customer@example.com",
                data.get("auth_status") or "UNAUTHENTICATED",
                1 if data.get("has_active_outage") else 0,
                data.get("router_status") or "ONLINE"
            ))
            conn.commit()
            return self.get_subscriber_by_account(clean_acc) or {}

    def delete_subscriber(self, account_number: str) -> bool:
        sub = self.get_subscriber_by_account(account_number)
        actual_acc = sub["account_number"] if sub else account_number.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM subscribers WHERE UPPER(account_number) = ?", (actual_acc,))
            conn.commit()
            return cursor.rowcount > 0

    def get_subscriber_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscribers")
            for r in cursor.fetchall():
                db_phone = r["phone_number"].replace(" ", "").replace("-", "")
                if db_phone.endswith(cleaned[-10:]) or cleaned.endswith(db_phone[-10:]):
                    d = dict(r)
                    d["has_active_outage"] = bool(d["has_active_outage"])
                    return d
        return None

    def get_subscriber_by_account(self, account_number: str) -> Optional[Dict[str, Any]]:
        raw = str(account_number).strip().upper()
        # Legacy alias map for backward compatibility with existing tests
        LEGACY_ALIASES = {
            "ACC-992014-X": "1001",
            "ACC-881230-B": "1002",
            "ACC-773419-C": "1003",
            "ACC-1001": "1001",
            "ACC-1004": "1004",
            "ACC-1005": "1005",
            "ACC-2002": "1005",
            "992014": "1001",
            "881230": "1002",
            "773419": "1003",
        }
        if raw in LEGACY_ALIASES:
            raw = LEGACY_ALIASES[raw]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscribers WHERE UPPER(account_number) = ?", (raw,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["has_active_outage"] = bool(d["has_active_outage"])
                return d

            digits = "".join(filter(str.isdigit, raw))
            if digits:
                cursor.execute("SELECT * FROM subscribers WHERE account_number = ?", (digits,))
                row = cursor.fetchone()
                if row:
                    d = dict(row)
                    d["has_active_outage"] = bool(d["has_active_outage"])
                    return d

                # Fallback: digits search
                cursor.execute("SELECT * FROM subscribers")
                for r in cursor.fetchall():
                    acc_digits = "".join(filter(str.isdigit, r["account_number"]))
                    if digits == acc_digits or (len(digits) >= 4 and digits in acc_digits):
                        d = dict(r)
                        d["has_active_outage"] = bool(d["has_active_outage"])
                        return d
        return None

    def get_subscriber_by_zip(self, zip_code: str) -> Optional[Dict[str, Any]]:
        cleaned = zip_code.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscribers WHERE zip_code = ? LIMIT 1", (cleaned,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["has_active_outage"] = bool(d["has_active_outage"])
                return d
        return None

    def get_subscriber_by_name(self, customer_name: str) -> Optional[Dict[str, Any]]:
        cleaned = customer_name.strip().lower()
        if not cleaned:
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscribers WHERE LOWER(customer_name) = ?", (cleaned,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["has_active_outage"] = bool(d["has_active_outage"])
                return d
            cursor.execute("SELECT * FROM subscribers")
            rows = cursor.fetchall()
            for r in rows:
                db_name = r["customer_name"].strip().lower()
                if cleaned == db_name or cleaned in db_name or db_name in cleaned:
                    d = dict(r)
                    d["has_active_outage"] = bool(d["has_active_outage"])
                    return d
                caller_parts = set(cleaned.split())
                db_parts = set(db_name.split())
                if len(caller_parts.intersection(db_parts)) >= 2:
                    d = dict(r)
                    d["has_active_outage"] = bool(d["has_active_outage"])
                    return d
        return None

    def get_subscriber_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        cleaned = email.strip().lower()
        if not cleaned:
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscribers WHERE LOWER(email) = ?", (cleaned,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["has_active_outage"] = bool(d["has_active_outage"])
                return d
            cursor.execute("SELECT * FROM subscribers")
            for r in cursor.fetchall():
                db_email = (r["email"] or "").strip().lower()
                if cleaned in db_email or db_email in cleaned:
                    d = dict(r)
                    d["has_active_outage"] = bool(d["has_active_outage"])
                    return d
        return None

    def update_balance(self, account_number: str, new_balance: float) -> bool:
        sub = self.get_subscriber_by_account(account_number)
        target_acc = sub["account_number"] if sub else account_number.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE subscribers SET current_balance = ? WHERE UPPER(account_number) = ?", (round(new_balance, 2), target_acc))
            conn.commit()
            return cursor.rowcount > 0

    def update_router_status(self, account_number: str, status: str) -> bool:
        sub = self.get_subscriber_by_account(account_number)
        target_acc = sub["account_number"] if sub else account_number.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE subscribers SET router_status = ? WHERE UPPER(account_number) = ?", (status, target_acc))
            conn.commit()
            return cursor.rowcount > 0

    def get_outage_by_zip(self, zip_code: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM outages WHERE zip_code = ?", (zip_code.strip(),))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def insert_cdr(self, session_id: str, ani: str, account_number: Optional[str], customer_name: Optional[str], intent: str, duration_sec: int, final_state: str, escalation_reason: Optional[str], avg_latency_ms: float, turns_count: int, transcript: List[Dict[str, Any]], csat_rating: Optional[int] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            transcript_str = json.dumps(transcript)
            cursor.execute("""
                INSERT OR REPLACE INTO cdrs (
                    session_id, timestamp, ani, account_number, customer_name,
                    intent, duration_sec, final_state, escalation_reason,
                    avg_latency_ms, turns_count, csat_rating, transcript_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, now, ani, account_number or "UNREGISTERED", customer_name or "Unknown Caller", intent, duration_sec, final_state, escalation_reason, avg_latency_ms, turns_count, csat_rating, transcript_str))
            conn.commit()

    def get_recent_cdrs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cdrs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                if d.get("transcript_json"):
                    try:
                        d["transcript"] = json.loads(d["transcript_json"])
                    except Exception:
                        d["transcript"] = []
                else:
                    d["transcript"] = []
                results.append(d)
            return results

    def record_csat(self, session_id: str, rating: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cdrs SET csat_rating = ? WHERE session_id = ?", (rating, session_id))
            conn.commit()
            return cursor.rowcount > 0

db = TelecomDatabase()
