from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider
from end_engine.cognition.branches import BranchController, SynthesisPlanner, CognitiveBranch
from end_engine.cognition.deduplication import TokenFindingDeduplicator
from end_engine.cognition.knowledge import KnowledgeRegister
from end_engine.cognition.policy import UtilitySelectionPolicy
from end_engine.cognition.questions import QuestionGenerator
from end_engine.cognition.session import CognitiveSession, MetaController
from end_engine.cognition.state import (Assumption, AssumptionStatus, Claim, CognitiveState, CoverageLevel,
    EvidenceStatus, InformationGain, OperatorOutcome, OutcomeStats, QuestionTarget, TargetType)
from end_engine.core.state import Candidate, StopReason, VerificationResult, Weakness, now, to_data
from end_engine.core.task_analyzer import TaskAnalyzer
from end_engine.core.termination import TerminationController
from end_engine.core.weaknesses import WeaknessRegistry
from end_engine.experience import JsonLedger, Trajectory
from end_engine.experience.serializer import dumps, loads
from end_engine.models.production_mock import PRODUCTION_TASK, ProductionAgentMockProvider
from end_engine.operators import default_operators


def candidate(content="The journal guarantees recoverability. Assume rollback can undo every side effect."):
    return Candidate("C0", None, 0, content, now())


def state(**changes):
    base = CognitiveState("C0", 0, "deep", uncertain_dimensions=("failure_modes", "alternatives", "evidence"),
        coverage=(("failure_modes", CoverageLevel.NONE), ("alternatives", CoverageLevel.NONE),
                  ("evidence", CoverageLevel.NONE), ("assumptions", CoverageLevel.NONE)),
        remaining_budget=(("cycles", 6), ("operations", 9)))
    return replace(base, **changes)


def outcome(op="WHAT_BREAKS", target="W001", level="ZERO", duplicates=0):
    operator = default_operators()[op]
    return OperatorOutcome(op, operator.family, target, operator.purpose, "Q001", (), InformationGain(level, duplicates=duplicates))


