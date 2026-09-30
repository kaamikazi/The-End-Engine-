import argparse
import logging
from pathlib import Path

from . import EndEngine, EngineConfig
from .experience.serializer import dumps, loads
from .models.production_mock import PRODUCTION_TASK, ProductionAgentMockProvider


def format_trace(record):
    lines = ["END ENGINE v0.2 — COGNITIVE OPERATOR BRAIN", "Offline fixture; scores and evidence judgments are synthetic.",
             "", "TASK", record["task"]["content"]]
    for step in record["steps"]:
        kind, data = step["type"], step["data"]
        if kind == "candidate":
            lines.extend(["", f"Candidate {data['candidate_id']}", data["content"]])
        elif kind == "cognitive_state":
            lines.append(f"State: open={data['high_severity_weaknesses']}, budget={dict(data['remaining_budget'])}")
            lines.append("Coverage: " + ", ".join(f"{k}={v}" for k,v in data["coverage"]))
        elif kind == "operator_selection":
            lines.extend(["", "Operator candidates:"])
            for item in data["ranking"][:5]:
                lines.append(f"  {item['operator']}: utility={item['utility']:.3f}, factors={item['scores']}")
            lines.append(f"Selected {data['operator']} -> {data['target']['target_id']}: {data['reason']}")
        elif kind == "question":
            lines.append(f"Question {data['question_id']}: {data['question']}")
        elif kind == "critique":
            lines.append(f"Critique: {data['summary']}")
            for w in data["findings"]:
                lines.append(f"  {w['id']} [{w['severity']}]: {w['description']} Evidence: {w['evidence']}")
        elif kind in ("claim_discovered", "assumption_discovered", "claim_status_change", "assumption_status_change"):
            lines.append(f"{kind}: {data['after']}")
        elif kind == "operator_outcome":
            lines.append(f"Information gain: {data['information_gain']}")
        elif kind == "branch_created":
            b = data["after"]
            lines.append(f"Branch {b['branch_id']} ({b['status']}): {b['hypothesis']} — {b['content']}")
        elif kind == "branch_evaluation":
            lines.append(f"Evaluation {data['branch_id']}: {data['scores']}; {data['recommendation']}; weaknesses={data['weaknesses']}")
        elif kind == "branch_status_change":
            lines.append(f"Branch {data['after']['branch_id']}: {data['before']['status']} -> {data['after']['status']}")
        elif kind in ("synthesis_plan", "revision_plan", "meta_check", "reframing"):
            lines.append(f"{kind}: {data}")
        elif kind == "verification":
            lines.append(f"Verification {data['candidate_id']}: {data['score']:.2f}, passed={data['passed']}, remaining={data['remaining_issues']}")
        elif kind == "termination":
            lines.extend(["", f"Termination: {data['reason']} — {data['explanation']}"])
        elif kind == "error":
            lines.append(f"ERROR: {data}")
    return "\n".join(lines)+"\n"


def main():
    parser = argparse.ArgumentParser(description="Run the offline v0.2 cognitive brain demonstration")
    parser.add_argument("--output-dir", default="demo_v02_output")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = EndEngine(EngineConfig(ledger_dir=args.output_dir, verbose=args.verbose), provider=ProductionAgentMockProvider())
    result = engine.run(PRODUCTION_TASK, mode="critical", max_cycles=8)
    record = engine.last_trajectory
    path = Path(args.output_dir)
    path.mkdir(parents=True, exist_ok=True)
    trace = format_trace(record)
    (path/"demo_trace.txt").write_text(trace, encoding="utf-8")
    serialized = dumps(record, pretty=True)
    (path/"demo_trajectory.json").write_text(serialized+"\n", encoding="utf-8")
    assert loads(serialized) == loads(Path(result.trajectory_path).read_text(encoding="utf-8"))
    print(trace)
    print("Complete trajectory: " + str((path/"demo_trajectory.json").resolve()))
    print("\nCOMPLETE TRAJECTORY JSON\n"+serialized)
    return int(result.termination_reason.value == "EXTERNAL_BLOCKER")


if __name__ == "__main__":
    raise SystemExit(main())
