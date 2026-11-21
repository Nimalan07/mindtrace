"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, RefreshCw, Lightbulb, Sparkles } from "lucide-react";
import { analyticsService } from "@/services/analytics.service";
import { TeacherAnalyticsResponse } from "@/types/analytics.types";
import { TeacherOverviewCards } from "@/components/teacher/TeacherOverviewCards";
import { ConceptPerformanceChart } from "@/components/teacher/ConceptPerformanceChart";
import { MisconceptionDistributionChart } from "@/components/teacher/MisconceptionDistributionChart";
import { StudentInterventionTable } from "@/components/teacher/StudentInterventionTable";

export default function TeacherDashboardPage() {
  const [data, setData] = useState<TeacherAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [reloadTrigger, setReloadTrigger] = useState<number>(0);

  useEffect(() => {
    let ignore = false;
    analyticsService
      .getTeacherAnalytics()
      .then((resp) => {
        if (!ignore) {
          setData(resp);
          setLoading(false);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load classroom analytics from the MINDTRACE backend."
          );
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [reloadTrigger]);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#14213D] via-[#1E293B] to-[#0F172A] rounded-2xl p-6 sm:p-8 text-white shadow-lg space-y-2 border border-slate-800">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Cohort Learning Intelligence</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          Educator Diagnostic & Cohort Analytics Dashboard
        </h2>
        <p className="text-xs text-slate-300 max-w-xl leading-relaxed">
          Aggregated classroom knowledge tracing distributions, concept difficulty heatmaps, and evidence-verified misconception clusters.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => {
              setLoading(true);
              setReloadTrigger((prev) => prev + 1);
            }}
            className="text-xs font-semibold text-rose-700 hover:text-rose-900 flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-6 animate-pulse">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-slate-200 rounded-xl" />
            ))}
          </div>
          <div className="h-80 bg-slate-200 rounded-2xl" />
          <div className="h-80 bg-slate-200 rounded-2xl" />
        </div>
      )}

      {/* Main Content */}
      {!loading && data && (
        <>
          {/* 1. Overview KPIs */}
          <TeacherOverviewCards data={data} />

          {/* 2. Concept Performance Heatmap Chart */}
          <ConceptPerformanceChart heatmaps={data.concept_heatmaps} />

          {/* 3. Misconceptions & At-Risk Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <MisconceptionDistributionChart
                misconceptions={data.frequent_misconceptions}
              />
            </div>
            <div className="lg:col-span-2">
              <StudentInterventionTable
                studentsAtRisk={data.students_at_risk}
              />
            </div>
          </div>

          {/* 4. Actionable Teaching Insights */}
          {data.actionable_teaching_insights?.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-3">
              <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-teal-600" />
                <span>Automated Pedagogical Teaching Insights</span>
              </h3>
              <div className="space-y-2">
                {data.actionable_teaching_insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-teal-50/60 border border-teal-200 text-xs text-teal-950 font-medium leading-relaxed flex items-start gap-2"
                  >
                    <span className="font-bold text-teal-700">#{idx + 1}</span>
                    <span>{insight}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
