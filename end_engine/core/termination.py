from dataclasses import dataclass

from .state import Complexity, StopReason, WeaknessStatus


@dataclass(frozen=True)
class TerminationDecision:
    reason: StopReason | None
    explanation: str


class TerminationController:
    def __init__(self, config):
        self.config = config

    def evaluate(self, *, analysis, iterations, verification, scores, weaknesses,
                 repeated_critiques=0, external_blocker=None, cognitive_state=None):
        if external_blocker:
            return TerminationDecision(StopReason.EXTERNAL_BLOCKER, external_blocker)
        if analysis.complexity is Complexity.FAST:
            return TerminationDecision(StopReason.FAST_PATH, "Fast mode skips recursive deliberation")
        budget = analysis.reasoning_budget
        if cognitive_state is not None:
            from ..cognition.state import AssumptionStatus, CoverageLevel
            remaining = dict(cognitive_state.remaining_budget).get("operations", 0)
            if remaining <= 0:
                return TerminationDecision(StopReason.BUDGET_EXHAUSTED, "Shared cognitive operation budget exhausted")
            if cognitive_state.active_branches:
                if iterations >= budget.max_cycles:
                    return TerminationDecision(StopReason.BUDGET_EXHAUSTED, "Cycle cap reached with branches requiring closure")
                return TerminationDecision(None, "Active branch evaluations/synthesis must complete")
            severe_assumptions = any(a.risk in ("HIGH", "CRITICAL") and a.status in
                (AssumptionStatus.UNTESTED, AssumptionStatus.WEAKENED) for a in cognitive_state.assumptions)
            major = {"correctness", "assumptions", "failure_modes", "evidence", "alternatives", "architecture", "safety", "second_order_effects"}
            missing = [d for d, level in cognitive_state.coverage if d in major and level is CoverageLevel.NONE]
            critical_gaps = analysis.complexity is Complexity.CRITICAL and (missing or severe_assumptions or cognitive_state.claims_without_evidence)
            if critical_gaps:
                if iterations >= budget.max_cycles:
                    return TerminationDecision(StopReason.BUDGET_EXHAUSTED, "Critical scrutiny/evidence gaps remain at the cycle cap")
                return TerminationDecision(None, "Critical task still has missing coverage, severe assumptions, or evidence gaps")
            if severe_assumptions:
                return TerminationDecision(StopReason.BUDGET_EXHAUSTED if iterations >= budget.max_cycles else None,
                                           "High-risk assumptions still need scrutiny")
            recent = cognitive_state.recent_outcomes[-self.config.cognitive_stagnation_patience:]
            if (iterations >= budget.min_cycles and len(recent) >= self.config.cognitive_stagnation_patience
                    and all(o.information_gain.level in ("LOW", "ZERO") for o in recent)
                    and not cognitive_state.high_severity_weaknesses):
                return TerminationDecision(StopReason.NO_MATERIAL_IMPROVEMENT, "Recent operations have diminishing cognitive value")
        if iterations >= budget.min_cycles and verification is not None:
            high_open = any(w.status is WeaknessStatus.OPEN and w.severity in ("high", "critical") for w in weaknesses)
            critical = analysis.complexity is Complexity.CRITICAL
            threshold = self.config.critical_quality_threshold if critical else self.config.quality_threshold
            acceptable = not high_open and not verification.remaining_issues
            if acceptable and verification.passed and verification.score >= threshold:
                return TerminationDecision(StopReason.QUALITY_THRESHOLD_REACHED,
                                           f"Score {verification.score:.3f} reaches {threshold:.3f}; no open high-severity issues")
            if acceptable and verification.passed and not critical:
                return TerminationDecision(StopReason.VERIFIER_PASSED, "Verifier passed after minimum scrutiny")
        if iterations >= budget.max_cycles:
            return TerminationDecision(StopReason.BUDGET_EXHAUSTED, "Maximum revision cycles reached; remaining issues are retained")
        if iterations < budget.min_cycles:
            return TerminationDecision(None, "Minimum scrutiny budget not yet met")
        deltas = [b - a for a, b in zip(scores, scores[1:])]
        if (repeated_critiques >= self.config.repeated_critique_patience and deltas
                and deltas[-1] <= self.config.improvement_epsilon):
            return TerminationDecision(StopReason.REPEATED_CRITIQUE, "Findings repeat without material score improvement")
        patience = self.config.stagnation_patience + int(analysis.complexity is Complexity.CRITICAL)
        if len(deltas) >= patience and all(delta <= self.config.improvement_epsilon for delta in deltas[-patience:]):
            return TerminationDecision(StopReason.NO_MATERIAL_IMPROVEMENT,
                                       f"Last {patience} revisions improved by at most {self.config.improvement_epsilon}")
        return TerminationDecision(None, "Further scrutiny may materially improve the candidate")
