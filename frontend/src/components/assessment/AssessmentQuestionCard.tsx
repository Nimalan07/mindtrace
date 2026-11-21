"use client";

import React, { useState } from "react";
import { Send, ArrowLeft, Lightbulb } from "lucide-react";
import { DiagnosticTask } from "@/types/diagnosis.types";

interface AssessmentQuestionCardProps {
  task: DiagnosticTask;
  onSubmit: (finalAnswer: string, reasoningText: string) => void;
  onBack: () => void;
  submitting?: boolean;
}

export function AssessmentQuestionCard({
  task,
  onSubmit,
  onBack,
  submitting,
}: AssessmentQuestionCardProps) {
  const [finalAnswer, setFinalAnswer] = useState("");
  const [reasoningText, setReasoningText] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!finalAnswer.trim()) {
      setValidationError("Please provide your final answer or calculation result.");
      return;
    }
    if (!reasoningText.trim()) {
      setValidationError("Please explain your step-by-step reasoning so the diagnostic engine can analyze it.");
      return;
    }
    setValidationError(null);
    // Combine or submit natural language response
    const combinedResponse = `${finalAnswer.trim()} | Reasoning: ${reasoningText.trim()}`;
    onSubmit(combinedResponse, reasoningText.trim());
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top back button */}
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Concept Selection</span>
      </button>

      {/* Problem Prompt Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200">
              Diagnostic Task • {task.concept_name}
            </span>
            <span className="text-xs font-mono text-slate-400">
              ID: {task.question_id}
            </span>
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            {task.title}
          </h2>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 text-sm sm:text-base leading-relaxed font-serif">
            {task.question_text}
          </div>
        </div>

        {/* Expected concepts tested */}
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">Concepts Evaluated:</span>
          <div className="flex flex-wrap gap-1.5">
            {task.relevant_concept_ids.map((cid) => (
              <span
                key={cid}
                className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-mono text-[11px]"
              >
                {cid}
              </span>
            ))}
          </div>
        </div>

        {/* Form: Answer and Reasoning Separately */}
        <form onSubmit={handleSubmit} className="space-y-5 pt-4 border-t border-slate-100">
          {validationError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
              {validationError}
            </div>
          )}

          {/* 1. Final Answer Input */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
              1. Your Final Answer / Numerical Conclusion
            </label>
            <input
              type="text"
              value={finalAnswer}
              onChange={(e) => {
                setFinalAnswer(e.target.value);
                if (validationError) setValidationError(null);
              }}
              placeholder="e.g. 4 m/s² to the right, or 'The forces are equal and opposite'..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-hidden focus:ring-2 focus:ring-teal-500 font-sans"
              disabled={submitting}
            />
          </div>

          {/* 2. Step-by-Step Reasoning Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                2. Step-by-Step Reasoning & Justification
              </label>
              <span className="text-[11px] text-teal-600 font-medium flex items-center gap-1">
                <Lightbulb className="w-3.5 h-3.5" />
                Explain what principles and formulas you used
              </span>
            </div>
            <textarea
              value={reasoningText}
              onChange={(e) => {
                setReasoningText(e.target.value);
                if (validationError) setValidationError(null);
              }}
              rows={5}
              placeholder="Explain each step of your thinking in order. For example: First I identified the mass... Next I considered the opposing forces... Then I applied..."
              className="w-full p-3.5 rounded-xl border border-slate-300 text-sm focus:outline-hidden focus:ring-2 focus:ring-teal-500 font-sans leading-relaxed"
              disabled={submitting}
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <p className="text-[11px] text-slate-400 max-w-md">
              MINDTRACE will extract each reasoning claim, detect the earliest point of derailment, and select targeted Bayesian probes.
            </p>

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs shadow-md shadow-teal-600/20 transition-all disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{submitting ? "Analyzing Reasoning..." : "Submit for Diagnosis"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
