from dataclasses import dataclass

from ..core.state import to_data
from ..models.base import ModelRequest
from ..models.protocol import REPAIR_INSTRUCTION
from ..models.schema import CRITIQUE, validate
from ..core.output_format import candidate_answer
from ..quality.assessment import AssessmentAuthorityPolicy


@dataclass(frozen=True)
class CognitiveOperator:
    name: str
    purpose: str
    trigger_conditions: tuple[str, ...]
    prompt_template: str
    expected_output_type: str = "StructuredCritique"
    family: str = "foundational"
    targets: tuple[str, ...] = ()
    best_when: tuple[str, ...] = ()
    poor_when: tuple[str, ...] = ()
    cost: float = 0.3
    novelty_bias: float = 0.6
    can_branch: bool = False
    compatible_followups: tuple[str, ...] = ()
    preferred_target_types: tuple[str, ...] = ("WEAKNESS", "WHOLE_CANDIDATE")

    def __post_init__(self):
        import math
        for value in (self.cost, self.novelty_bias):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Operator cost and novelty_bias must lie in [0, 1]")

    def execute(self, provider, *, task, candidate, weaknesses=(), question=None, cognitive_context=None, repair=None):
        """An independent operator call; it never rewrites the candidate."""
        request = ModelRequest("critique", self.prompt_template +
            " Return a brief, checkable critique with concrete findings and evidence. "
            "Do not rewrite the answer. Reuse weakness_id for existing issues; use null for new issues. "
            "Evidence may describe an observable gap, but do not invent measurements or citations. "
            "Answer the concrete question when provided. You may report bounded claims, assumptions, "
            "and evidenced status updates. Preserve the user's original goal in any proposed reframing.",
            {"operator": self.name, "task": task, "candidate": {**to_data(candidate), 'content': candidate_answer(candidate)},
             'assessment_context': AssessmentAuthorityPolicy(task).context(candidate),
            "weaknesses": to_data(weaknesses), "question": to_data(question),
             "cognitive_context": cognitive_context,
             "allowed_weakness_ids": sorted(w.id for w in weaknesses)}, CRITIQUE)
        if repair is not None:  # v0.3.5: one targeted protocol repair listing the valid identifiers
            request = ModelRequest(request.purpose, request.prompt + "\n\n" + REPAIR_INSTRUCTION,
                                   {**request.context, "protocol_repair": repair}, request.schema)
        data = provider.generate_structured(request).content
        return validate(data, CRITIQUE)
