import React, { useState, useEffect, useRef } from 'react';
import {
  Phone, PhoneOff, Mic, MicOff, Volume2, Radio,
  Send, ShieldCheck, Zap, Globe, Star
} from 'lucide-react';
import { apiPost } from '../api/client';
import { useCallWebSocket } from '../hooks/useCallWebSocket';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { TranscriptList } from './shared/TranscriptList';
import { PRESET_CALLERS, PRESET_UTTERANCES } from '../data/presets';

const CsatPrompt: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [rating, setRating] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const submit = (value: number) => {
    setRating(value);
    apiPost('/api/telemetry/csat', { session_id: sessionId, rating: value })
      .then(() => setSubmitted(true))
      .catch(() => {});
  };

  if (submitted) {
    return (
      <div className="text-xs text-emerald-300 flex items-center space-x-1.5">
        <Star className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
        <span>Thanks for your feedback!</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-xs">
      <span className="text-slate-400">Rate this call:</span>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => submit(n)}
          className="p-0.5 cursor-pointer"
          title={`${n} star${n > 1 ? 's' : ''}`}
        >
          <Star className={`w-4 h-4 ${rating != null && n <= rating ? 'text-amber-300 fill-amber-300' : 'text-slate-600'}`} />
        </button>
      ))}
    </div>
  );
};

