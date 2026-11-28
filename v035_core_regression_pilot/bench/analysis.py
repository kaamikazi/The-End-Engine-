"""Per-run analysis of END behaviour against EXTERNAL scores only. END's internal judgments are data, never truth.

Definitions (fixed before any live data was collected):
  meaningful difference  |external score delta| >= DELTA or a pass/fail change
  MISSED_PEAK            some candidate scored strictly higher than the returned candidate
  REGRESSION             a child candidate scored meaningfully lower than its parent
  OVERTHINKING (A)       an earlier candidate is meaningfully better than the returned one
  OVERTHINKING (B)       >= 1 END cycle, returned not meaningfully better than C0, and total tokens >= 3x the tokens
                         of the initial-candidate call (extra cost without external benefit)
  OVERTHINKING (C)       some candidate passed but the returned candidate fails
  ROLLBACK value         rejected latest candidate vs returned candidate, per rollback event
  Calibration            FULL_END: gate ACCEPT_* = accepted, REVISE/REJECT = rejected, BLOCKED = inconclusive.
                         END_LITE (no gate): returned candidate's LLM-verifier `passed` = accepted, else rejected;
                         no verifier result = inconclusive."""
DELTA = 0.1
IMPROVE = ("IMPROVEMENT", "STRONG_IMPROVEMENT")
REGRESS = ("REGRESSION", "SEVERE_REGRESSION")


def meaningful(a, b):
    """True when evaluation a differs meaningfully from evaluation b."""
    return abs(a["score"] - b["score"]) >= DELTA or a["passed"] != b["passed"]


def better(a, b):
    return meaningful(a, b) and (a["passed"], a["score"]) > (b["passed"], b["score"])


def classify_calibration(condition, end, external_passed):
    if condition in ("FULL_END_NATIVE", "FULL_END_STRUCTURED"):
        gate = end.get("quality_gate")
        internal = ("accepted" if gate in ("ACCEPT_VERIFIED", "ACCEPT_PROVISIONALLY") else
                    "rejected" if gate in ("REVISE", "REJECT") else "inconclusive")
        basis = f"quality_gate={gate}"
    else:
        verification = end.get("returned_verification")
        internal = "inconclusive" if verification is None else "accepted" if verification.get("passed") else "rejected"
        basis = f"llm_verifier_passed={None if verification is None else verification.get('passed')}"
    label = ("INCONCLUSIVE" if internal == "inconclusive" else
             ("TRUE_ACCEPT" if external_passed else "FALSE_ACCEPT") if internal == "accepted" else
             ("FALSE_REJECT" if external_passed else "TRUE_REJECT"))
    return {"internal": internal, "basis": basis, "external_passed": external_passed, "label": label}


def candidate_progression(trajectory, scores, returned_id):
    """scores: candidate_id -> external evaluation. Returns peak, regressions and overthinking signals."""
    order = [c["candidate_id"] for c in trajectory["candidates"]]
    parents = {c["candidate_id"]: c.get("parent_candidate_id") for c in trajectory["candidates"]}
    peak = max(order, key=lambda c: (scores[c]["passed"], scores[c]["score"], -order.index(c)))
    returned = scores[returned_id]
    regressions = [{"from": parents[c], "to": c, "from_score": scores[parents[c]]["score"], "to_score": scores[c]["score"]}
                   for c in order if parents[c] in scores and better(scores[parents[c]], scores[c])]
    earlier_better = [c for c in order[:order.index(returned_id)] if better(scores[c], returned)] if returned_id in order else []
    passed_before = [c for c in order if scores[c]["passed"]]
    return {"candidate_scores": {c: {"score": scores[c]["score"], "passed": scores[c]["passed"]} for c in order},
            "peak_candidate_id": peak, "returned_candidate_id": returned_id,
            "missed_peak": scores[peak]["score"] > returned["score"] or (scores[peak]["passed"] and not returned["passed"]),
            "regressions": regressions, "earlier_candidate_better": earlier_better,
            "correct_then_lost": bool(passed_before) and not returned["passed"]}


def overthinking(progression, end, cost, initial_call_tokens):
    signals = []
    if progression["earlier_candidate_better"]:
        signals.append("A_earlier_candidate_better")
    scores = progression["candidate_scores"]
    c0 = scores.get("C0")
    returned = scores[progression["returned_candidate_id"]]
    total = cost.get("total_tokens")
    if (end.get("iterations", 0) >= 1 and c0 is not None and not better(returned, c0) and total is not None
            and initial_call_tokens and total >= 3 * initial_call_tokens):
        signals.append("B_cycles_without_external_benefit")
    if progression["correct_then_lost"]:
        signals.append("C_correct_answer_lost")
    return signals


def rollback_value(end, scores, returned_id):
    out = []
    for event in end.get("rollback_events", []):
        rejected, returned = scores.get(event["from_candidate"]), scores.get(returned_id)
        if rejected is None or returned is None:
            label = "UNSCORED"
        elif better(returned, rejected):
            label = "ROLLBACK_SAVED_RUN"
        elif better(rejected, returned):
            label = "ROLLBACK_HURT_RUN"
        else:
            label = "ROLLBACK_NEUTRAL"
        out.append({"rejected": event["from_candidate"], "restored_to": event["to_candidate"], "returned": returned_id,
                    "rejected_score": rejected and rejected["score"], "returned_score": returned and returned["score"],
                    "label": label})
    return out


