import React, { useState, useEffect } from 'react';
import {
  PhoneCall, Headphones, BarChart3, Sliders, Radio, HelpCircle, WifiOff,
  ExternalLink, Layers
} from 'lucide-react';
import { PhoneSimulator } from './components/PhoneSimulator';
import { AgentDesktop } from './components/AgentDesktop';
import { OpsDashboard } from './components/OpsDashboard';
import { AdminConfig } from './components/AdminConfig';
import { WelcomeGuide } from './components/WelcomeGuide';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useHealthCheck } from './hooks/useHealthCheck';

const WELCOME_SEEN_KEY = 'voicenexus_welcome_seen';

type PortalMode = 'HUB' | 'CUSTOMER' | 'AGENT' | 'OPS' | 'ADMIN';

const getInitialPortal = (): PortalMode => {
  const path = window.location.pathname.toLowerCase();
  const search = new URLSearchParams(window.location.search);
  const portalParam = search.get('portal')?.toLowerCase();

  if (portalParam === 'customer' || portalParam === 'caller' || path.includes('/customer') || path.includes('/caller')) {
    return 'CUSTOMER';
  }
  if (portalParam === 'agent' || path.includes('/agent')) {
    return 'AGENT';
  }
  if (portalParam === 'ops' || path.includes('/ops')) {
    return 'OPS';
  }
  if (portalParam === 'admin' || path.includes('/admin')) {
    return 'ADMIN';
  }
  return 'HUB';
};

