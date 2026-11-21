"use client";

import React from "react";
import Link from "next/link";
import { BrainCircuit, ArrowLeft, CheckCircle2, Sparkles, Layers } from "lucide-react";

export default function AssessmentPlaceholderPage() {
  return (
    <div className="max-w-4xl mx-auto py-8 space-y-6">
      <Link
        href="/student/dashboard"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Student Dashboard</span>
      </Link>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-8 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600 mx-auto shadow-sm">
          <BrainCircuit className="w-8 h-8" />
        </div>

        <div className="space-y-2 max-w-xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>Phase C: Diagnostic Assessment & Bayesian Verification</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Diagnostic Assessment Module
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            This module will deliver open-ended physics reasoning prompts, first-error detection, and dynamic Bayesian diagnostic probes to precisely identify underlying misconceptions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto pt-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <Layers className="w-4 h-4 text-teal-600" />
              <span>Reasoning Extraction</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Parses open-ended student explanations into structured reasoning steps.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <CheckCircle2 className="w-4 h-4 text-teal-600" />
              <span>First-Error Detection</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Identifies the earliest faulty conceptual or mathematical step.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <BrainCircuit className="w-4 h-4 text-teal-600" />
              <span>Bayesian Probing</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Selects questions with maximal expected information gain to verify hypotheses.
            </p>
          </div>
        </div>

        <div className="pt-2">
          <Link
            href="/student/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#14213D] text-white hover:bg-slate-800 text-xs font-semibold transition-colors shadow-sm"
          >
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