class BrainComponentTests(unittest.TestCase):
    def setUp(self):
        self.operators = default_operators()
        self.trajectory = Trajectory(PRODUCTION_TASK, {}, {})
        self.analysis = TaskAnalyzer().analyze(PRODUCTION_TASK, mode="deep")
        self.config = EngineConfig()
        self.session = CognitiveSession(self.analysis, self.config, self.trajectory)

    def test_operator_metadata_and_taxonomy_available(self):
        families = set()
        for op in self.operators.values():
            metadata = to_data(op)
            families.add(op.family)
            self.assertTrue(metadata["targets"] and metadata["best_when"] and metadata["poor_when"])
            self.assertTrue(metadata["compatible_followups"])
            self.assertTrue(0 <= metadata["cost"] <= 1)
        self.assertEqual(len(families), 7)
        self.assertTrue(self.operators["ALTERNATIVE"].can_branch)
        self.assertFalse(self.operators["WHY"].can_branch)

    def test_state_reflects_structured_artifacts(self):
        registry = WeaknessRegistry()
        registry.ingest([{"weakness_id": None, "type": "failure_mode", "severity": "high",
                          "description": "Journal recovery is incomplete", "evidence": "No atomic commit"}], 0)
        self.session.knowledge.observe_candidate(candidate())
        self.session.consume()
        current = self.session.state(candidate(), registry, (0.5, 0.58))
        self.assertEqual(current.high_severity_weaknesses, ("W001",))
        self.assertEqual(len(current.claims_without_evidence), 2)
        self.assertEqual(len(current.assumptions), 1)
        self.assertAlmostEqual(current.recent_improvement, 0.08)
        self.assertEqual(dict(current.remaining_budget)["operations"], 8)
        self.assertEqual(self.trajectory.snapshot()["cognitive_states"][-1], to_data(current))

    def test_utility_factors_reconstruct_ranked_score(self):
        policy = UtilitySelectionPolicy()
        ranked = policy.rank(state(), self.operators)
        self.assertEqual(len(ranked), 17)
        self.assertEqual([r.utility for r in ranked], sorted((r.utility for r in ranked), reverse=True))
        for r in ranked:
            f = r.scores
            expected = f.relevance*f.information_gain*f.issue_value*f.novelty*f.task_importance-f.repetition_penalty-f.cost_penalty+f.meta_adjustment
            self.assertAlmostEqual(r.utility, expected, places=5)

    def test_low_value_same_question_penalized(self):
        weakness = Weakness("W001", "failure_mode", "high", "Recovery loses data", "No journal")
        clean = state(open_weaknesses=(weakness,))
        repeated = replace(clean, recent_outcomes=(outcome(), outcome(duplicates=2)))
        policy = UtilitySelectionPolicy()
        before = next(r for r in policy.rank(clean, self.operators) if r.operator == "WHAT_BREAKS")
        after = next(r for r in policy.rank(repeated, self.operators) if r.operator == "WHAT_BREAKS")
        self.assertLess(after.utility, before.utility)
        self.assertGreater(after.scores.repetition_penalty, before.scores.repetition_penalty)

    def test_same_operator_can_target_new_issue(self):
        weakness = Weakness("W002", "failure_mode", "critical", "Recovery corrupts a new partition", "No fencing")
        s = state(open_weaknesses=(weakness,), recent_outcomes=(outcome(target="W001", level="HIGH"),))
        selected = UtilitySelectionPolicy().select(s, self.operators)
        self.assertEqual(selected.operator, "WHAT_BREAKS")
        self.assertEqual(selected.target.target_id, "W002")
        self.assertLess(selected.scores.repetition_penalty, 0.1)

    def test_question_text_and_identity_follow_target(self):
        generator = QuestionGenerator()
        first = QuestionTarget(TargetType.CLAIM, "CL001", "Throughput scales linearly", "evidence")
        second = QuestionTarget(TargetType.CLAIM, "CL002", "Recovery is atomic", "evidence")
        q1 = generator.generate(self.operators["EVIDENCE"], first, question_id="Q001", parent_step=3)
        q2 = generator.generate(self.operators["EVIDENCE"], second, question_id="Q002", parent_step=4)
        self.assertNotEqual(q1.question, q2.question)
        self.assertIn("Recovery is atomic", q2.question)
        self.assertEqual(q2.parent_step, 4)

    def test_claims_extracted_deduplicated_and_status_tracked(self):
        knowledge = self.session.knowledge
        knowledge.observe_candidate(candidate())
        previous = knowledge.claims["CL001"]
        knowledge.observe_candidate(replace(candidate(), candidate_id="C1", iteration=1))
        self.assertEqual(len(knowledge.claims), 2)
        knowledge.update("CL001", "SUPPORTED", "Replay check covers this design claim")
        self.assertEqual(previous.evidence_status, EvidenceStatus.UNVERIFIED)
        self.assertEqual(knowledge.claims["CL001"].evidence_status, EvidenceStatus.SUPPORTED)
        self.assertEqual(knowledge.claims["CL001"].source_candidate, "C0")

    def test_assumption_status_transitions_are_explicit(self):
        knowledge = self.session.knowledge
        assumption, _ = knowledge.add_assumption("Rollback undoes side effects", "C0")
        for status in AssumptionStatus:
            knowledge.update(assumption.assumption_id, status.value, "Recorded justification", assumption=True)
            self.assertEqual(knowledge.assumptions[assumption.assumption_id].status, status)
        self.assertEqual(assumption.status, AssumptionStatus.UNTESTED)
        with self.assertRaises(ValueError):
            knowledge.update("A999", "SUPPORTED", "Missing ID", assumption=True)

    def test_information_gain_and_family_statistics(self):
        op = self.operators["ASSUMPTION"]
        target = QuestionTarget(TargetType.ASSUMPTION, "A001", "A questionable dependency", "assumptions")
        question = QuestionGenerator().generate(op, target, question_id="Q1", parent_step=0)
        finding = Weakness("W001", "assumption", "high", "Hidden dependency", "Missing guarantee")
        gain = self.session.complete(op, question, (finding,), set(), 1).information_gain
        self.assertEqual(gain.level, "HIGH")
        s = self.session.state(candidate(), WeaknessRegistry())
        self.assertEqual(dict(s.operator_statistics)["ASSUMPTION"].high_gain, 1)
        self.assertEqual(dict(s.family_statistics)["epistemic"].uses, 1)
        again = self.session.complete(op, question, (finding,), {"W001"}, 0)
        self.assertEqual(again.information_gain.level, "LOW")
        self.assertEqual(again.information_gain.duplicates, 1)

    def test_high_gain_history_increases_relevant_utility(self):
        weakness = Weakness("W009", "failure_mode", "high", "New recovery uncertainty", "Unexamined path")
        baseline = state(open_weaknesses=(weakness,))
        helpful = replace(baseline, operator_statistics=(("WHAT_BREAKS", OutcomeStats(uses=2, high_gain=2)),))
        exhausted = replace(baseline, operator_statistics=(("WHAT_BREAKS", OutcomeStats(uses=2, zero_gain=2)),))
        policy = UtilitySelectionPolicy()
        scores = [next(r.utility for r in policy.rank(s, self.operators) if r.operator == "WHAT_BREAKS")
                  for s in (baseline, helpful, exhausted)]
        self.assertGreater(scores[1], scores[0])
        self.assertLess(scores[2], scores[0])

    def test_coverage_is_scrutiny_not_verifier_quality(self):
        op = self.operators["WHAT_BREAKS"]
        q = QuestionGenerator().generate(op, QuestionTarget(TargetType.COMPONENT, "C0:failure_modes", "Recovery", "failure_modes"),
                                         question_id="Q1", parent_step=1)
        self.session.complete(op, q, (), set(), 0)
        self.assertEqual(dict(self.session.state(candidate(), WeaknessRegistry()).coverage)["failure_modes"], CoverageLevel.NONE)
        self.session.complete(op, q, (Weakness("W001", "failure_mode", "high", "Loss", "No recovery"),), set(), 0)
        self.assertEqual(dict(self.session.state(candidate(), WeaknessRegistry()).coverage)["failure_modes"], CoverageLevel.MEDIUM)

    def test_duplicate_findings_cannot_manufacture_high_coverage(self):
        op = self.operators["WHAT_BREAKS"]
        question = QuestionGenerator().generate(op, QuestionTarget(TargetType.WEAKNESS, "W001", "Recovery", "failure_modes"),
                                                question_id="Q1", parent_step=0)
        finding = Weakness("W001", "failure_mode", "high", "Recovery gap", "Missing log")
        for _ in range(6):
            self.session.complete(op, question, (finding,), {"W001"}, 0)
        current = self.session.state(candidate(), WeaknessRegistry(), verification=VerificationResult(
            True, 0.99, (("correctness", 0.99),), ()))
        self.assertEqual(dict(current.coverage)["failure_modes"], CoverageLevel.LOW)
        self.assertIn("correctness", current.resolved_dimensions)
        self.assertEqual(dict(current.coverage)["correctness"], CoverageLevel.NONE)

    def test_meta_check_changes_priority_without_candidate_mutation(self):
        repeated = state(recent_outcomes=(outcome(), outcome(), outcome()))
        meta = MetaController().check(repeated)
        self.assertGreater(meta["priority_adjustments"]["search"], 0)
        changed = replace(repeated, priority_adjustments=tuple(meta["priority_adjustments"].items()))
        policy = UtilitySelectionPolicy()
        before = next(r.utility for r in policy.rank(repeated, self.operators) if r.operator == "ALTERNATIVE")
        after = next(r.utility for r in policy.rank(changed, self.operators) if r.operator == "ALTERNATIVE")
        self.assertGreater(after, before)

    def test_reframing_preserves_goal_and_has_a_limit(self):
        proposal = {"reframed_problem": "Inspect authority boundaries", "reason": "Coupled release authority", "confidence": 0.9}
        first = self.session.reframe(proposal, PRODUCTION_TASK, "C0")
        self.assertEqual(first["original_problem"], PRODUCTION_TASK)
        self.assertFalse(first["goal_replaced"])
        self.assertEqual(self.trajectory.snapshot()["task"]["content"], PRODUCTION_TASK)
        self.assertIsNone(self.session.reframe(proposal, PRODUCTION_TASK, "C1"))

    def test_deduplication_handles_overlap_but_respects_target_and_negation(self):
        dedup = TokenFindingDeduplicator()
        existing = (Weakness("W001", "failure_mode", "high", "Recovery journal lacks atomic commit guarantees", "Gap", target_id="journal"),)
        paraphrase = {"type": "failure_mode", "description": "The recovery journal lacks atomic commit guarantees"}
        self.assertEqual(dedup.match(paraphrase, existing, "journal"), "W001")
        self.assertIsNone(dedup.match(paraphrase, existing, "replica"))
        self.assertIsNone(dedup.match({**paraphrase, "description": "Recovery journal does not lack atomic commit guarantees"}, existing, "journal"))


