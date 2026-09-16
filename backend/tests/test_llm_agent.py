import pytest
import asyncio
from app.engine.llm_agent import LLMAgent
from app.engine.orchestrator import DialogueOrchestrator
from app.services.bss_oss import bss_service
from app.config import config

@pytest.mark.asyncio
async def test_llm_agent_initialization_known_ani():
    agent = LLMAgent(session_id="test-known", ani="+15550192834")
    assert agent.account is not None
    assert agent.account.customer_name == "Jordan Rivera"
    greeting = agent.get_greeting()
    assert "Jordan" in greeting

@pytest.mark.asyncio
async def test_llm_agent_initialization_unknown_ani():
    agent = LLMAgent(session_id="test-unknown", ani="+919876543210")
    assert agent.account is None
    greeting = agent.get_greeting()
    assert "NexusFiber" in greeting
    assert "Jordan" not in greeting

@pytest.mark.asyncio
async def test_llm_agent_tools_execution():
    agent = LLMAgent(session_id="test-tools", ani="+919876543210")

    # 1. search_telecom_knowledge
    kb_res = await agent._execute_tool("search_telecom_knowledge", {"query": "esim"})
    assert kb_res["found"] is True
    assert "eSIM" in kb_res["topic"]

    # 2. lookup_account by account number
    acc_res = await agent._execute_tool("lookup_account", {"identifier": "ACC-992014-X"})
    assert acc_res["found"] is True
    assert acc_res["customer_name"] == "Jordan Rivera"
    assert agent.account is not None

    # 2b. lookup_account by customer name
    name_res = await agent._execute_tool("lookup_account", {"identifier": "Elena Vance"})
    assert name_res["found"] is True
    assert name_res["account_number"] == "ACC-881230-B"

    # 2c. lookup_account by email
    email_res = await agent._execute_tool("lookup_account", {"identifier": "sam.taylor@example.com"})
    assert email_res["found"] is True
    assert email_res["customer_name"] == "Sam Taylor"

    # 2d. lookup_account by 4-digit account number
    acc4_res = await agent._execute_tool("lookup_account", {"identifier": "1001"})
    assert acc4_res["found"] is True
    assert acc4_res["customer_name"] == "Sam Taylor"

    # 2e. lookup_account by phone number
    phone_res = await agent._execute_tool("lookup_account", {"identifier": "555-010-2002"})
    assert phone_res["found"] is True
    assert phone_res["customer_name"] == "Alex Morgan"

    # 2f. lookup_account by billing zip code
    zip_res = await agent._execute_tool("lookup_account", {"identifier": "78701"})
    assert zip_res["found"] is True
    assert zip_res["customer_name"] == "Marcus Brody"

    # 3. check_network_outage
    outage_res = await agent._execute_tool("check_network_outage", {"zip_code": "98101"})
    assert outage_res["has_outage"] is True

    # 4. transfer_to_agent
    esc_res = await agent._execute_tool("transfer_to_agent", {"reason": "User requested human"})
    assert esc_res["status"] == "TRANSFERRED"
    assert agent.is_escalated is True
    assert agent.escalation_payload is not None
    assert agent.escalation_payload.call_context.get("primary_intent") == "AGENT_ESCALATION"
    assert "customer_name" in agent.escalation_payload.customer_profile
    assert "notes" in agent.escalation_payload.resolution_summary
    assert "current_balance" in agent.escalation_payload.resolution_summary

def test_clean_spoken_text():
    agent = LLMAgent(session_id="test-clean", ani="+15550192834")
    raw = "**Hello!** Here is what you need to know:\n* Step 1\n* Step 2\nClick [here](https://example.com) for info."
    cleaned = agent._clean_spoken_text(raw)
    assert "**" not in cleaned
    assert "*" not in cleaned
    assert "https://" not in cleaned
    assert "Hello!" in cleaned

@pytest.mark.asyncio
async def test_orchestrator_integration_with_llm():
    orch = DialogueOrchestrator(session_id="test-orch", ani="+919876543210")
    session_data = await orch.start_session()
    assert session_data["type"] == "SESSION_STARTED"
    assert session_data["turn"]["speaker"] == "ai"
    assert len(session_data["turn"]["text"]) > 0
