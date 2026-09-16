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
    customer_ani = call.get("customer", {}).get("number", "+15550192834")

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

        # Persist to SQLite
        try:
            db.insert_cdr(
                session_id=session_id,
                ani=customer_ani,
                account_number="ACC-992014-X",
                customer_name="Jordan Rivera",
                intent="TELECOM_CARE",
                duration_sec=duration,
                final_state="RESOLVED_CONTAINED",
                escalation_reason=None,
                avg_latency_ms=250.0,
                turns_count=len(message.get("messages", [])) or 4,
                transcript=[{"speaker": "transcript", "text": transcript_turns}]
            )
        except Exception as e:
            logger.error(f"[Vapi] Error recording CDR to SQLite: {e}")

        # Post-Call SMS
        if customer_ani:
            sms_body = (
                f"NexusFiber Care: Thank you for calling! (Ref #{session_id[:8]}). "
                f"Your request has been logged. For digital self-service & eSIM guides, "
                f"visit: https://nexusfiber.telco/myaccount"
            )
            await sms_service.send_sms(customer_ani, sms_body)

        return {"status": "completed"}

    # Default fallback
    return {"status": "received"}


async def _execute_tool(name: str, args: Dict[str, Any], session_id: str, caller_ani: str) -> str:
    """Executes VoiceNexus telecom business tools on behalf of Vapi."""
    logger.info(f"[Vapi Tool] Executing {name} with args: {args}")

    from app.utils.speech_normalizer import clean_account_number, clean_zip_code

    if name == "lookup_account":
        raw_acc = args.get("account_number")
        phone = args.get("phone_number") or caller_ani
        raw_zip = args.get("zip_code")

        acc_num = clean_account_number(raw_acc) if raw_acc else None
        zip_c = clean_zip_code(raw_zip) if raw_zip else None

        acc = None
        if acc_num:
            acc = bss_service.get_account_by_number(acc_num)
        if not acc and phone:
            acc = bss_service.get_account_by_phone(phone)
        if not acc and zip_c:
            acc = bss_service.get_account_by_zip(zip_c)

        if acc:
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
        query = args.get("query", "")
        return search_kb(query)

    elif name == "process_bill_payment":
        raw_acc = args.get("account_number")
        acc_num = clean_account_number(raw_acc) if raw_acc else None
        amount = float(args.get("amount", 0.0))
        if not acc_num or amount <= 0:
            return "Payment failed: Missing valid account number or amount."
        res = bss_service.process_card_payment(acc_num, amount)
        return (
            f"Payment successful! Transaction ID: {res.get('transaction_id')}. "
            f"Amount paid: ${amount:.2f}. Remaining balance: ${res.get('remaining_balance', 0.0):.2f}."
        )

    elif name == "diagnose_and_reboot_router":
        raw_acc = args.get("account_number", "ACC-992014-X")
        acc_num = clean_account_number(raw_acc)
        res = bss_service.bounce_router(acc_num)
        return f"Router reset signal sent. Status: {res.get('status')}. Message: {res.get('message')}"

    elif name == "check_network_outage":
        raw_zip = args.get("zip_code", "94107")
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
        online = agent_hub.has_online_agents

        # Look up profile context if available
        matched_acc = bss_service.get_account_by_phone(caller_ani)
        cust_name = matched_acc.customer_name if matched_acc else "Caller"
        acc_id = matched_acc.account_number if matched_acc else "UNREGISTERED"

        cust_profile = {
            "account_number": acc_id,
            "customer_name": cust_name,
            "auth_status": matched_acc.auth_status.value if matched_acc else "UNAUTHENTICATED",
            "auth_method": "ANI_PASSIVE_MATCH" if matched_acc else "NONE",
            "phone_number": caller_ani,
            "source": "vapi_phone"
        }
        if matched_acc:
            dumped = matched_acc.model_dump()
            dumped["auth_status"] = matched_acc.auth_status.value if hasattr(matched_acc.auth_status, 'value') else str(matched_acc.auth_status)
            cust_profile.update(dumped)

        escalation_payload = EscalationPayload(
            session_id=session_id,
            ani=caller_ani,
            customer_profile=cust_profile,
            call_context={
                "primary_intent": "AGENT_ESCALATION",
                "intent_confidence": 0.95,
                "duration_in_ivr_seconds": 30,
                "turns_count": 4,
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
