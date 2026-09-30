from collections import Counter
from dataclasses import replace

from .knowledge import KnowledgeRegister
from .state import (AssumptionStatus, CognitiveState, CoverageLevel, EvidenceStatus,
                    InformationGain, OperatorOutcome, OutcomeStats)
from ..core.state import to_data


class CognitiveSession:
    def __init__(self, analysis, config, trajectory, extractor=None):
        self.analysis, self.config, self.trajectory = analysis, config, trajectory
        self.knowledge = KnowledgeRegister(trajectory, extractor)
        self.outcomes = []
        self.priority_adjustments = {}
        self.coverage_points = {d: 0 for d in analysis.dimensions}
        if analysis.complexity.value in ("deep", "critical"):
            self.coverage_points.update({d: 0 for d in ("assumptions", "evidence", "alternatives", "failure_modes", "second_order_effects")})
        self.operations_used = 0
        self.operation_limit = config.max_cognitive_operations
        if self.operation_limit is None:
            self.operation_limit = analysis.reasoning_budget.max_cycles + config.max_branches_per_operator
        if analysis.complexity.value == "fast":
            self.operation_limit = 0
        self.reframings = []
        self.last_meta_iteration = -1

    @property
    def remaining(self):
        return max(0, self.operation_limit - self.operations_used)

    def consume(self, units=1):
        if type(units) is not int or units < 0 or units > self.remaining:
            raise ValueError("Cognitive operation budget exceeded")
        self.operations_used += units
        self.trajectory.record("cognitive_budget", {"used": self.operations_used, "remaining": self.remaining})

    def _stats(self, family=False):
        grouped = {}
        for outcome in self.outcomes:
            key = outcome.family if family else outcome.operator
            stats = grouped.get(key, OutcomeStats())
            level = outcome.information_gain.level.lower() + "_gain"
            grouped[key] = replace(stats, uses=stats.uses+1, **{level: getattr(stats, level)+1})
        return tuple(sorted(grouped.items()))

    def state(self, candidate, registry, scores=(), branches=(), verification=None):
        coverage = tuple((name, CoverageLevel.NONE if points == 0 else CoverageLevel.LOW if points == 1
                          else CoverageLevel.MEDIUM if points < 4 else CoverageLevel.HIGH)
                         for name, points in sorted(self.coverage_points.items()))
        deltas = [b-a for a, b in zip(scores, scores[1:])]
        stagnation = 0
        for delta in reversed(deltas):
            if delta > self.config.improvement_epsilon:
                break
            stagnation += 1
        open_items = registry.open()
        # Verifier confidence and scrutiny coverage are distinct signals.
        resolved = tuple(d for d, value in verification.dimensions if value >= 0.8
                         and not any(w.type == d for w in open_items)) if verification else ()
        uncertain = tuple(d for d in self.coverage_points if d not in resolved)
        claims = tuple(self.knowledge.claims[c] for c in self.knowledge.current_claim_ids
                       if self.knowledge.claims[c].evidence_status in (EvidenceStatus.UNVERIFIED, EvidenceStatus.CONTRADICTED))
        state = CognitiveState(candidate.candidate_id, candidate.iteration, self.analysis.complexity.value,
            resolved, uncertain, open_items,
            tuple(w.id for w in open_items if w.severity in ("high", "critical")), claims,
            tuple(self.knowledge.assumptions.values()), tuple(b.branch_id for b in branches),
            tuple(sorted(Counter(o.operator for o in self.outcomes).items())), self._stats(), self._stats(True),
            tuple(self.outcomes[-8:]), deltas[-1] if deltas else 0, stagnation,
            (("cycles", max(0, self.analysis.reasoning_budget.max_cycles-candidate.iteration)),
             ("operations", self.remaining)), coverage, tuple(sorted(self.priority_adjustments.items())),
            tuple(b.branch_id for b in branches if b.status in ("ACTIVE", "PROMISING")))
        self.trajectory.record("cognitive_state", state, "cognitive_states")
        self.trajectory.set("cognitive_coverage", dict(coverage))
        self.trajectory.set("operator_statistics", dict(self._stats()))
        return state

    def complete(self, operator, question, findings, before_ids, knowledge_changes, *, branches=(), direction_changed=False):
        new_ids = set(w.id for w in findings) - before_ids
        duplicates = len(findings) - len(new_ids)
        viable = sum(b.status in ("PROMISING", "MERGED") for b in branches)
        information = len(new_ids) + knowledge_changes + viable
        level = "HIGH" if information >= 2 else "MEDIUM" if information else "LOW" if duplicates else "ZERO"
        gain = InformationGain(level, len(new_ids), duplicates, knowledge_changes, viable, direction_changed)
        outcome = OperatorOutcome(operator.name, operator.family, question.target.target_id, question.intent,
                                  question.question_id, tuple(w.id for w in findings), gain)
        self.outcomes.append(outcome)
        points = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "ZERO": 0}[level]
        for dimension in set(operator.targets) | {question.target.dimension}:
            if dimension in self.coverage_points:
                self.coverage_points[dimension] = (max(self.coverage_points[dimension], 1) if level == "LOW"
                                                   else self.coverage_points[dimension]+points)
        self.trajectory.record("operator_outcome", outcome, "operator_outcomes")
        return outcome

    def reframe(self, proposal, original_task, candidate_id):
        if self.analysis.complexity.value not in ("deep", "critical") or len(self.reframings) >= self.config.max_reframings:
            self.trajectory.record("reframing_declined", {"proposal": proposal, "reason": "Mode or reframing limit"})
            return None
        record = {"original_problem": original_task, **proposal, "source_candidate": candidate_id,
                  "status": "PROPOSED", "goal_replaced": False}
        self.reframings.append(record)
        self.priority_adjustments["foundational"] = 0.35
        self.trajectory.record("reframing", record, "reframings")
        return record

    def enrich_outcome(self, branches, direction_changed):
        before = self.outcomes[-1]
        viable = sum(b.status == "MERGED" for b in branches)
        information = before.information_gain.new_findings + before.information_gain.knowledge_changes + viable
        gain = replace(before.information_gain, viable_alternatives=viable,
                       changed_candidate_direction=direction_changed,
                       level="HIGH" if information >= 2 else "MEDIUM" if information else before.information_gain.level)
        after = replace(before, information_gain=gain)
        self.outcomes[-1] = after
        self.trajectory.record("operator_outcome_enriched", {"before": before, "after": after})
        self.trajectory.set("operator_outcomes", self.outcomes)
        if viable:
            self.coverage_points["alternatives"] = self.coverage_points.get("alternatives", 0)+viable


class MetaController:
    def check(self, state):
        recent = state.recent_outcomes[-3:]
        families = {o.family for o in recent}
        low_value = sum(o.information_gain.level in ("LOW", "ZERO") for o in recent)
        adjustments, reasons = {}, []
        if len(recent) >= 2 and (len(families) == 1 or low_value >= 2):
            adjustments["search"] = 0.6
            reasons.append("Recent operations are concentrated or low-value; inspect a competing approach")
        if recent and all(o.family == "optimization" for o in recent):
            adjustments["adversarial"] = 0.6
            reasons.append("Presentation/optimization scrutiny is crowding out substantive failure checks")
        if state.claims_without_evidence:
            adjustments["epistemic"] = 0.12
            reasons.append("Unverified claims remain")
        return {"candidate_id": state.current_candidate_id, "questions": [
                    "Are we attacking the right uncertainty?", "Would an unexplored alternative add more information?"],
                "priority_adjustments": adjustments, "rationale": reasons or ["No priority correction needed"]}
