from ..core.state import VerificationResult, WeaknessStatus, WeaknessUpdate, to_data
from ..models.base import ModelRequest
from ..models.protocol import REPAIR_INSTRUCTION
from ..models.schema import validate, verification_schema
from ..core.output_format import candidate_answer
from ..quality.assessment import AssessmentAuthorityPolicy


class LLMVerifier:
    def __init__(self, provider=None):
        self.provider = provider

    def verify(self, task, candidate, trajectory, repair=None):
        if self.provider is None:
            raise ValueError("LLMVerifier requires a provider")
        dimensions = trajectory["analysis"]["dimensions"]
        schema = verification_schema(dimensions)
        suffix, extra = ("\n\n" + REPAIR_INSTRUCTION, {"protocol_repair": repair}) if repair is not None else ("", {})
        view = {**to_data(candidate), 'content': candidate_answer(candidate)}
        data = self.provider.generate_structured(ModelRequest(
            "verification", "Evaluate each requested dimension explicitly on [0,1]. "
            "0 means unusable, 0.5 substantial gaps, 0.8 usable with limitations, 1 fully supported. "
            "Compare the candidate against the task and the recorded issues. Return remaining issues. "
            "Change a weakness status only with specific supporting evidence from the candidate or a check; "
            "planned fixes are not evidence. Accepted risk requires a clear documented justification. "
            "Do not claim to have executed tools or tests. Return concise evaluation results. "
            "weakness_updates may name only IDs listed in weaknesses; leave it empty when none apply." + suffix,
            {"task": task, "candidate": view, "dimensions": dimensions,
             'assessment_context': AssessmentAuthorityPolicy(task).context(candidate),
             "weaknesses": trajectory["weaknesses"],
             "previous_verification": trajectory["verification"][-1:], **extra}, schema)).content
        validate(data, schema)
        # Cap optimistic overall scores by the arithmetic mean of explicit dimensions.
        scores = data["dimensions"]
        score = min(data["score"], sum(scores.values()) / len(scores))
        passed = data["passed"] and score >= 0.8 and min(scores.values()) >= 0.6 and not data["remaining_issues"]
        return VerificationResult(passed, score, tuple(scores.items()), tuple(data["remaining_issues"]),
                                  tuple(WeaknessUpdate(u["id"], WeaknessStatus(u["status"]), u["reason"])
                                        for u in data["weakness_updates"]), "llm")
