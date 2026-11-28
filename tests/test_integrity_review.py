"""Evidence-integrity review regressions (v0.3.4). Providers, checkers and evidence are SYNTHETIC offline fixtures;
no live model is called anywhere in this module."""
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, ModelResponse
from end_engine.quality.integrity import ENGINE_EVIDENCE_PREFIX, EvidenceIndex, EvidenceIntegrity, content_sha256
from end_engine.quality.audits import ClaimValidator
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.quality.state import CheckContract, GateDecision
from end_engine.verification import CallableToolVerifier, ToolCheck

from .test_evidence_integrity import CONTENT, NARROW, Contents, cand, check, claim, claim_of, evaluate, has_reason
from .test_final_reconciliation import Scripted

OTHER = "The rollback path is not applicable to this schedule."
COVERS_NOTHING = "Executed checks cover no recorded claim or concern"
IDENTICAL_CONFLICT = "Contradictory evidence or judgments on byte-identical content remain unresolved"
IDENTICAL_FAILURE = "A trusted check of byte-identical content failed"


class TrustedClaims:
    """SYNTHETIC trusted claim vocabulary (like the Harness CheckBinding): the texts come from configuration."""
    def __init__(self, *texts):
        self.texts = texts

    def extract(self, candidate):
        return self.texts


def targeted(extra=lambda candidate: (), *, passed=lambda candidate: True, contract=lambda candidate: None):
    """SYNTHETIC trusted checker: targets only the claim whose text is exactly the trusted statement."""
    return CallableToolVerifier(lambda task, c, tests, claims: (ToolCheck(passed(c), "SYNTHETIC precedence check",
        tuple(x.claim_id for x in claims if x.text == NARROW) + tuple(extra(c)), None, contract(c)),))


class Spoofer(Contents):
    """SYNTHETIC generator whose critique marks the OTHER claim NOT_APPLICABLE with the given evidence text."""
    def __init__(self, contents, evidence):
        super().__init__(contents)
        self.evidence = evidence

    def generate_structured(self, request):
        if request.purpose == "critique":
            claims = request.context["cognitive_context"]["claims"]
            return ModelResponse({"summary": "SYNTHETIC critique", "findings": [], "claim_updates": [
                {"id": c["claim_id"], "status": "NOT_APPLICABLE", "evidence": self.evidence}
                for c in claims if c["text"] == OTHER]})
        return super().generate_structured(request)


def adversary(*second):
    """SYNTHETIC adversarial judge: PASS for every candidate except the second one evaluated (C1)."""
    def first(request):
        return ModelResponse(judgment_fixture(request.context["dimensions"]))

    def c1(request):
        data = judgment_fixture(request.context["dimensions"])
        for update in second:
            data.update(update)
        return ModelResponse(data)
    return MockJudgeProvider(scripted={"adversarial_judgment": [first, c1, first, first]})


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_engine(self, generator, judge, tool, *claims, max_cycles=2, **config):
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False, **config), provider=generator,
                           judge_provider=judge, tool_verifier=tool, claim_extractor=TrustedClaims(*(claims or (NARROW,))))
        result = engine.run("Schedule jobs within capacity and horizon.", mode="normal", max_cycles=max_cycles)
        return result, engine.last_trajectory

    @staticmethod
    def gates(record):
        return {g["candidate_id"]: g["decision"] for g in record["quality_gate_decisions"]}


