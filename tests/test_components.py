from dataclasses import replace
import unittest

from end_engine import EngineConfig, MockProvider
from end_engine.core.question_selector import AdaptiveQuestionSelector, LLMQuestionSelector, SelectionContext
from end_engine.core.state import (Candidate, Complexity, ReasoningBudget, StopReason, VerificationResult,
                                   Weakness, WeaknessStatus, WeaknessUpdate, now)
from end_engine.core.task_analyzer import TaskAnalyzer
from end_engine.core.termination import TerminationController
from end_engine.core.weaknesses import WeaknessRegistry
from end_engine.demo import TASK
from end_engine.models.schema import CANDIDATE, validate
from end_engine.operators import default_operators
from end_engine.verification import BasicRuleVerifier, LLMVerifier


class ComponentTests(unittest.TestCase):
    def candidate(self, content="A proposed solution"):
        return Candidate("C0", None, 0, content, now())

    def context(self, **kwargs):
        base = SelectionContext(TASK, self.candidate(), (), (), (), 0, 6,
                                ("correctness", "architecture", "failure_modes", "alternatives"), 4)
        return replace(base, **kwargs)

    def test_all_seventeen_operators_are_independently_callable(self):
        operators = default_operators()
        self.assertEqual(len(operators), 17)
        for name, operator in operators.items():
            with self.subTest(operator=name):
                output = operator.execute(MockProvider(), task=TASK, candidate=self.candidate())
                self.assertTrue(output["summary"])
                self.assertTrue(output["findings"])
                self.assertTrue(operator.purpose and operator.trigger_conditions and operator.expected_output_type)

    def test_selector_varies_operators_and_responds_to_open_weakness(self):
        selector, operators = AdaptiveQuestionSelector(), default_operators()
        used = []
        for iteration in range(6):
            selected = selector.select(self.context(iteration=iteration, operators_used=tuple(used), remaining_budget=6-iteration), operators)
            if used:
                self.assertNotEqual(selected.operator, used[-1])
            used.append(selected.operator)
        self.assertGreaterEqual(len(set(used)), 4)
        weakness = Weakness("W001", "failure_mode", "critical", "Recovery corrupts state", "No crash recovery")
        choice = selector.select(self.context(iteration=1, unresolved_weaknesses=(weakness,), operators_used=("ASSUMPTION",)), operators)
        self.assertEqual(choice.operator, "WHAT_BREAKS")
        self.assertIn("W001", choice.reason)

    def test_llm_repeat_guard(self):
        provider = MockProvider(scripted={"selection": [{"operator": "ASSUMPTION", "reason": "Repeat", "priority": 1.0}]})
        result = LLMQuestionSelector().select(self.context(operators_used=("ASSUMPTION",)), default_operators(), provider)
        self.assertNotEqual(result.operator, "ASSUMPTION")
        self.assertIn("Repeat guard", result.reason)

    def test_analyzer_uses_structure_without_domain_keywords(self):
        task = "\n".join(f"{i}. The result must meet condition {i} without exceeding limit {i}." for i in range(10))
        self.assertEqual(TaskAnalyzer().analyze(task).complexity, Complexity.DEEP)
        self.assertEqual(TaskAnalyzer().analyze("Explain a simple loop").complexity, Complexity.NORMAL)
        self.assertEqual(TaskAnalyzer().analyze("Use maximum quality for this answer").complexity, Complexity.CRITICAL)

    def test_weakness_transitions_preserve_snapshots_and_reopen(self):
        registry = WeaknessRegistry()
        finding = {"weakness_id": None, "type": "constraint", "severity": "high",
                   "description": "Missing quota", "evidence": "No explicit bound"}
        original = registry.ingest([finding], 0)[0]
        for status in (WeaknessStatus.RESOLVED, WeaknessStatus.ACCEPTED_RISK, WeaknessStatus.INVALIDATED):
            registry.apply_updates((WeaknessUpdate("W001", status, "A documented justification"),))
            self.assertEqual(registry.snapshot()[0].status, status)
        self.assertEqual(original.status, WeaknessStatus.OPEN)
        registry.ingest([finding], 2)
        self.assertEqual(registry.snapshot()[0].status, WeaknessStatus.OPEN)
        self.assertEqual(registry.snapshot()[0].occurrences, 2)
        with self.assertRaises(ValueError):
            registry.apply_updates((WeaknessUpdate("W999", WeaknessStatus.RESOLVED, "unknown"),))

    def test_unknown_critique_ids_rejected(self):
        registry = WeaknessRegistry()
        with self.assertRaises(ValueError):
            registry.ingest([{"weakness_id": "W999"}], 0)

    def test_rule_verifier_checks_explicit_requirements(self):
        verifier = BasicRuleVerifier(required_terms=("quota", "recovery"), forbidden_terms=("unlimited",))
        passed = verifier.verify(TASK, self.candidate("Quota with crash recovery"), {})
        failed = verifier.verify(TASK, self.candidate("Unlimited storage"), {})
        self.assertTrue(passed.passed)
        self.assertFalse(failed.passed)
        self.assertEqual(len(failed.remaining_issues), 3)

    def test_llm_verifier_does_not_accept_optimistic_overall_score(self):
        response = {"passed": True, "score": 0.99, "dimensions": {"correctness": 0.2, "clarity": 0.9},
                    "remaining_issues": [], "weakness_updates": []}
        verifier = LLMVerifier(MockProvider(scripted={"verification": [response]}))
        result = verifier.verify(TASK, self.candidate(), {"analysis": {"dimensions": ["correctness", "clarity"]},
                                                        "weaknesses": [], "verification": []})
        self.assertFalse(result.passed)
        self.assertAlmostEqual(result.score, 0.55)

    def test_schema_rejects_nonfinite_boolean_score_and_empty_content(self):
        for confidence, content in ((float("nan"), "text"), (True, "text"), (1.2, "text"), (0.5, "  ")):
            with self.subTest(confidence=confidence, content=content), self.assertRaises(ValueError):
                validate({"content": content, "known_strengths": [], "confidence": confidence}, CANDIDATE)

    def test_bad_configuration_and_budgets_are_rejected(self):
        for kwargs in ({"quality_threshold": float("nan")}, {"stagnation_patience": 0},
                       {"quality_threshold": 0.98, "critical_quality_threshold": 0.95}):
            with self.assertRaises(ValueError):
                EngineConfig(**kwargs)
        with self.assertRaises(ValueError):
            ReasoningBudget(3, 2, 1)


