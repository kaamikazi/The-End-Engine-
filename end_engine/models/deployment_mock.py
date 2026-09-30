"""Deterministic generator/judge fixtures plus an actually executed, bounded simulator.
No deployment, network, subprocess, or generated-code execution is performed.
"""
from itertools import permutations

from .mock import MockProvider
from .base import ModelResponse
from ..quality.mock import MockJudgeProvider, judgment_fixture
from ..verification.tool_verifier import CallableToolVerifier, ToolCheck


DEPLOYMENT_TASK = "Design a deployment controller that can automatically roll out a new service version while preventing a faulty release from causing a large-scale outage."
INVARIANT = "A rollout must preserve a healthy serving version."
CANDIDATES = (
    INVARIANT + " Apply the new version to all workers after a single successful health probe.",
    INVARIANT + " Use a bounded canary and pause promotion on delayed error signals. Add automatic rollback on failures.",
    INVARIANT + " Use a bounded canary and pause promotion on delayed error signals. Add automatic rollback on failures. "
    "Retire the previous pool when rollback starts, then restore the earlier version.",
    INVARIANT + " Use a bounded canary and pause promotion on delayed error signals. "
    "Retain the last healthy pool until rollback completes. Fence rollback by deployment epoch. "
    "Serialize promotion with rollback. Reject stale completion events. "
    "Check delayed failures and every ordering of retry, stale completion, and rollback completion in a bounded abstract model. "
    "Require production-specific validation before deployment; the abstract model covers only its encoded invariants.",
    INVARIANT + " Use a bounded canary. For elegant fast rollback, retire the previous pool when rollback starts. "
    "This concise workflow replaces the detailed fencing and recovery protocol.",
)


def rollback_model(content):
    """Six adversarial orderings of a deliberately small recovery-state machine."""
    text = content.lower()
    retain = "retain the last healthy pool until rollback completes" in text
    fenced = "fence rollback by deployment epoch" in text
    serialized = "serialize promotion with rollback" in text
    failures = []
    for events in permutations(("retry", "stale_completion", "rollback_complete")):
        healthy, rolling_back, epoch = retain, True, 2
        for event in events:
            if event == "stale_completion" and not fenced:
                healthy = False  # An obsolete rollout incorrectly routes traffic to the bad pool.
            elif event == "retry" and rolling_back and not serialized:
                healthy = False
            elif event == "rollback_complete":
                rolling_back = False
            if not healthy:
                failures.append({"events": events, "failed_at": event, "epoch": epoch})
                break
    return {"passed": not failures, "orderings": 6, "failures": failures}


class DeploymentMockProvider(MockProvider):
    def metadata(self):
        return {"provider": "mock-generator", "model": "deployment-fixture-v3", "offline": True}

    def generate_structured(self, request):
        if request.purpose in self.scripted:
            return super().generate_structured(request)
        c, purpose = request.context, request.purpose
        if purpose in ("initial_candidate", "revision"):
            index = min(c["iteration"], 4)
            return ModelResponse({"content": CANDIDATES[index], "known_strengths": ["Explicit rollout proposal"], "confidence": None})
        if purpose == "critique":
            target = c.get("question", {}).get("target", {}).get("target_id")
            weakness = next((w for w in c["weaknesses"] if w["id"] == target), None)
            findings = [{"weakness_id": weakness["id"], "type": weakness["type"], "severity": weakness["severity"],
                         "description": weakness["description"], "evidence": "Targeted review confirms this independent-judge concern."}] if weakness else []
            return ModelResponse({"summary": "Investigate the selected rollout safety gap and state a corrective invariant.", "findings": findings})
        if purpose == "revision_plan":
            return ModelResponse({"changes": [{"targets": [w["id"]], "action": "Add canary limits, retained healthy capacity, epoch fencing and serialized recovery as applicable.",
                "expected_effect": "Prevent the specific judged failure while preserving the user's rollout objective."}
                for w in c["weaknesses"] if w["status"] == "open"]})
        if purpose == "verification":
            iteration = c["candidate"]["iteration"]
            # Deliberately optimistic verifier: high scores do not reveal the rollback race.
            score = (0.58, 0.78, 0.97, 0.98, 0.99)[min(iteration, 4)]
            return ModelResponse({"passed": iteration >= 2, "score": score, "dimensions": {d: score for d in c["dimensions"]},
                "remaining_issues": [] if iteration >= 2 else ["Complete the rollout failure analysis"],
                "weakness_updates": [{"id": w["id"], "status": "resolved",
                    "reason": "The revision contains the proposed corrective controls (optimistic model judgment)."}
                    for w in c["weaknesses"] if w["status"] == "open"]})
        return super().generate_structured(request)


