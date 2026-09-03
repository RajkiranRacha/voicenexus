import React, { useState, useEffect } from 'react';
import { 
  PhoneCall, Headphones, BarChart3, Sliders, Radio
} from 'lucide-react';
import { PhoneSimulator } from './components/PhoneSimulator';
import { AgentDesktop } from './components/AgentDesktop';
import { OpsDashboard } from './components/OpsDashboard';
import { AdminConfig } from './components/AdminConfig';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'SIMULATOR' | 'AGENT' | 'OPS' | 'ADMIN'>('SIMULATOR');
  const [pendingCount, setPendingCount] = useState<number>(0);

  useEffect(() => {
    const checkPending = () => {
      fetch('/api/agent/pending')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setPendingCount(data.length);
          }
        })
        .catch(() => {});
    };
    checkPending();
    const interval = setInterval(checkPending, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Enterprise Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-950">
              <Radio className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base tracking-tight text-white">VoiceNexus</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800">
                  v1.0 Core
                </span>
                <span className="flex items-center space-x-1 text-[11px] text-emerald-400 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                  <span>Online</span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Turn IVR into resolution, not frustration.
              </p>
            </div>
          </div>

          {/* Navigation Mode Tabs */}
          <nav className="flex items-center space-x-1 bg-slate-950/80 p-1.5 rounded-2xl border border-slate-800">
            <button
              onClick={() => setActiveTab('SIMULATOR')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeTab === 'SIMULATOR'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>Caller Phone</span>
            </button>

            <button
              onClick={() => setActiveTab('AGENT')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all relative cursor-pointer ${
                activeTab === 'AGENT'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Headphones className="w-3.5 h-3.5" />
              <span>Agent Desktop</span>
              {pendingCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold animate-bounce">
                  {pendingCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('OPS')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeTab === 'OPS'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Care-Ops (VN-6)</span>
            </button>

            <button
              onClick={() => setActiveTab('ADMIN')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeTab === 'ADMIN'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Admin (VN-7)</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'SIMULATOR' && <PhoneSimulator />}
        {activeTab === 'AGENT' && <AgentDesktop />}
        {activeTab === 'OPS' && <OpsDashboard />}
        {activeTab === 'ADMIN' && <AdminConfig />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-3 text-center text-xs text-slate-500">
        VoiceNexus · NforceOne Portfolio · Conversational IVR Platform v1.0 · Latency SLO ≤ 1.0s
      </footer>
    </div>
  );
};

export default App;
