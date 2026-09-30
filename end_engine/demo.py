import argparse
import logging
from pathlib import Path

from . import EndEngine, EngineConfig
from .experience.serializer import dumps


TASK = "Design a memory architecture for a long-running AI agent that must preserve useful information without allowing memory growth to become unbounded."


def main():
    parser = argparse.ArgumentParser(description="Run the deterministic, offline END Engine demonstration")
    parser.add_argument("--output-dir", default="demo_output")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    directory = Path(args.output_dir)
    engine = EndEngine(EngineConfig(ledger_dir=str(directory), verbose=args.verbose))
    result = engine.run(TASK, mode="deep")
    record = engine.last_trajectory
    lines = ["END ENGINE v0.1 — OFFLINE MOCK DEMONSTRATION", "Scores and outputs are deterministic fixtures, not empirical model results.",
             "", "TASK", TASK]
    for step in record["steps"]:
        kind, data = step["type"], step["data"]
        if kind == "candidate":
            lines.extend(["", f"Candidate {data['iteration']} ({data['candidate_id']})", data["content"]])
        elif kind == "operator_selection":
            lines.extend(["", f"Selected operator: {data['operator']}", f"Reason: {data['reason']}"])
        elif kind == "critique":
            lines.append(f"Critique: {data['summary']}")
            for finding in data["findings"]:
                lines.extend([f"Weakness {finding['id']} [{finding['severity']}, {finding['status']}]: {finding['description']}",
                              f"Evidence: {finding['evidence']}"])
        elif kind == "revision_plan":
            lines.append("Revision plan:")
            for change in data["changes"]:
                lines.append(f"  {', '.join(change['targets'])}: {change['action']} Expected: {change['expected_effect']}")
        elif kind == "verification":
            lines.append(f"Verification {data['candidate_id']}: score={data['score']:.2f}; passed={data['passed']}; remaining={data['remaining_issues']}")
        elif kind == "weakness_status_change":
            lines.append(f"Weakness {data['after']['id']}: {data['before']['status']} -> {data['after']['status']}; {data['after']['status_reason']}")
        elif kind == "termination":
            lines.extend(["", f"Termination: {data['reason']}", data["explanation"]])
    lines.extend(["", f"JSONL trajectory: {result.trajectory_path}"])
    trace = "\n".join(lines)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "demo_trace.txt").write_text(trace + "\n", encoding="utf-8")
    pretty = dumps(record, pretty=True)
    (directory / "demo_trajectory.json").write_text(pretty + "\n", encoding="utf-8")
    print(trace)
    print("\nCOMPLETE TRAJECTORY JSON\n" + pretty)
    return 0 if result.termination_reason.value == "QUALITY_THRESHOLD_REACHED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
