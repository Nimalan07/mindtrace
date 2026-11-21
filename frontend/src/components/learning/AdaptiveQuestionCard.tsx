"use client";

import React, { useState, useEffect } from "react";
import { Send, Lightbulb, Clock } from "lucide-react";
import { AdaptiveQuestion } from "@/types/adaptive.types";
import { cn } from "@/lib/utils";

interface AdaptiveQuestionCardProps {
  question: AdaptiveQuestion;
  onSubmitAnswer: (answer: string, timeSpentSeconds: number) => void;
  submitting?: boolean;
}

export function AdaptiveQuestionCard({
  question,
  onSubmitAnswer,
  submitting,
}: AdaptiveQuestionCardProps) {
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [textAnswer, setTextAnswer] = useState<string>("");
  const [seconds, setSeconds] = useState<number>(0);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [question.id]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalAnswer = question.options?.length
      ? selectedOption
      : textAnswer.trim();

    if (!finalAnswer) {
      setError("Please select or enter an answer before submitting.");
      return;
    }
    setError(null);
    onSubmitAnswer(finalAnswer, seconds);
  };

  const isMultipleChoice = Boolean(question.options && question.options.length > 0);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
      {/* Title & Timing Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal-700 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-full">
            {question.id}
          </span>
          <h3 className="text-xl font-bold text-slate-900 tracking-tight mt-1">
            {question.title}
          </h3>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 font-mono text-xs">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{seconds}s</span>
        </div>
      </div>

      {/* Problem Prompt */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 text-sm sm:text-base leading-relaxed font-serif">
        {question.prompt}
      </div>

      {/* Optional Hints */}
      {question.hints && question.hints.length > 0 && (
        <div>
          {!showHint ? (
            <button
              type="button"
              onClick={() => setShowHint(true)}
              className="text-xs text-teal-600 hover:text-teal-700 font-semibold flex items-center gap-1"
            >
              <Lightbulb className="w-3.5 h-3.5" />
              <span>Need a pedagogical hint?</span>
            </button>
          ) : (
            <div className="p-3.5 rounded-xl bg-teal-50/70 border border-teal-200 text-xs text-teal-900 space-y-1 animate-in fade-in duration-150">
              <span className="font-bold flex items-center gap-1 text-[11px] uppercase tracking-wider">
                <Lightbulb className="w-3.5 h-3.5 text-teal-600" />
                Adaptive Hint
              </span>
              <p>{question.hints[0]}</p>
            </div>
          )}
        </div>
      )}

      {/* Answer Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}

        {isMultipleChoice ? (
          <div className="space-y-2.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Select the Correct Option
            </label>
            <div className="grid grid-cols-1 gap-2.5">
              {question.options?.map((opt, idx) => {
                // Option prefix: e.g. "A" if opt is "A) Yes..." or just opt
                const optKey = opt.trim().charAt(0);
                const isSelected = selectedOption === optKey || selectedOption === opt;

                return (
                  <div
                    key={idx}
                    onClick={() => {
                      setSelectedOption(optKey);
                      if (error) setError(null);
                    }}
                    className={cn(
                      "p-3.5 rounded-xl border text-xs sm:text-sm font-medium cursor-pointer transition-all flex items-start gap-3",
                      isSelected
                        ? "bg-teal-50/80 border-teal-500 ring-2 ring-teal-500/20 text-teal-950 font-semibold shadow-xs"
                        : "bg-white border-slate-200 hover:bg-slate-50 text-slate-800"
                    )}
                  >
                    <div
                      className={cn(
                        "w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5",
                        isSelected
                          ? "border-teal-600 bg-teal-600 text-white"
                          : "border-slate-300 bg-white"
                      )}
                    >
                      {isSelected && <span className="w-2 h-2 rounded-full bg-white" />}
                    </div>
                    <span>{opt}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Enter Your Numerical or Descriptive Answer
            </label>
            <input
              type="text"
              value={textAnswer}
              onChange={(e) => {
                setTextAnswer(e.target.value);
                if (error) setError(null);
              }}
              placeholder="Type your answer here..."
              className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500"
              disabled={submitting}
            />
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs shadow-md shadow-teal-600/20 transition-all disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            <span>{submitting ? "Evaluating..." : "Submit Answer"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
