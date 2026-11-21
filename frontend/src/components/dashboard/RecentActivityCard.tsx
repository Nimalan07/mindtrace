"use client";

import React from "react";
import { History, Check, X, HelpCircle, Activity } from "lucide-react";
import { ActivityItem } from "@/types/analytics.types";
import { formatProbability } from "@/lib/utils";

interface RecentActivityCardProps {
  activity: ActivityItem[];
}

export function RecentActivityCard({ activity }: RecentActivityCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
      <div>
        <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <History className="w-5 h-5 text-teal-600" />
          <span>Recent Diagnostic & Assessment Activity</span>
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Auditable chronological log of student evaluations and BKT parameter shifts
        </p>
      </div>

      {activity.length === 0 ? (
        <div className="py-8 px-4 rounded-xl bg-slate-50 border border-slate-100 text-center space-y-2">
          <Activity className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="text-xs font-semibold text-slate-700">
            No Recent Activity Logged Yet
          </p>
          <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
            Diagnostic reasoning evaluations and adaptive practice responses will stream directly here as you interact with the platform.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
          {activity.map((item, idx) => {
            const isCorrect = item.is_correct ?? null;
            const posterior = typeof item.posterior_mastery === "number"
              ? formatProbability(item.posterior_mastery)
              : null;
            const prior = typeof item.prior_mastery === "number"
              ? formatProbability(item.prior_mastery)
              : null;

            return (
              <div
                key={idx}
                className="p-3 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                      isCorrect === true
                        ? "bg-emerald-100 text-emerald-700"
                        : isCorrect === false
                        ? "bg-rose-100 text-rose-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {isCorrect === true ? (
                      <Check className="w-4 h-4" />
                    ) : isCorrect === false ? (
                      <X className="w-4 h-4" />
                    ) : (
                      <HelpCircle className="w-4 h-4" />
                    )}
                  </div>

                  <div className="min-w-0">
                    <span className="font-semibold text-slate-900 block truncate">
                      {item.concept_name || item.concept_id}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {item.question_id ? `Question: ${item.question_id}` : "Assessment"}
                      {item.timestamp ? ` • ${new Date(item.timestamp).toLocaleTimeString()}` : ""}
                    </span>
                  </div>
                </div>

                {posterior && (
                  <div className="text-right shrink-0 font-mono text-[11px]">
                    <span className="text-slate-400">{prior ? `${prior} → ` : ""}</span>
                    <span className="font-bold text-slate-800">{posterior}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
