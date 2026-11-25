"""Regressions from the first live Colab runs (2026-11-23, qwen3:4b and qwen3:14b on an L4).

See colab_t4_smoke_v1/ENGINE_FINDINGS_RUNS_1_2.md.
"""
import unittest

from end_engine.core.state import StopReason
from end_engine.quality.epistemic import epistemic_integrity, extract_epistemic_claims
from end_engine.quality.mock import MockJudgeProvider
from end_engine.verification import CallableToolVerifier
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


if __name__ == "__main__":
    unittest.main()