export const App: React.FC = () => {
  const [portalMode, setPortalMode] = useState<PortalMode>(getInitialPortal);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [showWelcome, setShowWelcome] = useState<boolean>(() => {
    try {
      return !localStorage.getItem(WELCOME_SEEN_KEY);
    } catch {
      return false;
    }
  });
  const backendStatus = useHealthCheck();

  const dismissWelcome = () => {
    setShowWelcome(false);
    try {
      localStorage.setItem(WELCOME_SEEN_KEY, '1');
    } catch {
      // ignore
    }
  };

  const navigateTo = (mode: PortalMode) => {
    setPortalMode(mode);
    let newUrl = '/';
    if (mode === 'CUSTOMER') newUrl = '/customer';
    else if (mode === 'AGENT') newUrl = '/agent';
    else if (mode === 'OPS') newUrl = '/ops';
    else if (mode === 'ADMIN') newUrl = '/admin';
    window.history.pushState(null, '', newUrl);
  };

  useEffect(() => {
    const onPopState = () => {
      setPortalMode(getInitialPortal());
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

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

  const openPortalInNewTab = (url: string) => {
    window.open(url, '_blank');
  };

  const getPortalLabel = () => {
    switch (portalMode) {
      case 'CUSTOMER': return 'PhoneCall';
      case 'AGENT': return 'Agent Workspace';
      case 'OPS': return 'Care-Ops';
      case 'ADMIN': return 'Admin Manager';
      default: return 'Portal Gateway';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {showWelcome && (
        <WelcomeGuide
          onClose={dismissWelcome}
          onGoToSimulator={() => { navigateTo('CUSTOMER'); dismissWelcome(); }}
        />
      )}

      {backendStatus === 'OFFLINE' && (
        <div className="bg-rose-950 border-b border-rose-800 text-rose-200 text-xs py-2 px-4 flex items-center justify-center space-x-2">
          <WifiOff className="w-3.5 h-3.5" />
          <span>Can't reach the VoiceNexus backend right now. Ensure the server is running on http://localhost:8000.</span>
        </div>
      )}

      {/* Enterprise Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
          {/* Logo & Portal Branding */}
          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => navigateTo('HUB')}
              className="flex items-center space-x-3 text-left cursor-pointer group"
              title="Return to Portal Gateway"
            >
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-950 group-hover:scale-105 transition-transform">
                <Radio className="w-5 h-5 text-white animate-pulse" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-extrabold text-base tracking-tight text-white group-hover:text-indigo-300 transition-colors">
                    VoiceNexus
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 hidden sm:inline">
                    {getPortalLabel()}
                  </span>
                  <span
                    className={`flex items-center space-x-1 text-[11px] font-medium ${
                      backendStatus === 'ONLINE' ? 'text-emerald-400' :
                      backendStatus === 'OFFLINE' ? 'text-rose-400' : 'text-slate-500'
                    }`}
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
            </button>
          </div>

          {/* Context Navigation Controls */}
          <div className="flex items-center gap-2 min-w-0">
            {/* Customer Call Portal (PhoneCall): ONLY "Open Agent Workspace" + Portal Gateway */}
            {portalMode === 'CUSTOMER' && (
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => openPortalInNewTab('/agent')}
                  className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-indigo-950/50 cursor-pointer"
                  title="Open Agent Workspace in a separate tab"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-white" />
                  <span>Open Agent Workspace</span>
                </button>

                <button
                  type="button"
                  onClick={() => navigateTo('HUB')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
                  title="Return to Portal Gateway"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Portal Gateway</span>
                </button>
              </div>
            )}

            {/* Agent Workspace: Separately maintained */}
            {portalMode === 'AGENT' && (
              <div className="flex items-center space-x-2">
                {pendingCount > 0 && (
                  <span className="px-2.5 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-bold animate-pulse flex items-center space-x-1">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                    <span>{pendingCount} Call{pendingCount > 1 ? 's' : ''} in Queue</span>
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => navigateTo('HUB')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
                  title="Return to Portal Gateway"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Portal Gateway</span>
                </button>
              </div>
            )}

            {/* Care-Ops: Separately maintained */}
            {portalMode === 'OPS' && (
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => navigateTo('HUB')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
                  title="Return to Portal Gateway"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Portal Gateway</span>
                </button>
              </div>
            )}

            {/* Admin Manager: Separately maintained */}
            {portalMode === 'ADMIN' && (
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => navigateTo('HUB')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
                  title="Return to Portal Gateway"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Portal Gateway</span>
                </button>
              </div>
            )}

            <button
              onClick={() => setShowWelcome(true)}
              className="p-2 rounded-xl border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-all cursor-pointer shrink-0"
              title="Quick Start Guide"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content View (Only renders active portal to prevent DOM & audio loopback collision) */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {portalMode === 'CUSTOMER' && <PhoneSimulator />}
        {portalMode === 'AGENT' && <AgentDesktop />}
        {portalMode === 'OPS' && <OpsDashboard />}
        {portalMode === 'ADMIN' && <AdminConfig />}

        {portalMode === 'HUB' && (
          <div className="max-w-4xl mx-auto space-y-6 py-4">
            <div className="text-center space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 px-3 py-1 rounded-full bg-indigo-950 border border-indigo-800">
                VoiceNexus Master Gateway
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                Select Your Portal
              </h1>
              <p className="text-sm text-slate-400 max-w-xl mx-auto">
                Each portal opens in a new tab so this gateway remains open. Switch easily between tabs with zero audio interference.
              </p>
            </div>

            {/* Portal Cards Grid (ONLY 4 Portals: PhoneCall, Agent Workspace, Care-Ops, Admin Manager) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Card 1: PhoneCall */}
              <div
                onClick={() => openPortalInNewTab('/customer')}
                className="bg-slate-900 border border-slate-800 hover:border-emerald-500 rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-4 hover:shadow-emerald-950/40 transition-all cursor-pointer group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-600/20 text-emerald-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <PhoneCall className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Inbound Caller
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
                    PhoneCall
                  </h3>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    Customer inbound care phone simulator (+1 800 NEXUS-CARE). Experience sub-second IVR voice dialogue, bill queries, payment arrangements, router reboot triage, and resolution wrap-up auto-disconnect.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-emerald-400 group-hover:translate-x-1 transition-transform">
                  <span>Launch PhoneCall in New Tab</span>
                  <ExternalLink className="w-4 h-4" />
                </div>
              </div>

              {/* Card 2: Agent Workspace */}
              <div
                onClick={() => openPortalInNewTab('/agent')}
                className="bg-slate-900 border border-slate-800 hover:border-indigo-500 rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-4 hover:shadow-indigo-950/40 transition-all cursor-pointer group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Headphones className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800">
                      Care Specialist
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors">
                      Agent Workspace
                    </h3>
                    {pendingCount > 0 && (
                      <span className="px-2 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-bold animate-bounce">
                        {pendingCount} waiting
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    Live contact center agent desktop. Receive zero-repetition escalations with pre-verified customer records, AI Next-Best-Action guidance, and two-way WebRTC audio.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-indigo-400 group-hover:translate-x-1 transition-transform">
                  <span>Launch Agent Workspace in New Tab</span>
                  <ExternalLink className="w-4 h-4" />
                </div>
              </div>

              {/* Card 3: Care-Ops */}
              <div
                onClick={() => openPortalInNewTab('/ops')}
                className="bg-slate-900 border border-slate-800 hover:border-cyan-500 rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-4 hover:shadow-cyan-950/40 transition-all cursor-pointer group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-2xl bg-cyan-600/20 text-cyan-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <BarChart3 className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                      Operations
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors">
                    Care-Ops
                  </h3>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    Contact center telemetry and command center. Monitor real-time IVR containment rate, escalation rates, Average Handle Time (AHT), intent distributions, and post-call CSAT ratings.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-cyan-400 group-hover:translate-x-1 transition-transform">
                  <span>Launch Care-Ops in New Tab</span>
                  <ExternalLink className="w-4 h-4" />
                </div>
              </div>

              {/* Card 4: Admin Manager */}
              <div
                onClick={() => openPortalInNewTab('/admin')}
                className="bg-slate-900 border border-slate-800 hover:border-amber-500 rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-4 hover:shadow-amber-950/40 transition-all cursor-pointer group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-2xl bg-amber-600/20 text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Sliders className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-amber-950 text-amber-300 border border-amber-800">
                      System Admin
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-amber-300 transition-colors">
                    Admin Manager
                  </h3>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    Tune neural voice personas, compliance disclosures, and feed telecom domain knowledge (eSIM, roaming, router diagnostics, MNP porting, and equipment returns).
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-semibold text-amber-400 group-hover:translate-x-1 transition-transform">
                  <span>Launch Admin Manager in New Tab</span>
                  <ExternalLink className="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-3 text-center text-xs text-slate-500">
        VoiceNexus · NforceOne Portfolio · Conversational IVR Platform v1.0 · Dedicated Portal Architecture
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
