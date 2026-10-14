from ..models.base import ModelRequest
from ..models.schema import validate
from .schema import comparison_schema
from .state import RevisionComparison
from ..core.output_format import candidate_answer


class RevisionComparator:
    def __init__(self, provider, *, material_delta=0.03, severe_delta=0.2):
        self.provider, self.material_delta, self.severe_delta = provider, material_delta, severe_delta

    def compare(self, task, parent, candidate, dimensions):
        schema = comparison_schema(dimensions)
        output = self.provider.generate_structured(ModelRequest("comparison",
            "Compare anonymous A and B against the original task. Do not prefer B for recency or length. "
            "For each dimension give the preferred alias and delta (B minus A), in [-1,1]. "
            "For complexity_cost, positive delta means extra burden. Identify lost requirements and recovery invariants.",
            {"task": task, "candidates": {"A": candidate_answer(parent), "B": candidate_answer(candidate)},
             "dimensions": dimensions, 'source_origins': {'task': 'TASK_INSTRUCTION_AND_ASSERTIONS',
                'candidates': 'CANDIDATE', 'comparison': 'MODEL_JUDGMENT_ADVISORY'}}, schema)).content
        validate(output, schema)
        delta = output["delta"]
        gains = [v for d,v in delta.items() if d != "complexity_cost"]
        severe = tuple(d for d,v in delta.items() if d in ("correctness", "robustness", "constraint_adherence") and v <= -self.severe_delta)
        positive = any(v > self.material_delta for v in gains)
        negative = any(v < -self.material_delta for v in gains) or delta.get("complexity_cost", 0) > self.severe_delta
        assessment = ("SEVERE_REGRESSION" if severe else "MIXED" if positive and negative else
                      "REGRESSION" if negative else "STRONG_IMPROVEMENT" if positive and max(gains) >= .2 else
                      "IMPROVEMENT" if positive else "NO_MATERIAL_CHANGE")
        mapping = {"A": parent.candidate_id, "B": candidate.candidate_id, "TIE": "TIE", "INCONCLUSIVE": "INCONCLUSIVE"}
        return RevisionComparison(parent.candidate_id, candidate.candidate_id,
            mapping[output["preferred"]] if output["preferred"] in ("A", "B") else None,
            tuple((d,mapping[v]) for d,v in output["dimensions"].items()), tuple(delta.items()),
            assessment, output["reason"], severe, False)
