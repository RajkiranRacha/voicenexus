import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorBoundaryState {
  error: Error | null;
}

/** Catches render-time crashes in any tab so a bug shows a recoverable message instead of a blank white page. */
export class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[VoiceNexus] Unhandled UI error:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-slate-900 border border-rose-900/60 rounded-2xl p-6 text-center space-y-4 shadow-xl">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-rose-950/60 border border-rose-800 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-rose-400" />
            </div>
            <div>
              <h2 className="font-bold text-slate-100">Something went wrong</h2>
              <p className="text-xs text-slate-400 mt-1.5">
                This screen hit an unexpected error and couldn't continue. Your call data on the server is unaffected — reloading usually fixes it.
              </p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reload VoiceNexus</span>
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
