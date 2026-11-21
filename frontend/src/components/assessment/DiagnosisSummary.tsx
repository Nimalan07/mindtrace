"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Award,
  ArrowRight,
  AlertTriangle,
  GitFork,
  FileCode,
  Sparkles,
} from "lucide-react";
import {
  DiagnosisSubmitResponse,
  Member2DiagnosisExport,
} from "@/types/diagnosis.types";
import { diagnosisService } from "@/services/diagnosis.service";
import { formatProbability } from "@/lib/utils";

interface DiagnosisSummaryProps {
  submitResponse: DiagnosisSubmitResponse;
  updatedHypotheses?: Record<string, number>;
  onReset: () => void;
}

export function DiagnosisSummary({
  submitResponse,
  updatedHypotheses,
  onReset,
}: DiagnosisSummaryProps) {
  const [exportData, setExportData] = useState<Member2DiagnosisExport | null>(null);
  const [exporting, setExporting] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  const sessionId = submitResponse.diagnosis_session_id;
  const firstError = submitResponse.first_error_result;
  const hypotheses = updatedHypotheses || submitResponse.posterior_hypothesis_distribution;
  const prereqs = submitResponse.prerequisite_concepts_to_review;

  const handleExport = async () => {
    setExporting(true);
    try {
      const data = await diagnosisService.exportDiagnosis(sessionId);
      setExportData(data);
      setShowExportModal(true);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setExporting(false);
    }
  };

  // Sort hypotheses descending by posterior probability
  const sortedHypotheses = Object.entries(hypotheses).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Completion Banner */}
      <div className="bg-gradient-to-r from-[#14213D] via-[#1E293B] to-[#0F172A] rounded-2xl p-6 sm:p-8 text-white shadow-lg space-y-4 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30">
              <Award className="w-3.5 h-3.5" />
              <span>Step E: Verified Diagnostic Summary</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Reasoning Diagnosis Complete
            </h2>
            <p className="text-xs text-slate-300 font-mono">
              Session ID: {sessionId}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              disabled={exporting}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-all"
            >
              <FileCode className="w-4 h-4 text-teal-400" />
              <span>{exporting ? "Exporting..." : "View Member 2 Contract"}</span>
            </button>

            <button
              onClick={onReset}
              className="px-4 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all"
            >
              New Assessment
            </button>
          </div>
        </div>
      </div>

      {/* Primary Diagnostic Findings Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Identified Reasoning Failure */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
            <span>Primary Reasoning Derailment</span>
          </h3>

          <div className="p-4 rounded-xl bg-rose-50/60 border border-rose-200 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-rose-900 font-mono uppercase">
                {firstError.error_type ? firstError.error_type.replace(/_/g, " ") : "Conceptual Divergence"}
              </span>
              <span className="text-[10px] bg-rose-200 text-rose-800 px-2 py-0.5 rounded font-bold">
                Step #{firstError.first_error_step_order || 1}
              </span>
            </div>
            <p className="text-rose-950 font-medium leading-relaxed">
              {firstError.error_explanation || "Reasoning diverged from expected physical principles."}
            </p>
          </div>

          <div className="space-y-1.5 text-xs text-slate-600">
            <span className="font-semibold text-slate-800 uppercase text-[10px] tracking-wider block">
              Observed Student Formulation:
            </span>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 font-serif italic text-slate-800 text-[11px]">
              &ldquo;{submitResponse.extracted_reasoning.original_student_response}&rdquo;
            </div>
          </div>
        </div>

        {/* Right: Competing Hypotheses & Posterior */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-600" />
            <span>Bayesian Posterior Distribution</span>
          </h3>

          <div className="space-y-2.5">
            {sortedHypotheses.slice(0, 4).map(([hyp, prob]) => (
              <div
                key={hyp}
                className="p-2.5 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 text-[10px]">
                    {hyp}
                  </span>
                  <span className="font-medium text-slate-800 truncate max-w-xs">
                    {hyp === "unknown_or_other" ? "Unclassified Deficit" : `Misconception ${hyp}`}
                  </span>
                </div>
                <span className="font-mono font-extrabold text-teal-700">
                  {formatProbability(prob)}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Diagnostic Status:</span>
            <span className="font-bold text-slate-800 capitalize">
              {submitResponse.diagnostic_status.replace(/_/g, " ")}
            </span>
          </div>
        </div>
      </div>

      {/* Recommended Prerequisite Repair Path */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <GitFork className="w-5 h-5 text-teal-600" />
              <span>Recommended Prerequisite Knowledge Repair Path</span>
            </h3>
            <p className="text-xs text-slate-500">
              Graph topology traverse: foundational concepts that must be reinforced before advancing
            </p>
          </div>

          <Link
            href={`/student/learning?topic=${encodeURIComponent(prereqs[0] || submitResponse.question_id)}`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs shadow-md shadow-teal-600/20 transition-all"
          >
            <span>Launch Adaptive Intervention</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {prereqs.length === 0 ? (
          <p className="text-xs text-slate-500 italic">
            Direct prerequisite dependencies satisfied; recommended to proceed directly with adaptive practice.
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-2 pt-2">
            {prereqs.map((prereq, idx) => (
              <React.Fragment key={prereq}>
                <div className="px-3 py-1.5 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 font-semibold text-xs font-mono">
                  {prereq}
                </div>
                {idx < prereqs.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                )}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Member 2 Export JSON Modal */}
      {showExportModal && exportData && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-teal-600" />
                <h4 className="font-bold text-slate-900 text-sm">
                  Member 2 Diagnostic Export Contract (`Member2DiagnosisExport`)
                </h4>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <pre className="p-4 rounded-xl bg-slate-900 text-teal-300 font-mono text-xs overflow-x-auto max-h-96">
              {JSON.stringify(exportData, null, 2)}
            </pre>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
