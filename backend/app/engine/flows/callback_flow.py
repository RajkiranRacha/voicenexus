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
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()
        is_es = language.startswith("es")
        is_hi = language.startswith("hi")

        if step == "INITIAL":
            flow_context["step"] = "AWAITING_TIME"
            flow_context["attempted_action"] = "SCHEDULE_CALLBACK"
            if is_es:
                response = (
                    f"Puedo hacer que uno de nuestros especialistas le devuelva la llamada al {account.phone_number}. "
                    "¿Qué horario le conviene más? Por ejemplo, esta tarde a las 2, o mañana por la mañana."
                )
            elif is_hi:
                response = (
                    f"मैं हमारे किसी विशेषज्ञ से आपको {account.phone_number} पर वापस कॉल करवा सकता हूँ। "
                    "आपके लिए कौन सा समय ठीक रहेगा? उदाहरण के लिए, आज दोपहर 2 बजे, या कल सुबह।"
                )
            else:
                response = (
                    f"I can have one of our care specialists call you back at {account.phone_number}. "
                    "What time window works best for you? For example, this afternoon at 2 PM, or tomorrow morning?"
                )
            return response, False, False, flow_context

        elif step == "AWAITING_TIME":
            time_pref = user_text if len(user_text.strip()) > 2 else (
                "dentro de las próximas 2 horas" if is_es else
                "अगले 2 घंटों के भीतर" if is_hi else
                "within the next 2 hours"
            )
            flow_context["callback_time"] = time_pref
            flow_context["step"] = "CONFIRM_CALLBACK"
            if is_es:
                response = (
                    f"Solo para confirmar: nuestro equipo de atención le llamará al {account.phone_number} el {time_pref}. "
                    "¿Le parece bien?"
                )
            elif is_hi:
                response = (
                    f"बस पुष्टि के लिए: हमारी टीम आपको {account.phone_number} पर {time_pref} कॉल करेगी। "
                    "क्या यह ठीक है?"
                )
            else:
                response = (
                    f"Just to confirm: our care team will call you back at {account.phone_number} on {time_pref}. "
                    "Does that sound good?"
                )
            return response, False, False, flow_context

        elif step == "CONFIRM_CALLBACK":
            affirmatives = ["yes", "sounds good", "perfect", "sure", "ok", "yeah",
                            "sí", "si", "perfecto", "de acuerdo", "vale",
                            "haan", "ha", "theek hai", "thik hai", "sahi hai"]
            if any(term in lowered for term in affirmatives):
                ref_id = f"CB-{uuid.uuid4().hex[:6].upper()}"
                flow_context["callback_ref"] = ref_id
                flow_context["step"] = "COMPLETED"
                if is_es:
                    response = (
                        f"Su devolución de llamada está confirmada con el ticket {ref_id}. "
                        "Un agente se comunicará con usted en el horario solicitado con su historial de cuenta listo. ¡Que tenga un excelente día!"
                    )
                elif is_hi:
                    response = (
                        f"आपकी कॉलबैक टिकट {ref_id} के साथ पुष्टि हो गई है। "
                        "एक एजेंट आपके अनुरोधित समय पर आपके पूरे खाते के इतिहास के साथ संपर्क करेगा। आपका दिन शुभ हो!"
                    )
                else:
                    response = (
                        f"Your callback is confirmed with ticket {ref_id}. "
                        "An agent will reach out at your requested time with your full account history ready. Have a wonderful day!"
                    )
                return response, True, False, flow_context
            else:
                if is_es:
                    response = "Entendido. ¿Prefiere esperar en línea para hablar con un agente ahora mismo?"
                elif is_hi:
                    response = "समझ गया। क्या आप अभी लाइन पर रुककर किसी एजेंट से बात करना पसंद करेंगे?"
                else:
                    response = "No problem. Would you rather wait on the line to speak with an agent right now?"
                return response, False, True, flow_context

        if is_es:
            return "Puedo programar una devolución de llamada para usted. ¿Qué horario le conviene?", False, False, flow_context
        elif is_hi:
            return "मैं आपके लिए एक कॉलबैक शेड्यूल कर सकता हूँ। कौन सा समय ठीक रहेगा?", False, False, flow_context
        return "I can schedule a callback for you. What time works best?", False, False, flow_context
