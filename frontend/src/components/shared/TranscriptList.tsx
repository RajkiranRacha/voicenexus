import React from 'react';

export interface TranscriptEntry {
  speaker: string;
  text: string;
  latency?: { total_turn_ms: number };
}

interface TranscriptListProps {
  turns: TranscriptEntry[];
  variant: 'bubble-detailed' | 'bubble-compact' | 'label-row';
}

/**
 * Renders a list of dialogue turns in one of three visual styles that
 * previously lived duplicated inline across PhoneSimulator, AgentDesktop and
 * OpsDashboard:
 *  - bubble-detailed: chat bubbles with per-turn latency (caller phone).
 *  - bubble-compact: chat bubbles without latency (agent live-call monitor).
 *  - label-row: "Speaker: text" rows (escalation snippet + CDR inspector).
 */
export const TranscriptList: React.FC<TranscriptListProps> = ({ turns, variant }) => {
  if (variant === 'label-row') {
    return (
      <>
        {turns.map((t, i) => (
          <div key={i} className="flex space-x-2">
            <span className={`font-semibold text-[11px] min-w-[70px] ${
              t.speaker === 'caller' ? 'text-indigo-400' : t.speaker === 'system' ? 'text-amber-400' : 'text-slate-400'
            }`}>
              {t.speaker === 'caller' ? 'Caller:' : t.speaker === 'system' ? 'System:' : 'VoiceNexus:'}
            </span>
            <span className="text-slate-200 flex-1">{t.text}</span>
          </div>
        ))}
      </>
    );
  }

  if (variant === 'bubble-compact') {
    return (
      <>
        {turns.map((t, idx) => (
          <div key={idx} className={`flex ${t.speaker === 'caller' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-3.5 py-2 leading-relaxed ${
              t.speaker === 'caller'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-200 border border-slate-700'
            }`}>
              <div className="text-[10px] opacity-75 font-semibold mb-0.5">
                {t.speaker === 'caller' ? 'Caller' : t.speaker === 'system' ? 'System' : 'VoiceNexus AI'}
              </div>
              <div>{t.text}</div>
            </div>
          </div>
        ))}
      </>
    );
  }

  return (
    <>
      {turns.map((turn, idx) => (
        <div key={idx} className={`flex ${turn.speaker === 'caller' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-[82%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
              turn.speaker === 'caller'
                ? 'bg-indigo-600 text-white rounded-br-none'
                : turn.speaker === 'ai'
                ? 'bg-slate-800/90 text-slate-100 border border-slate-700/60 rounded-bl-none'
                : 'bg-amber-950/60 text-amber-200 border border-amber-800'
            }`}
          >
            <div className="flex items-center justify-between mb-1 opacity-75 text-[10px]">
              <span className="font-semibold">
                {turn.speaker === 'caller' ? 'Caller (Customer)' : turn.speaker === 'system' ? 'System Notice' : 'VoiceNexus AI IVR'}
              </span>
              {turn.latency && <span>{turn.latency.total_turn_ms} ms</span>}
            </div>
            <div className="text-sm">{turn.text}</div>
          </div>
        </div>
      ))}
    </>
  );
};
