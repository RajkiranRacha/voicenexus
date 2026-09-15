import React, { useState } from 'react';
import {
  Sliders, Mic, Building2, Save, Check, ShieldAlert, Volume2, Plus, Trash2, BookOpen,
  Network, Server, Globe, Activity, ExternalLink, RefreshCw, AlertCircle, CheckCircle2
} from 'lucide-react';
import { useAdminConfig } from '../hooks/useAdminConfig';
import { TelecomKbManager } from './TelecomKbManager';

const NatTraversalConfig: React.FC<{ cfg: ReturnType<typeof useAdminConfig> }> = ({ cfg }) => {
  return (
    <div className="space-y-6">
      {/* Intro Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-cyan-400 pb-2 border-b border-slate-800">
          <Network className="w-4 h-4 text-cyan-400" />
          <span>Cross-Network WebRTC & NAT Traversal Configuration</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          When deploying to <strong>Render</strong> or any cloud host, callers and agents reside on separate networks.
          While STUN discovers public IP addresses for direct peer-to-peer audio, <strong>Symmetric NAT</strong> (common on 4G/5G mobile carriers, cellular hotspots, university, and strict home Wi-Fi) blocks direct UDP packets between peers.
          A <strong>TURN Relay Server</strong> ensures 100% reliable voice transfer across all networks by relaying encrypted media packets when direct P2P fails.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active STUN & TURN Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400 pb-2 border-b border-slate-800">
            <Server className="w-4 h-4 text-indigo-400" />
            <span>Active ICE Infrastructure</span>
          </div>

          <div className="space-y-3">
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-xs space-y-2">
              <div className="font-semibold text-slate-300 flex items-center justify-between">
                <span>Default STUN Servers (Public IP Discovery)</span>
                <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-mono">
                  Always Active
                </span>
              </div>
              <ul className="text-[11px] text-slate-400 space-y-1 font-mono">
                <li>• stun:stun.l.google.com:19302</li>
                <li>• stun:stun1.l.google.com:19302</li>
                <li>• stun:stun2.l.google.com:19302</li>
                <li>• stun:stun.cloudflare.com:3478</li>
              </ul>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-xs space-y-2">
              <div className="font-semibold text-slate-300 flex items-center justify-between">
                <span>TURN Relay Status</span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-mono border ${
                  cfg.turnServerUrl.trim() || cfg.iceServersJson.trim()
                    ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                    : 'bg-amber-950 text-amber-400 border-amber-800'
                }`}>
                  {cfg.turnServerUrl.trim() || cfg.iceServersJson.trim() ? 'TURN Configured' : 'No TURN Configured'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                {cfg.turnServerUrl.trim() || cfg.iceServersJson.trim()
                  ? 'Configured TURN relay is active for cross-network media fallback.'
                  : 'Without a TURN server, callers on mobile 4G/5G or behind Symmetric NAT cannot exchange audio with the agent.'}
              </p>
            </div>

            {/* Test ICE Gathering Tool */}
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-300">Test WebRTC Candidate Gathering</span>
                <button
                  type="button"
                  disabled={cfg.iceTestStatus.testing}
                  onClick={cfg.testIceGathering}
                  className="py-1.5 px-3 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-cyan-950/30 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${cfg.iceTestStatus.testing ? 'animate-spin' : ''}`} />
                  <span>{cfg.iceTestStatus.testing ? 'Gathering Candidates...' : 'Test ICE Gathering'}</span>
                </button>
              </div>

              {cfg.iceTestStatus.message && (
                <div className={`p-3 rounded-xl border text-xs space-y-2 ${
                  cfg.iceTestStatus.success
                    ? 'bg-emerald-950/40 border-emerald-800 text-emerald-200'
                    : 'bg-amber-950/40 border-amber-800 text-amber-200'
                }`}>
                  <div className="flex items-start space-x-2 font-semibold">
                    {cfg.iceTestStatus.success
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      : <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />}
                    <span>{cfg.iceTestStatus.message}</span>
                  </div>
                  {cfg.iceTestStatus.details && cfg.iceTestStatus.details.length > 0 && (
                    <div className="bg-slate-950/80 p-2 rounded-lg font-mono text-[10px] max-h-32 overflow-y-auto space-y-0.5 text-slate-300">
                      {cfg.iceTestStatus.details.map((d, i) => (
                        <div key={i}>{d}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* TURN Server Configuration Form */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400 pb-2 border-b border-slate-800">
            <Globe className="w-4 h-4 text-indigo-400" />
            <span>Custom TURN Relay Credentials</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                TURN Server URL(s):
              </label>
              <input
                type="text"
                placeholder="e.g. turn:global.relay.metered.ca:80,turns:global.relay.metered.ca:443"
                value={cfg.turnServerUrl}
                onChange={(e) => cfg.setTurnServerUrl(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[10px] text-slate-500 block mt-1">
                Separate multiple endpoints with commas. Port 80/443 recommended for firewall bypass.
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  TURN Username:
                </label>
                <input
                  type="text"
                  placeholder="Username"
                  value={cfg.turnUsername}
                  onChange={(e) => cfg.setTurnUsername(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  TURN Credential / Password:
                </label>
                <input
                  type="password"
                  placeholder="Credential"
                  value={cfg.turnCredential}
                  onChange={(e) => cfg.setTurnCredential(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                Advanced: Raw ICE Servers JSON Array (Optional)
              </label>
              <textarea
                rows={3}
                placeholder='[{"urls": ["stun:..."], ...}]'
                value={cfg.iceServersJson}
                onChange={(e) => cfg.setIceServersJson(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[10px] text-slate-500 block mt-1">
                If specified, overrides individual URL/user fields (matches standard RTCIceServer[] format).
              </span>
            </div>

            <button
              type="button"
              onClick={cfg.saveRtcSettings}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
            >
              {cfg.rtcSaveSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
              <span>{cfg.rtcSaveSuccess ? 'WebRTC Settings Applied!' : 'Save WebRTC & NAT Settings'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metered.ca Free Step-by-Step Guide */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-xs font-semibold text-amber-400">
            <Activity className="w-4 h-4" />
            <span>How to get Free TURN Relay for Render (Takes 1 Minute)</span>
          </div>
          <a
            href="https://www.metered.ca/tools/openrelay"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center space-x-1"
          >
            <span>Open Metered.ca</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-300">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-slate-100 mb-1">1. Sign Up Free</div>
            <p className="text-[11px] text-slate-400">
              Go to Metered.ca and create a free account. Free plan provides <strong>50GB/month</strong> free TURN relay without requiring a credit card.
            </p>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-slate-100 mb-1">2. Copy Credentials</div>
            <p className="text-[11px] text-slate-400">
              In your Metered Dashboard, navigate to TURN Credentials or click "Show ICE Servers Array" to view your server URL, username, and password.
            </p>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="font-bold text-slate-100 mb-1">3. Paste & Test</div>
            <p className="text-[11px] text-slate-400">
              Paste the credentials into the fields above, click <strong>Save</strong>, and click <strong>Test ICE Gathering</strong> to verify relay traversal.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export const AdminConfig: React.FC = () => {
  const [adminTab, setAdminTab] = useState<'VOICE_PROMPTS' | 'TELECOM_KB' | 'NAT_TRAVERSAL'>('VOICE_PROMPTS');
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
      {/* Sub-tab Switcher: Voice/Prompts vs Knowledge Base vs WebRTC */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setAdminTab('VOICE_PROMPTS')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              adminTab === 'VOICE_PROMPTS'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Brand Voice & Prompts</span>
          </button>
          <button
            type="button"
            onClick={() => setAdminTab('TELECOM_KB')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              adminTab === 'TELECOM_KB'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 text-amber-400" />
            <span>Telecom Knowledge Base</span>
          </button>
          <button
            type="button"
            onClick={() => setAdminTab('NAT_TRAVERSAL')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              adminTab === 'NAT_TRAVERSAL'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Network className="w-3.5 h-3.5 text-cyan-400" />
            <span>WebRTC & NAT Traversal (STUN / TURN)</span>
          </button>
        </div>

        {adminTab === 'VOICE_PROMPTS' && (
          <button
            onClick={cfg.saveSettings}
            className="py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-2 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
          >
            {cfg.savedSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
            <span>{cfg.savedSuccess ? 'Settings Applied!' : 'Save Configuration'}</span>
          </button>
        )}

        {adminTab === 'NAT_TRAVERSAL' && (
          <button
            onClick={cfg.saveRtcSettings}
            className="py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-2 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
          >
            {cfg.rtcSaveSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
            <span>{cfg.rtcSaveSuccess ? 'WebRTC Config Saved!' : 'Save WebRTC Settings'}</span>
          </button>
        )}
      </div>

      {adminTab === 'TELECOM_KB' ? (
        <TelecomKbManager />
      ) : adminTab === 'NAT_TRAVERSAL' ? (
        <NatTraversalConfig cfg={cfg} />
      ) : (
        <div className="space-y-6">

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
      )}
    </div>
  );
};
