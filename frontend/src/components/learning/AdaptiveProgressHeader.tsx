"use client";

import React from "react";
import { Zap, Flame, Target, ShieldAlert } from "lucide-react";
import { QuestionDifficulty } from "@/types/adaptive.types";
import { cn } from "@/lib/utils";

interface AdaptiveProgressHeaderProps {
  conceptId: string;
  difficulty: QuestionDifficulty;
  streak: number;
  recentErrorRate: number;
  isDiversion?: boolean;
  diversionReason?: string | null;
}

export function AdaptiveProgressHeader({
  conceptId,
  difficulty,
  streak,
  recentErrorRate,
  isDiversion,
  diversionReason,
}: AdaptiveProgressHeaderProps) {
  const getDifficultyBadge = (diff: QuestionDifficulty) => {
    switch (diff) {
      case "easy":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "medium":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "hard":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "expert":
        return "bg-amber-100 text-amber-800 border-amber-200";
    }
  };

  return (
    <div className="space-y-3">
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Active Learning Concept
              </span>
              <span
                className={cn(
                  "text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border",
                  getDifficultyBadge(difficulty)
                )}
              >
                Tier: {difficulty}
              </span>
            </div>
            <h2 className="text-lg font-extrabold text-slate-900 font-mono">
              {conceptId}
            </h2>
          </div>
        </div>

        {/* Real-time parameters */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 font-semibold">
            <Flame className="w-4 h-4 text-amber-600" />
            <span>Streak: {streak}</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-medium">
            <Zap className="w-4 h-4 text-teal-600" />
            <span>Error Rate: {(recentErrorRate * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Prerequisite Diversion Banner */}
      {isDiversion && (
        <div className="p-4 rounded-xl bg-amber-50 border-2 border-amber-300 text-amber-900 flex items-start gap-3 shadow-xs animate-in fade-in duration-200">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5 text-xs">
            <h4 className="font-bold text-amber-950 uppercase tracking-wide">
              Prerequisite Gap Detected — Adaptive Routing Active
            </h4>
            <p className="text-amber-800 leading-relaxed">
              {diversionReason ||
                "Your mastery of foundational prerequisite concepts fell below threshold. The adaptive engine has diverted to reinforce prerequisite dependencies before resuming advanced tasks."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
