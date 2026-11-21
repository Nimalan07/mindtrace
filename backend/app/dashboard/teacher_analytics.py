from typing import Any, Dict, List, Optional

from backend.app.adaptive_learning.learner_model import LearnerModel
from backend.app.dashboard.dashboard_schemas import (
    ConceptHeatmapView,
    StudentAtRiskView,
    TeacherAnalyticsResponse,
)
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.misconception_library import MisconceptionLibrary


class TeacherAnalyticsService:
    """Computes classroom-wide diagnostic distributions, misconception prevalence, and alerts."""

    def __init__(
        self,
        learner_model: LearnerModel,
        concept_graph: ConceptGraph,
        misconception_library: MisconceptionLibrary,
    ) -> None:
        self.learner_model = learner_model
        self.concept_graph = concept_graph
        self.misconception_library = misconception_library

    def get_teacher_dashboard(self) -> TeacherAnalyticsResponse:
        """Synthesize class-wide analytics across all active student profiles."""
        profiles = list(self.learner_model._profiles.values())
        total_students = len(profiles)

        if total_students == 0:
            return TeacherAnalyticsResponse(
                total_students=0,
                class_average_proficiency=0.0,
                concept_heatmaps=[],
                frequent_misconceptions=[],
                students_at_risk=[],
                topic_readiness={},
                actionable_teaching_insights=["No student data currently recorded."],
            )

        # 1. Class average proficiency
        class_avg = sum(p.overall_proficiency for p in profiles) / total_students

        # 2. Concept heatmaps
        all_concepts = self.concept_graph.get_all_concepts()
        heatmaps: List[ConceptHeatmapView] = []
        topic_sums: Dict[str, List[float]] = {}

        for cid in sorted(all_concepts):
            c_meta = self.concept_graph.get_concept(cid)
            c_name = c_meta.get("name", cid)
            c_topic = c_meta.get("topic", "General")

            masteries = [self.learner_model.get_concept_mastery(p.student_id, cid) for p in profiles]
            avg_m = sum(masteries) / len(masteries)
            struggling = sum(1 for m in masteries if m < 0.50)
            mastered = sum(1 for m in masteries if m >= 0.80)

            topic_sums.setdefault(c_topic, []).append(avg_m)

            heatmaps.append(
                ConceptHeatmapView(
                    concept_id=cid,
                    concept_name=c_name,
                    topic=c_topic,
                    average_mastery=round(avg_m, 4),
                    struggling_students_count=struggling,
                    mastered_students_count=mastered,
                )
            )

        # 3. Topic readiness
        topic_readiness: Dict[str, float] = {
            t: round(sum(scores) / len(scores), 4) for t, scores in topic_sums.items()
        }

        # 4. Misconception prevalence tracking
        misconception_counts: Dict[str, set] = {}
        for p in profiles:
            for rec in p.concept_masteries.values():
                for entry in rec.history:
                    if entry.get("source") == "diagnosis_export":
                        for m_id in entry.get("candidate_misconceptions", []):
                            if m_id != "unknown_or_other":
                                misconception_counts.setdefault(m_id, set()).add(p.student_id)

        frequent_misconceptions: List[Dict[str, Any]] = []
        for m_id, student_set in misconception_counts.items():
            m_item = self.misconception_library.get_by_id(m_id)
            title = m_item.title if m_item else m_id
            count = len(student_set)
            pct = round(count / total_students, 4)
            frequent_misconceptions.append(
                {
                    "misconception_id": m_id,
                    "title": title,
                    "affected_students_count": count,
                    "prevalence_percentage": pct,
                }
            )
        frequent_misconceptions.sort(key=lambda m: m["affected_students_count"], reverse=True)

        # 5. Students at risk identification
        students_at_risk: List[StudentAtRiskView] = []
        for p in profiles:
            weaknesses = [
                cid
                for cid, rec in p.concept_masteries.items()
                if rec.mastery_probability < 0.45
            ]
            if p.overall_proficiency < 0.45 or len(weaknesses) >= 2:
                # Find primary deficit
                primary_deficit = weaknesses[0] if weaknesses else "force"
                c_name = self.concept_graph.get_concept(primary_deficit).get("name", primary_deficit)

                # Find any active misconceptions
                student_m: List[str] = []
                for rec in p.concept_masteries.values():
                    for entry in rec.history:
                        student_m.extend(entry.get("candidate_misconceptions", []))
                unique_m = list(set(student_m) - {"unknown_or_other"})

                rec_action = (
                    f"Assign scaffolded prerequisite intervention on '{c_name}'."
                )
                if unique_m:
                    rec_action += f" Address confirmed misconception: {unique_m[0]}."

                students_at_risk.append(
                    StudentAtRiskView(
                        student_id=p.student_id,
                        overall_proficiency=p.overall_proficiency,
                        primary_deficit_concept=c_name,
                        active_misconceptions=unique_m,
                        recommended_intervention=rec_action,
                    )
                )

        students_at_risk.sort(key=lambda s: s.overall_proficiency)

        # 6. Actionable pedagogical insights
        insights: List[str] = []
        if frequent_misconceptions:
            top_m = frequent_misconceptions[0]
            insights.append(
                f"High-frequency misconception alert: {top_m['title']} affects "
                f"{top_m['prevalence_percentage']:.1%} of students. Dedicate the first 10 minutes of next lecture "
                "to contrasting this misconception with Newton's laws."
            )

        # Identify lowest topic
        if topic_readiness:
            lowest_topic = min(topic_readiness.items(), key=lambda kv: kv[1])
            if lowest_topic[1] < 0.50:
                insights.append(
                    f"Classroom readiness in '{lowest_topic[0]}' is critically low ({lowest_topic[1]:.1%}). "
                    "Recommend prerequisite reviews before moving to advanced dynamics."
                )

        if len(students_at_risk) > 0:
            insights.append(
                f"{len(students_at_risk)} student(s) flagged as requiring 1-on-1 scaffolding or diagnostic practice."
            )

        if not insights:
            insights.append("Classroom performance is stable. Continue with curriculum milestones.")

        return TeacherAnalyticsResponse(
            total_students=total_students,
            class_average_proficiency=round(class_avg, 4),
            concept_heatmaps=heatmaps,
            frequent_misconceptions=frequent_misconceptions,
            students_at_risk=students_at_risk,
            topic_readiness=topic_readiness,
            actionable_teaching_insights=insights,
        )
