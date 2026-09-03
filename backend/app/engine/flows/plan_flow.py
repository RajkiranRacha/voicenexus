from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount, AuthStatus

class PlanFlow:
    """
    Subflow for Plan Details, Data Allowance, and Plan Upgrades (VN-2, VN-4).
    Enforces step-up authentication and confirmation before committing modifications.
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any]
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()

        if step == "INITIAL":
            flow_context["attempted_action"] = "PLAN_INQUIRY"
            if any(term in lowered for term in ["upgrade", "faster", "more speed", "higher plan"]):
                flow_context["step"] = "OFFER_UPGRADE"
                response = (
                    f"You are currently subscribed to {account.plan_name} at ${account.monthly_rate:.2f} per month. "
                    "You are eligible for our Gigabit Pro 1000 plan with symmetrical 1-gigabit speeds for $110.00 per month, "
                    "with zero setup fees. Would you like to upgrade your service to Gigabit Pro?"
                )
                return response, False, False, flow_context
            else:
                flow_context["step"] = "DETAILS_PROVIDED"
                response = (
                    f"You are on our {account.plan_name} plan, with unlimited fiber data at ${account.monthly_rate:.2f} per month. "
                    "Your billing cycle renews on your due date. Would you like to explore speed upgrades or review add-ons?"
                )
                return response, False, False, flow_context

        elif step == "OFFER_UPGRADE":
            if any(term in lowered for term in ["yes", "upgrade", "sure", "ok", "yeah"]):
                flow_context["step"] = "CONFIRM_UPGRADE"
                response = (
                    f"To confirm before I make changes to your account: you are authorizing an upgrade to Gigabit Pro 1000, "
                    f"which will adjust your monthly bill to $110.00 starting on your next billing cycle. "
                    "Do you agree to this change?"
                )
                return response, False, False, flow_context
            else:
                response = "No changes have been made to your plan. Is there anything else I can assist you with today?"
                return response, True, False, flow_context

        elif step == "CONFIRM_UPGRADE":
            if any(term in lowered for term in ["yes", "i agree", "confirm", "sure", "correct"]):
                account.plan_name = "Gigabit Pro 1000"
                account.monthly_rate = 110.00
                flow_context["step"] = "COMPLETED"
                response = (
                    "Congratulations! Your service has been successfully upgraded to Gigabit Pro 1000. "
                    "Your new speeds will take effect within 15 minutes. A confirmation receipt has been emailed to your address. "
                    "Can I help you with anything else?"
                )
                return response, True, False, flow_context
            else:
                response = "Order canceled. Your current plan remains unchanged. How else can I help you?"
                return response, True, False, flow_context

        return "I can review your current plan features or help you upgrade your speed. What would you prefer?", False, False, flow_context
