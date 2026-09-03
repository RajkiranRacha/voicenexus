from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount
from app.services.bss_oss import bss_service

class OutageTriageFlow:
    """
    Subflow for Outage Check, Broadband Line Diagnostic, and Dispatch Booking (VN-4).
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any]
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()

        # Step 1: Initial triage check
        if step == "INITIAL":
            flow_context["attempted_action"] = "OUTAGE_AND_EQUIPMENT_TRIAGE"
            # 1. Check network outage in subscriber's area
            outage_info = bss_service.check_outage_by_zip(account.zip_code)
            if outage_info:
                flow_context["step"] = "OUTAGE_DECLARED"
                flow_context["outage_info"] = outage_info
                response = (
                    f"I have checked our network status for your area in {outage_info['region']}. "
                    f"There is currently a confirmed service outage due to {outage_info['reason']}. "
                    f"Our repair crew is already on-site, and the estimated restoration time is {outage_info['estimated_resolution']}. "
                    "Would you like to receive automated text updates as soon as service is restored?"
                )
                return response, False, False, flow_context

            # 2. No regional outage - diagnose subscriber router
            diag = bss_service.diagnose_broadband_line(account.account_number)
            flow_context["diagnostic"] = diag

            if diag["status"] == "DEGRADED_SIGNAL":
                flow_context["step"] = "AWAITING_REBOOT_PERMISSION"
                response = (
                    "There are no reported outages in your neighborhood, but my diagnostic test shows high packet loss "
                    "on your fiber gateway. I can send a remote signal right now to refresh your connection and reboot the unit. "
                    "May I proceed with the remote reset?"
                )
                return response, False, False, flow_context

            elif diag["status"] == "AREA_OUTAGE_DETECTED" or not diag["healthy"]:
                flow_context["step"] = "OFFER_DISPATCH"
                response = (
                    "My automated diagnostic shows your fiber optical terminal is completely unresponsive. "
                    "Since your connection is unpowered, I can schedule a field technician to inspect your premises. "
                    "Would you like me to book the next available appointment tomorrow at 10 AM?"
                )
                return response, False, False, flow_context

            else:
                flow_context["step"] = "HEALTHY_STATUS_RECITED"
                response = (
                    "I just tested your broadband connection and your fiber terminal is reporting optimal signal strength with zero packet loss. "
                    "Are you experiencing issues with a specific device, or would you like to speak to a technical specialist?"
                )
                return response, False, False, flow_context

        # Step 2: Outage update opt-in
        elif step == "OUTAGE_DECLARED":
            if any(term in lowered for term in ["yes", "sure", "please", "yep", "yeah"]):
                response = (
                    f"You have been enrolled in SMS alerts for your registered mobile number {account.phone_number}. "
                    "We will notify you immediately when normal service resumes. Thank you for your patience, and have a good day!"
                )
                return response, True, False, flow_context
            else:
                response = "Understood. Our crews are working urgently to restore service. Is there anything else I can help you with today?"
                return response, True, False, flow_context

        # Step 3: Remote reboot consent
        elif step == "AWAITING_REBOOT_PERMISSION":
            if any(term in lowered for term in ["yes", "sure", "go ahead", "ok", "yep", "please"]):
                bss_service.bounce_router(account.account_number)
                flow_context["step"] = "REBOOT_TRIGGERED"
                response = (
                    "I have sent the reset command. Your fiber gateway is now rebooting. "
                    "The indicator lights will cycle green over the next 90 seconds. "
                    "Is there anything else I can check for you while that restarts?"
                )
                return response, True, False, flow_context
            else:
                response = "Understood. Would you prefer to book a technician, or speak directly with an agent?"
                flow_context["step"] = "CHOOSE_NEXT"
                return response, False, False, flow_context

        # Step 4: Dispatch appointment
        elif step == "OFFER_DISPATCH":
            if any(term in lowered for term in ["yes", "sure", "book", "schedule", "tomorrow", "ok"]):
                dispatch = bss_service.schedule_technician(
                    account_number=account.account_number,
                    preferred_time_slot="Tomorrow at 10:00 AM",
                    notes="Automated IVR diagnostic flagged unresponsive optical terminal."
                )
                flow_context["dispatch_id"] = dispatch["dispatch_id"]
                flow_context["step"] = "DISPATCH_CONFIRMED"
                response = (
                    f"Your service appointment has been booked for tomorrow at 10:00 AM. "
                    f"Your dispatch reference number is {dispatch['dispatch_id']}. A technician will call 30 minutes before arrival. "
                    "Can I assist you with anything else?"
                )
                return response, True, False, flow_context
            else:
                flow_context["escalation_reason"] = "TECH_DISPATCH_DECLINED"
                flow_context["notes"] = "Caller declined automated dispatch booking. Connecting to care agent."
                response = "Let me connect you directly to our technical support team to assist you further."
                return response, False, True, flow_context

        return "I can help check for outages or run a line diagnostic on your router. What would you like to do?", False, False, flow_context
