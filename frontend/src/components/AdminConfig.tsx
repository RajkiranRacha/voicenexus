import React, { useState, useEffect } from 'react';
import { 
  Sliders, Mic, Building2, Save, Check, ShieldAlert, Volume2, Plus, Trash2
} from 'lucide-react';
import type { AdminConfigData } from '../types';

export const AdminConfig: React.FC = () => {
  const [operatorName, setOperatorName] = useState<string>("NexusFiber Telco");
  const [greetingPrompt, setGreetingPrompt] = useState<string>(
    "Thank you for calling NexusFiber Care. I am your automated digital assistant. How can I help you today?"
  );
  const [spanishGreeting, setSpanishGreeting] = useState<string>(
    "Gracias por llamar a NexusFiber Atención al Cliente. Soy su asistente digital automatizado. ¿Cómo le puedo ayudar hoy?"
  );
  const [hindiGreeting, setHindiGreeting] = useState<string>(
    "NexusFiber में कॉल करने के लिए धन्यवाद। मैं आपका स्वचालित डिजिटल सहायक हूँ। मैं आज आपकी क्या सहायता कर सकता हूँ?"
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
  const [selectedVoice, setSelectedVoice] = useState<string>("en-US-JennyNeural");
  const [speechRate, setSpeechRate] = useState<string>("+0%");
  const [language, setLanguage] = useState<string>("en-US");
  const [pronunciations, setPronunciations] = useState<Array<{ pattern: string; replace: string }>>([
    { pattern: "\\bONT\\b", replace: "O-N-T" },
    { pattern: "\\bVoIP\\b", replace: "Voice over I-P" },
    { pattern: "\\bGbps\\b", replace: "gigabits per second" },
    { pattern: "\\bMbps\\b", replace: "megabits per second" },
    { pattern: "\\bSSID\\b", replace: "Wi-Fi network name" }
  ]);
  const [newPattern, setNewPattern] = useState<string>("");
  const [newReplace, setNewReplace] = useState<string>("");
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  useEffect(() => {
    // 1. Instant recovery from localStorage if present
    try {
      const cached = localStorage.getItem('voicenexus_admin_config');
      if (cached) {
        const d = JSON.parse(cached);
        if (d.operator_name) setOperatorName(d.operator_name);
        if (d.greeting_prompt) setGreetingPrompt(d.greeting_prompt);
        if (d.spanish_greeting_prompt) setSpanishGreeting(d.spanish_greeting_prompt);
        if (d.hindi_greeting_prompt) setHindiGreeting(d.hindi_greeting_prompt);
        if (d.default_voice) setSelectedVoice(d.default_voice);
        if (d.voice_rate) setSpeechRate(d.voice_rate);
        if (d.language) setLanguage(d.language);
      }
    } catch {
      // ignore JSON parse error
    }

    // 2. Fetch server authoritative configuration
    fetch('/api/admin/config')
      .then(res => res.json())
      .then((data: AdminConfigData) => {
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
        }
      })
      .catch(() => {});
  }, []);

  const addPronunciation = () => {
    if (!newPattern.trim() || !newReplace.trim()) return;
    setPronunciations(prev => [...prev, { pattern: newPattern.trim(), replace: newReplace.trim() }]);
    setNewPattern("");
    setNewReplace("");
  };

  const removePronunciation = (idx: number) => {
    setPronunciations(prev => prev.filter((_, i) => i !== idx));
  };

  const saveSettings = () => {
    const overrideMap: Record<string, string> = {};
    pronunciations.forEach(p => {
      overrideMap[p.pattern] = p.replace;
    });

    // Cache locally
    try {
      localStorage.setItem('voicenexus_admin_config', JSON.stringify({
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
      fetch('/api/admin/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          voice_name: selectedVoice, 
          rate: speechRate, 
          pitch: "+0%",
          language: language
        })
      }),
      fetch('/api/admin/prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
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
      })
    ]).then(() => {
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    });
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <span>Brand Voice, Prompts & Compliance Admin (VN-7, VN-9)</span>
          </h2>
          <p className="text-xs text-slate-400">
            Tune neural voice persona, per-tenant greetings, regulatory disclosure, and pronunciation lexicons.
          </p>
        </div>
        <button
          onClick={saveSettings}
          className="py-2.5 px-5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-2 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
        >
          {savedSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
          <span>{savedSuccess ? 'Settings Applied!' : 'Save Configuration'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Brand Voice Tuning */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400 pb-2 border-b border-slate-800">
            <Mic className="w-4 h-4 text-indigo-400" />
            <span>Brand Voice Persona (VN-7)</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Active Neural Voice:</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <optgroup label="English Neural Voices">
                  <option value="en-US-JennyNeural">en-US-JennyNeural (Warm, Natural Female - Recommended)</option>
                  <option value="en-US-GuyNeural">en-US-GuyNeural (Professional, Conversational Male)</option>
                  <option value="en-US-AriaNeural">en-US-AriaNeural (Expressive, Empathetic Female)</option>
                  <option value="en-GB-SoniaNeural">en-GB-SoniaNeural (British English Care Voice)</option>
                </optgroup>
                <optgroup label="Spanish Neural Voices">
                  <option value="es-US-PalomaNeural">es-US-PalomaNeural (Spanish Neutral Female)</option>
                  <option value="es-US-AlonsoNeural">es-US-AlonsoNeural (Spanish Professional Male)</option>
                </optgroup>
                <optgroup label="Hindi Neural Voices">
                  <option value="hi-IN-SwaraNeural">hi-IN-SwaraNeural (Hindi Natural Female)</option>
                  <option value="hi-IN-MadhurNeural">hi-IN-MadhurNeural (Hindi Professional Male)</option>
                </optgroup>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Primary Language:</label>
                <select
                  value={language}
                  onChange={(e) => {
                    const newLang = e.target.value;
                    setLanguage(newLang);
                    if (newLang === 'hi-IN' && !selectedVoice.startsWith('hi-')) {
                      setSelectedVoice('hi-IN-SwaraNeural');
                    } else if (newLang === 'es-US' && !selectedVoice.startsWith('es-')) {
                      setSelectedVoice('es-US-PalomaNeural');
                    } else if (newLang === 'en-US' && !selectedVoice.startsWith('en-')) {
                      setSelectedVoice('en-US-JennyNeural');
                    }
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="en-US">English (en-US)</option>
                  <option value="es-US">Español (es-US)</option>
                  <option value="hi-IN">Hindi / हिन्दी (hi-IN)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Speech Rate ({speechRate}):</label>
                <select
                  value={speechRate}
                  onChange={(e) => setSpeechRate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="-25%">-25% (Slow & Deliberate)</option>
                  <option value="+0%">Normal (Standard Cadence)</option>
                  <option value="+25%">+25% (Fast Contact Center)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Regulatory & Compliance Disclosure (VN-9) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400 pb-2 border-b border-slate-800">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span>Regulatory AI & Recording Disclosure (VN-9)</span>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800">
              <div>
                <div className="text-xs font-semibold text-slate-200">Mandatory AI & Recording Disclosure</div>
                <div className="text-[11px] text-slate-500">Prefixes call greeting to satisfy regional telco regulations</div>
              </div>
              <input
                type="checkbox"
                checked={disclosureEnabled}
                onChange={(e) => setDisclosureEnabled(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Disclosure Prompt Text:</label>
              <textarea
                rows={2}
                disabled={!disclosureEnabled}
                value={disclosurePrompt}
                onChange={(e) => setDisclosurePrompt(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 disabled:opacity-40"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Tenant Branding & Dialog Prompts */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400 pb-2 border-b border-slate-800">
          <Building2 className="w-4 h-4 text-indigo-400" />
          <span>Tenant Prompts & Branding (VN-9)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Operator / Telco Name:</label>
            <input
              type="text"
              value={operatorName}
              onChange={(e) => setOperatorName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Hold Prompt:</label>
            <input
              type="text"
              value={holdPrompt}
              onChange={(e) => setHoldPrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Primary English Greeting Prompt:</label>
            <textarea
              rows={2}
              value={greetingPrompt}
              onChange={(e) => setGreetingPrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Spanish Secondary Greeting Prompt:</label>
            <textarea
              rows={2}
              value={spanishGreeting}
              onChange={(e) => setSpanishGreeting(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Hindi Tertiary Greeting Prompt (हिन्दी):</label>
            <textarea
              rows={2}
              value={hindiGreeting}
              onChange={(e) => setHindiGreeting(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Call Closing Prompt:</label>
            <input
              type="text"
              value={closePrompt}
              onChange={(e) => setClosePrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Live Agent Escalation Transfer Prompt:</label>
            <input
              type="text"
              value={escalationPrompt}
              onChange={(e) => setEscalationPrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Telco Pronunciation Overrides Lexicon (VN-7) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400">
            <Volume2 className="w-4 h-4 text-indigo-400" />
            <span>Telco Pronunciation Overrides & Acronyms (VN-7)</span>
          </div>
          <span className="text-[11px] text-slate-500">Phonetic SSML/speech normalization</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
          {pronunciations.map((item, idx) => (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 flex items-center justify-between text-xs">
              <div>
                <span className="font-mono text-indigo-400 font-semibold">{item.pattern}</span>
                <div className="text-[11px] text-slate-400">→ "{item.replace}"</div>
              </div>
              <button
                type="button"
                onClick={() => removePronunciation(idx)}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1 cursor-pointer"
                title="Remove override"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>

        <div className="pt-2 flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            placeholder="Regex pattern (e.g. \bVoIP\b)"
            value={newPattern}
            onChange={(e) => setNewPattern(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            placeholder="Phonetic replacement (e.g. Voice over I-P)"
            value={newReplace}
            onChange={(e) => setNewReplace(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="button"
            onClick={addPronunciation}
            className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Rule</span>
          </button>
        </div>
      </div>
    </div>
  );
};
