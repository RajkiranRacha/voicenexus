import React, { useState, useRef } from 'react';
import {
  Headphones, ShieldCheck, UserCheck,
  MessageSquare, CheckCircle2, Sparkles, Inbox, Radio, Lightbulb,
  Mic, MicOff, PhoneOff, Volume2, Send, AlertCircle
} from 'lucide-react';
import { useAgentWebSocket } from '../hooks/useAgentWebSocket';
import { getNextBestAction } from '../lib/nextBestAction';
import { TranscriptList } from './shared/TranscriptList';
import { MicStatusBadge } from './shared/MicStatusBadge';

export const AgentDesktop: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ESCALATIONS' | 'LIVE_STREAM'>('ESCALATIONS');
  const [agentSpeechText, setAgentSpeechText] = useState<string>('');
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);

  const agent = useAgentWebSocket(remoteAudioRef);

  const activeLiveSessions = Object.keys(agent.liveCalls);

  const handleSendAgentSpeech = () => {
    agent.sendAgentLiveSpeech(agentSpeechText);
    setAgentSpeechText('');
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Banner with Navigation Tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
            <Headphones className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>Agent Desktop & CTI Screen-Pop</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                agent.isConnected ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400'
              }`}>
                {agent.isConnected ? 'CTI Bridge Live' : 'Disconnected'}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Zero-repetition customer handoff with verified identity and AI Next-Best-Action guidance.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('ESCALATIONS')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'ESCALATIONS'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Inbox className="w-3.5 h-3.5" />
            <span>Escalation Queue ({agent.escalations.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('LIVE_STREAM')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'LIVE_STREAM'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>Live Calls ({activeLiveSessions.length})</span>
          </button>
        </div>
      </div>

      {activeTab === 'ESCALATIONS' ? (
        /* Escalations Queue Layout */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left List: Incoming Escalation Queue */}
          <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Inbox className="w-3.5 h-3.5 text-indigo-400" />
                <span>Pending Escalations ({agent.escalations.length})</span>
              </span>
            </div>

            <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
              {agent.escalations.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-slate-600 stroke-[1.5]" />
                  No escalated calls waiting in queue.
                  <div className="text-[11px] text-slate-600 mt-1">
                    Calls requiring human care will automatically pop here.
                  </div>
                </div>
              ) : (
                agent.escalations.map((esc) => {
                  const isSelected = agent.selectedEscalation?.session_id === esc.session_id;
                  const isAccepted = agent.acceptedCalls.includes(esc.session_id);

                  return (
                    <button
                      key={esc.session_id}
                      onClick={() => agent.setSelectedEscalation(esc)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all cursor-pointer ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-950/40 shadow-md'
                          : 'border-slate-800 bg-slate-950/50 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-200">
                          {esc.customer_profile.customer_name}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                          isAccepted ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}>
                          {isAccepted ? 'Answered' : 'Awaiting Agent'}
                        </span>
                      </div>
                      <div className="text-slate-400 text-[11px] truncate">
                        {esc.call_context.primary_intent}
                      </div>
                      <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                        <span>Queue: {esc.recommended_agent_queue}</span>
                        <span>{esc.call_context.duration_in_ivr_seconds}s in IVR</span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel: Selected Call Handoff Payload & Live Transcript */}
          <div className="lg:col-span-8 space-y-4">
            {agent.selectedEscalation ? (
              <div className="space-y-4">
                {/* Structured Handoff Card (VN-5) */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                  <div className="flex items-start justify-between pb-4 border-b border-slate-800">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-base font-bold text-slate-100">
                          {agent.selectedEscalation.customer_profile.customer_name}
                        </h3>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center space-x-1 font-semibold">
                          <ShieldCheck className="w-3 h-3" />
                          <span>{agent.selectedEscalation.customer_profile.auth_status}</span>
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        ANI: {agent.selectedEscalation.ani} · Account: {agent.selectedEscalation.customer_profile.account_number}
                      </div>
                    </div>

                    <div>
                      {/* Audio element for playing caller's voice */}
                      <audio ref={remoteAudioRef} autoPlay />

                      {!agent.acceptedCalls.includes(agent.selectedEscalation.session_id) ? (
                        <button
                          onClick={() => agent.acceptCall(agent.selectedEscalation!.session_id)}
                          className="py-2 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-xs flex items-center space-x-2 shadow-lg shadow-emerald-950/40 transition-all cursor-pointer"
                        >
                          <UserCheck className="w-4 h-4" />
                          <span>Accept & Answer Call</span>
                        </button>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <button
                            type="button"
                            onClick={agent.toggleMute}
                            className={`py-2 px-3.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                              agent.isMuted
                                ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/40'
                                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                            }`}
                            title={agent.isMuted ? 'Unmute microphone' : 'Mute microphone'}
                          >
                            {agent.isMuted ? <MicOff className="w-3.5 h-3.5 text-white" /> : <Mic className="w-3.5 h-3.5 text-emerald-400" />}
                            <span>{agent.isMuted ? 'Muted' : 'Mute Mic'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={agent.endActiveCall}
                            className="py-2 px-3.5 bg-rose-700 hover:bg-rose-600 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-rose-950/40 transition-all cursor-pointer"
                            title="Disconnect active voice call"
                          >
                            <PhoneOff className="w-3.5 h-3.5" />
                            <span>End Call</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Two-Way Voice Connection Status & Mic Banner */}
                  {agent.acceptedCalls.includes(agent.selectedEscalation.session_id) && (
                    <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-xl p-3.5 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center space-x-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                          <span className="text-xs font-bold text-emerald-300">
                            Voice Call Active with Customer ({agent.selectedEscalation.customer_profile.customer_name})
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 text-xs">
                          <MicStatusBadge isActive={agent.isMicActive} isMuted={agent.isMuted} label="Microphone" />

                          <span className={`px-2.5 py-1 rounded-lg border font-semibold flex items-center space-x-1.5 ${
                            agent.isAudioConnected ? 'bg-cyan-950 text-cyan-300 border-cyan-800' : 'bg-slate-800 text-slate-300 border-slate-700'
                          }`}>
                            <Volume2 className="w-3 h-3 text-cyan-400" />
                            <span>{agent.isAudioConnected ? 'Two-Way Audio: Connected' : 'Audio Stream: Initializing...'}</span>
                          </span>
                        </div>
                      </div>

                      {agent.micError && (
                        <div className="text-[11px] text-amber-300 bg-amber-950/60 border border-amber-800/60 rounded-lg p-2 flex items-center space-x-1.5">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                          <span>{agent.micError}</span>
                        </div>
                      )}

                      {/* Agent Quick Response / Live Speech Input */}
                      <div className="pt-2 border-t border-emerald-900/50 space-y-2">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Speak to Caller / Quick Handoff Responses:</span>
                          <span className="text-[10px] text-slate-400">Streams voice & text directly to customer's ear</span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                          {[
                            `Hello ${agent.selectedEscalation.customer_profile.customer_name}, my name is Sarah. I see your verified details here and can assist you right away.`,
                            "I have reviewed your billing arrangement. Let's get this scheduled for you.",
                            "Our technicians are currently addressing the fiber node in your area. Service will restore shortly.",
                            "I can apply the promotional Gigabit upgrade to your account with free equipment."
                          ].map((canned, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => agent.sendAgentLiveSpeech(canned)}
                              className="text-left p-1.5 rounded-lg bg-slate-900 hover:bg-indigo-950/80 border border-slate-800 hover:border-indigo-700/80 text-[11px] text-slate-300 hover:text-white transition-all cursor-pointer"
                            >
                              "{canned}"
                            </button>
                          ))}
                        </div>

                        <div className="flex space-x-2 pt-1">
                          <input
                            type="text"
                            value={agentSpeechText}
                            onChange={(e) => setAgentSpeechText(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSendAgentSpeech()}
                            placeholder="Type or speak a live response to caller..."
                            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                          />
                          <button
                            type="button"
                            disabled={!agentSpeechText.trim()}
                            onClick={handleSendAgentSpeech}
                            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl text-xs font-semibold flex items-center space-x-1 transition-all cursor-pointer"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>Transmit</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* AI Executive Summary Pill */}
                  <div className="bg-indigo-950/40 border border-indigo-900/60 rounded-xl p-3.5 space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs font-bold text-indigo-300">
                      <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                      <span>AI-Prepared Context (Do Not Ask Customer to Repeat)</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <div className="text-slate-400 text-[11px]">Primary Intent</div>
                        <div className="font-semibold text-slate-200">
                          {agent.selectedEscalation.call_context.primary_intent}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[11px]">Escalation Reason</div>
                        <div className="font-semibold text-amber-300">
                          {agent.selectedEscalation.resolution_summary.failure_or_escalation_reason}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[11px]">Current Balance</div>
                        <div className="font-semibold text-slate-200">
                          ${agent.selectedEscalation.resolution_summary.current_balance?.toFixed(2) || '0.00'}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-slate-300 pt-1 border-t border-indigo-900/40">
                      <span className="text-slate-400 font-medium">Notes: </span>
                      {agent.selectedEscalation.resolution_summary.notes}
                    </div>
                  </div>

                  {/* AI Next-Best-Action Guidance (VN-10) */}
                  {(() => {
                    const nba = getNextBestAction(
                      agent.selectedEscalation.call_context.primary_intent,
                      agent.selectedEscalation.resolution_summary.current_balance || 0,
                      agent.selectedEscalation.resolution_summary.failure_or_escalation_reason || ""
                    );
                    return (
                      <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1.5 text-xs">
                        <div className="flex items-center space-x-1.5 text-cyan-300 font-bold">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                          <span>AI Next-Best-Action: {nba.action}</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{nba.recommendation}</p>
                        <div className="text-[11px] text-emerald-400/90 font-medium pt-1">
                          Tip: {nba.tip}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Live Transcript Overlay (VN-10) */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                      <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                      <span>IVR Transcript & Pre-Handoff Dialogue</span>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 max-h-[240px] overflow-y-auto space-y-2.5 text-xs">
                      {agent.selectedEscalation.transcript_snippet.length === 0 ? (
                        <div className="text-slate-500 text-center py-4">No prior turns captured.</div>
                      ) : (
                        <TranscriptList turns={agent.selectedEscalation.transcript_snippet} variant="label-row" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-xs shadow-xl">
                Select an escalated call on the left to inspect the structured handoff payload.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Real-Time Live Call Monitor View (VN-10) */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className="pb-3 border-b border-slate-800 mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span>In-Flight Call Streams ({activeLiveSessions.length})</span>
            </div>

            <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
              {activeLiveSessions.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  <Radio className="w-8 h-8 mx-auto mb-2 text-slate-600 stroke-[1.5]" />
                  No live calls currently streaming.
                  <div className="text-[11px] text-slate-600 mt-1">
                    Start a call in Phone Simulator to watch real-time turns pop here.
                  </div>
                </div>
              ) : (
                activeLiveSessions.map((sId) => {
                  const call = agent.liveCalls[sId];
                  const isSelected = agent.selectedLiveSessionId === sId;
                  return (
                    <button
                      key={sId}
                      onClick={() => agent.setSelectedLiveSessionId(sId)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all cursor-pointer ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-950/40 shadow-md'
                          : 'border-slate-800 bg-slate-950/50 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-200">
                          {call.metadata?.customer_name || 'In-Flight Caller'}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-medium">
                          {call.metadata?.state || 'IN_PROGRESS'}
                        </span>
                      </div>
                      <div className="text-slate-400 text-[11px]">
                        Session: {sId} · Turns: {call.turns.length}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Live Call Dialogue Stream Pane */}
          <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            {agent.selectedLiveSessionId && agent.liveCalls[agent.selectedLiveSessionId] ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm">
                      Live Stream: {agent.liveCalls[agent.selectedLiveSessionId].metadata?.customer_name || agent.selectedLiveSessionId}
                    </h3>
                    <div className="text-xs text-slate-400">
                      ANI: {agent.liveCalls[agent.selectedLiveSessionId].metadata?.ani || 'Unknown'} · State: {agent.liveCalls[agent.selectedLiveSessionId].metadata?.state}
                    </div>
                  </div>
                  <span className="text-xs text-emerald-400 flex items-center space-x-1 font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                    <span>Real-Time Overlay Active</span>
                  </span>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 max-h-[460px] overflow-y-auto space-y-3 text-xs">
                  <TranscriptList turns={agent.liveCalls[agent.selectedLiveSessionId].turns} variant="bubble-compact" />
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs">
                Select a live session to monitor dialogue turns in real-time.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
