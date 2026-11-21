"use client";

import React from "react";
import { Users, TrendingUp, AlertTriangle, ShieldAlert } from "lucide-react";
import { TeacherAnalyticsResponse } from "@/types/analytics.types";
import { formatPercent } from "@/lib/utils";

interface TeacherOverviewCardsProps {
  data: TeacherAnalyticsResponse;
}

export function TeacherOverviewCards({ data }: TeacherOverviewCardsProps) {
  const strugglingConceptsCount = data.concept_heatmaps.filter(
    (c) => c.struggling_students_count > 0 || c.average_mastery < 0.5
  ).length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Students */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Cohort Enrollment
          </span>
          <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
            <Users className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {data.total_students}
          </span>
          <span className="text-xs text-slate-500">active learners</span>
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Tracked across Bayesian Knowledge Tracing profiles
        </p>
      </div>

      {/* 2. Class Average Proficiency */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Class Average Mastery
          </span>
          <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {formatPercent(data.class_average_proficiency)}
          </span>
          <span className="text-xs text-slate-500">BKT posterior</span>
        </div>
        <div className="mt-3 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, data.class_average_proficiency * 100))}%` }}
          />
        </div>
      </div>

      {/* 3. Concepts Requiring Attention */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Concepts in Deficit
          </span>
          <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {strugglingConceptsCount}
          </span>
          <span className="text-xs text-slate-500">of 23 concepts</span>
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Concepts with student struggle rate &gt; 0 or average &lt; 50%
        </p>
      </div>

      {/* 4. Students Requiring Intervention */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            At-Risk Alerts
          </span>
          <div className="w-9 h-9 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono">
            {data.students_at_risk.length}
          </span>
          <span className="text-xs text-slate-500">students flagged</span>
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Targeted instructional intervention recommended
        </p>
      </div>
    </div>
  );
}
