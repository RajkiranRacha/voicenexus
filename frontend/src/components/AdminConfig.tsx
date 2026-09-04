import React, { useState } from 'react';
import {
  Sliders, Mic, Building2, Save, Check, ShieldAlert, Volume2, Plus, Trash2
} from 'lucide-react';
import { useAdminConfig } from '../hooks/useAdminConfig';

export const AdminConfig: React.FC = () => {
  const cfg = useAdminConfig();
  const [newPattern, setNewPattern] = useState<string>("");
  const [newReplace, setNewReplace] = useState<string>("");

  const handleAddPronunciation = () => {
    cfg.addPronunciation(newPattern, newReplace);
    setNewPattern("");
    setNewReplace("");
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
          onClick={cfg.saveSettings}
          className="py-2.5 px-5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-2 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
        >
          {cfg.savedSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
          <span>{cfg.savedSuccess ? 'Settings Applied!' : 'Save Configuration'}</span>
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
                value={cfg.selectedVoice}
                onChange={(e) => cfg.setSelectedVoice(e.target.value)}
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
                  value={cfg.language}
                  onChange={(e) => {
                    const newLang = e.target.value;
                    cfg.setLanguage(newLang);
                    if (newLang === 'hi-IN' && !cfg.selectedVoice.startsWith('hi-')) {
                      cfg.setSelectedVoice('hi-IN-SwaraNeural');
                    } else if (newLang === 'es-US' && !cfg.selectedVoice.startsWith('es-')) {
                      cfg.setSelectedVoice('es-US-PalomaNeural');
                    } else if (newLang === 'en-US' && !cfg.selectedVoice.startsWith('en-')) {
                      cfg.setSelectedVoice('en-US-JennyNeural');
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
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Speech Rate ({cfg.speechRate}):</label>
                <select
                  value={cfg.speechRate}
                  onChange={(e) => cfg.setSpeechRate(e.target.value)}
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
                checked={cfg.disclosureEnabled}
                onChange={(e) => cfg.setDisclosureEnabled(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Disclosure Prompt Text:</label>
              <textarea
                rows={2}
                disabled={!cfg.disclosureEnabled}
                value={cfg.disclosurePrompt}
                onChange={(e) => cfg.setDisclosurePrompt(e.target.value)}
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
              value={cfg.operatorName}
              onChange={(e) => cfg.setOperatorName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Hold Prompt:</label>
            <input
              type="text"
              value={cfg.holdPrompt}
              onChange={(e) => cfg.setHoldPrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Primary English Greeting Prompt:</label>
            <textarea
              rows={2}
              value={cfg.greetingPrompt}
              onChange={(e) => cfg.setGreetingPrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Spanish Secondary Greeting Prompt:</label>
            <textarea
              rows={2}
              value={cfg.spanishGreeting}
              onChange={(e) => cfg.setSpanishGreeting(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Hindi Tertiary Greeting Prompt (हिन्दी):</label>
            <textarea
              rows={2}
              value={cfg.hindiGreeting}
              onChange={(e) => cfg.setHindiGreeting(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Call Closing Prompt:</label>
            <input
              type="text"
              value={cfg.closePrompt}
              onChange={(e) => cfg.setClosePrompt(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Live Agent Escalation Transfer Prompt:</label>
            <input
              type="text"
              value={cfg.escalationPrompt}
              onChange={(e) => cfg.setEscalationPrompt(e.target.value)}
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
          {cfg.pronunciations.map((item, idx) => (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 flex items-center justify-between text-xs">
              <div>
                <span className="font-mono text-indigo-400 font-semibold">{item.pattern}</span>
                <div className="text-[11px] text-slate-400">→ "{item.replace}"</div>
              </div>
              <button
                type="button"
                onClick={() => cfg.removePronunciation(idx)}
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
            onClick={handleAddPronunciation}
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