class ClaimStatusProvenanceTests(Lifecycle):
    """A model-set status is model-asserted even when its evidence text imitates the Engine's own wording."""

    def test_engine_wording_does_not_make_model_status_engine_written(self):
        for evidence, expected in ((ENGINE_EVIDENCE_PREFIX + "E-C0-1", "evidence_validated"),
                                   (ENGINE_EVIDENCE_PREFIX + "E-C0-9", "unresolved")):
            report, gate, validations = evaluate((claim("CL001", NARROW), claim("CL002", OTHER, "NOT_APPLICABLE", evidence)),
                                                 (check("E-C0-1", ("CL001",)),))
            c = claim_of(report, "CL002")
            self.assertEqual((validations[1].status, c.status_source, c.status), ("NOT_APPLICABLE", "model", expected))
            self.assertEqual(claim_of(report, "CL001").status, "verified")
            self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)
        self.assertTrue(has_reason(gate, "Unresolved evidence references kept as cited: CL002.evidence -> E-C0-9"))

    def test_status_written_by_the_engine_keeps_engine_provenance(self):
        text = ENGINE_EVIDENCE_PREFIX + "E-C0-1"
        claims, c1 = (claim("CL001", NARROW, "SUPPORTED", text),), cand("C1")
        evidence = (check("E-C1-1", (), candidate_id="C1"),)
        validations = ClaimValidator().validate(claims, "C1", evidence, content=c1.content)
        index = EvidenceIndex({}, c1, evidence=evidence, claims=claims)
        report = EvidenceIntegrity().assess(c1, claims, evidence, (), validations, index,
                                            engine_evidence={("CL001", "SUPPORTED", text)})
        c = claim_of(report, "CL001")
        self.assertEqual((c.status_source, c.status, c.references), ("engine", "model_claimed", ()))
        self.assertIn("does not transfer", c.reason)

    def test_critique_cannot_disguise_non_applicability_as_engine_support(self):
        control,_=self.run_engine(Contents(["S"]*3),MockJudgeProvider(),targeted())
        self.assertEqual(control.quality_gate,"ACCEPT_VERIFIED")
        result,record=self.run_engine(Spoofer(["S"]*3,ENGINE_EVIDENCE_PREFIX+"E-C0-1"),MockJudgeProvider(),targeted(),NARROW,OTHER)
        self.assertNotEqual(result.quality_gate,"ACCEPT_VERIFIED")
        spoofed=next(c for c in record["evidence_integrity"][1]["claims"] if c["claim_id"]=="CL002")
        self.assertEqual(spoofed["model_status"],"UNVERIFIED")
        self.assertNotEqual(spoofed["status"],"verified")
        self.assertTrue(any(f["producer"]=="claim_update" and not f["decisive"] for f in record["assessment_findings"]))


class CoverageTests(unittest.TestCase):
    """A receipt that covers no recorded claim or concern is not verification of anything."""

    def test_receipt_covering_nothing_does_not_permit_verified_acceptance(self):
        for targets in ((), ("CL009",)):  # no declared scope, or a target that names nothing recorded
            report, gate, _ = evaluate((), (check("E-C0-1", targets),))
            self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)
            self.assertIn(COVERS_NOTHING + ": E-C0-1", gate.reasons)

    def test_narrowly_scoped_coverage_still_verifies(self):
        report, gate, _ = evaluate((claim("CL001", NARROW),), (check("E-C0-1", ("CL001",)), check("E-C0-2", ())))
        self.assertEqual((claim_of(report, "CL001").status, gate.decision), ("verified", GateDecision.ACCEPT_VERIFIED))
        report, gate, _ = evaluate((), (check("E-C0-1", ("W001",)),), record={"weaknesses": [{"id": "W001"}]})
        self.assertEqual((report.uncertainties, gate.decision), ((), GateDecision.ACCEPT_VERIFIED))


