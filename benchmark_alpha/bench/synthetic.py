"""SYNTHETIC BENCHMARK INFRASTRUCTURE TEST fixtures.

A scripted model returns fixed answers per (task, condition) so that the benchmark pipeline (conditions, real END
Engine, external evaluators, analysis, archive, reports) can be validated offline. These scripts decide the outcomes;
they are NOT evidence that END (or any model) works or fails."""
import json

from end_engine.models.base import ModelProvider, ModelResponse
from end_engine.models.mock import MockProvider
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture

from .providers import JUDGE_PURPOSES, render

LABEL = "SYNTHETIC BENCHMARK INFRASTRUCTURE TEST"


def J(obj):
    return "Final answer:\n```json\n" + json.dumps(obj) + "\n```"


def P(code):
    return "Here is the function.\n```python\n" + code.strip("\n") + "\n```"


A = {  # (correct, wrong) answer texts per task
    "BA-001": (J([-40.0, 32.0, 97.9, 212.0, 70.7]), J([-40.0, 32.0, 97.8, 212.0, 70.7])),
    "BA-002": (P("def chunk(items, size):\n    if not isinstance(size, int) or size <= 0:\n        raise ValueError('size')\n"
                 "    return [items[i:i + size] for i in range(0, len(items), size)]"),
               P("def chunk(items, size):\n    result = []\n    for i in range(0, len(items) - size, size):\n"
                 "        result.append(items[i:i + size])\n    return result")),
    "BA-003": (P("import heapq\ndef min_rooms(meetings):\n    ends = []\n    for s, e in sorted(meetings):\n"
                 "        if ends and ends[0] <= s:\n            heapq.heapreplace(ends, e)\n        else:\n"
                 "            heapq.heappush(ends, e)\n    return len(ends)"),
               P("def min_rooms(meetings):\n    return len(meetings)")),
    "BA-004": (J({"A": 0, "B": 0, "C": 2, "D": 3, "E": 4}), J({"A": 0, "B": 0, "C": 2, "D": 1, "E": 3})),
    "BA-005": (J({"first": "E2", "last": "E1", "elapsed_minutes": 30}), J({"first": "E1", "last": "E2", "elapsed_minutes": 330})),
    "BA-007": (J({"corrupting_write": "W1_at_19", "prevention": "fencing_token_checked_by_storage",
                  "w1_after_rejection": "abandon_and_discard_result", "w2_retry_on_timeout": "safe_if_idempotent_with_same_token",
                  "explanation": "Storage must reject the stale token."}),
               J({"corrupting_write": "W1_at_19", "prevention": "w1_checks_lease_before_writing",
                  "w1_after_rejection": "retry_write", "w2_retry_on_timeout": "always_safe", "explanation": "Check first."})),
    "BA-009": (J({"conclusion": "Unknown; the deploy at 13:58 is a hypothesis.", "certainty": "hypothesis",
                  "evidence_used": ["E1"], "additional_evidence_needed": ["database metrics", "traces"]}),
               J({"conclusion": "The database caused it; both engineers agree.", "certainty": "established",
                  "evidence_used": ["E2"], "additional_evidence_needed": []})),
    "BA-010": (J({"conclusion": "Unresolved: E1 reports PASSED but E2 reports FAILED for the same commit.",
                  "certainty": "unknown", "evidence_used": ["E1", "E2"],
                  "additional_evidence_needed": ["rerun test_empty_config on a1b2c3d"]}),
               J({"conclusion": "Yes, QA passed so it works.", "certainty": "established", "evidence_used": ["E1"],
                  "additional_evidence_needed": []})),
    "BA-011": (J({"conclusion": "No. The test covered 100 req/s, one region, read-only traffic; it cannot support that promise.",
                  "certainty": "established", "evidence_used": ["E1"],
                  "additional_evidence_needed": ["5,000 req/s, 3-region, mixed read/write load test"]}),
               J({"conclusion": "Yes, we can promise it: the load test passed with p99 120 ms.", "certainty": "established",
                  "evidence_used": ["E1"], "additional_evidence_needed": []})),
    "BA-012": (P("def is_palindrome(s):\n    return s == s[::-1]"),
               P("def is_palindrome(s):\n    t = ''.join(ch.lower() for ch in s if ch.isalnum())\n    return t == t[::-1]")),
}
FABRICATED_BA009 = J({"conclusion": "Probably the deploy.", "certainty": "likely", "evidence_used": ["E1", "E3"],
                      "additional_evidence_needed": ["traces"]})
EXECUTION_CLAIM_BA002 = A["BA-002"][0] + "\n\nI ran the tests and all tests pass."

