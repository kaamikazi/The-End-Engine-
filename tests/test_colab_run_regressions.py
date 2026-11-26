"""Regressions from the first live Colab runs (2026-11-23, qwen3:4b and qwen3:14b on an L4).

See colab_t4_smoke_v1/ENGINE_FINDINGS_RUNS_1_2.md.
"""
from dataclasses import replace
import unittest

from end_engine.core.state import StopReason
from end_engine.quality.epistemic import epistemic_integrity, extract_epistemic_claims
from end_engine.quality.mock import MockJudgeProvider
from end_engine.verification import CallableToolVerifier
from end_engine import EngineConfig
from .test_v035_regressions import Gen, adversary, objection
from .test_v0351_regressions import Fixture, Stagnant

# Sentences that describe a design, a metric or a test plan; none asserts an earned status.
NOT_CLAIMS = (
    "- **Pruning effectiveness**: The percentage of pruned memories that are confirmed to be low-impact or "
    "redundant without affecting performance.",  # run 2 final draft; withheld the whole answer
    "Recall rate: the share of queries whose answers are verified against the archive.",
    "Entries are deleted only after they are confirmed to be stale by the scorer.",
    "Run a soak test; the bound is verified when memory stays under 600 MB for 24 hours.",
    "Before it is deployed in production, run a 24-hour soak test.",
    "The design should be tested in production behind a feature flag.",
    "It has not been tested in production.",
    "It hasn't been tested in production.",
    "Deploy the cache in production with a 500 MB limit.",
    # Graded run BA-009 (2026-11-25): these withheld a draft the grader scored 1.0.
    "We have \"hypothesis\" for the candidate, which is correct because we don't have the database metrics to confirm.",
    "We don't have evidence to confirm, so it's a hypothesis.",
    "We can change \"was\" to \"is hypothesized to be\" to avoid implying it's confirmed.",
    "So we don't need database metrics to confirm",
    "The cause isn’t confirmed.",
    "We lack the traces needed to confirm the cause.",
    "We are unable to verify the cause.",
    "The cause is yet to be established.",
    # Purpose clauses name a check still to be done (pilot BA-009 trajectory 2965e080).
    "The root cause requires further investigation into database-specific metrics to confirm the exact impact.",
    "Collect query logs to confirm the cause.",
    "The cause remains to be verified.",
)

# Unsupported empirical or status claims; each must be flagged without executed evidence.
CLAIMS = (
    "The inclusion of performance metrics and concrete examples demonstrates the effectiveness of memory "
    "prioritization.",  # run 2 final draft
    "The system consistently demonstrates memory usage <=600 MB under real-world loads.",  # run 1 final draft
    "This design has been battle-tested in production for 3+ years and scales seamlessly.",  # run 1 first draft
    "Systems using this design never exceeded 1 GB of active memory in 1 year of testing.",  # run 1 first draft
    "In our benchmarks, retrieval latency stayed under 5 ms.",
    "It has been deployed in production at three companies.",
    "This design has been verified in production.",
    "After testing, the bound is verified.",
    # Absence words do not negate a status asserted after a conjunction, or "without doubt".
    "It shipped without downtime and was verified in staging.",
    "It ran without any errors and the bound was confirmed.",
    "It is without doubt confirmed.",
    "The database is the root cause (so that part is established).",  # graded run BA-009 C1
    "We were able to confirm the fix.",
    "We managed to verify the bound.",
)


class ColabRunEpistemicTests(unittest.TestCase):
    def test_definitions_plans_and_criteria_are_not_status_claims(self):
        for text in NOT_CLAIMS:
            with self.subTest(text=text):
                self.assertEqual(extract_epistemic_claims(text), ())
                self.assertEqual(epistemic_integrity(text, "C0"), ())

    def test_unsupported_status_and_track_record_claims_are_overclaims(self):
        for text in CLAIMS:
            with self.subTest(text=text):
                checks = epistemic_integrity(text, "C0")
                self.assertTrue(checks and all(c["overclaim"] for c in checks))

    def test_track_record_is_reported_once_per_clause(self):
        claims = extract_epistemic_claims("It was battle-tested in production for 3+ years in our benchmarks.")
        self.assertEqual([c.declared_status for c in claims], ["track_record"])


