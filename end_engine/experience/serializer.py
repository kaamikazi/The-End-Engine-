import json


def dumps(record: dict, *, pretty: bool = False) -> str:
    return json.dumps(record, ensure_ascii=False, allow_nan=False,
                      indent=2 if pretty else None, sort_keys=True)


def loads(text: str) -> dict:
    def invalid_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    value = json.loads(text, parse_constant=invalid_constant)
    if not isinstance(value, dict) or value.get("schema_version") not in ("1.0", "2.0", "3.0"):
        raise ValueError("Expected an END trajectory with schema_version 1.0, 2.0 or 3.0")
    required = {"trajectory_id", "task", "analysis", "configuration", "model", "steps",
                "candidates", "critiques", "revision_plans", "verification", "weaknesses",
                "model_calls", "errors", "termination", "final_result"}
    if not required <= value.keys():
        raise ValueError(f"Incomplete trajectory: missing {sorted(required - value.keys())}")
    if value["schema_version"] in ("2.0", "3.0"):
        cognitive = {"cognitive_states", "operator_utilities", "questions", "claims", "assumptions",
                     "operator_outcomes", "branches", "branch_evaluations", "synthesis_plans",
                     "cognitive_coverage", "meta_checks", "reframings"}
        if not cognitive <= value.keys():
            raise ValueError(f"Incomplete v0.2 trajectory: missing {sorted(cognitive - value.keys())}")
    if value["schema_version"] == "3.0":
        quality = {"judgments", "adversarial_judgments", "pairwise_comparisons", "quality_deltas",
                   "quality_gate_decisions", "fatal_issues", "disputes", "claim_validations", "assumption_audits",
                   "resolution_audits", "adversarial_tests", "verifier_evidence", "rollback_events",
                   "best_candidate_id", "latest_candidate_id", "acceptance_label", "transition_labels", "scorecard"}
        if not quality <= value.keys():
            raise ValueError(f"Incomplete v0.3 trajectory: missing {sorted(quality-value.keys())}")
    return value
