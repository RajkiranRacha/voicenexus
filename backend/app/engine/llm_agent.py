import json
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.config import config
from app.models.schemas import SubscriberAccount, EscalationPayload, AuthStatus
from app.services.bss_oss import bss_service
from app.services.identity import identity_service
from app.services.telecom_kb import telecom_kb_service

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_telecom_knowledge",
            "description": "Look up official guides for eSIM activation, international roaming rates, Wi-Fi password setup, router LED lights, or APN settings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword or topic, e.g. 'esim', 'roaming', 'wifi password'"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_account",
            "description": "Look up subscriber account by customer name (e.g. 'Jordan Rivera', 'Elena Vance'), account number ('ACC-992014-X', '1001'), registered phone (+1555...), billing ZIP code ('94107'), or email address ('jordan.rivera@example.com').",
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string", "description": "Customer name, account number, phone number, ZIP code, or email address"}
                },
                "required": ["identifier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_network_outage",
            "description": "Check active network outage status for a 5-digit ZIP code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {"type": "string", "description": "5-digit ZIP code"}
                },
                "required": ["zip_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_and_reboot_router",
            "description": "Diagnose line health or remotely reboot subscriber router.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {"type": "string", "description": "Customer account number"},
                    "action": {"type": "string", "enum": ["diagnose", "reboot"], "description": "diagnose or reboot"}
                },
                "required": ["account_number", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_bill_payment",
            "description": "Charge card on file to pay balance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {"type": "string", "description": "Customer account number"},
                    "amount": {"type": "number", "description": "Amount in USD"}
                },
                "required": ["account_number", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": "Transfer caller to human agent if requested or if problem cannot be resolved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for transfer"}
                },
                "required": ["reason"]
            }
        }
    }
]


