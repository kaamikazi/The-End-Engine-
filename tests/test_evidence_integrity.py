"""Evidence integrity (v0.3.3). Providers, checkers and evidence are SYNTHETIC offline fixtures, except the class
labelled OFFLINE REPLAY, which reads a read-only extract of the preserved Antigravity smoke 8b553c71
(tests/fixtures/recorded_8b553c71_integrity.json). No live model is called anywhere in this module."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.cognition.state import Claim, EvidenceStatus
from end_engine.core.state import Candidate, VerificationResult, now
from end_engine.models.deployment_mock import (DEPLOYMENT_TASK, DeploymentJudgeProvider, DeploymentMockProvider,
                                              deployment_tool_verifier)
from end_engine.quality.audits import ClaimValidator
from end_engine.quality.gate import QualityGate
from end_engine.quality.integrity import STATES, EvidenceIndex, EvidenceIntegrity, content_sha256
from end_engine.quality.judges import AdversarialJudge, CandidateJudge
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.quality.providers import _JudgeBridge
from end_engine.quality.state import (CheckContract, DimensionJudgment, EvidenceArtifact, GateDecision, JudgeIssue,
                                      Judgment, ResolutionAudit, Verdict)
from end_engine.verification import CallableToolVerifier, ToolCheck

FIXTURE = Path(__file__).parent / "fixtures" / "recorded_8b553c71_integrity.json"
CONTENT = "Schedule: A at 0, B at 1, C at 3, D at 6."
NARROW = "Precedence constraints hold for this schedule."
FINAL = "The schedule passes the final evaluation."
UNCERTAIN_SCOPE = "Evidence used outside its checked scope was not counted"
UNRESOLVED_REFS = "Unresolved evidence references kept as cited"
CONFLICT = "Contradictory evidence or judgments remain unresolved"


def cand(identity="C0", content=CONTENT):
    return Candidate(identity, None, int(identity[1:]), content, now())


def claim(identity, text, status="UNVERIFIED", evidence="", source="C0"):
    return Claim(identity, text, "technical", source, evidence_status=EvidenceStatus(status), evidence=evidence)


def check(identity, targets, *, passed=True, candidate_id="C0", contract=None, kind="EXECUTED_EVIDENCE"):
    return EvidenceArtifact(identity, candidate_id, kind, "synthetic_checker", passed, "SYNTHETIC check",
                            tuple(targets), None, contract)


def judge(identity="J001", candidate_id="C0", *, adversarial=False, verdict=Verdict.PASS, evidence=(), minor=(),
          major=(), uncertainties=()):
    return Judgment(identity, candidate_id, "adversarial" if adversarial else "primary", verdict,
                    (("correctness", DimensionJudgment(.95, .95)),), major_issues=tuple(major), minor_issues=tuple(minor),
                    uncertainties=tuple(uncertainties), evidence=tuple(evidence),
                    recommended_action="ACCEPT" if verdict is Verdict.PASS else "REVISE", adversarial=adversarial)


def evaluate(claims=(), evidence=(), judgments=None, *, candidate=None, record=None, independent=True, audits=()):
    """The deterministic post-model stage of QualitySession.evaluate: claim validation, integrity and the gate."""
    candidate = candidate or cand()
    judgments = judgments if judgments is not None else (judge(), judge("AJ001", adversarial=True))
    validations = ClaimValidator().validate(claims, candidate.candidate_id, evidence, content=candidate.content)
    index = EvidenceIndex(record or {}, candidate, evidence=evidence, judgments=judgments, claims=claims)
    report = EvidenceIntegrity().assess(candidate, claims, evidence, judgments, validations, index, audits=audits,
                                        independent=independent)
    gate = QualityGate().evaluate(candidate_id=candidate.candidate_id,
        verification=VerificationResult(True, .99, (("correctness", .99),), ()),
        judgments=tuple(j for j in judgments if not j.adversarial), adversarial=tuple(j for j in judgments if j.adversarial),
        validations=validations, audits=audits, evidence=evidence, independent=independent, integrity=report)
    return report, gate, validations


def claim_of(report, identity):
    return next(c for c in report.claims if c.claim_id == identity)


def statement_of(report, source):
    return next(s for s in report.statements if s.source == source)


def has_reason(gate, prefix):
    return any(r.startswith(prefix) for r in gate.reasons)


class EvidenceReferenceTests(unittest.TestCase):
    def test_nonexistent_reference_is_kept_as_cited_and_blocks_verified(self):
        claims = (claim("CL001", NARROW),)
        evidence = (check("E-C0-1", ("CL001",)),)
        report, gate, _ = evaluate(claims, evidence)
        self.assertEqual(gate.decision, GateDecision.ACCEPT_VERIFIED)  # Control: nothing invented.
        invented = (judge(evidence=("E-C0-1", "E-C0-9")),
                    judge("AJ001", adversarial=True, uncertainties=(
                        "Receipt receipts/0badc0de-0000-4000-8000-000000000000.json confirms the precedence check.",)))
        report, gate, _ = evaluate(claims, evidence, invented)
        bad = {(r.source, r.reference): r.status for r in report.references if r.status != "valid"}
        self.assertEqual(bad, {("J001.evidence", "E-C0-9"): "nonexistent",
            ("AJ001.uncertainties[0]", "receipts/0badc0de-0000-4000-8000-000000000000.json"): "nonexistent"})
        self.assertEqual(statement_of(report, "J001.verdict").status, "unresolved")
        self.assertEqual(statement_of(report, "AJ001.uncertainties[0]").text, invented[1].uncertainties[0])  # verbatim
        self.assertEqual(claim_of(report, "CL001").status, "verified")  # the real checker still supports the claim
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)  # never a fabricated failure
        self.assertTrue(has_reason(gate, UNRESOLVED_REFS))

    def test_model_claim_citing_invented_receipt_stays_unresolved(self):
        claims = (claim("CL001", NARROW, "SUPPORTED", "Verified by execution 5f0c1e2a-1111-4222-8333-444455556666"),)
        report, gate, validations = evaluate(claims, (check("E-C0-1", ()),))
        self.assertEqual(validations[0].status, "UNVERIFIED")
        c = claim_of(report, "CL001")
        self.assertEqual((c.status, c.model_status, c.status_source), ("unresolved", "SUPPORTED", "model"))
        self.assertEqual(c.history, ("model_claimed", "evidence_referenced", "unresolved"))
        self.assertEqual(c.references, ("5f0c1e2a-1111-4222-8333-444455556666: nonexistent",))
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_valid_reference_to_the_wrong_candidate_is_not_support(self):
        # E-C0-1 really exists, but it was recorded for C0. C1's judge and C1's claim cite it.
        record = {"verifier_evidence": [vars(check("E-C0-1", ("CL001",)))],
                  "candidates": [{"candidate_id": "C0", "content": CONTENT}]}
        for content in (CONTENT, "Schedule: A at 8, B at 0, C at 2, D at 5."):  # identical bytes do not transfer it
            c1 = cand("C1", content)
            claims = (claim("CL001", NARROW, "SUPPORTED", "Supported by E-C0-1"),)
            report, gate, validations = evaluate(claims, (check("E-C1-1", (), candidate_id="C1"),),
                (judge("J002", "C1", evidence=("E-C0-1",)), judge("AJ002", "C1", adversarial=True)), candidate=c1, record=record)
            self.assertEqual(validations[0].status, "UNVERIFIED")
            wrong = [(r.source, r.status, r.owner) for r in report.references if r.reference == "E-C0-1"]
            self.assertEqual(wrong, [("J002.evidence", "wrong_candidate", "C0"), ("CL001.evidence", "wrong_candidate", "C0")])
            self.assertEqual(claim_of(report, "CL001").status, "unresolved")
            self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)


class ScopeTests(unittest.TestCase):
    def test_development_pass_is_not_final_task_proof(self):
        dev = CheckContract("scheduling.development", "development", ("schema", "precedence"))
        for contract in (dev, None):  # declared development scope, or legacy evidence with no declared phase
            report, gate, validations = evaluate((claim("CL001", FINAL),), (check("E-C0-1", ("CL001",), contract=contract),))
            self.assertEqual((validations[0].status, validations[0].out_of_scope_artifacts), ("UNVERIFIED", ("E-C0-1",)))
            c = claim_of(report, "CL001")
            self.assertEqual(c.status, "unsupported")
            self.assertIn("final-task claim", c.out_of_scope[0][1])
            self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)  # not REVISE: no failure is invented
            self.assertTrue(has_reason(gate, UNCERTAIN_SCOPE))
        final = CheckContract("scheduling.final", "final", ("schema", "precedence", "capacity", "horizon"))
        report, gate, _ = evaluate((claim("CL001", FINAL),), (check("E-C0-1", ("CL001",), contract=final),))
        self.assertEqual((claim_of(report, "CL001").status, gate.decision), ("verified", GateDecision.ACCEPT_VERIFIED))

    def test_development_evidence_cited_for_complete_correctness_statement(self):
        evidence = (check("E-C0-1", ("CL001",), contract=CheckContract("scheduling.development")),)
        text = "E-C0-1 shows all constraints are satisfied, including capacity and horizon."
        report, gate, _ = evaluate((claim("CL001", NARROW),), evidence,
                                   (judge(evidence=("E-C0-1",)), judge("AJ001", adversarial=True, uncertainties=(text,))))
        s = statement_of(report, "AJ001.uncertainties[0]")
        self.assertEqual((s.status, s.history), ("unsupported", ("model_claimed", "evidence_referenced",
                                                                 "evidence_validated", "unsupported")))
        self.assertEqual(claim_of(report, "CL001").status, "verified")  # the narrow claim itself is in scope
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_checker_pass_outside_its_declared_statements(self):
        contract = CheckContract("scheduling.precedence", claims=(NARROW,), artifact_sha256=content_sha256(CONTENT))
        claims = (claim("CL001", NARROW), claim("CL002", "Capacity is never exceeded by this schedule."))
        # A sloppy mapping targets both claims; the contract declares only the precedence statement.
        report, gate, validations = evaluate(claims, (check("E-C0-1", ("CL001", "CL002"), contract=contract),))
        self.assertEqual([v.status for v in validations], ["SUPPORTED", "UNVERIFIED"])
        self.assertEqual((claim_of(report, "CL001").status, claim_of(report, "CL002").status), ("verified", "unsupported"))
        self.assertIn("outside the statements", claim_of(report, "CL002").out_of_scope[0][1])
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_checker_bound_to_a_different_artifact_supports_nothing(self):
        contract = CheckContract("scheduling.precedence", artifact_sha256=content_sha256("some other artifact"))
        report, gate, validations = evaluate((claim("CL001", NARROW),), (check("E-C0-1", ("CL001",), contract=contract),))
        self.assertEqual((validations[0].status, validations[0].out_of_scope_artifacts), ("UNVERIFIED", ("E-C0-1",)))
        self.assertEqual(report.trusted_evidence[0]["artifact_binding"], "mismatch")
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)
        self.assertTrue(has_reason(gate, "Executed evidence checked a different artifact"))

    def test_check_contract_phase_must_be_declared_by_trusted_code(self):
        tool = CallableToolVerifier(lambda task, c, tests, claims: (
            ToolCheck(True, "SYNTHETIC check", ("CL001",), None, CheckContract("x", "production")),))
        with self.assertRaises(ValueError):
            tool.collect("Task", cand(), (), ())

    def test_trusted_checker_supports_a_narrowly_scoped_claim(self):
        contract = CheckContract("scheduling.precedence", "development", ("precedence",), (NARROW,),
                                 content_sha256(CONTENT), "1.0", "declared precedence subset on this task input")
        tool = CallableToolVerifier(lambda task, c, tests, claims: (
            ToolCheck(True, "SYNTHETIC precedence check", ("CL001",), None, contract),), name="synthetic_precedence")
        evidence = tool.collect("Task", cand(), (), ())
        self.assertEqual(evidence[0].contract, contract)
        report, gate, _ = evaluate((claim("CL001", NARROW),), evidence, (judge(evidence=("E-C0-1",)), judge("AJ001", adversarial=True)))
        c = claim_of(report, "CL001")
        self.assertEqual((c.status, c.history, c.supporting), ("verified", ("model_claimed", "checker_supported", "verified"), ("E-C0-1",)))
        self.assertEqual(statement_of(report, "J001.verdict").status, "evidence_validated")  # still a model statement
        self.assertEqual(report.trusted_evidence[0]["artifact_binding"], "matches")
        self.assertEqual((report.uncertainties, gate.decision), ((), GateDecision.ACCEPT_VERIFIED))


class StatusAndContradictionTests(unittest.TestCase):
    def test_two_agreeing_model_judges_are_corroboration_not_verification(self):
        claims = (claim("CL001", "Recovery always succeeds.", "SUPPORTED", "Both judges agree; see E-C0-1"),)
        model_only = (check("E-C0-1", ("CL001",), kind="MODEL_JUDGMENT"),)
        judges = (judge(evidence=("E-C0-1",)), judge("J002", evidence=("E-C0-1",)), judge("AJ001", adversarial=True))
        report, gate, validations = evaluate(claims, model_only, judges)
        self.assertEqual(validations[0].status, "UNVERIFIED")
        c = claim_of(report, "CL001")
        self.assertEqual((c.status, c.history), ("evidence_validated",
                                                 ("model_claimed", "evidence_referenced", "evidence_validated")))
        self.assertEqual((report.model_agreement["agreement"], report.model_agreement["status"]), (True, "model_claimed"))
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)
        self.assertTrue(has_reason(gate, "Model-asserted claim status has no trusted evidence: CL001 (SUPPORTED)"))
        self.assertTrue(set(s.status for s in (*report.claims, *report.statements)) <= set(STATES))

    def test_model_asserted_non_applicability_is_not_verification(self):
        claims = (claim("CL001", "The rollback path is not applicable here.", "NOT_APPLICABLE", "The model explains why"),)
        report, gate, validations = evaluate(claims, (check("E-C0-1", ()),))
        self.assertEqual(validations[0].status, "NOT_APPLICABLE")
        self.assertEqual(claim_of(report, "CL001").status, "model_claimed")
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_checker_pass_contradicted_by_a_judgment_stays_visible(self):
        issue = JudgeIssue("constraint", "Precedence breaks if B is delayed", "CL001")
        claims, evidence = (claim("CL001", NARROW),), (check("E-C0-1", ("CL001",)),)
        report, gate, _ = evaluate(claims, evidence, (judge(evidence=("E-C0-1",)), judge("AJ001", adversarial=True, minor=(issue,))))
        self.assertEqual([(c.target, c.supporting, c.opposing) for c in report.contradictions],
                         [("CL001", ("check E-C0-1 PASS", "J001 PASS citing E-C0-1"), ("AJ001 minor issue",))])
        self.assertEqual(claim_of(report, "CL001").status, "unresolved")
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)  # a minor objection alone is not a failure
        self.assertTrue(has_reason(gate, CONFLICT))

    def test_contradictory_checks_are_not_resolved_by_order(self):
        passed, failed = check("E-C0-1", ("CL001",)), check("E-C0-2", ("CL001",), passed=False)
        results = [evaluate((claim("CL001", NARROW),), order) for order in ((passed, failed), (failed, passed))]
        for report, gate, _ in results:
            self.assertEqual(report.contradictions[0].target, "CL001")
            self.assertEqual(set(report.contradictions[0].supporting + report.contradictions[0].opposing),
                             {"check E-C0-1 PASS", "check E-C0-2 FAIL"})
            self.assertEqual(claim_of(report, "CL001").status, "unresolved")
            self.assertEqual(gate.decision, GateDecision.REVISE)  # the recorded failed check, as before
        self.assertEqual(results[0][1], results[1][1])

    def test_accepted_risk_remains_unverified(self):
        audit = ResolutionAudit("W001", "WEAKLY_SUPPORTED", "Justified low risk", 7, transition="accepted_risk")
        report, gate, _ = evaluate((claim("CL001", NARROW),), (check("E-C0-1", ("CL001",)),), audits=(audit,))
        self.assertEqual(report.accepted_risks[0]["status"], "unresolved")
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)
        self.assertIn("Accepted risks remain unverified: W001", gate.reasons)


class CitingJudge(MockJudgeProvider):
    """SYNTHETIC independent judge that cites the given evidence IDs in every judgment."""
    def __init__(self, cite=(), **kwargs):
        super().__init__(**kwargs)
        self.cite = tuple(cite)

    def for_run(self):
        return CitingJudge(self.cite, model=self.model, confidence=self.confidence)

    def evaluate(self, request):
        response = super().evaluate(request)
        if request.purpose in ("judgment", "adversarial_judgment") and self.cite:
            return ModelResponse({**response.content, "evidence": list(self.cite)})
        return response


class ContentJudge(MockJudgeProvider):
    """SYNTHETIC independent judge: fatal objection to content mentioning start 99, otherwise PASS."""
    def for_run(self):
        return ContentJudge(model=self.model, confidence=self.confidence)

    def evaluate(self, request):
        if request.purpose in ("judgment", "adversarial_judgment") and "99" in request.context["candidate"]["content"]:
            return ModelResponse(judgment_fixture(request.context["dimensions"], verdict="FAIL", score=.2, fatal=True,
                issues=[{"category": "constraint_violation", "description": "SYNTHETIC: start 99 exceeds the horizon",
                         "target": "candidate", "fatal": True, "evidence": []}]))
        return super().evaluate(request)


class Contents(MockProvider):
    """SYNTHETIC generator returning scripted candidate contents; critiques find nothing."""
    def __init__(self, contents):
        super().__init__()
        self.contents, self.counts = list(contents), {}

    def generate_structured(self, request):
        p, c = request.purpose, request.context
        n = self.counts[p] = self.counts.get(p, 0) + 1
        if p in ("initial_candidate", "revision"):
            index = 0 if p == "initial_candidate" else n
            return ModelResponse({"content": self.contents[min(index, len(self.contents) - 1)], "known_strengths": [],
                                  "confidence": None})
        if p == "verification":
            return ModelResponse({"passed": True, "score": .99, "dimensions": {d: .99 for d in c["dimensions"]},
                                  "remaining_issues": [], "weakness_updates": []})
        if p == "critique":
            return ModelResponse({"summary": "SYNTHETIC critique", "findings": []})
        if p == "revision_plan":
            return ModelResponse({"changes": []})
        return super().generate_structured(request)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_engine(self, contents, judge, tool, max_cycles=2, claim_extractor=None):
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False), provider=Contents(contents),
                           judge_provider=judge, tool_verifier=tool, claim_extractor=claim_extractor)
        result = engine.run("Schedule jobs within capacity and horizon.", mode="normal", max_cycles=max_cycles)
        return result, engine.last_trajectory

    def test_invented_judge_citation_no_longer_aborts_the_run_and_blocks_verified(self):
        # v0.3.4: the SYNTHETIC check targets a trusted claim; a check covering nothing no longer verifies anything.
        class Trusted:
            def extract(self, candidate):
                return (NARROW,)
        tool = CallableToolVerifier(lambda task, c, tests, claims: (
            ToolCheck(True, "SYNTHETIC executed subset", tuple(x.claim_id for x in claims)),))
        control, _ = self.run_engine(["Start A at 0."], MockJudgeProvider(), tool, claim_extractor=Trusted())
        self.assertEqual(control.quality_gate, "ACCEPT_VERIFIED")
        result, record = self.run_engine(["Start A at 0."], CitingJudge(("E-C0-7",)), tool, claim_extractor=Trusted())
        self.assertNotEqual(result.termination_reason.value, "EXTERNAL_BLOCKER")  # 0.3.2 raised here
        self.assertEqual((record["judgments"][0]["evidence"], record["judgments"][0]["unresolved_evidence"]),
                         (["E-C0-7"], ["E-C0-7"]))
        refs = [r for r in record["evidence_integrity"][0]["references"] if r["reference"] == "E-C0-7"]
        self.assertEqual({r["status"] for r in refs}, {"nonexistent"})
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")
        self.assertTrue(record["scorecard"]["evidence_integrity"]["unresolved_references"])

    def test_missing_evidence_stays_visible_after_rollback(self):
        c0, c1 = "The schedule will pass the final evaluation. Start A at 0.", "Start A at 99."
        dev = CheckContract("scheduling.development", "development", ("schema",))
        # A sloppy SYNTHETIC mapping targets every claim with a development-scope PASS.
        tool = CallableToolVerifier(lambda task, c, tests, claims: (
            ToolCheck(True, "SYNTHETIC development subset", tuple(x.claim_id for x in claims), None, dev),))
        result, record = self.run_engine([c0, c1], ContentJudge(), tool)
        self.assertEqual((result.best_candidate_id, result.answer), ("C0", c0))
        self.assertTrue(record["rollback_events"])
        summary = record["scorecard"]["evidence_integrity"]
        self.assertEqual(summary["candidate_id"], "C0")
        missing = {i["id"]: i["status"] for i in summary["not_verified"]}
        self.assertEqual(missing.get("CL001"), "unsupported")
        self.assertIn("C1", {e["candidate_id"] for e in record["evidence_integrity"]})  # later records are kept
        self.assertNotEqual(result.quality_gate, "ACCEPT_VERIFIED")
        self.assertTrue(any(u.startswith(UNCERTAIN_SCOPE) for u in record["scorecard"]["known_uncertainties"]))

    def test_deployment_acceptance_and_rollback_are_unchanged(self):
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False), provider=DeploymentMockProvider(),
                           judge_provider=DeploymentJudgeProvider(), tool_verifier=deployment_tool_verifier())
        result = engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=4)
        record = engine.last_trajectory
        self.assertEqual((result.quality_gate, result.best_candidate_id), ("ACCEPT_VERIFIED", "C3"))
        self.assertEqual(record["scorecard"]["evidence_integrity"]["blocks_verified_acceptance"], [])
        self.assertEqual(len(record["evidence_integrity"]), len(record["quality_gate_decisions"]))


class RecordedSmokeReplayTests(unittest.TestCase):
    """OFFLINE REPLAY of the Engine 0.3.2 Antigravity smoke 8b553c71: recorded candidates, receipts and judgments are
    fed through the real judge-parsing, validation, integrity and gate code. SYNTHETIC mutations are labelled."""
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def replay_judgment(self, recorded, candidate, evidence, adversarial=False):
        raw = {k: recorded[k] for k in ("verdict", "dimensions", "fatal_issues", "major_issues", "minor_issues",
                                        "uncertainties", "evidence", "recommended_action")}
        purpose = "adversarial_judgment" if adversarial else "judgment"
        provider = _JudgeBridge(MockJudgeProvider(scripted={purpose: [raw]}), "replay")
        kind = AdversarialJudge(provider) if adversarial else CandidateJudge(provider)
        return kind.judge("replayed task", candidate, tuple(raw["dimensions"]), (), evidence, recorded["judgment_id"])

    def setUp(self):
        d = self.data
        self.assertTrue(d["_label"].startswith("OFFLINE REPLAY FRAGMENT"))
        self.candidates = {c["candidate_id"]: cand(c["candidate_id"], c["content"]) for c in d["candidates"]}
        self.evidence = {e["candidate_id"]: EvidenceArtifact(**{**e, "targets": tuple(e["targets"])}) for e in d["verifier_evidence"]}
        self.claim = claim("CL001", d["claims_at_discovery"][0]["text"])
        self.record = {"verifier_evidence": d["verifier_evidence"], "candidates": d["candidates"]}

    def test_recorded_c0_evaluation_replays_with_scope_limits_visible(self):
        c0, e0 = self.candidates["C0"], (self.evidence["C0"],)
        j = self.replay_judgment(self.data["judgments"][0], c0, e0)
        aj = self.replay_judgment(self.data["adversarial_judgments"][0], c0, e0, adversarial=True)
        report, gate, validations = evaluate((self.claim,), e0, (j, aj), candidate=c0, record=self.record,
                                             independent=self.data["different_model_identity"])
        recorded = self.data["recorded_claim_validations"][0]
        self.assertEqual((validations[0].status, list(validations[0].supporting_artifacts)),
                         (recorded["status"], recorded["supporting_artifacts"]))
        self.assertEqual(claim_of(report, "CL001").status, "verified")  # a development claim within development scope
        s = statement_of(report, "AJ001.uncertainties[0]")
        self.assertEqual(s.text, self.data["adversarial_judgments"][0]["uncertainties"][0])  # model text preserved
        self.assertEqual((s.status, s.references), ("unsupported", (self.evidence["C0"].artifact_id + ": valid",)))
        self.assertEqual({statement_of(report, x).status for x in ("J001.verdict", "AJ001.verdict")}, {"evidence_validated"})
        self.assertEqual((report.model_agreement["agreement"], report.model_agreement["same_model_identity"]), (True, True))
        original = self.data["recorded_quality_gates"][0]
        self.assertEqual(gate.decision.value, original["decision"])  # outcome unchanged: ACCEPT_PROVISIONALLY
        self.assertTrue(set(original["reasons"]) <= set(gate.reasons))
        self.assertIn(UNCERTAIN_SCOPE + ": AJ001.uncertainties[0]", gate.reasons)

    def test_synthetic_mutations_of_the_recorded_run_are_blocked(self):
        c0, c1, e0 = self.candidates["C0"], self.candidates["C1"], self.evidence["C0"]
        self.assertEqual(c0.content, c1.content)  # recorded: byte-identical candidates
        # SYNTHETIC: the development receipt is mapped onto a capacity/horizon claim it never checked.
        wide = claim("CL002", "Resource capacity and horizon constraints are fully satisfied.")
        mutated = EvidenceArtifact(**{**vars(e0), "targets": ("CL001", "CL002")})
        report, gate, _ = evaluate((self.claim, wide), (mutated,), candidate=c0, record=self.record, independent=False)
        self.assertEqual((claim_of(report, "CL001").status, claim_of(report, "CL002").status), ("verified", "unsupported"))
        # SYNTHETIC: C1's judge cites C0's recorded receipt instead of C1's own.
        recorded = {**self.data["judgments"][1], "evidence": [e0.artifact_id]}
        j = self.replay_judgment(recorded, c1, (self.evidence["C1"],))
        self.assertEqual(j.unresolved_evidence, (e0.artifact_id,))
        report, gate, _ = evaluate((self.claim,), (self.evidence["C1"],), (j, judge("AJ002", "C1", adversarial=True)),
                                   candidate=c1, record=self.record, independent=False)
        self.assertEqual([(r.status, r.owner) for r in report.references if r.reference == e0.artifact_id],
                         [("wrong_candidate", "C0")])
        self.assertTrue(has_reason(gate, UNRESOLVED_REFS))
        self.assertEqual(gate.decision, GateDecision.ACCEPT_PROVISIONALLY)


if __name__ == "__main__":
    unittest.main()
