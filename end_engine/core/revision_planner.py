from .state import Change, RevisionPlan, to_data
from ..models.base import ModelRequest
from ..models.schema import PLAN, validate


class RevisionPlanner:
    def plan(self, task, candidate, critique, weaknesses, provider, *, synthesis=None, reframing=None):
        data = provider.generate_structured(ModelRequest(
            "revision_plan", "Create explicit changes addressing the critique and unresolved weaknesses. "
            "For each change name existing weakness IDs, the action, and the expected effect. "
            "Do not rewrite the candidate or claim that planned changes are already verified. "
            "An improvement without a recorded weakness may use an empty targets list.",
            {"task": task, "candidate": to_data(candidate), "critique": to_data(critique),
             "weaknesses": to_data(weaknesses), "synthesis": to_data(synthesis),
             "proposed_reframing": reframing}, PLAN)).content
        validate(data, PLAN)
        valid_ids = {w.id for w in weaknesses}
        for change in data["changes"]:
            if not set(change["targets"]) <= valid_ids:
                raise ValueError("Revision plan targets unknown weakness IDs")
        return RevisionPlan(candidate.candidate_id, tuple(
            Change(tuple(c["targets"]), c["action"], c["expected_effect"]) for c in data["changes"]))
