"""v0.3.5 regression pack: protocol robustness and grounded judgment. Every model output here is a SYNTHETIC scripted
fixture; no live model is called. Cases R1-R12 reproduce failure patterns observed in Benchmark Alpha (v0.3.4); the
benchmark's task texts are used only as fixtures, never in production logic. The C0 A/B fixture checks separation of
answer and Engine metadata; it does NOT measure answer quality."""
import json
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, MockProvider, ModelResponse
from end_engine.cognition.branches import BranchController
from end_engine.cognition.session import CognitiveSession
from end_engine.core.output_format import check_candidate, consensus_kind
from end_engine.core.state import StopReason
from end_engine.core.task_analyzer import TaskAnalyzer
from end_engine.experience import JsonLedger, Trajectory
from end_engine.models.production_mock import PRODUCTION_TASK, ProductionAgentMockProvider
from end_engine.models.protocol import ModelProtocolError
from end_engine.operators import default_operators
from end_engine.quality.grounding import ground_issue
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.quality.state import JudgeIssue, CheckContract
from end_engine.quality.integrity import content_sha256
from end_engine.verification import CallableToolVerifier, ToolCheck

from .test_evidence_integrity import cand, check, claim, claim_of, evaluate

TASK = "Schedule the jobs so that every constraint holds. Return the schedule."
BUGGY_TASK = ("This function has bugs. Fix it.\n```python\ndef chunk(items, size):\n    result = []\n"
              "    for i in range(0, len(items) - size, size):\n        result.append(items[i:i + size])\n    return result\n```")
FIXED = ("```python\ndef chunk(items, size):\n    if size <= 0:\n        raise ValueError('size')\n"
         "    return [items[i:i + size] for i in range(0, len(items), size)]\n```")
BUGGY_LOOP = "for i in range(0, len(items) - size, size)"
PREMISE_TASK = ("Because Python's built-in sorted() is not stable, write sort_by_age(people) that sorts (name, age) "
                "tuples by age while keeping equal ages in their original order.")
PREMISE_ANSWER = "Note: sorted() is actually stable (Timsort).\n```python\ndef sort_by_age(p):\n    return sorted(p, key=lambda x: x[1])\n```"
JSON_TASK = 'Give the final answer as a JSON object with keys "first" and "last" in a ```json code block.'


def finding(weakness_id=None, description="Horizon is not checked for this schedule", severity="low"):
    return {"weakness_id": weakness_id, "type": "constraint", "severity": severity, "description": description,
            "evidence": "SYNTHETIC fixture finding"}


class Gen(MockProvider):
    """SYNTHETIC generator: scripted per purpose and per call (repair calls consume the next item)."""
    def __init__(self, contents=("Schedule: A at 0, B at 2.",), *, critiques=(), plans=(), verifications=(), native=(),
                 fail=None):
        super().__init__()
        self.contents, self.critiques, self.plans = list(contents), list(critiques), list(plans)
        self.verifications, self.native, self.fail = list(verifications), list(native), dict(fail or {})
        self.counts, self.requests = {}, []

    def _n(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def generate(self, request):
        self.requests.append(("text", request))
        n = self._n("text")  # native outputs are consumed in call order
        if request.purpose in self.fail:
            raise self.fail[request.purpose]
        return ModelResponse(self.native[min(n - 1, len(self.native) - 1)])

    def generate_structured(self, request):
        self.requests.append(("structured", request))
        p, c = request.purpose, request.context
        n = self._n(p)
        if p in self.fail:
            raise self.fail[p]
        pick = lambda seq, default: seq[n - 1] if n - 1 < len(seq) else default
        if p in ("initial_candidate", "revision"):
            index = 0 if p == "initial_candidate" else self.counts[p]
            return ModelResponse({"content": self.contents[min(index, len(self.contents) - 1)], "known_strengths": [],
                                  "confidence": None})
        if p == "verification":
            return ModelResponse({"passed": True, "score": .95, "dimensions": {d: .95 for d in c["dimensions"]},
                                  "remaining_issues": [], "weakness_updates": pick(self.verifications, [])})
        if p == "critique":
            out = pick(self.critiques, {"summary": "SYNTHETIC critique", "findings": []})
            return out if isinstance(out, ModelResponse) else ModelResponse(out)
        if p == "revision_plan":
            return ModelResponse(pick(self.plans, {"changes": []}))
        return super().generate_structured(request)


def adversary(*responses):
    """SYNTHETIC independent judge; adversarial judgments scripted per candidate, PASS otherwise."""
    def passing(r):
        return judgment_fixture(r.context["dimensions"])
    return MockJudgeProvider(scripted={"adversarial_judgment": [*responses, passing, passing, passing]})


def objection(description, *, fatal=True, **fields):
    def respond(r):
        data = judgment_fixture(r.context["dimensions"], verdict="FAIL", score=.2, fatal=fatal,
                                issues=[{"category": "correctness", "description": description, "target": "candidate",
                                         "fatal": fatal, "evidence": [], **fields}])
        data["recommended_action"] = "REJECT" if fatal else "REVISE"
        return data
    return respond


class Run(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_engine(self, generator, *, task=TASK, judge=None, max_cycles=1, tool=None, **config):
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False, **config),
                           provider=generator, judge_provider=judge, tool_verifier=tool)
        result = engine.run(task, mode="normal", max_cycles=max_cycles)
        return result, engine.last_trajectory

    @staticmethod
    def events(record, stage=None):
        return [e for e in record["protocol_events"] if stage is None or e["stage"] == stage]


