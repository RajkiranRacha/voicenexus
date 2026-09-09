"""
Centralized trilingual (en-US / es-US / hi-IN) message templates for the
VoiceNexus dialogue engine (state machine + flows). Every entry preserves the
exact wording that previously lived inline as if/elif branches in
app/engine/state_machine.py and app/engine/flows/*.py -- this module only
changes *where* the strings live, not what they say. Templates use
str.format() placeholders; callers supply the values via app.i18n.t(key, lang, **kwargs).
"""

STRINGS: dict[str, dict[str, str]] = {
    # -- state_machine.py: greeting -----------------------------------------
    "greeting.known_account": {
        "es": (
            "{prefix}Gracias por llamar a {operator_name}. Veo que se comunica desde la línea "
            "asociada a la cuenta de {customer_name}. Soy su asistente digital. ¿En qué le puedo ayudar hoy?"
        ),
        "hi": (
            "{prefix}{operator_name} में कॉल करने के लिए धन्यवाद। मैं {customer_name} "
            "के खाते से आपका स्वागत करता हूँ। मैं आपका डिजिटल सहायक हूँ। मैं आज आपकी क्या सहायता कर सकता हूँ?"
        ),
        "en": (
            "{prefix}Thank you for calling {operator_name}. I see you're calling from the number "
            "associated with {customer_name}'s account. I am your automated care assistant. "
            "How can I help you today?"
        ),
    },
    "greeting.unknown_ani": {
        "es": (
            "{prefix}Gracias por llamar a {operator_name}. No reconozco este número en nuestro sistema. "
            "Para consultar sus registros, por favor dígame su número de cuenta o código postal de facturación."
        ),
        "hi": (
            "{prefix}{operator_name} में कॉल करने के लिए धन्यवाद। मैं आपका डिजिटल सहायक हूँ। "
            "कृपया अपना 6-अंकों का खाता नंबर या 5-अंकों का बिलिंग पिन कोड बताएं।"
        ),
        "en": (
            "{prefix}Thank you for calling {operator_name}. I am your automated care assistant. "
            "I don't recognize the phone number you are calling from. To pull up your account records, "
            "could you please tell me your account number or 5-digit billing ZIP code?"
        ),
    },

    "wrapup.closing": {
        "es": "¡Con gusto! Nos alegra haberle ayudado a resolver su consulta. Gracias por ser cliente de NexusFiber. ¡Que tenga un excelente día! ¡Hasta luego!",
        "hi": "आपका बहुत-बहुत स्वागत है! हमें खुशी है कि आपकी समस्या का समाधान हो गया। NexusFiber Telco में कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो! अलविदा!",
        "en": "You're very welcome! We're glad your issue was resolved. Thank you for choosing NexusFiber Telco. Have a wonderful day! Goodbye.",
    },
    "gratitude.closing": {
        "es": "¡De nada! Si no necesita nada más, gracias por ser cliente de NexusFiber. ¡Que tenga un excelente día!",
        "hi": "आपका बहुत-बहुत स्वागत है! यदि आपको और सहायता की आवश्यकता नहीं है, तो NexusFiber का ग्राहक बनने के लिए धन्यवाद। आपका दिन शुभ हो!",
        "en": "You're very welcome! If there's nothing else, thank you for being a valued NexusFiber customer. Have a wonderful day!",
    },
    "gratitude.continue": {
        "es": "¡Es un placer! ¿En qué más le puedo ayudar hoy? Puede consultar su factura, plan o reportar una avería.",
        "hi": "आपका स्वागत है! आज मैं आपकी क्या सहायता कर सकता हूँ? आप बिल, प्लान या इंटरनेट समस्या की जानकारी ले सकते हैं।",
        "en": "You're very welcome! How can I assist you today? You can ask about your bill, current plan, or check for area outages.",
    },
    "acknowledgement.continue": {
        "es": "Entendido. ¿En qué le puedo ayudar hoy? Puede consultar su factura, reportar averías o verificar su plan.",
        "hi": "समझ गया। आज मैं आपकी क्या सहायता कर सकता हूँ? आप अपना बिल चेक कर सकते हैं या प्लान देख सकते हैं।",
        "en": "Understood. How can I help you today? You can check your bill, report an outage, or view your plan.",
    },
    "confirmation.continue": {
        "es": "Excelente. ¿En qué le puedo ayudar hoy? Puede preguntar por su factura, hacer un pago o reportar problemas de red.",
        "hi": "बहुत अच्छा! आज मैं आपकी क्या सहायता कर सकता हूँ? आप बिल, भुगतान या नेटवर्क की जानकारी ले सकते हैं।",
        "en": "Great! How can I help you today? You can ask about your bill, make a payment, or check for area outages.",
    },
    "rejection.closing": {
        "es": "Entendido. Si no necesita nada más, gracias por llamar a NexusFiber. ¡Que tenga un buen día!",
        "hi": "समझ गया। यदि आपको और सहायता नहीं चाहिए, तो NexusFiber में कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!",
        "en": "Understood. If there is nothing else, thank you for calling NexusFiber. Have a great day!",
    },
    "unrecognized.retry": {
        "es": "Disculpe, no le entendí bien. Le puedo ayudar con su factura, hacer un pago, verificar averías o revisar su plan.",
        "hi": "माफ़ कीजिए, मैं समझ नहीं पाया। मैं बिल चेक करने, भुगतान करने, आउटेज देखने या प्लान बदलने में मदद कर सकता हूँ।",
        "en": "I didn't quite catch that. I can help you check your bill, make a payment, check for internet outages, or review your plan. How can I assist?",
    },

    # -- billing_flow.py ------------------------------------------------------
    "billing.out_of_scope": {
        "es": (
            "Veo que está consultando sobre una solicitud especializada de facturación que requiere nuestro equipo de especialistas. "
            "Estoy preparando los detalles de su cuenta para que el agente pueda ayudarle de inmediato."
        ),
        "hi": (
            "मैं देख रहा हूँ कि आप एक विशेष बिलिंग अनुरोध के बारे में पूछ रहे हैं जिसके लिए हमारी बिलिंग विशेषज्ञ टीम की आवश्यकता है। "
            "मैं आपके खाते का विवरण तैयार कर रहा हूँ ताकि एजेंट तुरंत आपकी मदद कर सके।"
        ),
        "en": (
            "I see you are inquiring about a specialized billing request that requires our billing specialist team. "
            "I am preparing your account details so the agent can help you right away."
        ),
    },
    "billing.zero_balance": {
        "es": "Su saldo actual es $0.00. No se requiere ningún pago en este momento. ¿Puedo ayudarle con algo más hoy?",
        "hi": "आपके खाते का शेष $0.00 है। इस समय किसी भुगतान की आवश्यकता नहीं है। क्या आज मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?",
        "en": "Your account balance is currently $0.00. No payment is required at this time. Can I help you with anything else today?",
    },
    "billing.confirm_direct_payment": {
        "es": (
            "Su saldo es de ${balance:.2f}, con vencimiento el {due_date}. Tenemos su tarjeta terminada en {card_last4} registrada. "
            "Para confirmar antes de cobrar: ¿le gustaría que procese un pago único de "
            "${balance:.2f} a esta tarjeta ahora mismo?"
        ),
        "hi": (
            "आपका शेष ${balance:.2f} है, जिसकी देय तिथि {due_date} है। हमारे पास आपका कार्ड नंबर {card_last4} पर समाप्त होने वाला दर्ज है। "
            "शुल्क लेने से पहले पुष्टि करने के लिए: क्या आप चाहेंगे कि मैं इस कार्ड पर "
            "${balance:.2f} का एकमुश्त भुगतान अभी प्रोसेस करूं?"
        ),
        "en": (
            "Your balance is ${balance:.2f}, due on {due_date}. We have your card ending in {card_last4} on file. "
            "To confirm before charging: would you like me to process a one-time payment of "
            "${balance:.2f} to this card right now?"
        ),
    },
    "billing.email_statement_sent": {
        "es": "He enviado una copia detallada de su último estado de cuenta a {email}. Debería recibirlo en unos minutos. ¿Hay algo más en lo que pueda ayudarle?",
        "hi": "मैंने आपके नवीनतम बिलिंग स्टेटमेंट की एक विस्तृत प्रति {email} पर भेज दी है। आपको यह कुछ ही मिनटों में मिल जाएगी। क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?",
        "en": "I have sent an itemized copy of your latest billing statement to {email}. You should receive it within a few minutes. Is there anything else I can assist you with?",
    },
    "billing.payment_arrangement_offer": {
        "es": (
            "Su saldo actual es ${balance:.2f}, con vencimiento el {due_date}. "
            "Puedo ayudarle a programar un acuerdo de pago. ¿Qué fecha le gustaría establecer para su pago?"
        ),
        "hi": (
            "आपका वर्तमान शेष ${balance:.2f} है, जिसकी देय तिथि {due_date} है। "
            "मैं आपके लिए एक भुगतान योजना निर्धारित करने में मदद कर सकता हूँ। आप भुगतान के लिए कौन सी तारीख निर्धारित करना चाहेंगे?"
        ),
        "en": (
            "Your current balance is ${balance:.2f}, due on {due_date}. "
            "I can help you schedule a payment arrangement. What date would you like to set for your payment?"
        ),
    },
    "billing.balance_recited": {
        "es": (
            "Su saldo actual es de ${balance:.2f}, y su fecha de vencimiento es {due_date}. "
            "¿Le gustaría pagar ahora con su tarjeta registrada, establecer un acuerdo de pago, o hay algo más en su factura en lo que pueda ayudarle?"
        ),
        "hi": (
            "आपका वर्तमान खाता शेष ${balance:.2f} है, और आपकी देय तिथि {due_date} है। "
            "क्या आप अपने दर्ज कार्ड से अभी भुगतान करना चाहेंगे, एक भुगतान योजना बनाना चाहेंगे, या आपके बिल से जुड़ा कुछ और है जिसमें मैं मदद कर सकूं?"
        ),
        "en": (
            "Your current account balance is ${balance:.2f}, and your due date is {due_date}. "
            "Would you like to pay now using your card on file, set up a payment arrangement, or is there anything else with your bill I can help with?"
        ),
    },
    "billing.direct_payment_success": {
        "es": (
            "¡Listo! Su pago de ${amount:.2f} ha sido aprobado en la tarjeta terminada en {card_last4}. "
            "Su número de referencia de recibo es {transaction_id}, y su saldo actualizado es $0.00. "
            "¿Puedo ayudarle con algo más hoy?"
        ),
        "hi": (
            "सफलता! आपका ${amount:.2f} का भुगतान कार्ड नंबर {card_last4} पर स्वीकृत हो गया है। "
            "आपका रसीद संदर्भ नंबर {transaction_id} है, और आपका अपडेटेड शेष $0.00 है। "
            "क्या आज मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
        ),
        "en": (
            "Success! Your payment of ${amount:.2f} has been approved on card ending in {card_last4}. "
            "Your receipt reference number is {transaction_id}, and your updated balance is $0.00. "
            "Can I help you with anything else today?"
        ),
    },
    "billing.direct_payment_declined": {
        "es": "No se procesó ningún pago. ¿Le gustaría programar un acuerdo de pago para más adelante?",
        "hi": "कोई भुगतान प्रोसेस नहीं किया गया। क्या आप बाद के लिए भुगतान योजना बनाना चाहेंगे?",
        "en": "No payment was processed. Would you like to schedule a payment arrangement for later instead?",
    },
    "billing.direct_payment_confirm_retry": {
        "es": "Por favor confirme: ¿le gustaría que cobre ${balance:.2f} a su tarjeta terminada en {card_last4}? Por favor diga sí o no.",
        "hi": "कृपया पुष्टि करें: क्या मैं आपके कार्ड नंबर {card_last4} पर ${balance:.2f} शुल्क लूं? कृपया हाँ या नहीं कहें।",
        "en": "Please confirm: would you like me to charge ${balance:.2f} to your card ending in {card_last4}? Please say yes or no.",
    },
    "billing.confirm_payment_date": {
        "es": (
            "Para confirmar antes de programar: usted desea establecer una promesa de pago por su saldo total de "
            "${balance:.2f} para ser procesado el {chosen_date}. ¿Es correcto?"
        ),
        "hi": (
            "शेड्यूल करने से पहले पुष्टि करने के लिए: आप अपने पूरे शेष ${balance:.2f} के लिए "
            "{chosen_date} को भुगतान का वादा करना चाहते हैं। क्या यह सही है?"
        ),
        "en": (
            "To confirm before I schedule: you would like to set a payment promise for your full balance of "
            "${balance:.2f} to be processed on {chosen_date}. Is that correct?"
        ),
    },
    "billing.payment_promise_confirmed": {
        "es": (
            "Gracias. Su acuerdo de pago por ${balance:.2f} ha sido programado para el {proposed_date}. "
            "Su código de confirmación es {confirmation_code}. Su servicio permanecerá activo sin interrupciones. ¿Puedo ayudarle con algo más?"
        ),
        "hi": (
            "धन्यवाद। आपके ${balance:.2f} के भुगतान की व्यवस्था {proposed_date} के लिए निर्धारित कर दी गई है। "
            "आपका पुष्टिकरण कोड {confirmation_code} है। आपकी सेवा बिना किसी रुकावट के जारी रहेगी। क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
        ),
        "en": (
            "Thank you. Your payment arrangement for ${balance:.2f} has been scheduled for {proposed_date}. "
            "Your confirmation code is {confirmation_code}. Your service will remain uninterrupted. Can I help with anything else?"
        ),
    },
    "billing.adjust_payment_date": {
        "es": "No hay problema, vamos a ajustarlo. ¿Qué fecha prefiere para programar el pago?",
        "hi": "कोई बात नहीं, चलिए इसे ठीक करते हैं। आप भुगतान के लिए कौन सी तारीख पसंद करेंगे?",
        "en": "No problem, let's adjust that. What date would you prefer to schedule the payment for?",
    },
    "billing.confirm_payment_date_retry": {
        "es": "Por favor aclare: ¿debo confirmar y programar este acuerdo de pago? Por favor diga sí o no.",
        "hi": "कृपया स्पष्ट करें: क्या मुझे इस भुगतान व्यवस्था की पुष्टि और शेड्यूल करना चाहिए? कृपया हाँ या नहीं कहें।",
        "en": "Please clarify: should I confirm and schedule this payment arrangement for you? Please say yes or no.",
    },
    "billing.closing_thanks": {
        "es": "Gracias por ser un cliente valioso. ¡Que tenga un día maravilloso!",
        "hi": "एक महत्वपूर्ण ग्राहक होने के लिए धन्यवाद। आपका दिन शुभ हो!",
        "en": "Thank you for being a valued customer. Have a wonderful day!",
    },
    "billing.ask_payment_date": {
        "es": "¿Qué fecha le gustaría programar para ese pago?",
        "hi": "आप उस भुगतान के लिए कौन सी तारीख निर्धारित करना चाहेंगे?",
        "en": "What date would you like to schedule that payment for?",
    },
    "billing.fallback": {
        "es": "Puedo ayudarle con su saldo o establecer un acuerdo de pago. ¿Cómo le gustaría proceder?",
        "hi": "मैं आपके शेष या भुगतान व्यवस्था स्थापित करने में मदद कर सकता हूँ। आप कैसे आगे बढ़ना चाहेंगे?",
        "en": "I can assist you with your balance or setting up a payment arrangement. How would you like to proceed?",
    },
    "billing.default_next_friday": {
        "es": "el próximo viernes",
        "hi": "अगले शुक्रवार",
        "en": "next Friday",
    },

    # -- outage_triage_flow.py -------------------------------------------------
    "outage.declared": {
        "es": (
            "He revisado el estado de nuestra red para su área en {region}. "
            "Actualmente hay una interrupción de servicio confirmada debido a {reason}. "
            "Nuestro equipo de reparación ya está en el sitio, y el tiempo estimado de restauración es {eta}. "
            "¿Le gustaría recibir actualizaciones automáticas por mensaje de texto tan pronto se restablezca el servicio?"
        ),
        "hi": (
            "मैंने आपके क्षेत्र {region} में नेटवर्क की स्थिति जांची है। "
            "वर्तमान में {reason} के कारण एक पुष्ट सेवा अवरोध है। "
            "हमारी मरम्मत टीम पहले से ही मौके पर है, और अनुमानित बहाली समय {eta} है। "
            "क्या आप सेवा बहाल होते ही स्वचालित टेक्स्ट अपडेट प्राप्त करना चाहेंगे?"
        ),
        "en": (
            "I have checked our network status for your area in {region}. "
            "There is currently a confirmed service outage due to {reason}. "
            "Our repair crew is already on-site, and the estimated restoration time is {eta}. "
            "Would you like to receive automated text updates as soon as service is restored?"
        ),
    },
    "outage.degraded_signal_offer_reboot": {
        "es": (
            "No hay averías reportadas en su vecindario, pero mi diagnóstico muestra pérdida alta de paquetes "
            "en su puerta de enlace de fibra. Puedo enviar una señal remota ahora mismo para reiniciar su conexión. "
            "¿Puedo proceder con el reinicio remoto?"
        ),
        "hi": (
            "आपके पड़ोस में कोई सेवा अवरोध दर्ज नहीं है, लेकिन मेरी जांच में आपके फाइबर गेटवे पर उच्च पैकेट लॉस दिखा है। "
            "मैं अभी आपके कनेक्शन को रीफ्रेश करने के लिए एक रिमोट सिग्नल भेज सकता हूँ। "
            "क्या मैं रिमोट रीसेट के साथ आगे बढ़ूं?"
        ),
        "en": (
            "There are no reported outages in your neighborhood, but my diagnostic test shows high packet loss "
            "on your fiber gateway. I can send a remote signal right now to refresh your connection and reboot the unit. "
            "May I proceed with the remote reset?"
        ),
    },
    "outage.offer_dispatch": {
        "es": (
            "Mi diagnóstico automático muestra que su terminal óptico de fibra no responde. "
            "Ya que su conexión no tiene energía, puedo programar un técnico de campo para inspeccionar su domicilio. "
            "¿Le gustaría que reserve la próxima cita disponible mañana a las 10 AM?"
        ),
        "hi": (
            "मेरी स्वचालित जांच में पता चला है कि आपका फाइबर ऑप्टिकल टर्मिनल प्रतिक्रिया नहीं दे रहा है। "
            "चूंकि आपका कनेक्शन बंद है, मैं आपके परिसर का निरीक्षण करने के लिए एक फील्ड तकनीशियन भेज सकता हूँ। "
            "क्या मैं कल सुबह 10 बजे की अगली उपलब्ध नियुक्ति बुक करूं?"
        ),
        "en": (
            "My automated diagnostic shows your fiber optical terminal is completely unresponsive. "
            "Since your connection is unpowered, I can schedule a field technician to inspect your premises. "
            "Would you like me to book the next available appointment tomorrow at 10 AM?"
        ),
    },
    "outage.healthy_status": {
        "es": (
            "Acabo de probar su conexión de banda ancha y su terminal de fibra reporta una señal óptima sin pérdida de paquetes. "
            "¿Tiene problemas con un dispositivo específico, o le gustaría hablar con un especialista técnico?"
        ),
        "hi": (
            "मैंने अभी आपके ब्रॉडबैंड कनेक्शन का परीक्षण किया और आपका फाइबर टर्मिनल शून्य पैकेट लॉस के साथ बेहतरीन सिग्नल दिखा रहा है। "
            "क्या आपको किसी विशेष डिवाइस में समस्या हो रही है, या आप किसी तकनीकी विशेषज्ञ से बात करना चाहेंगे?"
        ),
        "en": (
            "I just tested your broadband connection and your fiber terminal is reporting optimal signal strength with zero packet loss. "
            "Are you experiencing issues with a specific device, or would you like to speak to a technical specialist?"
        ),
    },
    "outage.sms_alert_enrolled": {
        "es": (
            "Se le ha inscrito en alertas por SMS en su número móvil registrado {phone_number}. "
            "Le notificaremos de inmediato cuando el servicio se restablezca. Gracias por su paciencia, ¡que tenga un buen día!"
        ),
        "hi": (
            "आपको आपके पंजीकृत मोबाइल नंबर {phone_number} पर SMS अलर्ट के लिए नामांकित कर दिया गया है। "
            "सेवा सामान्य होते ही हम आपको तुरंत सूचित करेंगे। धैर्य के लिए धन्यवाद, आपका दिन शुभ हो!"
        ),
        "en": (
            "You have been enrolled in SMS alerts for your registered mobile number {phone_number}. "
            "We will notify you immediately when normal service resumes. Thank you for your patience, and have a good day!"
        ),
    },
    "outage.sms_alert_declined": {
        "es": "Entendido. Nuestros equipos están trabajando urgentemente para restaurar el servicio. ¿Hay algo más en lo que pueda ayudarle hoy?",
        "hi": "समझ गया। हमारी टीमें सेवा बहाल करने के लिए तत्परता से काम कर रही हैं। क्या आज मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?",
        "en": "Understood. Our crews are working urgently to restore service. Is there anything else I can help you with today?",
    },
    "outage.reboot_confirmed": {
        "es": (
            "He enviado el comando de reinicio. Su puerta de enlace de fibra se está reiniciando ahora. "
            "Las luces indicadoras cambiarán a verde en los próximos 90 segundos. "
            "¿Hay algo más que pueda revisar mientras eso se reinicia?"
        ),
        "hi": (
            "मैंने रीसेट कमांड भेज दिया है। आपका फाइबर गेटवे अब रीबूट हो रहा है। "
            "अगले 90 सेकंड में इंडिकेटर लाइट्स हरी हो जाएंगी। "
            "क्या इस बीच मैं आपके लिए कुछ और जांच सकता हूँ?"
        ),
        "en": (
            "I have sent the reset command. Your fiber gateway is now rebooting. "
            "The indicator lights will cycle green over the next 90 seconds. "
            "Is there anything else I can check for you while that restarts?"
        ),
    },
    "outage.reboot_declined_choose_next": {
        "es": "Entendido. ¿Prefiere reservar un técnico, o hablar directamente con un agente?",
        "hi": "समझ गया। क्या आप एक तकनीशियन बुक करना पसंद करेंगे, या सीधे किसी एजेंट से बात करना चाहेंगे?",
        "en": "Understood. Would you prefer to book a technician, or speak directly with an agent?",
    },
    "outage.dispatch_confirmed": {
        "es": (
            "Su cita de servicio ha sido reservada para mañana a las 10:00 AM. "
            "Su número de referencia de despacho es {dispatch_id}. Un técnico llamará 30 minutos antes de llegar. "
            "¿Puedo ayudarle con algo más?"
        ),
        "hi": (
            "आपकी सेवा नियुक्ति कल सुबह 10:00 बजे के लिए बुक कर दी गई है। "
            "आपका डिस्पैच संदर्भ नंबर {dispatch_id} है। पहुंचने से 30 मिनट पहले एक तकनीशियन कॉल करेगा। "
            "क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
        ),
        "en": (
            "Your service appointment has been booked for tomorrow at 10:00 AM. "
            "Your dispatch reference number is {dispatch_id}. A technician will call 30 minutes before arrival. "
            "Can I assist you with anything else?"
        ),
    },
    "outage.dispatch_declined": {
        "es": "Permítame conectarlo directamente con nuestro equipo de soporte técnico para ayudarle más.",
        "hi": "मुझे आपको सीधे हमारी तकनीकी सहायता टीम से जोड़ने दें ताकि वे आपकी और मदद कर सकें।",
        "en": "Let me connect you directly to our technical support team to assist you further.",
    },
    "outage.fallback": {
        "es": "Puedo ayudarle a verificar averías o ejecutar un diagnóstico de línea en su router. ¿Qué le gustaría hacer?",
        "hi": "मैं आउटेज जांचने या आपके राउटर पर लाइन डायग्नोस्टिक चलाने में मदद कर सकता हूँ। आप क्या करना चाहेंगे?",
        "en": "I can help check for outages or run a line diagnostic on your router. What would you like to do?",
    },

    # -- plan_flow.py -----------------------------------------------------------
    "plan.offer_upgrade": {
        "es": (
            "Actualmente está suscrito al plan {plan_name} por ${monthly_rate:.2f} al mes. "
            "Es elegible para nuestro plan Gigabit Pro 1000 con velocidades simétricas de 1 gigabit por $110.00 al mes, "
            "sin costos de instalación. ¿Le gustaría actualizar su servicio a Gigabit Pro?"
        ),
        "hi": (
            "आप वर्तमान में {plan_name} प्लान पर हैं, जिसकी कीमत ${monthly_rate:.2f} प्रति माह है। "
            "आप हमारे Gigabit Pro 1000 प्लान के लिए पात्र हैं, जिसमें 1 गीगाबिट की सिमेट्रिक स्पीड $110.00 प्रति माह में मिलती है, "
            "बिना किसी सेटअप शुल्क के। क्या आप Gigabit Pro में अपग्रेड करना चाहेंगे?"
        ),
        "en": (
            "You are currently subscribed to {plan_name} at ${monthly_rate:.2f} per month. "
            "You are eligible for our Gigabit Pro 1000 plan with symmetrical 1-gigabit speeds for $110.00 per month, "
            "with zero setup fees. Would you like to upgrade your service to Gigabit Pro?"
        ),
    },
    "plan.details": {
        "es": (
            "Está en nuestro plan {plan_name}, con datos de fibra ilimitados por ${monthly_rate:.2f} al mes. "
            "Su ciclo de facturación se renueva en su fecha de vencimiento. ¿Le gustaría conocer las mejoras de velocidad o revisar complementos?"
        ),
        "hi": (
            "आप हमारे {plan_name} प्लान पर हैं, जिसमें असीमित फाइबर डेटा ${monthly_rate:.2f} प्रति माह में मिलता है। "
            "आपका बिलिंग चक्र आपकी नियत तारीख पर नवीनीकृत होता है। क्या आप स्पीड अपग्रेड या ऐड-ऑन के बारे में जानना चाहेंगे?"
        ),
        "en": (
            "You are on our {plan_name} plan, with unlimited fiber data at ${monthly_rate:.2f} per month. "
            "Your billing cycle renews on your due date. Would you like to explore speed upgrades or review add-ons?"
        ),
    },
    "plan.confirm_upgrade": {
        "es": (
            "Para confirmar antes de hacer cambios en su cuenta: usted autoriza una actualización a Gigabit Pro 1000, "
            "lo que ajustará su factura mensual a $110.00 a partir de su próximo ciclo de facturación. "
            "¿Está de acuerdo con este cambio?"
        ),
        "hi": (
            "आपके खाते में बदलाव करने से पहले पुष्टि करने के लिए: आप Gigabit Pro 1000 में अपग्रेड को अधिकृत कर रहे हैं, "
            "जो आपके अगले बिलिंग चक्र से आपका मासिक बिल $110.00 कर देगा। "
            "क्या आप इस बदलाव से सहमत हैं?"
        ),
        "en": (
            "To confirm before I make changes to your account: you are authorizing an upgrade to Gigabit Pro 1000, "
            "which will adjust your monthly bill to $110.00 starting on your next billing cycle. "
            "Do you agree to this change?"
        ),
    },
    "plan.upgrade_declined": {
        "es": "No se han realizado cambios en su plan. ¿Hay algo más en lo que pueda ayudarle hoy?",
        "hi": "आपके प्लान में कोई बदलाव नहीं किया गया है। क्या आज मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?",
        "en": "No changes have been made to your plan. Is there anything else I can assist you with today?",
    },
    "plan.upgrade_success": {
        "es": (
            "¡Felicidades! Su servicio se ha actualizado con éxito a Gigabit Pro 1000. "
            "Sus nuevas velocidades estarán activas en 15 minutos. Se ha enviado un recibo de confirmación a su correo. "
            "¿Puedo ayudarle con algo más?"
        ),
        "hi": (
            "बधाई हो! आपकी सेवा सफलतापूर्वक Gigabit Pro 1000 में अपग्रेड कर दी गई है। "
            "आपकी नई स्पीड 15 मिनट में लागू हो जाएगी। एक पुष्टिकरण रसीद आपके पते पर ईमेल कर दी गई है। "
            "क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूँ?"
        ),
        "en": (
            "Congratulations! Your service has been successfully upgraded to Gigabit Pro 1000. "
            "Your new speeds will take effect within 15 minutes. A confirmation receipt has been emailed to your address. "
            "Can I help you with anything else?"
        ),
    },
    "plan.upgrade_canceled": {
        "es": "Pedido cancelado. Su plan actual permanece sin cambios. ¿En qué más le puedo ayudar?",
        "hi": "ऑर्डर रद्द कर दिया गया है। आपका मौजूदा प्लान अपरिवर्तित है। मैं और कैसे मदद कर सकता हूँ?",
        "en": "Order canceled. Your current plan remains unchanged. How else can I help you?",
    },
    "plan.fallback": {
        "es": "Puedo revisar las características de su plan actual o ayudarle a mejorar su velocidad. ¿Qué prefiere?",
        "hi": "मैं आपके वर्तमान प्लान की विशेषताएं बता सकता हूँ या आपकी स्पीड अपग्रेड करने में मदद कर सकता हूँ। आप क्या पसंद करेंगे?",
        "en": "I can review your current plan features or help you upgrade your speed. What would you prefer?",
    },

    # -- callback_flow.py ---------------------------------------------------------
    "callback.ask_time": {
        "es": (
            "Puedo hacer que uno de nuestros especialistas le devuelva la llamada al {phone_number}. "
            "¿Qué horario le conviene más? Por ejemplo, esta tarde a las 2, o mañana por la mañana."
        ),
        "hi": (
            "मैं हमारे किसी विशेषज्ञ से आपको {phone_number} पर वापस कॉल करवा सकता हूँ। "
            "आपके लिए कौन सा समय ठीक रहेगा? उदाहरण के लिए, आज दोपहर 2 बजे, या कल सुबह।"
        ),
        "en": (
            "I can have one of our care specialists call you back at {phone_number}. "
            "What time window works best for you? For example, this afternoon at 2 PM, or tomorrow morning?"
        ),
    },
    "callback.confirm_time": {
        "es": "Solo para confirmar: nuestro equipo de atención le llamará al {phone_number} el {time_pref}. ¿Le parece bien?",
        "hi": "बस पुष्टि के लिए: हमारी टीम आपको {phone_number} पर {time_pref} कॉल करेगी। क्या यह ठीक है?",
        "en": "Just to confirm: our care team will call you back at {phone_number} on {time_pref}. Does that sound good?",
    },
    "callback.confirmed": {
        "es": (
            "Su devolución de llamada está confirmada con el ticket {ref_id}. "
            "Un agente se comunicará con usted en el horario solicitado con su historial de cuenta listo. ¡Que tenga un excelente día!"
        ),
        "hi": (
            "आपकी कॉलबैक टिकट {ref_id} के साथ पुष्टि हो गई है। "
            "एक एजेंट आपके अनुरोधित समय पर आपके पूरे खाते के इतिहास के साथ संपर्क करेगा। आपका दिन शुभ हो!"
        ),
        "en": (
            "Your callback is confirmed with ticket {ref_id}. "
            "An agent will reach out at your requested time with your full account history ready. Have a wonderful day!"
        ),
    },
    "callback.declined_offer_wait": {
        "es": "Entendido, no programaremos una devolución de llamada. Le estoy conectando ahora mismo con un agente en línea.",
        "hi": "समझ गया, हम कॉलबैक शेड्यूल नहीं करेंगे। मैं अभी आपको लाइन पर एक एजेंट से जोड़ रहा हूँ।",
        "en": "Understood, no callback scheduled. I'm connecting you with an agent on the line right now.",
    },
    "callback.fallback": {
        "es": "Puedo programar una devolución de llamada para usted. ¿Qué horario le conviene?",
        "hi": "मैं आपके लिए एक कॉलबैक शेड्यूल कर सकता हूँ। कौन सा समय ठीक रहेगा?",
        "en": "I can schedule a callback for you. What time works best?",
    },
    "callback.default_time_window": {
        "es": "dentro de las próximas 2 horas",
        "hi": "अगले 2 घंटों के भीतर",
        "en": "within the next 2 hours",
    },
    "escalation.prompt": {
        "es": (
            "Quiero asegurarme de que esto se resuelva correctamente. Le estoy transfiriendo a uno de nuestros "
            "especialistas de atención en este momento. Le he enviado sus datos verificados para que no tenga que repetirlos."
        ),
        "hi": (
            "मैं यह सुनिश्चित करना चाहता हूँ कि यह सही ढंग से हल हो। मैं अभी आपको हमारे एक "
            "सहायता विशेषज्ञ से जोड़ रहा हूँ। मैंने उन्हें आपका सत्यापित विवरण भेज दिया है ताकि आपको दोहराना न पड़े।"
        ),
        "en": (
            "I want to make sure this gets resolved correctly. I am transferring you to one of our "
            "care specialists right now. I've sent them your verified details so you won't have to repeat yourself."
        ),
    },
}