class LLMAgent:
    """
    Enterprise Conversational AI IVR Dialogue Agent.
    Powered by Groq's high-speed LPU inference with function tool execution.
    Handles dynamic customer authentication from ANY phone number, telecom KB inquiries,
    self-service network diagnostics/reboot, billing actions, and human escalation.
    """

    def __init__(self, session_id: str, ani: str, account: Optional[SubscriberAccount] = None):
        self.session_id = session_id
        self.ani = ani
        self.account = account
        self.escalation_payload: Optional[EscalationPayload] = None
        self.is_escalated: bool = False
        self.should_close_call: bool = False
        self.language: str = config.LANGUAGE
        self.history: List[Dict[str, Any]] = []

        # Attempt initial ANI match if account was not already supplied
        if not self.account and self.ani:
            self.account = bss_service.get_account_by_phone(self.ani)

        self._init_system_prompt()

    def _init_system_prompt(self):
        acc_info = "None (Caller is from an unrecognized or custom mobile number)"
        if self.account:
            acc_info = (
                f"Account: {self.account.account_number}, Name: {self.account.customer_name}, "
                f"Plan: {self.account.plan_name}, Balance: ${self.account.current_balance:.2f} due {self.account.due_date}, "
                f"Card ending {self.account.payment_card_last4}, Router: {self.account.router_status}, Outage: {self.account.has_active_outage}"
            )

        system_content = (
            f"You are the Voice AI Digital Assistant for {config.OPERATOR_NAME}.\n"
            f"You are on a LIVE TELEPHONE CALL with a customer.\n"
            f"Caller ANI: {self.ani}. Verified Subscriber: {acc_info}\n\n"
            f"VOICE CALL RULES:\n"
            f"1. SPOKEN BREVITY: Reply in 1 or 2 concise spoken sentences only. Never speak essays, bullets, or lists.\n"
            f"2. NO MARKDOWN: Never use asterisks, bolding, bullet points, headers, or markdown formatting.\n"
            f"3. ANY PHONE NUMBER: If caller is unrecognized, answer general questions immediately! When they ask about personal bills, account balance, or line repair, verify them by asking for their account number, registered phone number, billing ZIP code, full name, or email.\n"
            f"4. TOOLS: When asked about eSIM, roaming rates, Wi-Fi password, router lights, or policies, ALWAYS call search_telecom_knowledge. When asked for account details or when caller provides their name, email, account number, phone number, or ZIP code, ALWAYS call lookup_account. When asked for outages, call check_network_outage.\n"
            f"5. CONFIRMATION: Always confirm with the caller before executing a payment or restarting their router.\n"
            f"6. ESCALATION: If the caller asks for a human, representative, agent, or operator, immediately call transfer_to_agent.\n"
            f"7. LANGUAGE: Respond in Spanish if the user speaks Spanish, Hindi if Hindi, otherwise English.\n"
        )

        self.history = [{"role": "system", "content": system_content}]

    def get_greeting(self) -> str:
        """Generates initial spoken greeting on call connect."""
        prefix = f"{config.REGULATORY_DISCLOSURE_PROMPT} " if config.REGULATORY_DISCLOSURE_ENABLED else ""
        if self.account:
            greeting = f"{prefix}Hello {self.account.customer_name}, thank you for calling {config.OPERATOR_NAME}! How can I help you today?"
        else:
            greeting = f"{prefix}Thank you for calling {config.OPERATOR_NAME}! How can I help you today?"
        
        self.history.append({"role": "assistant", "content": greeting})
        return greeting

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes registered Python service functions based on LLM tool call."""
        if name == "search_telecom_knowledge":
            query = args.get("query", "")
            match = telecom_kb_service.find_match(query, self.language)
            if match:
                ans = match.get("answers", {}).get(self.language[:2], match.get("answers", {}).get("en", ""))
                return {"found": True, "topic": match.get("topic"), "answer": ans}
            return {"found": False, "message": "Article not found in knowledge base."}

        elif name == "lookup_account":
            ident = args.get("identifier", "").strip()
            acc = (
                bss_service.get_account_by_phone(ident)
                or bss_service.get_account_by_number(ident)
                or bss_service.get_account_by_zip(ident)
                or bss_service.get_account_by_name(ident)
                or bss_service.get_account_by_email(ident)
                or identity_service.verify_knowledge_based(ident)
            )
            if acc:
                acc.auth_status = AuthStatus.KBA_VERIFIED
                self.account = acc
                return {
                    "found": True,
                    "account_number": acc.account_number,
                    "customer_name": acc.customer_name,
                    "plan": acc.plan_name,
                    "monthly_rate": acc.monthly_rate,
                    "balance": acc.current_balance,
                    "due_date": acc.due_date,
                    "card_last4": acc.payment_card_last4,
                    "router_status": acc.router_status,
                    "zip_code": acc.zip_code,
                    "email": acc.email,
                    "auth_status": acc.auth_status.value
                }
            return {"found": False, "message": f"No active account found for '{ident}'."}

        elif name == "check_network_outage":
            zip_code = args.get("zip_code", self.account.zip_code if self.account else "94107")
            outage = bss_service.check_outage_by_zip(zip_code)
            if outage:
                return {"has_outage": True, "region": outage.get("region"), "eta": outage.get("estimated_resolution")}
            return {"has_outage": False, "message": f"All broadband nodes in ZIP {zip_code} are normal."}

        elif name == "diagnose_and_reboot_router":
            acc_num = args.get("account_number", self.account.account_number if self.account else "")
            action = args.get("action", "diagnose")
            if action == "reboot":
                res = bss_service.bounce_router(acc_num)
                if self.account:
                    self.account.router_status = "ONLINE"
                return res
            else:
                return bss_service.diagnose_broadband_line(acc_num)

        elif name == "process_bill_payment":
            acc_num = args.get("account_number", self.account.account_number if self.account else "")
            amount = float(args.get("amount", self.account.current_balance if self.account else 0.0))
            card = self.account.payment_card_last4 if self.account else "4242"
            res = bss_service.process_card_payment(acc_num, amount, card_last4=card, idempotency_key=str(uuid.uuid4()))
            return res

        elif name == "transfer_to_agent":
            reason = args.get("reason", "Caller requested live agent")
            self.is_escalated = True
            
            transcript_snippet = [
                {"speaker": m["role"], "text": str(m.get("content", ""))}
                for m in self.history if m.get("content") and m["role"] in ("user", "assistant")
            ]

            self.escalation_payload = EscalationPayload(
                session_id=self.session_id,
                ani=self.ani,
                customer_profile=self.account.model_dump() if self.account else {"status": "UNAUTHENTICATED"},
                call_context={"ani": self.ani, "language": self.language},
                resolution_summary={
                    "status": "ESCALATED",
                    "intent": "AGENT_ESCALATION",
                    "failure_or_escalation_reason": reason,
                    "summary": f"Escalated to live agent: {reason}"
                },
                recommended_agent_queue="Tier 2 Customer Care",
                transcript_snippet=transcript_snippet
            )
            return {"status": "TRANSFERRED", "message": "Connecting to live agent now."}

        return {"error": f"Unknown tool '{name}'"}

    def _clean_spoken_text(self, text: str) -> str:
        """Strips markdown formatting so TTS sounds completely natural."""
        if not text:
            return ""
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _get_windowed_history(self) -> List[Dict[str, Any]]:
        """Maintains a lightweight sliding window: system prompt + last 6 turns."""
        if len(self.history) <= 7:
            return list(self.history)
        system_msg = self.history[0]
        recent_turns = self.history[-6:]
        return [system_msg] + recent_turns

    async def process_turn(self, user_text: str) -> Tuple[str, Optional[EscalationPayload], Optional[SubscriberAccount]]:
        """
        Processes a single conversational turn:
        User Text -> Groq Model -> Optional Tool Calls -> Final Spoken Utterance.
        """
        self.history.append({"role": "user", "content": user_text})

        # Check for knowledge-based auth verification if caller is unauthenticated
        if not self.account:
            kba_acc = identity_service.verify_knowledge_based(user_text)
            if kba_acc:
                kba_acc.auth_status = AuthStatus.KBA_VERIFIED
                self.account = kba_acc

        lowered = user_text.lower()
        if any(w in lowered for w in ["español", "spanish", "habla español"]):
            self.language = "es-US"
        elif any(w in lowered for w in ["hindi", "हिंदी", "हिन्दी"]):
            self.language = "hi-IN"

        models_to_try = [
            config.GROQ_MODEL or "qwen/qwen3.8-27b",
            "openai/gpt-oss-20b"
        ]

        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            for model_name in models_to_try:
                try:
                    for _ in range(3):
                        payload = {
                            "model": model_name,
                            "messages": self._get_windowed_history(),
                            "tools": TOOLS_SCHEMA,
                            "tool_choice": "auto",
                            "temperature": 0.2,
                            "max_tokens": 200
                        }

                        resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
                        if resp.status_code == 429:
                            print(f"[LLMAgent] Rate limit on {model_name}, trying fallback...")
                            break
                        if resp.status_code != 200:
                            print(f"[LLMAgent] Groq error ({resp.status_code}): {resp.text}")
                            break

                        choice = resp.json()["choices"][0]["message"]
                        tool_calls = choice.get("tool_calls")

                        if not tool_calls:
                            raw_text = choice.get("content", "") or ""
                            spoken_text = self._clean_spoken_text(raw_text)
                            self.history.append({"role": "assistant", "content": spoken_text})
                            return (spoken_text, self.escalation_payload, self.account)

                        self.history.append(choice)

                        for tc in tool_calls:
                            fn_name = tc["function"]["name"]
                            try:
                                fn_args = json.loads(tc["function"]["arguments"])
                            except Exception:
                                fn_args = {}
                            
                            tool_result = await self._execute_tool(fn_name, fn_args)
                            self.history.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "name": fn_name,
                                "content": json.dumps(tool_result)
                            })
                    else:
                        continue
                except Exception as e:
                    print(f"[LLMAgent] Exception on {model_name}: {e}")
                    continue

        return ("Thank you for that information. How else can I help you today?", self.escalation_payload, self.account)
