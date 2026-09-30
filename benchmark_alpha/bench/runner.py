"""Benchmark Alpha orchestration: executes (trial, task, condition) runs and stores one record per run.

Order: trial-major (every task gets trial 1 before any task gets trial 2), task order and condition order shuffled
per trial/task with random.Random seeded from the benchmark seed, so the order is reproducible and stored.
A run whose trial record already exists is skipped (resume); nothing already written is overwritten."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import time
import traceback

from .analysis import (candidate_progression, classify_calibration, delta_validation, operator_effects, overthinking,
                       rollback_value)
from .conditions import (CONDITIONS, EndSettings, load_trajectory, run_direct, run_end_lite, run_full_end,
                         run_self_reflect)
from .evaluators import evaluate
from .providers import CallLog

BENCHMARK = {"name": "END Engine Benchmark Alpha", "version": "alpha-1"}


def now():
    return datetime.now(timezone.utc).isoformat()


def load_tasks(directory):
    tasks = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(directory).glob("BA-*.json"))]
    return tasks


def task_set_hash(tasks):
    return hashlib.sha256(json.dumps(tasks, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def trial_seed(seed, task_id, trial):
    return int(hashlib.sha256(f"{seed}:{task_id}:{trial}".encode()).hexdigest()[:8], 16)


def execution_plan(tasks, trials, seed, conditions=CONDITIONS):
    plan = []
    for trial in range(1, trials + 1):
        order = [t["task_id"] for t in tasks]
        random.Random(f"{seed}|tasks|{trial}").shuffle(order)
        for task_id in order:
            conds = list(conditions)
            random.Random(f"{seed}|{task_id}|{trial}").shuffle(conds)
            plan += [{"trial": trial, "task_id": task_id, "condition": c, "position": i} for i, c in enumerate(conds)]
    return plan


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_one(task, trial, condition, model, log, out, end_settings):
    ledger = out / "trajectories"
    if condition == "DIRECT":
        return run_direct(task, model)
    if condition == "SELF_REFLECT":
        return run_self_reflect(task, model)
    if condition == "END_LITE":
        return run_end_lite(task, model, ledger, end_settings)
    return run_full_end(task, model, ledger, end_settings)


def evaluate_run(task, record, out):
    evaluation = {"run_id": record["run_id"], "final": evaluate(task, record["answer"]), "stages": {}, "candidates": {}}
    for stage in ("initial",):
        if stage in record["stages"]:
            evaluation["stages"][stage] = evaluate(task, record["stages"][stage])
    analysis = None
    end = record.get("end")
    if end:
        trajectory = load_trajectory(out / "trajectories", end["trajectory_file"])
        for c in trajectory["candidates"]:
            evaluation["candidates"][c["candidate_id"]] = evaluate(task, c["content"])
        scores = evaluation["candidates"]
        initial = next((e for e in record["calls"] if e["purpose"] == "initial_candidate" and e["status"] == "ok"), None)
        initial_tokens = None if initial is None or initial["input_tokens"] is None or initial["output_tokens"] is None \
            else initial["input_tokens"] + initial["output_tokens"]
        progression = candidate_progression(trajectory, scores, end["returned_candidate_id"])
        analysis = {"progression": progression,
                    "overthinking": overthinking(progression, end, record["cost"], initial_tokens),
                    "rollbacks": rollback_value(end, scores, end["returned_candidate_id"]),
                    "delta_validation": delta_validation(trajectory, scores),
                    "operator_effects": operator_effects(trajectory, scores),
                    "calibration": classify_calibration(record["condition"], end, evaluation["final"]["passed"]),
                    "best_internal_candidate_id": end["best_candidate_id"]}
    evaluation["analysis"] = analysis
    return evaluation


def reevaluate(out, tasks):
    """Recompute every derived evaluation from the stored trial records with the current evaluator version.
    Trial records and trajectories are only read; evaluations are derived data."""
    out = Path(out)
    by_id = {t["task_id"]: t for t in tasks}
    for path in sorted((out / "trials").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        write_json(out / "evaluations" / path.name, evaluate_run(by_id[record["task_id"]], record, out))


def run_benchmark(out, tasks, *, trials, seed, model_factory, model_record, data_origin, end_settings=None,
                  conditions=CONDITIONS, engine_identity=None, label=None, progress=print):
    """model_factory(log, trial_seed, task, condition, trial) -> ModelProvider writing every attempt to log."""
    out = Path(out)
    end_settings = end_settings or EndSettings()
    plan = execution_plan(tasks, trials, seed, conditions)
    by_id = {t["task_id"]: t for t in tasks}
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "benchmark": BENCHMARK, "label": label, "data_origin": data_origin, "engine": engine_identity,
        "python": {"version": platform.python_version(), "implementation": platform.python_implementation()},
        "model": model_record, "trials": trials, "conditions": list(conditions),
        "task_ids": [t["task_id"] for t in tasks], "task_set_hash": task_set_hash(tasks),
        "evaluation": {"primary": "deterministic external evaluators (benchmark_alpha/bench/evaluators.py)",
                       "model_judge": "not used for scoring (blinded judge infrastructure only)",
                       "analysis_thresholds": {"meaningful_score_delta": 0.1}},
        "end_settings": end_settings.describe(), "randomization_seed": seed,
        "planned_order": [f"{p['task_id']}.T{p['trial']}.{p['condition']}" for p in plan],
        "executed_order": [], "started_at": now(), "ended_at": None, "sessions": []}
    session = {"started_at": now(), "ended_at": None, "completed": 0, "skipped_existing": 0}
    manifest["sessions"].append(session)
    write_json(manifest_path, manifest)
    for step in plan:
        task = by_id[step["task_id"]]
        run_id = f"{step['task_id']}.T{step['trial']}.{step['condition']}"
        trial_path = out / "trials" / f"{run_id}.json"
        if trial_path.exists():
            session["skipped_existing"] += 1
            continue
        log = CallLog()
        seed_value = trial_seed(seed, task["task_id"], step["trial"])
        model = model_factory(log, seed_value, task, step["condition"], step["trial"])
        started, clock = now(), time.perf_counter()
        error = None
        try:
            output = run_one(task, step["trial"], step["condition"], model, log, out, end_settings)
        except Exception as exc:  # recorded as a failed run; never retried or repaired
            output = {"answer": "", "stages": {}}
            error = {"type": type(exc).__name__, "message": str(exc)[:500], "traceback": traceback.format_exc()[-2000:]}
        wall = round((time.perf_counter() - clock) * 1000, 3)
        cost = {**log.totals(), "wall_ms": wall, "tool_check_calls": 0,
                "end_cycles": (output.get("end") or {}).get("iterations"),
                "branch_count": (output.get("end") or {}).get("branch_count")}
        record = {"run_id": run_id, "trial_id": f"{task['task_id']}.T{step['trial']}", "task_id": task["task_id"],
                  "category": task["category"], "trial": step["trial"], "condition": step["condition"],
                  "position_in_trial": step["position"], "trial_seed": seed_value, "data_origin": data_origin,
                  "started_at": started, "ended_at": now(), "answer": output["answer"], "stages": output["stages"],
                  "end": output.get("end"), "error": error, "cost": cost, "calls": log.entries,
                  "model": model.metadata()}
        write_json(trial_path, record)
        write_json(out / "evaluations" / f"{run_id}.json", evaluate_run(task, record, out))
        manifest["executed_order"].append(run_id)
        session["completed"] += 1
        manifest["ended_at"] = session["ended_at"] = now()
        write_json(manifest_path, manifest)
        progress(f"{run_id}: wall {wall/1000:.1f}s calls {cost['calls']} tokens {cost['total_tokens']} "
                 f"error {error and error['type']}")
    session["ended_at"] = manifest["ended_at"] = now()
    write_json(manifest_path, manifest)
    return manifest