class ProtocolRecoveryTests(Run):
    def test_R1_unknown_weakness_in_critique_is_repaired_or_discarded(self):
        bad = {"summary": "s", "findings": [finding(), finding("completeness", "Answer is incomplete")]}
        result, record = self.run_engine(Gen(critiques=[bad, bad]))
        self.assertNotIn(result.termination_reason, (StopReason.EXTERNAL_BLOCKER, StopReason.MODEL_PROTOCOL_FAILURE))
        self.assertEqual([c["candidate_id"] for c in record["candidates"]], ["C0", "C1"])  # the loop continued
        self.assertEqual([w["id"] for w in record["weaknesses"]], ["W001"])  # never an ID named "completeness"
        actions = [e["action"] for e in self.events(record, "critique")]
        self.assertEqual(actions, ["repair_requested", "invalid_elements_discarded"])
        repair_request = [c["request"] for c in record["model_calls"] if c["request"]["purpose"] == "critique"][1]
        self.assertEqual(repair_request["context"]["protocol_repair"]["invalid_values"], ["completeness"])
        self.assertEqual(repair_request["context"]["protocol_repair"]["allowed_identifiers"]["weakness_ids"], [])
        good = {"summary": "s", "findings": [finding()]}
        _, record = self.run_engine(Gen(critiques=[bad, good]))
        self.assertEqual([e["action"] for e in self.events(record, "critique")], ["repair_requested", "repaired"])

    def test_R2_unknown_targets_in_revision_plan_are_never_remapped(self):
        plans = [{"changes": [{"targets": ["timezone_ambiguity"], "action": "a1", "expected_effect": "e1"}]},
                 {"changes": [{"targets": ["W001", "W009"], "action": "a2", "expected_effect": "e2"},
                              {"targets": ["root_cause"], "action": "a3", "expected_effect": "e3"}]}]
        result, record = self.run_engine(Gen(critiques=[{"summary": "s", "findings": [finding()]}], plans=plans))
        self.assertNotEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        plan = record["revision_plans"][0]
        self.assertEqual([(c["targets"], c["action"]) for c in plan["changes"]], [(["W001"], "a2")])
        discarded = self.events(record, "revision_plan")[-1]["discarded"]
        self.assertEqual({d["change"]["action"] for d in discarded}, {"a2", "a3"})  # a3 dropped, a2 trimmed
        self.assertEqual([c["candidate_id"] for c in record["candidates"]], ["C0", "C1"])

    def test_R3_invalid_verification_updates_rejected_valid_ones_kept(self):
        updates = [{"id": "W001", "status": "resolved", "reason": "The revision adds an explicit horizon check"},
                   {"id": "C0", "status": "resolved", "reason": "Candidate is fine"},
                   {"id": "W001", "status": "resolved", "reason": "Duplicate update of the same weakness"}]
        gen = Gen(critiques=[{"summary": "s", "findings": [finding()]}], verifications=[[], updates, updates])
        result, record = self.run_engine(gen)
        self.assertNotEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER)
        event = self.events(record, "verification")[-1]
        self.assertEqual((event["action"], event["kept"]), ("invalid_updates_rejected", ["W001"]))
        self.assertEqual(sorted((r["id"], r["reason"]) for r in event["rejected"]),
                         [("C0", "unknown weakness ID"), ("W001", "duplicate update")])
        changes = [s["data"]["after"]["id"] for s in record["steps"] if s["type"] == "weakness_status_change"]
        self.assertEqual(changes, ["W001"])
        self.assertEqual([u["id"] for u in record["verification"][-1]["weakness_updates"]], ["W001"])

    def test_R4_repeated_invalid_output_terminates_boundedly(self):
        # v0.3.5.1 retains old configuration values but enforces one targeted attempt per result.
        for attempts, calls in ((0, 1), (1, 2), (2, 2)):
            gen = Gen(critiques=[ModelResponse("not JSON")] * 5)
            result, record = self.run_engine(gen, protocol_repair_attempts=attempts)
            self.assertEqual(result.termination_reason, StopReason.MODEL_PROTOCOL_FAILURE, attempts)
            self.assertEqual(gen.counts["critique"], calls, attempts)
            self.assertEqual(record["termination"]["category"],
                             "MODEL_PROTOCOL_REPAIR_EXHAUSTED" if attempts else "MODEL_PROTOCOL_SCHEMA_FAILURE")
            self.assertEqual(record["errors"][-1]["category"], record["termination"]["category"])
            self.assertTrue(JsonLedger().load(result.trajectory_path)["termination"])  # complete, persisted trace
        # Reference-level failures never loop either: one repair per stage, then salvage.
        bad = {"summary": "s", "findings": [finding("W404")]}
        gen = Gen(critiques=[bad] * 10)
        self.run_engine(gen, max_cycles=2)
        self.assertLessEqual(gen.counts["critique"], 4)

    def test_R5_real_provider_failure_is_still_an_external_blocker(self):
        for purpose, error in (("critique", RuntimeError("provider unavailable")),
                               ("revision", ConnectionError("connection refused")),
                               ("initial_candidate", TimeoutError("timed out"))):
            result, record = self.run_engine(Gen(fail={purpose: error}))
            self.assertEqual(result.termination_reason, StopReason.EXTERNAL_BLOCKER, purpose)
            self.assertEqual(record["termination"]["category"], "EXTERNAL_FAILURE", purpose)
            self.assertEqual(record["protocol_events"], [], purpose)  # never retried as a model-output problem

    def test_branch_synthesis_failure_is_local_and_invariant_holds(self):
        def manager():
            configuration = EngineConfig()
            trajectory = Trajectory(PRODUCTION_TASK, {}, {})
            session = CognitiveSession(TaskAnalyzer().analyze(PRODUCTION_TASK, mode="deep"), configuration, trajectory)
            return BranchController(configuration, trajectory, session), trajectory
        forbidden = {"source_branches": ["B1", "B2", "B3"], "adopt": [{"branch": "B1", "element": "unsafe"}], "reject": []}
        allowed = {"source_branches": ["B1", "B2", "B3"], "adopt": [{"branch": "B2", "element": "safe"}],
                   "reject": [{"branch": "B1", "element": "unsafe", "reason": "rejected"}]}
        candidate = cand(content="The journal guarantees recoverability.")
        controller, trajectory = manager()
        plan, branches = controller.explore(PRODUCTION_TASK, candidate, default_operators()["ALTERNATIVE"], None,
            ("correctness",), ProductionAgentMockProvider(scripted={"synthesis": [forbidden, forbidden]}))
        self.assertEqual(plan.adopt, ())
        self.assertEqual([b.status for b in branches], ["REJECTED", "EXHAUSTED", "EXHAUSTED"])  # nothing adopted
        self.assertEqual([e["action"] for e in trajectory.snapshot()["protocol_events"]],
                         ["repair_requested", "synthesis_discarded"])
        controller, trajectory = manager()
        plan, branches = controller.explore(PRODUCTION_TASK, candidate, default_operators()["ALTERNATIVE"], None,
            ("correctness",), ProductionAgentMockProvider(scripted={"synthesis": [forbidden, allowed]}))
        self.assertEqual([e.branch for e in plan.adopt], ["B2"])
        self.assertEqual(branches[0].status, "REJECTED")  # the forbidden adoption was never applied
        controller, _ = manager()
        with self.assertRaises(RuntimeError):  # a provider failure is not a protocol failure
            controller.explore(PRODUCTION_TASK, candidate, default_operators()["ALTERNATIVE"], None, ("correctness",),
                               ProductionAgentMockProvider(scripted={"synthesis": [RuntimeError("unavailable")]}))

    def test_protocol_errors_remain_value_errors_for_components(self):
        self.assertTrue(issubclass(ModelProtocolError, ValueError))


