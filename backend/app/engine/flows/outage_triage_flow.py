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
        flow_context: Dict[str, Any],
        language: str = "en-US"
    ) -> Tuple[str, bool, bool, Dict[str, Any]]:
        step = flow_context.get("step", "INITIAL")
        lowered = user_text.lower()
        is_es = language.startswith("es")
        is_hi = language.startswith("hi")
        affirmatives = ["yes", "sure", "please", "yep", "yeah", "ok", "go ahead", "book", "schedule", "tomorrow",
                        "sí", "si", "por favor", "claro", "de acuerdo", "adelante", "mañana",
                        "haan", "ha", "theek hai", "sahi hai", "kal"]

        # Step 1: Initial triage check
        if step == "INITIAL":
            flow_context["attempted_action"] = "OUTAGE_AND_EQUIPMENT_TRIAGE"
            # 1. Check network outage in subscriber's area
            outage_info = bss_service.check_outage_by_zip(account.zip_code)
            if outage_info:
                flow_context["step"] = "OUTAGE_DECLARED"
                flow_context["outage_info"] = outage_info
                if is_es:
                    response = (
                        f"He revisado el estado de nuestra red para su área en {outage_info['region']}. "
                        f"Actualmente hay una interrupción de servicio confirmada debido a {outage_info['reason']}. "
                        f"Nuestro equipo de reparación ya está en el sitio, y el tiempo estimado de restauración es {outage_info['estimated_resolution']}. "
                        "¿Le gustaría recibir actualizaciones automáticas por mensaje de texto tan pronto se restablezca el servicio?"
                    )
                elif is_hi:
                    response = (
                        f"मैंने आपके क्षेत्र {outage_info['region']} में नेटवर्क की स्थिति जांची है। "
                        f"वर्तमान में {outage_info['reason']} के कारण एक पुष्ट सेवा अवरोध है। "
                        f"हमारी मरम्मत टीम पहले से ही मौके पर है, और अनुमानित बहाली समय {outage_info['estimated_resolution']} है। "
                        "क्या आप सेवा बहाल होते ही स्वचालित टेक्स्ट अपडेट प्राप्त करना चाहेंगे?"
                    )
                else:
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
                if is_es:
                    response = (
                        "No hay averías reportadas en su vecindario, pero mi diagnóstico muestra pérdida alta de paquetes "
                        "en su puerta de enlace de fibra. Puedo enviar una señal remota ahora mismo para reiniciar su conexión. "
                        "¿Puedo proceder con el reinicio remoto?"
                    )
                elif is_hi:
                    response = (
                        "आपके पड़ोस में कोई सेवा अवरोध दर्ज नहीं है, लेकिन मेरी जांच में आपके फाइबर गेटवे पर उच्च पैकेट लॉस दिखा है। "
                        "मैं अभी आपके कनेक्शन को रीफ्रेश करने के लिए एक रिमोट सिग्नल भेज सकता हूँ। "
                        "क्या मैं रिमोट रीसेट के साथ आगे बढ़ूं?"
                    )
                else:
                    response = (
                        "There are no reported outages in your neighborhood, but my diagnostic test shows high packet loss "
                        "on your fiber gateway. I can send a remote signal right now to refresh your connection and reboot the unit. "
                        "May I proceed with the remote reset?"
                    )
                return response, False, False, flow_context

            elif diag["status"] == "AREA_OUTAGE_DETECTED" or not diag["healthy"]:
                flow_context["step"] = "OFFER_DISPATCH"
                if is_es:
                    response = (
                        "Mi diagnóstico automático muestra que su terminal óptico de fibra no responde. "
                        "Ya que su conexión no tiene energía, puedo programar un técnico de campo para inspeccionar su domicilio. "
                        "¿Le gustaría que reserve la próxima cita disponible mañana a las 10 AM?"
                    )
                elif is_hi:
                    response = (
                        "मेरी स्वचालित जांच में पता चला है कि आपका फाइबर ऑप्टिकल टर्मिनल प्रतिक्रिया नहीं दे रहा है। "
                        "चूंकि आपका कनेक्शन बंद है, मैं आपके परिसर का निरीक्षण करने के लिए एक फील्ड तकनीशियन भेज सकता हूँ। "
                        "क्या मैं कल सुबह 10 बजे की अगली उपलब्ध नियुक्ति बुक करूं?"
                    )
                else:
                    response = (
                        "My automated diagnostic shows your fiber optical terminal is completely unresponsive. "
                        "Since your connection is unpowered, I can schedule a field technician to inspect your premises. "
                        "Would you like me to book the next available appointment tomorrow at 10 AM?"
                    )
                return response, False, False, flow_context

            else:
                flow_context["step"] = "HEALTHY_STATUS_RECITED"
                if is_es:
                    response = (
                        "Acabo de probar su conexión de banda ancha y su terminal de fibra reporta una señal óptima sin pérdida de paquetes. "
                        "¿Tiene problemas con un dispositivo específico, o le gustaría hablar con un especialista técnico?"
                    )
                elif is_hi:
                    response = (
                        "मैंने अभी आपके ब्रॉडबैंड कनेक्शन का परीक्षण किया और आपका फाइबर टर्मिनल शून्य पैकेट लॉस के साथ बेहतरीन सिग्नल दिखा रहा है। "
                        "क्या आपको किसी विशेष डिवाइस में समस्या हो रही है, या आप किसी तकनीकी विशेषज्ञ से बात करना चाहेंगे?"
                    )
                else:
                    response = (
                        "I just tested your broadband connection and your fiber terminal is reporting optimal signal strength with zero packet loss. "
                        "Are you experiencing issues with a specific device, or would you like to speak to a technical specialist?"
                    )
                return response, False, False, flow_context

        # Step 2: Outage update opt-in
        elif step == "OUTAGE_DECLARED":
            if any(term in lowered for term in affirmatives):
                if is_es:
                    response = (
                        f"Se le ha inscrito en alertas por SMS en su número móvil registrado {account.phone_number}. "
                        "Le notificaremos de inmediato cuando el servicio se restablezca. Gracias por su paciencia, ¡que tenga un buen día!"
                    )
                elif is_hi:
                    response = (
                        f"आपको आपके पंजीकृत मोबाइल नंबर {account.phone_number} पर SMS अलर्ट के लिए नामांकित कर दिया गया है। "
                        "सेवा सामान्य होते ही हम आपको तुरंत सूचित करेंगे। धैर्य के लिए धन्यवाद, आपका दिन शुभ हो!"
                    )
                else:
                    response = (
                        f"You have been enrolled in SMS alerts for your registered mobile number {account.phone_number}. "
                        "We will notify you immediately when normal service resumes. Thank you for your patience, and have a good day!"
                    )
                return response, True, False, flow_context
            else:
                if is_es:
                    response = "Entendido. Nuestros equipos están trabajando urgentemente para restaurar el servicio. ¿Hay algo más en lo que pueda ayudarle hoy?"
                elif is_hi:
                    response = "समझ गया। हमारी टीमें सेवा बहाल करने के लिए तत्परता से काम कर रही हैं। क्या आज मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
                else:
                    response = "Understood. Our crews are working urgently to restore service. Is there anything else I can help you with today?"
                return response, True, False, flow_context

        # Step 3: Remote reboot consent
        elif step == "AWAITING_REBOOT_PERMISSION":
            if any(term in lowered for term in affirmatives):
                bss_service.bounce_router(account.account_number)
                flow_context["step"] = "REBOOT_TRIGGERED"
                if is_es:
                    response = (
                        "He enviado el comando de reinicio. Su puerta de enlace de fibra se está reiniciando ahora. "
                        "Las luces indicadoras cambiarán a verde en los próximos 90 segundos. "
                        "¿Hay algo más que pueda revisar mientras eso se reinicia?"
                    )
                elif is_hi:
                    response = (
                        "मैंने रीसेट कमांड भेज दिया है। आपका फाइबर गेटवे अब रीबूट हो रहा है। "
                        "अगले 90 सेकंड में इंडिकेटर लाइट्स हरी हो जाएंगी। "
                        "क्या इस बीच मैं आपके लिए कुछ और जांच सकता हूँ?"
                    )
                else:
                    response = (
                        "I have sent the reset command. Your fiber gateway is now rebooting. "
                        "The indicator lights will cycle green over the next 90 seconds. "
                        "Is there anything else I can check for you while that restarts?"
                    )
                return response, True, False, flow_context
            else:
                flow_context["step"] = "CHOOSE_NEXT"
                if is_es:
                    response = "Entendido. ¿Prefiere reservar un técnico, o hablar directamente con un agente?"
                elif is_hi:
                    response = "समझ गया। क्या आप एक तकनीशियन बुक करना पसंद करेंगे, या सीधे किसी एजेंट से बात करना चाहेंगे?"
                else:
                    response = "Understood. Would you prefer to book a technician, or speak directly with an agent?"
                return response, False, False, flow_context

        # Step 4: Dispatch appointment
        elif step == "OFFER_DISPATCH":
            if any(term in lowered for term in affirmatives):
                dispatch = bss_service.schedule_technician(
                    account_number=account.account_number,
                    preferred_time_slot="Tomorrow at 10:00 AM",
                    notes="Automated IVR diagnostic flagged unresponsive optical terminal."
                )
                flow_context["dispatch_id"] = dispatch["dispatch_id"]
                flow_context["step"] = "DISPATCH_CONFIRMED"
                if is_es:
                    response = (
                        f"Su cita de servicio ha sido reservada para mañana a las 10:00 AM. "
                        f"Su número de referencia de despacho es {dispatch['dispatch_id']}. Un técnico llamará 30 minutos antes de llegar. "
                        "¿Puedo ayudarle con algo más?"
                    )
                elif is_hi:
                    response = (
                        f"आपकी सेवा नियुक्ति कल सुबह 10:00 बजे के लिए बुक कर दी गई है। "
                        f"आपका डिस्पैच संदर्भ नंबर {dispatch['dispatch_id']} है। पहुंचने से 30 मिनट पहले एक तकनीशियन कॉल करेगा। "
                        "क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
                    )
                else:
                    response = (
                        f"Your service appointment has been booked for tomorrow at 10:00 AM. "
                        f"Your dispatch reference number is {dispatch['dispatch_id']}. A technician will call 30 minutes before arrival. "
                        "Can I assist you with anything else?"
                    )
                return response, True, False, flow_context
            else:
                flow_context["escalation_reason"] = "TECH_DISPATCH_DECLINED"
                flow_context["notes"] = "Caller declined automated dispatch booking. Connecting to care agent."
                if is_es:
                    response = "Permítame conectarlo directamente con nuestro equipo de soporte técnico para ayudarle más."
                elif is_hi:
                    response = "मुझे आपको सीधे हमारी तकनीकी सहायता टीम से जोड़ने दें ताकि वे आपकी और मदद कर सकें।"
                else:
                    response = "Let me connect you directly to our technical support team to assist you further."
                return response, False, True, flow_context

        if is_es:
            return "Puedo ayudarle a verificar averías o ejecutar un diagnóstico de línea en su router. ¿Qué le gustaría hacer?", False, False, flow_context
        elif is_hi:
            return "मैं आउटेज जांचने या आपके राउटर पर लाइन डायग्नोस्टिक चलाने में मदद कर सकता हूँ। आप क्या करना चाहेंगे?", False, False, flow_context
        return "I can help check for outages or run a line diagnostic on your router. What would you like to do?", False, False, flow_context
