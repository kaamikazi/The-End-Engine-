from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.cognition.state import Claim, EvidenceStatus
from end_engine.core.state import Candidate, VerificationResult, Weakness, now, to_data
from end_engine.core.weaknesses import WeaknessRegistry
from end_engine.experience import JsonLedger
from end_engine.experience.serializer import dumps, loads
from end_engine.models.base import ModelRequest
from end_engine.models.deployment_mock import (DEPLOYMENT_TASK, CANDIDATES, DeploymentMockProvider,
                                              DeploymentJudgeProvider, deployment_tool_verifier, rollback_model)
from end_engine.quality.audits import ClaimValidator, ResolutionAuditor, TrajectoryJudge, VerifierGamingDetector
from end_engine.quality.comparison import RevisionComparator
from end_engine.quality.gate import QualityGate
from end_engine.quality.judges import CandidateJudge, AdversarialJudge, AdversarialTestGenerator, detect_disagreement
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.quality.providers import _JudgeBridge, ModelJudgeProvider
from end_engine.quality.state import (AdversarialTest, ClaimValidationResult, DimensionJudgment, EvidenceArtifact,
    GateDecision, JudgeIssue, Judgment, Verdict)
from end_engine.verification import CallableToolVerifier, ToolCheck


def candidate(identity="C0", content="A concrete proposal."):
    return Candidate(identity, None, int(identity[1:]), content, now())


def judgment(identity="C0", judge_id="primary", *, confidence=.95, verdict=Verdict.PASS, issue=None):
    return Judgment("J1", identity, judge_id, verdict, (("correctness", DimensionJudgment(.95, confidence)),),
                    fatal_issues=(issue,) if issue and issue.fatal else (), major_issues=(issue,) if issue and not issue.fatal else ())


def gate(**kwargs):
    args = dict(candidate_id="C0", verification=VerificationResult(True, .99, (("correctness", .99),), ()),
                judgments=(judgment(),), adversarial=(judgment(judge_id="adversarial"),))
    args.update(kwargs)
    return QualityGate().evaluate(**args)