class CandidateGenerationTests(Run):
    def test_R6_native_c0_is_the_task_itself_and_keeps_the_task_format(self):
        answer = '```json\n{"first": "E2", "last": "E1"}\n```'
        gen = Gen(native=[answer])
        result, record = self.run_engine(gen, task=JSON_TASK, max_cycles=0, candidate_generation="native")
        kind, request = gen.requests[0]
        self.assertEqual((kind, request.purpose, request.prompt, request.context, request.schema),
                         ("text", "initial_candidate", JSON_TASK, {}, None))
        self.assertEqual(record["candidates"][0]["content"], answer)
        self.assertEqual(result.answer, answer)
        self.assertEqual(record["engine_checks"][0]["format_violations"], [])
        self.assertEqual(record["model_calls"][0]["method"], "generate")

    def test_R7_internals_never_reach_the_revision_prompt_and_leaks_are_flagged(self):
        clean = '```json\n{"first": "E2", "last": "E1"}\n```'
        leaking = "Per the revision plan for W001 (candidate C0), here is the fix:\n" + clean
        gen = Gen(native=[clean, leaking], critiques=[{"summary": "s", "findings": [finding()]}],
                  plans=[{"changes": [{"targets": ["W001"], "action": "State the horizon check",
                                       "expected_effect": "Covers horizon"}]}])
        result, record = self.run_engine(gen, task=JSON_TASK, judge=MockJudgeProvider(), candidate_generation="native")
        revision = [r for k, r in gen.requests if k == "text" and r.purpose == "revision"][0]
        self.assertNotIn("W001", revision.prompt)
        self.assertIn("State the horizon check", revision.prompt)
        leak = next(c for c in record["engine_checks"] if c["candidate_id"] == "C1")["internal_leakage"]
        self.assertEqual(leak, ["weakness identifier: W001", "candidate identifier: candidate C0", "revision plan: revision plan"])
        c1 = next(g for g in record["quality_gate_decisions"] if g["candidate_id"] == "C1")
        self.assertEqual(c1["decision"], "REVISE")
        self.assertTrue(any(r.startswith("Candidate exposes Engine internals") for r in c1["reasons"]))
        self.assertEqual((result.best_candidate_id, result.answer), ("C0", clean))  # the user gets the clean answer

    def test_C0_AB_structured_vs_native_metadata_stays_separate(self):
        """SYNTHETIC A/B: identical scripted answer text in both modes. Checks separation only, not quality."""
        answer = '```json\n{"first": "E2", "last": "E1"}\n```'
        structured_gen, native_gen = Gen(contents=[answer]), Gen(native=[answer])
        structured, s_record = self.run_engine(structured_gen, task=JSON_TASK, max_cycles=0)
        native, n_record = self.run_engine(native_gen, task=JSON_TASK, max_cycles=0, candidate_generation="native")
        s_request = structured_gen.requests[0][1]
        self.assertEqual(sorted(s_request.schema["properties"]), ["confidence", "content", "known_strengths"])
        # Structured mode keeps the exact v0.3.4 request (integrations compare baselines against it byte for byte).
        self.assertTrue(s_request.prompt.startswith("Produce an initial answer to the task. State assumptions and material limitations."))
        self.assertIn("MODEL_REVISION_PLAN", s_request.prompt)
        self.assertIn("assessment_context", s_request.context)
        self.assertIsNone(native_gen.requests[0][1].schema)
        self.assertEqual(structured.answer, native.answer)
        for result, record in ((structured, s_record), (native, n_record)):
            self.assertNotIn("known_strengths", result.answer)
            self.assertEqual(record["engine_checks"][0]["format_violations"], [])
            loaded = JsonLedger().load(result.trajectory_path)  # sidecar metadata serializes and round-trips
            self.assertEqual(loaded["engine_checks"], record["engine_checks"])
            self.assertEqual(json.loads(json.dumps(loaded)), loaded)

    def test_native_mode_requires_explicit_opt_in(self):
        self.assertEqual(EngineConfig().candidate_generation, "structured")
        with self.assertRaises(ValueError):
            EngineConfig(candidate_generation="free")


