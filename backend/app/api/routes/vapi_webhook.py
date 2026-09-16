import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Response
from app.services.bss_oss import bss_service
from app.services.agent_hub import agent_hub
from app.services.telemetry import telemetry_service
from app.services.sms_service import sms_service
from app.db.database import db
from app.models.schemas import EscalationPayload, DialogueTurn, LatencyMetrics

logger = logging.getLogger("voicenexus.vapi")
router = APIRouter(prefix="/api/vapi", tags=["Vapi Voice Gateway"])

# Helper: load telecom knowledge base
TELECOM_KB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "telecom_kb.json"))
_KB_DATA = None

def _get_kb() -> List[Dict[str, Any]]:
    global _KB_DATA
    if _KB_DATA is None and os.path.exists(TELECOM_KB_PATH):
        try:
            with open(TELECOM_KB_PATH, "r", encoding="utf-8") as f:
                _KB_DATA = json.load(f)
        except Exception:
            _KB_DATA = []
    return _KB_DATA or []

def search_kb(query: str) -> str:
    kb = _get_kb()
    q = query.lower()
    words = [w for w in q.split() if len(w) > 2]
    best_match = None
    best_score = 0
    for item in kb:
        questions = " ".join(item.get("questions", []))
        keywords = " ".join(item.get("keywords", []))
        topic = item.get("topic", "")
        text_corpus = f"{questions} {keywords} {topic}".lower()
        score = sum(1 for w in words if w in text_corpus)
        if score > best_score:
            best_score = score
            best_match = item
    if best_match and best_score > 0:
        ans = best_match.get("answers", {}).get("en") or best_match.get("answer", "")
        return f"{best_match.get('topic')}: {ans}"
    return "No exact telecom policy found. Standard fiber account guidelines apply."


# In-memory session context for active Vapi calls
_vapi_sessions: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(session_id: str, caller_ani: str = "") -> Dict[str, Any]:
    """Retrieves or creates session context for multi-turn Vapi calls."""
    if session_id not in _vapi_sessions:
        matched_acc = bss_service.get_account_by_phone(caller_ani) if caller_ani else None
        _vapi_sessions[session_id] = {
            "session_id": session_id,
            "caller_ani": caller_ani,
            "account": matched_acc,
            "primary_intent": "TELECOM_CARE",
            "escalated": False,
            "escalation_reason": None,
            "turns_count": 0,
        }
    elif caller_ani and not _vapi_sessions[session_id].get("caller_ani"):
        _vapi_sessions[session_id]["caller_ani"] = caller_ani
        if not _vapi_sessions[session_id].get("account"):
            _vapi_sessions[session_id]["account"] = bss_service.get_account_by_phone(caller_ani)
    return _vapi_sessions[session_id]


