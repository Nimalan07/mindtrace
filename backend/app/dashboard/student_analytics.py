from typing import Any, Dict, List

from backend.app.adaptive_learning.learner_model import LearnerModel
from backend.app.adaptive_learning.spaced_repetition import SpacedRepetitionEngine
from backend.app.dashboard.dashboard_schemas import (
    ConceptMasteryView,
    MasteryStatus,
    StudentAnalyticsResponse,
)
from backend.app.diagnosis.concept_graph import ConceptGraph


class StudentAnalyticsService:
    """Computes personalized progress metrics, mastery distribution, and revision alerts."""

    def __init__(
        self,
        learner_model: LearnerModel,
        concept_graph: ConceptGraph,
        spaced_repetition_engine: SpacedRepetitionEngine,
    ) -> None:
        self.learner_model = learner_model
        self.concept_graph = concept_graph
        self.spaced_repetition = spaced_repetition_engine

    def get_student_dashboard(self, student_id: str) -> StudentAnalyticsResponse:
        """Synthesize end-to-end dashboard analytics for a single student."""
        profile = self.learner_model.get_or_create_profile(student_id)
        all_concepts = self.concept_graph.get_all_concepts()

        breakdown: List[ConceptMasteryView] = []
        counts = {"mastered": 0, "practicing": 0, "needs_support": 0}

        for cid in sorted(all_concepts):
            c_meta = self.concept_graph.get_concept(cid)
            c_name = c_meta.get("name", cid)
            c_topic = c_meta.get("topic", "General")

            rec = profile.concept_masteries.get(cid)
            p_l = rec.mastery_probability if rec else self.learner_model.default_p_l0
            opps = rec.opportunities if rec else 0
            corrects = rec.correct_count if rec else 0

            if p_l >= 0.80:
                st = MasteryStatus.MASTERED
                counts["mastered"] += 1
            elif p_l >= 0.50:
                st = MasteryStatus.PRACTICING
                counts["practicing"] += 1
            else:
                st = MasteryStatus.NEEDS_SUPPORT
                counts["needs_support"] += 1

            breakdown.append(
                ConceptMasteryView(
                    concept_id=cid,
                    concept_name=c_name,
                    topic=c_topic,
                    mastery_probability=round(p_l, 4),
                    status=st,
                    opportunities=opps,
                    correct_count=corrects,
                )
            )

        # Sort for strengths and weaknesses
        sorted_by_mastery = sorted(breakdown, key=lambda v: v.mastery_probability, reverse=True)
        strengths = [
            f"{v.concept_name} ({v.mastery_probability:.1%})"
            for v in sorted_by_mastery
            if v.mastery_probability >= 0.70
        ][:3]

        weaknesses = [
            f"{v.concept_name} ({v.mastery_probability:.1%})"
            for v in reversed(sorted_by_mastery)
            if v.mastery_probability < 0.50
        ][:3]

        # Recommended next topics: concepts where prerequisites are mastered but concept is not
        recommended_next: List[str] = []
        for cid in self.concept_graph.get_learning_order():
            c_p_l = self.learner_model.get_concept_mastery(student_id, cid)
            if c_p_l < 0.75:
                # Check prerequisites
                prereqs = self.concept_graph.get_direct_prerequisites(cid)
                prereqs_ok = all(
                    self.learner_model.get_concept_mastery(student_id, p) >= 0.50
                    for p in prereqs
                )
                if prereqs_ok:
                    recommended_next.append(self.concept_graph.get_concept(cid).get("name", cid))
                    if len(recommended_next) >= 3:
                        break

        # Spaced repetition cards
        due_cards = self.spaced_repetition.get_due_cards(student_id)
        due_views = [
            {
                "concept_id": c.concept_id,
                "concept_name": self.concept_graph.get_concept(c.concept_id).get("name", c.concept_id),
                "interval_days": c.interval_days,
                "repetition_count": c.repetition_count,
                "urgency_score": c.urgency_score,
                "next_review_due": c.next_review_due.isoformat(),
            }
            for c in due_cards[:5]
        ]

        # Recent activity extraction
        recent_activity: List[Dict[str, Any]] = []
        for rec in profile.concept_masteries.values():
            for h in rec.history:
                entry = dict(h)
                entry["concept_id"] = rec.concept_id
                entry["concept_name"] = self.concept_graph.get_concept(rec.concept_id).get("name", rec.concept_id)
                recent_activity.append(entry)

        # Sort recent activity descending by timestamp
        recent_activity.sort(key=lambda a: a.get("timestamp", ""), reverse=True)

        accuracy = (
            round(profile.total_correct / profile.total_assessments, 4)
            if profile.total_assessments > 0
            else 0.0
        )

        return StudentAnalyticsResponse(
            student_id=student_id,
            overall_proficiency=profile.overall_proficiency,
            total_assessments=profile.total_assessments,
            total_correct=profile.total_correct,
            accuracy_rate=accuracy,
            mastery_counts=counts,
            concept_mastery_breakdown=breakdown,
            strengths=strengths,
            critical_weaknesses=weaknesses,
            recommended_next_topics=recommended_next,
            due_revisions_count=len(due_cards),
            due_revisions=due_views,
            recent_activity=recent_activity[:10],
        )
