from copy import deepcopy

from ..models.base import ModelResponse
from .providers import JudgeProvider


def judgment_fixture(dimensions, *, verdict="PASS", score=0.9, confidence=0.9, issues=(), fatal=False):
    return {"verdict": verdict, "dimensions": {d: {"score": score, "confidence": confidence} for d in dimensions},
            "fatal_issues": list(issues) if fatal else [], "major_issues": [] if fatal else list(issues),
            "minor_issues": [], "uncertainties": [], "evidence": [],
            "recommended_action": "ACCEPT" if verdict == "PASS" else "REVISE"}


class MockJudgeProvider(JudgeProvider):
    def __init__(self, *, scripted=None, model="independent-judge-fixture", confidence=0.9):
        self.scripted = deepcopy(scripted or {})
        self.positions = {}
        self.model, self.confidence = model, confidence

    def for_run(self):
        return MockJudgeProvider(scripted=self.scripted, model=self.model, confidence=self.confidence)

    def metadata(self):
        return {"provider": "mock-judge", "model": self.model, "offline": True}

    def evaluate(self, request):
        p, c = request.purpose, request.context
        if p in self.scripted:
            index = self.positions.get(p, 0)
            if index >= len(self.scripted[p]):
                raise RuntimeError(f"Judge script exhausted: {p}")
            self.positions[p] = index+1
            response = self.scripted[p][index]
            if isinstance(response, Exception):
                raise response
            if callable(response):
                response = response(request)
            return response if isinstance(response, ModelResponse) else ModelResponse(deepcopy(response))
        if p in ("judgment", "adversarial_judgment"):
            return ModelResponse(judgment_fixture(c["dimensions"], confidence=self.confidence))
        if p == "comparison":
            same = c["candidates"]["A"] == c["candidates"]["B"]
            return ModelResponse({"preferred": "TIE" if same else "B",
                "dimensions": {d: "TIE" if same else "B" for d in c["dimensions"]},
                "delta": {d: 0 if same else .05 for d in c["dimensions"]},
                "reason": "Deterministic fixture preference, not empirical performance evidence"})
        if p == "adversarial_tests":
            return ModelResponse({"tests": [{"target": c["claims"][0]["claim_id"] if c["claims"] else "candidate",
                "scenario": "Introduce a partial failure while recovery is in progress.",
                "expected_property": "The stated safety invariant remains satisfied.", "execution_status": "UNEXECUTED"}]})
        raise ValueError(f"Unknown judge purpose: {p}")
