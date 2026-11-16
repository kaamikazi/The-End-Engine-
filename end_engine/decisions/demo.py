"""Offline routing example. Live mode requires a separate explicit flag and model pin.

This module was run only in its default offline mode during implementation.
"""
import argparse
import json
from pathlib import Path

from .. import EndEngine, EngineConfig, MockProvider
from ..experience.serializer import dumps
from .config import DecisionConfig


def main():
    parser=argparse.ArgumentParser(description="Experimental decision routing with a mock reasoning provider")
    parser.add_argument("--output-dir",default="trajectories/decision_demo")
    parser.add_argument("--allow-live",action="store_true",help="Explicitly authorize at most one TypeSafe decision request")
    parser.add_argument("--model",help="Explicit TypeSafe model pin or alias; required for live mode")
    args=parser.parse_args()
    if args.allow_live and not args.model:
        parser.error("Live mode requires an explicit --model; no moving alias is selected for you")
    config=EngineConfig(ledger_dir=args.output_dir,max_run_calls=8,decision=DecisionConfig(
        provider="jev" if args.allow_live else "scripted",requested_model=args.model if args.allow_live else None,
        max_calls_per_run=1))
    engine=EndEngine(config,provider=MockProvider())
    result=engine.run("Design a bounded memory store for an agent.",mode="normal",max_cycles=1)
    record=engine.last_trajectory
    directory=Path(args.output_dir)
    (directory/"decision_demo.json").write_text(dumps(record,pretty=True)+"\n",encoding="utf-8")
    print(json.dumps({"execution_mode":"explicit_live_decision" if args.allow_live else "offline",
        "decision_summary":record.get("decision_summary"),"shared_budget":record.get("run_call_budget"),
        "gate":result.quality_gate,"trajectory":result.trajectory_path,
        "notice":"Jev judgments are model-generated decision signals. They are not independent evidence and do not satisfy END Engine verification requirements by themselves."},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
