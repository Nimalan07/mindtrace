"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AlertCircle, RefreshCw } from "lucide-react";
import { useStudent } from "@/context/StudentContext";
import { adaptiveService } from "@/services/adaptive.service";
import {
  AdaptiveNextQuestionResponse,
  AssessmentEvaluation,
  InterventionPlan,
} from "@/types/adaptive.types";
import { AdaptiveProgressHeader } from "@/components/learning/AdaptiveProgressHeader";
import { AdaptiveQuestionCard } from "@/components/learning/AdaptiveQuestionCard";
import { LearningFeedbackCard } from "@/components/learning/LearningFeedbackCard";
import { KnowledgeRepairCard } from "@/components/learning/KnowledgeRepairCard";

function LearningContent() {
  const { currentStudentId } = useStudent();
  const searchParams = useSearchParams();
  const initialTopic = searchParams.get("topic") || "net_force";

  const [questionData, setQuestionData] = useState<AdaptiveNextQuestionResponse | null>(null);
  const [loadingQuestion, setLoadingQuestion] = useState<boolean>(true);
  const [evaluation, setEvaluation] = useState<AssessmentEvaluation | null>(null);
  const [submittingAnswer, setSubmittingAnswer] = useState<boolean>(false);
  const [intervention, setIntervention] = useState<InterventionPlan | null>(null);
  const [showIntervention, setShowIntervention] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [excludedIds, setExcludedIds] = useState<string[]>([]);
  const [reloadTrigger, setReloadTrigger] = useState<number>(0);

  useEffect(() => {
    let ignore = false;
    adaptiveService
      .getNextQuestion({
        student_id: currentStudentId,
        target_concept_id: initialTopic,
        exclude_question_ids: excludedIds,
        allow_prerequisite_diversion: true,
      })
      .then((resp) => {
        if (!ignore) {
          setQuestionData(resp);
          setLoadingQuestion(false);
          setEvaluation(null);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load adaptive question.");
          setLoadingQuestion(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [currentStudentId, initialTopic, reloadTrigger, excludedIds]);

  // Submit Answer
  const handleSubmitAnswer = async (answer: string, timeSpentSeconds: number) => {
    if (!questionData?.question) return;
    setSubmittingAnswer(true);
    setError(null);

    try {
      const evalResp = await adaptiveService.submitAssessmentAnswer({
        student_id: currentStudentId,
        question_id: questionData.question.id,
        student_answer: answer,
        time_spent_seconds: timeSpentSeconds,
      });

      setEvaluation(evalResp);
      setExcludedIds((prev) => [...prev, questionData.question!.id]);

      // If incorrect, load targeted knowledge repair intervention
      if (!evalResp.is_correct) {
        try {
          const plan = await adaptiveService.getInterventionForConcept(
            currentStudentId,
            evalResp.concept_id
          );
          setIntervention(plan);
        } catch (planErr) {
          console.error("Intervention plan fetch error:", planErr);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Answer submission evaluation failed.");
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleNextQuestion = () => {
    setShowIntervention(false);
    setLoadingQuestion(true);
    setReloadTrigger((prev) => prev + 1);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-rose-800">Adaptive Engine Notice</h4>
              <p className="text-xs text-rose-700">{error}</p>
            </div>
          </div>
          <button
            onClick={() => {
              setLoadingQuestion(true);
              setReloadTrigger((prev) => prev + 1);
            }}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Progress Header */}
      {questionData && (
        <AdaptiveProgressHeader
          conceptId={questionData.target_concept_id}
          difficulty={questionData.difficulty_tier}
          streak={questionData.streak}
          recentErrorRate={questionData.recent_error_rate}
          isDiversion={questionData.is_prerequisite_diversion}
          diversionReason={questionData.diversion_reason}
        />
      )}

      {/* Loading Skeleton */}
      {loadingQuestion && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 space-y-4 animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-1/3" />
          <div className="h-24 bg-slate-200 rounded-xl w-full" />
          <div className="h-12 bg-slate-200 rounded-xl w-full" />
        </div>
      )}

      {/* Question Card */}
      {!loadingQuestion && questionData?.question && !evaluation && (
        <AdaptiveQuestionCard
          key={questionData.question.id}
          question={questionData.question}
          onSubmitAnswer={handleSubmitAnswer}
          submitting={submittingAnswer}
        />
      )}

      {/* Evaluation Feedback */}
      {evaluation && (
        <LearningFeedbackCard
          evaluation={evaluation}
          onNextQuestion={handleNextQuestion}
          onOpenIntervention={() => setShowIntervention(true)}
        />
      )}

      {/* Knowledge Repair Plan Card */}
      {showIntervention && intervention && (
        <KnowledgeRepairCard
          plan={intervention}
          onClose={() => setShowIntervention(false)}
        />
      )}
    </div>
  );
}

export default function AdaptiveLearningPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-400">Loading Adaptive Engine...</div>}>
      <LearningContent />
    </Suspense>
  );
}
