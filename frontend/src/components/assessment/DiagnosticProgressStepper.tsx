"use client";

import React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export type AssessmentStep = "select_concept" | "solve_problem" | "reasoning_analysis" | "verify_probe" | "final_diagnosis";

interface DiagnosticProgressStepperProps {
  currentStep: AssessmentStep;
  onStepClick?: (step: AssessmentStep) => void;
  maxStepReached: number;
}

const STEPS: Array<{ id: AssessmentStep; label: string; stage: string; order: number }> = [
  { id: "select_concept", label: "Concept", stage: "Step A", order: 1 },
  { id: "solve_problem", label: "Problem", stage: "Step B", order: 2 },
  { id: "reasoning_analysis", label: "Error Analysis", stage: "Step C", order: 3 },
  { id: "verify_probe", label: "Bayesian Probing", stage: "Step D", order: 4 },
  { id: "final_diagnosis", label: "Diagnosis", stage: "Step E", order: 5 },
];

export function DiagnosticProgressStepper({
  currentStep,
  onStepClick,
  maxStepReached,
}: DiagnosticProgressStepperProps) {
  const currentOrder = STEPS.find((s) => s.id === currentStep)?.order || 1;

  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-5 shadow-xs">
      <div className="flex items-center justify-between max-w-4xl mx-auto relative">
        {/* Connector Line behind steps */}
        <div className="absolute top-4 left-6 right-6 h-0.5 bg-slate-200 -z-0" />
        <div
          className="absolute top-4 left-6 h-0.5 bg-teal-500 transition-all duration-500 -z-0"
          style={{
            width: `${((Math.min(currentOrder, maxStepReached) - 1) / (STEPS.length - 1)) * 100}%`,
          }}
        />

        {STEPS.map((s) => {
          const isCompleted = s.order < currentOrder;
          const isCurrent = s.id === currentStep;
          const isClickable = s.order <= maxStepReached && onStepClick;

          return (
            <button
              key={s.id}
              onClick={() => isClickable && onStepClick(s.id)}
              disabled={!isClickable}
              className={cn(
                "relative z-10 flex flex-col items-center gap-1.5 focus:outline-hidden group",
                isClickable ? "cursor-pointer" : "cursor-default opacity-70"
              )}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center font-mono text-xs font-bold transition-all duration-200",
                  isCompleted
                    ? "bg-teal-600 text-white shadow-sm"
                    : isCurrent
                    ? "bg-[#14213D] text-teal-400 ring-4 ring-teal-100 border border-teal-500 shadow-md"
                    : "bg-white border-2 border-slate-300 text-slate-400"
                )}
              >
                {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : s.order}
              </div>
              <div className="text-center">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">
                  {s.stage}
                </span>
                <span
                  className={cn(
                    "text-xs font-semibold block whitespace-nowrap",
                    isCurrent
                      ? "text-slate-900 font-bold"
                      : isCompleted
                      ? "text-teal-700"
                      : "text-slate-400"
                  )}
                >
                  {s.label}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
