from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.core.state import StopReason, VerificationResult, WeaknessStatus
from end_engine.demo import TASK
from end_engine.experience import JsonLedger
from end_engine.verification import BasicRuleVerifier


class FixedVerifier:
    def __init__(self, score=0.4, passed=False):
        self.score, self.passed = score, passed

    def verify(self, task, candidate, trajectory):
        return VerificationResult(self.passed, self.score, (("test_dimension", self.score),), ())


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def engine(self, **kwargs):
        config = kwargs.pop("config", EngineConfig(ledger_dir=self.directory.name))
        return EndEngine(config, **kwargs)

    def test_fast_transform_does_not_recurse(self):
        engine = self.engine()
        result = engine.run("uppercase hello world")
        self.assertEqual(result.answer, "HELLO WORLD")
        self.assertEqual(result.termination_reason, StopReason.FAST_PATH)
        self.assertEqual(result.iterations, 0)
        self.assertEqual(len(engine.last_trajectory["candidates"]), 1)
        self.assertEqual(engine.last_trajectory["critiques"], [])
        self.assertEqual([c["request"]["purpose"] for c in engine.last_trajectory["model_calls"]],
                         ["initial_candidate", "verification"])

    def test_deep_offline_demo_preserves_lineage_and_results(self):
        engine = self.engine()
        result = engine.run(TASK)
        record = engine.last_trajectory
        self.assertEqual(result.termination_reason, StopReason.QUALITY_THRESHOLD_REACHED)
        self.assertEqual(result.iterations, 2)
        self.assertEqual([c["parent_candidate_id"] for c in record["candidates"]], [None, "C0", "C1"])
        self.assertEqual([v["candidate_id"] for v in record["verification"]], ["C0", "C1", "C2"])
        self.assertEqual(len(record["revision_plans"]), 2)
        self.assertEqual(record["errors"], [])
        self.assertEqual(record["model"]["provider"], "mock")
        self.assertTrue(all(w["status"] == "resolved" for w in record["weaknesses"]))
        self.assertEqual(record["candidates"][1]["known_weaknesses"][0]["status"], "open")
        self.assertTrue(all("latency_ms" in call for call in record["model_calls"]))

    def test_max_cycles_override_and_zero_budget(self):
        for maximum in (0, 1):
            with self.subTest(maximum=maximum):
                engine = self.engine()
                result = engine.run(TASK, mode="deep", max_cycles=maximum)
                self.assertEqual(result.iterations, maximum)
                self.assertEqual(len(engine.last_trajectory["candidates"]), maximum + 1)
                self.assertEqual(result.termination_reason, StopReason.BUDGET_EXHAUSTED)

    def test_fast_mode_cannot_be_expanded_by_max_cycles(self):
        engine = self.engine()
        result = engine.run(TASK, mode="fast", max_cycles=9)
        self.assertEqual(result.iterations, 0)
        self.assertEqual(result.termination_reason, StopReason.FAST_PATH)

    def test_engine_hard_cap_survives_custom_controller(self):
        from end_engine.core.termination import TerminationDecision
        class ContinueForever:
            def evaluate(self, **kwargs):
                return TerminationDecision(None, "continue")
        result = self.engine(termination=ContinueForever()).run(TASK, max_cycles=1)
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.termination_reason, StopReason.BUDGET_EXHAUSTED)

    def test_candidate_is_immutable_and_public_snapshots_are_detached(self):
        from end_engine.core.state import Candidate, now
        candidate = Candidate("C0", None, 0, "original", now(), ("strength",))
        with self.assertRaises(FrozenInstanceError):
            candidate.content = "changed"
        with self.assertRaises(TypeError):
            candidate.known_strengths[0] = "changed"
        engine = self.engine()
        engine.run(TASK)
        external = engine.last_trajectory
        external["candidates"][0]["content"] = "mutated"
        self.assertNotEqual(engine.last_trajectory["candidates"][0]["content"], "mutated")

    def test_weaknesses_persist_without_verifier_resolution(self):
        engine = self.engine(verifier=FixedVerifier(score=0.99, passed=True))
        result = engine.run(TASK, max_cycles=2)
        record = engine.last_trajectory
        self.assertEqual(result.termination_reason, StopReason.BUDGET_EXHAUSTED)
        self.assertEqual(record["weaknesses"][0]["id"], "W001")
        self.assertEqual(record["weaknesses"][0]["status"], "open")
        self.assertEqual(record["candidates"][2]["known_weaknesses"][0]["id"], "W001")

    def test_diminishing_improvement_stops_before_cap(self):
        engine = self.engine(verifier=FixedVerifier())
        result = engine.run(TASK, max_cycles=8)
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.termination_reason, StopReason.NO_MATERIAL_IMPROVEMENT)
        self.assertTrue(engine.last_trajectory["weaknesses"])

    def test_repeated_findings_stop_without_forgetting_open_issue(self):
        finding = {"weakness_id": None, "type": "constraint", "severity": "high",
                   "description": "An explicit storage bound is missing", "evidence": "No quota"}
        provider = MockProvider(scripted={"critique": [{"summary": "Same gap", "findings": [finding]}] * 4})
        config = replace(EngineConfig(ledger_dir=self.directory.name), stagnation_patience=10)
        engine = self.engine(provider=provider, verifier=FixedVerifier(), config=config)
        result = engine.run(TASK, max_cycles=6)
        self.assertEqual(result.termination_reason, StopReason.REPEATED_CRITIQUE)
        self.assertEqual(result.iterations, 3)
        self.assertEqual(len(engine.last_trajectory["weaknesses"]), 1)
        self.assertEqual(engine.last_trajectory["weaknesses"][0]["occurrences"], 3)

    def test_jsonl_round_trip_preserves_complete_record(self):
        engine = self.engine()
        result = engine.run(TASK)
        path = Path(result.trajectory_path)
        self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)
        loaded = JsonLedger().load(path)
        self.assertEqual(loaded, engine.last_trajectory)
        self.assertEqual(json.loads(json.dumps(loaded)), loaded)
        self.assertEqual([s["step"] for s in loaded["steps"]], list(range(len(loaded["steps"]))))

    def test_provider_failure_keeps_partial_trajectory(self):
        provider = MockProvider(scripted={"revision": [RuntimeError("simulated outage")]})
        engine = self.engine(provider=provider)
        result = engine.run(TASK)
        record = JsonLedger().load(result.trajectory_path)
        self.assertEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        self.assertEqual(result.iterations, 0)
        self.assertEqual(record["errors"][0]["stage"], "revision")
        self.assertEqual(len(record["revision_plans"]), 1)
        self.assertIn("simulated outage", record["model_calls"][-1]["error"]["message"])

    def test_malformed_output_is_retained_and_stops_cleanly(self):
        provider = MockProvider(scripted={"critique": [ModelResponse("this is not JSON")]})
        engine = self.engine(provider=provider)
        result = engine.run(TASK)
        self.assertEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        self.assertEqual(engine.last_trajectory["model_calls"][-1]["response"]["content"], "this is not JSON")
        self.assertTrue(Path(result.trajectory_path).exists())

    def test_verification_failure_does_not_reuse_old_candidate_score(self):
        class FailAfterInitial(FixedVerifier):
            def verify(self, task, candidate, trajectory):
                if candidate.iteration:
                    raise RuntimeError("verification unavailable")
                return super().verify(task, candidate, trajectory)
        engine = self.engine(verifier=FailAfterInitial())
        result = engine.run(TASK)
        self.assertEqual(result.iterations, 1)
        self.assertIsNone(result.verification)
        self.assertEqual(len(engine.last_trajectory["verification"]), 1)

    def test_initial_failure_still_saves_execution(self):
        engine = self.engine(provider=MockProvider(scripted={"initial_candidate": [RuntimeError("offline failure")]}))
        result = engine.run(TASK)
        self.assertEqual(result.answer, "")
        self.assertEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        self.assertIsNone(engine.last_trajectory["final_candidate_id"])
        self.assertTrue(Path(result.trajectory_path).exists())

    def test_llm_classification_and_selection_are_recorded(self):
        config = EngineConfig(ledger_dir=self.directory.name, llm_classification=True, llm_selection=True)
        engine = self.engine(config=config)
        engine.run(TASK)
        calls = [c["request"]["purpose"] for c in engine.last_trajectory["model_calls"]]
        self.assertIn("classification", calls)
        self.assertEqual(calls.count("selection"), 2)
        self.assertEqual(engine.last_trajectory["analysis"]["source"], "llm")

    def test_explicit_mode_bypasses_llm_classification(self):
        provider = MockProvider(scripted={"classification": [RuntimeError("must not be called")]})
        engine = self.engine(provider=provider, config=EngineConfig(ledger_dir=self.directory.name, llm_classification=True))
        self.assertEqual(engine.run(TASK, mode="fast").termination_reason, StopReason.FAST_PATH)

    def test_usage_and_tool_calls_preserved(self):
        response = ModelResponse({"content": "HELLO", "known_strengths": [], "confidence": None},
                                 {"input_tokens": 10, "output_tokens": 3},
                                 ({"name": "example_check", "result": "fixture only"},))
        engine = self.engine(provider=MockProvider(scripted={"initial_candidate": [response]}), verifier=BasicRuleVerifier())
        engine.run("uppercase hello")
        record = engine.last_trajectory
        self.assertEqual(record["usage"]["totals"], {"input_tokens": 10, "output_tokens": 3})
        self.assertEqual(record["usage"]["reported_calls"], 1)
        self.assertEqual(len(record["tool_calls"]), 1)

    def test_separate_judge_provider_is_honored_and_recorded(self):
        from end_engine.verification import LLMVerifier
        class SeparateJudge(MockProvider):
            def metadata(self):
                return {"provider": "independent-mock", "model": "judge-fixture"}
        engine = self.engine(verifier=LLMVerifier(SeparateJudge()))
        engine.run(TASK)
        calls = engine.last_trajectory["model_calls"]
        self.assertEqual(len({call["call_id"] for call in calls}), len(calls))
        judges = [call for call in calls if call["request"]["purpose"] == "verification"]
        self.assertTrue(all(call["model"]["provider"] == "independent-mock" for call in judges))

    def test_invalid_provider_metadata_still_saves_failure(self):
        class BadMetadata(MockProvider):
            def metadata(self):
                return {"provider": object()}
        engine = self.engine(provider=BadMetadata())
        result = engine.run(TASK)
        self.assertEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        self.assertTrue(Path(result.trajectory_path).exists())
        self.assertEqual(engine.last_trajectory["errors"][0]["stage"], "provider_metadata")

    def test_storage_failure_propagates_and_leaves_recoverable_record(self):
        class FailedLedger:
            def save(self, record):
                raise OSError("disk full")
        engine = self.engine(ledger=FailedLedger())
        with self.assertRaisesRegex(OSError, "disk full"):
            engine.run("uppercase hello")
        self.assertEqual(engine.last_trajectory["errors"][-1]["stage"], "ledger_save")
        self.assertTrue(engine.last_trajectory["final_result"])

    def test_engine_is_reusable_without_cross_run_state(self):
        engine = self.engine()
        first = engine.run(TASK)
        second = engine.run(TASK)
        self.assertNotEqual(first.trajectory_id, second.trajectory_id)
        self.assertEqual(first.iterations, second.iterations)
        self.assertEqual(len(engine.last_trajectory["candidates"]), 3)

    def test_bad_inputs_fail_before_execution(self):
        engine = self.engine()
        for arguments in ({"task": ""}, {"task": "x", "max_cycles": -1}, {"task": "x", "max_cycles": True},
                          {"task": "x", "max_cycles": 1.2}, {"task": "x", "mode": "invalid"}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                engine.run(**arguments)
