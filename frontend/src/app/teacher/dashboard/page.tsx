"use client";

import React from "react";
import Link from "next/link";
import { Users, ArrowLeft, BarChart3, AlertTriangle, Lightbulb, Sparkles } from "lucide-react";

export default function TeacherPlaceholderPage() {
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
          <Users className="w-8 h-8" />
        </div>

        <div className="space-y-2 max-w-xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>Phase E: Class-Level Diagnostic Analytics & Heatmaps</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Educator Diagnostic Dashboard
          </h2>

          <p className="text-sm text-slate-600 leading-relaxed">
            The Educator Dashboard synthesizes classroom-wide BKT mastery distributions, concept difficulty heatmaps, persistent misconception clusters, and at-risk student early warning flags.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto pt-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <BarChart3 className="w-4 h-4 text-teal-600" />
              <span>Concept Heatmaps</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Visualizes average mastery and struggling vs mastered ratios across all 23 concepts.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-teal-600">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Misconception Frequency</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Ranks verified misconceptions by prevalence to guide lecture focus and intervention.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <Lightbulb className="w-4 h-4 text-teal-600" />
              <span>Actionable Teaching Insights</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Automated pedagogical guidance generated from real classroom learning curves.
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
