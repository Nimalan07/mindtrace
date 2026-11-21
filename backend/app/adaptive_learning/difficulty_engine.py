from typing import List, Optional
from backend.app.adaptive_learning.assessment_schemas import QuestionDifficulty


class AdaptiveDifficultyEngine:
    """
    Transparent rule-based difficulty adaptation calibrated against
    current BKT concept mastery and recent performance streaks.
    """

    def __init__(
        self,
        easy_threshold: float = 0.40,
        hard_threshold: float = 0.75,
    ) -> None:
        self.easy_threshold = easy_threshold
        self.hard_threshold = hard_threshold

    def determine_difficulty(
        self,
        current_mastery: float,
        recent_correct_streak: int = 0,
        recent_incorrect_streak: int = 0,
    ) -> tuple[QuestionDifficulty, str]:
        """
        Compute optimal question difficulty based on student knowledge state
        and recent streak adjustments.
        """
        if current_mastery < self.easy_threshold:
            base_diff = QuestionDifficulty.EASY
            rationale = (
                f"Mastery probability ({current_mastery:.2f}) is below {self.easy_threshold:.2f}; "
                "recommending Easy foundational practice."
            )
        elif current_mastery < self.hard_threshold:
            base_diff = QuestionDifficulty.MEDIUM
            rationale = (
                f"Mastery probability ({current_mastery:.2f}) indicates intermediate competence; "
                "recommending Medium reinforcement questions."
            )
        else:
            base_diff = QuestionDifficulty.HARD
            rationale = (
                f"Mastery probability ({current_mastery:.2f}) exceeds {self.hard_threshold:.2f}; "
                "recommending Hard challenge to verify deep transfer."
            )

        # Dynamic streak modifications
        if recent_correct_streak >= 3 and base_diff == QuestionDifficulty.EASY:
            return QuestionDifficulty.MEDIUM, (
                f"{rationale} (Upgraded to Medium following {recent_correct_streak} consecutive correct answers)."
            )
        if recent_correct_streak >= 3 and base_diff == QuestionDifficulty.MEDIUM:
            return QuestionDifficulty.HARD, (
                f"{rationale} (Upgraded to Hard following {recent_correct_streak} consecutive correct answers)."
            )

        if recent_incorrect_streak >= 2 and base_diff == QuestionDifficulty.HARD:
            return QuestionDifficulty.MEDIUM, (
                f"{rationale} (Downgraded to Medium following {recent_incorrect_streak} consecutive errors)."
            )
        if recent_incorrect_streak >= 2 and base_diff == QuestionDifficulty.MEDIUM:
            return QuestionDifficulty.EASY, (
                f"{rationale} (Downgraded to Easy following {recent_incorrect_streak} consecutive errors)."
            )

        return base_diff, rationale