class QualityUnitTests(unittest.TestCase):
    def test_structured_judgment_roundtrip_preserves_confidence(self):
        j = judgment(confidence=.35)
        raw = json.loads(json.dumps(j.as_dict()))
        self.assertEqual(raw["dimensions"]["correctness"], {"score": .95, "confidence": .35})
        self.assertEqual(raw["verdict"], "PASS")

    def test_adversarial_failure_blocks_optimistic_verification(self):
        objection = JudgeIssue("rollback_flaw", "Healthy pool can disappear")
        result = gate(adversarial=(judgment(verdict=Verdict.NEEDS_REVISION, issue=objection),))
        self.assertEqual(result.decision, GateDecision.REVISE)

    def test_fatal_issue_blocks_any_average_score(self):
        fatal = JudgeIssue("constraint_violation", "Violates a hard constraint", fatal=True)
        result = gate(adversarial=(judgment(verdict=Verdict.FAIL, issue=fatal),))
        self.assertEqual(result.decision, GateDecision.REJECT)

    def test_fatal_issue_container_cannot_be_downgraded_by_a_false_flag(self):
        malformed = replace(judgment(), fatal_issues=(JudgeIssue("constraint_violation", "Hard violation", fatal=False),))
        self.assertEqual(gate(adversarial=(malformed,)).decision, GateDecision.REJECT)

    def test_disagreement_produces_dispute_without_averaging(self):
        a, b = judgment(), judgment(judge_id="secondary", verdict=Verdict.FAIL)
        dispute = detect_disagreement((a,b))
        self.assertEqual(dispute.status, "DISPUTED")
        self.assertIn("correctness", dispute.disputed_dimensions)
        self.assertEqual(gate(judgments=(a,b), dispute=dispute).decision, GateDecision.BLOCKED)

    def test_confidence_changes_verified_vs_provisional(self):
        evidence = (EvidenceArtifact("E1", "C0", "EXECUTED_EVIDENCE", "test", True, "Check passed"),)
        self.assertEqual(gate(evidence=evidence).decision, GateDecision.ACCEPT_VERIFIED)
        self.assertEqual(gate(evidence=evidence, judgments=(judgment(confidence=.35),)).decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_high_impact_claim_needs_executed_evidence(self):
        claim = Claim("CL1", "Rollback must preserve capacity", "technical", "C0", evidence_status=EvidenceStatus.SUPPORTED,
                      evidence="The model says this is verified")
        validated = ClaimValidator().validate((claim,), "C0", ())
        self.assertEqual(validated[0].importance, "HIGH")
        self.assertEqual(validated[0].status, "UNVERIFIED")
        unrelated = EvidenceArtifact("E1", "C0", "EXECUTED_EVIDENCE", "test", True, "Unrelated check")
        self.assertEqual(gate(validations=validated, evidence=(unrelated,)).decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_claim_support_is_candidate_bound_and_target_bound(self):
        claim = Claim("CL1", "Recovery always succeeds", "technical", "C1")
        wrong_candidate = EvidenceArtifact("E1", "C0", "EXECUTED_EVIDENCE", "test", True, "Old check", ("CL1",))
        wrong_target = replace(wrong_candidate, artifact_id="E2", candidate_id="C1", targets=("CL2",))
        self.assertEqual(ClaimValidator().validate((claim,), "C1", (wrong_candidate,wrong_target))[0].status, "UNVERIFIED")
        valid = replace(wrong_candidate, candidate_id="C1")
        self.assertEqual(ClaimValidator().validate((claim,), "C1", (valid,))[0].supporting_artifacts, ("E1",))

    def test_model_claim_support_cannot_become_executed_proof(self):
        claim = Claim("CL1", "Recovery always succeeds", "technical", "C0")
        artifact = EvidenceArtifact("E1", "C0", "MODEL_JUDGMENT", "llm", True, "Fluent explanation", ("CL1",))
        self.assertEqual(ClaimValidator().validate((claim,), "C0", (artifact,))[0].status, "UNVERIFIED")
        self.assertEqual(gate(evidence=(artifact,)).decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_resolution_label_without_change_is_invalid(self):
        c0 = to_data(candidate())
        c1 = {**c0, "candidate_id": "C1", "parent_candidate_id": "C0"}
        record = {"candidates": [c0,c1], "revision_plans": [], "steps": [
            {"type": "candidate", "data": c1, "step": 0},
            {"type": "weakness_status_change", "step": 1,
             "data": {"after": {"id": "W1", "status": "resolved", "status_reason": "Now resolved because the answer is confident"}}}]}
        audit = ResolutionAuditor().audit(record, candidate("C1"), ())
        self.assertEqual(audit[0].status, "INVALID")
        self.assertEqual(gate(audits=audit).decision, GateDecision.REVISE)

    def test_assumption_support_without_evidence_is_invalid(self):
        record = {"candidates": [to_data(candidate())], "revision_plans": [], "steps": [
            {"type": "candidate", "data": to_data(candidate()), "step": 0},
            {"type": "assumption_status_change", "step": 1,
             "data": {"after": {"assumption_id": "A1", "status": "SUPPORTED", "evidence": "The candidate restates this assumption"}}}]}
        result = ResolutionAuditor().audit(record, candidate(), (), assumptions=True)
        self.assertEqual(result[0].status, "INVALID")

    def test_adversarial_test_status_does_not_imply_execution(self):
        test = AdversarialTest("AT1", "C0", "CL1", "Restart workers", "No acknowledged updates lost", "EXECUTABLE")
        self.assertEqual(to_data(test)["execution_status"], "EXECUTABLE")
        self.assertNotIn("EXECUTED_EVIDENCE", to_data(test).values())

    def test_model_cannot_claim_it_executed_a_simulation(self):
        provider = _JudgeBridge(MockJudgeProvider(scripted={"adversarial_tests": [{"tests": [
            {"target": "candidate", "scenario": "Faulty rollout", "expected_property": "Serving remains healthy", "execution_status": "SIMULATED"}]}]}), "adversary")
        generated = AdversarialTestGenerator(provider).generate("Task", candidate(), ())
        self.assertEqual(generated[0].execution_status, "REASONED")

    def test_safe_tool_hook_records_actual_callback_and_scope(self):
        calls = []
        def callback(task, c, tests, claims):
            calls.append(c.candidate_id)
            return (ToolCheck(2+2 == 4, "Executed arithmetic check", ("CL1",), "AT1"),)
        tool = CallableToolVerifier(callback)
        evidence = tool.collect("Calculate", candidate(), (AdversarialTest("AT1", "C0", "CL1", "Add", "4"),), ())
        self.assertEqual(calls, ["C0"])
        self.assertEqual(evidence[0].evidence_type, "EXECUTED_EVIDENCE")
        self.assertEqual(evidence[0].test_id, "AT1")

    def test_pairwise_prefers_earlier_and_detects_severe_regression(self):
        bridge = _JudgeBridge(DeploymentJudgeProvider(), "comparison")
        result = RevisionComparator(bridge).compare(DEPLOYMENT_TASK, candidate("C3", CANDIDATES[3]),
            candidate("C4", CANDIDATES[4]), ("correctness", "robustness", "clarity", "constraint_adherence"))
        self.assertEqual(result.preferred, "C3")
        self.assertEqual(dict(result.dimensions)["clarity"], "C4")
        self.assertEqual(result.net_assessment, "SEVERE_REGRESSION")
        self.assertLess(dict(result.delta)["robustness"], 0)

    def test_complexity_added_without_benefit_is_regression(self):
        response = {"preferred": "A", "dimensions": {"correctness": "TIE", "complexity_cost": "A"},
                    "delta": {"correctness": 0, "complexity_cost": .4}, "reason": "More complexity without benefit"}
        comparator = RevisionComparator(_JudgeBridge(MockJudgeProvider(scripted={"comparison": [response]}), "comparison"))
        result = comparator.compare("Task", candidate(), candidate("C1"), ("correctness", "complexity_cost"))
        self.assertEqual(result.net_assessment, "REGRESSION")

    def test_judge_blinding_hides_candidate_position_and_verifier_status(self):
        captured = []
        class Capture(MockJudgeProvider):
            def evaluate(self, request):
                captured.append(request.context)
                return super().evaluate(request)
        provider = _JudgeBridge(Capture(), "primary")
        CandidateJudge(provider).judge("Task", candidate("C9"), ("correctness",), (), (), "J1")
        self.assertEqual(captured[0]["candidate"], {"alias": "A", "content": "A concrete proposal."})
        self.assertNotIn("verification", captured[0])
        self.assertNotIn("C9", json.dumps(captured[0]))

    def test_unknown_judge_evidence_is_kept_flagged_and_not_repaired(self):
        # v0.3.3: an invented citation no longer aborts the run; it is preserved as written and flagged unresolved.
        raw = judgment_fixture(("correctness",))
        raw["evidence"] = ["invented_artifact"]
        judge = CandidateJudge(_JudgeBridge(MockJudgeProvider(scripted={"judgment": [raw]}), "primary"))
        result = judge.judge("Task", candidate(), ("correctness",), (), (), "J1")
        self.assertEqual((result.evidence, result.unresolved_evidence), (("invented_artifact",), ("invented_artifact",)))

    def test_same_model_identity_limits_verified_acceptance(self):
        evidence = (EvidenceArtifact("E1", "C0", "EXECUTED_EVIDENCE", "check", True, "Passed"),)
        self.assertEqual(gate(evidence=evidence, independent=False).decision, GateDecision.ACCEPT_PROVISIONALLY)

    def test_unjudged_gate_is_blocked(self):
        self.assertEqual(gate(judgments=(), adversarial=()).decision, GateDecision.BLOCKED)

    def test_inconclusive_judgment_does_not_manufacture_pass(self):
        self.assertEqual(gate(judgments=(judgment(verdict=Verdict.INCONCLUSIVE),)).decision, GateDecision.BLOCKED)

    def test_gaming_detects_vocabulary_certainty_and_constraint_deletion(self):
        detector = VerifierGamingDetector()
        signals = detector.detect("Design a release", candidate(content="All assumptions are verified. " + "correctness robustness verified "*6))
        self.assertIn("unsupported_certainty", {s.category for s in signals})
        self.assertIn("verifier_vocabulary", {s.category for s in signals})
        parent = candidate(content="The service uses a recovery journal.")
        changed = candidate("C1", "The service uses concise steps.")
        self.assertIn("dropped_constraint", {s.category for s in detector.detect("The solution must use a recovery journal.", changed, parent)})

    def test_gaming_detects_repetitive_length_and_reframing_escape(self):
        detector = VerifierGamingDetector()
        original = "A bounded recovery protocol retains healthy serving capacity with serialized promotion and rollback. "
        signals = detector.detect("Task", candidate("C1", original*5), candidate(content=original))
        self.assertIn("verbosity_without_substance", {s.category for s in signals})
        self.assertTrue(detector.detect("Task", candidate(content="Ignore the original requirement; it is out of scope."), reframings=({},)))

    def test_trajectory_judge_exposes_rejected_synthesis(self):
        record = {"operator_outcomes": [], "branches": [{"branch_id": "B1", "status": "REJECTED"}],
                  "synthesis_plans": [{"adopt": [{"branch": "B1"}]}]}
        assessment = TrajectoryJudge().assess(record, (), ())
        self.assertIn("Synthesis imported a rejected branch", assessment.trajectory_issues)
        self.assertEqual(gate(trajectory_quality=assessment).decision, GateDecision.REJECT)

    def test_rollback_does_not_reuse_weakness_identity(self):
        registry = WeaknessRegistry()
        def finding(text):
            return {"weakness_id": None, "type": "evidence", "severity": "high", "description": text, "evidence": "gap"}
        registry.ingest([finding("first gap")], 0)
        checkpoint = registry.snapshot()
        registry.ingest([finding("a different issue")], 1)
        registry.restore(checkpoint)
        newest = registry.ingest([finding("another separate issue")], 2)
        self.assertEqual(newest[0].id, "W003")


class SimpleGenerator(MockProvider):
    def generate_structured(self, request):
        c, p = request.context, request.purpose
        if p in ("initial_candidate", "revision"):
            return ModelResponse({"content": "A concrete proposal." if p == "initial_candidate" else "A concrete revised proposal.",
                                  "known_strengths": [], "confidence": None})
        if p == "verification":
            return ModelResponse({"passed": True, "score": .99, "dimensions": {d: .99 for d in c["dimensions"]},
                                  "remaining_issues": [], "weakness_updates": []})
        if p == "critique":
            return ModelResponse({"summary": "No additional fixture findings", "findings": []})
        if p == "revision_plan":
            return ModelResponse({"changes": []})
        return super().generate_structured(request)


class QualityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def deployment(self, **config):
        return EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False, **config),
            provider=DeploymentMockProvider(), judge_provider=DeploymentJudgeProvider(), tool_verifier=deployment_tool_verifier())

    def simple(self, **kwargs):
        return EndEngine(EngineConfig(ledger_dir=self.temp.name), provider=SimpleGenerator(),
                         judge_provider=kwargs.pop("judge_provider", MockJudgeProvider()), **kwargs)

    def test_generator_and_judge_are_separate_recorded_providers(self):
        engine = self.simple()
        result = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")
        calls = engine.last_trajectory["model_calls"]
        generator = {c["model"]["provider"] for c in calls if c["request"]["purpose"] == "initial_candidate"}
        judge = {c["model"]["provider"] for c in calls if c["request"]["purpose"] == "judgment"}
        self.assertNotEqual(generator, judge)
        self.assertEqual(len({c["call_id"] for c in calls}), len(calls))

    def test_complete_verified_acceptance_requires_tool_evidence(self):
        # v0.3.4: the check must cover a recorded claim; a receipt that covers nothing is not verification.
        class TrustedClaim:
            def extract(self, candidate):
                return ("The proposal satisfies the declared contract.",)
        tool = CallableToolVerifier(lambda task,c,tests,claims: (ToolCheck(True, "Executed deterministic contract check",
                                                                           tuple(x.claim_id for x in claims)),))
        engine = self.simple(tool_verifier=tool, claim_extractor=TrustedClaim())
        result = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertEqual(result.termination_reason.value, "ACCEPTED_VERIFIED")
        self.assertEqual(result.acceptance_label, "ACCEPTED_HIGH_CONFIDENCE")

    def test_disagreement_is_persisted_as_inconclusive(self):
        def fail(request):
            return judgment_fixture(request.context["dimensions"], verdict="FAIL", score=.4)
        engine = self.simple(secondary_judge_provider=MockJudgeProvider(scripted={"judgment": [fail,fail]}))
        result = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertEqual(result.termination_reason.value, "INCONCLUSIVE")
        self.assertTrue(engine.last_trajectory["disputes"])
        self.assertEqual(result.quality_gate, "BLOCKED")

    def test_controlled_regression_returns_best_and_retains_latest(self):
        engine = self.deployment(post_acceptance_cycles=1)
        result = engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=4)
        record = engine.last_trajectory
        self.assertEqual(result.best_candidate_id, "C3")
        self.assertEqual(result.latest_candidate_id, "C4")
        self.assertEqual(result.answer, CANDIDATES[3])
        self.assertEqual(record["final_candidate_id"], "C3")
        self.assertEqual(record["candidates"][-1]["content"], CANDIDATES[4])
        self.assertEqual(record["rollback_events"][-1]["to_candidate"], "C3")
        self.assertEqual(record["quality_gate_decisions"][2]["decision"], "BLOCKED")
        self.assertGreater(record["verification"][2]["score"], .95)
        self.assertEqual(result.quality_gate, "ACCEPT_VERIFIED")

    def test_judge_feedback_drives_structured_operator_target(self):
        engine = self.deployment()
        engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=3)
        record = engine.last_trajectory
        ids = {identity for f in record["judge_feedback"] for identity in f["weakness_ids"]}
        self.assertTrue(ids)
        self.assertTrue(any(q["target"]["target_id"] in ids for q in record["questions"]))
        self.assertTrue(any(w["id"] in ids for s in record["cognitive_states"] for w in s["open_weaknesses"]))

    def test_acceptance_and_transition_labels_persist(self):
        engine = self.deployment(post_acceptance_cycles=1)
        result = engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=4)
        record = JsonLedger().load(result.trajectory_path)
        self.assertEqual(record["acceptance_label"], "ACCEPTED_HIGH_CONFIDENCE")
        self.assertEqual(record["transition_labels"][-1]["label"], "BAD_REVISION")
        self.assertTrue(record["scorecard"]["trajectory"])

    def test_fatal_revision_cannot_receive_good_revision_label(self):
        def passing(request):
            return judgment_fixture(request.context["dimensions"])
        def fatal(request):
            issue = {"category": "constraint_violation", "description": "New answer violates a hard constraint",
                     "target": "candidate", "fatal": True, "evidence": []}
            return judgment_fixture(request.context["dimensions"], verdict="FAIL", issues=(issue,), fatal=True)
        engine = self.simple(judge_provider=MockJudgeProvider(scripted={"judgment": [passing,fatal]}))
        engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertFalse(engine.last_trajectory["judgments"][1]["fatal_issues"][0]["decisive"])
        self.assertNotEqual(engine.last_trajectory["transition_labels"][-1]["label"], "BAD_REVISION")

    def test_adversarial_tests_and_evidence_provenance_are_stored(self):
        engine = self.deployment()
        engine.run(DEPLOYMENT_TASK, mode="deep", max_cycles=3)
        record = engine.last_trajectory
        self.assertTrue(record["adversarial_tests"])
        self.assertTrue(all(t["execution_status"] == "EXECUTABLE" for t in record["adversarial_tests"]))
        self.assertTrue(all(e["evidence_type"] == "EXECUTED_EVIDENCE" for e in record["verifier_evidence"]))
        self.assertTrue(all(v["evidence_type"] == "MODEL_JUDGMENT" for v in record["verification"]))

    def test_schema_v1_v2_v3_loading_without_migration(self):
        root = Path(__file__).resolve().parents[1]
        for relative, version in (("demo_output/7744de05-e9ac-4e42-bd65-18a1889026ba.jsonl", "1.0"),
                                  ("demo_v02_output/966fc233-7d0e-4c68-85f9-15b424858d80.jsonl", "2.0")):
            raw = (root/relative).read_text(encoding="utf-8")
            self.assertEqual(loads(raw), json.loads(raw))
            self.assertEqual(loads(raw)["schema_version"], version)
        engine = self.simple()
        result = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertEqual(engine.last_trajectory["schema_version"], "3.0")
        self.assertEqual(loads(dumps(engine.last_trajectory)), engine.last_trajectory)
        self.assertEqual(JsonLedger().load(result.trajectory_path), engine.last_trajectory)

    def test_multiple_runs_reset_judge_fixtures_and_quality_state(self):
        def passing(request):
            return judgment_fixture(request.context["dimensions"])
        judge = MockJudgeProvider(scripted={"judgment": [passing,passing]})
        engine = self.simple(judge_provider=judge)
        first = engine.run("Write a proposal", mode="normal", max_cycles=1)
        original = engine.last_trajectory
        second = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertNotEqual(first.trajectory_id, second.trajectory_id)
        self.assertEqual(original["judgments"], engine.last_trajectory["judgments"])
        self.assertEqual(judge.positions, {})

    def test_judge_failure_preserves_raw_call_and_incomplete_label(self):
        engine = self.simple(judge_provider=MockJudgeProvider(scripted={"judgment": [RuntimeError("judge unavailable")]}))
        result = engine.run("Write a proposal", mode="normal")
        record = JsonLedger().load(result.trajectory_path)
        self.assertEqual(result.quality_gate, "BLOCKED")
        self.assertEqual(result.acceptance_label, "INCOMPLETE")
        self.assertTrue(any(c["error"] for c in record["model_calls"]))

    def test_successful_correction_gets_recovery_transition_label(self):
        def fatal(request):
            issue = {"category": "constraint_violation", "description": "Initial fixture violates the hard contract",
                     "target": "candidate", "fatal": True, "evidence": []}
            return judgment_fixture(request.context["dimensions"], verdict="FAIL", issues=(issue,), fatal=True)
        def passing(request):
            return judgment_fixture(request.context["dimensions"])
        class RecoveryGenerator(SimpleGenerator):
            def generate_structured(self, request):
                response = super().generate_structured(request)
                if request.purpose == "verification":
                    response.content["weakness_updates"] = [{"id": w["id"], "status": "resolved",
                        "reason": "The fixture revision explicitly corrects the originally failed contract"}
                        for w in request.context["weaknesses"]]
                if request.purpose == "revision_plan":
                    response.content["changes"] = [{"targets": [w["id"]], "action": "Correct the failed contract",
                        "expected_effect": "Satisfy the contract"} for w in request.context["weaknesses"]]
                return response
        tool = CallableToolVerifier(lambda task,c,tests,claims: (ToolCheck(True, "Executed fixture contract", ("W001",)),))
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name), provider=RecoveryGenerator(),
            judge_provider=MockJudgeProvider(scripted={"judgment": [fatal,passing]}), tool_verifier=tool)
        result = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertEqual(result.quality_gate, "ACCEPT_VERIFIED")
        self.assertEqual(engine.last_trajectory["transition_labels"][-1]["label"], "GOOD_REVISION")

    def test_explicit_quality_mode_uses_offline_separate_judge(self):
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, quality_evaluation=True), provider=SimpleGenerator())
        result = engine.run("Write a proposal", mode="normal", max_cycles=1)
        self.assertEqual(engine.last_trajectory["schema_version"], "3.0")
        self.assertTrue(engine.last_trajectory["judgments"])
        self.assertEqual(result.quality_gate, "ACCEPT_PROVISIONALLY")

    def test_legacy_demos_remain_compatible_but_unjudged(self):
        from end_engine.demo import TASK
        from end_engine.models.production_mock import PRODUCTION_TASK, ProductionAgentMockProvider
        for task, provider in ((TASK, MockProvider()), (PRODUCTION_TASK, ProductionAgentMockProvider())):
            engine = EndEngine(EngineConfig(ledger_dir=self.temp.name), provider=provider)
            result = engine.run(task, mode="deep", max_cycles=8)
            self.assertIn(result.termination_reason.value, ("QUALITY_THRESHOLD_REACHED", "BUDGET_EXHAUSTED"))
            if isinstance(provider, ProductionAgentMockProvider):
                self.assertEqual(result.termination_reason.value, "BUDGET_EXHAUSTED")
            self.assertEqual(result.quality_gate, "BLOCKED")
            self.assertEqual(result.acceptance_label, "INCONCLUSIVE")
            self.assertEqual(engine.last_trajectory["judgments"], [])

    def test_failing_abstract_model_and_corrected_model_are_distinct(self):
        self.assertFalse(rollback_model(CANDIDATES[2])["passed"])
        self.assertTrue(rollback_model(CANDIDATES[3])["passed"])
        self.assertFalse(rollback_model(CANDIDATES[4])["passed"])
        self.assertEqual(rollback_model(CANDIDATES[3])["orderings"], 6)