class DeploymentJudgeProvider(MockJudgeProvider):
    def metadata(self):
        return {"provider": "independent-mock-judge", "model": "rollback-adversary-v3", "offline": True}

    def for_run(self):
        return DeploymentJudgeProvider()

    def evaluate(self, request):
        c, purpose = request.context, request.purpose
        if purpose in ("judgment", "adversarial_judgment"):
            content = c["candidate"]["content"]
            text = content.lower()
            safe = rollback_model(content)["passed"]
            issue = None
            fatal = "elegant fast rollback" in text
            if "bounded canary" not in text:
                issue = {"category": "assumption", "description": "A single health probe cannot exclude delayed or partial rollout failures.", "target": "candidate", "fatal": False, "evidence": []}
            elif purpose == "adversarial_judgment" and not safe:
                issue = {"category": "rollback_flaw", "description": "Rollback can retire the last healthy pool before recovery finishes, and stale completion can race with retry.",
                         "target": c["claims"][0]["claim_id"] if c["claims"] else "candidate", "fatal": fatal, "evidence": []}
            verdict = "FAIL" if fatal and issue else "NEEDS_REVISION" if issue else "PASS"
            result = judgment_fixture(c["dimensions"], verdict=verdict, score=0.4 if fatal else .7 if issue else .96,
                                      confidence=.95, issues=(issue,) if issue else (), fatal=fatal)
            return ModelResponse(result)
        if purpose == "comparison":
            a, b = c["candidates"]["A"], c["candidates"]["B"]
            good_a, good_b = rollback_model(a)["passed"], rollback_model(b)["passed"]
            regression = good_a and not good_b
            preferred = "A" if regression else "B"
            delta = {d: (-.5 if regression and d in ("correctness", "robustness", "constraint_adherence") else
                          .12 if regression and d == "clarity" else -.1 if regression else .22 if good_b else .08)
                     for d in c["dimensions"]}
            return ModelResponse({"preferred": preferred, "dimensions": {d: "B" if regression and d == "clarity" else preferred for d in c["dimensions"]},
                                  "delta": delta, "reason": "B removes retained healthy capacity and epoch fencing" if regression else
                                  "B adds substantive rollout protections; the safe proposal passes the bounded recovery model"})
        if purpose == "adversarial_tests":
            targets = [{"id": x["claim_id"]} for x in c["claims"]] + c.get("audit_targets", [])
            unique = tuple(dict.fromkeys(x["id"] for x in targets))[:4]
            return ModelResponse({"tests": [{"target": identity,
                "scenario": "Interleave stale completion, retry and rollback completion while the new release is faulty.",
                "expected_property": "A healthy serving pool remains available in every encoded event ordering.",
                "execution_status": "EXECUTABLE"} for identity in unique or ("candidate",)]})
        return super().evaluate(request)


def deployment_tool_verifier():
    def check(task, candidate, tests, claims):
        if "retire the previous" not in candidate.content.lower() and "retain the last healthy" not in candidate.content.lower():
            return ()  # Early sketches do not yet specify an executable abstract recovery policy.
        if "elegant fast rollback" not in candidate.content.lower() and "retain the last healthy" not in candidate.content.lower():
            return ()  # The adversarial review first identifies the missing invariant; execution follows correction.
        result = rollback_model(candidate.content)
        description = f"Executed abstract rollback model over {result['orderings']} event orderings; {len(result['failures'])} violated the serving invariant. No real deployment was executed."
        checks = [ToolCheck(result["passed"], description, (test.target,), test.test_id) for test in tests]
        return tuple(checks)
    return CallableToolVerifier(check, name="bounded_rollback_state_machine")
