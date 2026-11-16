from dataclasses import replace
import importlib
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.cognition.policy import UtilitySelectionPolicy
from end_engine.cognition.state import Claim, CognitiveState, EvidenceStatus, CoverageLevel
from end_engine.core.state import Weakness, VerificationResult
from end_engine.decisions import (DecisionConfig, DecisionRequest, DecisionResult, DecisionStatus,
    ChoiceDecision, BinaryDecision, ScoreDecision, ScriptedDecisionProvider, ReplayDecisionProvider)
from end_engine.decisions.context import DecisionContextBuilder
from end_engine.decisions.jev import JevDecisionProvider
from end_engine.decisions.providers import DecisionProvider
from end_engine.decisions.routing import DecisionRoutingSession, RoutingConstraints
from end_engine.decisions.types import DecisionProvenance, result_from_data, validate_result
from end_engine.experience import Trajectory, JsonLedger
from end_engine.models.budget import RunBudgetExceeded, RunCallBudget
from end_engine.operators import default_operators
from end_engine.quality.mock import MockJudgeProvider
from end_engine.verification import BasicRuleVerifier


def cognitive(**kwargs):
    state = CognitiveState("C0", 0, "deep", remaining_budget=(("operations", 9), ("cycles", 6)),
        coverage=tuple((d, CoverageLevel.NONE) for d in ("correctness", "architecture", "evidence", "alternatives")))
    return replace(state, **kwargs)


def choice(request, selected=None, *, probability=.99, confidence=.99):
    selected = selected or request.choices[0]
    others = [c for c in request.choices if c != selected]
    pairs = [(selected, probability if others else 1.0)]
    pairs += [(c,(1-probability)/len(others)) for c in others]
    return DecisionResult(request.question_id, "choice", DecisionStatus.SUCCESS,
        DecisionProvenance("scripted", request.requested_model, "fixture-pin", "fixture-request", usage=(("input_tokens", 12),)),
        ChoiceDecision(selected, tuple(pairs), confidence))


class FakeSDK:
    """Faithful in-memory SDK/transport contract; no HTTP client is constructed."""
    def __init__(self, result=None, error=None):
        self.result, self.error, self.requests, self.options = result, error, [], []
        for name in ("Choice", "Noul", "Score", "RetryPolicy"):
            setattr(self, name, lambda **kw: SimpleNamespace(**kw))
        sdk = self
        class Client:
            def __init__(self, **kw): sdk.options.append(kw)
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def system_one(self, **kw):
                sdk.requests.append(kw)
                if sdk.error: raise sdk.error
                return sdk.result
        self.TypeSafeClient = Client


def response(**answers):
    return SimpleNamespace(model="jev-fixture-pin", request_id="request-fixture", usage=SimpleNamespace(input_tokens=20, output_tokens=None),
                           choices=answers.get("choices",{}), nouls=answers.get("nouls",{}), scores=answers.get("scores",{}))


