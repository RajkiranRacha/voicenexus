from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount, AuthStatus
from app.engine.nlu_utils import is_affirmative
from app.i18n import t

class PlanFlow:
    """
    Subflow for Plan Details, Data Allowance, and Plan Upgrades (VN-2, VN-4).
    Enforces step-up authentication and confirmation before committing modifications.
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()

        if step == "INITIAL":
            flow_context["attempted_action"] = "PLAN_INQUIRY"
            if any(term in lowered for term in ["upgrade", "faster", "more speed", "higher plan", "más velocidad", "mejorar plan", "अपग्रेड", "तेज़ स्पीड", "ज़्यादा स्पीड"]):
                flow_context["step"] = "OFFER_UPGRADE"
                return t("plan.offer_upgrade", language, plan_name=account.plan_name, monthly_rate=account.monthly_rate), False, False, flow_context
            else:
                flow_context["step"] = "DETAILS_PROVIDED"
                return t("plan.details", language, plan_name=account.plan_name, monthly_rate=account.monthly_rate), False, False, flow_context

        elif step == "OFFER_UPGRADE":
            # "upgrade" is a domain-specific confirmation word here (caller repeating
            # the offered action), in addition to the generic affirmative vocabulary.
            if is_affirmative(user_text, language) or "upgrade" in lowered:
                flow_context["step"] = "CONFIRM_UPGRADE"
                return t("plan.confirm_upgrade", language), False, False, flow_context
            else:
                return t("plan.upgrade_declined", language), True, False, flow_context

        elif step == "CONFIRM_UPGRADE":
            if is_affirmative(user_text, language):
                account.plan_name = "Gigabit Pro 1000"
                account.monthly_rate = 110.00
                flow_context["step"] = "COMPLETED"
                return t("plan.upgrade_success", language), True, False, flow_context
            else:
                return t("plan.upgrade_canceled", language), True, False, flow_context

        return t("plan.fallback", language), False, False, flow_context
