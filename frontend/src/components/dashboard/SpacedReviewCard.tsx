"use client";

import React from "react";
import { CalendarClock, CheckCircle, Flame } from "lucide-react";
import { DueRevisionItem } from "@/types/analytics.types";

interface SpacedReviewCardProps {
  dueRevisions: DueRevisionItem[];
  totalDueCount: number;
}

export function SpacedReviewCard({
  dueRevisions,
  totalDueCount,
}: SpacedReviewCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <CalendarClock className="w-5 h-5 text-amber-600" />
            <span>Spaced Repetition Queue</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Decay-resilient memory retention via SuperMemo SM-2 intervals
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          {totalDueCount} Due
        </span>
      </div>

      {dueRevisions.length === 0 ? (
        <div className="py-8 px-4 rounded-xl bg-slate-50 border border-slate-100 text-center space-y-2">
          <div className="w-9 h-9 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center">
            <CheckCircle className="w-5 h-5" />
          </div>
          <p className="text-xs font-semibold text-slate-800">
            No Concept Reviews Due Today
          </p>
          <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
            All mastered and practiced concepts are currently within their memory half-life window.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {dueRevisions.map((rev) => (
            <div
              key={rev.concept_id}
              className="p-3 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition-colors flex items-center justify-between gap-3"
            >
              <div className="min-w-0">
                <span className="text-xs font-semibold text-slate-900 block truncate">
                  {rev.concept_name}
                </span>
                <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono mt-0.5">
                  <span>Interval: {rev.interval_days}d</span>
                  <span>•</span>
                  <span>Reps: {rev.repetition_count}</span>
                  {rev.urgency_score > 0 && (
                    <>
                      <span>•</span>
                      <span className="text-amber-600 font-semibold flex items-center gap-0.5">
                        <Flame className="w-3 h-3" />
                        Urgency {rev.urgency_score.toFixed(1)}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="shrink-0 text-right">
                <span className="text-[10px] font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                  Due Now
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
