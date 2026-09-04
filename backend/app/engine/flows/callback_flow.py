import uuid
from typing import Dict, Any, Tuple
from app.models.schemas import SubscriberAccount
from app.engine.nlu_utils import is_affirmative
from app.i18n import t

class CallbackFlow:
    """
    Subflow for Callback Scheduling (VN-8).
    Allows callers to schedule a callback rather than waiting on hold.
    """

    @staticmethod
    def handle_turn(
        user_text: str,
        account: SubscriberAccount,
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")

        if step == "INITIAL":
            flow_context["step"] = "AWAITING_TIME"
            flow_context["attempted_action"] = "SCHEDULE_CALLBACK"
            return t("callback.ask_time", language, phone_number=account.phone_number), False, False, flow_context

        elif step == "AWAITING_TIME":
            time_pref = user_text if len(user_text.strip()) > 2 else t("callback.default_time_window", language)
            flow_context["callback_time"] = time_pref
            flow_context["step"] = "CONFIRM_CALLBACK"
            return t("callback.confirm_time", language, phone_number=account.phone_number, time_pref=time_pref), False, False, flow_context

        elif step == "CONFIRM_CALLBACK":
            if is_affirmative(user_text, language):
                ref_id = f"CB-{uuid.uuid4().hex[:6].upper()}"
                flow_context["callback_ref"] = ref_id
                flow_context["step"] = "COMPLETED"
                return t("callback.confirmed", language, ref_id=ref_id), True, False, flow_context
            else:
                return t("callback.declined_offer_wait", language), False, True, flow_context

        return t("callback.fallback", language), False, False, flow_context
