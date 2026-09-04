import React from 'react';

interface DistributionBarListProps {
  items: Array<[string, number]>;
  total: number;
  unitLabel: string;
  barColorClass: string;
  labelColorClass: string;
  emptyMessage?: string;
}

/** Renders a labeled percentage-bar breakdown, shared by OpsDashboard's intent-distribution and escalation-reason panels. */
export const DistributionBarList: React.FC<DistributionBarListProps> = ({
  items, total, unitLabel, barColorClass, labelColorClass, emptyMessage
}) => {
  if (items.length === 0 && emptyMessage) {
    return <div className="text-slate-500 text-xs py-6 text-center">{emptyMessage}</div>;
  }

  return (
    <div className="space-y-3">
      {items.map(([label, count]) => {
        const pct = total > 0 ? (count / total) * 100 : 0;
        return (
          <div key={label} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className={`font-medium ${labelColorClass}`}>{label}</span>
              <span className="text-slate-400">{count} {unitLabel} ({pct.toFixed(0)}%)</span>
            </div>
            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-850">
              <div
                className={`${barColorClass} h-full rounded-full transition-all duration-500`}
                style={{ width: `${Math.max(5, pct)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
