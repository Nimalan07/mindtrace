from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.adaptive_learning.bkt_model import BKTModel, BKTParameters, BKTUpdateResult
from backend.app.diagnosis.service_schemas import Member2DiagnosisExport


class ConceptMasteryRecord(BaseModel):
    """Tracking structure for a single concept's mastery lifecycle."""

    model_config = ConfigDict(extra="forbid")

    concept_id: str
    mastery_probability: float = Field(ge=0.0, le=1.0)
    opportunities: int = 0
    correct_count: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    history: List[Dict[str, Any]] = Field(default_factory=list)


class LearnerProfile(BaseModel):
    """Complete learner mastery representation across the curriculum."""

    model_config = ConfigDict(extra="forbid")

    student_id: str
    overall_proficiency: float = Field(ge=0.0, le=1.0, default=0.25)
    concept_masteries: Dict[str, ConceptMasteryRecord] = Field(default_factory=dict)
    total_assessments: int = 0
    total_correct: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LearnerModel:
    """
    In-memory and stateful learner model applying BKT updates and maintaining
    the multi-concept mastery state for students.
    """

    def __init__(
        self,
        bkt_model: Optional[BKTModel] = None,
        default_p_l0: float = 0.25,
    ) -> None:
        self.bkt = bkt_model or BKTModel()
        self.default_p_l0 = default_p_l0
        self._profiles: Dict[str, LearnerProfile] = {}

    def get_or_create_profile(self, student_id: str) -> LearnerProfile:
        """Fetch existing learner profile or initialize with priors."""
        if student_id not in self._profiles:
            self._profiles[student_id] = LearnerProfile(student_id=student_id)
        return self._profiles[student_id]

    def get_concept_mastery(self, student_id: str, concept_id: str) -> float:
        """Retrieve current mastery probability P(L) for a concept."""
        profile = self.get_or_create_profile(student_id)
        record = profile.concept_masteries.get(concept_id)
        if record is None:
            return self.default_p_l0
        return record.mastery_probability

    def get_all_masteries(self, student_id: str) -> Dict[str, float]:
        """Return dict of concept_id -> mastery_probability for all observed concepts."""
        profile = self.get_or_create_profile(student_id)
        return {
            cid: rec.mastery_probability for cid, rec in profile.concept_masteries.items()
        }

    def update_from_assessment(
        self,
        student_id: str,
        concept_id: str,
        is_correct: bool,
        question_id: str,
    ) -> BKTUpdateResult:
        """Update learner mastery following a standard assessment question attempt."""
        profile = self.get_or_create_profile(student_id)
        current_rec = profile.concept_masteries.get(concept_id)

        prior_p_l = current_rec.mastery_probability if current_rec else self.default_p_l0
        opps = (current_rec.opportunities + 1) if current_rec else 1

        bkt_result = self.bkt.update_mastery(
            current_p_l=prior_p_l,
            is_correct=is_correct,
            concept_id=concept_id,
            opportunity_index=opps,
        )

        now = datetime.now(timezone.utc)
        history_entry = {
            "source": "assessment",
            "question_id": question_id,
            "is_correct": is_correct,
            "prior": prior_p_l,
            "posterior": bkt_result.updated_mastery,
            "timestamp": now.isoformat(),
        }

        if current_rec is None:
            new_rec = ConceptMasteryRecord(
                concept_id=concept_id,
                mastery_probability=bkt_result.updated_mastery,
                opportunities=1,
                correct_count=1 if is_correct else 0,
                last_updated=now,
                history=[history_entry],
            )
            profile.concept_masteries[concept_id] = new_rec
        else:
            current_rec.mastery_probability = bkt_result.updated_mastery
            current_rec.opportunities = opps
            if is_correct:
                current_rec.correct_count += 1
            current_rec.last_updated = now
            current_rec.history.append(history_entry)

        profile.total_assessments += 1
        if is_correct:
            profile.total_correct += 1
        self._recalculate_overall_proficiency(profile)
        return bkt_result

    def update_from_diagnosis_export(
        self,
        export: Member2DiagnosisExport,
    ) -> Dict[str, BKTUpdateResult]:
        """
        Consume Member 1's Member2DiagnosisExport to update BKT mastery without arbitrary drops.
        
        Uses explicit mapping based on error category, evidence confidence, and
        misconception posteriors.
        """
        profile = self.get_or_create_profile(export.student_id)
        results: Dict[str, BKTUpdateResult] = {}

        # Determine target concept to update
        target_concept = export.first_error_concept_id
        if not target_concept and export.relevant_concept_ids:
            target_concept = export.relevant_concept_ids[0]

        if not target_concept:
            return results

        # Check for confirmed/dominant misconception
        has_dominant_misconception = False
        for m_id, prob in export.posterior_hypotheses.items():
            if m_id != "unknown_or_other" and prob > 0.60:
                has_dominant_misconception = True
                break

        # Calibrate slip and guess
        calibration = self.bkt.calibrate_from_diagnosis(
            error_category=export.identified_error_category,
            evidence_confidence=export.evidence_confidence,
            has_dominant_misconception=has_dominant_misconception,
        )

        current_rec = profile.concept_masteries.get(target_concept)
        prior_p_l = current_rec.mastery_probability if current_rec else self.default_p_l0
        opps = (current_rec.opportunities + 1) if current_rec else 1

        # An error was diagnosed
        bkt_res = self.bkt.update_mastery(
            current_p_l=prior_p_l,
            is_correct=False,
            concept_id=target_concept,
            opportunity_index=opps,
            custom_slip=calibration["p_s"],
            custom_guess=calibration["p_g"],
            confidence_weight=calibration["confidence_weight"],
        )

        now = datetime.now(timezone.utc)
        history_entry = {
            "source": "diagnosis_export",
            "session_id": export.session_id,
            "question_id": export.question_id,
            "error_category": export.identified_error_category,
            "evidence_confidence": export.evidence_confidence,
            "candidate_misconceptions": export.candidate_misconception_ids,
            "prior": prior_p_l,
            "posterior": bkt_res.updated_mastery,
            "timestamp": now.isoformat(),
        }

        if current_rec is None:
            profile.concept_masteries[target_concept] = ConceptMasteryRecord(
                concept_id=target_concept,
                mastery_probability=bkt_res.updated_mastery,
                opportunities=1,
                correct_count=0,
                last_updated=now,
                history=[history_entry],
            )
        else:
            current_rec.mastery_probability = bkt_res.updated_mastery
            current_rec.opportunities = opps
            current_rec.last_updated = now
            current_rec.history.append(history_entry)

        profile.total_assessments += 1
        self._recalculate_overall_proficiency(profile)
        results[target_concept] = bkt_res
        return results

    def _recalculate_overall_proficiency(self, profile: LearnerProfile) -> None:
        """Update mean proficiency across all tracked concepts."""
        if not profile.concept_masteries:
            profile.overall_proficiency = self.default_p_l0
        else:
            total = sum(rec.mastery_probability for rec in profile.concept_masteries.values())
            profile.overall_proficiency = round(total / len(profile.concept_masteries), 4)
        profile.updated_at = datetime.now(timezone.utc)
