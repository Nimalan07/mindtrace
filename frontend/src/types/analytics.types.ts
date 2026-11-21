export type MasteryStatus = "mastered" | "practicing" | "needs_support";

export interface ConceptMasteryView {
  concept_id: string;
  concept_name: string;
  topic: string;
  mastery_probability: number;
  status: MasteryStatus;
  opportunities: number;
  correct_count: number;
}

export interface DueRevisionItem {
  concept_id: string;
  concept_name: string;
  interval_days: number;
  repetition_count: number;
  urgency_score: number;
  next_review_due: string;
}

export interface ActivityItem {
  concept_id: string;
  concept_name: string;
  timestamp?: string;
  is_correct?: boolean;
  question_id?: string;
  prior_mastery?: number;
  posterior_mastery?: number;
  [key: string]: unknown;
}

export interface StudentAnalyticsResponse {
  student_id: string;
  overall_proficiency: number;
  total_assessments: number;
  total_correct: number;
  accuracy_rate: number;
  mastery_counts: {
    mastered: number;
    practicing: number;
    needs_support: number;
    [key: string]: number;
  };
  concept_mastery_breakdown: ConceptMasteryView[];
  strengths: string[];
  critical_weaknesses: string[];
  recommended_next_topics: string[];
  due_revisions_count: number;
  due_revisions: DueRevisionItem[];
  recent_activity: ActivityItem[];
}

export interface HealthResponse {
  status: string;
  service: string;
  registered_concepts: number;
  registered_misconceptions: number;
  available_likelihood_models?: number;
  question_bank_size: number;
  tracked_students: number;
}

export interface ConceptHeatmapView {
  concept_id: string;
  concept_name: string;
  topic: string;
  average_mastery: number;
  struggling_students_count: number;
  mastered_students_count: number;
}

export interface StudentAtRiskView {
  student_id: string;
  overall_proficiency: number;
  primary_deficit_concept: string;
  active_misconceptions: string[];
  recommended_intervention: string;
}

export interface TeacherAnalyticsResponse {
  total_students: number;
  class_average_proficiency: number;
  concept_heatmaps: ConceptHeatmapView[];
  frequent_misconceptions: Array<{
    misconception_id: string;
    affected_students_count: number;
    [key: string]: unknown;
  }>;
  students_at_risk: StudentAtRiskView[];
  topic_readiness: Record<string, number>;
  actionable_teaching_insights: string[];
}
