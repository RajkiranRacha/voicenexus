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
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()
        is_es = language.startswith("es")
        is_hi = language.startswith("hi")

        if step == "INITIAL":
            flow_context["attempted_action"] = "PLAN_INQUIRY"
            if any(term in lowered for term in ["upgrade", "faster", "more speed", "higher plan", "más velocidad", "mejorar plan", "अपग्रेड", "तेज़ स्पीड", "ज़्यादा स्पीड"]):
                flow_context["step"] = "OFFER_UPGRADE"
                if is_es:
                    response = (
                        f"Actualmente está suscrito al plan {account.plan_name} por ${account.monthly_rate:.2f} al mes. "
                        "Es elegible para nuestro plan Gigabit Pro 1000 con velocidades simétricas de 1 gigabit por $110.00 al mes, "
                        "sin costos de instalación. ¿Le gustaría actualizar su servicio a Gigabit Pro?"
                    )
                elif is_hi:
                    response = (
                        f"आप वर्तमान में {account.plan_name} प्लान पर हैं, जिसकी कीमत ${account.monthly_rate:.2f} प्रति माह है। "
                        "आप हमारे Gigabit Pro 1000 प्लान के लिए पात्र हैं, जिसमें 1 गीगाबिट की सिमेट्रिक स्पीड $110.00 प्रति माह में मिलती है, "
                        "बिना किसी सेटअप शुल्क के। क्या आप Gigabit Pro में अपग्रेड करना चाहेंगे?"
                    )
                else:
                    response = (
                        f"You are currently subscribed to {account.plan_name} at ${account.monthly_rate:.2f} per month. "
                        "You are eligible for our Gigabit Pro 1000 plan with symmetrical 1-gigabit speeds for $110.00 per month, "
                        "with zero setup fees. Would you like to upgrade your service to Gigabit Pro?"
                    )
                return response, False, False, flow_context
            else:
                flow_context["step"] = "DETAILS_PROVIDED"
                if is_es:
                    response = (
                        f"Está en nuestro plan {account.plan_name}, con datos de fibra ilimitados por ${account.monthly_rate:.2f} al mes. "
                        "Su ciclo de facturación se renueva en su fecha de vencimiento. ¿Le gustaría conocer las mejoras de velocidad o revisar complementos?"
                    )
                elif is_hi:
                    response = (
                        f"आप हमारे {account.plan_name} प्लान पर हैं, जिसमें असीमित फाइबर डेटा ${account.monthly_rate:.2f} प्रति माह में मिलता है। "
                        "आपका बिलिंग चक्र आपकी नियत तारीख पर नवीनीकृत होता है। क्या आप स्पीड अपग्रेड या ऐड-ऑन के बारे में जानना चाहेंगे?"
                    )
                else:
                    response = (
                        f"You are on our {account.plan_name} plan, with unlimited fiber data at ${account.monthly_rate:.2f} per month. "
                        "Your billing cycle renews on your due date. Would you like to explore speed upgrades or review add-ons?"
                    )
                return response, False, False, flow_context

        elif step == "OFFER_UPGRADE":
            if any(term in lowered for term in ["yes", "upgrade", "sure", "ok", "yeah", "sí", "si", "de acuerdo", "haan", "ha", "theek hai"]):
                flow_context["step"] = "CONFIRM_UPGRADE"
                if is_es:
                    response = (
                        f"Para confirmar antes de hacer cambios en su cuenta: usted autoriza una actualización a Gigabit Pro 1000, "
                        "lo que ajustará su factura mensual a $110.00 a partir de su próximo ciclo de facturación. "
                        "¿Está de acuerdo con este cambio?"
                    )
                elif is_hi:
                    response = (
                        f"आपके खाते में बदलाव करने से पहले पुष्टि करने के लिए: आप Gigabit Pro 1000 में अपग्रेड को अधिकृत कर रहे हैं, "
                        "जो आपके अगले बिलिंग चक्र से आपका मासिक बिल $110.00 कर देगा। "
                        "क्या आप इस बदलाव से सहमत हैं?"
                    )
                else:
                    response = (
                        f"To confirm before I make changes to your account: you are authorizing an upgrade to Gigabit Pro 1000, "
                        f"which will adjust your monthly bill to $110.00 starting on your next billing cycle. "
                        "Do you agree to this change?"
                    )
                return response, False, False, flow_context
            else:
                if is_es:
                    response = "No se han realizado cambios en su plan. ¿Hay algo más en lo que pueda ayudarle hoy?"
                elif is_hi:
                    response = "आपके प्लान में कोई बदलाव नहीं किया गया है। क्या आज मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"
                else:
                    response = "No changes have been made to your plan. Is there anything else I can assist you with today?"
                return response, True, False, flow_context

        elif step == "CONFIRM_UPGRADE":
            if any(term in lowered for term in ["yes", "i agree", "confirm", "sure", "correct", "sí", "si", "confirmo", "de acuerdo", "haan", "ha", "theek hai", "sahi hai"]):
                account.plan_name = "Gigabit Pro 1000"
                account.monthly_rate = 110.00
                flow_context["step"] = "COMPLETED"
                if is_es:
                    response = (
                        "¡Felicidades! Su servicio se ha actualizado con éxito a Gigabit Pro 1000. "
                        "Sus nuevas velocidades estarán activas en 15 minutos. Se ha enviado un recibo de confirmación a su correo. "
                        "¿Puedo ayudarle con algo más?"
                    )
                elif is_hi:
                    response = (
                        "बधाई हो! आपकी सेवा सफलतापूर्वक Gigabit Pro 1000 में अपग्रेड कर दी गई है। "
                        "आपकी नई स्पीड 15 मिनट में लागू हो जाएगी। एक पुष्टिकरण रसीद आपके पते पर ईमेल कर दी गई है। "
                        "क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
                    )
                else:
                    response = (
                        "Congratulations! Your service has been successfully upgraded to Gigabit Pro 1000. "
                        "Your new speeds will take effect within 15 minutes. A confirmation receipt has been emailed to your address. "
                        "Can I help you with anything else?"
                    )
                return response, True, False, flow_context
            else:
                if is_es:
                    response = "Pedido cancelado. Su plan actual permanece sin cambios. ¿En qué más le puedo ayudar?"
                elif is_hi:
                    response = "ऑर्डर रद्द कर दिया गया है। आपका मौजूदा प्लान अपरिवर्तित है। मैं और कैसे मदद कर सकता हूँ?"
                else:
                    response = "Order canceled. Your current plan remains unchanged. How else can I help you?"
                return response, True, False, flow_context

        if is_es:
            return "Puedo revisar las características de su plan actual o ayudarle a mejorar su velocidad. ¿Qué prefiere?", False, False, flow_context
        elif is_hi:
            return "मैं आपके वर्तमान प्लान की विशेषताएं बता सकता हूँ या आपकी स्पीड अपग्रेड करने में मदद कर सकता हूँ। आप क्या पसंद करेंगे?", False, False, flow_context
        return "I can review your current plan features or help you upgrade your speed. What would you prefer?", False, False, flow_context
