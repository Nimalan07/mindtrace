import { apiClient } from "./api";
import {
  AdaptiveNextQuestionRequest,
  AdaptiveNextQuestionResponse,
  AssessmentAnswerRequest,
  AssessmentEvaluation,
  InterventionPlan,
  SpacedRepetitionCard,
  SpacedReviewRequest,
} from "@/types/adaptive.types";

export const adaptiveService = {
  async getNextQuestion(request: AdaptiveNextQuestionRequest): Promise<AdaptiveNextQuestionResponse> {
    const res = await apiClient.post<AdaptiveNextQuestionResponse>("/api/adaptive/question/next", request);
    return res.data;
  },

  async submitAssessmentAnswer(request: AssessmentAnswerRequest): Promise<AssessmentEvaluation> {
    const res = await apiClient.post<AssessmentEvaluation>("/api/adaptive/assessment/submit", request);
    return res.data;
  },

  async getDueSpacedCards(studentId: string): Promise<SpacedRepetitionCard[]> {
    const encoded = encodeURIComponent(studentId.trim());
    const res = await apiClient.get<SpacedRepetitionCard[]>(`/api/adaptive/spaced-repetition/due/${encoded}`);
    return res.data;
  },

  async recordSpacedReview(request: SpacedReviewRequest): Promise<SpacedRepetitionCard> {
    const res = await apiClient.post<SpacedRepetitionCard>("/api/adaptive/spaced-repetition/review", request);
    return res.data;
  },

  async getInterventionForConcept(studentId: string, conceptId: string): Promise<InterventionPlan> {
    const sId = encodeURIComponent(studentId.trim());
    const cId = encodeURIComponent(conceptId.trim());
    const res = await apiClient.get<InterventionPlan>(`/api/adaptive/intervention/${sId}/${cId}`);
    return res.data;
  },

  async getInterventionFromSession(sessionId: string): Promise<InterventionPlan> {
    const sId = encodeURIComponent(sessionId.trim());
    const res = await apiClient.post<InterventionPlan>(`/api/adaptive/intervention/session/${sId}`);
    return res.data;
  },
};
