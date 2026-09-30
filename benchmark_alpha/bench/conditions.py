"""The four Benchmark Alpha conditions. All receive the task prompt verbatim and one model transport.

DIRECT        one text generation of the task prompt.
SELF_REFLECT  initial answer -> self-critique -> one revision (three text generations; no END machinery).
END_LITE      END v0.3.4 without the quality layer: no judge provider (so no QualityGate, judges, adversary,
              comparison or rollback), branching disabled, meta checks effectively disabled, mode "normal",
              max_cycles 2. Internal acceptance is the Engine's own LLM verifier result.
FULL_END      END v0.3.4 strict quality path with Engine defaults: heuristic task analysis (mode chosen by the Engine),
              branching enabled, primary judge + adversarial judge (same model, via ModelJudgeProvider), QualityGate,
              rollback, final reconciliation. No secondary judge and no tool verifier are configured (none exists for
              these tasks without leaking the external evaluator). max_cycles is the benchmark-wide FULL_END_MAX_CYCLES.
Nothing here is task-specific."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from end_engine import EndEngine, EngineConfig
from end_engine.models.base import ModelRequest
from end_engine.quality.providers import ModelJudgeProvider

CONDITIONS = ("DIRECT", "SELF_REFLECT", "END_LITE", "FULL_END")
SELF_CRITIQUE = ("Here is a task and an answer you wrote.\n\nTASK:\n{task}\n\nANSWER:\n{answer}\n\n"
                 "Critique this answer. List concrete errors, unmet requirements and unsupported claims. "
                 "Do not rewrite the answer.")
SELF_REVISE = ("TASK:\n{task}\n\nYOUR PREVIOUS ANSWER:\n{answer}\n\nCRITIQUE OF THAT ANSWER:\n{critique}\n\n"
               "Write your final, revised answer to the task. Follow all output instructions in the task.")


@dataclass(frozen=True)
class EndSettings:
    lite_mode: str = "normal"
    lite_max_cycles: int = 2
    full_max_cycles: int | None = None   # None = the Engine's own budget for the analyzed complexity

    def lite_config(self, ledger_dir):
        return EngineConfig(ledger_dir=str(ledger_dir), enable_branching=False, meta_check_interval=1000,
                            post_acceptance_cycles=0)

    def full_config(self, ledger_dir):
        return EngineConfig(ledger_dir=str(ledger_dir))

    def describe(self):
        return {"END_LITE": {"engine_config": {"enable_branching": False, "meta_check_interval": 1000,
                                               "post_acceptance_cycles": 0, "quality_evaluation": False},
                             "judge_provider": None, "secondary_judge": None, "adversarial_judge": None,
                             "tool_verifier": None, "mode": self.lite_mode, "max_cycles": self.lite_max_cycles},
                "FULL_END": {"engine_config": "EngineConfig() defaults (branching on, post_acceptance_cycles 0, "
                                              "judge_min_confidence 0.75)",
                             "judge_provider": "ModelJudgeProvider(same model transport)",
                             "adversarial_judge": "defaults to the primary judge (same model)",
                             "secondary_judge": None, "tool_verifier": None, "mode": None,
                             "max_cycles": self.full_max_cycles}}


def run_direct(task, model):
    answer = model.generate(ModelRequest("direct_answer", task["prompt"], {}, None)).content
    return {"answer": answer, "stages": {"answer": answer}}


def run_self_reflect(task, model):
    initial = model.generate(ModelRequest("self_reflect_initial", task["prompt"], {}, None)).content
    critique = model.generate(ModelRequest("self_reflect_critique",
                                           SELF_CRITIQUE.format(task=task["prompt"], answer=initial), {}, None)).content
    final = model.generate(ModelRequest("self_reflect_revision", SELF_REVISE.format(
        task=task["prompt"], answer=initial, critique=critique), {}, None)).content
    return {"answer": final, "stages": {"initial": initial, "critique": critique, "final": final}}


def _end(task, model, config, *, judge=None, mode=None, max_cycles=None):
    engine = EndEngine(config, provider=model, judge_provider=judge)
    result = engine.run(task["prompt"], mode=mode, max_cycles=max_cycles)
    trajectory = engine.last_trajectory
    path = Path(result.trajectory_path)
    data = path.read_bytes()
    rollbacks = [dict(r) for r in trajectory.get("rollback_events", [])]
    verification = trajectory.get("verification") or []
    final_id = trajectory.get("final_candidate_id")
    returned_verification = next((v for v in reversed(verification) if v["candidate_id"] == final_id), None)
    return {"answer": result.answer, "stages": {}, "end": {
        "trajectory_id": result.trajectory_id, "trajectory_file": path.name,
        "trajectory_sha256": hashlib.sha256(data).hexdigest(),
        "termination": result.termination_reason.value, "quality_gate": result.quality_gate,
        "acceptance_label": result.acceptance_label, "returned_candidate_id": final_id,
        "best_candidate_id": trajectory.get("best_candidate_id"), "latest_candidate_id": trajectory.get("latest_candidate_id"),
        "iterations": result.iterations, "complexity": (trajectory.get("analysis") or {}).get("complexity"),
        "candidates": [c["candidate_id"] for c in trajectory.get("candidates", [])],
        "returned_verification": returned_verification and {k: returned_verification.get(k) for k in
                                                            ("passed", "score", "remaining_issues", "evidence_type")},
        "rollback_events": rollbacks, "branch_count": len(trajectory.get("branches", [])),
        "gate_decisions": [{"candidate_id": g["candidate_id"], "decision": g["decision"]}
                           for g in trajectory.get("quality_gate_decisions", [])],
        "errors": [{"stage": e.get("stage"), "message": str(e.get("message"))[:300]} for e in trajectory.get("errors", [])]}}


def run_end_lite(task, model, ledger_dir, settings: EndSettings):
    return _end(task, model, settings.lite_config(ledger_dir), mode=settings.lite_mode, max_cycles=settings.lite_max_cycles)


def run_full_end(task, model, ledger_dir, settings: EndSettings):
    return _end(task, model, settings.full_config(ledger_dir), judge=ModelJudgeProvider(model),
                max_cycles=settings.full_max_cycles)


def load_trajectory(directory, name):
    """Read an Engine ledger record (one JSON line). Never writes."""
    return json.loads(Path(directory, name).read_text(encoding="utf-8").splitlines()[0])
