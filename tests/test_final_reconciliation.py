"""Final-assessment reconciliation (v0.3.2). All providers are SYNTHETIC offline fixtures; no live model is called."""
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.verification import CallableToolVerifier, ToolCheck

A, B = '{"starts":[{"job":"A","start":8}]}', '{"starts":[{"job":"A","start":1}]}'
LONG = ("Direct trace confirms the stated limits hold for this exact schedule; the missing automated coverage is external "
        "to the answer artifact, which cannot add checks.")


def finding(severity, description="Capacity exceeded at t=3 for this schedule"):
    return {"weakness_id": None, "type": "constraint", "severity": severity, "description": description,
            "evidence": "Synthetic fixture finding"}


class Scripted(MockProvider):
    """SYNTHETIC generator: candidate contents, critique findings and verifier updates are scripted per call."""
    def __init__(self, contents, critiques=(), updates=None, fail=None):
        super().__init__()
        self.contents, self.critiques, self.updates, self.fail = list(contents), list(critiques), updates or {}, fail or {}
        self.counts = {}

    def generate_structured(self, request):
        c, p = request.context, request.purpose
        n = self.counts[p] = self.counts.get(p, 0) + 1
        if self.fail.get(p) == n:
            raise RuntimeError("model_attempts_exhausted")  # Stands in for an external request-budget stop.
        if p in ("initial_candidate", "revision"):
            index = 0 if p == "initial_candidate" else n
            return ModelResponse({"content": self.contents[min(index, len(self.contents) - 1)], "known_strengths": [],
                                  "confidence": None})
        if p == "verification":
            return ModelResponse({"passed": True, "score": .99, "dimensions": {d: .99 for d in c["dimensions"]},
                                  "remaining_issues": [], "weakness_updates": self.updates.get(n, [])})
        if p == "critique":
            return ModelResponse({"summary": "Scripted critique",
                                  "findings": self.critiques[n - 1] if n <= len(self.critiques) else []})
        if p == "revision_plan":
            return ModelResponse({"changes": []})
        return super().generate_structured(request)


class SameModelJudge(MockJudgeProvider):
    """SYNTHETIC judge sharing the generator identity, so candidate gates are provisional as in the recorded smoke."""
    def for_run(self):
        return SameModelJudge(scripted=self.scripted, model=self.model, confidence=self.confidence)

    def metadata(self):
        return MockProvider().metadata()


class DeclaredSubset:
    """SYNTHETIC trusted claim vocabulary; SCOPED checks target only this statement (v0.3.4: an executed check must
    cover a recorded claim or concern before it can support verified acceptance)."""
    def extract(self, candidate):
        return ("The declared development checks pass for this task input.",)


def scoped():
    return CallableToolVerifier(lambda task, c, tests, claims: (ToolCheck(True, "Executed declared subset",
                                                                          tuple(x.claim_id for x in claims)),))


def passing(request):
    return judgment_fixture(request.context["dimensions"])


def objecting(request):
    return judgment_fixture(request.context["dimensions"], verdict="NEEDS_REVISION", score=.5, issues=[
        {"category": "constraint", "description": "Judge objection under this candidate's evidence scope",
         "target": "candidate", "fatal": False, "evidence": []}])


class FinalReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_engine(self, generator, *, judge=None, tool=None, max_cycles=2, claim_extractor=None, **config):
        tool = tool or CallableToolVerifier(lambda task, c, tests, claims: (ToolCheck(True, "Executed declared subset"),))
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False, **config), provider=generator,
                           judge_provider=judge or SameModelJudge(), tool_verifier=tool, claim_extractor=claim_extractor)
        result = engine.run("Schedule jobs within capacity and horizon.", mode="normal", max_cycles=max_cycles)
        return result, engine.last_trajectory

    @staticmethod
    def gate(record, identity):
        return next(g for g in record["quality_gate_decisions"] if g["candidate_id"] == identity)

    def assert_no_reconciliation_calls(self, record):
        termination = next(s["step"] for s in record["steps"] if s["type"] == "termination")
        self.assertEqual(record["final_reconciliation"]["model_calls"], 0)
        self.assertTrue(all(s["step"] < termination for s in record["steps"] if s["type"] == "model_call"))

    def test_c0_restored_after_identical_c1_acquires_unresolved_high_concern(self):
        # C0 and C1 are identical; the post-acceptance critique of C1 finds a high defect; C2 differs and stays REVISE.
        result, record = self.run_engine(Scripted([A, A, B], critiques=[[], [finding("high")]]), post_acceptance_cycles=1)
        self.assertEqual((result.best_candidate_id, record["final_candidate_id"], result.answer), ("C0", "C0", A))
        self.assertEqual(self.gate(record, "C0")["decision"], "ACCEPT_PROVISIONALLY")  # Historical gate is immutable.
        self.assertEqual(result.quality_gate, "REVISE")
        self.assertNotIn(result.acceptance_label, ("ACCEPTED_PROVISIONAL", "ACCEPTED_HIGH_CONFIDENCE"))
        rec = record["final_reconciliation"]
        self.assertEqual((rec["changed"], rec["original_gate"]["decision"], rec["identical_content_candidates"]),
                         (True, "ACCEPT_PROVISIONALLY", ["C0", "C1"]))
        concern = rec["later_applicable_concerns"][0]
        self.assertEqual((concern["id"], concern["severity"], concern["status"], concern["provenance"]["candidate_id"]),
                         ("W001", "high", "open", "C1"))
        self.assertIn("Unresolved high-severity concern applicable to the returned content: W001",
                      rec["reconciled_gate"]["reasons"])
        self.assertIn(("W001", "high", "open"), [(w["id"], w["severity"], w["status"]) for w in record["weaknesses"]])
        self.assertIn("W001", record["cognitive_states"][-1]["high_severity_weaknesses"])
        self.assertIn({"id": "W001", "severity": "high", "status": "open"}, record["scorecard"]["unresolved_concerns"])
        self.assert_no_reconciliation_calls(record)

    def test_accepted_low_risk_stays_visible_and_blocks_verified_acceptance(self):
        # Independent judge: C0 is ACCEPT_VERIFIED at its own gate; identical C1 later validly accepts a low risk.
        generator = Scripted([A, A], critiques=[[finding("low", "Horizon is an untested guarantee")]],
                             updates={2: [{"id": "W001", "status": "accepted_risk", "reason": LONG}]})
        result, record = self.run_engine(generator, judge=MockJudgeProvider(), tool=scoped(), claim_extractor=DeclaredSubset())
        self.assertEqual((result.best_candidate_id, self.gate(record, "C0")["decision"]), ("C0", "ACCEPT_VERIFIED"))
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")
        self.assertNotEqual(result.acceptance_label, "ACCEPTED_HIGH_CONFIDENCE")
        rec = record["final_reconciliation"]
        self.assertIn("Accepted risks remain unverified: W001", rec["reconciled_gate"]["reasons"])
        self.assertEqual(rec["applied_transitions"][0]["audit"], "WEAKLY_SUPPORTED")  # Model support, not evidence.
        self.assertIn({"id": "W001", "severity": "low", "status": "accepted_risk"}, record["scorecard"]["unresolved_concerns"])

    def test_concern_validly_resolved_later_is_not_resurrected(self):
        def checks(task, candidate, tests, claims):
            if candidate.candidate_id == "C1":
                return (ToolCheck(True, "Executed capacity check on this exact schedule", ("W001",)),)
            return (ToolCheck(True, "Executed declared subset"),)
        generator = Scripted([A, A], critiques=[[finding("high")]],
                             updates={2: [{"id": "W001", "status": "resolved", "reason": "Executed capacity check passed"}]})
        result, record = self.run_engine(generator, tool=CallableToolVerifier(checks))
        rec = record["final_reconciliation"]
        self.assertEqual(rec["applied_transitions"][0]["audit"], "VALID")
        self.assertEqual({w["id"]: w["status"] for w in record["weaknesses"]}["W001"], "resolved")
        self.assertNotIn("REVISE", result.quality_gate)
        self.assertFalse(any("W001" in r for r in rec["reconciled_gate"]["reasons"]))
        self.assertEqual(record["cognitive_states"][-1]["high_severity_weaknesses"], [])

    def test_defect_only_in_different_candidate_does_not_contaminate_returned_candidate(self):
        # The judge objects only to C2, whose content differs; C0 remains the returned candidate unchanged.
        judge = SameModelJudge(scripted={"adversarial_judgment": [passing, passing, objecting, objecting]})
        result, record = self.run_engine(Scripted([A, A, B], critiques=[[], []]), judge=judge, post_acceptance_cycles=1)
        self.assertEqual(result.best_candidate_id, "C0")
        rec = record["final_reconciliation"]
        self.assertEqual((rec["changed"], rec["later_applicable_concerns"], rec["not_transferred"]), (False, [], []))
        self.assertEqual(result.quality_gate, self.gate(record, "C0")["decision"])
        self.assertTrue(any(f["candidate_id"] == "C2" for f in record["judge_feedback"]))
        self.assertEqual(record["weaknesses"], [])

    def test_candidate_specific_audit_failure_is_not_transferred(self):
        generator = Scripted([A, A], critiques=[[finding("low", "Horizon is an untested guarantee")]],
                             updates={2: [{"id": "W001", "status": "accepted_risk", "reason": "Accepted."}]})
        result, record = self.run_engine(generator)
        self.assertEqual(self.gate(record, "C1")["decision"], "REVISE")  # C1's own procedural failure.
        rec = record["final_reconciliation"]
        self.assertIn(("audit_failure", "C1"), [(n["kind"], n["candidate_id"]) for n in rec["not_transferred"]])
        self.assertEqual(rec["ignored_transitions"][0]["reason"], "rejected by audit")
        self.assertFalse(any("Risk acceptance does not meet criteria" in r for r in rec["reconciled_gate"]["reasons"]))
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")
        # The content concern itself stays visible and unresolved at its own severity.
        self.assertIn({"id": "W001", "severity": "low", "status": "open"}, record["scorecard"]["unresolved_concerns"])

    def test_judgment_of_identical_content_is_reported_as_undetermined_not_transferred(self):
        judge = MockJudgeProvider(scripted={"adversarial_judgment": [passing] + [objecting] * 6})
        result, record = self.run_engine(Scripted([A, A, A]), judge=judge, tool=scoped(), claim_extractor=DeclaredSubset())
        self.assertEqual(self.gate(record, "C0")["decision"], "ACCEPT_VERIFIED")
        rec = record["final_reconciliation"]
        self.assertTrue(rec["not_transferred"] and all(n["kind"] == "judge_feedback" for n in rec["not_transferred"]))
        self.assertTrue(any(r.startswith("Applicability undetermined") for r in rec["reconciled_gate"]["reasons"]))
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")
        self.assertEqual(record["cognitive_states"][-1]["high_severity_weaknesses"], [])

    def test_budget_exhaustion_keeps_its_cause_and_reports_applicable_concerns(self):
        # Cycle cap inside END: termination stays BUDGET_EXHAUSTED.
        result, record = self.run_engine(Scripted([A, A, A], critiques=[[finding("high")]]))
        self.assertEqual((result.termination_reason.value, result.quality_gate), ("BUDGET_EXHAUSTED", "REVISE"))
        self.assertIn({"id": "W001", "severity": "high", "status": "open"}, record["scorecard"]["unresolved_concerns"])
        # External request-budget stop (as the Harness raises): termination stays EXTERNAL_BLOCKER, gate BLOCKED.
        result, record = self.run_engine(Scripted([A, A, A], critiques=[[finding("high")]], fail={"revision_plan": 2}))
        self.assertEqual((result.termination_reason.value, result.quality_gate, result.acceptance_label),
                         ("EXTERNAL_BLOCKER", "BLOCKED", "INCOMPLETE"))
        reasons = record["scorecard"]["known_uncertainties"]
        self.assertIn("Execution failed before the quality process completed", reasons)
        self.assertIn("Unresolved high-severity concern applicable to the returned content: W001", reasons)
        self.assert_no_reconciliation_calls(record)

    def test_existing_acceptance_and_rollback_remain_intact(self):
        from end_engine.models.deployment_mock import (CANDIDATES, DEPLOYMENT_TASK, DeploymentJudgeProvider,
                                                      DeploymentMockProvider, deployment_tool_verifier)
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False, post_acceptance_cycles=1),
                           provider=DeploymentMockProvider(), judge_provider=DeploymentJudgeProvider(),
                           tool_verifier=deployment_tool_verifier())
        result = engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=4)
        record = engine.last_trajectory
        self.assertEqual((result.best_candidate_id, result.latest_candidate_id, result.answer), ("C3", "C4", CANDIDATES[3]))
        self.assertEqual(record["rollback_events"][-1]["to_candidate"], "C3")
        self.assertEqual((result.quality_gate, result.termination_reason.value), ("ACCEPT_VERIFIED", "ACCEPTED_VERIFIED"))
        rec = record["final_reconciliation"]  # C4's regression and judge findings do not touch C3.
        self.assertEqual((rec["changed"], rec["later_applicable_concerns"], rec["not_transferred"]), (False, [], []))
        self.assertEqual({w["id"]: w["status"] for w in record["weaknesses"]}, {"W001": "resolved", "W002": "resolved"})