@router.post("/webhook")
async def vapi_webhook(request: Request):
    """
    Main webhook endpoint for Vapi AI Assistant.
    Coordinates tool execution, live agent transcript sync, and post-call analytics.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    message = payload.get("message", {})
    msg_type = message.get("type")
    call = message.get("call", {})
    call_id = call.get("id", "vapi-call")
    session_id = f"vapi-{call_id}"
    customer_ani = call.get("customer", {}).get("number") or ""
    session_ctx = get_or_create_session(session_id, customer_ani)
    session_ctx["turns_count"] += 1

    # 1. TOOL CALLS: Vapi assistant wants to execute backend actions
    if msg_type == "tool-calls":
        tool_calls = message.get("toolCallList") or message.get("toolCalls") or []
        results = []

        for tc in tool_calls:
            tc_id = tc.get("id")
            func = tc.get("function", {})
            name = func.get("name")
            raw_args = func.get("arguments", {})
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            result_str = await _execute_tool(name, args, session_id, customer_ani)
            results.append({
                "toolCallId": tc_id,
                "result": result_str
            })

        return {"results": results}

    # 2. STATUS UPDATE: Call initiated or state changed
    elif msg_type == "status-update":
        status = message.get("status")
        if status == "in-progress":
            telemetry_service.record_call_start(session_id, customer_ani)
            logger.info(f"[Vapi] Call started: {session_id} from {customer_ani}")
        return {"status": "ok"}

    # 3. TRANSCRIPT STREAM: Real-time turn broadcast to Agent Desktop
    elif msg_type == "transcript":
        transcript_type = message.get("transcriptType")
        if transcript_type == "final":
            role = message.get("role", "user")
            text = message.get("transcript", "")
            turn = {
                "turn_id": int(message.get("timestamp", 0)),
                "speaker": "caller" if role == "user" else "ai",
                "text": text,
                "timestamp": str(message.get("timestamp", ""))
            }
            metadata = {
                "ani": customer_ani,
                "session_id": session_id,
                "provider": "vapi"
            }
            await agent_hub.broadcast_transcript_turn(session_id, turn, metadata)
        return {"status": "ok"}

    # 4. END OF CALL REPORT: Save CDR, trigger analytics & SMS
    elif msg_type == "end-of-call-report":
        duration = int(message.get("durationSeconds") or (message.get("durationMinutes", 0) * 60) or 45)
        transcript_turns = message.get("transcript", "")
        summary = message.get("summary", "Vapi cellular call completed.")

        sess = _vapi_sessions.pop(session_id, {})
        acc = sess.get("account") or (bss_service.get_account_by_phone(customer_ani) if customer_ani else None)
        acc_num = acc.account_number if acc else "UNREGISTERED"
        cust_name = acc.customer_name if acc else "Unknown Caller"
        is_escalated = sess.get("escalated", False)
        esc_reason = sess.get("escalation_reason")
        final_state = "ESCALATED_TO_AGENT" if is_escalated else "RESOLVED_CONTAINED"
        intent = sess.get("primary_intent", "TELECOM_CARE")
        turns = sess.get("turns_count") or len(message.get("messages", [])) or 4

        # Persist to SQLite
        try:
            db.insert_cdr(
                session_id=session_id,
                ani=customer_ani or (acc.phone_number if acc else "+15550000000"),
                account_number=acc_num,
                customer_name=cust_name,
                intent=intent,
                duration_sec=duration,
                final_state=final_state,
                escalation_reason=esc_reason,
                avg_latency_ms=250.0,
                turns_count=turns,
                transcript=[{"speaker": "transcript", "text": transcript_turns}]
            )
        except Exception as e:
            logger.error(f"[Vapi] Error recording CDR to SQLite: {e}")

        # Post-Call SMS
        target_phone = customer_ani or (acc.phone_number if acc else "")
        if target_phone:
            if is_escalated:
                sms_body = (
                    f"NexusFiber Care: Your request has been transferred to a care specialist (Ref #{session_id[:8]}). "
                    f"Our specialist is reviewing your file. Manage your account at: https://nexusfiber.telco/myaccount"
                )
            else:
                sms_body = (
                    f"NexusFiber Care: Thank you for calling! (Ref #{session_id[:8]}). "
                    f"Your request has been resolved. For self-service, bill pay, & eSIM guides, "
                    f"visit: https://nexusfiber.telco/myaccount"
                )
            await sms_service.send_sms(target_phone, sms_body)

        return {"status": "completed"}

    # Default fallback
    return {"status": "received"}


async def _execute_tool(name: str, args: Dict[str, Any], session_id: str, caller_ani: str) -> str:
    """Executes VoiceNexus telecom business tools on behalf of Vapi."""
    logger.info(f"[Vapi Tool] Executing {name} with args: {args}")

    from app.utils.speech_normalizer import clean_account_number, clean_zip_code

    session_ctx = get_or_create_session(session_id, caller_ani)

    if name == "lookup_account":
        session_ctx["primary_intent"] = "BILLING_INQUIRY"
        raw_acc = (
            args.get("account_number")
            or args.get("accountNumber")
            or args.get("account")
            or args.get("account_id")
            or args.get("identifier")
            or args.get("id")
        )
        phone = args.get("phone_number") or args.get("phoneNumber") or args.get("phone")
        raw_zip = args.get("zip_code") or args.get("zipCode") or args.get("zip")

        acc = None
        if raw_acc is not None and str(raw_acc).strip():
            acc_str = str(raw_acc).strip()
            acc_num = clean_account_number(acc_str)
            acc = (
                bss_service.get_account_by_number(acc_num)
                or bss_service.get_account_by_number(acc_str)
                or bss_service.get_account_by_phone(acc_str)
                or bss_service.get_account_by_name(acc_str)
                or bss_service.get_account_by_zip(acc_str)
                or bss_service.get_account_by_email(acc_str)
            )
        if not acc and phone:
            acc = bss_service.get_account_by_phone(str(phone).strip())
        if not acc and raw_zip:
            zip_c = clean_zip_code(str(raw_zip).strip())
            acc = bss_service.get_account_by_zip(zip_c)
        if not acc and caller_ani:
            acc = bss_service.get_account_by_phone(str(caller_ani).strip())

        if acc:
            session_ctx["account"] = acc
            return (
                f"Account Found: Customer {acc.customer_name}, Account #{acc.account_number}. "
                f"Current Balance: ${acc.current_balance:.2f} due on {acc.due_date}. "
                f"Plan: {acc.plan_name}. Router Status: {acc.router_status}."
            )
        return (
            "Account not found for provided credentials. If you are an existing subscriber, "
            "please provide your account number or billing zip code. If you are looking to set up "
            "new fiber service, say 'new service' and I can check coverage in your area."
        )

    elif name == "search_telecom_knowledge":
        session_ctx["primary_intent"] = "GENERAL_POLICY"
        query = args.get("query") or args.get("q") or args.get("topic") or ""
        return search_kb(query)

    elif name == "process_bill_payment":
        session_ctx["primary_intent"] = "PAYMENT"
        raw_acc = (
            args.get("account_number")
            or args.get("accountNumber")
            or args.get("account")
            or args.get("account_id")
            or args.get("identifier")
        )
        if not raw_acc and session_ctx.get("account"):
            raw_acc = session_ctx["account"].account_number

        acc_num = clean_account_number(str(raw_acc)) if raw_acc is not None else None
        amount = float(args.get("amount", 0.0))
        if not acc_num or amount <= 0:
            return "Payment failed: Missing valid account number or amount."
        res = bss_service.process_card_payment(acc_num, amount)
        return (
            f"Payment successful! Transaction ID: {res.get('transaction_id')}. "
            f"Amount paid: ${amount:.2f}. Remaining balance: ${res.get('remaining_balance', 0.0):.2f}."
        )

    elif name == "diagnose_and_reboot_router":
        session_ctx["primary_intent"] = "TECH_SUPPORT"
        raw_acc = (
            args.get("account_number")
            or args.get("accountNumber")
            or args.get("account")
            or args.get("account_id")
            or args.get("identifier")
        )
        if not raw_acc and session_ctx.get("account"):
            raw_acc = session_ctx["account"].account_number
        elif not raw_acc:
            raw_acc = "1001"

        acc_num = clean_account_number(str(raw_acc))
        res = bss_service.bounce_router(acc_num)
        return f"Router reset signal sent. Status: {res.get('status')}. Message: {res.get('message')}"

    elif name == "check_network_outage":
        session_ctx["primary_intent"] = "OUTAGE_TRIAGE"
        raw_zip = args.get("zip_code")
        if not raw_zip and session_ctx.get("account"):
            raw_zip = session_ctx["account"].zip_code
        elif not raw_zip:
            raw_zip = "94107"

        zip_c = clean_zip_code(raw_zip) or "94107"
        outage = bss_service.check_outage_by_zip(zip_c)
        if outage:
            return (
                f"Active outage in {outage.get('region')} ({zip_c}). "
                f"Status: {outage.get('status')}. Reason: {outage.get('reason')}. "
                f"Estimated resolution: {outage.get('estimated_resolution')}."
            )
        return f"No reported network outages in zip code {zip_c}. Grid and fiber nodes operating normally."

    elif name == "transfer_to_agent":
        reason = args.get("reason", "Caller requested human representative")
        session_ctx["escalated"] = True
        session_ctx["escalation_reason"] = reason
        session_ctx["primary_intent"] = "AGENT_ESCALATION"
        online = agent_hub.has_online_agents

        # Look up profile context: explicit argument -> session cache -> caller ANI match
        raw_acc = (
            args.get("account_number")
            or args.get("accountNumber")
            or args.get("account")
            or args.get("identifier")
        )
        matched_acc = None
        if raw_acc:
            acc_num = clean_account_number(str(raw_acc))
            matched_acc = bss_service.get_account_by_number(acc_num) or bss_service.get_account_by_number(str(raw_acc))
        if not matched_acc:
            matched_acc = session_ctx.get("account")
        if not matched_acc and caller_ani:
            matched_acc = bss_service.get_account_by_phone(caller_ani)

        cust_name = matched_acc.customer_name if matched_acc else "Caller"
        acc_id = matched_acc.account_number if matched_acc else "UNREGISTERED"
        phone_num = matched_acc.phone_number if matched_acc else caller_ani

        cust_profile = {
            "account_number": acc_id,
            "customer_name": cust_name,
            "auth_status": matched_acc.auth_status.value if matched_acc else "UNAUTHENTICATED",
            "auth_method": "ACCOUNT_VERIFIED" if matched_acc else "NONE",
            "phone_number": phone_num,
            "source": "vapi_phone"
        }
        if matched_acc:
            dumped = matched_acc.model_dump()
            dumped["auth_status"] = matched_acc.auth_status.value if hasattr(matched_acc.auth_status, 'value') else str(matched_acc.auth_status)
            cust_profile.update(dumped)

        escalation_payload = EscalationPayload(
            session_id=session_id,
            ani=caller_ani or phone_num,
            customer_profile=cust_profile,
            call_context={
                "primary_intent": "AGENT_ESCALATION",
                "intent_confidence": 0.95,
                "duration_in_ivr_seconds": 30,
                "turns_count": session_ctx.get("turns_count", 4),
                "caller_intent": "AGENT_ESCALATION",
                "provider": "vapi"
            },
            resolution_summary={
                "status": "ESCALATED",
                "intent": "AGENT_ESCALATION",
                "attempted_action": "LIVE_AGENT_ESCALATION",
                "current_balance": matched_acc.current_balance if matched_acc else 0.0,
                "failure_or_escalation_reason": reason,
                "notes": f"Vapi call escalated: {reason}",
                "flow_step": "AGENT_HANDOFF"
            },
            recommended_agent_queue="tier2_human_specialist",
            transcript_snippet=[{"speaker": "system", "text": f"Vapi call escalated: {reason}"}]
        )
        await agent_hub.broadcast_escalation(escalation_payload)

        if online:
            return (
                "Transferring call now. I have alerted our care specialist on the desktop portal. "
                "They have your account details and are answering right now."
            )
        else:
            return (
                "I have prioritized your request and alerted our care specialist on the desktop portal. "
                "They have received your account details and live transcript."
            )

    return f"Tool {name} executed successfully."
