"""Benchmark Beta-Gemini command line (END v0.3.5, gemini-3.8-flash via the Gemini Developer API).

  python -B -m bench.cli baseline                 write ENGINE_BASELINE.json (runs nothing else)
  python -B -m bench.cli synthetic OUT            SYNTHETIC BENCHMARK INFRASTRUCTURE TEST into OUT
  python -B -m bench.cli preflight                write PREFLIGHT.json (identity, hashes, matrix; no network) and print it
  python -B -m bench.cli probe                    ONE tiny Gemini request (connectivity, modelVersion); writes PROBE.json
  python -B -m bench.cli live OUT --trials 2      the 120-run benchmark (only after explicit approval)
The API key is read from the GEMINI_API_KEY environment variable and is never written anywhere.
  python -B -m bench.cli summarize OUT            rebuild summary/CSV/reports from stored records
Run from benchmark_beta/ with the Engine repository on sys.path (added automatically)."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent.parent          # benchmark_beta/
ENGINE = HERE.parent                                    # repository root
sys.path.insert(0, str(ENGINE))

from .conditions import EndSettings  # noqa: E402
from .providers import ModelSettings, OllamaModel, discover  # noqa: E402
from .gemini import KEY_ENV, GeminiModel, GeminiSettings, probe  # noqa: E402
from .report import summarize  # noqa: E402
from .runner import load_tasks, reevaluate, run_benchmark, task_set_hash  # noqa: E402
from . import synthetic  # noqa: E402

SEED = 20261103  # Beta-Gemini's own randomization seed (Alpha 20261001, local-Qwen Beta attempt 20261102)
ALPHA = ENGINE / "benchmark_alpha"
ALPHA_TASK_SET_HASH = "9e177f6d6be25acf82010d898e42a86c7a4d516af882eaa1725bcb5efe468ca6"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def engine_identity(root=ENGINE):
    """Same algorithm as the Harness's controlled load: SHA-256 over end_engine/**/*.py and pyproject.toml."""
    import tomllib
    manifest = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((root / "end_engine").rglob("*.py"))}
    project = (root / "pyproject.toml").read_bytes()
    manifest["pyproject.toml"] = hashlib.sha256(project).hexdigest()
    return {"version": tomllib.loads(project.decode("utf-8"))["project"]["version"],
            "source_sha256": hashlib.sha256(canonical(manifest)).hexdigest(),
            "fingerprint_scope": "end_engine/**/*.py and pyproject.toml", "files": len(manifest), "git_commit": None,
            "git_status": "not a git repository"}


def preflight(tasks, trials=2):
    """Read-only checks before the live run; writes PREFLIGHT.json into benchmark_beta/."""
    from .conditions import CONDITIONS
    from .runner import execution_plan
    import os
    from dataclasses import asdict
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    engine = engine_identity()
    settings = GeminiSettings()
    plan = execution_plan(tasks, trials, SEED)
    checks = {
        "engine_version_is_0.3.5": engine["version"] == "0.3.5",
        "task_set_hash_matches_alpha": task_set_hash(tasks) == ALPHA_TASK_SET_HASH,
        "task_files_identical_to_alpha": all(sha(p) == sha(ALPHA / "tasks" / p.name) for p in sorted((HERE / "tasks").glob("BA-*.json"))),
        "evaluators_identical_to_alpha": sha(HERE / "bench" / "evaluators.py") == sha(ALPHA / "bench" / "evaluators.py"),
        "api_key_env_present": bool(os.environ.get(KEY_ENV)),
        "planned_runs_120": len(plan) == 120 and len({(p["trial"], p["task_id"], p["condition"]) for p in plan}) == 120,
    }
    result = {"engine": engine, "model": settings.model, "seed": SEED, "trials": trials, "conditions": list(CONDITIONS),
              "tasks": [t["task_id"] for t in tasks], "task_set_hash": task_set_hash(tasks),
              "evaluators_sha256": sha(HERE / "bench" / "evaluators.py"), "settings": asdict(settings),
              "planned_runs": len(plan), "checks": checks, "all_checks_pass": all(checks.values()),
              "matrix": {t["task_id"]: {f"T{n}": [p["condition"] for p in plan if p["task_id"] == t["task_id"] and p["trial"] == n]
                                        for n in range(1, trials + 1)} for t in tasks}}
    (HERE / "PREFLIGHT.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline")
    s = sub.add_parser("synthetic"); s.add_argument("out")
    live = sub.add_parser("live"); live.add_argument("out"); live.add_argument("--model", default="qwen3:4b")
    live.add_argument("--trials", type=int, default=2); live.add_argument("--full-max-cycles", type=int, default=None)
    sub.add_parser("preflight")
    sub.add_parser("probe")
    live.add_argument("--tasks", nargs="*", default=None)
    m = sub.add_parser("summarize"); m.add_argument("out")
    args = parser.parse_args(argv)
    tasks = load_tasks(HERE / "tasks")
    if args.command == "baseline":
        print(json.dumps(engine_identity(), indent=1))
    elif args.command == "preflight":
        print(json.dumps(preflight(tasks), indent=1))
    elif args.command == "probe":
        import os
        result = probe(GeminiSettings())
        result["api_key_env"] = KEY_ENV
        result["api_key_present"] = bool(os.environ.get(KEY_ENV))
        (HERE / "PROBE.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=1))
    elif args.command == "synthetic":
        chosen = [t for t in tasks if t["task_id"] in synthetic.SCENARIOS]
        run_benchmark(args.out, chosen, trials=1, seed=SEED, model_factory=synthetic.factory(),
                      model_record={"provider": "synthetic-scripted", "model": "synthetic-fixture",
                                    "settings": None, "label": synthetic.LABEL},
                      data_origin="SYNTHETIC", engine_identity=engine_identity(), label=synthetic.LABEL)
        summarize(args.out)
    elif args.command == "live":
        if sys.platform == "win32":  # per-process "system required" request; released when this process exits
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
        from dataclasses import asdict
        settings = GeminiSettings()
        probe_record = json.loads((HERE / "PROBE.json").read_text(encoding="utf-8"))
        if probe_record.get("status") != "ok":
            raise SystemExit("Run `probe` successfully before the live benchmark")
        chosen = [t for t in tasks if not args.tasks or t["task_id"] in args.tasks]
        record = {"provider": settings.provider, "model": settings.model,
                  "model_version_at_probe": probe_record.get("model_version"),
                  "settings": {**asdict(settings), "tools": None, "grounding": None, "code_execution": None,
                               "seed": "not sent (unsupported/unused)", "context_window": "provider default"},
                  "api_key": f"read from {KEY_ENV} at request time; never recorded", "same_model_all_conditions": True}

        def factory(log, trial_seed, task, condition, trial):
            return GeminiModel(settings, log, trial_seed=trial_seed)
        run_benchmark(args.out, chosen, trials=args.trials, seed=SEED, model_factory=factory, model_record=record,
                      data_origin="LIVE_GEMINI_API", end_settings=EndSettings(full_max_cycles=args.full_max_cycles),
                      engine_identity=engine_identity(), label="Benchmark Beta-Gemini live run (END v0.3.5, gemini-3.8-flash)",
                      progress=lambda m: print(m, flush=True))
        reevaluate(args.out, tasks)
        summarize(args.out)
    else:
        reevaluate(args.out, tasks)
        summarize(args.out)


if __name__ == "__main__":
    main()
