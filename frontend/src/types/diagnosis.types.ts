export interface ReasoningStep {
  step_id: string;
  order: number;
  original_text: string;
  claim: string;
  reasoning_type: string;
  concept_ids: string[];
  formulas: string[];
  evidence_text: string;
  uncertainty_flag: boolean;
}

export interface ExtractedReasoning {
  question_id: string;
  original_student_response: string;
  reasoning_steps: ReasoningStep[];
  identified_concepts: string[];
  extraction_status: string;
  ambiguity_notes: string[];
}

export interface ExpectedStep {
  step_id: string;
  expected_concept_ids: string[];
  expected_principle: string;
  acceptable_reasoning: string[];
  acceptable_formulas: string[];
  validation_criteria?: Record<string, unknown>;
}

export interface QuestionRubric {
  question_id: string;
  question_text: string;
  expected_steps: ExpectedStep[];
  accepted_alternative_methods?: string[];
  expected_answer: string;
  relevant_concept_ids: string[];
}

export interface DiagnosticTask {
  question_id: string;
  concept_id: string;
  concept_name: string;
  title: string;
  question_text: string;
  relevant_concept_ids: string[];
  rubric: QuestionRubric;
}

export interface StepEvaluation {
  step_id: string;
  order: number;
  status: "correct" | "incorrect" | "uncertain";
  matched_expected_step_id: string | null;
  error_type: string | null;
  confidence: "high" | "medium" | "low" | "uncertain";
  explanation: string;
  is_first_error: boolean;
  is_downstream_error: boolean;
}

export interface FirstErrorResult {
  has_error: boolean;
  first_error_step_id: string | null;
  first_error_step_order: number | null;
  error_type: string | null;
  error_explanation: string | null;
  step_evaluations: StepEvaluation[];
  affected_downstream_step_ids: string[];
  relevant_concept_ids: string[];
  retrieved_misconception_ids: string[];
  confidence: "high" | "medium" | "low" | "uncertain";
  unsupported_claims: string[];
}

export interface FollowupQuestionView {
  question_id: string;
  question_text: string;
  expected_information_gain: number;
  selection_rationale: string;
  calibration_status: "empirically_calibrated" | "illustrative";
}

export interface DiagnosisSubmitRequest {
  student_id: string;
  question_id: string;
  question_text: string;
  student_response: string;
  rubric: QuestionRubric;
  relevant_concept_ids: string[];
}

export interface DiagnosisSubmitResponse {
  diagnosis_session_id: string;
  student_id: string;
  question_id: string;
  extracted_reasoning: ExtractedReasoning;
  first_error_result: FirstErrorResult;
  candidate_misconception_ids: string[];
  posterior_hypothesis_distribution: Record<string, number>;
  selected_followup_question: FollowupQuestionView | null;
  diagnostic_status: "collecting_evidence" | "sufficient_evidence" | "inconclusive" | "no_available_questions";
  prerequisite_concepts_to_review: string[];
  uncertainty_notes: string[];
  calibration_status: "empirically_calibrated" | "illustrative";
}

export interface DiagnosisFollowupRequest {
  diagnosis_session_id: string;
  followup_question_id: string;
  student_response: string;
}

export interface DiagnosisFollowupResponse {
  diagnosis_session_id: string;
  interpreted_evidence: {
    question_id: string;
    student_response: string;
    category: "supports_hypothesis" | "weakens_hypothesis" | "neutral_or_inconclusive";
    confidence: number;
    interpretation_notes: string;
  };
  updated_hypothesis_distribution: Record<string, number>;
  evidence_history_count: number;
  diagnostic_status: "collecting_evidence" | "sufficient_evidence" | "inconclusive" | "no_available_questions";
  next_followup_question: FollowupQuestionView | null;
  uncertainty_notes: string[];
  calibration_status: "empirically_calibrated" | "illustrative";
}

export interface ConceptDetailView {
  id: string;
  name: string;
  topic: string;
  description: string;
  prerequisites: string[];
  related_concepts: string[];
}

export interface ConceptListResponse {
  subject: string;
  domain: string;
  version: string;
  total_concepts: number;
  total_prerequisite_edges: number;
  concepts: ConceptDetailView[];
}

export interface Member2DiagnosisExport {
  student_id: string;
  session_id: string;
  question_id: string;
  relevant_concept_ids: string[];
  first_error_concept_id: string | null;
  first_error_step_order: number | null;
  identified_error_category: string | null;
  candidate_misconception_ids: string[];
  posterior_hypotheses: Record<string, number>;
  diagnostic_status: string;
  prerequisite_concepts_to_review: string[];
  evidence_confidence: number;
}
