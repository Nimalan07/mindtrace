import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from backend.app.diagnosis.bayesian_engine import BayesianEngine
from backend.app.diagnosis.bayesian_schemas import (
    DiagnosticQuestionModel,
    DiagnosticSession,
    ResponseCategory,
)


class ActiveQuestionSelector:
    """
    Selects the diagnostic follow-up question that maximizes expected Information Gain (IG).
    
    Uses Shannon entropy:
    H(H) = -sum(P(Hi) * log2(P(Hi)))
    IG(Q) = H(H) - sum_r(P(r|Q) * H(H|r,Q))
    """

    RESPONSE_CATEGORIES: List[ResponseCategory] = [
        "supports_hypothesis",
        "weakens_hypothesis",
        "neutral_or_inconclusive",
    ]

    def __init__(
        self,
        question_catalog: Optional[List[DiagnosticQuestionModel]] = None,
    ) -> None:
        self.question_catalog: List[DiagnosticQuestionModel] = question_catalog or []

    @classmethod
    def load_from_json(cls, file_path: Union[str, Path]) -> "ActiveQuestionSelector":
        """Load question likelihood models from a JSON file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Likelihood catalog file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        questions: List[DiagnosticQuestionModel] = [
            DiagnosticQuestionModel.model_validate(q) for q in raw_data.get("questions", [])
        ]
        return cls(question_catalog=questions)

    def calculate_information_gain(
        self,
        current_distribution: Dict[str, float],
        question: DiagnosticQuestionModel,
    ) -> float:
        """
        Calculate expected information gain (reduction in Shannon entropy) for a question.
        """
        prior_entropy = BayesianEngine.calculate_entropy(current_distribution)

        expected_conditional_entropy = 0.0

        for r in self.RESPONSE_CATEGORIES:
            # P(r | Q) = sum_i(P(r | Hi, Q) * P(Hi))
            prob_r = 0.0
            unnormalized_posteriors: Dict[str, float] = {}

            for h, prior in current_distribution.items():
                hyp_likelihoods = question.response_likelihoods.get(h)
                if hyp_likelihoods is not None:
                    likelihood = hyp_likelihoods.get(r, 0.0)
                else:
                    # Neutral uniform fallback for unmodeled hypotheses
                    likelihood = 1.0 / len(self.RESPONSE_CATEGORIES)

                joint = likelihood * prior
                prob_r += joint
                unnormalized_posteriors[h] = joint

            if prob_r > 0.0:
                # Posterior distribution given response r
                post_r = {h: joint / prob_r for h, joint in unnormalized_posteriors.items()}
                entropy_given_r = BayesianEngine.calculate_entropy(post_r)
                expected_conditional_entropy += prob_r * entropy_given_r

        information_gain = prior_entropy - expected_conditional_entropy
        # Clip small negative numerical artifacts to 0.0
        return max(0.0, information_gain)

    def select_best_question(
        self,
        session: DiagnosticSession,
        available_questions: Optional[List[DiagnosticQuestionModel]] = None,
    ) -> Tuple[Optional[DiagnosticQuestionModel], float, str]:
        """
        Select the question with the highest information gain that has not yet been asked.
        Breaks ties deterministically using question_id alphabetical order.
        """
        candidates = available_questions if available_questions is not None else self.question_catalog
        current_distribution = {
            h: belief.posterior_probability
            for h, belief in session.hypothesis_beliefs.items()
        }

        # Filter out questions already asked in this session
        unasked = [
            q for q in candidates if q.question_id not in session.asked_question_ids
        ]

        if not unasked:
            return None, 0.0, "No available unasked questions remaining in catalog."

        evaluated_questions: List[Tuple[float, str, DiagnosticQuestionModel]] = []

        for q in unasked:
            if not q.response_likelihoods:
                # Fallback mode for questions lacking a likelihood model
                evaluated_questions.append((0.0, q.question_id, q))
            else:
                ig = self.calculate_information_gain(current_distribution, q)
                evaluated_questions.append((ig, q.question_id, q))

        # Sort by: -information_gain (descending), then question_id (ascending)
        evaluated_questions.sort(key=lambda item: (-item[0], item[1]))

        best_ig, best_qid, best_question = evaluated_questions[0]

        if not best_question.response_likelihoods:
            rationale = (
                f"Selected question '{best_qid}' via fallback mode; "
                f"likelihood model unavailable (Information Gain not computed)."
            )
        else:
            rationale = (
                f"Selected question '{best_qid}' maximizing expected Information Gain "
                f"({best_ig:.4f} bits) across competing hypotheses."
            )

        return best_question, best_ig, rationale
