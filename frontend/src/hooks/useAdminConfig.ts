import { useState, useEffect, useCallback } from 'react';
import { apiGet, apiPost } from '../api/client';
import type { AdminConfigData } from '../types';

const LOCAL_STORAGE_KEY = 'voicenexus_admin_config';

export interface PronunciationRule {
  pattern: string;
  replace: string;
}

/** Encapsulates AdminConfig's localStorage+server hydration, pronunciation-rule CRUD, and save flow. */
function getCachedConfig(): Record<string, any> | null {
  try {
    const cached = localStorage.getItem(LOCAL_STORAGE_KEY);
    return cached ? JSON.parse(cached) : null;
  } catch {
    return null;
  }
}

export function useAdminConfig() {
  const cached = getCachedConfig();
  const [operatorName, setOperatorName] = useState<string>(cached?.operator_name || "NexusFiber Telco");
  const [greetingPrompt, setGreetingPrompt] = useState<string>(
    cached?.greeting_prompt || "Thank you for calling NexusFiber Care. I am your automated digital assistant. How can I help you today?"
  );
  const [spanishGreeting, setSpanishGreeting] = useState<string>(
    cached?.spanish_greeting_prompt || "Gracias por llamar a NexusFiber Atención al Cliente. Soy su asistente digital automatizado. ¿Cómo le puedo ayudar hoy?"
  );
  const [hindiGreeting, setHindiGreeting] = useState<string>(
    cached?.hindi_greeting_prompt || "NexusFiber में कॉल करने के लिए धन्यवाद। मैं आपका स्वचालित डिजिटल सहायक हूँ। मैं आज आपकी क्या सहायता कर सकता हूँ?"
  );
  const [holdPrompt, setHoldPrompt] = useState<string>(
    "Please hold for just a moment while I pull up your account records."
  );
  const [closePrompt, setClosePrompt] = useState<string>(
    "Thank you for being a valued NexusFiber customer. Have a great day!"
  );
  const [escalationPrompt, setEscalationPrompt] = useState<string>(
    "I want to make sure this gets resolved correctly. I am transferring you to one of our care specialists right now. I've sent them your verified details so you won't have to repeat yourself."
  );
  const [disclosureEnabled, setDisclosureEnabled] = useState<boolean>(true);
  const [disclosurePrompt, setDisclosurePrompt] = useState<string>(
    "This call may be recorded for quality assurance and uses automated intelligence."
  );
  const [selectedVoice, setSelectedVoice] = useState<string>(cached?.default_voice || "en-US-JennyNeural");
  const [speechRate, setSpeechRate] = useState<string>(cached?.voice_rate || "+0%");
  const [language, setLanguage] = useState<string>(cached?.language || "en-US");
  const [pronunciations, setPronunciations] = useState<PronunciationRule[]>([
    { pattern: "\\bONT\\b", replace: "O-N-T" },
    { pattern: "\\bVoIP\\b", replace: "Voice over I-P" },
    { pattern: "\\bGbps\\b", replace: "gigabits per second" },
    { pattern: "\\bMbps\\b", replace: "megabits per second" },
    { pattern: "\\bSSID\\b", replace: "Wi-Fi network name" }
  ]);
  const [turnServerUrl, setTurnServerUrl] = useState<string>("");
  const [turnUsername, setTurnUsername] = useState<string>("");
  const [turnCredential, setTurnCredential] = useState<string>("");
  const [iceServersJson, setIceServersJson] = useState<string>("");
  const [effectiveIceServers, setEffectiveIceServers] = useState<any[]>([]);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);
  const [rtcSaveSuccess, setRtcSaveSuccess] = useState<boolean>(false);
  const [iceTestStatus, setIceTestStatus] = useState<{
    testing: boolean;
    success?: boolean;
    message?: string;
    details?: string[];
  }>({ testing: false });

  useEffect(() => {

    // 2. Fetch server authoritative configuration
    apiGet<AdminConfigData>('/api/admin/config')
      .then((data) => {
        if (data) {
          if (data.operator_name) setOperatorName(data.operator_name);
          if (data.greeting_prompt) setGreetingPrompt(data.greeting_prompt);
          if (data.spanish_greeting_prompt) setSpanishGreeting(data.spanish_greeting_prompt);
          if (data.hindi_greeting_prompt) setHindiGreeting(data.hindi_greeting_prompt);
          if (data.hold_prompt) setHoldPrompt(data.hold_prompt);
          if (data.close_prompt) setClosePrompt(data.close_prompt);
          if (data.escalation_prompt) setEscalationPrompt(data.escalation_prompt);
          if (typeof data.regulatory_disclosure_enabled === 'boolean') {
            setDisclosureEnabled(data.regulatory_disclosure_enabled);
          }
          if (data.regulatory_disclosure_prompt) {
            setDisclosurePrompt(data.regulatory_disclosure_prompt);
          }
          if (data.default_voice) setSelectedVoice(data.default_voice);
          if (data.voice_rate) setSpeechRate(data.voice_rate);
          if (data.language) setLanguage(data.language);
          if (data.pronunciation_overrides) {
            const list = Object.entries(data.pronunciation_overrides).map(([pattern, replace]) => ({
              pattern, replace
            }));
            setPronunciations(list);
          }
          if (data.turn_server_url !== undefined) setTurnServerUrl(data.turn_server_url);
          if (data.turn_username !== undefined) setTurnUsername(data.turn_username);
          if (data.turn_credential !== undefined) setTurnCredential(data.turn_credential);
          if (data.ice_servers_json !== undefined) setIceServersJson(data.ice_servers_json);
          if (data.effective_ice_servers) setEffectiveIceServers(data.effective_ice_servers);
        }
      })
      .catch(() => {});
  }, []);

  const addPronunciation = useCallback((pattern: string, replace: string) => {
    if (!pattern.trim() || !replace.trim()) return;
    setPronunciations(prev => [...prev, { pattern: pattern.trim(), replace: replace.trim() }]);
  }, []);

  const removePronunciation = useCallback((idx: number) => {
    setPronunciations(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const saveSettings = useCallback(() => {
    const overrideMap: Record<string, string> = {};
    pronunciations.forEach(p => {
      overrideMap[p.pattern] = p.replace;
    });

    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify({
        operator_name: operatorName,
        greeting_prompt: greetingPrompt,
        spanish_greeting_prompt: spanishGreeting,
        hindi_greeting_prompt: hindiGreeting,
        default_voice: selectedVoice,
        voice_rate: speechRate,
        language: language
      }));
    } catch {
      // ignore
    }

    Promise.all([
      apiPost('/api/admin/voice', {
        voice_name: selectedVoice,
        rate: speechRate,
        pitch: "+0Hz",
        language: language
      }),
      apiPost('/api/admin/prompts', {
        operator_name: operatorName,
        greeting_prompt: greetingPrompt,
        spanish_greeting_prompt: spanishGreeting,
        hindi_greeting_prompt: hindiGreeting,
        hold_prompt: holdPrompt,
        close_prompt: closePrompt,
        escalation_prompt: escalationPrompt,
        regulatory_disclosure_enabled: disclosureEnabled,
        regulatory_disclosure_prompt: disclosurePrompt,
        pronunciation_overrides: overrideMap
      })
    ]).then(() => {
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    });
  }, [
    operatorName, greetingPrompt, spanishGreeting, hindiGreeting, holdPrompt,
    closePrompt, escalationPrompt, disclosureEnabled, disclosurePrompt,
    selectedVoice, speechRate, language, pronunciations
  ]);

  const saveRtcSettings = useCallback(async () => {
    try {
      const res = await apiPost<{ success: boolean; effective_ice_servers?: any[] }>('/api/admin/rtc', {
        turn_server_url: turnServerUrl,
        turn_username: turnUsername,
        turn_credential: turnCredential,
        ice_servers_json: iceServersJson
      });
      if (res.success) {
        if (res.effective_ice_servers) {
          setEffectiveIceServers(res.effective_ice_servers);
        }
        setRtcSaveSuccess(true);
        setTimeout(() => setRtcSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Failed to save RTC config:", err);
    }
  }, [turnServerUrl, turnUsername, turnCredential, iceServersJson]);

  const testIceGathering = useCallback(async () => {
    setIceTestStatus({ testing: true });
    const collectedTypes = new Set<string>();
    const details: string[] = [];

    try {
      let testServers: RTCIceServer[] = [];
      if (iceServersJson.trim()) {
        try {
          testServers = JSON.parse(iceServersJson);
        } catch {
          setIceTestStatus({
            testing: false,
            success: false,
            message: 'Invalid ICE Servers JSON syntax.',
            details: ['Please ensure valid JSON array matching [{ "urls": "..." }] format.']
          });
          return;
        }
      } else {
        testServers = [
          {
            urls: [
              'stun:stun.l.google.com:19302',
              'stun:stun1.l.google.com:19302',
              'stun:stun.cloudflare.com:3478'
            ]
          }
        ];
        if (turnServerUrl.trim()) {
          const entry: any = {
            urls: turnServerUrl.split(',').map(u => u.trim()).filter(Boolean)
          };
          if (turnUsername.trim()) entry.username = turnUsername.trim();
          if (turnCredential.trim()) entry.credential = turnCredential.trim();
          testServers.push(entry);
        }
      }

      const pc = new RTCPeerConnection({
        iceServers: testServers,
        iceCandidatePoolSize: 1
      });

      pc.addTransceiver('audio', { direction: 'recvonly' });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      await new Promise<void>((resolve) => {
        const timer = setTimeout(() => resolve(), 5000);

        pc.onicecandidate = (event) => {
          if (event.candidate) {
            const cand = event.candidate;
            const type = cand.type || 'unknown';
            collectedTypes.add(type);
            details.push(`[${type.toUpperCase()}] ${cand.protocol} candidate: ${cand.candidate.slice(0, 40)}...`);
          } else {
            clearTimeout(timer);
            resolve();
          }
        };
      });

      pc.close();

      const hasRelay = collectedTypes.has('relay');
      const hasSrflx = collectedTypes.has('srflx');

      if (hasRelay) {
        setIceTestStatus({
          testing: false,
          success: true,
          message: 'TURN relay verified successfully! Relay candidates gathered for cross-network connectivity.',
          details
        });
      } else if (hasSrflx) {
        setIceTestStatus({
          testing: false,
          success: !turnServerUrl.trim(),
          message: turnServerUrl.trim()
            ? 'STUN succeeded, but TURN relay candidate was not gathered. Check TURN credentials and ports.'
            : 'STUN verified (public IP discovered). Note: Symmetric NAT or mobile networks still require TURN.',
          details
        });
      } else {
        setIceTestStatus({
          testing: false,
          success: false,
          message: 'Failed to gather public candidates. Firewall or ISP may be blocking UDP packets.',
          details
        });
      }
    } catch (err: any) {
      setIceTestStatus({
        testing: false,
        success: false,
        message: `ICE Gathering test failed: ${err?.message || err}`,
        details
      });
    }
  }, [turnServerUrl, turnUsername, turnCredential, iceServersJson]);

  return {
    operatorName, setOperatorName,
    greetingPrompt, setGreetingPrompt,
    spanishGreeting, setSpanishGreeting,
    hindiGreeting, setHindiGreeting,
    holdPrompt, setHoldPrompt,
    closePrompt, setClosePrompt,
    escalationPrompt, setEscalationPrompt,
    disclosureEnabled, setDisclosureEnabled,
    disclosurePrompt, setDisclosurePrompt,
    selectedVoice, setSelectedVoice,
    speechRate, setSpeechRate,
    language, setLanguage,
    pronunciations, addPronunciation, removePronunciation,
    turnServerUrl, setTurnServerUrl,
    turnUsername, setTurnUsername,
    turnCredential, setTurnCredential,
    iceServersJson, setIceServersJson,
    effectiveIceServers,
    savedSuccess, saveSettings,
    rtcSaveSuccess, saveRtcSettings,
    iceTestStatus, testIceGathering,
  };
}
