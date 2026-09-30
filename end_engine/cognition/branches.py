from dataclasses import dataclass, replace
from typing import Protocol

from ..core.state import to_data
from ..models.base import ModelRequest
from ..models.schema import BRIEF, SCORE, STRING, STRINGS, obj, validate


@dataclass(frozen=True)
class BranchEvaluation:
    branch_id: str
    scores: tuple[tuple[str, float], ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True)
class CognitiveBranch:
    branch_id: str
    parent_candidate_id: str
    created_by: str
    hypothesis: str
    content: str
    status: str = "ACTIVE"
    evaluation: BranchEvaluation | None = None
    parent_branch_id: str | None = None
    depth: int = 1


@dataclass(frozen=True)
class SynthesisElement:
    branch: str
    element: str
    reason: str = ""


@dataclass(frozen=True)
class SynthesisPlan:
    source_branches: tuple[str, ...]
    adopt: tuple[SynthesisElement, ...]
    reject: tuple[SynthesisElement, ...]


class BranchEvaluator(Protocol):
    def evaluate(self, task, branch, dimensions, provider) -> BranchEvaluation: ...


class LLMBranchEvaluator:
    def evaluate(self, task, branch, dimensions, provider):
        dimensions = tuple(dict.fromkeys((*dimensions, "constraint_fit", "simplicity")))
        schema = obj({"scores": obj({d: SCORE for d in dimensions}), "strengths": STRINGS,
                      "weaknesses": STRINGS, "recommendation": {"type": "string", "enum": ["MERGE_COMPONENTS", "REJECT", "EXHAUSTED"]}})
        data = provider.generate_structured(ModelRequest("branch_evaluation",
            "Assess this hypothesis on each requested dimension. Higher simplicity means lower unnecessary complexity. "
            "Preserve useful components and disqualifying weaknesses. Do not collapse the decision to one scalar score.",
            {"task": task, "branch": to_data(branch), "dimensions": dimensions}, schema)).content
        validate(data, schema)
        return BranchEvaluation(branch.branch_id, tuple(data["scores"].items()), tuple(data["strengths"]),
                                tuple(data["weaknesses"]), data["recommendation"])


class SynthesisPlanner:
    def synthesize(self, task, candidate, branches, provider):
        schema = obj({"source_branches": STRINGS,
                      "adopt": {"type": "array", "maxItems": 12, "items": obj({"branch": STRING, "element": BRIEF})},
                      "reject": {"type": "array", "maxItems": 12, "items": obj({"branch": STRING, "element": BRIEF, "reason": BRIEF})}})
        data = provider.generate_structured(ModelRequest("synthesis",
            "Create a synthesis plan using all evaluated branches. Combine useful components across promising branches "
            "when compatible. Preserve rejected ideas and their reasons. Include every branch in source_branches. "
            "Never adopt from a rejected or exhausted branch. Do not rewrite the candidate.",
            {"task": task, "candidate": to_data(candidate), "branches": to_data(branches)}, schema)).content
        validate(data, schema)
        sources = {b.branch_id: b for b in branches}
        if set(data["source_branches"]) != sources.keys() or len(data["source_branches"]) != len(sources):
            raise ValueError("Synthesis must account for every branch exactly once")
        for item in (*data["adopt"], *data["reject"]):
            if item["branch"] not in sources:
                raise ValueError("Synthesis references an unknown branch")
        for item in data["adopt"]:
            if sources[item["branch"]].status != "PROMISING":
                raise ValueError("Cannot adopt from a non-promising branch")
        return SynthesisPlan(tuple(data["source_branches"]),
                             tuple(SynthesisElement(**item) for item in data["adopt"]),
                             tuple(SynthesisElement(**item) for item in data["reject"]))


