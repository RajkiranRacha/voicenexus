from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount
from app.services.bss_oss import bss_service
from app.engine.nlu_utils import is_affirmative
from app.i18n import t

class OutageTriageFlow:
    """
    Subflow for Outage Check, Broadband Line Diagnostic, and Dispatch Booking (VN-4).
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")

        # Step 1: Initial triage check
        if step == "INITIAL":
            flow_context["attempted_action"] = "OUTAGE_AND_EQUIPMENT_TRIAGE"
            # 1. Check network outage in subscriber's area
            outage_info = bss_service.check_outage_by_zip(account.zip_code)
            if outage_info:
                flow_context["step"] = "OUTAGE_DECLARED"
                flow_context["outage_info"] = outage_info
                response = t(
                    "outage.declared", language,
                    region=outage_info["region"], reason=outage_info["reason"], eta=outage_info["estimated_resolution"]
                )
                return response, False, False, flow_context

            # 2. No regional outage - diagnose subscriber router
            diag = bss_service.diagnose_broadband_line(account.account_number)
            flow_context["diagnostic"] = diag

            if diag["status"] == "DEGRADED_SIGNAL":
                flow_context["step"] = "AWAITING_REBOOT_PERMISSION"
                return t("outage.degraded_signal_offer_reboot", language), False, False, flow_context

            elif diag["status"] == "AREA_OUTAGE_DETECTED" or not diag["healthy"]:
                flow_context["step"] = "OFFER_DISPATCH"
                return t("outage.offer_dispatch", language), False, False, flow_context

            else:
                flow_context["step"] = "HEALTHY_STATUS_RECITED"
                return t("outage.healthy_status", language), False, False, flow_context

        # Step 2: Outage update opt-in
        elif step == "OUTAGE_DECLARED":
            if is_affirmative(user_text, language):
                return t("outage.sms_alert_enrolled", language, phone_number=account.phone_number), True, False, flow_context
            else:
                return t("outage.sms_alert_declined", language), True, False, flow_context

        # Step 3: Remote reboot consent
        elif step == "AWAITING_REBOOT_PERMISSION":
            if is_affirmative(user_text, language):
                bss_service.bounce_router(account.account_number)
                flow_context["step"] = "REBOOT_TRIGGERED"
                return t("outage.reboot_confirmed", language), True, False, flow_context
            else:
                flow_context["step"] = "CHOOSE_NEXT"
                return t("outage.reboot_declined_choose_next", language), False, False, flow_context

        # Step 4: Dispatch appointment
        elif step == "OFFER_DISPATCH":
            if is_affirmative(user_text, language):
                dispatch = bss_service.schedule_technician(
                    account_number=account.account_number,
                    preferred_time_slot="Tomorrow at 10:00 AM",
                    notes="Automated IVR diagnostic flagged unresponsive optical terminal."
                )
                flow_context["dispatch_id"] = dispatch["dispatch_id"]
                flow_context["step"] = "DISPATCH_CONFIRMED"
                return t("outage.dispatch_confirmed", language, dispatch_id=dispatch["dispatch_id"]), True, False, flow_context
            else:
                flow_context["escalation_reason"] = "TECH_DISPATCH_DECLINED"
                flow_context["notes"] = "Caller declined automated dispatch booking. Connecting to care agent."
                return t("outage.dispatch_declined", language), False, True, flow_context

        return t("outage.fallback", language), False, False, flow_context
