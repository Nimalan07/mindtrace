"use client";

import React from "react";
import { CheckCircle2, XCircle, ArrowDown, Sparkles } from "lucide-react";
import { ExtractedReasoning, FirstErrorResult } from "@/types/diagnosis.types";
import { cn } from "@/lib/utils";

interface ReasoningStepTimelineProps {
  extractedReasoning: ExtractedReasoning;
  firstErrorResult: FirstErrorResult;
}

export function ReasoningStepTimeline({
  extractedReasoning,
  firstErrorResult,
}: ReasoningStepTimelineProps) {
  const steps = extractedReasoning.reasoning_steps;
  const firstErrorStepId = firstErrorResult.first_error_step_id;
  const downstreamStepIds = new Set(firstErrorResult.affected_downstream_step_ids || []);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-600" />
            <span>Extracted Reasoning Step Timeline</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            MINDTRACE structured extraction: {steps.length} ordered claims evaluated against the expert rubric
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium">
          Status: {extractedReasoning.extraction_status}
        </span>
      </div>

      {/* Vertical Timeline */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
        {steps.map((step) => {
          const isFirstError = step.step_id === firstErrorStepId;
          const isDownstream = downstreamStepIds.has(step.step_id);

          // Find corresponding evaluation if present
          const evalItem = firstErrorResult.step_evaluations?.find(
            (e) => e.step_id === step.step_id
          );
          const isIncorrect = isFirstError || evalItem?.status === "incorrect";
          const isCorrect = !isFirstError && !isDownstream && evalItem?.status === "correct";

          return (
            <div key={step.step_id} className="relative group">
              {/* Timeline marker icon */}
              <div
                className={cn(
                  "absolute -left-6 top-1 w-7 h-7 rounded-full flex items-center justify-center -translate-x-1/2 bg-white ring-4 ring-white shadow-xs",
                  isFirstError
                    ? "bg-rose-500 text-white ring-rose-100 animate-bounce"
                    : isDownstream
                    ? "bg-purple-100 text-purple-700 ring-purple-50"
                    : isIncorrect
                    ? "bg-rose-100 text-rose-700 ring-rose-50"
                    : "bg-emerald-100 text-emerald-700 ring-emerald-50"
                )}
              >
                {isFirstError ? (
                  <XCircle className="w-4 h-4 text-white" />
                ) : isDownstream ? (
                  <ArrowDown className="w-3.5 h-3.5 text-purple-700" />
                ) : isIncorrect ? (
                  <XCircle className="w-4 h-4 text-rose-700" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                )}
              </div>

              {/* Step Card Content */}
              <div
                className={cn(
                  "p-4 rounded-xl border transition-all text-xs space-y-2",
                  isFirstError
                    ? "bg-rose-50/70 border-rose-300 ring-2 ring-rose-200/50"
                    : isDownstream
                    ? "bg-purple-50/40 border-purple-200"
                    : "bg-slate-50/70 border-slate-200"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-800 font-mono">
                      Step {step.order}
                    </span>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                      {step.reasoning_type.replace(/_/g, " ")}
                    </span>
                  </div>

                  {isFirstError && (
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-rose-600 text-white shadow-xs">
                      First Error Detected
                    </span>
                  )}
                  {isDownstream && !isFirstError && (
                    <span className="text-[10px] uppercase font-medium px-2 py-0.5 rounded-md bg-purple-100 text-purple-800">
                      Downstream Impact
                    </span>
                  )}
                  {isCorrect && (
                    <span className="text-[10px] uppercase font-semibold text-emerald-700">
                      Valid Step
                    </span>
                  )}
                </div>

                {/* Claim Statement */}
                <div>
                  <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider block">
                    Claim
                  </span>
                  <p className="font-semibold text-slate-900 text-sm">
                    {step.claim}
                  </p>
                </div>

                {/* Evidence Quote */}
                <div className="p-2.5 rounded-lg bg-white/80 border border-slate-200/60 font-serif italic text-slate-700 text-[11px]">
                  &ldquo;{step.original_text || step.evidence_text}&rdquo;
                </div>

                {/* Concepts & Formulas */}
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {step.concept_ids?.map((cid) => (
                    <span
                      key={cid}
                      className="px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-mono text-[10px]"
                    >
                      {cid}
                    </span>
                  ))}
                  {step.formulas?.map((f, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono text-[10px]"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
