import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List

VAPI_API_BASE = "https://api.vapi.ai"
USER_AGENT = "VoiceNexus/1.0 (Windows NT 10.0; Win64; x64)"

SYSTEM_PROMPT = """You are the AI Voice Care Assistant for NexusFiber Telco.
Your job is to assist callers with their fiber internet, mobile, and account issues over the phone.

Core Rules for Voice Calls:
1. Keep replies concise: 1 to 2 spoken sentences maximum.
2. Never speak markdown, symbols, asterisks, bullet points, or JSON. Speak naturally as if speaking on a phone call.
3. Spoken Digits & Identifiers:
   - When callers speak numbers, zip codes, or account numbers (like 555, 94107, 90210, ACC-1001, ACC-992014-X), accept them naturally whether spoken as digits or words.
   - If looking up an account, you can use the caller's phone number, 5-digit zip code (e.g. 94107, 90210, 98101), or account number.
4. Unregistered Callers:
   - If an account is not found with the caller's phone number, politely ask for their 5-digit billing zip code or account number.
   - If the caller is a prospective new customer or not registered, answer their questions about fiber plans, check coverage with check_network_outage, or offer to connect them to our team.
5. If caller asks about eSIM setup, roaming, plans, billing cycles, or general questions, use the search_telecom_knowledge tool.
6. If caller asks about their balance, bill, or router, use lookup_account or diagnose_and_reboot_router.
7. If caller wants to pay, verify their account number and amount, then use process_bill_payment.
8. If caller asks to speak to a person, representative, or human specialist, use transfer_to_agent.
9. Always be polite, warm, and professional.
"""

TOOLS_CONFIG = [
    {
        "type": "function",
        "function": {
            "name": "lookup_account",
            "description": "Look up subscriber account by account_number, phone_number, or billing zip_code",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {"type": "string", "description": "e.g. ACC-992014-X"},
                    "phone_number": {"type": "string"},
                    "zip_code": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_telecom_knowledge",
            "description": "Search telecom knowledge base for questions on eSIM setup, roaming packages, 5G, Wi-Fi 6, cancellation, billing cycles",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_bill_payment",
            "description": "Process credit card payment against subscriber's outstanding balance",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {"type": "string"},
                    "amount": {"type": "number"}
                },
                "required": ["account_number", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_and_reboot_router",
            "description": "Diagnose fiber connection and send remote reset signal to customer gateway/router",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {"type": "string"}
                },
                "required": ["account_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_network_outage",
            "description": "Check for active fiber outages by zip code",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {"type": "string"}
                },
                "required": ["zip_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": "Escalate and transfer call to an online care specialist in the web portal",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"}
                },
                "required": ["reason"]
            }
        }
    }
]

def make_request(url: str, api_key: str, method: str = "GET", payload: Dict[str, Any] = None) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    if data:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"Vapi API Error ({e.code}) on {method} {url}: {err_msg}")
        raise

def get_assistants(api_key: str) -> List[Dict[str, Any]]:
    return make_request(f"{VAPI_API_BASE}/assistant", api_key, "GET")

def get_phone_numbers(api_key: str) -> List[Dict[str, Any]]:
    return make_request(f"{VAPI_API_BASE}/phone-number", api_key, "GET")

def setup_assistant(api_key: str, server_url: str) -> Dict[str, Any]:
    assistants = get_assistants(api_key)
    target_asst = None
    for a in assistants:
        name = a.get("name", "").lower()
        if "voicenexus" in name:
            target_asst = a
            break

    payload = {
        "name": "VoiceNexus AI",
        "firstMessage": "Thank you for calling NexusFiber Telco! How can I help you today?",
        "serverUrl": server_url,
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT}
            ],
            "tools": TOOLS_CONFIG
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
            "keywords": [
                "NexusFiber:3", "GigaFiber:3", "FiberConnect:2", "eSIM:3",
                "outage:2", "router:2", "555:3", "94107:3", "98101:3", "78701:3",
                "90210:3", "10001:3", "ACC:3", "ACC-992014-X:3", "ACC-1001:3"
            ]
        },
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600
    }

    if target_asst:
        asst_id = target_asst.get("id")
        print(f"Found existing assistant: {target_asst.get('name')} ({asst_id}). Updating...")
        updated = make_request(f"{VAPI_API_BASE}/assistant/{asst_id}", api_key, "PATCH", payload)
        print("Successfully updated VoiceNexus Assistant with system prompt, tools & server URL!")
        return updated
    else:
        print("Creating new VoiceNexus Assistant...")
        created = make_request(f"{VAPI_API_BASE}/assistant", api_key, "POST", payload)
        print(f"Successfully created VoiceNexus Assistant! ID: {created.get('id')}")
        return created

def setup_phone_number(api_key: str, assistant_id: str, server_url: str):
    numbers = get_phone_numbers(api_key)
    if not numbers:
        print("No phone numbers found in your Vapi account.")
        print("Go to https://dashboard.vapi.ai/phone-numbers to claim your free phone number.")
        return

    for phone in numbers:
        phone_id = phone.get("id")
        phone_num = phone.get("number")
        print(f"Configuring phone number: {phone_num} ({phone_id})...")
        payload = {
            "assistantId": assistant_id,
            "server": {"url": server_url, "timeoutSeconds": 20}
        }
        make_request(f"{VAPI_API_BASE}/phone-number/{phone_id}", api_key, "PATCH", payload)
        print(f"SUCCESS: Phone number {phone_num} is now connected to VoiceNexus AI!")

if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("VAPI_API_KEY", "")
    server_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv("VAPI_SERVER_URL", "")

    if not api_key:
        print("Usage: python setup_vapi.py <VAPI_API_KEY> <SERVER_URL>")
        sys.exit(1)

    print("=== Starting VoiceNexus Vapi Auto-Configuration ===")
    asst = setup_assistant(api_key, server_url)
    setup_phone_number(api_key, asst.get("id"), server_url)
    print("=== Setup Completed Successfully! ===")
