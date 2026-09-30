from typing import Protocol

from .state import (AssumptionStatus, CoverageLevel, OperatorUtility, QuestionTarget,
                    TargetType, UtilityFactors, UtilitySelection)


IMPORTANCE = {"fast": 0.4, "normal": 0.9, "deep": 1.15, "critical": 1.4}
RISK_VALUE = {"low": 0.4, "medium": 0.8, "high": 1.6, "critical": 1.9}


class OperatorSelectionPolicy(Protocol):
    def rank(self, state, operators) -> tuple[OperatorUtility, ...]: ...
    def select(self, state, operators) -> UtilitySelection: ...


class UtilitySelectionPolicy:
    def target(self, state, operator):
        candidates = []
        for w in state.open_weaknesses:
            if w.type in (*operator.targets, *operator.trigger_conditions):
                candidates.append((RISK_VALUE[w.severity], QuestionTarget(TargetType.WEAKNESS, w.id, w.description, w.type)))
        if "ASSUMPTION" in operator.preferred_target_types:
            for a in state.assumptions:
                if a.status in (AssumptionStatus.UNTESTED, AssumptionStatus.WEAKENED):
                    candidates.append((RISK_VALUE[a.risk.lower()], QuestionTarget(TargetType.ASSUMPTION,
                        a.assumption_id, a.statement, "assumptions")))
        if set(operator.preferred_target_types) & {"CLAIM", "EVIDENCE_GAP"}:
            for claim in state.claims_without_evidence:
                candidates.append((0.95, QuestionTarget(TargetType.EVIDENCE_GAP if "EVIDENCE_GAP" in operator.preferred_target_types
                    else TargetType.CLAIM, claim.claim_id, claim.text, "evidence")))
        if candidates:
            # Prefer an unexamined target among equally valuable targets.
            def value(pair):
                repeats = sum(o.operator == operator.name and o.target_id == pair[1].target_id for o in state.recent_outcomes)
                return pair[0] - 0.3*repeats
            return max(candidates, key=value)
        coverage = dict(state.coverage)
        targets = operator.targets or operator.trigger_conditions
        dimension = next((d for d in targets if coverage.get(d) is CoverageLevel.NONE), targets[0] if targets else "correctness")
        return (0.6, QuestionTarget(TargetType.COMPONENT, f"{state.current_candidate_id}:{dimension}",
                                   f"The candidate's {dimension.replace('_', ' ')}", dimension))

    def rank(self, state, operators):
        ranked = []
        operator_stats, family_stats = dict(state.operator_statistics), dict(state.family_statistics)
        coverage = dict(state.coverage)
        for name, op in operators.items():
            issue_value, target = self.target(state, op)
            same = [o for o in state.recent_outcomes if o.operator == name and o.target_id == target.target_id and o.intent == op.purpose]
            # Candidate-scoped dimension targets retain intent across revisions, preventing
            # a new candidate ID from erasing repetition history for the same dimension.
            if target.target_type is TargetType.COMPONENT:
                same = [o for o in state.recent_outcomes if o.operator == name and o.target_id.endswith(":"+target.dimension)]
            stats, family = operator_stats.get(name), family_stats.get(op.family)
            mean_gain = ((stats.high_gain + 0.65*stats.medium_gain + 0.15*stats.low_gain) / stats.uses) if stats else 0.6
            family_gain = ((family.high_gain + 0.65*family.medium_gain + 0.15*family.low_gain) / family.uses) if family else 0.6
            information_gain = 0.35 + 0.45*mean_gain + 0.20*family_gain
            if (op.can_branch and op.family == "search" and not state.alternatives_considered
                    and dict(state.remaining_budget).get("operations", 0) >= 3):
                information_gain += 0.12  # Competing hypotheses can add information beyond another critique.
            uncovered = sum(coverage.get(d) is CoverageLevel.NONE for d in op.targets)
            relevance = min(1.3, 0.55 + 0.12*uncovered + (0.55 if target.target_type is not TargetType.COMPONENT else 0))
            novelty = (0.7 + 0.3*op.novelty_bias) / (1 + 0.5*len(same))
            low_repeats = sum(o.information_gain.level in ("LOW", "ZERO") for o in same)
            repetition = 0.18*len(same) + 0.25*low_repeats + 0.08*sum(o.information_gain.duplicates for o in same)
            # A useful family does not get a global prohibition on repeated use.
            if state.recent_outcomes and state.recent_outcomes[-1].operator == name:
                repetition += 0.06
            remaining = dict(state.remaining_budget).get("operations", 1)
            cost = op.cost*(0.35 if remaining <= 2 else 0.15)
            adjustment = dict(state.priority_adjustments).get(op.family, 0) + dict(state.priority_adjustments).get(name, 0)
            factors = UtilityFactors(relevance, information_gain, issue_value, novelty, IMPORTANCE[state.complexity],
                                     repetition, cost, adjustment)
            utility = relevance*information_gain*issue_value*novelty*factors.task_importance-repetition-cost+adjustment
            rationale = (f"Investigate {target.target_id} ({target.dimension}); expected gain {information_gain:.2f}, "
                         f"issue value {issue_value:.2f}, novelty {novelty:.2f}, repetition penalty {repetition:.2f}")
            ranked.append(OperatorUtility(name, round(utility, 6), factors, target, rationale))
        return tuple(sorted(ranked, key=lambda entry: (-entry.utility, entry.operator)))

    def choose(self, ranking, name=None):
        if not ranking:
            raise ValueError("Operator registry is empty")
        selected = next((r for r in ranking if r.operator == name), ranking[0])
        return UtilitySelection(selected.operator, selected.rationale, max(0, min(1, selected.utility)),
                                selected.utility, selected.scores, (selected.target.target_id,), selected.target, ranking)

    def select(self, state, operators):
        return self.choose(self.rank(state, operators))