class TerminationTests(unittest.TestCase):
    def decision(self, **overrides):
        arguments = {"analysis": TaskAnalyzer().analyze(TASK), "iterations": 2,
                     "verification": VerificationResult(False, 0.7, (("correctness", 0.7),), ()),
                     "scores": (0.5, 0.6, 0.7), "weaknesses": ()}
        arguments.update(overrides)
        return TerminationController(EngineConfig()).evaluate(**arguments)

    def test_minimum_scrutiny_precedes_quality(self):
        good = VerificationResult(True, 0.99, (("correctness", 0.99),), ())
        self.assertIsNone(self.decision(iterations=1, verification=good).reason)
        self.assertEqual(self.decision(verification=good).reason, StopReason.QUALITY_THRESHOLD_REACHED)

    def test_high_severity_open_issue_blocks_quality_and_pass(self):
        issue = Weakness("W001", "failure_mode", "high", "Data loss", "No recovery")
        good = VerificationResult(True, 0.99, (("correctness", 0.99),), ())
        self.assertIsNone(self.decision(verification=good, weaknesses=(issue,)).reason)

    def test_failed_verification_cannot_claim_quality(self):
        result = VerificationResult(False, 0.99, (("correctness", 0.99),), ())
        self.assertIsNone(self.decision(verification=result).reason)

    def test_critical_uses_higher_quality_threshold(self):
        analysis = TaskAnalyzer().analyze(TASK, mode="critical")
        good = VerificationResult(True, 0.91, (("correctness", 0.91),), ())
        self.assertIsNone(self.decision(analysis=analysis, iterations=3, verification=good).reason)

    def test_verifier_passed_and_external_blocker(self):
        good = VerificationResult(True, 0.85, (("correctness", 0.85),), ())
        self.assertEqual(self.decision(verification=good).reason, StopReason.VERIFIER_PASSED)
        self.assertEqual(self.decision(external_blocker="dependency unavailable").reason, StopReason.EXTERNAL_BLOCKER)

    def test_target_is_not_a_hard_stop(self):
        self.assertIsNone(self.decision(iterations=4, scores=(0.2, 0.3, 0.4, 0.5, 0.7)).reason)

    def test_score_regression_is_no_material_improvement(self):
        self.assertEqual(self.decision(scores=(0.8, 0.7, 0.6)).reason, StopReason.NO_MATERIAL_IMPROVEMENT)
