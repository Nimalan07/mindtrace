"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { GraduationCap, ArrowLeft, GitMerge, BookCheck, ShieldAlert, Sparkles } from "lucide-react";

function LearningPlaceholderContent() {
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic");

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
          <GraduationCap className="w-8 h-8" />
        </div>

        <div className="space-y-2 max-w-xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>Phase D: Adaptive Practice & Personalized Interventions</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Adaptive Learning Module
          </h2>

          {topic && (
            <div className="p-3 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 text-xs font-medium">
              Targeted concept queue initiated for:{" "}
              <span className="font-bold font-mono">{topic}</span>
            </div>
          )}

          <p className="text-sm text-slate-600 leading-relaxed">
            This module dynamically serves items calibrated to your exact BKT zone of proximal development, auto-diverting to foundational prerequisites if misconceptions are detected.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto pt-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <GitMerge className="w-4 h-4 text-teal-600" />
              <span>Prerequisite Diversion</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Automatically routes to unmastered foundational dependencies before advanced items.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <BookCheck className="w-4 h-4 text-teal-600" />
              <span>Adaptive Difficulty</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Difficulty progression dynamically adapts across 4 tiers based on streak and error rate.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
              <ShieldAlert className="w-4 h-4 text-teal-600" />
              <span>Targeted Interventions</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Refutation texts, contrasting examples, and micro-practice for verified misconceptions.
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

export default function LearningPlaceholderPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-400">Loading learning session...</div>}>
      <LearningPlaceholderContent />
    </Suspense>
  );
}
