"use client";

import React from "react";
import { ShieldAlert, Users } from "lucide-react";

interface MisconceptionItem {
  misconception_id: string;
  affected_students_count: number;
  [key: string]: unknown;
}

interface MisconceptionDistributionChartProps {
  misconceptions: MisconceptionItem[];
}

export function MisconceptionDistributionChart({
  misconceptions,
}: MisconceptionDistributionChartProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
      <div>
        <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
          <span>Prevalence of Diagnosed Misconceptions</span>
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Verified cognitive reasoning traps ranked by classroom occurrence
        </p>
      </div>

      {misconceptions.length === 0 ? (
        <div className="py-10 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-100">
          No widespread misconception clusters detected in this cohort.
        </div>
      ) : (
        <div className="space-y-3">
          {misconceptions.map((item, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-slate-50 transition-colors flex items-center justify-between text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 text-[11px]">
                    {item.misconception_id}
                  </span>
                  <span className="font-semibold text-slate-900">
                    Diagnosed Reasoning Fallacy
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-slate-200 font-semibold text-slate-800 text-xs">
                <Users className="w-3.5 h-3.5 text-teal-600" />
                <span>{item.affected_students_count} affected</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
