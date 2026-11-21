export type QuestionDifficulty = "easy" | "medium" | "hard" | "expert";

export interface AdaptiveQuestion {
  id: string;
  concept_id: string;
  secondary_concept_ids?: string[];
  title: string;
  prompt: string;
  difficulty: QuestionDifficulty;
  question_type: "multiple_choice" | "numerical" | "open_reasoning";
  options?: string[];
  correct_answer: string;
  rubric?: string;
  hints?: string[];
  prerequisites?: string[];
  target_misconceptions?: string[];
}

export interface AdaptiveNextQuestionRequest {
  student_id: string;
  target_concept_id?: string;
  exclude_question_ids?: string[];
  allow_prerequisite_diversion?: boolean;
}

export interface AdaptiveNextQuestionResponse {
  student_id: string;
  target_concept_id: string;
  question: AdaptiveQuestion | null;
  is_prerequisite_diversion: boolean;
  diversion_reason: string | null;
  difficulty_tier: QuestionDifficulty;
  streak: number;
  recent_error_rate: number;
}

export interface AssessmentAnswerRequest {
  student_id: string;
  question_id: string;
  student_answer: string;
  time_spent_seconds?: number;
}

export interface AssessmentEvaluation {
  student_id: string;
  question_id: string;
  concept_id: string;
  is_correct: boolean;
  prior_mastery: number;
  updated_mastery: number;
  prior_difficulty: QuestionDifficulty;
  updated_difficulty: QuestionDifficulty;
  feedback_message: string;
  next_recommended_concept?: string | null;
}

export interface SpacedRepetitionCard {
  concept_id: string;
  student_id: string;
  interval_days: number;
  repetition_count: number;
  urgency_score: number;
  next_review_due: string;
  easiness_factor: number;
  last_reviewed_at?: string;
}

export interface SpacedReviewRequest {
  student_id: string;
  concept_id: string;
  quality_score: number;
}

export interface InterventionStage {
  stage_order: number;
  stage_name: string;
  target_misconception_id?: string | null;
  intervention_strategy: "refutation_text" | "contrasting_cases" | "guided_derivation" | "concept_bridging" | "micro_practice";
  content_markdown: string;
  check_question?: string | null;
  expected_insight?: string | null;
}

export interface InterventionPlan {
  plan_id: string;
  student_id: string;
  session_id: string;
  target_concept_id: string;
  diagnosed_misconception_ids: string[];
  stages: InterventionStage[];
  actionable_summary: string;
  prerequisite_refreshers: string[];
}