class BranchTests(unittest.TestCase):
    def manager(self, **config):
        configuration = EngineConfig(**config)
        trajectory = Trajectory(PRODUCTION_TASK, {}, {})
        session = CognitiveSession(TaskAnalyzer().analyze(PRODUCTION_TASK, mode="deep"), configuration, trajectory)
        return BranchController(configuration, trajectory, session), trajectory, session

    def test_branch_active_limit_and_budget(self):
        manager, _, session = self.manager(max_active_branches=2)
        op = default_operators()["ALTERNATIVE"]
        manager.add("C0", op, "One", "Content")
        manager.add("C0", op, "Two", "Content")
        self.assertEqual(session.operations_used, 2)
        with self.assertRaises(ValueError):
            manager.add("C0", op, "Three", "Content")

    def test_branch_per_operator_limit(self):
        manager, _, _ = self.manager(max_active_branches=3, max_branches_per_operator=1)
        op = default_operators()["ALTERNATIVE"]
        manager.add("C0", op, "One", "Content")
        with self.assertRaisesRegex(ValueError, "Per-operator"):
            manager.add("C0", op, "Two", "Content")

    def test_branch_depth_limit_and_ancestry(self):
        manager, _, _ = self.manager(max_branch_depth=2, max_active_branches=4)
        op = default_operators()["ALTERNATIVE"]
        parent = manager.add("C0", op, "Parent", "Content")
        child = manager.add("C0", op, "Child", "Content", parent_branch_id=parent.branch_id)
        self.assertEqual(child.depth, 2)
        with self.assertRaises(ValueError):
            manager.add("C0", op, "Too deep", "Content", parent_branch_id=child.branch_id)
        with self.assertRaises(ValueError):
            manager.add("C1", op, "Wrong ancestry", "Content", parent_branch_id=parent.branch_id)

    def test_nonbranching_operator_rejected(self):
        manager, _, _ = self.manager()
        with self.assertRaises(ValueError):
            manager.add("C0", default_operators()["WHY"], "Hypothesis", "Content")

    def test_branch_generation_over_limit_is_rejected_before_creation(self):
        manager, trajectory, _ = self.manager(max_branches_per_operator=1)
        provider = ProductionAgentMockProvider(scripted={"branch_generation": [{"branches": [
            {"hypothesis": "a", "content": "x"}, {"hypothesis": "b", "content": "y"}]}]})
        with self.assertRaises(ValueError):
            manager.explore(PRODUCTION_TASK, candidate(), default_operators()["ALTERNATIVE"], None, ("correctness",), provider)
        self.assertEqual(trajectory.snapshot()["branches"], [])

    def test_rejected_branches_retained_and_multiple_sources_synthesized(self):
        manager, trajectory, _ = self.manager()
        plan, branches = manager.explore(PRODUCTION_TASK, candidate(), default_operators()["ALTERNATIVE"],
                                          None, ("correctness", "robustness"), ProductionAgentMockProvider())
        self.assertEqual([b.status for b in branches], ["REJECTED", "MERGED", "MERGED"])
        self.assertEqual({e.branch for e in plan.adopt}, {"B2", "B3"})
        self.assertEqual(plan.reject[0].branch, "B1")
        self.assertEqual(len(trajectory.snapshot()["branch_evaluations"]), 3)
        self.assertGreater(len(branches[0].evaluation.scores), 1)
        self.assertEqual(plan.source_branches, ("B1", "B2", "B3"))

    def test_default_mock_supports_branch_pipeline_offline(self):
        manager, _, _ = self.manager()
        plan, branches = manager.explore(PRODUCTION_TASK, candidate(), default_operators()["ALTERNATIVE"],
                                          None, ("correctness",), MockProvider())
        self.assertEqual(len(plan.adopt), 3)
        self.assertTrue(all(b.status == "MERGED" for b in branches))

    def test_synthesis_rejects_unknown_or_rejected_adoptions(self):
        branch = CognitiveBranch("B1", "C0", "ALTERNATIVE", "unsafe", "content", status="REJECTED")
        provider = MockProvider(scripted={"synthesis": [{"source_branches": ["B1"],
            "adopt": [{"branch": "B1", "element": "unsafe component"}], "reject": []}]})
        with self.assertRaises(ValueError):
            SynthesisPlanner().synthesize(PRODUCTION_TASK, candidate(), (branch,), provider)


