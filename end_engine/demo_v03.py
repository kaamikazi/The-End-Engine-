import argparse
import logging
from pathlib import Path

from . import EndEngine, EngineConfig
from .demo_v02 import format_trace
from .experience.serializer import dumps, loads
from .models.deployment_mock import DEPLOYMENT_TASK, DeploymentMockProvider, DeploymentJudgeProvider, deployment_tool_verifier


def quality_trace(record):
    lines = ["END ENGINE v0.3 — INDEPENDENT QUALITY AND ROLLBACK", DEPLOYMENT_TASK,
             "Mock model judgments; actual execution is limited to the documented abstract state-machine checks."]
    for step in record["steps"]:
        kind, d = step["type"], step["data"]
        if kind == "candidate":
            lines.extend(["", f"Candidate {d['candidate_id']}", d["content"]])
        elif kind == "operator_selection":
            lines.append(f"Operator {d['operator']} -> {d['target']['target_id']}: {d['reason']}")
        elif kind == "question":
            lines.append(f"Question {d['question_id']}: {d['question']}")
        elif kind == "verification":
            lines.append(f"[VERIFY] {d['candidate_id']} score={d['score']:.2f}, type={d['evidence_type']}")
        elif kind in ("judgment", "adversarial_judgment"):
            lines.append(f"[{kind.upper()}] {d['candidate_id']}: {d['verdict']} — {d['major_issues'] or d['fatal_issues']}")
        elif kind in ("adversarial_test", "verifier_evidence", "claim_validation", "resolution_audit", "assumption_audit",
                      "pairwise_comparison", "quality_gate", "candidate_rollback", "transition_label", "judge_feedback"):
            lines.append(f"[{kind.upper()}] {d}")
        elif kind == "termination":
            lines.append(f"Termination: {d}")
    lines.extend(["", "FINAL SCORECARD", dumps(record["scorecard"], pretty=True)])
    return "\n".join(lines)+"\n"


def main():
    parser = argparse.ArgumentParser(description="Offline v0.3 quality gate and controlled regression demonstration")
    parser.add_argument("--output-dir", default="demo_v03_output")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = EndEngine(EngineConfig(ledger_dir=args.output_dir, verbose=args.verbose, post_acceptance_cycles=1,
                                    enable_branching=False), provider=DeploymentMockProvider(),
                       judge_provider=DeploymentJudgeProvider(), tool_verifier=deployment_tool_verifier())
    result = engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=4)
    record = engine.last_trajectory
    directory = Path(args.output_dir)
    trace = quality_trace(record)
    (directory/"demo_trace.txt").write_text(trace, encoding="utf-8")
    (directory/"cognitive_trace.txt").write_text(format_trace(record), encoding="utf-8")
    serialized = dumps(record, pretty=True)
    (directory/"demo_trajectory.json").write_text(serialized+"\n", encoding="utf-8")
    assert loads(serialized) == loads(Path(result.trajectory_path).read_text(encoding="utf-8"))
    print(trace)
    print("\nCOMPLETE TRAJECTORY JSON\n"+serialized)
    return 0 if result.best_candidate_id == "C3" and result.latest_candidate_id == "C4" and result.quality_gate == "ACCEPT_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
