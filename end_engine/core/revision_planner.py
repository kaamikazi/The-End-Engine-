from .state import Change, RevisionPlan, to_data
from ..models.base import ModelRequest
from ..models.protocol import INVALID_REFERENCE, REPAIR_INSTRUCTION, ModelProtocolError
from ..models.schema import PLAN, validate
from ..core.output_format import candidate_answer
from ..quality.assessment import AssessmentAuthorityPolicy


class RevisionPlanner:
    def plan(self, task, candidate, critique, weaknesses, provider, *, synthesis=None, reframing=None, repair=None,
             salvage=False):
        """repair: protocol_repair context for one targeted retry. salvage: instead of raising on unknown targets, drop
        them; a change whose targets were all unknown is discarded, never re-targeted. Returns (plan, discarded) when
        salvage is requested, otherwise the plan."""
        context = {"task": task, "candidate": to_data(candidate), "critique": to_data(critique),
                   "weaknesses": to_data(weaknesses), "synthesis": to_data(synthesis), "proposed_reframing": reframing}
        context['allowed_weakness_ids'] = sorted(w.id for w in weaknesses)
        context['candidate']['content'] = candidate_answer(candidate)
        context['assessment_context'] = AssessmentAuthorityPolicy(task).context(candidate)
        prompt = ("Create explicit changes addressing the critique and unresolved weaknesses. "
                  "For each change name existing weakness IDs, the action, and the expected effect. "
                  "Do not rewrite the candidate or claim that planned changes are already verified. "
                  "An improvement without a recorded weakness may use an empty targets list.")
        prompt += (" Targets must be copied exactly from allowed_weakness_ids. JSON field names, candidate IDs, "
                   "claim IDs and prose labels are not weakness IDs. If none applies, use targets=[]; never invent an ID.")
        prompt += (' You produce MODEL_REVISION_PLAN suggestions, never new user requirements. '
                   'Original task constraints prevail. Do not add unsupported evidence or verification authority.')
        if repair is not None:
            prompt, context = prompt + "\n\n" + REPAIR_INSTRUCTION, {**context, "protocol_repair": repair}
        data = provider.generate_structured(ModelRequest("revision_plan", prompt, context, PLAN)).content
        return self.from_data(candidate, weaknesses, data, salvage=salvage)

    def from_data(self, candidate, weaknesses, data, *, salvage=False):
        """Parse/salvage an already returned result without making another model call."""
        validate(data, PLAN)
        valid_ids = {w.id for w in weaknesses}
        invalid = sorted({t for c in data["changes"] for t in c["targets"] if t not in valid_ids})
        if invalid and not salvage:
            raise ModelProtocolError(INVALID_REFERENCE, "Revision plan targets unknown weakness IDs", stage="revision_plan",
                                     invalid=invalid, allowed={"weakness_ids": sorted(valid_ids)}, output=data)
        changes, discarded = [], []
        for c in data["changes"]:
            kept = tuple(t for t in c["targets"] if t in valid_ids)
            if c["targets"] and not kept:
                discarded.append({"change": c, "reason": "every target is an unknown weakness ID"})
                continue
            if len(kept) != len(c["targets"]):
                discarded.append({"change": c, "reason": "unknown targets removed",
                                  "removed": [t for t in c["targets"] if t not in valid_ids]})
            changes.append(Change(kept, c["action"], c["expected_effect"]))
        plan = RevisionPlan(candidate.candidate_id, tuple(changes))
        return (plan, tuple(discarded)) if salvage else plan