# Scenario per task: condition -> script. END scripts: candidate contents, per-candidate adversarial verdict (FULL_END),
# verifier pass flag. "ok"/"bad" select the correct/wrong answer text.
SCENARIOS = {
    "BA-001": {"purpose": "DIRECT wins", "DIRECT": "ok", "SELF_REFLECT": ["ok", "bad"], "END_LITE": {"contents": ["bad"]},
               "FULL_END": {"contents": ["bad"]}},
    "BA-005": {"purpose": "SELF_REFLECT wins", "DIRECT": "bad", "SELF_REFLECT": ["bad", "ok"],
               "END_LITE": {"contents": ["bad"]}, "FULL_END": {"contents": ["bad"]}},
    "BA-004": {"purpose": "END wins", "DIRECT": "bad", "SELF_REFLECT": ["bad", "bad"],
               "END_LITE": {"contents": ["bad", "ok"]}, "FULL_END": {"contents": ["bad", "ok"]}},
    "BA-012": {"purpose": "END overthinks (C0 correct, later candidate normalizes)", "DIRECT": "ok",
               "SELF_REFLECT": ["ok", "ok"], "END_LITE": {"contents": ["ok", "bad"]}, "FULL_END": {"contents": ["ok", "bad"]}},
    "BA-003": {"purpose": "QualityGate false accept", "DIRECT": "ok", "SELF_REFLECT": ["ok", "ok"],
               "END_LITE": {"contents": ["bad"]}, "FULL_END": {"contents": ["bad"]}},
    "BA-002": {"purpose": "rollback saves a run; false execution claim", "DIRECT": EXECUTION_CLAIM_BA002,
               "SELF_REFLECT": ["ok", "ok"], "END_LITE": {"contents": ["ok"]},
               "FULL_END": {"contents": ["ok", "bad"], "adversarial": ["pass", "fatal"]}},
    "BA-007": {"purpose": "rollback hurts a run", "DIRECT": "bad", "SELF_REFLECT": ["bad", "bad"],
               "END_LITE": {"contents": ["bad"]},
               "FULL_END": {"contents": ["bad", "ok", "bad"], "adversarial": ["pass", "fatal", "pass"]}},
    "BA-011": {"purpose": "narrow evidence overgeneralized", "DIRECT": "bad", "SELF_REFLECT": ["bad", "ok"],
               "END_LITE": {"contents": ["bad"]}, "FULL_END": {"contents": ["bad"]}},
    "BA-009": {"purpose": "model agreement without evidence; fabricated evidence ID", "DIRECT": "bad",
               "SELF_REFLECT": ["bad", FABRICATED_BA009], "END_LITE": {"contents": ["ok"]}, "FULL_END": {"contents": ["bad"]}},
    "BA-010": {"purpose": "contradictory evidence: preserved vs ignored", "DIRECT": "bad", "SELF_REFLECT": ["bad", "ok"],
               "END_LITE": {"contents": ["ok"]}, "FULL_END": {"contents": ["ok"]}},
}


def text_for(task_id, choice):
    return A[task_id][0] if choice == "ok" else A[task_id][1] if choice == "bad" else choice


class SyntheticModel(ModelProvider):
    def __init__(self, task_id, condition, log, *, usage=True):
        self.task_id, self.condition, self.log, self.usage = task_id, condition, log, usage
        self.script = SCENARIOS[task_id][condition]
        self.counts, self.mock, self.judge = {}, MockProvider(), MockJudgeProvider()

    def metadata(self):
        return {"provider": "synthetic-scripted", "model": "synthetic-fixture", "data_origin": "SYNTHETIC", "label": LABEL}

    def _log(self, request, content, structured):
        prompt, out = len(render(request)) // 4, len(content if isinstance(content, str) else json.dumps(content)) // 4
        self.log.add(role=JUDGE_PURPOSES.get(request.purpose, "generator"), purpose=request.purpose, structured=structured,
                     attempt=1, seed=None, status="ok", done_reason="stop", latency_ms=0.0,
                     input_tokens=prompt if self.usage else None, output_tokens=out if self.usage else None)
        return ModelResponse(content, {"input_tokens": prompt, "output_tokens": out} if self.usage else None)

    def generate(self, request):
        n = self.counts[request.purpose] = self.counts.get(request.purpose, 0) + 1
        if request.purpose == "direct_answer":
            return self._log(request, text_for(self.task_id, self.script), False)
        if request.purpose == "self_reflect_initial":
            return self._log(request, text_for(self.task_id, self.script[0]), False)
        if request.purpose == "self_reflect_critique":
            return self._log(request, "SYNTHETIC critique.", False)
        if request.purpose == "self_reflect_revision":
            return self._log(request, text_for(self.task_id, self.script[1]), False)
        raise ValueError(f"unscripted text purpose {request.purpose} (call {n})")

    def generate_structured(self, request):
        p, c = request.purpose, request.context
        n = self.counts[p] = self.counts.get(p, 0) + 1
        contents = self.script["contents"]
        if p in ("initial_candidate", "revision"):
            index = 0 if p == "initial_candidate" else n
            data = {"content": text_for(self.task_id, contents[min(index, len(contents) - 1)]), "known_strengths": [],
                    "confidence": None}
        elif p == "verification":
            data = {"passed": True, "score": .95, "dimensions": {d: .95 for d in c["dimensions"]}, "remaining_issues": [],
                    "weakness_updates": []}
        elif p == "critique":
            data = {"summary": "SYNTHETIC critique", "findings": []}
        elif p == "revision_plan":
            data = {"changes": []}
        elif p == "adversarial_judgment":
            verdicts = self.script.get("adversarial", [])
            fatal = n - 1 < len(verdicts) and verdicts[n - 1] == "fatal"
            data = judgment_fixture(c["dimensions"], verdict="FAIL" if fatal else "PASS", score=.2 if fatal else .9,
                                    fatal=fatal, issues=[{"category": "constraint_violation", "description":
                                                          "SYNTHETIC fatal objection", "target": "candidate", "fatal": True,
                                                          "evidence": []}] if fatal else [])
        elif p in JUDGE_PURPOSES:
            data = self.judge.evaluate(request).content
        else:
            data = self.mock.generate_structured(request).content
        return self._log(request, data, True)


def factory(*, usage=True):
    def make(log, trial_seed, task, condition, trial):
        return SyntheticModel(task["task_id"], condition, log, usage=usage)
    return make
