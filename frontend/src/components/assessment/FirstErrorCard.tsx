"use client";

import React from "react";
import { AlertOctagon, CornerDownRight, CheckCircle, ShieldAlert } from "lucide-react";
import { FirstErrorResult } from "@/types/diagnosis.types";

interface FirstErrorCardProps {
  firstError: FirstErrorResult;
}

export function FirstErrorCard({ firstError }: FirstErrorCardProps) {
  if (!firstError.has_error || !firstError.first_error_step_id) {
    return (
      <div className="bg-emerald-50 rounded-2xl border border-emerald-200 p-6 flex items-start gap-4">
        <CheckCircle className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-emerald-950">
            No Conceptual or Reasoning Errors Localized
          </h3>
          <p className="text-xs text-emerald-800 leading-relaxed">
            All extracted reasoning steps adhere strictly to the expert rubric expectations. Prerequisite and target concept reasoning appear structurally sound.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-rose-50 via-white to-amber-50/30 rounded-2xl border-2 border-rose-300 p-6 shadow-md space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center shadow-md shadow-rose-600/30 shrink-0">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-rose-700">
                First Error Localized
              </span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold">
                Step #{firstError.first_error_step_order}
              </span>
            </div>
            <h3 className="text-lg font-extrabold text-slate-900 tracking-tight">
              {firstError.error_type
                ? firstError.error_type.replace(/_/g, " ").toUpperCase()
                : "REASONING FAILURE"}
            </h3>
          </div>
        </div>

        <div className="text-right shrink-0">
          <span className="text-[11px] text-slate-500 block">Detector Confidence</span>
          <span className="text-xs font-bold text-slate-800 uppercase font-mono">
            {firstError.confidence || "High"}
          </span>
        </div>
      </div>

      {/* Explanation banner */}
      <div className="p-4 rounded-xl bg-white border border-rose-200/80 shadow-xs text-xs sm:text-sm text-slate-800 leading-relaxed">
        <p className="font-medium">
          {firstError.error_explanation ||
            "The student reasoning diverged from standard physical principles at this step, creating downstream conceptual conflicts."}
        </p>
      </div>

      {/* Downstream Chain */}
      {firstError.affected_downstream_step_ids?.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-slate-600 pt-1">
          <CornerDownRight className="w-4 h-4 text-purple-600 shrink-0" />
          <span>
            <strong className="text-purple-900 font-semibold">Downstream Cascade:</strong>{" "}
            Subsequent steps{" "}
            <span className="font-mono text-purple-800 font-bold">
              [{firstError.affected_downstream_step_ids.join(", ")}]
            </span>{" "}
            were compromised by this initial error.
          </span>
        </div>
      )}

      {/* Candidate misconceptions retrieved */}
      {firstError.retrieved_misconception_ids?.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-slate-600 pt-1">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong className="text-amber-900 font-semibold">Candidate Hypotheses:</strong>{" "}
            {firstError.retrieved_misconception_ids.map((id) => (
              <span
                key={id}
                className="ml-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-mono text-[10px] font-bold"
              >
                {id}
              </span>
            ))}
          </span>
        </div>
      )}
    </div>
  );
}
