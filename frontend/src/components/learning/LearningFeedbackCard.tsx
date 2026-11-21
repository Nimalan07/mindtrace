"use client";

import React from "react";
import { CheckCircle2, XCircle, ArrowRight, ShieldAlert, TrendingUp } from "lucide-react";
import { AssessmentEvaluation } from "@/types/adaptive.types";
import { formatProbability, cn } from "@/lib/utils";

interface LearningFeedbackCardProps {
  evaluation: AssessmentEvaluation;
  onNextQuestion: () => void;
  onOpenIntervention?: () => void;
}

export function LearningFeedbackCard({
  evaluation,
  onNextQuestion,
  onOpenIntervention,
}: LearningFeedbackCardProps) {
  const isCorrect = evaluation.is_correct;
  const prior = evaluation.prior_mastery;
  const updated = evaluation.updated_mastery;
  const delta = updated - prior;

  return (
    <div
      className={cn(
        "rounded-2xl border-2 p-6 sm:p-8 space-y-6 shadow-md transition-all animate-in fade-in duration-200",
        isCorrect
          ? "bg-emerald-50/50 border-emerald-300"
          : "bg-rose-50/50 border-rose-300"
      )}
    >
      {/* Result Status Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-md shrink-0",
              isCorrect ? "bg-emerald-600 shadow-emerald-600/30" : "bg-rose-600 shadow-rose-600/30"
            )}
          >
            {isCorrect ? <CheckCircle2 className="w-7 h-7" /> : <XCircle className="w-7 h-7" />}
          </div>
          <div>
            <span
              className={cn(
                "text-xs font-bold uppercase tracking-wider block",
                isCorrect ? "text-emerald-700" : "text-rose-700"
              )}
            >
              Evaluation Complete
            </span>
            <h3 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              {isCorrect ? "Correct Response!" : "Needs Revision"}
            </h3>
          </div>
        </div>

        {/* Difficulty transition */}
        <div className="text-right shrink-0">
          <span className="text-[10px] text-slate-500 block uppercase font-semibold">
            Difficulty Tier
          </span>
          <span className="text-xs font-mono font-bold text-slate-800 uppercase">
            {evaluation.prior_difficulty} → {evaluation.updated_difficulty}
          </span>
        </div>
      </div>

      {/* Backend Feedback Message */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 text-sm text-slate-800 leading-relaxed font-medium shadow-xs">
        {evaluation.feedback_message}
      </div>

      {/* BKT Mastery Update Visualizer */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-2 shadow-xs">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-700 flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-teal-600" />
            <span>Bayesian Knowledge Tracing (BKT) Posterior</span>
          </span>
          <div className="font-mono text-xs font-bold">
            <span className="text-slate-400">{formatProbability(prior)}</span>
            <span className="mx-1 text-slate-300">→</span>
            <span className={cn(delta >= 0 ? "text-emerald-700 font-extrabold" : "text-rose-700 font-extrabold")}>
              {formatProbability(updated)}
            </span>
            <span
              className={cn(
                "ml-1.5 text-[10px] px-1.5 py-0.2 rounded font-bold",
                delta >= 0 ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
              )}
            >
              {delta >= 0 ? `+${(delta * 100).toFixed(1)}%` : `${(delta * 100).toFixed(1)}%`}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div
            className={cn(
              "h-2.5 rounded-full transition-all duration-700",
              isCorrect ? "bg-emerald-500" : "bg-amber-500"
            )}
            style={{ width: `${Math.min(100, Math.max(0, updated * 100))}%` }}
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        {!isCorrect && onOpenIntervention ? (
          <button
            type="button"
            onClick={onOpenIntervention}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs shadow-md shadow-amber-600/20 transition-all"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>View Knowledge Repair Plan</span>
          </button>
        ) : (
          <div />
        )}

        <button
          type="button"
          onClick={onNextQuestion}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-[#14213D] hover:bg-slate-800 text-white font-semibold text-xs shadow-md transition-all"
        >
          <span>Next Adaptive Item</span>
          <ArrowRight className="w-4 h-4 text-teal-400" />
        </button>
      </div>
    </div>
  );
}