class GroundedJudgmentTests(Run):
    def gate(self, record, candidate_id="C0"):
        return next(g for g in record["quality_gate_decisions"] if g["candidate_id"] == candidate_id)

    def test_R8_task_code_attributed_to_candidate_is_misattributed(self):
        description = f"The loop condition `{BUGGY_LOOP}` stops early and drops the last chunk."
        result, record = self.run_engine(Gen(contents=[FIXED]), task=BUGGY_TASK, judge=adversary(objection(description)))
        incident = record["judge_groundings"][0]
        self.assertEqual((incident["status"], incident["severity"]), ("MISATTRIBUTED", "fatal"))
        gate = self.gate(record)
        self.assertNotIn(gate["decision"], ("REJECT", "REVISE"))
        self.assertTrue(any(r.startswith("Judge findings not grounded in the candidate") for r in gate["reasons"]))
        self.assertEqual((record["judge_feedback"], record["rollback_events"]), ([], []))
        self.assertEqual(record["fatal_issues"][0]["grounding"], "MISATTRIBUTED")  # the incident stays visible
        self.assertEqual(record["adversarial_judgments"][0]["fatal_issues"][0]["decisive"], False)

    def test_R11_quoted_defect_that_is_in_the_candidate_still_rejects(self):
        buggy_answer = BUGGY_TASK.split("Fix it.\n", 1)[1]
        source = 'Function returns the last chunk for length 4 size 2.'
        defect = 'Function does not return the last chunk for length 4 size 2.'
        def execute(t, c, tests, claims):
            # Trusted, controlled SYNTHETIC fixture; not a production execution facility.
            self.assertEqual(c.content, buggy_answer)
            namespace = {}
            exec(c.content.split('```python\n')[1].split('```')[0], namespace)
            passed = namespace['chunk']([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
            return (ToolCheck(passed, source, contract=CheckContract('last-chunk', properties=(source,),
                        artifact_sha256=content_sha256(c.content), bounds='length 4 size 2')),)
        for fields in ({}, {"candidate_quote": BUGGY_LOOP, "claim_type": "CANDIDATE_INTERNAL"}):
            description = f"The loop condition `{BUGGY_LOOP}` stops early and drops the last chunk."
            _, record = self.run_engine(Gen(contents=[buggy_answer]), task=BUGGY_TASK,
                                        judge=adversary(objection(description, source_claim=source,
                                            alleged_defect=defect, basis='Scoped deterministic chunk test', **fields)),
                                        tool=CallableToolVerifier(execute))
            self.assertEqual(self.gate(record)["decision"], "REJECT", fields)
            self.assertEqual(record["judge_groundings"], [], fields)
            self.assertEqual(record["fatal_issues"][0]["grounding"], "SEMANTIC_SUPPORTED")

    def test_R9_contradicting_a_task_premise_is_not_a_defect(self):
        premise = ("The candidate claims that Python's `sorted()` is stable, but the problem statement explicitly "
                   "states that `sorted()` is not stable.")
        _, record = self.run_engine(Gen(contents=[PREMISE_ANSWER]), task=PREMISE_TASK, judge=adversary(objection(premise)))
        self.assertEqual(record["judge_groundings"][0]["status"], "TASK_PREMISE_DEPENDENT")
        self.assertNotIn(self.gate(record)["decision"], ("REJECT", "REVISE"))
        external = objection("Python's sorted() is not stable.", claim_type="EXTERNAL_FACT")
        _, record = self.run_engine(Gen(contents=[PREMISE_ANSWER]), task=PREMISE_TASK, judge=adversary(external))
        self.assertEqual(record["judge_groundings"][0]["status"], "REQUIRES_EXTERNAL_VALIDATION")
        self.assertNotIn(self.gate(record)["decision"], ("REJECT", "REVISE"))
        # Positive control: the same factual claim backed by an executed check of this candidate is decisive.
        issue = JudgeIssue("correctness", "Python's sorted() is not stable.", claim_type="EXTERNAL_FACT", evidence=("E-C0-1",))
        self.assertFalse(ground_issue(issue, PREMISE_TASK, PREMISE_ANSWER, executed_ids=("E-C0-1",)).decisive)

    def test_R12_real_task_constraint_violation_still_counts(self):
        prose = "The first event was E2 and the last was E1."
        constraint = objection("The task requires a JSON object in a ```json code block, but the candidate answered in prose.",
                               fatal=False, claim_type="TASK_CONSTRAINT", task_reference="in a ```json code block")
        _, record = self.run_engine(Gen(contents=[prose]), task=JSON_TASK, judge=adversary(constraint))
        gate = self.gate(record)
        self.assertEqual(gate["decision"], "REVISE")
        self.assertTrue(any("missing the required" in r for r in gate["reasons"]))
        self.assertTrue(any(r.startswith("Candidate does not follow the task's required output format") for r in gate["reasons"]))
        self.assertEqual(record["judge_groundings"], [])
        undeclared = JudgeIssue("format", "The candidate states its answer in prose, but the task requires a JSON object.")
        self.assertTrue(ground_issue(undeclared, JSON_TASK, prose).decisive)  # a constraint contrast is not a premise

    def test_ungrounded_quote_is_not_decisive(self):
        issue = JudgeIssue("correctness", "Off-by-one error", candidate_quote="while j < n - 1:")
        g = ground_issue(issue, BUGGY_TASK, FIXED)
        self.assertEqual((g.status, g.decisive), ("UNGROUNDED", False))

    def test_judges_receive_typed_sources(self):
        _, record = self.run_engine(Gen(contents=[FIXED]), task=BUGGY_TASK, judge=MockJudgeProvider())
        request = next(c["request"] for c in record["model_calls"] if c["request"]["purpose"] == "judgment")
        self.assertTrue(request["context"]["sources"]["task"].startswith("TASK_PROVIDED"))
        self.assertIn("Never attribute task text to the candidate", request["prompt"])
        self.assertIn("claim_type", request["schema"]["properties"]["fatal_issues"]["items"]["properties"])


class ConsensusTests(Run):
    def test_R10_agreement_is_consensus_not_verification(self):
        support = "Two on-call engineers both agree that the database is the root cause."
        report, gate, _ = evaluate((claim("CL001", "The database is the root cause.", "SUPPORTED", support),), (check("E-C0-1", ()),))
        c = claim_of(report, "CL001")
        self.assertEqual(c.consensus, "REPORTED_CONSENSUS")
        self.assertNotEqual(c.status, "verified")
        self.assertIn("agreement, not verification", c.reason)
        self.assertTrue(any(u.startswith("Agreement is recorded as consensus") for u in gate.reasons))
        self.assertEqual(consensus_kind("All three judges agree the fix is correct."), "MODEL_CONSENSUS")
        # The candidate itself presenting agreement as confirmation is flagged, and blocks verified acceptance.
        answer = "Two on-call engineers independently confirmed the database as the culprit."
        self.assertEqual(check_candidate(TASK, "C0", answer)["consensus_as_confirmation"], [answer])

        class Trusted:
            def extract(self, candidate):
                return ("The declared checks pass.",)
        tool = CallableToolVerifier(lambda t, c, tests, claims: (ToolCheck(True, "SYNTHETIC check", tuple(x.claim_id for x in claims)),))
        engine = EndEngine(EngineConfig(ledger_dir=self.temp.name, enable_branching=False), provider=Gen(contents=[answer]),
                           judge_provider=MockJudgeProvider(), tool_verifier=tool, claim_extractor=Trusted())
        result = engine.run(TASK, mode="normal", max_cycles=0)
        gate = engine.last_trajectory["quality_gate_decisions"][0]
        # v0.3.5.1 requires targeted correction, rather than returning a provisional overclaim.
        self.assertEqual(gate["decision"], "REVISE")
        self.assertTrue(any('epistemic status exceeds' in r for r in gate['reasons']))
        self.assertTrue(engine.last_trajectory['output_integrity']['blocked'])
        self.assertEqual(result.answer, '')
        self.assertEqual(check_candidate(TASK, "C0", "Both engineers wrote that it is the database.")["consensus_as_confirmation"], [])


if __name__ == "__main__":
    unittest.main()
