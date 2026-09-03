import React, { useState } from 'react';
import { Sliders, Mic, Building2, Save, Check } from 'lucide-react';

export const AdminConfig: React.FC = () => {
  const [operatorName, setOperatorName] = useState<string>("NexusFiber Telco");
  const [greetingPrompt, setGreetingPrompt] = useState<string>(
    "Thank you for calling NexusFiber Care. I am your automated digital assistant. How can I help you today?"
  );
  const [selectedVoice, setSelectedVoice] = useState<string>("en-US-JennyNeural");
  const [speechRate, setSpeechRate] = useState<string>("+0%");
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const saveSettings = () => {
    Promise.all([
      fetch('/api/admin/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_name: selectedVoice, rate: speechRate, pitch: "+0%" })
      }),
      fetch('/api/admin/prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operator_name: operatorName, greeting_prompt: greetingPrompt })
      })
    ]).then(() => {
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <span>Brand Voice & Tenant Admin (VN-7, VN-9)</span>
          </h2>
          <p className="text-xs text-slate-400">
            Tune neural voice persona, per-tenant greetings, and operational guardrails.
          </p>
        </div>
        <button
          onClick={saveSettings}
          className="py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
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
                <option value="en-US-JennyNeural">en-US-JennyNeural (Warm, Natural Female - Recommended)</option>
                <option value="en-US-GuyNeural">en-US-GuyNeural (Professional, Conversational Male)</option>
                <option value="en-US-AriaNeural">en-US-AriaNeural (Expressive, Empathetic Female)</option>
                <option value="en-GB-SoniaNeural">en-GB-SoniaNeural (British English Care Voice)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Speech Rate ({speechRate}):</label>
              <select
                value={speechRate}
                onChange={(e) => setSpeechRate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="-10%">-10% (Measured & Deliberate)</option>
                <option value="+0%">Normal (Standard Conversational)</option>
                <option value="+10%">+10% (Brisk Contact Center Cadence)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tenant Prompts & Branding */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400 pb-2 border-b border-slate-800">
            <Building2 className="w-4 h-4 text-indigo-400" />
            <span>Tenant Branding & Ingress Prompts (VN-9)</span>
          </div>

          <div className="space-y-3">
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
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Custom Greeting Prompt:</label>
              <textarea
                rows={3}
                value={greetingPrompt}
                onChange={(e) => setGreetingPrompt(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
