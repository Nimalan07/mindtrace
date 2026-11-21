"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, ArrowRight } from "lucide-react";
import { useStudent } from "@/context/StudentContext";
import { diagnosisService } from "@/services/diagnosis.service";
import {
  ConceptDetailView,
  DiagnosticTask,
  DiagnosisSubmitResponse,
  DiagnosisFollowupResponse,
} from "@/types/diagnosis.types";
import {
  DiagnosticProgressStepper,
  AssessmentStep,
} from "@/components/assessment/DiagnosticProgressStepper";
import { ConceptSelector } from "@/components/assessment/ConceptSelector";
import { AssessmentQuestionCard } from "@/components/assessment/AssessmentQuestionCard";
import { ReasoningStepTimeline } from "@/components/assessment/ReasoningStepTimeline";
import { FirstErrorCard } from "@/components/assessment/FirstErrorCard";
import { MisconceptionHypothesisList } from "@/components/assessment/MisconceptionHypothesisList";
import { FollowUpQuestionCard } from "@/components/assessment/FollowUpQuestionCard";
import { DiagnosisSummary } from "@/components/assessment/DiagnosisSummary";

export default function AssessmentPage() {
  const { currentStudentId } = useStudent();

  // Progress state
  const [currentStep, setCurrentStep] = useState<AssessmentStep>("select_concept");
  const [maxStepReached, setMaxStepReached] = useState<number>(1);

  // Data states
  const [concepts, setConcepts] = useState<ConceptDetailView[]>([]);
  const [loadingConcepts, setLoadingConcepts] = useState<boolean>(true);
  const [selectedConcept, setSelectedConcept] = useState<ConceptDetailView | null>(null);
  const [currentTask, setCurrentTask] = useState<DiagnosticTask | null>(null);

  // Diagnosis submission & session state
  const [submittingProblem, setSubmittingProblem] = useState<boolean>(false);
  const [submitResponse, setSubmitResponse] = useState<DiagnosisSubmitResponse | null>(null);
  const [followupResponse, setFollowupResponse] = useState<DiagnosisFollowupResponse | null>(null);
  const [submittingFollowup, setSubmittingFollowup] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch registered concepts on mount
  useEffect(() => {
    let ignore = false;
    diagnosisService
      .getConcepts()
      .then((data) => {
        if (!ignore) {
          setConcepts(data.concepts);
          setLoadingConcepts(false);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load concepts.");
          setLoadingConcepts(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  // Step A: Concept Selection
  const handleSelectConcept = async (concept: ConceptDetailView) => {
    setSelectedConcept(concept);
    setError(null);
    try {
      const task = await diagnosisService.getDiagnosticQuestionForConcept(concept.id);
      setCurrentTask(task);
      setCurrentStep("solve_problem");
      setMaxStepReached((prev) => Math.max(prev, 2));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load task for selected concept.");
    }
  };

  // Step B: Submit initial problem & reasoning
  const handleSubmitProblem = async (combinedResponse: string) => {
    if (!currentTask) return;
    setSubmittingProblem(true);
    setError(null);

    try {
      const response = await diagnosisService.submitDiagnosis({
        student_id: currentStudentId,
        question_id: currentTask.question_id,
        question_text: currentTask.question_text,
        student_response: combinedResponse,
        rubric: currentTask.rubric,
        relevant_concept_ids: currentTask.relevant_concept_ids,
      });

      setSubmitResponse(response);
      setCurrentStep("reasoning_analysis");
      setMaxStepReached((prev) => Math.max(prev, 3));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Reasoning analysis submission failed.");
    } finally {
      setSubmittingProblem(false);
    }
  };

  // Advance from Step C (Reasoning Analysis) to Step D (Probe) or Step E (Diagnosis)
  const handleProceedFromAnalysis = () => {
    if (submitResponse?.selected_followup_question) {
      setCurrentStep("verify_probe");
      setMaxStepReached((prev) => Math.max(prev, 4));
    } else {
      setCurrentStep("final_diagnosis");
      setMaxStepReached((prev) => Math.max(prev, 5));
    }
  };

  // Step D: Submit follow-up probe answer
  const handleSubmitFollowup = async (studentResponse: string) => {
    if (!submitResponse?.selected_followup_question) return;
    setSubmittingFollowup(true);
    setError(null);

    try {
      const response = await diagnosisService.submitFollowup({
        diagnosis_session_id: submitResponse.diagnosis_session_id,
        followup_question_id: submitResponse.selected_followup_question.question_id,
        student_response: studentResponse,
      });

      setFollowupResponse(response);
      setCurrentStep("final_diagnosis");
      setMaxStepReached((prev) => Math.max(prev, 5));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Follow-up probe verification failed.");
    } finally {
      setSubmittingFollowup(false);
    }
  };

  // Reset assessment
  const handleReset = () => {
    setCurrentStep("select_concept");
    setMaxStepReached(1);
    setSelectedConcept(null);
    setCurrentTask(null);
    setSubmitResponse(null);
    setFollowupResponse(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Interactive Progress Stepper */}
      <DiagnosticProgressStepper
        currentStep={currentStep}
        onStepClick={(step) => setCurrentStep(step)}
        maxStepReached={maxStepReached}
      />

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-rose-800">Diagnostic Engine Alert</h4>
              <p className="text-xs text-rose-700">{error}</p>
            </div>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-xs font-semibold text-rose-700 hover:text-rose-900"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* STEP A: Concept Selection */}
      {currentStep === "select_concept" && (
        <ConceptSelector
          concepts={concepts}
          selectedConceptId={selectedConcept?.id || null}
          onSelectConcept={handleSelectConcept}
          loading={loadingConcepts}
        />
      )}

      {/* STEP B: Problem & Reasoning Submission */}
      {currentStep === "solve_problem" && currentTask && (
        <AssessmentQuestionCard
          task={currentTask}
          onSubmit={handleSubmitProblem}
          onBack={() => setCurrentStep("select_concept")}
          submitting={submittingProblem}
        />
      )}

      {/* STEP C: Reasoning Analysis & First Error Localization */}
      {currentStep === "reasoning_analysis" && submitResponse && (
        <div className="space-y-6 max-w-4xl mx-auto">
          {/* First Error Prominent Card */}
          <FirstErrorCard firstError={submitResponse.first_error_result} />

          {/* Sequential Step Timeline */}
          <ReasoningStepTimeline
            extractedReasoning={submitResponse.extracted_reasoning}
            firstErrorResult={submitResponse.first_error_result}
          />

          {/* Competing Misconceptions */}
          <MisconceptionHypothesisList
            hypotheses={submitResponse.posterior_hypothesis_distribution}
            diagnosticStatus={submitResponse.diagnostic_status}
            calibrationStatus={submitResponse.calibration_status}
            uncertaintyNotes={submitResponse.uncertainty_notes}
          />

          {/* Action button to advance to probe or final diagnosis */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleProceedFromAnalysis}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs shadow-md shadow-teal-600/20 transition-all"
            >
              <span>
                {submitResponse.selected_followup_question
                  ? "Advance to Bayesian Verification Probe"
                  : "View Final Diagnostic Synthesis"}
              </span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP D: Targeted Bayesian Follow-Up Probe */}
      {currentStep === "verify_probe" && submitResponse?.selected_followup_question && (
        <div className="space-y-6 max-w-4xl mx-auto">
          <FollowUpQuestionCard
            question={submitResponse.selected_followup_question}
            onSubmitFollowup={handleSubmitFollowup}
            submitting={submittingFollowup}
          />

          {/* Current Hypotheses State */}
          <MisconceptionHypothesisList
            hypotheses={
              followupResponse?.updated_hypothesis_distribution ||
              submitResponse.posterior_hypothesis_distribution
            }
            diagnosticStatus={
              followupResponse?.diagnostic_status || submitResponse.diagnostic_status
            }
            calibrationStatus={submitResponse.calibration_status}
          />
        </div>
      )}

      {/* STEP E: Final Diagnosis Synthesis */}
      {currentStep === "final_diagnosis" && submitResponse && (
        <DiagnosisSummary
          submitResponse={submitResponse}
          updatedHypotheses={followupResponse?.updated_hypothesis_distribution}
          onReset={handleReset}
        />
      )}
    </div>
  );
}
