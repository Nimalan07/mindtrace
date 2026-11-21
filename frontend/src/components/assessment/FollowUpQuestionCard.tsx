"use client";

import React, { useState } from "react";
import { Send, BrainCircuit } from "lucide-react";
import { FollowupQuestionView } from "@/types/diagnosis.types";

interface FollowUpQuestionCardProps {
  question: FollowupQuestionView;
  onSubmitFollowup: (studentResponse: string) => void;
  submitting?: boolean;
}

export function FollowUpQuestionCard({
  question,
  onSubmitFollowup,
  submitting,
}: FollowUpQuestionCardProps) {
  const [response, setResponse] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!response.trim()) {
      setError("Please provide your answer and reasoning to this follow-up probe.");
      return;
    }
    setError(null);
    onSubmitFollowup(response.trim());
  };

  return (
    <div className="bg-white rounded-2xl border-2 border-teal-500/40 shadow-md p-6 sm:p-8 space-y-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold">
            <BrainCircuit className="w-3.5 h-3.5 text-teal-600" />
            <span>Targeted Diagnostic Follow-Up Probe</span>
          </div>

          <span className="text-xs font-mono text-slate-400">
            Probe ID: {question.question_id}
          </span>
        </div>

        <h3 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
          Discriminative Verification Question
        </h3>

        <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200 text-slate-900 text-sm sm:text-base font-serif leading-relaxed">
          {question.question_text}
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span className="text-[11px] text-teal-700 italic">
            Rationale: {question.selection_rationale}
          </span>
          <span className="font-mono text-slate-400">
            EIG: {question.expected_information_gain.toFixed(3)} bits
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
            Your Response to This Probe
          </label>
          <textarea
            value={response}
            onChange={(e) => {
              setResponse(e.target.value);
              if (error) setError(null);
            }}
            rows={4}
            placeholder="Answer the question and explain your physics intuition..."
            className="w-full p-3.5 rounded-xl border border-slate-300 text-sm focus:outline-hidden focus:ring-2 focus:ring-teal-500 font-sans leading-relaxed"
            disabled={submitting}
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#14213D] hover:bg-slate-800 text-white font-semibold text-xs shadow-md transition-all disabled:opacity-50"
          >
            <Send className="w-4 h-4 text-teal-400" />
            <span>{submitting ? "Updating Posterior..." : "Submit Probe Answer"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
