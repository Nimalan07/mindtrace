"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight, BookOpen, Compass, Award } from "lucide-react";
import { StudentAnalyticsResponse } from "@/types/analytics.types";

interface DashboardHeaderProps {
  data: StudentAnalyticsResponse;
}

export function DashboardHeader({ data }: DashboardHeaderProps) {
  const topNextTopic = data.recommended_next_topics.length > 0
    ? data.recommended_next_topics[0]
    : null;

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#14213D] via-[#1E293B] to-[#0F172A] p-6 sm:p-8 text-white shadow-lg border border-slate-800">
      {/* Background Accent glow */}
      <div className="absolute -top-12 -right-12 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        {/* Left: Student Identity & Greeting */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Bayesian Knowledge Tracing (BKT) Active</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Welcome back, <span className="text-teal-400 font-mono">{data.student_id}</span>
          </h2>

          <p className="text-sm text-slate-300 max-w-xl leading-relaxed">
            MINDTRACE has analyzed your conceptual reasoning and prerequisite paths across 23 Physics concepts. Here is your real-time diagnostic progress.
          </p>
        </div>

        {/* Right: Dynamic Continue Learning Action */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
          {topNextTopic ? (
            <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-slate-800/80 border border-teal-500/30 backdrop-blur-xs">
              <span className="text-[11px] uppercase tracking-wider text-teal-300 font-semibold flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-teal-400" />
                Recommended Next Step
              </span>
              <span className="text-sm font-bold text-white truncate max-w-xs">
                {topNextTopic}
              </span>
              <Link
                href={`/student/learning?topic=${encodeURIComponent(topNextTopic)}`}
                className="mt-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs transition-all shadow-md shadow-teal-500/20 group"
              >
                <span>Continue Learning</span>
                <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-slate-800/80 border border-slate-700 backdrop-blur-xs">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-teal-400" />
                Diagnostic Status
              </span>
              <span className="text-sm font-semibold text-slate-200">
                Explore Diagnostic Assessment
              </span>
              <Link
                href="/student/assessment"
                className="mt-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-medium text-xs transition-all"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Take Diagnostic Probe</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