class CognitiveTerminationTests(unittest.TestCase):
    def evaluate(self, s, **kwargs):
        arguments = dict(analysis=TaskAnalyzer().analyze(PRODUCTION_TASK, mode=s.complexity), iterations=3,
            verification=VerificationResult(True, 0.98, (("correctness", 0.98),), ()),
            scores=(0.5, 0.6, 0.8, 0.98), weaknesses=(), cognitive_state=s)
        arguments.update(kwargs)
        return TerminationController(EngineConfig()).evaluate(**arguments)

    def test_critical_missing_coverage_blocks_premature_success(self):
        s = state(complexity="critical")
        self.assertIsNone(self.evaluate(s).reason)
        self.assertEqual(self.evaluate(s, iterations=8).reason, StopReason.BUDGET_EXHAUSTED)

    def test_severe_assumptions_and_evidence_gaps_block_critical(self):
        covered = tuple((d, CoverageLevel.HIGH) for d in ("failure_modes", "evidence", "alternatives"))
        for additions in ({"assumptions": (Assumption("A1", "Safety assumption", "C0"),)},
                          {"claims_without_evidence": (Claim("CL1", "Unverified guarantee", "technical", "C0"),)}):
            with self.subTest(additions=additions):
                self.assertIsNone(self.evaluate(state(complexity="critical", coverage=covered, **additions)).reason)

    def test_diminishing_cognitive_value_stops(self):
        s = state(coverage=(("evidence", CoverageLevel.HIGH),), recent_outcomes=(outcome(), outcome(), outcome()))
        self.assertEqual(self.evaluate(s).reason, StopReason.NO_MATERIAL_IMPROVEMENT)

    def test_active_branches_prevent_success(self):
        self.assertIsNone(self.evaluate(state(active_branches=("B1",))).reason)

    def test_shared_operation_budget_exhaustion(self):
        self.assertEqual(self.evaluate(state(remaining_budget=(("operations", 0),))).reason, StopReason.BUDGET_EXHAUSTED)


class BrainIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def engine(self, **config):
        return EndEngine(EngineConfig(ledger_dir=self.directory.name, **config), provider=ProductionAgentMockProvider())

    def test_deep_run_branches_questions_and_synthesis_are_real_stages(self):
        engine = self.engine()
        result = engine.run(PRODUCTION_TASK, mode="deep", max_cycles=8)
        record = engine.last_trajectory
        self.assertEqual(record["errors"], [])
        self.assertEqual(len(record["branches"]), 3)
        self.assertEqual(result.termination_reason, StopReason.QUALITY_THRESHOLD_REACHED)
        self.assertEqual(len(record["questions"]), result.iterations)
        self.assertTrue(record["operator_utilities"])
        self.assertTrue(record["meta_checks"])
        synthesis_call = next(c for c in record["model_calls"] if c["request"]["purpose"] == "synthesis")
        self.assertEqual(len(synthesis_call["request"]["context"]["branches"]), 3)
        plans = [c for c in record["model_calls"] if c["request"]["purpose"] == "revision_plan"]
        self.assertTrue(any(c["request"]["context"]["synthesis"] for c in plans))

    def test_fast_and_normal_do_not_branch_by_default(self):
        for mode in ("fast", "normal"):
            engine = self.engine()
            engine.run(PRODUCTION_TASK, mode=mode)
            self.assertEqual(engine.last_trajectory["branches"], [])

    def test_critical_demo_is_bounded_and_does_not_replace_goal(self):
        engine = self.engine()
        result = engine.run(PRODUCTION_TASK, mode="critical", max_cycles=8)
        record = engine.last_trajectory
        self.assertEqual(result.termination_reason, StopReason.QUALITY_THRESHOLD_REACHED)
        self.assertEqual(result.iterations, 5)
        self.assertEqual(record["task"]["content"], PRODUCTION_TASK)
        self.assertEqual(len(record["reframings"]), 1)
        self.assertTrue(all(c["request"]["context"].get("task", PRODUCTION_TASK) == PRODUCTION_TASK for c in record["model_calls"]))
        self.assertEqual(len(record["branches"]), 3)
        self.assertEqual(len(record["operator_outcomes"]), 5)

    def test_v02_round_trip_and_v01_compatibility(self):
        engine = self.engine()
        result = engine.run(PRODUCTION_TASK, mode="critical")
        record = engine.last_trajectory
        self.assertEqual(record["schema_version"], "2.0")
        self.assertEqual(JsonLedger().load(result.trajectory_path), record)
        self.assertEqual(loads(dumps(record)), record)
        legacy_path = Path(__file__).resolve().parents[1]/"demo_output"/"7744de05-e9ac-4e42-bd65-18a1889026ba.jsonl"
        original = legacy_path.read_text(encoding="utf-8")
        legacy = loads(original)
        self.assertEqual(legacy["schema_version"], "1.0")
        self.assertEqual(legacy, json.loads(original))

    def test_sequential_runs_do_not_leak_cognitive_state(self):
        engine = self.engine()
        first = engine.run(PRODUCTION_TASK, mode="critical")
        old = engine.last_trajectory
        second = engine.run(PRODUCTION_TASK, mode="critical")
        new = engine.last_trajectory
        self.assertNotEqual(first.trajectory_id, second.trajectory_id)
        for field in ("operator_statistics", "cognitive_coverage", "questions", "branches", "claims", "assumptions"):
            self.assertEqual(old[field], new[field])

    def test_branch_failure_preserves_rejected_and_exhausts_active_records(self):
        provider = ProductionAgentMockProvider(scripted={"synthesis": [RuntimeError("Synthesis unavailable")]})
        engine = EndEngine(EngineConfig(ledger_dir=self.directory.name), provider=provider)
        result = engine.run(PRODUCTION_TASK, mode="critical")
        self.assertEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        self.assertEqual([b["status"] for b in engine.last_trajectory["branches"]], ["REJECTED", "EXHAUSTED", "EXHAUSTED"])
        self.assertEqual(len(engine.last_trajectory["branch_evaluations"]), 3)
        self.assertTrue(JsonLedger().load(result.trajectory_path)["errors"])

    def test_branching_consumes_shared_budget_and_cannot_explode(self):
        engine = self.engine(max_cognitive_operations=6)
        result = engine.run(PRODUCTION_TASK, mode="critical", max_cycles=8)
        record = engine.last_trajectory
        self.assertEqual(result.termination_reason, StopReason.BUDGET_EXHAUSTED)
        used = len(record["questions"])+len(record["branches"])
        self.assertLessEqual(used, 6)
        self.assertLessEqual(len(record["branches"]), 3)

    def test_no_complete_trajectory_dump_in_cognitive_calls(self):
        engine = self.engine()
        engine.run(PRODUCTION_TASK, mode="critical")
        for call in engine.last_trajectory["model_calls"]:
            self.assertNotIn("steps", call["request"]["context"])
            self.assertNotIn("model_calls", call["request"]["context"])
