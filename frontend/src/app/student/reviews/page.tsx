"use client";

import React, { useState, useEffect } from "react";
import {
  CalendarClock,
  CheckCircle2,
  Flame,
  RefreshCw,
  Clock,
} from "lucide-react";
import { useStudent } from "@/context/StudentContext";
import { adaptiveService } from "@/services/adaptive.service";
import { SpacedRepetitionCard } from "@/types/adaptive.types";
import { cn } from "@/lib/utils";

export default function SpacedReviewsPage() {
  const { currentStudentId } = useStudent();
  const [cards, setCards] = useState<SpacedRepetitionCard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeCard, setActiveCard] = useState<SpacedRepetitionCard | null>(null);
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);
  const [completedCards, setCompletedCards] = useState<SpacedRepetitionCard[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [reloadTrigger, setReloadTrigger] = useState<number>(0);

  useEffect(() => {
    let ignore = false;
    adaptiveService
      .getDueSpacedCards(currentStudentId)
      .then((due) => {
        if (!ignore) {
          setCards(due);
          setActiveCard(due.length > 0 ? due[0] : null);
          setLoading(false);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load spaced review queue.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [currentStudentId, reloadTrigger]);

  // Submit Review Score
  const handleRecordReview = async (qualityScore: number) => {
    if (!activeCard) return;
    setSubmittingReview(true);
    setError(null);

    try {
      const updated = await adaptiveService.recordSpacedReview({
        student_id: currentStudentId,
        concept_id: activeCard.concept_id,
        quality_score: qualityScore,
      });

      // Move activeCard to completedCards
      setCompletedCards((prev) => [updated, ...prev]);
      // Remove from due list
      const remaining = cards.filter((c) => c.concept_id !== activeCard.concept_id);
      setCards(remaining);
      setActiveCard(remaining.length > 0 ? remaining[0] : null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to record spaced review.");
    } finally {
      setSubmittingReview(false);
    }
  };

  const QUALITY_SCORES = [
    { score: 0, label: "Blackout", desc: "Complete memory lapse", color: "bg-rose-100 text-rose-800 hover:bg-rose-200" },
    { score: 1, label: "Incorrect", desc: "Wrong, but recognized", color: "bg-orange-100 text-orange-800 hover:bg-orange-200" },
    { score: 2, label: "Vague", desc: "Recalled with serious cues", color: "bg-amber-100 text-amber-800 hover:bg-amber-200" },
    { score: 3, label: "Hesitant", desc: "Correct with effort", color: "bg-blue-100 text-blue-800 hover:bg-blue-200" },
    { score: 4, label: "Good", desc: "Correct after brief pause", color: "bg-teal-100 text-teal-800 hover:bg-teal-200" },
    { score: 5, label: "Mastered", desc: "Instant, effortless recall", color: "bg-emerald-100 text-emerald-800 hover:bg-emerald-200" },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Banner */}
      <div className="bg-gradient-to-r from-[#14213D] via-[#1E293B] to-[#0F172A] rounded-2xl p-6 sm:p-8 text-white shadow-lg space-y-2 border border-slate-800">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-semibold border border-amber-500/30">
          <CalendarClock className="w-3.5 h-3.5" />
          <span>SuperMemo SM-2 Interval Decay Engine</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          Spaced Repetition & Retention Queue
        </h2>
        <p className="text-xs text-slate-300 max-w-xl leading-relaxed">
          Active recall reviews calibrated to your individual forgetting curves to cement physics principles into long-term memory.
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-center justify-between">
          <p className="text-xs font-medium">{error}</p>
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

      {/* Active Review Card Session */}
      {activeCard ? (
        <div className="bg-white rounded-2xl border-2 border-teal-500/40 p-6 sm:p-8 shadow-md space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <span className="text-[10px] uppercase font-bold text-teal-700 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-full">
                Active Recall Card
              </span>
              <h3 className="text-xl font-bold text-slate-900 tracking-tight mt-1 font-mono">
                {activeCard.concept_id}
              </h3>
            </div>

            <div className="flex items-center gap-3 text-xs font-mono text-slate-500">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Interval: {activeCard.interval_days}d
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-amber-700 font-bold">
                <Flame className="w-3.5 h-3.5 text-amber-500" />
                Urgency: {activeCard.urgency_score.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Recall Target
            </span>
            <p className="text-lg font-serif font-bold text-slate-900">
              Can you state the core principle, formula, and vector direction rules for{" "}
              <span className="text-teal-700 font-sans font-bold">{activeCard.concept_id}</span>?
            </p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Pause for a moment to mentally reconstruct the principle before rating your retention quality below.
            </p>
          </div>

          {/* Quality Score Buttons */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block text-center">
              Rate Your Retrieval Effort (0 to 5)
            </span>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
              {QUALITY_SCORES.map((q) => (
                <button
                  key={q.score}
                  type="button"
                  onClick={() => handleRecordReview(q.score)}
                  disabled={submittingReview}
                  className={cn(
                    "p-3 rounded-xl border text-center transition-all flex flex-col items-center justify-between gap-1 shadow-2xs group cursor-pointer disabled:opacity-50",
                    q.color
                  )}
                >
                  <span className="text-lg font-mono font-extrabold">{q.score}</span>
                  <span className="text-xs font-bold">{q.label}</span>
                  <span className="text-[10px] opacity-80 leading-tight">{q.desc}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-3 shadow-xs">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto shadow-xs">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            {cards.length === 0 && !loading
              ? "All Spaced Reviews Up to Date!"
              : "Loading Review Session..."}
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            {cards.length === 0 && !loading
              ? "You have completed all memory retention cards due today. As you practice more topics, the SM-2 engine will schedule future intervals automatically."
              : "Retrieving student spaced repetition cards from the backend database."}
          </p>
        </div>
      )}

      {/* Completed reviews in this session */}
      {completedCards.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Completed Reviews in This Session ({completedCards.length})</span>
            </h4>
          </div>

          <div className="space-y-2">
            {completedCards.map((card, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-slate-800">{card.concept_id}</span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Reps: {card.repetition_count}
                  </span>
                </div>
                <div className="text-right text-[11px] font-mono text-emerald-700 font-semibold">
                  New Interval: {card.interval_days} days
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