class PrimitiveTests(unittest.TestCase):
    def request(self, kind="choice"):
        return DecisionRequest("D1", kind, "A narrow question", '{}', choices=("a","b") if kind=="choice" else (),
            score_levels=("low","medium","high") if kind=="score" else (), requested_model="jev-fixture-pin")

    def adapt(self, request, sdk):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY":"fixture-only-not-a-real-credential"}):
            return JevDecisionProvider(requested_model="jev-fixture-pin", sdk_loader=lambda:sdk).evaluate(request)

    def test_choice_normalization_and_pinning(self):
        sdk = FakeSDK(response(choices={"D1":SimpleNamespace(choice="b", probabilities={"a":.12,"b":.88},confidence=.73)}))
        result = self.adapt(self.request(), sdk)
        self.assertEqual(result.value, ChoiceDecision("b", (("a",.12),("b",.88)), .73))
        self.assertEqual(result.provenance.requested_model, "jev-fixture-pin")
        self.assertEqual(result.provenance.resolved_model, "jev-fixture-pin")
        self.assertEqual(result.provenance.request_id, "request-fixture")
        self.assertEqual(result.provenance.usage, (("input_tokens",20),("output_tokens",None)))
        self.assertEqual(sdk.options[0]["retry"].max_retries, 0)
        self.assertEqual(len(sdk.requests), 1)

    def test_noul_normalization_has_no_invented_confidence(self):
        result = self.adapt(self.request("binary"), FakeSDK(response(nouls={"D1":SimpleNamespace(noul=.91)})))
        self.assertEqual(result.value, BinaryDecision(.91, True))
        self.assertNotIn("confidence", result.as_dict()["value"])
        self.assertEqual(result.provenance.evidence_type, "MODEL_JUDGMENT")

    def test_score_normalization_preserves_ordered_expectation(self):
        sdk = FakeSDK(response(scores={"D1":SimpleNamespace(score=1.7,probabilities={0:.1,1:.1,2:.8},
            legend={0:"low",1:"medium",2:"high"},confidence=.64)}))
        result = self.adapt(self.request("score"),sdk)
        self.assertEqual(result.value.ordered_score, 1.7)
        self.assertEqual(result.value.score_confidence, .64)
        self.assertEqual(dict(result.value.score_probabilities), {0:.1,1:.1,2:.8})

    def test_J8_no_universal_confidence_is_invented(self):
        self.assertFalse(hasattr(ChoiceDecision("a",(("a",1.0),),.8),"confidence"))
        self.assertFalse(hasattr(BinaryDecision(.8,True),"confidence"))
        self.assertFalse(hasattr(ScoreDecision(1.2,((0,.2),(1,.4),(2,.4)),((0,"a"),(1,"b"),(2,"c")),.7),"confidence"))

    def test_missing_key_is_local_unavailability(self):
        with patch.dict(os.environ, {}, clear=True):
            loader = lambda: self.fail("SDK must not load without a credential")
            result = JevDecisionProvider(requested_model="jev-pin",sdk_loader=loader).evaluate(replace(self.request(),requested_model="jev-pin"))
        self.assertEqual(result.status, DecisionStatus.UNAVAILABLE)
        self.assertEqual(result.failure_reason,"missing_api_key")
        self.assertIsNone(result.value)

    def test_missing_sdk_is_explicit(self):
        def missing(): raise ModuleNotFoundError("optional module absent",name="typesafe_sdk")
        with patch.dict(os.environ,{"TYPESAFE_API_KEY":"fixture-only-not-a-real-credential"}):
            result=JevDecisionProvider(requested_model="jev-fixture-pin",sdk_loader=missing).evaluate(self.request())
        self.assertEqual(result.failure_reason,"missing_sdk")

    def test_unrelated_import_failure_is_not_misreported(self):
        def broken(): raise ModuleNotFoundError("dependency broken",name="unrelated_dependency")
        with patch.dict(os.environ,{"TYPESAFE_API_KEY":"fixture-only-not-a-real-credential"}), self.assertRaises(ModuleNotFoundError):
            JevDecisionProvider(requested_model="jev-fixture-pin",sdk_loader=broken).availability()

    def test_timeout_connection_rate_limit_http_unknown_model(self):
        class HTTPError(Exception):
            def __init__(self,status): self.status=status
        for error, expected in ((TimeoutError("fixture"),DecisionStatus.TIMEOUT),(ConnectionError("fixture"),DecisionStatus.CONNECTION_FAILURE),
            (HTTPError(429),DecisionStatus.RATE_LIMITED),(HTTPError(500),DecisionStatus.HTTP_FAILURE),
            (HTTPError(404),DecisionStatus.UNKNOWN_MODEL),(HTTPError(401),DecisionStatus.AUTHENTICATION_FAILURE)):
            with self.subTest(expected=expected):
                result=self.adapt(self.request(),FakeSDK(error=error))
                self.assertEqual(result.status,expected)
                self.assertIsNone(result.value)

    def test_failure_messages_do_not_leak_credentials_or_headers(self):
        secret="fixture-only-not-a-real-credential"
        result=self.adapt(self.request(),FakeSDK(error=RuntimeError("Authorization Bearer "+secret)))
        self.assertNotIn(secret,json.dumps(result.as_dict()))
        self.assertNotIn("Authorization",json.dumps(result.as_dict()))

    def test_reflected_environment_credential_is_redacted_from_native_labels(self):
        credential="fixture-only-not-a-real-credential"
        sdk=FakeSDK(response(choices={"D1":SimpleNamespace(choice=credential,
                     probabilities={credential:.99,"other":.01},confidence=.99)}))
        result=self.adapt(self.request(),sdk)
        self.assertNotIn(credential,json.dumps(result.as_dict()))
        self.assertEqual(result.value.selected_choice,"[REDACTED]")

    def test_malformed_missing_answer_nan_and_nonfinite_probabilities(self):
        for raw in (response(),response(choices={"D1":SimpleNamespace(choice="a",probabilities={"a":float("nan"),"b":.2},confidence=.9)}),
                    response(choices={"D1":SimpleNamespace(choice="a",probabilities={"a":.2,"b":.2},confidence=.9)})):
            result=self.adapt(self.request(),FakeSDK(raw))
            self.assertEqual(result.status,DecisionStatus.MALFORMED)

    def test_normalized_values_roundtrip_without_sdk_types(self):
        req=self.request()
        original=choice(req,"b")
        self.assertEqual(result_from_data(json.loads(json.dumps(original.as_dict()))),original)

    def test_large_context_and_invalid_configuration_rejected(self):
        with self.assertRaises(ValueError): DecisionRequest("D1","choice","q",json.dumps({"data":"x"*9000}),choices=("a",))
        for kwargs in ({"max_calls_per_run":-1},{"timeout_seconds":float("nan")},{"categories":("evidence_relevance",)},
                       {"provider":"unknown"},{"min_choice_probability":2}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError): DecisionConfig(**kwargs)


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.operators=default_operators()
        self.state=cognitive()
        self.utility=UtilitySelectionPolicy()
        self.baseline=self.utility.select(self.state,self.operators)

    def session(self, responses, *, config=None, constraints=None, limit=30):
        trajectory=Trajectory("task",{},{});trajectory.configure_call_budget(limit)
        config=config or DecisionConfig(provider="scripted",max_utility_loss=10)
        return DecisionRoutingSession(config,ScriptedDecisionProvider(responses),trajectory,constraints),trajectory

    def test_valid_family_signal_is_advisory(self):
        session,trace=self.session((lambda req:choice(req,"epistemic"),))
        selected=session.select(self.state,self.operators,self.baseline)
        self.assertEqual(self.operators[selected.operator].family,"epistemic")
        self.assertEqual(trace.snapshot()["decisions"][0]["disposition"],"accepted")

    def test_J5_Jev_recommends_forbidden_operator_with_extremely_high_probability(self):
        def forbidden(req):
            return DecisionResult(req.question_id,"choice",DecisionStatus.SUCCESS,DecisionProvenance("jev_fixture"),
                                  ChoiceDecision("VERIFY",(("VERIFY",.9999),("foundational",.0001)),.9999))
        constraints=RoutingConstraints(forbidden_operators=("VERIFY",))
        session,trace=self.session((forbidden,),constraints=constraints)
        selected=session.select(self.state,self.operators,self.baseline)
        self.assertNotEqual(selected.operator,"VERIFY")
        record=trace.snapshot()["decisions"][0]
        self.assertEqual(record["disposition"],"rejected_by_policy")
        self.assertEqual(record["result"]["value"]["selected_choice"],"VERIFY")

    def test_mandatory_END_operator_overrides_advice_without_consulting(self):
        session,trace=self.session((lambda req:self.fail("No decision call permitted"),),
                                   constraints=RoutingConstraints(mandatory_operator="VERIFY"))
        self.assertEqual(session.select(self.state,self.operators,self.baseline).operator,"VERIFY")
        self.assertEqual(session.calls,0)
        self.assertEqual(trace.snapshot()["model_calls"],[])

    def test_custom_policy_is_authoritative(self):
        session,trace=self.session((lambda req:self.fail("Must not consult"),))
        self.assertEqual(session.select(self.state,self.operators,self.baseline,authoritative=True),self.baseline)
        self.assertEqual(session.calls,0)

    def test_single_available_family_requires_no_model_call(self):
        session,trace=self.session((lambda req:self.fail("No useful classification remains"),),
            constraints=RoutingConstraints(allowed_operators=("WHY","HOW")))
        selected=session.select(self.state,self.operators,self.baseline)
        self.assertIn(selected.operator,("WHY","HOW"))
        self.assertEqual(trace.snapshot()["decision_summary"]["requests"],0)
        self.assertEqual(trace.snapshot()["decision_summary"]["ignored"],1)

    def test_low_choice_probability_and_native_confidence_fall_back(self):
        for confidence in (None,.2):
            session,trace=self.session((lambda req,c=confidence:choice(req,confidence=c),))
            self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
            self.assertEqual(trace.snapshot()["decisions"][0]["disposition"],"ignored_low_certainty")

    def test_provider_failure_returns_deterministic_fallback(self):
        session,trace=self.session((TimeoutError("hidden diagnostic"),))
        self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
        self.assertEqual(trace.snapshot()["decisions"][0]["result"]["status"],"timeout")
        self.assertEqual(trace.call_budget.by_kind["decision"],1)

    def test_malformed_provider_result_is_not_a_positive_signal(self):
        session,trace=self.session((lambda req: {"approve":True},))
        self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
        self.assertEqual(trace.snapshot()["decisions"][0]["result"]["status"],"malformed")

    def test_low_selected_probability_is_a_fallback(self):
        session,trace=self.session((lambda req:choice(req,probability=.35),))
        self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
        self.assertEqual(trace.snapshot()["decisions"][0]["disposition"],"ignored_low_certainty")

    def test_unavailable_provider_does_not_reserve_an_inference_call(self):
        trace=Trajectory("task",{},{});trace.configure_call_budget(10)
        session=DecisionRoutingSession(DecisionConfig(provider="scripted"),ScriptedDecisionProvider(available=False),trace)
        self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
        self.assertEqual(trace.call_budget.used,0)

    def test_decision_subbudget_cannot_add_free_calls(self):
        session,trace=self.session((choice,choice),config=DecisionConfig(provider="scripted",max_calls_per_run=1,max_utility_loss=10))
        session.select(self.state,self.operators,self.baseline)
        session.select(self.state,self.operators,self.baseline)
        self.assertEqual(session.calls,1)
        self.assertEqual(trace.call_budget.used,1)
        self.assertEqual(trace.snapshot()["decisions"][-1]["result"]["status"],"exhausted")

    def test_J4_shared_budget_prevents_decision_calls(self):
        session,trace=self.session((lambda req:self.fail("Budget must prevent this call"),),limit=0)
        self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
        self.assertEqual(session.calls,0)
        self.assertEqual(trace.snapshot()["decisions"][0]["result"]["status"],"exhausted")

    def test_latency_subbudget_rejects_late_signal(self):
        session,trace=self.session((choice,),config=DecisionConfig(provider="scripted",max_latency_ms=1,max_utility_loss=10))
        with patch('end_engine.decisions.routing.perf_counter',side_effect=[0,.01]):
            self.assertEqual(session.select(self.state,self.operators,self.baseline),self.baseline)
        self.assertEqual(trace.snapshot()["decisions"][0]["rule"],"latency_budget_exceeded")

    def test_repetition_control_does_not_offer_penalized_operator(self):
        ranking=self.utility.rank(self.state,self.operators)
        penalized=tuple(replace(r,scores=replace(r.scores,repetition_penalty=1)) if r.operator=="VERIFY" else r for r in ranking)
        baseline=replace(self.baseline,ranking=penalized)
        session,trace=self.session((lambda req:choice(req,"epistemic"),))
        self.assertNotEqual(session.select(self.state,self.operators,baseline).operator,"VERIFY")

    def test_minimal_projection_excludes_candidate_evidence_and_secrets(self):
        issue=Weakness("W1","failure_mode","high","Failure with TYPESAFE_API_KEY=fixture-sensitive-value","Huge evidence blob")
        state=cognitive(open_weaknesses=(issue,),claims_without_evidence=(Claim("CL1","private claim","technical","C0"),))
        data=DecisionContextBuilder().build(state,self.utility.rank(state,self.operators),self.operators,remaining_calls=3)
        self.assertNotIn("fixture-sensitive-value",data)
        self.assertNotIn("Huge evidence blob",data)
        self.assertNotIn("private claim",data)
        self.assertNotIn("created_at",data)
        self.assertLess(len(data),8192)

    def test_replay_consumes_recorded_signal_without_any_external_provider(self):
        session,trace=self.session((lambda req:choice(req,"epistemic"),))
        first=session.select(self.state,self.operators,self.baseline)
        replay_trace=Trajectory("task",{},{});replay_trace.configure_call_budget(30)
        replay=DecisionRoutingSession(session.config,ReplayDecisionProvider.from_trajectory(trace.snapshot()),replay_trace)
        second=replay.select(self.state,self.operators,self.baseline)
        self.assertEqual(first,second)
        self.assertTrue(replay_trace.snapshot()["decisions"][0]["result"]["provenance"]["replayed"])

    def test_replay_missing_or_mismatched_input_is_explicit(self):
        for records in ((),({"request_fingerprint":"wrong"},)):
            trace=Trajectory("task",{},{});trace.configure_call_budget(30)
            replay=DecisionRoutingSession(DecisionConfig(provider="replay",max_utility_loss=10),ReplayDecisionProvider(records),trace)
            self.assertEqual(replay.select(self.state,self.operators,self.baseline),self.baseline)
            self.assertIn(trace.snapshot()["decisions"][0]["result"]["failure_reason"],("replay_missing","replay_input_mismatch"))
            self.assertEqual(trace.call_budget.used,0)

    def test_replay_preserves_uncalled_unavailable_decisions(self):
        trace=Trajectory("task",{},{});trace.configure_call_budget(30)
        config=DecisionConfig(provider="scripted",max_utility_loss=10)
        original=DecisionRoutingSession(config,ScriptedDecisionProvider(available=False),trace)
        original.select(self.state,self.operators,self.baseline)
        original.select(self.state,self.operators,self.baseline)
        replay_trace=Trajectory("task",{},{});replay_trace.configure_call_budget(30)
        replay=DecisionRoutingSession(config,ReplayDecisionProvider.from_trajectory(trace.snapshot()),replay_trace)
        replay.select(self.state,self.operators,self.baseline)
        replay.select(self.state,self.operators,self.baseline)
        self.assertEqual(replay_trace.call_budget.used,0)
        self.assertTrue(all(d["result"]["failure_reason"]=="fixture_unavailable" for d in replay_trace.snapshot()["decisions"]))