class BranchProgressTests(unittest.TestCase):
    """Runs 3-4: exploring branches reset the no-progress count although the revision returned its parent unchanged,
    so the unchanged-revision stop never fired."""
    def observe(self, *states):
        from end_engine.core.progress import InternalProgress
        from end_engine.experience import Trajectory
        trace = Trajectory("Task", {}, {})
        progress = InternalProgress(trace)
        stalled = [progress.observe(cycle, state) for cycle, state in enumerate(states)]
        return progress, trace.snapshot()["cycle_progress"], stalled

    def test_branches_without_answer_change_are_not_progress(self):
        a, b = {"candidate_content": ("a",), "branch_state": ()}, {"candidate_content": ("a",), "branch_state": (("x", "DONE"),)}
        progress, records, stalled = self.observe(a, a, b)
        self.assertEqual(progress.stagnant, 2)
        self.assertEqual(stalled, [False, False, True])
        self.assertEqual((records[-1]["reasons"], records[-1]["ignored"]), ([], ["branch_state"]))

    def test_branches_with_answer_change_or_other_change_still_count(self):
        a = {"candidate_content": ("a",), "branch_state": (), "issue_state": ()}
        changed_answer = {"candidate_content": ("b",), "branch_state": (("x", "DONE"),), "issue_state": ()}
        progress, records, _ = self.observe(a, changed_answer)
        self.assertEqual(progress.stagnant, 0)
        self.assertEqual(records[-1]["reasons"], ["candidate_content", "branch_state"])
        resolved = {"candidate_content": ("a",), "branch_state": (("x", "DONE"),), "issue_state": (("gap", "resolved"),)}
        progress, records, _ = self.observe(a, resolved)
        self.assertEqual((progress.stagnant, records[-1]["reasons"], records[-1]["ignored"]),
                         (0, ["issue_state"], ["branch_state"]))


class UnchangedRevisionTests(Fixture):
    """Run 3 re-judged byte-identical revisions for two cycles. A revision that returns its parent unchanged and
    reaches the no-progress patience now stops before it is verified and judged again."""
    TASK = "Inspect this bounded proposal."

    def run_stagnant(self, **kwargs):
        engine = self.engine(Stagnant(contents=("Alpha answer.",)), judge_provider=MockJudgeProvider(), **kwargs)
        result = engine.run(self.TASK, mode="normal", max_cycles=5)
        return result, engine.last_trajectory

    def test_unchanged_revision_at_patience_stops_without_rejudging(self):
        result, record = self.run_stagnant()
        self.assertEqual((result.termination_reason, result.iterations), (StopReason.NO_PROGRESS, 2))
        self.assertTrue(record["no_progress_stop"])
        unchanged = [s["data"] for s in record["steps"] if s["type"] == "unchanged_revision"]
        self.assertEqual(len(unchanged), 1)
        self.assertEqual((unchanged[0]["candidate_id"], unchanged[0]["parent_candidate_id"]), ("C2", "C1"))
        # The duplicate is neither a candidate nor verified; the answer comes from an evaluated candidate.
        self.assertEqual([c["candidate_id"] for c in record["candidates"]], ["C0", "C1"])
        self.assertEqual({v["candidate_id"] for v in record["verification"]}, {"C0", "C1"})
        self.assertEqual(result.answer, "Alpha answer.")
        self.assertTrue(record["cycle_progress"][-1]["unchanged_revision"])

    def test_tool_verifier_keeps_rechecking_unchanged_revisions(self):
        tool = CallableToolVerifier(lambda task, candidate, tests, claims: ())
        result, record = self.run_stagnant(tool_verifier=tool)
        self.assertFalse([s for s in record["steps"] if s["type"] == "unchanged_revision"])
        verified = [v["candidate_id"] for v in record["verification"]]
        self.assertEqual(verified, [c["candidate_id"] for c in record["candidates"]])


