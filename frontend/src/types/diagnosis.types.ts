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

export interface DiagnosticFollowupQuestion {
  question_id: string;
  question_text: string;
  target_misconception_ids: string[];
  options: Array<{
    option_id: string;
    text: string;
    associated_misconception_id?: string;
  }>;
}

export interface DiagnosisSubmitResponse {
  diagnosis_session_id: string;
  extracted_reasoning: ExtractedReasoning;
  first_error_result: {
    first_error_step_id: string | null;
    first_error_step_order: number | null;
    identified_error_category: string;
    relevant_concept_ids: string[];
    explanation: string;
  };
  candidate_misconception_ids: string[];
  selected_followup_question: DiagnosticFollowupQuestion | null;
  posterior_hypotheses: Record<string, number>;
  diagnostic_status: string;
}

export interface Member2DiagnosisExport {
  student_id: string;
  session_id: string;
  question_id: string;
  relevant_concept_ids: string[];
  first_error_concept_id: string | null;
  first_error_step_order: number | null;
  identified_error_category: string;
  candidate_misconception_ids: string[];
  posterior_hypotheses: Record<string, number>;
  diagnostic_status: string;
  prerequisite_concepts_to_review: string[];
  evidence_confidence: number;
}
