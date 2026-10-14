from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import replace

from .types import (ChoiceDecision, DecisionProvenance, DecisionResult, DecisionStatus, result_from_data)


class DecisionProvider(ABC):
    def budget_cost(self, request):
        return 1
    def availability(self):
        """Local preflight only: no inference or network request."""
        return "available", None

    def for_run(self):
        return self

    @abstractmethod
    def evaluate(self, request) -> DecisionResult: ...


class DeterministicDecisionProvider(DecisionProvider):
    def evaluate(self, request):
        if request.question_type != "choice":
            return DecisionResult(request.question_id, request.question_type, DecisionStatus.UNAVAILABLE,
                DecisionProvenance("deterministic"), failure_reason="unsupported_primitive")
        scores = request.context.get("family_utility", {})
        selected = max(request.choices, key=lambda c: (scores.get(c, 0), c))
        return DecisionResult(request.question_id, "choice", DecisionStatus.SUCCESS,
            DecisionProvenance("deterministic"), ChoiceDecision(selected,
                tuple((choice, 1.0 if choice == selected else 0.0) for choice in request.choices), 1.0))


class ScriptedDecisionProvider(DecisionProvider):
    """Offline fixture. Reset cursors across runs; callbacks see only the projection."""
    def __init__(self, responses=(), *, available=True):
        self.responses, self.available, self.index = tuple(responses), available, 0

    def for_run(self):
        return ScriptedDecisionProvider(self.responses, available=self.available)

    def availability(self):
        return ("available", None) if self.available else ("unavailable", "fixture_unavailable")

    def evaluate(self, request):
        if self.index >= len(self.responses):
            return DecisionResult(request.question_id, request.question_type, DecisionStatus.UNAVAILABLE,
                DecisionProvenance("scripted"), failure_reason="script_exhausted")
        value = self.responses[self.index]
        self.index += 1
        if isinstance(value, Exception): raise value
        return value(request) if callable(value) else deepcopy(value)


class ReplayDecisionProvider(DecisionProvider):
    """No live fallback transport exists. Missing/mismatched records stay explicit."""
    def __init__(self, records):
        self.records, self.index = deepcopy(tuple(records)), 0

    @classmethod
    def from_trajectory(cls, trajectory):
        return cls(trajectory.get("decisions", ()))

    def for_run(self):
        return ReplayDecisionProvider(self.records)

    def budget_cost(self, request):
        if self.index >= len(self.records) or self.records[self.index].get("request_fingerprint") != request.fingerprint:
            return 0
        return int(self.records[self.index].get("budget_consumed", 0))

    def evaluate(self, request):
        if self.index >= len(self.records):
            return DecisionResult(request.question_id, request.question_type, DecisionStatus.UNAVAILABLE,
                DecisionProvenance("replay", availability="missing", replayed=True), failure_reason="replay_missing")
        record = self.records[self.index]
        self.index += 1
        if record.get("request_fingerprint") != request.fingerprint:
            return DecisionResult(request.question_id, request.question_type, DecisionStatus.UNAVAILABLE,
                DecisionProvenance("replay", availability="mismatch", replayed=True), failure_reason="replay_input_mismatch")
        result = result_from_data(record["result"])
        return replace(result, provenance=replace(result.provenance, replayed=True))