class FormatRevisionTests(Fixture):
    """Graded run BA-009 (structured): every draft lacked the required ```json block. The format check blocked stopping,
    but no revision plan asked for the format, so no revision restored it."""
    TASK = ('Question: what was the root cause? Give your final answer as one JSON object in a ```json code block '
            'with exactly these keys: "conclusion" (string), "certainty" (string).')
    PROSE = 'The root cause is likely a database issue after the deployment.'
    FIXED = '```json\n{"conclusion": "Database issue after the deployment", "certainty": "hypothesis"}\n```'

    def run_engine(self, gen, generation='structured'):
        config = EngineConfig(ledger_dir=self.temp.name, enable_branching=False, candidate_generation=generation)
        engine = self.engine(gen, config=config, judge_provider=MockJudgeProvider())
        result = engine.run(self.TASK, mode="normal", max_cycles=2)
        return result, engine.last_trajectory

    @staticmethod
    def engine_changes(plan):
        return [c for c in plan["changes"] if c["source_origin"] == "ENGINE_DERIVED" and "output format" in c["action"]]

    def test_structured_revision_is_told_the_format_violation(self):
        gen = Gen(contents=(self.PROSE, self.FIXED))
        result, record = self.run_engine(gen)
        sent = [r.context["revision_plan"] for kind, r in gen.requests if r.purpose == "revision"]
        changes = self.engine_changes(sent[0])
        self.assertEqual(len(changes), 1)
        self.assertIn("missing the required ```json code block", changes[0]["action"])
        required = [s["data"] for s in record["steps"] if s["type"] == "format_revision_required"]
        self.assertEqual(required[0]["candidate_id"], "C0")
        self.assertIn("```json", result.answer)

    def test_native_revision_prompt_carries_the_format_violation(self):
        gen = Gen(native=(self.PROSE, self.FIXED))
        result, record = self.run_engine(gen, generation='native')
        prompts = [r.prompt for kind, r in gen.requests if r.purpose == "revision"]
        self.assertIn("[ENGINE_DERIVED] Restore the output format", prompts[0])
        self.assertIn("missing the required ```json code block", prompts[0])
        self.assertIn("```json", result.answer)

    def test_no_format_change_when_the_format_is_met(self):
        gen = Gen(contents=(self.FIXED,))
        _, record = self.run_engine(gen)
        self.assertFalse([s for s in record["steps"] if s["type"] == "format_revision_required"])
        self.assertFalse([c for p in record["revision_plans"] for c in self.engine_changes(p)])


class SafeBestDraftTests(Fixture):
    """Graded run 2, BA-009 native: C1 was correct and clean (gate BLOCKED by an unvalidated advisory concern). C2 went
    back to certainty "established"; its REVISE gate outranked BLOCKED, so it replaced C1 as best and the answer was
    withheld. A draft that the output-integrity check would withhold must not replace one it would return."""
    TASK = FormatRevisionTests.TASK
    SAFE = '```json\n{"conclusion": "Database issue after the deployment", "certainty": "hypothesis"}\n```'
    OVERCLAIM = '```json\n{"conclusion": "Database issue after the deployment", "certainty": "established"}\n```'

    def run_engine(self, contents, judge):
        engine = self.engine(Gen(contents=contents), judge_provider=judge)
        result = engine.run(self.TASK, mode="normal", max_cycles=2)
        return result, engine.last_trajectory

    @staticmethod
    def gates(record):
        return {g["candidate_id"]: g["decision"] for g in record["quality_gate_decisions"]}

    def test_overclaiming_revision_does_not_replace_a_clean_blocked_draft(self):
        # The advisory objection to C0 is not validated, so C0 is BLOCKED; C1 and C2 overclaim and are REVISE.
        result, record = self.run_engine((self.SAFE, self.OVERCLAIM), adversary(objection("SYNTHETIC: weak evidence")))
        gates = self.gates(record)
        self.assertEqual((gates["C0"], gates["C1"]), ("BLOCKED", "REVISE"))
        self.assertEqual(result.best_candidate_id, "C0")
        self.assertFalse(record["output_integrity"]["blocked"])
        self.assertEqual(result.answer, self.SAFE)

    def test_clean_revision_still_replaces_an_overclaiming_draft(self):
        result, record = self.run_engine((self.OVERCLAIM, self.SAFE), MockJudgeProvider())
        self.assertEqual(self.gates(record)["C0"], "REVISE")
        self.assertEqual(result.best_candidate_id, "C1")
        self.assertEqual(result.answer, self.SAFE)


