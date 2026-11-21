"use client";

import React from "react";
import {
  TrendingUp,
  CheckCircle2,
  PieChart,
  CalendarClock,
} from "lucide-react";
import { StudentAnalyticsResponse } from "@/types/analytics.types";
import { formatPercent } from "@/lib/utils";

interface MetricCardsGridProps {
  data: StudentAnalyticsResponse;
}

export function MetricCardsGrid({ data }: MetricCardsGridProps) {
  const masteredCount = data.mastery_counts?.mastered ?? 0;
  const practicingCount = data.mastery_counts?.practicing ?? 0;
  const supportCount = data.mastery_counts?.needs_support ?? 0;
  const totalConcepts = masteredCount + practicingCount + supportCount;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Overall Proficiency Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Overall Proficiency
          </span>
          <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {formatPercent(data.overall_proficiency)}
          </span>
          <span className="text-xs text-slate-500">BKT posterior</span>
        </div>

        {/* Progress bar */}
        <div className="mt-3 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
          <div
            className="bg-teal-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, data.overall_proficiency * 100))}%` }}
          />
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Knowledge tracing across all registered prerequisite paths
        </p>
      </div>

      {/* 2. Cumulative Assessment Accuracy */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Assessment Accuracy
          </span>
          <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {formatPercent(data.accuracy_rate)}
          </span>
          <span className="text-xs text-slate-500 font-mono">
            ({data.total_correct}/{data.total_assessments})
          </span>
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-600">
          <span className="font-semibold text-slate-800">{data.total_assessments}</span>
          <span>total questions answered</span>
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Excludes slip & guess variance calibrated via Bayesian updates
        </p>
      </div>

      {/* 3. Mastery Distribution */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Concept Mastery
          </span>
          <div className="w-9 h-9 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
            <PieChart className="w-5 h-5" />
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {masteredCount}
          </span>
          <span className="text-xs text-slate-500">of {totalConcepts || 23} Mastered</span>
        </div>

        {/* Multi-segment bar */}
        <div className="mt-3 w-full bg-slate-100 rounded-full h-2 flex overflow-hidden">
          <div
            className="bg-teal-500 h-2 transition-all duration-300"
            style={{ width: `${(masteredCount / (totalConcepts || 1)) * 100}%` }}
            title={`Mastered: ${masteredCount}`}
          />
          <div
            className="bg-blue-400 h-2 transition-all duration-300"
            style={{ width: `${(practicingCount / (totalConcepts || 1)) * 100}%` }}
            title={`Practicing: ${practicingCount}`}
          />
          <div
            className="bg-amber-400 h-2 transition-all duration-300"
            style={{ width: `${(supportCount / (totalConcepts || 1)) * 100}%` }}
            title={`Needs Support: ${supportCount}`}
          />
        </div>

        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
            {masteredCount} mastered
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            {practicingCount} practicing
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            {supportCount} support
          </span>
        </div>
      </div>

      {/* 4. Spaced Revision Queue */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Spaced Revisions Due
          </span>
          <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <CalendarClock className="w-5 h-5" />
          </div>
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {data.due_revisions_count}
          </span>
          <span className="text-xs text-slate-500">concepts due</span>
        </div>

        <div className="mt-3">
          {data.due_revisions_count > 0 ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 text-[11px] font-semibold">
              Attention needed for long-term retention
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 text-[11px] font-semibold">
              Retention schedule up to date
            </span>
          )}
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Calibrated via SM-2 decay and memory half-life modeling
        </p>
      </div>
    </div>
  );
}
