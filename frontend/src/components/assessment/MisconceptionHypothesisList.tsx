"use client";

import React from "react";
import { GitCompare, Info, AlertCircle } from "lucide-react";
import { formatProbability, cn } from "@/lib/utils";

interface MisconceptionHypothesisListProps {
  hypotheses: Record<string, number>;
  diagnosticStatus: string;
  calibrationStatus?: "empirically_calibrated" | "illustrative";
  uncertaintyNotes?: string[];
}

export function MisconceptionHypothesisList({
  hypotheses,
  diagnosticStatus,
  calibrationStatus = "illustrative",
  uncertaintyNotes = [],
}: MisconceptionHypothesisListProps) {
  // Sort hypotheses descending by posterior probability
  const sorted = Object.entries(hypotheses).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-teal-600" />
            <span>Bayesian Hypothesis Distribution</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Competing posterior probabilities updated via Bayes&apos; theorem across candidate hypotheses
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={cn(
              "px-2.5 py-1 rounded-full text-xs font-semibold capitalize",
              diagnosticStatus === "sufficient_evidence"
                ? "bg-teal-100 text-teal-800"
                : diagnosticStatus === "collecting_evidence"
                ? "bg-blue-100 text-blue-800"
                : "bg-amber-100 text-amber-800"
            )}
          >
            {diagnosticStatus.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      {/* Scientific Integrity Notice */}
      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-2.5 text-xs text-slate-600">
        <Info className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-semibold text-slate-800">
            Scientific Calibration Status:{" "}
            <span className="font-mono text-teal-700 font-bold uppercase">
              {calibrationStatus.replace(/_/g, " ")}
            </span>
          </p>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Posterior probabilities reflect informational Bayesian updates from evidence observations. A single test answer does not constitute a permanent diagnosis. Unspecified variations are retained under the <code className="font-mono text-slate-700 bg-slate-200/60 px-1 py-0.2 rounded">unknown_or_other</code> hypothesis.
          </p>
        </div>
      </div>

      {/* Hypotheses Progress Bars */}
      <div className="space-y-3">
        {sorted.map(([hypothesisId, prob]) => {
          const isUnknown = hypothesisId === "unknown_or_other";
          const percentage = Math.min(100, Math.max(0, prob * 100));

          return (
            <div
              key={hypothesisId}
              className={cn(
                "p-3.5 rounded-xl border transition-all space-y-1.5",
                prob >= 0.75
                  ? "bg-teal-50/60 border-teal-300"
                  : isUnknown
                  ? "bg-slate-50 border-slate-200"
                  : "bg-white border-slate-200/80"
              )}
            >
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "font-mono font-bold px-2 py-0.5 rounded text-[11px]",
                      isUnknown
                        ? "bg-slate-200 text-slate-700"
                        : "bg-teal-100 text-teal-800"
                    )}
                  >
                    {hypothesisId}
                  </span>
                  <span className="font-semibold text-slate-900">
                    {isUnknown
                      ? "Alternative or Unclassified Deficit"
                      : `Candidate Misconception ${hypothesisId}`}
                  </span>
                </div>

                <span className="font-mono font-extrabold text-slate-900 text-xs">
                  {formatProbability(prob)}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className={cn(
                    "h-2 rounded-full transition-all duration-500",
                    isUnknown
                      ? "bg-slate-400"
                      : prob >= 0.75
                      ? "bg-teal-600"
                      : "bg-blue-500"
                  )}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Uncertainty notes if present */}
      {uncertaintyNotes.length > 0 && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Epistemic Uncertainty Notes
          </span>
          {uncertaintyNotes.map((note, idx) => (
            <p key={idx} className="text-xs text-amber-700 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{note}</span>
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
