"""Summaries, failure archive, CSV and reports, rebuilt entirely from the stored trial and evaluation files."""
import csv
import io
import re
import json
from pathlib import Path
import shutil
import statistics

from .analysis import better, tags_for
from .conditions import CONDITIONS
from .evaluators import COUNTERS

PAIRS = (("FULL_END_NATIVE", "DIRECT"), ("FULL_END_STRUCTURED", "DIRECT"), ("END_LITE_NATIVE", "DIRECT"),
         ("FULL_END_NATIVE", "SELF_REFLECT"), ("FULL_END_STRUCTURED", "SELF_REFLECT"), ("END_LITE_NATIVE", "SELF_REFLECT"),
         ("FULL_END_NATIVE", "FULL_END_STRUCTURED"), ("FULL_END_NATIVE", "END_LITE_NATIVE"), ("SELF_REFLECT", "DIRECT"))
END_CONDITIONS = ("END_LITE_NATIVE", "FULL_END_NATIVE", "FULL_END_STRUCTURED")
GATED = ("FULL_END_NATIVE", "FULL_END_STRUCTURED")
ALPHA_SUMMARY = Path(__file__).resolve().parent.parent.parent / "benchmark_alpha" / "summary.json"


def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None, "stdev": None}
    return {"n": len(values), "mean": round(statistics.fmean(values), 4), "median": round(statistics.median(values), 4),
            "min": round(min(values), 4), "max": round(max(values), 4),
            "stdev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0}


def ratio(a, b):
    return None if a is None or b in (None, 0) else round(a / b, 3)


def load_runs(out):
    out = Path(out)
    runs = []
    for path in sorted((out / "trials").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        evaluation = json.loads((out / "evaluations" / path.name).read_text(encoding="utf-8"))
        runs.append((record, evaluation))
    return runs


def summarize(out):
    out = Path(out)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    runs = load_runs(out)
    peers = {}
    for record, evaluation in runs:
        peers.setdefault(record["trial_id"], {})[record["condition"]] = evaluation["final"]
    rows, tags_index = [], {}
    for record, evaluation in runs:
        tags = tags_for(record, evaluation, evaluation.get("analysis"), peers[record["trial_id"]])
        for tag in tags:
            tags_index.setdefault(tag, []).append(record["run_id"])
        final, end, cost, analysis = evaluation["final"], record.get("end") or {}, record["cost"], evaluation.get("analysis") or {}
        rows.append({"run_id": record["run_id"], "trial_id": record["trial_id"], "task_id": record["task_id"],
                     "category": record["category"], "trial": record["trial"], "condition": record["condition"],
                     "position_in_trial": record["position_in_trial"], "data_origin": record["data_origin"],
                     "passed": final["passed"], "score": final["score"], "format_ok": final["format_ok"],
                     **final["counters"],
                     "calls": cost["calls"], "failed_attempts": cost["failed_attempts"],
                     "prompt_tokens": cost["prompt_tokens"], "completion_tokens": cost["completion_tokens"],
                     "total_tokens": cost["total_tokens"], "wall_s": round(cost["wall_ms"] / 1000, 3),
                     "end_cycles": cost.get("end_cycles"), "branch_count": cost.get("branch_count"),
                     "complexity": end.get("complexity"), "termination": end.get("termination"),
                     "quality_gate": end.get("quality_gate"), "acceptance_label": end.get("acceptance_label"),
                     "returned_candidate": end.get("returned_candidate_id"), "best_internal": end.get("best_candidate_id"),
                     "latest_candidate": end.get("latest_candidate_id"),
                     "peak_candidate": (analysis.get("progression") or {}).get("peak_candidate_id"),
                     "calibration": (analysis.get("calibration") or {}).get("label"),
                     "overthinking": "|".join(analysis.get("overthinking") or []),
                     "rollbacks": "|".join(r["label"] for r in analysis.get("rollbacks") or []),
                     "end_errors": "|".join(e["message"][:80] for e in end.get("errors") or []),
                     "run_error": (record.get("error") or {}).get("type"), "tags": "|".join(tags),
                     "review_flags": len(final["review_flags"])})
    archive(out, runs, tags_index)
    summary = build_summary(manifest, rows, runs)
    summary["tags"] = {k: sorted(v) for k, v in sorted(tags_index.items())}
    text = json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    (out / "summary.json").write_text(text, encoding="utf-8")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]) if rows else ["run_id"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (out / "results.csv").write_text(buffer.getvalue(), encoding="utf-8")
    (out / "REPORT.md").write_text(render_report({**manifest, "_out": str(out)}, summary), encoding="utf-8")
    review = render_manual_review(manifest, summary, runs)
    if (out / "MANUAL_REVIEW_NOTES.md").exists():
        review += "\n" + (out / "MANUAL_REVIEW_NOTES.md").read_text(encoding="utf-8")
    (out / "MANUAL_REVIEW.md").write_text(review, encoding="utf-8")
    return summary


def archive(out, runs, tags_index):
    """Byte-identical copies of the original trial and evaluation records; trajectories are referenced by hash."""
    root = out / "failures"
    by_id = {r["run_id"]: r for r, _ in runs}
    for tag, run_ids in tags_index.items():
        for run_id in run_ids:
            target = root / tag / run_id
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(out / "trials" / f"{run_id}.json", target / "trial.json")
            shutil.copyfile(out / "evaluations" / f"{run_id}.json", target / "evaluation.json")
            end = by_id[run_id].get("end")
            reference = {"tag": tag, "run_id": run_id, "trial_record": f"trials/{run_id}.json",
                         "evaluation_record": f"evaluations/{run_id}.json",
                         "trajectory": end and {"trajectory_id": end["trajectory_id"],
                                                "file": f"trajectories/{end['trajectory_file']}",
                                                "sha256_at_run": end["trajectory_sha256"]},
                         "note": "Preserved as recorded. No cause is inferred automatically."}
            (target / "reference.json").write_text(json.dumps(reference, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def build_summary(manifest, rows, runs):
    conds = [c for c in CONDITIONS if any(r["condition"] == c for r in rows)]
    by_cond = {c: [r for r in rows if r["condition"] == c] for c in conds}
    overall = {}
    for c, rs in by_cond.items():
        overall[c] = {"runs": len(rs), "passed": sum(r["passed"] for r in rs),
                      "pass_rate": round(sum(r["passed"] for r in rs) / len(rs), 4) if rs else None,
                      "score": stats([r["score"] for r in rs]),
                      "hallucination_counters": {k: sum(r[k] for r in rs) for k in COUNTERS},
                      "tokens": stats([r["total_tokens"] for r in rs]),
                      "runs_with_unknown_tokens": sum(r["total_tokens"] is None for r in rs),
                      "calls": stats([r["calls"] for r in rs]), "wall_s": stats([r["wall_s"] for r in rs]),
                      "failed_attempts": sum(r["failed_attempts"] for r in rs),
                      "format_ok": sum(r["format_ok"] for r in rs),
                      "pass_rate_when_format_ok": (round(sum(r["passed"] for r in rs if r["format_ok"]) /
                                                         sum(r["format_ok"] for r in rs), 4)
                                                   if any(r["format_ok"] for r in rs) else None),
                      "run_errors": sum(r["run_error"] is not None for r in rs),
                      "end_external_blocker": sum(r["termination"] == "EXTERNAL_BLOCKER" for r in rs)}
    categories = sorted({r["category"] for r in rows})
    by_category = {cat: {c: {"runs": len(x), "pass_rate": round(sum(r["passed"] for r in x) / len(x), 4),
                             "mean_score": round(statistics.fmean(r["score"] for r in x), 4)}
                         for c in conds for x in [[r for r in by_cond[c] if r["category"] == cat]] if x}
                   for cat in categories}
    by_task = {t: {c: {"passed": f"{sum(r['passed'] for r in x)}/{len(x)}",
                       "scores": [r["score"] for r in sorted(x, key=lambda r: r["trial"])]}
                   for c in conds for x in [[r for r in by_cond[c] if r["task_id"] == t]] if x}
               for t in sorted({r["task_id"] for r in rows})}
    evaluations = {r["run_id"]: e for r, e in runs}
    index = {(r["trial_id"], r["condition"]): r for r in rows}
    pairwise = {}
    for a, b in PAIRS:
        if a not in by_cond or b not in by_cond:
            continue
        w = t = l = 0
        deltas, tok_a, tok_b, lat_a, lat_b = [], [], [], [], []
        for ra in by_cond[a]:
            rb = index.get((ra["trial_id"], b))
            if rb is None:
                continue
            fa, fb = evaluations[ra["run_id"]]["final"], evaluations[rb["run_id"]]["final"]
            w, t, l = (w + 1, t, l) if better(fa, fb) else (w, t, l + 1) if better(fb, fa) else (w, t + 1, l)
            deltas.append(fa["score"] - fb["score"])
            if ra["total_tokens"] is not None and rb["total_tokens"] is not None:
                tok_a.append(ra["total_tokens"]); tok_b.append(rb["total_tokens"])
            lat_a.append(ra["wall_s"]); lat_b.append(rb["wall_s"])
        pairwise[f"{a}_vs_{b}"] = {
            "matched_pairs": w + t + l, "wins": w, "ties": t, "losses": l,
            "external_score_delta_mean": round(statistics.fmean(deltas), 4) if deltas else None,
            "token_multiplier": ratio(sum(tok_a), sum(tok_b)) if tok_a else None, "token_pairs_known": len(tok_a),
            "latency_multiplier": ratio(sum(lat_a), sum(lat_b)) if lat_a else None,
            "unsupported_claims": {a: sum(index[(r["trial_id"], a)]["unsupported_claim_count"] for r in by_cond[b]
                                          if (r["trial_id"], a) in index),
                                   b: sum(r["unsupported_claim_count"] for r in by_cond[b] if (r["trial_id"], a) in index)},
            "false_accepts": {x: sum(r["calibration"] == "FALSE_ACCEPT" for r in by_cond[x]) for x in (a, b)}}
    calibration = {}
    for c in END_CONDITIONS:
        if c not in by_cond:
            continue
        counts = {k: sum(r["calibration"] == k for r in by_cond[c]) for k in
                  ("TRUE_ACCEPT", "FALSE_ACCEPT", "TRUE_REJECT", "FALSE_REJECT", "INCONCLUSIVE")}
        false_accepts = [{"run_id": r["run_id"], "quality_gate": r["quality_gate"], "acceptance_label": r["acceptance_label"],
                          "basis": evaluations[r["run_id"]]["analysis"]["calibration"]["basis"],
                          "returned": r["returned_candidate"], "external_score": r["score"],
                          "failed_checks": [ch["name"] for ch in evaluations[r["run_id"]]["final"]["checks"]
                                            if ch["required"] and ch["score"] < 1]}
                         for r in by_cond[c] if r["calibration"] == "FALSE_ACCEPT"]
        calibration[c] = {"basis": "QualityGate" if c in GATED else "LLM verifier (no gate in END_LITE_NATIVE)",
                          "counts": counts, "false_accepts": false_accepts}
    end_rows = [r for r in rows if r["condition"] in END_CONDITIONS]
    progression, overthinking_cases, rollbacks, deltas, ops = [], [], [], {}, {}
    for r in end_rows:
        analysis = evaluations[r["run_id"]]["analysis"]
        p = analysis["progression"]
        progression.append({"run_id": r["run_id"], "scores": p["candidate_scores"], "peak": p["peak_candidate_id"],
                            "returned": p["returned_candidate_id"], "best_internal": analysis["best_internal_candidate_id"],
                            "missed_peak": p["missed_peak"], "regressions": p["regressions"]})
        if analysis["overthinking"]:
            overthinking_cases.append({"run_id": r["run_id"], "signals": analysis["overthinking"],
                                       "tokens": r["total_tokens"], "cycles": r["end_cycles"]})
        rollbacks += [{"run_id": r["run_id"], **x} for x in analysis["rollbacks"]]
        for d in analysis["delta_validation"]:
            deltas.setdefault(r["condition"], {}).setdefault(d["label"], 0)
            deltas[r["condition"]][d["label"]] += 1
        for e in analysis["operator_effects"]:
            o = ops.setdefault(r["condition"], {}).setdefault(e["operator"], {"uses": 0, "positive": 0, "negative": 0,
                                                                              "neutral": 0, "no_revision": 0, "tokens": []})
            o["uses"] += 1
            o[e["effect"] or "no_revision"] += 1
            o["tokens"].append(e["cycle_tokens_recorded"])
    for cond in ops.values():
        for o in cond.values():
            o["mean_cycle_tokens_recorded"] = round(statistics.fmean(o.pop("tokens")), 1) if o["uses"] else None
    delta_list = [{"run_id": r["run_id"], **d} for r in end_rows for d in evaluations[r["run_id"]]["analysis"]["delta_validation"]]
    self_reflect = [{"run_id": r["run_id"], "initial": evaluations[r["run_id"]]["stages"]["initial"]["score"],
                     "final": r["score"]} for r in by_cond.get("SELF_REFLECT", []) if "initial" in evaluations[r["run_id"]]["stages"]]
    c0_vs_direct = []
    for r in end_rows:
        d = index.get((r["trial_id"], "DIRECT"))
        c0 = evaluations[r["run_id"]]["candidates"].get("C0")
        if d and c0:
            c0_vs_direct.append({"run_id": r["run_id"], "c0_score": c0["score"], "direct_score": d["score"]})
    terminations = {}
    for c in END_CONDITIONS:
        rs = [r for r, _ in runs if r["condition"] == c]
        if not rs:
            continue
        reasons, errors, gates = {}, {}, {}
        for r in rs:
            end = r.get("end") or {}
            reasons[end.get("termination")] = reasons.get(end.get("termination"), 0) + 1
            gates[end.get("quality_gate")] = gates.get(end.get("quality_gate"), 0) + 1
            for e in end.get("errors") or []:
                key = f"{e['stage']}: " + re.sub(r"\b(?:[CWA]\d+|CL\d+)\b", "<id>", e["message"])[:120]
                errors[key] = errors.get(key, 0) + 1
        terminations[c] = {"termination_reasons": reasons, "final_quality_gate": gates, "engine_errors": errors,
                           "mean_end_cycles": stats([(r.get("end") or {}).get("iterations") for r in rs])["mean"]}
    protocol = protocol_metrics(runs, evaluations)
    truncation = {c: sum(r["cost"].get("truncated_text_answers", 0) for r, _ in runs if r["condition"] == c) for c in conds}
    budget = {c: {"mean_calls": overall[c]["calls"]["mean"], "mean_tokens": overall[c]["tokens"]["mean"],
                  "mean_wall_s": overall[c]["wall_s"]["mean"], "pass_rate": overall[c]["pass_rate"],
                  "mean_score": overall[c]["score"]["mean"]} for c in conds}
    base = overall.get("DIRECT")
    for c in conds:
        if base:
            budget[c]["calls_x_direct"] = ratio(overall[c]["calls"]["mean"], base["calls"]["mean"])
            budget[c]["tokens_x_direct"] = ratio(overall[c]["tokens"]["mean"], base["tokens"]["mean"])
            budget[c]["latency_x_direct"] = ratio(overall[c]["wall_s"]["mean"], base["wall_s"]["mean"])
            budget[c]["score_minus_direct"] = (None if overall[c]["score"]["mean"] is None or base["score"]["mean"] is None
                                               else round(overall[c]["score"]["mean"] - base["score"]["mean"], 4))
    return {"benchmark": manifest["benchmark"], "label": manifest.get("label"), "data_origin": manifest["data_origin"],
            "engine": manifest.get("engine"), "model": manifest.get("model"), "task_set_hash": manifest["task_set_hash"],
            "runs": len(rows), "planned_runs": len(manifest["planned_order"]), "overall": overall,
            "by_category": by_category, "by_task": by_task,
            "task_categories": {r["task_id"]: r["category"] for r in rows}, "pairwise": pairwise, "calibration": calibration,
            "candidate_progression": progression, "overthinking": overthinking_cases, "rollbacks": rollbacks,
            "delta_validation": {"counts": deltas, "items": delta_list}, "operator_effects": ops,
            "self_reflect_initial_vs_final": self_reflect, "end_c0_vs_direct": c0_vs_direct, "cost_budget": budget,
            "end_terminations": terminations, "truncated_text_answers": truncation, "protocol_robustness": protocol,
            "alpha_comparison": alpha_comparison(overall, protocol),
            "run_notes": {k: manifest.get(k) for k in ("configuration_changes", "scope_decision",
                                                        "repository_events_during_run")},
            "review_flags": {r["run_id"]: evaluations[r["run_id"]]["final"]["review_flags"] for r in rows
                             if evaluations[r["run_id"]]["final"]["review_flags"]}}


def protocol_metrics(runs, evaluations):
    """v0.3.5 measures per END condition, from the stored trial records (which summarize each trajectory)."""
    out = {}
    for c in END_CONDITIONS:
        rs = [(r, evaluations[r["run_id"]]) for r, _ in runs if r["condition"] == c]
        if not rs:
            continue
        n = len(rs)
        ends = [r["end"] or {} for r, _ in rs]
        acts = [e.get("protocol_actions") or {} for e in ends]
        repaired_runs = [e for e, a in zip(ends, acts) if a.get("repair_requested")]
        failed = ("EXTERNAL_BLOCKER", "MODEL_PROTOCOL_FAILURE")
        groundings = {}
        for e in ends:
            for g in e.get("judge_groundings") or []:
                groundings[g["status"]] = groundings.get(g["status"], 0) + 1
        c0 = [ev["candidates"].get("C0") for _, ev in rs if ev["candidates"].get("C0")]
        transport = sum(1 for r, _ in rs for call in r["calls"] if call["attempt"] > 1)
        out[c] = {"runs": n, "candidate_generation": ends[0].get("candidate_generation"),
                  "external_blocker": sum(e.get("termination") == "EXTERNAL_BLOCKER" for e in ends),
                  "model_protocol_failure": sum(e.get("termination") == "MODEL_PROTOCOL_FAILURE" for e in ends),
                  "termination_categories": {k: sum(e.get("termination_category") == k for e in ends)
                                             for k in sorted({str(e.get("termination_category")) for e in ends})},
                  "repairs_attempted": sum(a.get("repair_requested", 0) for a in acts),
                  "repairs_succeeded": sum(a.get("repaired", 0) for a in acts),
                  "elements_discarded_events": sum(a.get(k, 0) for a in acts for k in (
                      "invalid_elements_discarded", "invalid_targets_discarded", "invalid_updates_rejected",
                      "synthesis_discarded", "branch_exploration_skipped")),
                  "repair_exhausted_events": sum(a.get("repair_exhausted", 0) for a in acts),
                  "runs_with_repair": len(repaired_runs),
                  "runs_continued_after_repair": sum(e.get("termination") not in failed for e in repaired_runs),
                  "transport_retries": transport,
                  "mean_end_cycles": stats([e.get("iterations") for e in ends])["mean"],
                  "pass_rate": round(sum(ev["final"]["passed"] for _, ev in rs) / n, 4),
                  "c0_score": stats([x["score"] for x in c0]),
                  "c0_format_ok": f"{sum(bool(x.get('format_ok')) for x in c0)}/{len(c0)}",
                  "final_format_ok": f"{sum(bool(ev['final'].get('format_ok')) for _, ev in rs)}/{n}",
                  "judge_groundings": groundings,
                  "engine_check_format_violations_C0": sum(bool((e.get("engine_checks") or [{}])[0].get("format_violations"))
                                                           for e in ends if e.get("engine_checks")),
                  "engine_check_internal_leakage_any": sum(any(c.get("internal_leakage") for c in e.get("engine_checks") or [])
                                                           for e in ends),
                  "engine_check_consensus_any": sum(any(c.get("consensus_as_confirmation") for c in e.get("engine_checks") or [])
                                                    for e in ends)}
    return out


def alpha_comparison(overall, protocol):
    """Historical v0.3.4 values from benchmark_alpha/summary.json (read only) next to Beta's measured values."""
    try:
        alpha = json.loads(ALPHA_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    a_full, a_lite = alpha["overall"].get("FULL_END", {}), alpha["overall"].get("END_LITE", {})
    a_term = alpha.get("end_terminations", {})
    c0 = alpha.get("end_c0_vs_direct", [])
    rows = {"FULL_END pass rate (Alpha v0.3.4)": f"{a_full.get('passed')}/{a_full.get('runs')}",
            "END_LITE pass rate (Alpha v0.3.4)": f"{a_lite.get('passed')}/{a_lite.get('runs')}",
            "FULL_END EXTERNAL_BLOCKER (Alpha)": f"{a_full.get('end_external_blocker')}/{a_full.get('runs')}",
            "END_LITE EXTERNAL_BLOCKER (Alpha)": f"{a_lite.get('end_external_blocker')}/{a_lite.get('runs')}",
            "FULL_END mean END cycles (Alpha)": (a_term.get("FULL_END") or {}).get("mean_end_cycles"),
            "END C0 mean external score (Alpha, both END conditions)":
                round(statistics.fmean(x["c0_score"] for x in c0), 4) if c0 else None,
            "DIRECT pass rate (Alpha)": f"{alpha['overall']['DIRECT']['passed']}/{alpha['overall']['DIRECT']['runs']}",
            "SELF_REFLECT pass rate (Alpha)":
                f"{alpha['overall']['SELF_REFLECT']['passed']}/{alpha['overall']['SELF_REFLECT']['runs']}"}
    beta = {c: {"pass": f"{overall[c]['passed']}/{overall[c]['runs']}", **({k: protocol[c][k] for k in
            ("external_blocker", "model_protocol_failure", "mean_end_cycles", "c0_score")} if c in protocol else {})}
            for c in overall}
    return {"source": "benchmark_alpha/summary.json (END v0.3.4; read only)", "alpha": rows, "beta": beta}


def _table(header, lines):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join("" if v is None else str(v) for v in line) + " |" for line in lines]
    return "\n".join(out)


def render_report(manifest, s):
    o, conds = s["overall"], list(s["overall"])
    hc = lambda c, k: o[c]["hallucination_counters"][k]
    synthetic = s["data_origin"] == "SYNTHETIC"
    banner = ("> **SYNTHETIC BENCHMARK INFRASTRUCTURE TEST.** Scripted model outputs validate the benchmark system. "
              "These numbers are NOT evidence about END or any model.\n\n" if synthetic else "")
    L = [f"# {s['benchmark']['name']} — {s['label'] or s['data_origin']}", "", banner.rstrip(), "",
         "## 1. Executive summary", "",
         "Generated from stored records. Measured values only; see §21–22 for limits.", ""]
    for c in conds:
        L.append(f"- {c}: passed {o[c]['passed']}/{o[c]['runs']} runs (pass rate {o[c]['pass_rate']}), mean external "
                 f"score {o[c]['score']['mean']}, mean tokens {o[c]['tokens']['mean']}, mean calls {o[c]['calls']['mean']}, "
                 f"mean wall {o[c]['wall_s']['mean']} s.")
    for k, v in s["pairwise"].items():
        L.append(f"- {k}: {v['wins']} wins / {v['ties']} ties / {v['losses']} losses over {v['matched_pairs']} matched "
                 f"task-trials; score delta {v['external_score_delta_mean']}; token ×{v['token_multiplier']}; latency ×{v['latency_multiplier']}.")
    for c, cal in s["calibration"].items():
        L.append(f"- {c} internal vs external ({cal['basis']}): {cal['counts']}.")
    scope = (s.get("run_notes") or {}).get("scope_decision")
    L.append(f"- Runs completed: {s['runs']} of {s['planned_runs']} planned"
             + (f" ({scope['decision']}; decided by {scope['by']})." if scope else "."))
    notes = Path(manifest.get("_out", "")) / "ANALYSIS_NOTES.md"
    if manifest.get("_out") and notes.exists():
        L += ["", notes.read_text(encoding="utf-8").strip()]
    L += ["", "## 2. Engine identity", "", "```json", json.dumps(s["engine"], indent=1), "```", "",
          "## 3. Model / provider identity", "", "```json", json.dumps(s["model"], indent=1), "```", "",
          "## 4. Methodology", "",
          f"- Trials per task: {manifest['trials']}; conditions: {', '.join(manifest['conditions'])}; randomization seed "
          f"{manifest['randomization_seed']} (trial-major; task order and condition order shuffled per trial; planned and "
          "executed order stored in manifest.json).",
          "- Every condition receives the task prompt verbatim. Hidden expectations are never sent to the model.",
          "- One run is one (task, trial, condition). Failures are recorded, never retried at run level and never repaired.",
          f"- Task set hash: `{s['task_set_hash']}`.",
          f"- Truncated text answers (text call reached the output cap; kept as the answer): {s['truncated_text_answers']}.",
          "- Configuration changes, scope decision and repository events during the run (from manifest.json):", "",
          "```json", json.dumps(s["run_notes"], indent=1), "```", "",
          "## 5. Task set", "", _table(["task", "category", "runs per condition"],
                                        [[t, s["task_categories"][t], len(next(iter(v.values()))["scores"])]
                                         for t, v in s["by_task"].items()]), "",
          "Task definitions (prompt, constraints, evaluation type, expected properties, failure conditions): `tasks/BA-*.json`.", "",
          "## 6. Conditions", "", "```json", json.dumps(manifest["end_settings"], indent=1), "```",
          "DIRECT: one text generation. SELF_REFLECT: answer → self-critique → one revision (three text generations).", "",
          "## 7. External evaluation methodology", "",
          "Deterministic evaluators only (executable unit tests in an isolated interpreter after an AST whitelist, known "
          "answers, a constraint validator, fixed-option structured rubrics, evidence-JSON validators with regex checks). "
          "No model judge contributes to any score. Hallucination counters cover only the designed failure classes. "
          "Answers with ambiguous wording are flagged for manual review (see summary.json `review_flags`).", "",
          "## 8. Overall results", "",
          _table(["Condition", "Pass rate", "Mean score (sd)", "Unsupported claims", "Mean tokens", "Mean calls", "Mean wall s",
                  "Run errors", "END EXTERNAL_BLOCKER"],
                 [[c, f"{o[c]['passed']}/{o[c]['runs']}", f"{o[c]['score']['mean']} ({o[c]['score']['stdev']})",
                   hc(c, "unsupported_claim_count"), o[c]["tokens"]["mean"], o[c]["calls"]["mean"], o[c]["wall_s"]["mean"],
                   o[c]["run_errors"], o[c]["end_external_blocker"]] for c in conds]), "",
          "Format compliance (diagnostic; does not change any score — the required answer structure is a hard "
          "requirement of every task):", "",
          _table(["Condition", "required structure present", "pass rate when present"],
                 [[c, f"{o[c]['format_ok']}/{o[c]['runs']}", o[c]["pass_rate_when_format_ok"]] for c in conds]), "",
          "Score distribution per condition (mean / median / min / max / sd):", "",
          _table(["Condition", "mean", "median", "min", "max", "sd"],
                 [[c, *(o[c]["score"][k] for k in ("mean", "median", "min", "max", "stdev"))] for c in conds]), "",
          "## 9. Results by task type", "",
          _table(["Category", *conds], [[cat, *(f"{v[c]['pass_rate']} / {v[c]['mean_score']}" if c in v else "" for c in conds)]
                                        for cat, v in s["by_category"].items()]),
          "", "(pass rate / mean score)", "",
          _table(["Task", *conds], [[t, *(f"{v[c]['passed']} {v[c]['scores']}" if c in v else "" for c in conds)]
                                    for t, v in s["by_task"].items()]), ""]
    for title, keys in (("10. DIRECT vs END", ("FULL_END_NATIVE_vs_DIRECT", "FULL_END_STRUCTURED_vs_DIRECT",
                                                "END_LITE_NATIVE_vs_DIRECT")),
                        ("11. SELF_REFLECT vs END", ("FULL_END_NATIVE_vs_SELF_REFLECT", "FULL_END_STRUCTURED_vs_SELF_REFLECT",
                                                     "END_LITE_NATIVE_vs_SELF_REFLECT", "SELF_REFLECT_vs_DIRECT")),
                        ("12. END variants: native vs structured C0, full vs lite", ("FULL_END_NATIVE_vs_FULL_END_STRUCTURED",
                                                                                     "FULL_END_NATIVE_vs_END_LITE_NATIVE"))):
        L += [f"## {title}", "", _table(["Comparison", "W/T/L", "Score delta", "Token ×", "Latency ×", "Unsupported claims",
                                         "False accepts"],
               [[k, f"{v['wins']}/{v['ties']}/{v['losses']}", v["external_score_delta_mean"], v["token_multiplier"],
                 v["latency_multiplier"], v["unsupported_claims"], v["false_accepts"]]
                for k in keys for v in [s["pairwise"].get(k)] if v]), ""]
    L += ["Wins/ties/losses use the meaningful-difference rule (|Δscore| ≥ 0.1 or pass/fail change).", "",
          "## 13. END INTERNAL QUALITY VS EXTERNAL RESULT", ""]
    for c, cal in s["calibration"].items():
        L += [f"**{c}** (internal basis: {cal['basis']})", "", _table(list(cal["counts"]), [list(cal["counts"].values())]), ""]
        if cal["false_accepts"]:
            L += ["Every FALSE_ACCEPT:", "", _table(["run", "gate", "label", "basis", "returned", "score", "failed checks"],
                  [[f["run_id"], f["quality_gate"], f["acceptance_label"], f["basis"], f["returned"], f["external_score"],
                    ", ".join(f["failed_checks"])] for f in cal["false_accepts"]]), ""]
    L += ["**How END runs ended** (termination reason, final gate, and Engine errors that stopped the loop; IDs normalized):", ""]
    for c, t in s["end_terminations"].items():
        L += [f"*{c}* — mean END cycles {t['mean_end_cycles']}", "",
              _table(["termination", "runs"], sorted(t["termination_reasons"].items(), key=lambda x: -x[1])), "",
              _table(["final quality_gate", "runs"], sorted(((str(k), v) for k, v in t["final_quality_gate"].items()),
                                                            key=lambda x: -x[1])), "",
              _table(["Engine error (stage: message)", "runs"], sorted(t["engine_errors"].items(), key=lambda x: -x[1]))
              if t["engine_errors"] else "No Engine errors.", ""]
    pr = s["protocol_robustness"]
    keys = ["candidate_generation", "external_blocker", "model_protocol_failure", "repairs_attempted", "repairs_succeeded",
            "elements_discarded_events", "repair_exhausted_events", "runs_with_repair", "runs_continued_after_repair",
            "transport_retries", "mean_end_cycles", "pass_rate", "c0_format_ok", "final_format_ok",
            "engine_check_internal_leakage_any", "engine_check_consensus_any"]
    L += ["## 13b. v0.3.5 PROTOCOL ROBUSTNESS AND GROUNDING", "",
          "Repairs are END protocol repairs (trajectory protocol_events). Transport retries are the benchmark transport's "
          "own single retry of a malformed structured response, counted separately.", "",
          _table(["measure", *pr], [[k, *(pr[c].get(k) for c in pr)] for k in keys]), "",
          "C0 external score by condition (generation mode in the table above):", "",
          _table(["condition", "C0 mean", "median", "min", "max", "n"],
                 [[c, *(pr[c]["c0_score"][k] for k in ("mean", "median", "min", "max", "n"))] for c in pr]), "",
          "Judge findings classified non-decisive by v0.3.5 grounding (counts by status):", "", "```json",
          json.dumps({c: pr[c]["judge_groundings"] for c in pr}, indent=1), "```", ""]
    ac = s.get("alpha_comparison")
    if ac:
        L += ["**Historical comparison with Benchmark Alpha (END v0.3.4, different session and seed; read only):**", "",
              _table(["Alpha (v0.3.4) measure", "value"], list(ac["alpha"].items())), "",
              _table(["Beta condition", "pass", "EXTERNAL_BLOCKER", "MODEL_PROTOCOL_FAILURE", "mean cycles", "C0 mean"],
                     [[c, v["pass"], v.get("external_blocker"), v.get("model_protocol_failure"), v.get("mean_end_cycles"),
                       (v.get("c0_score") or {}).get("mean")] for c, v in ac["beta"].items()]), ""]
    L += ["## 14. EPISTEMIC / HALLUCINATION RESULTS", "",
          "Counts over Benchmark Alpha tasks only; not universal hallucination rates.", "",
          _table(["Condition", *COUNTERS], [[c, *(hc(c, k) for k in COUNTERS)] for c in conds]), "",
          "## 15. Candidate progression", "",
          _table(["run", "external score per candidate", "peak", "returned", "best internal", "missed peak", "regressions"],
                 [[p["run_id"], " ".join(f"{k}:{v['score']}" for k, v in p["scores"].items()), p["peak"], p["returned"],
                   p["best_internal"], p["missed_peak"], len(p["regressions"])] for p in s["candidate_progression"]]), "",
          "## 16. Overthinking cases", "",
          _table(["run", "signals", "tokens", "END cycles"], [[x["run_id"], ", ".join(x["signals"]), x["tokens"], x["cycles"]]
                                                               for x in s["overthinking"]]) if s["overthinking"] else "None detected.", "",
          "## 17. Rollback analysis", "",
          _table(["run", "rejected", "returned", "rejected score", "returned score", "label"],
                 [[r["run_id"], r["rejected"], r["returned"], r["rejected_score"], r["returned_score"], r["label"]]
                  for r in s["rollbacks"]]) if s["rollbacks"] else "No rollback occurred.", "",
          "Quality-delta validation (END's comparator vs external delta):", "", "```json",
          json.dumps(s["delta_validation"]["counts"], indent=1), "```", "",
          "## 18. Operator observations", "", "Exploratory only; sample sizes are too small for causal claims.", ""]
    for c, ops in s["operator_effects"].items():
        L += [f"**{c}**", "", _table(["operator", "uses", "positive", "negative", "neutral", "no revision", "mean cycle tokens"],
              [[k, v["uses"], v["positive"], v["negative"], v["neutral"], v["no_revision"], v["mean_cycle_tokens_recorded"]]
               for k, v in sorted(ops.items())]), ""]
    b = s["cost_budget"]
    L += ["## 19. Cost / latency", "", "No provider pricing is configured: monetary cost = null.", "",
          _table(["Condition", "mean score", "Δscore vs DIRECT", "mean calls", "calls ×", "mean tokens", "tokens ×",
                  "mean wall s", "latency ×"],
                 [[c, b[c]["mean_score"], b[c].get("score_minus_direct"), b[c]["mean_calls"], b[c].get("calls_x_direct"),
                   b[c]["mean_tokens"], b[c].get("tokens_x_direct"), b[c]["mean_wall_s"], b[c].get("latency_x_direct")]
                  for c in b]), "",
          "**A. Unconstrained:** the table above (each condition's intended behaviour).", "",
          "**B. Roughly matched budget:** no budget-matched baseline condition was executed, so no matched-budget "
          "result exists. The multipliers above show how far apart the budgets are; the only near-matched view available is "
          "END's own first candidate C0 (one generation, like DIRECT) against DIRECT in the same task-trial:", "",
          f"END C0 vs DIRECT pairs: {len(s['end_c0_vs_direct'])}; mean C0 score "
          f"{round(statistics.fmean(x['c0_score'] for x in s['end_c0_vs_direct']), 4) if s['end_c0_vs_direct'] else None}, "
          f"mean DIRECT score {round(statistics.fmean(x['direct_score'] for x in s['end_c0_vs_direct']), 4) if s['end_c0_vs_direct'] else None}.", "",
          "## 20. Failure archive", "", "`failures/<TAG>/<run_id>/` holds byte-identical copies of the trial and evaluation "
          "records plus a trajectory reference with its SHA-256. No cause is inferred.", "",
          _table(["tag", "runs"], [[k, len(v)] for k, v in s["tags"].items()]), "",
          "## 21. Limitations", "",
          "- Benchmark Beta is small (12 tasks × 2 trials); far too small for statistical significance.",
          "- Results are specific to this model, these settings and this 12-task set.",
          "- Hallucination measurements cover only the designed failure classes, via task-specific patterns; they can miss or "
          "mis-flag wording (see review flags).",
          "- Model judges can be wrong; here END's internal judges are the same model as the generator.",
          "- Public benchmark contamination may exist for classic problems (e.g. meeting rooms, palindromes).",
          "- FULL_END conditions have no tool verifier and use a same-model judge, so they cannot reach ACCEPT_VERIFIED by design.",
          "- The transport retries a malformed structured response once (as in Alpha); after that, the failure is raised as "
          "a model-protocol error, so END v0.3.5 classifies it as MODEL_PROTOCOL_* and may make its own repair call.",
          "- Alpha numbers are historical (v0.3.4, earlier session, different seed); Alpha and Beta baselines are separate samples.",
          "", "## 22. What Benchmark Beta does NOT prove", "",
          "- A positive result does not prove general reasoning improvement.",
          "- A negative result does not prove END can never work.",
          "- No result here generalizes beyond this model, task set and configuration."]
    return "\n".join(L) + "\n"


def render_manual_review(manifest, s, runs):
    evaluations = {r["run_id"]: e for r, e in runs}
    records = {r["run_id"]: r for r, _ in runs}
    picks = []

    def add(reason, run_id):
        if run_id and run_id not in [p[1] for p in picks] and len(picks) < 10:
            picks.append((reason, run_id))
    end_runs = [r for r in records.values() if r["condition"] in END_CONDITIONS]

    def gain(r):
        c0 = evaluations[r["run_id"]]["candidates"].get("C0")
        return evaluations[r["run_id"]]["final"]["score"] - (c0["score"] if c0 else 0)
    if end_runs:
        best, worst = max(end_runs, key=gain), min(end_runs, key=gain)
        if gain(best) > 0:
            add("largest END improvement over its own C0", best["run_id"])
        if gain(worst) < 0:
            add("largest END regression from its own C0", worst["run_id"])
    for tag, reason in (("FALSE_ACCEPT", "QualityGate/verifier false accept"), ("ROLLBACK_SAVED_RUN", "rollback save"),
                        ("ROLLBACK_HURT_RUN", "rollback hurt"), ("DIRECT_BEAT_END", "direct beat END"),
                        ("OVERTHINKING", "overthinking"), ("CORRECT_ABSTENTION", "correct uncertainty"),
                        ("SCOPE_OVERREACH", "scope overreach"), ("FABRICATED_EVIDENCE", "fabricated evidence"),
                        ("END_HELPED", "END helped")):
        add(reason, (s["tags"].get(tag) or [None])[0])
    lines = [f"# Manual review set — {s['label'] or s['data_origin']}", "",
             "Selected automatically by the rules in `bench/report.py`; inspect the referenced files.", ""]
    if s["data_origin"] == "SYNTHETIC":
        lines += ["**SYNTHETIC BENCHMARK INFRASTRUCTURE TEST** — scripted outputs, not evidence.", ""]
    for reason, run_id in picks:
        r, e = records[run_id], evaluations[run_id]
        end = r.get("end") or {}
        lines += [f"## {run_id} — {reason}", "",
                  f"- condition {r['condition']}, external passed={e['final']['passed']} score={e['final']['score']}",
                  f"- END: gate={end.get('quality_gate')} label={end.get('acceptance_label')} termination={end.get('termination')} "
                  f"returned={end.get('returned_candidate_id')} trajectory=`trajectories/{end.get('trajectory_file')}`" if end else "- no END trajectory",
                  f"- files: `trials/{run_id}.json`, `evaluations/{run_id}.json`",
                  f"- failed checks: {[c['name'] for c in e['final']['checks'] if c['score'] < 1]}",
                  f"- review flags: {e['final']['review_flags']}", ""]
    return "\n".join(lines) + "\n"
