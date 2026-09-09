import React from 'react';
import { PhoneCall, Headphones, BarChart3, Sliders, X, Sparkles } from 'lucide-react';

const STEPS = [
  {
    icon: PhoneCall,
    title: '1. Caller Phone',
    body: "Dial the care line as a simulated customer. Pick a preset caller (or type a custom number), then speak or type things like \"How much is my bill?\"",
  },
  {
    icon: Headphones,
    title: '2. Agent Desktop',
    body: 'When VoiceNexus can\'t resolve something in-flow, it escalates here with a full context handoff — no need to make the customer repeat themselves.',
  },
  {
    icon: BarChart3,
    title: '3. Care-Ops',
    body: 'Live containment rate, handle time, and escalation-driver analytics across every call, updating in real time.',
  },
  {
    icon: Sliders,
    title: '4. Admin',
    body: 'Tune the brand voice, language, greetings, and pronunciation overrides — changes apply to the next call immediately.',
  },
];

interface WelcomeGuideProps {
  onClose: () => void;
  onGoToSimulator: () => void;
}

export const WelcomeGuide: React.FC<WelcomeGuideProps> = ({ onClose, onGoToSimulator }) => {
  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center shadow-lg">
              <Sparkles className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-slate-100 text-sm">Welcome to VoiceNexus</h2>
              <p className="text-[11px] text-slate-400">A quick tour of this conversational IVR demo, in four stops.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors cursor-pointer"
            aria-label="Close welcome guide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {STEPS.map((step) => (
            <div key={step.title} className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
              <div className="flex items-center space-x-2 text-indigo-300 font-semibold text-xs">
                <step.icon className="w-3.5 h-3.5" />
                <span>{step.title}</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>

        <div className="bg-indigo-950/40 border border-indigo-900/60 rounded-xl p-3 text-[11px] text-indigo-200">
          Tip: no microphone needed — every screen has typed input and one-click test scenarios, so you can try the full flow silently.
        </div>

        <div className="flex justify-end space-x-2 pt-1">
          <button
            onClick={onClose}
            className="py-2 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition-all cursor-pointer"
          >
            Explore on my own
          </button>
          <button
            onClick={onGoToSimulator}
            className="py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition-all cursor-pointer"
          >
            <PhoneCall className="w-3.5 h-3.5" />
            <span>Start with a call</span>
          </button>
        </div>
      </div>
    </div>
  );
};
