"""Benchmark Alpha command line.

  python -B -m bench.cli baseline                 write ENGINE_BASELINE.json (runs nothing else)
  python -B -m bench.cli synthetic OUT            SYNTHETIC BENCHMARK INFRASTRUCTURE TEST into OUT
  python -B -m bench.cli live OUT --model qwen3:4b --trials 3 [--full-max-cycles N]
  python -B -m bench.cli summarize OUT            rebuild summary/CSV/reports from stored records
Run from benchmark_alpha/ with the Engine repository on sys.path (added automatically)."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent.parent          # benchmark_alpha/
ENGINE = HERE.parent                                    # repository root
sys.path.insert(0, str(ENGINE))

from .conditions import EndSettings  # noqa: E402
from .providers import ModelSettings, OllamaModel, discover  # noqa: E402
from .report import summarize  # noqa: E402
from .runner import load_tasks, reevaluate, run_benchmark, task_set_hash  # noqa: E402
from . import synthetic  # noqa: E402

SEED = 20261001


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


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline")
    s = sub.add_parser("synthetic"); s.add_argument("out")
    live = sub.add_parser("live"); live.add_argument("out"); live.add_argument("--model", default="qwen3:4b")
    live.add_argument("--trials", type=int, default=3); live.add_argument("--full-max-cycles", type=int, default=None)
    live.add_argument("--tasks", nargs="*", default=None)
    m = sub.add_parser("summarize"); m.add_argument("out")
    args = parser.parse_args(argv)
    tasks = load_tasks(HERE / "tasks")
    if args.command == "baseline":
        print(json.dumps(engine_identity(), indent=1))
    elif args.command == "synthetic":
        chosen = [t for t in tasks if t["task_id"] in synthetic.SCENARIOS]
        run_benchmark(args.out, chosen, trials=1, seed=SEED, model_factory=synthetic.factory(),
                      model_record={"provider": "synthetic-scripted", "model": "synthetic-fixture",
                                    "settings": None, "label": synthetic.LABEL},
                      data_origin="SYNTHETIC", engine_identity=engine_identity(), label=synthetic.LABEL)
        summarize(args.out)
    elif args.command == "live":
        settings = ModelSettings(args.model)
        identity = discover(settings)
        chosen = [t for t in tasks if not args.tasks or t["task_id"] in args.tasks]
        record = {"provider": settings.provider, "model": settings.model, "model_identity": identity,
                  "settings": {"temperature": settings.temperature, "top_p": settings.top_p,
                               "max_output_tokens": settings.num_predict, "context_window_requested": settings.num_ctx,
                               "seed": f"per call: sha256(base_seed={settings.base_seed}, trial seed, call index)",
                               "thinking": settings.think, "system_instructions": settings.system,
                               "structured_retries": settings.structured_retries, "timeout_seconds": settings.timeout_seconds,
                               "context_limit_reported": identity.get("context_length")},
                  "same_model_all_conditions": True}

        def factory(log, trial_seed, task, condition, trial):
            return OllamaModel(settings, identity, log, trial_seed=trial_seed)
        run_benchmark(args.out, chosen, trials=args.trials, seed=SEED, model_factory=factory, model_record=record,
                      data_origin="LIVE_LOCAL_MODEL", end_settings=EndSettings(full_max_cycles=args.full_max_cycles),
                      engine_identity=engine_identity(), label="Benchmark Alpha live run",
                      progress=lambda m: print(m, flush=True))
        reevaluate(args.out, tasks)
        summarize(args.out)
    else:
        reevaluate(args.out, tasks)
        summarize(args.out)


if __name__ == "__main__":
    main()
