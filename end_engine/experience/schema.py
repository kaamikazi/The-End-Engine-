from copy import deepcopy
from uuid import uuid4

from ..core.state import now, to_data
from ..models.budget import RunCallBudget


class Trajectory:
    """Run-local event recorder. Public reads and recorded values are detached copies."""

    def __init__(self, task, configuration, model):
        self._call_counter = 0
        self.call_budget = None
        self._data = {
            "schema_version": "2.0", "trajectory_id": str(uuid4()),
            "task": {"content": task}, "configuration": deepcopy(configuration),
            "model": deepcopy(model), "created_at": now(), "completed_at": None,
            "analysis": None, "steps": [], "candidates": [], "critiques": [],
            "revision_plans": [], "verification": [], "weaknesses": [],
            "model_calls": [], "tool_calls": [], "errors": [],
            "final_candidate_id": None, "final_result": None, "termination": None,
            "usage": {"totals": {}, "reported_calls": 0, "unreported_calls": 0},
            "latency_ms": None,
            "cognitive_states": [], "operator_utilities": [], "questions": [],
            "claims": [], "assumptions": [], "operator_outcomes": [], "operator_statistics": {},
            "branches": [], "branch_evaluations": [], "synthesis_plans": [],
            "cognitive_coverage": {}, "meta_checks": [], "reframings": [],
            "judgments": [], "adversarial_judgments": [], "pairwise_comparisons": [], "quality_deltas": [],
            "quality_gate_decisions": [], "fatal_issues": [], "disputes": [], "claim_validations": [],
            "resolution_audits": [], "assumption_audits": [], "adversarial_tests": [], "verifier_evidence": [],
            "rollback_events": [], "judge_feedback": [], "gaming_signals": [], "trajectory_judgments": [],
            "transition_labels": [], "evidence_integrity": [],
            "protocol_events": [], "judge_groundings": [], "engine_checks": [], "best_candidate_id": None, "latest_candidate_id": None,
            "repair_outcomes": [], "epistemic_checks": [], "cycle_progress": [],
            "repair_statistics": {}, "no_progress_cycles": 0, "no_progress_stop": False,
            "assessment_findings": [], "revision_evidence_deltas": [],
            "acceptance_label": "INCOMPLETE", "scorecard": None,
        }

    @property
    def id(self):
        return self._data["trajectory_id"]

    def next_call_id(self):
        identity = f"M{self._call_counter}"
        self._call_counter += 1
        return identity

    def configure_call_budget(self, limit):
        self.call_budget = RunCallBudget(limit)
        self.set("run_call_budget", self.call_budget.snapshot())

    def reserve_call(self, kind):
        if self.call_budget is None:
            return
        try:
            self.call_budget.reserve(kind)
        finally:
            self.set("run_call_budget", self.call_budget.snapshot())

    def set(self, key, value):
        self._data[key] = deepcopy(to_data(value))

    def record(self, kind, payload, collection=None):
        payload = deepcopy(to_data(payload))
        self._data["steps"].append({"step": len(self._data["steps"]), "type": kind,
                                    "timestamp": now(), "data": payload})
        if collection:
            self._data[collection].append(deepcopy(payload))

    def snapshot(self):
        return deepcopy(self._data)

    def aggregate_usage(self):
        totals, reported, unreported = {}, 0, 0
        for call in self._data["model_calls"]:
            usage = (call.get("response") or {}).get("usage")
            if usage is None:
                unreported += 1
            else:
                reported += 1
                for key, value in usage.items():
                    if type(value) is int and value >= 0:
                        totals[key] = totals.get(key, 0) + value
        self.set("usage", {"totals": totals, "reported_calls": reported, "unreported_calls": unreported})
