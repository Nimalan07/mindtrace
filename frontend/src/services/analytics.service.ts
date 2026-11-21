import { apiClient } from "./api";
import {
  HealthResponse,
  StudentAnalyticsResponse,
  TeacherAnalyticsResponse,
} from "@/types/analytics.types";

export const analyticsService = {
  /**
   * Retrieves comprehensive BKT mastery and progress analytics for a specific student.
   * Directly interfaces with GET /api/analytics/student/{student_id}
   */
  async getStudentAnalytics(studentId: string): Promise<StudentAnalyticsResponse> {
    const encodedId = encodeURIComponent(studentId.trim());
    const response = await apiClient.get<StudentAnalyticsResponse>(
      `/api/analytics/student/${encodedId}`
    );
    return response.data;
  },

  /**
   * Checks the health and operational status of the MINDTRACE unified engine.
   * Directly interfaces with GET /health
   */
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },

  /**
   * Retrieves classroom-level analytics, concept heatmaps, and at-risk alerts.
   * Directly interfaces with GET /api/analytics/teacher
   */
  async getTeacherAnalytics(): Promise<TeacherAnalyticsResponse> {
    const response = await apiClient.get<TeacherAnalyticsResponse>("/api/analytics/teacher");
    return response.data;
  },
};
