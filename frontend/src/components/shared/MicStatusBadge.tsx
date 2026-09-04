import React from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';

interface MicStatusBadgeProps {
  isActive: boolean;
  isMuted: boolean;
  label?: string;
  className?: string;
}

/** Three-state (inactive / muted / live) microphone status pill shared by the caller phone and agent desktop. */
export const MicStatusBadge: React.FC<MicStatusBadgeProps> = ({ isActive, isMuted, label = 'Microphone', className = '' }) => {
  return (
    <span className={`px-2.5 py-1 rounded-lg border font-semibold flex items-center space-x-1.5 ${
      isActive
        ? (isMuted ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-emerald-900/60 text-emerald-300 border-emerald-700')
        : 'bg-rose-950 text-rose-300 border-rose-800'
    } ${className}`}>
      {isActive ? (
        isMuted ? <MicOff className="w-3 h-3 text-amber-400" /> : <Mic className="w-3 h-3 text-emerald-400 animate-pulse" />
      ) : (
        <AlertCircle className="w-3 h-3 text-rose-400" />
      )}
      <span>{isActive ? (isMuted ? `${label}: Muted` : `${label}: Live (Active)`) : `${label}: Inactive / Denied`}</span>
    </span>
  );
};