def delta_validation(trajectory, scores):
    out = []
    for item in trajectory.get("quality_deltas", []):
        a, b = scores.get(item["from_candidate"]), scores.get(item["to_candidate"])
        if a is None or b is None:
            continue
        predicted = item["net_assessment"]
        external = "IMPROVEMENT" if better(b, a) else "REGRESSION" if better(a, b) else "NO_MATERIAL_CHANGE"
        if predicted in IMPROVE:
            label = "MATCH" if external == "IMPROVEMENT" else "DELTA_MISMATCH" if external == "REGRESSION" else "PARTIAL_MISMATCH"
        elif predicted in REGRESS:
            label = "MATCH" if external == "REGRESSION" else "DELTA_MISMATCH" if external == "IMPROVEMENT" else "PARTIAL_MISMATCH"
        elif predicted == "NO_MATERIAL_CHANGE":
            label = "MATCH" if external == "NO_MATERIAL_CHANGE" else "PARTIAL_MISMATCH"
        else:
            label = "UNCLASSIFIED"
        out.append({"from": item["from_candidate"], "to": item["to_candidate"], "predicted": predicted,
                    "external": external, "external_delta": round(b["score"] - a["score"], 4), "label": label})
    return out


def operator_effects(trajectory, scores):
    steps = trajectory["steps"]
    out = []
    for i, step in enumerate(steps):
        if step["type"] != "critique":
            continue
        source = step["data"]["candidate_id"]
        selection = next((s["data"] for s in reversed(steps[:i]) if s["type"] == "operator_selection"), {})
        outcome = next((s["data"] for s in steps[i:] if s["type"] == "operator_outcome"), {})
        child = next((s for s in steps[i:] if s["type"] == "candidate" and s["data"].get("parent_candidate_id") == source), None)
        start = next((j for j in range(i, -1, -1) if steps[j]["type"] == "operator_selection"), i)
        stop = steps.index(child) if child else len(steps)
        tokens, missing = 0, 0
        for s in steps[start:stop]:
            if s["type"] == "model_call":
                usage = (s["data"].get("response") or {}).get("usage") if isinstance(s["data"].get("response"), dict) else None
                if usage and "input_tokens" in usage and "output_tokens" in usage:
                    tokens += usage["input_tokens"] + usage["output_tokens"]
                else:
                    missing += 1
        target = (selection.get("target") or {}).get("target_id") if isinstance(selection.get("target"), dict) else None
        before = scores.get(source)
        after = scores.get(child["data"]["candidate_id"]) if child else None
        effect = None if after is None or before is None else (
            "positive" if better(after, before) else "negative" if better(before, after) else "neutral")
        out.append({"operator": step["data"].get("operator"), "target": target, "on_candidate": source,
                    "information_gain": (outcome.get("information_gain") or {}).get("level"),
                    "revision_candidate": child["data"]["candidate_id"] if child else None,
                    "external_before": before and before["score"], "external_after": after and after["score"],
                    "effect": effect, "cycle_tokens_recorded": tokens, "cycle_calls_missing_usage": missing})
    return out


HALLUCINATION_TAGS = {"fabricated_reference_count": "FABRICATED_EVIDENCE", "scope_overreach_count": "SCOPE_OVERREACH",
                      "contradiction_ignored_count": "IGNORED_CONTRADICTION", "correct_uncertainty_count": "CORRECT_ABSTENTION",
                      "unsupported_high_impact_claim_count": "UNSUPPORTED_HIGH_IMPACT_CLAIM"}


def tags_for(record, evaluation, analysis, peers):
    """peers: condition -> final evaluation for the same task and trial."""
    tags = [tag for key, tag in HALLUCINATION_TAGS.items() if evaluation["final"]["counters"][key] > 0]
    if record["condition"] in ("END_LITE_NATIVE", "FULL_END_NATIVE", "FULL_END_STRUCTURED") and analysis:
        final = evaluation["final"]
        c0 = evaluation.get("candidates", {}).get("C0")
        if c0 is not None and better(final, c0):
            tags.append("END_HELPED")
        if c0 is not None and better(c0, final):
            tags.append("END_HURT")
        for other, tag in (("DIRECT", "DIRECT_BEAT_END"), ("SELF_REFLECT", "SELF_REFLECT_BEAT_END")):
            if other in peers and better(peers[other], final):
                tags.append(tag)
        label = (analysis.get("calibration") or {}).get("label")
        if label in ("FALSE_ACCEPT", "FALSE_REJECT"):
            tags.append(label)
        if analysis.get("overthinking"):
            tags.append("OVERTHINKING")
        tags += [r["label"] for r in analysis.get("rollbacks", []) if r["label"] in ("ROLLBACK_SAVED_RUN", "ROLLBACK_HURT_RUN")]
    return sorted(set(tags))
