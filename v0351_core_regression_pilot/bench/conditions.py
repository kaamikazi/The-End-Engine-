"""The five Benchmark Beta conditions (END Engine v0.3.5). All receive the task prompt verbatim and one transport.

DIRECT               one text generation of the task prompt.
SELF_REFLECT         initial answer -> self-critique -> one revision (three text generations; no END machinery).
END_LITE_NATIVE      END without the quality layer (no judges, QualityGate, comparison or rollback), branching off, meta
                     checks effectively off, mode "normal", max_cycles 2, candidate_generation="native".
FULL_END_NATIVE      END strict quality path with Engine defaults (heuristic task analysis, branching on, primary +
                     adversarial judge = same model, QualityGate, rollback, reconciliation), candidate_generation="native".
FULL_END_STRUCTURED  identical to FULL_END_NATIVE except candidate_generation="structured" (the v0.3.4 generation path),
                     isolating v0.3.5 protocol recovery + grounded judging from the native C0 change.
All END conditions: protocol_repair_attempts=1, no secondary judge, no tool verifier. Nothing here is task-specific."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from end_engine import EndEngine, EngineConfig
from end_engine.models.base import ModelRequest
from end_engine.quality.providers import ModelJudgeProvider

CONDITIONS = ("DIRECT", "SELF_REFLECT", "END_LITE_NATIVE", "FULL_END_NATIVE", "FULL_END_STRUCTURED")
END_CONDITIONS = ("END_LITE_NATIVE", "FULL_END_NATIVE", "FULL_END_STRUCTURED")
GATED = ("FULL_END_NATIVE", "FULL_END_STRUCTURED")
GENERATION = {"END_LITE_NATIVE": "native", "FULL_END_NATIVE": "native", "FULL_END_STRUCTURED": "structured"}
REPAIRS = 1
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
                            post_acceptance_cycles=0, candidate_generation="native", protocol_repair_attempts=REPAIRS)

    def full_config(self, ledger_dir, generation):
        return EngineConfig(ledger_dir=str(ledger_dir), candidate_generation=generation, protocol_repair_attempts=REPAIRS)

    def describe(self):
        full = {"engine_config": "EngineConfig() defaults (branching on, post_acceptance_cycles 0, judge_min_confidence "
                                 "0.75) + protocol_repair_attempts=1",
                "judge_provider": "ModelJudgeProvider(same model transport)",
                "adversarial_judge": "defaults to the primary judge (same model)",
                "secondary_judge": None, "tool_verifier": None, "mode": None, "max_cycles": self.full_max_cycles}
        return {"END_LITE_NATIVE": {"engine_config": {"enable_branching": False, "meta_check_interval": 1000,
                                                      "post_acceptance_cycles": 0, "quality_evaluation": False,
                                                      "candidate_generation": "native", "protocol_repair_attempts": REPAIRS},
                                    "judge_provider": None, "secondary_judge": None, "adversarial_judge": None,
                                    "tool_verifier": None, "mode": self.lite_mode, "max_cycles": self.lite_max_cycles},
                "FULL_END_NATIVE": {**full, "candidate_generation": "native"},
                "FULL_END_STRUCTURED": {**full, "candidate_generation": "structured"}}


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
    events = trajectory.get("protocol_events", [])
    actions = {}
    for e in events:
        actions[e["action"]] = actions.get(e["action"], 0) + 1
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
        "candidate_generation": config.candidate_generation, "protocol_repair_attempts": config.protocol_repair_attempts,
        "termination_category": (trajectory.get("termination") or {}).get("category"),
        "protocol_actions": actions, "protocol_events": len(events),
        "judge_groundings": [{k: g.get(k) for k in ("judgment_id", "candidate_id", "issue", "status", "description")}
                             for g in trajectory.get("judge_groundings", [])],
        "engine_checks": trajectory.get("engine_checks", []),
        "gate_decisions": [{"candidate_id": g["candidate_id"], "decision": g["decision"]}
                           for g in trajectory.get("quality_gate_decisions", [])],
        "errors": [{"stage": e.get("stage"), "message": str(e.get("message"))[:300]} for e in trajectory.get("errors", [])]}}


def run_end_lite(task, model, ledger_dir, settings: EndSettings):
    return _end(task, model, settings.lite_config(ledger_dir), mode=settings.lite_mode, max_cycles=settings.lite_max_cycles)


def run_full_end(task, model, ledger_dir, settings: EndSettings, generation):
    return _end(task, model, settings.full_config(ledger_dir, generation), judge=ModelJudgeProvider(model),
                max_cycles=settings.full_max_cycles)


def load_trajectory(directory, name):
    """Read an Engine ledger record (one JSON line). Never writes."""
    return json.loads(Path(directory, name).read_text(encoding="utf-8").splitlines()[0])