class BranchController:
    def __init__(self, config, trajectory, session, *, evaluator=None, synthesis=None):
        self.config, self.trajectory, self.session = config, trajectory, session
        self.evaluator = evaluator if evaluator is not None else LLMBranchEvaluator()
        self.synthesis = synthesis if synthesis is not None else SynthesisPlanner()
        self._branches = {}

    def snapshot(self):
        return tuple(self._branches.values())

    def _record(self, branch, before=None):
        self._branches[branch.branch_id] = branch
        self.trajectory.record("branch_created" if before is None else "branch_status_change",
                               {"before": before, "after": branch})
        self.trajectory.set("branches", self.snapshot())

    def capacity(self, parent_branch_id=None):
        if parent_branch_id is not None and parent_branch_id not in self._branches:
            raise ValueError("Unknown parent branch")
        depth = self._branches[parent_branch_id].depth+1 if parent_branch_id else 1
        if depth > self.config.max_branch_depth:
            return 0
        active = sum(b.status in ("ACTIVE", "PROMISING") for b in self.snapshot())
        # Leave one operation for further main-candidate scrutiny after a branch batch.
        return max(0, min(self.config.max_active_branches-active,
                          self.config.max_branches_per_operator, self.session.remaining-1))

    def add(self, candidate_id, operator, hypothesis, content, *, parent_branch_id=None):
        if not operator.can_branch:
            raise ValueError("Operator does not support branching")
        siblings = sum(b.created_by == operator.name and b.parent_candidate_id == candidate_id
                       and b.parent_branch_id == parent_branch_id for b in self.snapshot())
        if siblings >= self.config.max_branches_per_operator:
            raise ValueError("Per-operator branch batch limit reached")
        if not self.capacity(parent_branch_id):
            raise ValueError("Branch depth, active count, or operation limit reached")
        if parent_branch_id and self._branches[parent_branch_id].status not in ("ACTIVE", "PROMISING"):
            raise ValueError("Cannot expand a closed branch")
        if parent_branch_id and self._branches[parent_branch_id].parent_candidate_id != candidate_id:
            raise ValueError("Branch ancestry belongs to a different candidate")
        self.session.consume()
        branch = CognitiveBranch(f"B{len(self._branches)+1}", candidate_id, operator.name, hypothesis, content,
                                 parent_branch_id=parent_branch_id,
                                 depth=self._branches[parent_branch_id].depth+1 if parent_branch_id else 1)
        self._record(branch)
        return branch

    def should_branch(self, state, operator):
        if not self.config.enable_branching or not operator.can_branch or state.complexity not in ("deep", "critical"):
            return False
        if state.alternatives_considered or self.capacity() < 2:
            return False
        # Branch only for competing design uncertainty, or multiple severe stress cases.
        return ((operator.family == "search" and bool(state.open_weaknesses or state.stagnation))
                or (len(state.high_severity_weaknesses) >= 2 and state.stagnation >= 1))

    def explore(self, task, candidate, operator, question, dimensions, provider, *, parent_branch_id=None):
        count = self.capacity(parent_branch_id)
        if count < 1:
            raise ValueError("No branch capacity")
        schema = obj({"branches": {"type": "array", "minItems": 1, "maxItems": count,
                      "items": obj({"hypothesis": BRIEF, "content": BRIEF})}})
        output = provider.generate_structured(ModelRequest("branch_generation",
            "Explore distinct competing hypotheses for this concrete question. Generate only the requested bounded batch. "
            "Preserve the original goal and constraints; make no source-code or deployment changes.",
            {"task": task, "candidate": to_data(candidate), "question": to_data(question), "max_branches": count}, schema)).content
        validate(output, schema)
        created = [self.add(candidate.candidate_id, operator, item["hypothesis"], item["content"],
                            parent_branch_id=parent_branch_id) for item in output["branches"]]
        for branch in created:
            evaluation = self.evaluator.evaluate(task, branch, dimensions, provider)
            # A custom evaluator receives the same structural and identity checks.
            if not isinstance(evaluation, BranchEvaluation) or evaluation.branch_id != branch.branch_id:
                raise ValueError("Invalid branch evaluation identity")
            if not set(dimensions) <= dict(evaluation.scores).keys() or len(dict(evaluation.scores)) != len(evaluation.scores):
                raise ValueError("Branch evaluation omitted or duplicated dimensions")
            validate(dict(evaluation.scores), obj({d: SCORE for d, _ in evaluation.scores}))
            statuses = {"REJECT": "REJECTED", "EXHAUSTED": "EXHAUSTED", "MERGE_COMPONENTS": "PROMISING"}
            if evaluation.recommendation not in statuses:
                raise ValueError("Invalid branch recommendation")
            self.trajectory.record("branch_evaluation", evaluation, "branch_evaluations")
            self._record(replace(branch, status=statuses[evaluation.recommendation], evaluation=evaluation), branch)
        evaluated = tuple(self._branches[b.branch_id] for b in created)
        plan = self.synthesis.synthesize(task, candidate, evaluated, provider)
        self.trajectory.record("synthesis_plan", plan, "synthesis_plans")
        adopted = {element.branch for element in plan.adopt}
        for branch in evaluated:
            if branch.status == "PROMISING":
                self._record(replace(branch, status="MERGED" if branch.branch_id in adopted else "EXHAUSTED"), branch)
        return plan, tuple(self._branches[b.branch_id] for b in created)

    def close_active(self, reason):
        for branch in self.snapshot():
            if branch.status in ("ACTIVE", "PROMISING"):
                self._record(replace(branch, status="EXHAUSTED"), branch)
                self.trajectory.record("branch_closed", {"branch_id": branch.branch_id, "reason": reason})
