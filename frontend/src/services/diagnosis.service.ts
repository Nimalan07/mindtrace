import { apiClient } from "./api";
import {
  ConceptListResponse,
  DiagnosticTask,
  DiagnosisFollowupRequest,
  DiagnosisFollowupResponse,
  DiagnosisSubmitRequest,
  DiagnosisSubmitResponse,
  Member2DiagnosisExport,
} from "@/types/diagnosis.types";

export const diagnosisService = {
  async getConcepts(): Promise<ConceptListResponse> {
    const res = await apiClient.get<ConceptListResponse>("/api/diagnosis/concepts");
    return res.data;
  },

  async getDiagnosticQuestions(): Promise<DiagnosticTask[]> {
    const res = await apiClient.get<DiagnosticTask[]>("/api/diagnosis/questions");
    return res.data;
  },

  async getDiagnosticQuestionForConcept(conceptId: string): Promise<DiagnosticTask> {
    const encoded = encodeURIComponent(conceptId.trim());
    const res = await apiClient.get<DiagnosticTask>(`/api/diagnosis/questions/${encoded}`);
    return res.data;
  },

  async submitDiagnosis(request: DiagnosisSubmitRequest): Promise<DiagnosisSubmitResponse> {
    const res = await apiClient.post<DiagnosisSubmitResponse>("/api/diagnosis/submit", request);
    return res.data;
  },

  async submitFollowup(request: DiagnosisFollowupRequest): Promise<DiagnosisFollowupResponse> {
    const res = await apiClient.post<DiagnosisFollowupResponse>("/api/diagnosis/followup", request);
    return res.data;
  },

  async exportDiagnosis(sessionId: string): Promise<Member2DiagnosisExport> {
    const encoded = encodeURIComponent(sessionId.trim());
    const res = await apiClient.get<Member2DiagnosisExport>(`/api/diagnosis/session/${encoded}/export`);
    return res.data;
  },
};
