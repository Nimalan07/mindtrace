"use client";

import React from "react";
import { CheckCircle2, AlertOctagon, Compass, ArrowRight } from "lucide-react";
import Link from "next/link";

interface StrengthsAndWeaknessesCardProps {
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export function StrengthsAndWeaknessesCard({
  strengths,
  weaknesses,
  recommendations,
}: StrengthsAndWeaknessesCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
      <div>
        <h3 className="text-base font-bold text-slate-900 tracking-tight">
          Pedagogical Insights & Trajectory
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Algorithmic gap analysis and prerequisite-ordered study suggestions
        </p>
      </div>

      <div className="space-y-4">
        {/* Top Strengths */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Demonstrated Strengths</span>
          </div>
          {strengths.length === 0 ? (
            <p className="text-xs text-slate-400 italic pl-6">
              Complete more assessments to establish verified strengths (&ge; 70% mastery).
            </p>
          ) : (
            <div className="space-y-1 pl-6">
              {strengths.map((s, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs py-1 px-2.5 rounded-lg bg-emerald-50/60 border border-emerald-100 text-emerald-900 font-medium"
                >
                  <span>{s}</span>
                  <span className="text-[10px] text-emerald-700 font-semibold uppercase">
                    Solid
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Critical Weaknesses */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-800 uppercase tracking-wider">
            <AlertOctagon className="w-4 h-4 text-amber-600" />
            <span>Priority Areas for Remediation</span>
          </div>
          {weaknesses.length === 0 ? (
            <p className="text-xs text-slate-400 italic pl-6">
              No critical conceptual deficits detected under 50% mastery threshold.
            </p>
          ) : (
            <div className="space-y-1 pl-6">
              {weaknesses.map((w, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs py-1 px-2.5 rounded-lg bg-amber-50/60 border border-amber-100 text-amber-900 font-medium"
                >
                  <span>{w}</span>
                  <span className="text-[10px] text-amber-700 font-semibold uppercase">
                    Focus Need
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Prerequisite Next Steps */}
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-800 uppercase tracking-wider">
            <Compass className="w-4 h-4 text-teal-600" />
            <span>Recommended Next Concepts</span>
          </div>
          {recommendations.length === 0 ? (
            <p className="text-xs text-slate-400 italic pl-6">
              All immediate prerequisite concepts satisfy current mastery criteria.
            </p>
          ) : (
            <div className="space-y-1.5 pl-6">
              {recommendations.map((topic, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs py-1.5 px-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-800"
                >
                  <span className="font-semibold text-slate-900">{topic}</span>
                  <Link
                    href={`/student/learning?topic=${encodeURIComponent(topic)}`}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-600 hover:text-teal-700"
                  >
                    <span>Practice</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
