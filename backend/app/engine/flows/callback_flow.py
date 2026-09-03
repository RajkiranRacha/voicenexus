import uuid
from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount

class CallbackFlow:
    """
    Subflow for Callback Scheduling (VN-8).
    Allows callers to schedule a callback rather than waiting on hold.
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
            flow_context["step"] = "AWAITING_TIME"
            flow_context["attempted_action"] = "SCHEDULE_CALLBACK"
            response = (
                f"I can have one of our care specialists call you back at {account.phone_number}. "
                "What time window works best for you? For example, this afternoon at 2 PM, or tomorrow morning?"
            )
            return response, False, False, flow_context

        elif step == "AWAITING_TIME":
            time_pref = user_text if len(user_text.strip()) > 2 else "within the next 2 hours"
            flow_context["callback_time"] = time_pref
            flow_context["step"] = "CONFIRM_CALLBACK"
            response = (
                f"Just to confirm: our care team will call you back at {account.phone_number} on {time_pref}. "
                "Does that sound good?"
            )
            return response, False, False, flow_context

        elif step == "CONFIRM_CALLBACK":
            if any(term in lowered for term in ["yes", "sounds good", "perfect", "sure", "ok", "yeah"]):
                ref_id = f"CB-{uuid.uuid4().hex[:6].upper()}"
                flow_context["callback_ref"] = ref_id
                flow_context["step"] = "COMPLETED"
                response = (
                    f"Your callback is confirmed with ticket {ref_id}. "
                    "An agent will reach out at your requested time with your full account history ready. Have a wonderful day!"
                )
                return response, True, False, flow_context
            else:
                response = "No problem. Would you rather wait on the line to speak with an agent right now?"
                return response, False, True, flow_context

        return "I can schedule a callback for you. What time works best?", False, False, flow_context
