from dataclasses import dataclass
from typing import Protocol

from .state import Candidate, Critique, Selection, VerificationResult, Weakness, WeaknessStatus, to_data
from ..models.base import ModelRequest
from ..models.schema import SELECTION, validate


@dataclass(frozen=True)
class SelectionContext:
    task: str
    candidate: Candidate
    previous_critiques: tuple[Critique, ...]
    unresolved_weaknesses: tuple[Weakness, ...]
    operators_used: tuple[str, ...]
    iteration: int
    remaining_budget: int
    dimensions: tuple[str, ...]
    target_cycles: int
    last_verification: VerificationResult | None = None
    cognitive_state: object | None = None


class QuestionSelector(Protocol):
    def select(self, context: SelectionContext, operators: dict, provider=None) -> Selection: ...


class AdaptiveQuestionSelector:
    def select(self, context, operators, provider=None):
        if context.cognitive_state is not None:
            from ..cognition.policy import UtilitySelectionPolicy
            return UtilitySelectionPolicy().select(context.cognitive_state, operators)
        if not operators:
            raise ValueError("Operator library must not be empty")
        ranked = []
        text = (context.task + " " + context.candidate.content).lower()
        for name, operator in operators.items():
            matches = set(operator.trigger_conditions) & set(context.dimensions)
            score = 0.10 + 0.08 * len(matches)
            reasons = [f"matches evaluation dimensions {', '.join(sorted(matches))}"] if matches else []
            for weakness in context.unresolved_weaknesses:
                if weakness.status is WeaknessStatus.OPEN and weakness.type in operator.trigger_conditions:
                    score += 0.42 if weakness.severity in ("high", "critical") else 0.24
                    reasons.append(f"addresses {weakness.id}: {weakness.description}")
            if name == "ASSUMPTION" and not context.previous_critiques:
                score += 0.35
                reasons.append("initial proposal has not had its assumptions inspected")
            if name == "EVIDENCE" and any(term in text for term in ("measured", "percent", "study", "%")):
                score += 0.22
                reasons.append("candidate or task includes empirical claims")
            if name == "CONSTRAINT" and any(term in text for term in ("must", "without", "bounded", "limit")):
                score += 0.15
                reasons.append("task or proposal contains explicit limits")
            if name == "VERIFY" and (context.remaining_budget <= 1 or context.iteration >= context.target_cycles):
                score += 0.28
                reasons.append("remaining budget favors checks of existing claims")
            if name == "VERIFY" and context.last_verification and context.last_verification.remaining_issues:
                score += 0.12
                reasons.append("last verification reports outstanding issues")
            count = context.operators_used.count(name)
            score -= 0.22 * count
            if context.operators_used and name == context.operators_used[-1]:
                score -= 0.45
            ranked.append((score, name, reasons))
        score, name, reasons = max(ranked, key=lambda item: (item[0], item[1]))
        return Selection(name, "; ".join(reasons) or "Inspect an under-examined dimension", max(0, min(1, score)))


class LLMQuestionSelector:
    def __init__(self):
        self.fallback = AdaptiveQuestionSelector()

    def select(self, context, operators, provider=None):
        if provider is None:
            raise ValueError("LLM selection requires a provider")
        schema = {**SELECTION, "properties": {**SELECTION["properties"],
                  "operator": {"type": "string", "enum": list(operators)}}}
        from ..cognition.policy import UtilitySelectionPolicy
        policy = UtilitySelectionPolicy()
        ranking = policy.rank(context.cognitive_state, operators) if context.cognitive_state is not None else ()
        compact_state = to_data(context.cognitive_state) if context.cognitive_state is not None else to_data(context)
        data = provider.generate_structured(ModelRequest(
            "selection", "Choose one operator based on candidate gaps, prior critiques, open weaknesses and budget. "
            "Avoid consecutive repetition unless a high-severity unresolved weakness requires it. "
            "Give a concise, evidence-based selection rationale.",
            {"state": compact_state, "utility_ranking": to_data(ranking),
             "operators": [to_data(op) for op in operators.values()]}, schema)).content
        validate(data, schema)
        selected = Selection(**data)
        if context.operators_used and selected.operator == context.operators_used[-1]:
            triggers = operators[selected.operator].trigger_conditions
            justified = any(w.severity in ("high", "critical") and w.type in triggers
                            for w in context.unresolved_weaknesses)
            if not justified:
                choice = self.fallback.select(context, operators)
                return Selection(choice.operator, "Repeat guard: " + choice.reason, choice.priority)
        return policy.choose(ranking, selected.operator) if ranking else selected
