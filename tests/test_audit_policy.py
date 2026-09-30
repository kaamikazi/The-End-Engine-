"""Audit-policy regressions (v0.3.1). All providers here are SYNTHETIC offline fixtures; the recorded fragment is an
explicitly labelled OFFLINE REPLAY of audit inputs from a Harness smoke run. No live model is called."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.core.state import Candidate, VerificationResult, now, to_data
from end_engine.quality.audits import ResolutionAuditor
from end_engine.quality.gate import QualityGate
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.quality.state import DimensionJudgment, EvidenceArtifact, GateDecision, JudgeIssue, Judgment, Verdict
from end_engine.verification import CallableToolVerifier, ToolCheck

FIXTURE = Path(__file__).with_name("fixtures") / "recorded_71532008_audit.json"
CONCERN = ("Resource capacity and horizon are untested guarantees under the declared checks, although the candidate "
           "satisfies both on direct inspection.")
JUSTIFICATION = ("Direct trace confirms capacity and horizon hold for this exact schedule; the missing automated coverage "
                 "is external to the answer artifact, which cannot add checks.")
SCHEDULE = '{"starts":[{"job":"A","start":8},{"job":"B","start":0}]}'


def judgment(identity="J1", *, adversarial=False, verdict=Verdict.PASS, action="ACCEPT", major=(), candidate_id="C1"):
    return Judgment(identity, candidate_id, "adversarial" if adversarial else "primary", verdict,
                    (("correctness", DimensionJudgment(.95, .95)),), major_issues=tuple(major),
                    recommended_action=action, adversarial=adversarial)


def record(status="accepted_risk", reason=JUSTIFICATION, severity="low", *, changed=False, description=CONCERN):
    c0 = {"candidate_id": "C0", "parent_candidate_id": None, "iteration": 0, "content": SCHEDULE}
    c1 = {**c0, "candidate_id": "C1", "parent_candidate_id": "C0", "iteration": 1,
          "content": SCHEDULE.replace("8", "7") if changed else SCHEDULE}
    after = {"id": "W001", "type": "untested_guarantee", "severity": severity, "description": description,
             "status": status, "status_reason": reason}
    return {"candidates": [c0, c1], "revision_plans": [{"candidate_id": "C0", "changes": [
                {"targets": ["W001"], "action": "Add explicit verification", "expected_effect": "Covers the concern"}]}],
            "steps": [{"type": "candidate", "step": 0, "data": c1},
                      {"type": "weakness_status_change", "step": 1, "data": {"before": {**after, "status": "open"}, "after": after}}]}


def c1():
    return Candidate("C1", "C0", 1, SCHEDULE, now())


PASSING = (judgment("J1"), judgment("AJ1", adversarial=True))
DEV_PASS = (EvidenceArtifact("E1", "C1", "EXECUTED_EVIDENCE", "harness:receipt", True, "Declared development subset", ("CL001",)),)


def audit(rec=None, judgments=PASSING, evidence=DEV_PASS):
    return ResolutionAuditor().audit(rec or record(), c1(), evidence, judgments=judgments)[0]


def gate(audits, *, evidence=DEV_PASS, independent=True):
    return QualityGate().evaluate(candidate_id="C1", verification=VerificationResult(True, .99, (("correctness", .99),), ()),
        judgments=(judgment("J1"),), adversarial=(judgment("AJ1", adversarial=True),), audits=audits,
        evidence=evidence, independent=independent)


class RiskAcceptanceCriteriaTests(unittest.TestCase):
    def test_reported_low_concern_on_unchanged_candidate_is_weakly_supported_never_verified(self):
        result = audit()
        self.assertEqual(result.status, "WEAKLY_SUPPORTED")
        self.assertEqual((result.transition, result.corroborating_judgments, result.criteria_gaps), ("accepted_risk", ("J1", "AJ1"), ()))
        self.assertEqual(result.supporting_artifacts, ())  # Model corroboration is never executed evidence.
        decision = gate((result,))
        self.assertEqual(decision.decision, GateDecision.ACCEPT_PROVISIONALLY)
        self.assertIn("Accepted risks remain unverified: W001", decision.reasons)
        self.assertIn("Status transitions have only model-based support", decision.reasons)

    def test_empty_short_or_restating_justification_is_rejected(self):
        for reason in ("", "Accepted.", "   " * 30, CONCERN):
            result = audit(record(reason=reason))
            self.assertEqual(result.status, "INVALID", reason)
            self.assertIn("justification is missing, too short, or only restates the concern", result.criteria_gaps)
            self.assertEqual(gate((result,)).decision, GateDecision.REVISE)

    def test_uncorroborated_or_contradicted_risk_acceptance_is_rejected(self):
        objection = JudgeIssue("constraint", "Capacity is exceeded at t=3")
        cases = {
            "independent judgments do not corroborate acceptance": (
                (judgment("J1"), judgment("AJ1", adversarial=True, verdict=Verdict.NEEDS_REVISION, action="REVISE", major=(objection,))), DEV_PASS),
            "independent and adversarial judgments of this candidate are required": ((judgment("J1"),), DEV_PASS),
            "executed evidence for this candidate failed": (PASSING, (EvidenceArtifact(
                "E2", "C1", "EXECUTED_EVIDENCE", "harness:receipt", False, "Declared development subset", ("CL001",)),)),
        }
        for gap, (judgments, evidence) in cases.items():
            result = audit(judgments=judgments, evidence=evidence)
            self.assertEqual(result.status, "INVALID", gap)
            self.assertIn(gap, result.criteria_gaps)
        other_candidate = (judgment("J9", candidate_id="C0"), judgment("AJ9", adversarial=True, candidate_id="C0"))
        self.assertEqual(audit(judgments=other_candidate).status, "INVALID")

    def test_high_or_critical_concern_cannot_be_accepted_without_revision_or_evidence(self):
        for severity in ("high", "critical"):
            result = audit(record(severity=severity))
            self.assertEqual(result.status, "INVALID")
            self.assertIn(f"severity {severity} requires a targeted revision or executed evidence", result.criteria_gaps)

    def test_resolution_claims_and_evidence_rules_are_unchanged(self):
        self.assertEqual(audit(record(status="resolved")).status, "INVALID")
        targeted = EvidenceArtifact("E3", "C1", "EXECUTED_EVIDENCE", "harness:receipt", True, "Capacity check", ("W001",))
        valid = audit(record(status="resolved"), evidence=(targeted,))
        self.assertEqual(valid.status, "VALID")
        self.assertEqual(audit(record(status="resolved", changed=True)).status, "WEAKLY_SUPPORTED")
        verified = gate((valid,), evidence=(targeted,))
        self.assertEqual(verified.decision, GateDecision.ACCEPT_VERIFIED)
        # An accepted risk stays an unverified concern even when targeted executed evidence exists.
        risk = audit(record(), evidence=(targeted,))
        self.assertEqual(risk.status, "VALID")
        self.assertEqual(gate((risk,), evidence=(targeted,)).decision, GateDecision.ACCEPT_PROVISIONALLY)


class RecordedFragmentReplayTests(unittest.TestCase):
    """OFFLINE REPLAY of the audit inputs recorded in Harness smoke 71532008; no model call."""
    def test_recorded_transition_now_audits_as_weakly_supported_risk(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertIn("OFFLINE REPLAY FRAGMENT", data["_label"])
        self.assertEqual(data["recorded_audit"]["status"], "INVALID")  # What Engine 0.3.0 recorded.
        self.assertEqual(data["candidates"][0]["content"], data["candidates"][1]["content"])
        judgments = tuple(Judgment(j["judgment_id"], j["candidate_id"], j["judge_id"], Verdict(j["verdict"]),
            tuple((d, DimensionJudgment(**v)) for d, v in j["dimensions"].items()),
            major_issues=tuple(JudgeIssue(**{**i, "evidence": tuple(i["evidence"])}) for i in j["major_issues"]),
            fatal_issues=tuple(JudgeIssue(**{**i, "evidence": tuple(i["evidence"])}) for i in j["fatal_issues"]),
            uncertainties=tuple(j["uncertainties"]), evidence=tuple(j["evidence"]),
            recommended_action=j["recommended_action"], adversarial=j["adversarial"]) for j in data["c1_judgments"])
        evidence = tuple(EvidenceArtifact(e["artifact_id"], e["candidate_id"], e["evidence_type"], e["source"], e["passed"],
                                          e["description"], tuple(e["targets"])) for e in data["c1_evidence"])
        rec = {"candidates": data["candidates"], "revision_plans": data["revision_plans"], "steps": data["steps"]}
        candidate = Candidate(**{k: data["candidates"][1][k] for k in ("candidate_id", "parent_candidate_id", "iteration",
                                                                     "content", "created_at")})
        result = ResolutionAuditor().audit(rec, candidate, evidence, judgments=judgments)[0]
        self.assertEqual((result.target_id, result.status, result.transition), ("W001", "WEAKLY_SUPPORTED", "accepted_risk"))
        self.assertEqual(result.corroborating_judgments, ("J002", "AJ002"))
        decision = QualityGate().evaluate(candidate_id="C1", verification=VerificationResult(True, 1.0, (("correctness", 1.0),), ()),
            judgments=judgments[:1], adversarial=judgments[1:], audits=(result,), evidence=evidence, independent=False)
        self.assertEqual(decision.decision, GateDecision.ACCEPT_PROVISIONALLY)
        self.assertIn("Generator and judge share model identity", decision.reasons)
        self.assertIn("Accepted risks remain unverified: W001", decision.reasons)


class ReportedScenarioGenerator(MockProvider):
    """SYNTHETIC reconstruction of the reported pattern: correct C0, one low-severity coverage concern, an unchanged
    revision, and a verifier status update chosen by each test."""
    def __init__(self, *, severity="low", update_reason=JUSTIFICATION, update_status="accepted_risk", assumption_risk=None):
        super().__init__()
        self.severity, self.update_reason, self.update_status = severity, update_reason, update_status
        self.assumption_risk = assumption_risk
        self.critiques = self.verifications = 0

    def generate_structured(self, request):
        c, p = request.context, request.purpose
        if p in ("initial_candidate", "revision"):
            return ModelResponse({"content": SCHEDULE, "known_strengths": [], "confidence": None})
        if p == "verification":
            self.verifications += 1
            updates = [{"id": "W001", "status": self.update_status, "reason": self.update_reason}] \
                if self.verifications == 2 and self.update_status else []
            return ModelResponse({"passed": True, "score": .99, "dimensions": {d: .99 for d in c["dimensions"]},
                                  "remaining_issues": [], "weakness_updates": updates})
        if p == "critique":
            self.critiques += 1
            findings = [{"weakness_id": None, "type": "untested_guarantee", "severity": self.severity,
                         "description": CONCERN, "evidence": "Declared checks omit capacity and horizon"}] if self.critiques == 1 else []
            output = {"summary": "Coverage concern only", "findings": findings}
            if self.assumption_risk and self.critiques == 1:
                # An unsupported model claim that an assumption is SUPPORTED, with no revision or executed evidence.
                output.update(assumptions=[{"statement": "Job durations are exact integers", "risk": self.assumption_risk,
                                            "status": "UNTESTED", "evidence": "Stated in the task input"}],
                              assumption_updates=[{"id": "A001", "status": "SUPPORTED", "evidence": "The model restates it"}])
            return ModelResponse(output)
        if p == "revision_plan":
            return ModelResponse({"changes": [{"targets": ["W001"], "action": "Add explicit verification",
                                               "expected_effect": "Covers capacity and horizon"}]})
        return super().generate_structured(request)


class SameModelJudge(MockJudgeProvider):
    """SYNTHETIC judge sharing the generator identity, as in the recorded run, so C0 is only provisionally accepted."""
    def for_run(self):
        return SameModelJudge(scripted=self.scripted, model=self.model, confidence=self.confidence)

    def metadata(self):
        return MockProvider().metadata()


class ReportedScenarioEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_engine(self, generator, judge=None):
        tool = CallableToolVerifier(lambda task, c, tests, claims: (ToolCheck(True, "Executed declared development subset"),))
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False), provider=generator,
                           judge_provider=judge or SameModelJudge(), tool_verifier=tool)
        result = engine.run("Schedule four jobs under capacity and horizon.", mode="normal", max_cycles=2)
        return result, engine.last_trajectory

    @staticmethod
    def gate_for(record, identity):
        return next(g for g in record["quality_gate_decisions"] if g["candidate_id"] == identity)

    @staticmethod
    def open_weaknesses_seen(record):
        return {(w["id"], w["severity"], w["status"]) for s in record["cognitive_states"] for w in s["open_weaknesses"]}

    def test_justified_low_risk_ends_after_mandatory_cycle_without_severity_inflation(self):
        result, record = self.run_engine(ReportedScenarioGenerator())
        self.assertEqual([c["content"] for c in record["candidates"]], [SCHEDULE, SCHEDULE])  # Mandatory cycle ran once.
        self.assertEqual(self.gate_for(record, "C0")["decision"], "ACCEPT_PROVISIONALLY")
        c1_gate = self.gate_for(record, "C1")
        self.assertEqual(c1_gate["decision"], "ACCEPT_PROVISIONALLY")
        self.assertIn("Accepted risks remain unverified: W001", c1_gate["reasons"])
        self.assertIn("Status transitions have only model-based support", c1_gate["reasons"])
        self.assertEqual((result.quality_gate, result.termination_reason.value), ("ACCEPT_PROVISIONALLY", "ACCEPTED_PROVISIONALLY"))
        self.assertEqual(len(record["model_calls"]), 13)  # Engine 0.3.0 needed 22 here and started a second cycle.
        change = next(s["data"] for s in record["steps"] if s["type"] == "weakness_status_change")
        self.assertEqual((change["after"]["severity"], change["after"]["status"]), ("low", "accepted_risk"))
        audit = record["resolution_audits"][-1]
        self.assertEqual((audit["status"], audit["transition"], audit["supporting_artifacts"]), ("WEAKLY_SUPPORTED", "accepted_risk", []))
        self.assertTrue(audit["corroborating_judgments"])
        self.assertEqual(record["judge_feedback"], [])
        self.assertTrue(all(not s["high_severity_weaknesses"] for s in record["cognitive_states"]))

    def test_empty_justification_keeps_concern_open_at_its_severity(self):
        _, record = self.run_engine(ReportedScenarioGenerator(update_reason="Accepted."))
        c1_gate = self.gate_for(record, "C1")
        self.assertEqual(c1_gate["decision"], "REVISE")
        self.assertIn("Risk acceptance does not meet criteria", c1_gate["reasons"][0])
        self.assertNotIn("Unresolved high-severity weaknesses remain", c1_gate["reasons"])
        failure = next(s["data"] for s in record["steps"] if s["type"] == "audit_failure")
        self.assertEqual((failure["target_id"], failure["action"], failure["retained_severity"], failure["new_weakness_created"]),
                         ("W001", "reopened", "low", False))
        revert = next(s["data"] for s in record["steps"] if s["type"] == "weakness_status_change" and s["data"].get("source"))
        self.assertEqual((revert["source"], revert["before"]["status"], revert["after"]["status"], revert["after"]["severity"]),
                         ("resolution_audit", "accepted_risk", "open", "low"))
        self.assertIn("rejected by audit", revert["after"]["status_reason"])
        self.assertEqual(self.open_weaknesses_seen(record), {("W001", "low", "open")})  # Unresolved; no meta-weakness.
        self.assertEqual(record["judge_feedback"], [])
        self.assertTrue(all(not s["high_severity_weaknesses"] for s in record["cognitive_states"]))
        self.assertEqual(record["trajectory_judgments"][1]["resolution_integrity"], "LOW")
        self.assertEqual([a["status"] for a in record["resolution_audits"]], ["INVALID"])  # Visible once, not re-reported.
        later = [g for g in record["quality_gate_decisions"] if g["candidate_id"] not in ("C0", "C1")]
        self.assertTrue(later and all("Accepted risks remain unverified: W001" not in g["reasons"] for g in later))

    def test_genuine_high_severity_concern_still_escalates_and_remains_unresolved(self):
        result, record = self.run_engine(ReportedScenarioGenerator(severity="high"))
        c1_gate = self.gate_for(record, "C1")
        self.assertEqual(c1_gate["decision"], "REVISE")
        self.assertIn("Unresolved high-severity weaknesses remain", c1_gate["reasons"])
        self.assertIn("severity high requires a targeted revision or executed evidence", c1_gate["reasons"][0])
        self.assertEqual(self.open_weaknesses_seen(record), {("W001", "high", "open")})
        self.assertIn("W001", next(s for s in record["cognitive_states"] if s["high_severity_weaknesses"])["high_severity_weaknesses"])
        self.assertGreater(len(record["candidates"]), 2)  # Escalation still drives a further revision cycle.
        self.assertEqual(self.gate_for(record, "C2")["decision"], "REVISE")
        self.assertEqual(result.termination_reason.value, "BUDGET_EXHAUSTED")  # Engine-native cycle cap, not a blocker.

    def test_unsupported_assumption_transition_resets_without_severity_inflation(self):
        for risk, severe in (("LOW", False), ("HIGH", True)):
            _, record = self.run_engine(ReportedScenarioGenerator(assumption_risk=risk))
            audits = [a for a in record["assumption_audits"] if a["target_id"] == "A001"]
            self.assertEqual([a["status"] for a in audits], ["INVALID"], risk)
            failure = next(s["data"] for s in record["steps"] if s["type"] == "audit_failure" and s["data"]["kind"] == "assumption")
            self.assertEqual((failure["action"], failure["retained_severity"], failure["new_weakness_created"]),
                             ("reset_to_untested", risk, False))
            reset = [s["data"] for s in record["steps"] if s["type"] == "assumption_status_change"][-1]
            self.assertEqual((reset["before"]["status"], reset["after"]["status"]), ("SUPPORTED", "UNTESTED"))
            self.assertIn("rejected by audit", reset["after"]["evidence"])
            self.assertEqual(record["judge_feedback"], [])
            c1_gate = self.gate_for(record, "C1")
            self.assertEqual(c1_gate["decision"], "REVISE")
            self.assertNotIn("Unresolved high-severity weaknesses remain", c1_gate["reasons"])
            self.assertEqual("Severe assumptions remain untested" in c1_gate["reasons"], severe, risk)

    def test_existing_verified_acceptance_and_rollback_are_unchanged(self):
        from end_engine.models.deployment_mock import (CANDIDATES, DEPLOYMENT_TASK, DeploymentJudgeProvider,
                                                      DeploymentMockProvider, deployment_tool_verifier)
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False, post_acceptance_cycles=1),
                           provider=DeploymentMockProvider(), judge_provider=DeploymentJudgeProvider(),
                           tool_verifier=deployment_tool_verifier())
        result = engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=4)
        record = engine.last_trajectory
        self.assertEqual((result.best_candidate_id, result.latest_candidate_id, result.answer), ("C3", "C4", CANDIDATES[3]))
        self.assertEqual(record["rollback_events"][-1]["to_candidate"], "C3")
        self.assertEqual(result.quality_gate, "ACCEPT_VERIFIED")

    def test_judge_major_issue_still_becomes_high_candidate_weakness(self):
        def objection(request):
            data = judgment_fixture(request.context["dimensions"], verdict="NEEDS_REVISION", score=.5,
                                    issues=[{"category": "constraint", "description": "Capacity exceeded at t=3",
                                             "target": "candidate", "fatal": False, "evidence": []}])
            return data
        judge = SameModelJudge(scripted={"adversarial_judgment": [objection] * 10})
        result, record = self.run_engine(ReportedScenarioGenerator(), judge=judge)
        feedback = [w for w in record["weaknesses"] if w["description"] == "Capacity exceeded at t=3"]
        self.assertTrue(feedback and all(w["severity"] == "high" for w in feedback))
        self.assertNotIn(result.quality_gate, ("ACCEPT_PROVISIONALLY", "ACCEPT_VERIFIED"))
