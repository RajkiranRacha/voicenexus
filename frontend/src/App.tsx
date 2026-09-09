import React, { useState, useEffect } from 'react';
import {
  PhoneCall, Headphones, BarChart3, Sliders, Radio, HelpCircle, WifiOff
} from 'lucide-react';
import { PhoneSimulator } from './components/PhoneSimulator';
import { AgentDesktop } from './components/AgentDesktop';
import { OpsDashboard } from './components/OpsDashboard';
import { AdminConfig } from './components/AdminConfig';
import { WelcomeGuide } from './components/WelcomeGuide';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useHealthCheck } from './hooks/useHealthCheck';

const WELCOME_SEEN_KEY = 'voicenexus_welcome_seen';

const NAV_ITEMS = [
  { key: 'SIMULATOR' as const, label: 'Caller Phone', icon: PhoneCall },
  { key: 'AGENT' as const, label: 'Agent Desktop', icon: Headphones },
  { key: 'OPS' as const, label: 'Care-Ops', icon: BarChart3 },
  { key: 'ADMIN' as const, label: 'Admin', icon: Sliders },
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'SIMULATOR' | 'AGENT' | 'OPS' | 'ADMIN'>('SIMULATOR');
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [showWelcome, setShowWelcome] = useState<boolean>(false);
  const backendStatus = useHealthCheck();

  useEffect(() => {
    try {
      if (!localStorage.getItem(WELCOME_SEEN_KEY)) {
        setShowWelcome(true);
      }
    } catch {
      // ignore
    }
  }, []);

  const dismissWelcome = () => {
    setShowWelcome(false);
    try {
      localStorage.setItem(WELCOME_SEEN_KEY, '1');
    } catch {
      // ignore
    }
  };

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
      {showWelcome && (
        <WelcomeGuide
          onClose={dismissWelcome}
          onGoToSimulator={() => { setActiveTab('SIMULATOR'); dismissWelcome(); }}
        />
      )}

      {backendStatus === 'OFFLINE' && (
        <div className="bg-rose-950 border-b border-rose-800 text-rose-200 text-xs py-2 px-4 flex items-center justify-center space-x-2">
          <WifiOff className="w-3.5 h-3.5" />
          <span>Can't reach the VoiceNexus backend right now. Calls and settings won't work until the server is back — check that it's still running.</span>
        </div>
      )}

      {/* Enterprise Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center space-x-3 shrink-0">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-950">
              <Radio className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base tracking-tight text-white">VoiceNexus</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 hidden sm:inline">
                  v1.0 Core
                </span>
                <span
                  className={`flex items-center space-x-1 text-[11px] font-medium ${
                    backendStatus === 'ONLINE' ? 'text-emerald-400' :
                    backendStatus === 'OFFLINE' ? 'text-rose-400' : 'text-slate-500'
                  }`}
                  title={backendStatus === 'ONLINE' ? 'Backend reachable' : backendStatus === 'OFFLINE' ? 'Backend unreachable' : 'Checking backend...'}
                >
                  <span className={`w-2 h-2 rounded-full ${
                    backendStatus === 'ONLINE' ? 'bg-emerald-500 animate-ping' :
                    backendStatus === 'OFFLINE' ? 'bg-rose-500' : 'bg-slate-600 animate-pulse'
                  }`} />
                  <span>{backendStatus === 'ONLINE' ? 'Online' : backendStatus === 'OFFLINE' ? 'Offline' : 'Checking...'}</span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Turn IVR into resolution, not frustration.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 min-w-0">
            {/* Navigation Mode Tabs */}
            <nav className="flex items-center space-x-1 bg-slate-950/80 p-1.5 rounded-2xl border border-slate-800 overflow-x-auto max-w-full">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.key}
                  onClick={() => setActiveTab(item.key)}
                  className={`px-2.5 sm:px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all relative cursor-pointer whitespace-nowrap ${
                    activeTab === item.key
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <item.icon className="w-3.5 h-3.5 shrink-0" />
                  <span className="hidden md:inline">{item.label}</span>
                  {item.key === 'AGENT' && pendingCount > 0 && (
                    <span className="ml-1 px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold animate-bounce">
                      {pendingCount}
                    </span>
                  )}
                </button>
              ))}
            </nav>

            <button
              onClick={() => setShowWelcome(true)}
              className="p-2 rounded-xl border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-all cursor-pointer shrink-0"
              title="How does this demo work?"
              aria-label="Open quick-start guide"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div style={{ display: activeTab === 'SIMULATOR' ? 'block' : 'none' }}>
          <PhoneSimulator />
        </div>
        <div style={{ display: activeTab === 'AGENT' ? 'block' : 'none' }}>
          <AgentDesktop />
        </div>
        <div style={{ display: activeTab === 'OPS' ? 'block' : 'none' }}>
          <OpsDashboard />
        </div>
        <div style={{ display: activeTab === 'ADMIN' ? 'block' : 'none' }}>
          <AdminConfig />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-3 text-center text-xs text-slate-500">
        VoiceNexus · NforceOne Portfolio · Conversational IVR Platform v1.0 · Latency SLO ≤ 1.0s
      </footer>
    </div>
  );
};

const AppWithBoundary: React.FC = () => (
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

export default AppWithBoundary;
