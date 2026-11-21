"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { useStudent } from "@/context/StudentContext";
import { analyticsService } from "@/services/analytics.service";
import { StudentAnalyticsResponse } from "@/types/analytics.types";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { MetricCardsGrid } from "@/components/dashboard/MetricCardsGrid";
import { ConceptMasteryBreakdown } from "@/components/dashboard/ConceptMasteryBreakdown";
import { StrengthsAndWeaknessesCard } from "@/components/dashboard/StrengthsAndWeaknessesCard";
import { SpacedReviewCard } from "@/components/dashboard/SpacedReviewCard";
import { RecentActivityCard } from "@/components/dashboard/RecentActivityCard";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";

export default function StudentDashboardPage() {
  const { currentStudentId } = useStudent();
  const [data, setData] = useState<StudentAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadTrigger, setReloadTrigger] = useState<number>(0);

  useEffect(() => {
    let ignore = false;

    const runFetch = async () => {
      try {
        const response = await analyticsService.getStudentAnalytics(currentStudentId);
        if (!ignore) {
          setData(response);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg =
            err instanceof Error
              ? err.message
              : "Failed to load student analytics from the MINDTRACE backend service.";
          setError(msg);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    runFetch();

    return () => {
      ignore = true;
    };
  }, [currentStudentId, reloadTrigger]);

  const isStale = data !== null && data.student_id !== currentStudentId;
  const showSkeleton = loading || isStale;

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadTrigger((prev) => prev + 1);
  };

  return (
    <div className="space-y-6">
      {/* Error Banner with Retry */}
      {error && !loading && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-rose-800">
                Connection to Diagnostic Engine Failed
              </h4>
              <p className="text-xs text-rose-700 leading-relaxed">{error}</p>
              <p className="text-[11px] text-rose-600">
                Ensure the FastAPI backend is running at{" "}
                <code className="font-mono bg-rose-100/70 px-1 py-0.5 rounded">
                  {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}
                </code>
              </p>
            </div>
          </div>
          <button
            onClick={handleRetry}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {showSkeleton && <DashboardSkeleton />}

      {/* Main Content */}
      {!showSkeleton && !error && data && (
        <>
          {/* Top Banner with dynamic Next Topic & BKT Status */}
          <DashboardHeader data={data} />

          {/* Key Metric Cards */}
          <MetricCardsGrid data={data} />

          {/* Concept Mastery Table across all 23 concepts */}
          <ConceptMasteryBreakdown concepts={data.concept_mastery_breakdown} />

          {/* Two-column insights: Strengths/Weaknesses and Spaced Revision Queue */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <StrengthsAndWeaknessesCard
              strengths={data.strengths}
              weaknesses={data.critical_weaknesses}
              recommendations={data.recommended_next_topics}
            />
            <SpacedReviewCard
              dueRevisions={data.due_revisions}
              totalDueCount={data.due_revisions_count}
            />
          </div>

          {/* Recent Auditable Activity Log */}
          <RecentActivityCard activity={data.recent_activity} />
        </>
      )}
    </div>
  );
}
