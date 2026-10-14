from dataclasses import dataclass, replace
from time import perf_counter

from ..cognition.policy import UtilitySelectionPolicy
from ..core.state import now, to_data
from ..models.budget import RunBudgetExceeded
from .context import DecisionContextBuilder, redact
from .types import ChoiceDecision, DecisionRequest, DecisionResult, DecisionProvenance, DecisionStatus, validate_result


@dataclass(frozen=True)
class RoutingConstraints:
    """END-owned constraints. The provider has no API for modifying them."""
    forbidden_operators: tuple[str, ...] = ()
    allowed_operators: tuple[str, ...] | None = None
    mandatory_operator: str | None = None
    allowed_modes: tuple[str, ...] = ("normal", "deep", "critical")


class DecisionRoutingSession:
    def __init__(self, config, provider, trajectory, constraints=None):
        self.config, self.provider, self.trajectory = config, provider.for_run(), trajectory
        self.constraints = constraints if constraints is not None else RoutingConstraints()
        self.context_builder, self.utility = DecisionContextBuilder(), UtilitySelectionPolicy()
        self.calls, self.latency_ms, self.attempts, self.fallbacks, self.rejected = 0, 0.0, 0, 0, 0
        self.requests, self.ignored = 0, 0
        self.trajectory.set("decisions", [])
        self._summary()

    def _summary(self):
        self.trajectory.set("decision_summary", {"opportunities":self.attempts,"requests":self.requests,
            "calls":self.calls,"latency_ms":self.latency_ms,"fallbacks":self.fallbacks,"rejected":self.rejected,"ignored":self.ignored})

    def _ignore(self, reason, selected):
        self.ignored += 1
        self.trajectory.record("decision.ignored", {"reason":reason,"operator":selected.operator})
        self._summary()
        return selected

    def _allowed(self, state, operators, baseline):
        ranking = baseline.ranking if hasattr(baseline, "ranking") else self.utility.rank(state, operators)
        allow = self.constraints.allowed_operators
        eligible = tuple(r for r in ranking if r.operator in operators and r.operator not in self.constraints.forbidden_operators
                         and (allow is None or r.operator in allow))
        if not eligible:
            raise ValueError("END routing policy permits no available operator")
        return eligible

    def select(self, state, operators, baseline, *, authoritative=False):
        self.attempts += 1
        eligible = self._allowed(state, operators, baseline)
        fallback = baseline if baseline.operator in {r.operator for r in eligible} else self.utility.choose(eligible)
        mandatory = self.constraints.mandatory_operator
        if mandatory is not None:
            if mandatory not in {r.operator for r in eligible}:
                raise ValueError("Mandatory operator is unavailable or forbidden")
            return self._ignore("mandatory_operator",self.utility.choose(eligible,mandatory))
        if authoritative or state.complexity not in self.constraints.allowed_modes or "operator_routing" not in self.config.categories:
            return self._ignore("authoritative_policy_or_mode",fallback)
        # Only near-best operators respecting repetition may receive a model recommendation.
        permitted = tuple(r for r in eligible if r.utility >= eligible[0].utility-self.config.max_utility_loss
                          and r.scores.repetition_penalty <= self.config.max_repetition_penalty)
        if not permitted:
            return self._ignore("repetition_policy",fallback)
        families = tuple(sorted({operators[r.operator].family for r in permitted}))
        if len(families) == 1:
            return self._ignore("single_eligible_family",fallback)
        request = DecisionRequest(f"D{self.attempts:03d}", "choice",
            "Which available operator family is most useful for the unresolved issues in this bounded state? Choose one offered family.",
            self.context_builder.build(state, permitted, operators, remaining_calls=max(0,self.config.max_calls_per_run-self.calls)),
            choices=families, requested_model=self.config.requested_model,
            timeout_seconds=min(self.config.timeout_seconds,max(.001,(self.config.max_latency_ms-self.latency_ms)/1000)))
        self.requests += 1
        self.trajectory.record("decision.requested", {"policy": "bounded_operator_family_routing", "request": request,
            "request_fingerprint": request.fingerprint, "baseline_operator": fallback.operator})
        start = perf_counter()
        call_id = None
        result = None
        exhausted = (self.calls >= self.config.max_calls_per_run or self.latency_ms >= self.config.max_latency_ms
                     or dict(state.remaining_budget).get("operations", 0) <= 0 or
                     self.trajectory.call_budget is not None and self.trajectory.call_budget.remaining <= 4)
        if exhausted:
            result = DecisionResult(request.question_id, "choice", DecisionStatus.EXHAUSTED,
                DecisionProvenance("END_policy", request.requested_model), failure_reason="decision_or_shared_budget_exhausted")
            self.trajectory.record("decision.budget_exhausted", {"question_id": request.question_id})
        else:
            try:
                availability, reason = self.provider.availability()
                if availability != "available":
                    result = DecisionResult(request.question_id, "choice", DecisionStatus.UNAVAILABLE,
                        DecisionProvenance("decision_provider", request.requested_model, availability=availability), failure_reason=reason)
                else:
                    cost = self.provider.budget_cost(request) if hasattr(self.provider, "budget_cost") else 1
                    if cost not in (0,1) or type(cost) is not int:
                        raise ValueError("Decision budget cost must be 0 or 1")
                    if cost:
                        call_id = self.trajectory.next_call_id()
                        self.trajectory.reserve_call("decision")
                        self.calls += 1
                    result = self.provider.evaluate(request)
                    validate_result(result, request)
            except Exception as exc:
                state_code = (DecisionStatus.EXHAUSTED if isinstance(exc, RunBudgetExceeded) else
                              DecisionStatus.TIMEOUT if isinstance(exc, TimeoutError) else
                              DecisionStatus.MALFORMED if isinstance(exc, (ValueError, TypeError, AttributeError)) else DecisionStatus.PROVIDER_ERROR)
                result = DecisionResult(request.question_id, "choice", state_code,
                    DecisionProvenance("decision_provider", request.requested_model, error_type=type(exc).__name__), failure_reason=state_code.value)
                self.trajectory.record("decision.error", {"question_id": request.question_id, "status": state_code,
                                                           "error_type": type(exc).__name__})
        elapsed = round((perf_counter()-start)*1000,3)
        self.latency_ms += elapsed
        if call_id:
            self.trajectory.record("model_call", {"call_id": call_id, "started_at": now(), "completed_at": now(),
                "method": "evaluate_decision", "model": {"provider": result.provenance.provider,
                "requested_model": result.provenance.requested_model, "resolved_model": result.provenance.resolved_model},
                "request": to_data(request), "response": {"content": result.as_dict(), "usage": dict(result.provenance.usage) or None},
                "latency_ms": elapsed, "error": None if result.status is DecisionStatus.SUCCESS else {"type": result.status.value},
                "replayed": result.provenance.replayed}, "model_calls")
        selected, disposition, rule = fallback, "fallback", result.failure_reason or result.status.value
        if result.status is DecisionStatus.SUCCESS:
            value = result.value
            probabilities = dict(value.choice_probabilities)
            if (value.selected_choice not in families or set(probabilities) != set(families)):
                disposition, rule = "rejected_by_policy", "choice_not_available"
            elif (probabilities[value.selected_choice] < self.config.min_choice_probability or
                  value.choice_confidence is None or value.choice_confidence < self.config.min_choice_confidence):
                disposition, rule = "ignored_low_certainty", "choice_probability_or_native_confidence_below_threshold"
            elif self.latency_ms > self.config.max_latency_ms:
                disposition, rule = "rejected_by_policy", "latency_budget_exceeded"
            else:
                winners = tuple(r for r in permitted if operators[r.operator].family == value.selected_choice)
                # Recheck availability/constraints after the call, not only before requesting it.
                winners = tuple(r for r in winners if r.operator in operators and r.operator not in self.constraints.forbidden_operators)
                if winners:
                    selected, disposition, rule = self.utility.choose(eligible, winners[0].operator), "accepted", "END_policy_validated"
                else:
                    disposition, rule = "rejected_by_policy", "operator_no_longer_available"
        if disposition != "accepted":
            self.fallbacks += 1
            if disposition == "rejected_by_policy": self.rejected += 1
            self.trajectory.record("decision.rejected" if disposition == "rejected_by_policy" else "decision.fallback",
                {"question_id": request.question_id, "disposition": disposition, "rule": rule, "operator": selected.operator})
        trace = {"policy": "bounded_operator_family_routing", "request": to_data(request), "request_fingerprint": request.fingerprint,
            "result": result.as_dict(), "disposition": disposition, "rule": rule, "selected_operator": selected.operator,
            "fallback_operator": fallback.operator, "thresholds": {"choice_probability": self.config.min_choice_probability,
                "choice_confidence": self.config.min_choice_confidence}, "budget_consumed": int(call_id is not None),
            "latency_ms": elapsed}
        self.trajectory.record("decision.completed", trace, "decisions")
        self._summary()
        return selected