class IdenticalContentReportingTests(Lifecycle):
    """C0 is returned after byte-identical C1 receives integrity findings. Selection, rollback, historical gates and
    termination stay as recorded; only findings applicable to the returned content are carried into its report."""

    def run_identical(self, judge, tool=None, **config):
        return self.run_engine(Contents([CONTENT] * 3), judge, tool or targeted(), post_acceptance_cycles=1, **config)

    def test_content_contradiction_on_identical_candidate_stays_visible(self):
        control,control_record=self.run_identical(adversary())
        self.assertEqual(control.quality_gate,"ACCEPT_VERIFIED")
        issue={"category":"constraint","description":"SYNTHETIC: precedence B->C fails at t=3","target":"CL001","fatal":False,"evidence":[]}
        result,record=self.run_identical(adversary({"minor_issues":[issue]}))
        self.assertEqual((result.best_candidate_id,result.answer),("C0",CONTENT))
        self.assertFalse(record["evidence_integrity"][1]["contradictions"])
        self.assertFalse(record["adversarial_judgments"][1]["minor_issues"][0]["decisive"])
        self.assertTrue(record["assessment_findings"])

    def test_explicit_rollback_keeps_rollback_and_reports_applicable_conflict(self):
        issue={"category":"constraint_violation","description":"SYNTHETIC: precedence B->C fails at t=3","target":"CL001","fatal":True,"evidence":[]}
        result,record=self.run_identical(adversary({"fatal_issues":[issue],"verdict":"FAIL","recommended_action":"REJECT"}))
        self.assertEqual((result.best_candidate_id,self.gates(record)["C1"]),("C0","BLOCKED"))
        self.assertEqual(record["rollback_events"],[])
        self.assertTrue(any(not f["decisive"] for f in record["assessment_findings"]))
        self.assertNotEqual(result.quality_gate,"REJECT")

    def test_failed_check_bound_to_identical_content_is_applicable(self):
        digest = content_sha256(CONTENT)
        tool = targeted(passed=lambda c: c.candidate_id != "C1",
                        contract=lambda c: CheckContract("synthetic.precedence", artifact_sha256=digest))
        # C1's check fails on the same bytes (C1: REVISE), so the loop continues to C2 and returns C0.
        result, record = self.run_engine(Contents([CONTENT] * 3), MockJudgeProvider(), tool)
        self.assertEqual((result.best_candidate_id, self.gates(record)["C0"], self.gates(record)["C1"]),
                         ("C0", "ACCEPT_VERIFIED", "REVISE"))
        found = record["final_reconciliation"]["integrity_findings"]["applicable"]
        self.assertEqual([(f["kind"], f["target"], f["candidate_id"], f["artifacts"]) for f in found],
                         [("failed_check", "CL001", "C1", ["E-C1-1"])])
        self.assertTrue(found[0]["applicability"].startswith("demonstrated"))
        self.assertIn(IDENTICAL_FAILURE + ": CL001 (E-C1-1 on C1; bound to this content by the checker's artifact hash)",
                      record["final_reconciliation"]["reconciled_gate"]["reasons"])
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")  # reported, never converted into a failure

    def test_judge_citation_errors_and_process_failures_are_listed_not_transferred(self):
        cases = {
            "wrong_candidate": (adversary({"evidence": ["E-C0-1"]}), None),
            "nonexistent": (adversary({"uncertainties": ["Receipt 5f0c1e2a-1111-4222-8333-444455556666 confirms it."]}), None),
            "process": (MockJudgeProvider(), targeted(contract=lambda c: CheckContract(
                "synthetic.precedence", artifact_sha256=content_sha256("other bytes")) if c.candidate_id == "C1" else None)),
        }
        for label, (judge, tool) in cases.items():
            result, record = self.run_identical(judge, tool)
            self.assertEqual(self.gates(record)["C1"], "ACCEPT_PROVISIONALLY", label)  # C1's own evaluation keeps it
            rec = record["final_reconciliation"]
            self.assertEqual(rec["integrity_findings"]["applicable"], [], label)
            listed = [n for n in rec["not_transferred"] if n["kind"] == "evidence_integrity"]
            # A check of a different artifact also leaves C1's claim outside that check's scope.
            self.assertEqual({(n["candidate_id"], n["category"]) for n in listed},
                             {("C1", "process"), ("C1", "claim_status")} if label == "process" else {("C1", "citation")}, label)
            if label != "process":
                self.assertEqual([n["status"] for n in listed], [label])
            self.assertEqual((result.best_candidate_id, result.quality_gate), ("C0", "ACCEPT_VERIFIED"), label)

    def test_contradiction_resolved_later_by_validated_transition_is_not_reraised(self):
        generator=Scripted([CONTENT]*3,critiques=[[{"weakness_id":None,"type":"constraint","severity":"low","description":"Horizon slack is untested for this schedule","evidence":"SYNTHETIC finding"}]],updates={3:[{"id":"W001","status":"resolved","reason":"Executed horizon check passed on this schedule"}]})
        issue={"category":"constraint","description":"SYNTHETIC: horizon has no slack","target":"W001","fatal":False,"evidence":[]}
        tool=targeted(lambda c:("W001",) if c.candidate_id!="C0" else ())
        result,record=self.run_engine(generator,adversary({"minor_issues":[issue]}),tool,post_acceptance_cycles=1)
        self.assertEqual(result.best_candidate_id,"C0")
        self.assertFalse(record["evidence_integrity"][1]["contradictions"])
        self.assertEqual([a["audit"] for a in record["final_reconciliation"]["applied_transitions"]],["VALID"])
        self.assertEqual(record["final_reconciliation"]["integrity_findings"]["applicable"],[])
        self.assertEqual(result.quality_gate,"ACCEPT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
