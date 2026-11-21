"use client";

import React, { useState } from "react";
import { GitFork, Sparkles } from "lucide-react";
import { InterventionPlan } from "@/types/adaptive.types";
import { cn } from "@/lib/utils";

interface KnowledgeRepairCardProps {
  plan: InterventionPlan;
  onClose?: () => void;
}

export function KnowledgeRepairCard({ plan, onClose }: KnowledgeRepairCardProps) {
  const [activeStage, setActiveStage] = useState<number>(1);

  return (
    <div className="bg-white rounded-2xl border-2 border-amber-300 shadow-lg p-6 sm:p-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-200 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Targeted Pedagogical Intervention</span>
          </div>
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">
            Knowledge Repair: Concept {plan.target_concept_id}
          </h3>
          <p className="text-xs text-slate-500">
            Multi-stage cognitive remediation synthesizing refutation texts, contrasting cases, and prerequisite bridges
          </p>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 text-sm font-bold"
          >
            ✕
          </button>
        )}
      </div>

      {/* Actionable Summary */}
      <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-xs sm:text-sm text-amber-950 font-medium leading-relaxed">
        {plan.actionable_summary}
      </div>

      {/* Stage Selector Tabs */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto pb-1">
        {plan.stages.map((stg) => {
          const isActive = activeStage === stg.stage_order;
          return (
            <button
              key={stg.stage_order}
              type="button"
              onClick={() => setActiveStage(stg.stage_order)}
              className={cn(
                "px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 whitespace-nowrap",
                isActive
                  ? "border-amber-600 text-amber-900 bg-amber-50/60"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              )}
            >
              Stage {stg.stage_order}: {stg.stage_name}
            </button>
          );
        })}
      </div>

      {/* Active Stage Content */}
      {plan.stages.map((stg) => {
        if (stg.stage_order !== activeStage) return null;
        return (
          <div key={stg.stage_order} className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono font-bold text-slate-600 uppercase">
                Strategy: {stg.intervention_strategy.replace(/_/g, " ")}
              </span>
              {stg.target_misconception_id && (
                <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-mono text-[10px] font-bold">
                  Targets: {stg.target_misconception_id}
                </span>
              )}
            </div>

            <div className="text-xs sm:text-sm text-slate-800 leading-relaxed font-serif whitespace-pre-line bg-white p-4 rounded-xl border border-slate-200/80">
              {stg.content_markdown}
            </div>

            {stg.check_question && (
              <div className="p-3.5 rounded-xl bg-teal-50/70 border border-teal-200 text-xs space-y-1">
                <span className="font-bold text-teal-900 uppercase text-[10px] tracking-wider block">
                  Comprehension Check
                </span>
                <p className="font-medium text-teal-950">{stg.check_question}</p>
                {stg.expected_insight && (
                  <p className="text-[11px] text-teal-700 italic pt-1">
                    Expected Insight: {stg.expected_insight}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Prerequisite Refreshers */}
      {plan.prerequisite_refreshers?.length > 0 && (
        <div className="pt-2 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-600">
          <GitFork className="w-4 h-4 text-teal-600 shrink-0" />
          <span>
            <strong className="text-slate-800 font-semibold">Prerequisite Refreshers:</strong>{" "}
            {plan.prerequisite_refreshers.map((p) => (
              <span
                key={p}
                className="ml-1 px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]"
              >
                {p}
              </span>
            ))}
          </span>
        </div>
      )}
    </div>
  );
}