export const PhoneSimulator: React.FC = () => {
  const [selectedAni, setSelectedAni] = useState<string>(PRESET_CALLERS[0].ani);
  const [customAni, setCustomAni] = useState<string>("");
  const [inputText, setInputText] = useState<string>('');
  const [autoPlayAudio, setAutoPlayAudio] = useState<boolean>(true);

  const agentAudioRef = useRef<HTMLAudioElement | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  const activeAni = customAni.trim() || selectedAni;

  const call = useCallWebSocket(agentAudioRef);
  const speech = useSpeechRecognition(call.callLanguage, (transcript) => call.sendUtterance(transcript, setInputText));

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [call.turns]);

  const startCall = () => call.startCall(activeAni, autoPlayAudio);
  const sendUtterance = (text: string) => call.sendUtterance(text, setInputText);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto">
      {/* Audio element for playing live agent voice */}
      <audio ref={agentAudioRef} autoPlay />

      {/* Left Column: Phone Console & Audio Telemetry */}
      <div className="lg:col-span-4 space-y-4">
        {/* Softphone Hardware Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                call.connectedAgent ? 'bg-emerald-400 animate-ping' :
                call.callState === 'IN_CALL' ? 'bg-emerald-500 animate-pulse' :
                call.callState === 'ESCALATED' ? 'bg-amber-500' :
                call.callState === 'CONNECTING' ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'
              }`} />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {call.connectedAgent ? `Live with ${call.connectedAgent.name}` :
                 call.callState === 'IN_CALL' ? 'Active Call In-Flow' :
                 call.callState === 'ESCALATED' ? 'Escalated to Agent' :
                 call.callState === 'CONNECTING' ? 'Connecting to SBC...' : 'Line Idle'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAutoPlayAudio(!autoPlayAudio)}
                className={`p-1.5 rounded-lg text-xs flex items-center space-x-1 ${
                  autoPlayAudio ? 'bg-indigo-950 text-indigo-300 border border-indigo-700' : 'bg-slate-800 text-slate-400'
                }`}
                title="Toggle Audio Voice Playback"
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>{autoPlayAudio ? 'Voice On' : 'Muted'}</span>
              </button>
            </div>
          </div>

          {/* Caller Identity Selection */}
          <div className="mt-4 space-y-2">
            <label className="text-xs font-medium text-slate-300">Simulate Inbound Caller (ANI):</label>
            <div className="space-y-1.5">
              {PRESET_CALLERS.map((c) => (
                <button
                  key={c.ani}
                  disabled={call.callState === 'IN_CALL' || call.callState === 'CONNECTING'}
                  onClick={() => { setSelectedAni(c.ani); setCustomAni(""); }}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs transition-all cursor-pointer ${
                    activeAni === c.ani
                      ? 'border-indigo-500 bg-indigo-950/40 text-white'
                      : 'border-slate-800 bg-slate-950/50 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-slate-200">{c.name} ({c.ani})</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{c.scenario}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Active Call Controls */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            {call.callState === 'IDLE' || call.callState === 'ENDED' ? (
              <button
                onClick={startCall}
                className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/40 transition-all cursor-pointer"
              >
                <Phone className="w-5 h-5" />
                <span>Dial Care Line (+1 800 NEXUS-CARE)</span>
              </button>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={call.endCall}
                  className="w-full py-2.5 px-4 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-rose-950/40 transition-all cursor-pointer"
                >
                  <PhoneOff className="w-4 h-4" />
                  <span>Disconnect Call</span>
                </button>

                {call.connectedAgent ? (
                  <button
                    type="button"
                    onClick={call.toggleCallerMute}
                    className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                      call.isCallerMuted
                        ? 'border-rose-500/80 bg-rose-950/50 text-rose-200'
                        : 'border-emerald-800 bg-emerald-950/40 text-emerald-300'
                    }`}
                  >
                    {call.isCallerMuted ? <MicOff className="w-3.5 h-3.5 text-rose-400" /> : <Mic className="w-3.5 h-3.5 text-emerald-400" />}
                    <span>{call.isCallerMuted ? 'Caller Mic Muted (Click to Unmute)' : 'Caller Mic Live (Click to Mute)'}</span>
                  </button>
                ) : (
                  /* Barge-in Interruption Button */
                  <button
                    onClick={call.handleBargeIn}
                    disabled={!call.isPlayingAudio}
                    className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
                      call.isPlayingAudio
                        ? 'border-amber-500/80 bg-amber-950/50 text-amber-200 animate-pulse cursor-pointer'
                        : 'border-slate-800 bg-slate-900/50 text-slate-500 cursor-not-allowed'
                    }`}
                  >
                    <MicOff className="w-3.5 h-3.5" />
                    <span>{call.isPlayingAudio ? 'Barge-In (Interrupt AI Speech)' : 'AI Not Speaking'}</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* DTMF Dialpad (VN-9 degraded mode fallback) */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            <div className="text-[11px] font-semibold uppercase text-slate-400 mb-2 flex items-center justify-between">
              <span>DTMF Touch-Tone Keypad</span>
              <span className="text-[10px] text-slate-500 font-normal">0 = Operator</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((digit) => (
                <button
                  key={digit}
                  disabled={call.callState !== 'IN_CALL'}
                  onClick={() => call.sendDtmf(digit)}
                  className="py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 font-mono text-sm font-semibold disabled:opacity-40 transition-all cursor-pointer"
                >
                  {digit}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Real-Time Sub-Second Latency Telemetry Badge */}
        {call.latestLatency && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Turn Latency Budget</span>
              </span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                call.latestLatency.total_turn_ms <= 1000
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-amber-950 text-amber-300 border border-amber-800'
              }`}>
                {call.latestLatency.total_turn_ms} ms (SLO: ≤1000ms)
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">STT ASR</div>
                <div className="font-semibold text-slate-300">{call.latestLatency.stt_ms} ms</div>
              </div>
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">NLU / FSM</div>
                <div className="font-semibold text-indigo-300">{call.latestLatency.nlu_ms} ms</div>
              </div>
              <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/60">
                <div className="text-slate-500">Neural TTS</div>
                <div className="font-semibold text-cyan-300">{call.latestLatency.tts_ms} ms</div>
              </div>
            </div>
          </div>
        )}

        {/* Post-Call CSAT */}
        {call.callState === 'ENDED' && call.sessionId && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <CsatPrompt sessionId={call.sessionId} />
          </div>
        )}
      </div>

      {/* Right Column: Live Conversation Transcript & Interactive Utterance Prompts */}
      <div className="lg:col-span-8 flex flex-col space-y-4">
        {/* Caller Context Banner */}
        {call.callerProfile ? (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold">
                {call.callerProfile.customer_name[0]}
              </div>
              <div>
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <span>{call.callerProfile.customer_name}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center space-x-1 ${
                    call.callerProfile.auth_status === 'OTP_VERIFIED' ? 'bg-purple-950 text-purple-300 border-purple-800' :
                    call.callerProfile.auth_status === 'KBA_VERIFIED' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' :
                    'bg-indigo-950 text-indigo-300 border-indigo-800'
                  }`}>
                    <ShieldCheck className="w-2.5 h-2.5" />
                    <span>{call.callerProfile.auth_status}</span>
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center space-x-1">
                    <Globe className="w-2.5 h-2.5 text-cyan-400" />
                    <span>{call.callLanguage}</span>
                  </span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  Acc: {call.callerProfile.account_number} · {call.callerProfile.plan_name} · Bal: ${call.callerProfile.current_balance.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="text-right text-[11px] text-slate-400 hidden sm:block">
              <div>Zip: {call.callerProfile.zip_code}</div>
              <div className={call.callerProfile.has_active_outage ? 'text-rose-400 font-semibold' : 'text-slate-400'}>
                {call.callerProfile.has_active_outage ? '⚠ Area Outage Active' : 'Network Nominal'}
              </div>
            </div>
          </div>
        ) : call.callState === 'IN_CALL' ? (
          <div className="bg-amber-950/40 border border-amber-900/60 rounded-2xl p-3.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-amber-300">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>
                <strong>Unregistered ANI ({activeAni}):</strong> Awaiting Knowledge-Based Authentication (say Account # or Zip Code 94107).
              </span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center space-x-1">
              <Globe className="w-2.5 h-2.5 text-cyan-400" />
              <span>{call.callLanguage}</span>
            </span>
          </div>
        ) : null}

        {/* Connected to Live Agent Banner */}
        {call.connectedAgent && (
          <div className="bg-emerald-950/60 border border-emerald-800/90 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-2 text-xs shadow-lg shadow-emerald-950/30">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <div>
                <div className="font-bold text-emerald-300 flex items-center space-x-1.5">
                  <span>Connected to Live Care Specialist</span>
                  <span className="text-white bg-emerald-800/80 px-2 py-0.5 rounded-md text-[11px]">
                    {call.connectedAgent.name}
                  </span>
                </div>
                <div className="text-[11px] text-emerald-400/80">
                  Two-way voice connection active · You can speak directly to the specialist
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold flex items-center space-x-1.5 ${
                call.isCallerMicActive
                  ? (call.isCallerMuted ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-emerald-900/80 text-emerald-200 border-emerald-700')
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                {call.isCallerMuted ? <MicOff className="w-3 h-3 text-amber-400" /> : <Mic className="w-3 h-3 text-emerald-400 animate-pulse" />}
                <span>{call.isCallerMuted ? 'Mic: Muted' : 'Mic: Live (Active)'}</span>
              </span>

              <button
                type="button"
                onClick={call.toggleCallerMute}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-[11px] font-medium transition-all cursor-pointer"
              >
                {call.isCallerMuted ? 'Unmute' : 'Mute'}
              </button>
            </div>
          </div>
        )}

        {/* Live Audio & Transcript Display */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex-1 flex flex-col h-[480px] shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <span className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
              <Radio className="w-3.5 h-3.5 text-indigo-400" />
              <span>In-Flow Audio Dialogue Stream</span>
            </span>
            {call.isPlayingAudio && (
              <span className="text-[11px] text-cyan-400 flex items-center space-x-1.5 animate-pulse">
                <Volume2 className="w-3.5 h-3.5" />
                <span>VoiceNexus is speaking...</span>
              </span>
            )}
            {call.audioDegraded && (
              <span
                className="text-[11px] text-amber-400 flex items-center space-x-1.5"
                title="Neural voice synthesis is temporarily unavailable. Continuing in degraded text/DTMF mode per reliability SLO."
              >
                <MicOff className="w-3.5 h-3.5" />
                <span>Degraded mode: voice audio unavailable, text/DTMF still active</span>
              </span>
            )}
          </div>

          {/* Transcript Scroll Area */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-2">
            {call.turns.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <Phone className="w-8 h-8 mb-2 text-slate-600 stroke-[1.5]" />
                <p>Click <strong className="text-emerald-400">Dial Care Line</strong> to simulate an inbound customer call.</p>
              </div>
            ) : (
              <TranscriptList turns={call.turns} variant="bubble-detailed" />
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Custom Caller Speech Input with Microphone */}
          <div className="mt-3 pt-3 border-t border-slate-800 flex space-x-2">
            <button
              type="button"
              disabled={call.callState !== 'IN_CALL'}
              onClick={speech.toggleListening}
              className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                speech.isListening
                  ? 'bg-rose-600 text-white animate-pulse'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              } disabled:opacity-40 cursor-pointer`}
              title="Speak into microphone via Web Speech API"
            >
              <Mic className="w-3.5 h-3.5" />
              <span>{speech.isListening ? 'Listening...' : 'Voice Mic'}</span>
            </button>

            <input
              type="text"
              disabled={call.callState !== 'IN_CALL'}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendUtterance(inputText)}
              placeholder={call.callState === 'IN_CALL' ? "Speak or type as caller (e.g., 'How much is my bill?')..." : "Start call to speak"}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
            <button
              disabled={call.callState !== 'IN_CALL' || !inputText.trim()}
              onClick={() => sendUtterance(inputText)}
              className="px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </div>
        </div>

        {/* Quick PRD Evaluation Scenarios (One-Click Testing) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
          <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
            <span>One-Click Test Utterances (PRD Scenarios):</span>
            <span className="text-[10px] text-slate-500">Fast Scenario Replay</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESET_UTTERANCES.map((u, i) => (
              <button
                key={i}
                disabled={call.callState !== 'IN_CALL'}
                onClick={() => sendUtterance(u.text)}
                className="text-left p-2 rounded-xl bg-slate-850 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-700/60 text-slate-300 hover:text-white text-[11px] transition-all disabled:opacity-40 disabled:hover:bg-slate-850 disabled:hover:border-slate-800 cursor-pointer"
              >
                <div className="font-semibold text-indigo-400">{u.label}</div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">"{u.text}"</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