class SimpleGenerator(MockProvider):
    def generate_structured(self,request):
        if request.purpose in ("initial_candidate","revision"):
            return ModelResponse({"content":"A concrete answer that proposes a bounded design.","known_strengths":[],"confidence":None})
        if request.purpose=="critique":return ModelResponse({"summary":"No new fixture finding","findings":[]})
        if request.purpose=="revision_plan":return ModelResponse({"changes":[]})
        return super().generate_structured(request)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)

    def engine(self, *, provider=None, verifier=None, **kwargs):
        config=EngineConfig(ledger_dir=self.tmp.name,decision=DecisionConfig(provider="scripted",max_utility_loss=10),
                            protocol_repair_attempts=0)
        return EndEngine(config,provider=provider or SimpleGenerator(),verifier=verifier or BasicRuleVerifier(),
                         decision_provider=ScriptedDecisionProvider((choice,)*8),**kwargs)

    def test_disabled_default_does_not_load_SDK_or_consult_decision_provider(self):
        forbidden=ScriptedDecisionProvider((lambda req:self.fail("Disabled provider executed"),))
        engine=EndEngine(EngineConfig(ledger_dir=self.tmp.name),decision_provider=forbidden)
        with patch('end_engine.decisions.jev.importlib.import_module',side_effect=AssertionError("No SDK import")):
            result=engine.run("uppercase hello")
        self.assertEqual(result.answer,"HELLO")
        self.assertNotIn("decisions",engine.last_trajectory)
        self.assertNotIn("run_call_budget",engine.last_trajectory)

    def test_fast_mode_never_consults_enabled_decision_model(self):
        config=EngineConfig(ledger_dir=self.tmp.name,decision=DecisionConfig(provider="scripted"))
        engine=EndEngine(config,decision_provider=ScriptedDecisionProvider((lambda req:self.fail("FAST consulted provider"),)))
        result=engine.run("uppercase hello",mode="fast")
        self.assertEqual(result.answer,"HELLO")
        self.assertEqual(engine.last_trajectory["decision_summary"]["calls"],0)

    def test_shared_budget_includes_structured_protocol_repair(self):
        invalid=ModelResponse("malformed output")
        valid={"content":"A repaired fixture proposal.","known_strengths":[],"confidence":None}
        provider=MockProvider(scripted={"initial_candidate":[invalid,valid]})
        engine=EndEngine(EngineConfig(ledger_dir=self.tmp.name,max_run_calls=3),provider=provider)
        result=engine.run("Write a proposal",mode="fast")
        self.assertEqual(result.answer,"A repaired fixture proposal.")
        self.assertEqual(engine.last_trajectory["run_call_budget"]["used"],3)
        self.assertEqual(len(engine.last_trajectory["model_calls"]),3)

    def test_disabled_behavior_matches_without_any_decision_injection(self):
        plain=EndEngine(EngineConfig(ledger_dir=self.tmp.name))
        disabled=EndEngine(EngineConfig(ledger_dir=self.tmp.name),decision_provider=ScriptedDecisionProvider(available=False))
        with patch('end_engine.engine.now',return_value="2026-10-04T00:00:00+00:00"):
            a=plain.run("Design bounded memory",mode="deep");old=plain.last_trajectory
            b=disabled.run("Design bounded memory",mode="deep");new=disabled.last_trajectory
        self.assertEqual((a.answer,a.iterations,a.termination_reason,a.verification),(b.answer,b.iterations,b.termination_reason,b.verification))
        self.assertEqual([c["request"] for c in old["model_calls"]],[c["request"] for c in new["model_calls"]])

    def test_J1_Jev_cannot_verify_a_claim(self):
        class Claims:
            def extract(self,candidate): return ("The proposed answer is fully correct.",)
        def supports(request):
            return DecisionResult(request.question_id,"choice",DecisionStatus.SUCCESS,DecisionProvenance("jev_fixture"),
                ChoiceDecision("supported",(("supported",.99),("unsupported",.01)),.99))
        config=EngineConfig(ledger_dir=self.tmp.name,decision=DecisionConfig(provider="scripted",max_utility_loss=10))
        engine=EndEngine(config,provider=SimpleGenerator(),verifier=BasicRuleVerifier(),claim_extractor=Claims(),
                         decision_provider=ScriptedDecisionProvider((supports,)))
        engine.run("Provide an answer",mode="normal",max_cycles=1)
        self.assertTrue(engine.last_trajectory["claims"])
        self.assertTrue(all(c["evidence_status"]=="UNVERIFIED" for c in engine.last_trajectory["claims"]))
        signal=engine.last_trajectory["decisions"][0]["result"]
        self.assertEqual(signal["value"]["choice_probabilities"][0],["supported",.99])
        self.assertEqual(signal["provenance"]["evidence_type"],"MODEL_JUDGMENT")

    def test_J2_failed_verifier_cannot_be_overridden_by_high_probability(self):
        engine=self.engine(verifier=BasicRuleVerifier(required_terms=("missing mandatory component",)))
        result=engine.run("Provide a complete design",mode="normal",max_cycles=1)
        self.assertFalse(result.verification.passed)
        self.assertEqual(result.termination_reason.value,"BUDGET_EXHAUSTED")
        self.assertTrue(engine.last_trajectory["decisions"])

    def test_J3_mandatory_revision_remains_mandatory(self):
        engine=self.engine()
        result=engine.run("Provide a complete design",mode="deep",max_cycles=2)
        self.assertEqual(result.iterations,2)
        self.assertEqual(len(engine.last_trajectory["candidates"]),3)

    def test_J6_generator_judge_and_Jev_agreement_is_not_verification(self):
        class Claims:
            def extract(self,candidate): return ("The proposed answer is fully correct.",)
        engine=self.engine(judge_provider=MockJudgeProvider(),claim_extractor=Claims())
        result=engine.run("Provide a complete design",mode="normal",max_cycles=1)
        self.assertEqual(result.quality_gate,"ACCEPT_PROVISIONALLY")
        self.assertNotEqual(result.acceptance_label,"ACCEPTED_HIGH_CONFIDENCE")
        self.assertEqual(engine.last_trajectory["verifier_evidence"],[])
        self.assertTrue(all(c["status"]=="UNVERIFIED" for c in engine.last_trajectory["claim_validations"]))

    def test_J7_missing_key_does_not_break_baseline_fallback(self):
        config=EngineConfig(ledger_dir=self.tmp.name,decision=DecisionConfig(provider="jev",requested_model="jev-fixture-pin"))
        engine=EndEngine(config,provider=SimpleGenerator(),verifier=BasicRuleVerifier())
        with patch.dict(os.environ,{},clear=True):result=engine.run("Provide a design",mode="normal",max_cycles=1)
        self.assertTrue(result.answer)
        self.assertEqual(engine.last_trajectory["decision_summary"]["calls"],0)
        self.assertEqual(engine.last_trajectory["decisions"][0]["result"]["failure_reason"],"missing_api_key")

    def test_all_decision_generator_judge_and_tool_calls_share_one_budget(self):
        from end_engine.verification import CallableToolVerifier,ToolCheck
        tool=CallableToolVerifier(lambda *args:(ToolCheck(True,"Safe fixture check"),))
        engine=self.engine(judge_provider=MockJudgeProvider(),tool_verifier=tool)
        engine.run("Provide a design",mode="normal",max_cycles=1)
        record=engine.last_trajectory
        calls=record["run_call_budget"]["by_kind"]
        self.assertGreater(calls["decision"],0)
        self.assertGreater(calls["model"],0)
        self.assertGreater(calls["tool"],0)
        self.assertGreater(calls["verifier_tool"],0)
        self.assertEqual(record["run_call_budget"]["used"],sum(calls.values()))
        self.assertTrue(any(c["method"]=="evaluate_decision" for c in record["model_calls"]))

    def test_global_budget_exhaustion_stops_additional_operations(self):
        config=EngineConfig(ledger_dir=self.tmp.name,max_run_calls=2,decision=DecisionConfig(provider="scripted"))
        engine=EndEngine(config,decision_provider=ScriptedDecisionProvider((lambda r:self.fail("No call allowed"),)))
        result=engine.run("Design a service",mode="deep",max_cycles=8)
        self.assertEqual(result.termination_reason.value,"BUDGET_EXHAUSTED")
        self.assertEqual(result.iterations,0)
        self.assertEqual(engine.last_trajectory["run_call_budget"]["used"],2)

    def test_full_trajectory_serialization_and_replay_preserve_selected_operators(self):
        engine=self.engine()
        result=engine.run("Provide a design",mode="normal",max_cycles=1)
        record=JsonLedger().load(result.trajectory_path)
        self.assertEqual(record,engine.last_trajectory)
        replay_config=replace(engine.config,decision=replace(engine.config.decision,provider="replay"))
        replay_engine=EndEngine(replay_config,provider=SimpleGenerator(),verifier=BasicRuleVerifier(),
            decision_provider=ReplayDecisionProvider.from_trajectory(record))
        replay_engine.run("Provide a design",mode="normal",max_cycles=1)
        self.assertEqual([s["data"]["operator"] for s in record["steps"] if s["type"]=="operator_selection"],
                         [s["data"]["operator"] for s in replay_engine.last_trajectory["steps"] if s["type"]=="operator_selection"])
        self.assertTrue(replay_engine.last_trajectory["decisions"][0]["result"]["provenance"]["replayed"])

    def test_no_state_leaks_across_runs(self):
        engine=self.engine()
        first=engine.run("Provide a design",mode="normal",max_cycles=1);previous=engine.last_trajectory
        second=engine.run("Provide a design",mode="normal",max_cycles=1)
        self.assertNotEqual(first.trajectory_id,second.trajectory_id)
        self.assertEqual(previous["decision_summary"]["calls"],engine.last_trajectory["decision_summary"]["calls"])
        self.assertEqual(previous["decisions"][0]["request_fingerprint"],engine.last_trajectory["decisions"][0]["request_fingerprint"])