class CutOffGen(Gen):
    """SYNTHETIC: the native text calls numbered in `cut` (1-based, in call order) end at the output cap."""
    def __init__(self, *args, cut=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.cut = set(cut)

    def generate(self, request):
        response = super().generate(request)
        return replace(response, finish_reason="length" if self.counts["text"] in self.cut else "stop")


class CutOffTests(Fixture):
    """Graded runs 2-3: 3 of 12 native revisions hit the 4,096-token cap inside the reasoning. Each became a candidate
    whose answer region was the unfinished reasoning, and was judged, critiqued and checked for overclaims."""
    TASK = FormatRevisionTests.TASK
    ANSWER = FormatRevisionTests.FIXED
    REVISED = '```json\n{"conclusion": "Database issue after the deployment", "certainty": "likely"}\n```'
    CUT = "Okay, the engineers said it is definitely the database, but no metrics are available, so I should"

    def run_engine(self, gen, max_cycles):
        config = EngineConfig(ledger_dir=self.temp.name, enable_branching=False, candidate_generation="native")
        engine = self.engine(gen, config=config, judge_provider=MockJudgeProvider())
        result = engine.run(self.TASK, mode="normal", max_cycles=max_cycles)
        return result, engine.last_trajectory

    @staticmethod
    def revisions(gen):
        return [r.prompt for kind, r in gen.requests if kind == "text" and r.purpose == "revision"]

    @staticmethod
    def candidate(record, cid):
        return next(c for c in record["candidates"] if c["candidate_id"] == cid)

    def test_cut_off_revision_is_retried_once(self):
        gen = CutOffGen(native=(self.ANSWER, self.CUT, self.REVISED), cut={2})
        _, record = self.run_engine(gen, max_cycles=1)
        prompts = self.revisions(gen)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0], prompts[1])  # the same request, sent again
        c1 = self.candidate(record, "C1")
        self.assertEqual((c1["content"], c1["answer_region_status"]), (self.REVISED, "WHOLE_RESPONSE"))
        events = [s["data"] for s in record["steps"] if s["type"] == "truncated_response"]
        self.assertEqual([(e["purpose"], e["action"]) for e in events], [("revision", "retried once")])

    def test_revision_cut_off_twice_is_incomplete_and_never_returned(self):
        gen = CutOffGen(native=(self.ANSWER, self.CUT, self.CUT, self.REVISED), cut={2, 3})
        result, record = self.run_engine(gen, max_cycles=2)
        c1 = self.candidate(record, "C1")
        self.assertEqual(c1["answer_region_status"], "AMBIGUOUS")
        self.assertIn("cut off at the output limit", c1["answer_region_reason"])
        # The next revision is told why, and the user never gets the unfinished text.
        prompts = self.revisions(gen)
        self.assertEqual(len(prompts), 3)
        self.assertIn("[ENGINE_DERIVED] The previous answer was cut off", prompts[2])
        self.assertNotEqual(result.answer, self.CUT)
        self.assertIn(result.answer, (self.ANSWER, self.REVISED))

    def test_cut_off_initial_answer_is_marked_but_not_retried(self):
        # C0 stays the exact DIRECT call: one request, never repeated.
        gen = CutOffGen(native=(self.CUT, self.ANSWER), cut={1})
        result, record = self.run_engine(gen, max_cycles=0)
        self.assertEqual(len([r for k, r in gen.requests if k == "text"]), 1)
        self.assertEqual(self.candidate(record, "C0")["answer_region_status"], "AMBIGUOUS")
        self.assertTrue(record["output_integrity"]["blocked"])
        self.assertEqual(result.answer, "")


if __name__ == "__main__":
    unittest.main()
