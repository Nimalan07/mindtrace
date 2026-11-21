import math
from typing import Dict, List, Optional

from backend.app.diagnosis.bayesian_schemas import (
    BayesianUpdateResult,
    DiagnosticQuestionModel,
    DiagnosticSession,
    EvidenceObservation,
    HypothesisBelief,
    ResponseCategory,
    SessionStatus,
)


class BayesianEngine:
    """
    Evidence-driven Bayesian verification engine for candidate misconception hypotheses.
    
    Maintains competing hypothesis distributions, applies Bayes' Theorem with
    numerically stable calculations, prevents repeated evidence double-counting,
    and supports an explicit unknown_or_other hypothesis.
    """

    UNKNOWN_HYPOTHESIS = "unknown_or_other"

    def __init__(
        self,
        posterior_threshold: float = 0.80,
        min_evidence_count: int = 2,
    ) -> None:
        self.posterior_threshold = posterior_threshold
        self.min_evidence_count = min_evidence_count

    @staticmethod
    def calculate_entropy(distribution: Dict[str, float]) -> float:
        """
        Compute Shannon entropy in bits:
        H(H) = -sum(P(Hi) * log2(P(Hi)))
        """
        entropy = 0.0
        for p in distribution.values():
            if p > 0.0:
                entropy -= p * math.log2(p)
        return entropy

    def initialize_session(
        self,
        session_id: str,
        candidate_hypotheses: List[str],
        custom_priors: Optional[Dict[str, float]] = None,
        include_unknown: bool = True,
    ) -> DiagnosticSession:
        """
        Initialize an auditable diagnostic session.
        If custom_priors is omitted, defaults to a uniform baseline distribution.
        """
        hypotheses = list(candidate_hypotheses)
        if include_unknown and self.UNKNOWN_HYPOTHESIS not in hypotheses:
            hypotheses.append(self.UNKNOWN_HYPOTHESIS)

        if len(hypotheses) == 0:
            raise ValueError("Cannot initialize session with empty hypotheses.")

        beliefs: Dict[str, HypothesisBelief] = {}

        if custom_priors is not None:
            # Validate custom priors keys
            for h in hypotheses:
                if h not in custom_priors:
                    raise ValueError(f"Missing prior for hypothesis '{h}' in custom_priors.")

            # Normalize custom priors safely
            total = sum(custom_priors[h] for h in hypotheses)
            if total <= 0:
                raise ValueError("Sum of custom priors must be greater than zero.")

            for h in hypotheses:
                normalized_p = custom_priors[h] / total
                beliefs[h] = HypothesisBelief(
                    misconception_id=h,
                    prior_probability=normalized_p,
                    posterior_probability=normalized_p,
                    evidence_count=0,
                )
        else:
            # Baseline uniform prior
            uniform_p = 1.0 / len(hypotheses)
            for h in hypotheses:
                beliefs[h] = HypothesisBelief(
                    misconception_id=h,
                    prior_probability=uniform_p,
                    posterior_probability=uniform_p,
                    evidence_count=0,
                )

        return DiagnosticSession(
            session_id=session_id,
            candidate_hypotheses=hypotheses,
            hypothesis_beliefs=beliefs,
            evidence_history=[],
            asked_question_ids=[],
            session_status="collecting_evidence",
        )

    def update(
        self,
        session: DiagnosticSession,
        observation: EvidenceObservation,
        question_likelihoods: Dict[str, Dict[ResponseCategory, float]],
    ) -> BayesianUpdateResult:
        """
        Execute a sequential Bayesian belief update with the observed evidence.
        
        Calculates:
        P(Hi | E) = (P(E | Hi) * P(Hi)) / sum_j(P(E | Hj) * P(Hj))
        """
        # 1. Prevent processing the same question evidence twice (double-counting)
        if observation.question_id in session.asked_question_ids:
            raise ValueError(
                f"Evidence for question '{observation.question_id}' has already been processed in this session."
            )

        current_distribution = {
            h: belief.posterior_probability
            for h, belief in session.hypothesis_beliefs.items()
        }
        entropy_before = self.calculate_entropy(current_distribution)

        unnormalized_posteriors: Dict[str, float] = {}
        uncertainty_notes: List[str] = []

        category = observation.response_category

        # 2. Compute unnormalized numerator: P(E | Hi) * P(Hi)
        for h, prior in current_distribution.items():
            hyp_likelihood_dist = question_likelihoods.get(h)
            if hyp_likelihood_dist is not None:
                likelihood = hyp_likelihood_dist.get(category, 0.0)
            else:
                # Fallback neutral distribution if hypothesis is unmodeled in question
                likelihood = 1.0 / len(session.candidate_hypotheses)
                uncertainty_notes.append(
                    f"No likelihood model found for hypothesis '{h}' on question '{observation.question_id}'; using fallback."
                )

            unnormalized_posteriors[h] = likelihood * prior

        marginal_evidence = sum(unnormalized_posteriors.values())

        # 3. Handle zero-likelihood edge case safely
        if marginal_evidence <= 0.0:
            uncertainty_notes.append(
                "Marginal probability of evidence evaluated to zero across all hypotheses. Retaining prior beliefs."
            )
            posterior_distribution = current_distribution.copy()
        else:
            posterior_distribution = {
                h: val / marginal_evidence for h, val in unnormalized_posteriors.items()
            }

        entropy_after = self.calculate_entropy(posterior_distribution)

        # 4. Update session beliefs
        updated_beliefs: List[HypothesisBelief] = []
        for h, post_p in posterior_distribution.items():
            old_belief = session.hypothesis_beliefs[h]
            new_belief = HypothesisBelief(
                misconception_id=h,
                prior_probability=old_belief.posterior_probability,
                posterior_probability=post_p,
                evidence_count=old_belief.evidence_count + 1,
            )
            session.hypothesis_beliefs[h] = new_belief
            updated_beliefs.append(new_belief)

        session.evidence_history.append(observation)
        session.asked_question_ids.append(observation.question_id)

        # 5. Evaluate stopping criteria
        max_posterior = max(posterior_distribution.values())
        max_evidence = max(b.evidence_count for b in updated_beliefs)

        if max_posterior >= self.posterior_threshold and max_evidence >= self.min_evidence_count:
            session.session_status = "sufficient_evidence"
        else:
            session.session_status = "collecting_evidence"

        return BayesianUpdateResult(
            hypothesis_beliefs=updated_beliefs,
            evidence_observation=observation,
            entropy_before=entropy_before,
            entropy_after=entropy_after,
            posterior_distribution=posterior_distribution,
            update_status="updated",
            uncertainty_notes=uncertainty_notes,
        )
