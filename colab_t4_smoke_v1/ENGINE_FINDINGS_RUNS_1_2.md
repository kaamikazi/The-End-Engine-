# END Engine findings from the first two Colab runs

Date: 2026-11-23. Engine commit `d9c5187` (v0.3.5.2 checkpoint branch). No Engine code was changed.

| Run | Model | Cycles | GPU | END time | Calls | END answer |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | qwen3:4b | 3 | L4 | 259 s | 31 | withheld |
| 2 | qwen3:14b | 5 | L4 | 1,349 s | 55 | withheld |

Both runs had 0 failed calls. Run 2 used the notebook copy without `NUM_CTX`. Six of its calls had prompts of about 8,300–10,000 tokens that Ollama cut to 4,098 tokens: calls 23, 32, 37, 38, 47 and 50. Those were three critiques, both syntheses and the final verification. Run 1 had no cut prompts.

Raw evidence: `D:\end_colab_run_20261123T160647Z (2).zip` (run 1) and `D:\end_colab_run_20261123T164123Z (1).zip` (run 2).

## 1. The LLM verifier copies the previous verification's scores

**What happened.** Every verification after the first returned exactly the same seven dimension scores as the previous verification it was shown. That held in all 8 later verifications across both runs and both models, while the drafts changed a lot (run 2 grew from 5.7k to 11k characters). As a result, the overall score stayed fixed: 0.8 in run 1 and 0.7286 in run 2.

**Cause.** `end_engine/verification/llm_verifier.py:31` puts `previous_verification` (scores included) into the verifier's input.

**Controlled replay.** [verifier_anchoring_replay.py](verifier_anchoring_replay.py) re-sends run 1's last verification request (C3, qwen3:4b, 3,401 prompt tokens, the same as on Colab) to local Ollama, 3 seeds per condition. Output: [verifier_anchoring_replay_output.txt](verifier_anchoring_replay_output.txt).

| Condition | Result |
| --- | --- |
| A: unchanged (prior shows 0.8 on every dimension) | 3/3 returned 0.8 on every dimension |
| B: previous verification removed | 0/3 matched. Mean: alternatives 0.0, completeness 0.57, correctness 0.53, failure_modes 0.5 |
| C: fake prior with 0.3 on every dimension | 3/3 returned 0.3 on every dimension |

The verifier echoes whatever prior it is given. The verification score and pass/fail cannot show whether a revision helped, and anything built on them (progress, no-progress stopping, candidate selection by score) inherits that.

**Fix applied (uncommitted).** `llm_verifier.py` no longer sends `previous_verification`. Open issues still reach the verifier through `weaknesses`. A new test, `test_llm_verifier_does_not_show_earlier_verification_results`, fails on the old code and passes now. The full suite passes: 304 engine tests and 13 pilot tests.

**Replay with the fix.** [verifier_fix_replay.py](verifier_fix_replay.py) re-sends all four of run 1's verifications without the prior, 2 seeds each. Output: [verifier_fix_replay_output.txt](verifier_fix_replay_output.txt).

| Draft | Length | Original score | Replayed scores |
| --- | --- | --- | --- |
| C0 | 13.6k chars | 0.8 | 0.743, 0.786 |
| C1 | 4.3k | 0.8 | 0.600, 0.586 |
| C2 | 4.0k | 0.8 | 0.600, 0.643 |
| C3 | 3.4k | 0.8 | 0.629, 0.514 |

The score now moves. It rates the long first draft about 0.15 above the shortened revisions. The differences between C1, C2 and C3 are within seed noise (up to about 0.11).

**Caution.** The higher-scoring C0 is the draft with the invented "battle-tested in production for 3+ years" claim, and the overclaim check (section 2) does not flag it. If score feeds candidate selection, this fix alone could make a fabricated draft more likely to be returned. Fix section 2's missed patterns before relying on it.

**Comparability.** Runs made with this fix are not comparable to the frozen v0.3.5.x pilots, because the verifier input changed.

## 2. The overclaim word-match flags definitions and plans

**What happened.** Run 2's last draft was withheld for two sentences:

- "Pruning effectiveness: The percentage of pruned memories that are **confirmed** to be low-impact…" This is the definition of a metric.
- "The inclusion of performance metrics… **demonstrates** the effectiveness…" This is self-praise, which is a fair catch.

**Cause.** `end_engine/quality/epistemic.py:14-15` (`STRONG`) and `:94-97` treat words such as verified, confirmed and demonstrates as status claims when "is/are/has" comes before them. The only exceptions are negation and if/whether/could/might/may/would/should. With no executed evidence, `epistemic_integrity` marks every match as an overclaim (`:136-144`).

**Reproduction with `extract_epistemic_claims`.**

| Sentence | Flagged | Should be |
| --- | --- | --- |
| Run 2 metric definition ("…that are confirmed to be low-impact…") | yes | no |
| "Entries are deleted only after they are confirmed to be stale by the scorer." | yes | no |
| "Run a soak test; the bound is verified when memory stays under 600 MB for 24 hours." | yes | no |
| "Recall rate: the share of queries whose answers are verified against the archive." | yes | no |
| Run 2 self-praise ("…demonstrates the effectiveness…") | yes | yes |
| Run 1 "The system consistently demonstrates memory usage ≤600 MB under real-world loads." | yes | yes |
| "This design has been verified in production." | yes | yes |

The check also misses real fabrications that avoid those words. Run 1's first draft said "battle-tested in production for 3+ years" and "never exceeded 1 GB" in testing, and it had 0 flagged phrases.

**Fix applied (uncommitted)** in `end_engine/quality/epistemic.py`.

- Status words are no longer treated as claims in three cases:
  - in a metric-definition line ("Name: the percentage/share/rate… of");
  - after "when/until/unless/once/after/before/while" with no comma in between;
  - when followed by a pass criterion ("verified when/if/once/until…").
- A new `track_record` claim type covers "battle-tested", "tested/deployed/used in production", "N years of testing/production" and "in our/real-world tests/benchmarks". Only a negation directly before the phrase cancels it.
- The existing exceptions (negation, hypothetical, quotation, attribution) apply to both.
- Tests live in `tests/test_colab_run_regressions.py`. On the original code, 9 of their cases fail. The full suite passes: 307 engine tests and 13 pilot tests.

**All drafts from both runs, rechecked.**

| Draft | Before | After |
| --- | --- | --- |
| Run 1 C0 (and its DIRECT answer) | 0 flagged | 2 flagged: "battle-tested in production for 3+ years", "In 1 year of testing… never exceeded 1 GB" |
| Run 1 C1, C2 | 0 | 0 |
| Run 1 C3 | 1 ("consistently demonstrates ≤600 MB under real-world loads") | 1 (same) |
| Run 2 C0–C4 and DIRECT | 0 | 0 |
| Run 2 C5 | 2 (metric definition + self-praise) | 1 (self-praise only) |

Run 2's answer would still be withheld, now only for the self-praise sentence, which is a fair catch. The verifier-fix caution in section 1 is covered: run 1's C0 is now flagged, so it would be withheld instead of returned.

This remains a word-based check. It will still miss fabrications phrased in other ways.

## 3. One flagged sentence empties the whole answer

`end_engine/engine.py:450-458` sets `answer = ''` when the selected draft fails output integrity. It does not fall back to an earlier draft that passes. Run 2's C0–C4 and run 1's C0–C2 had 0 flagged phrases (by `extract_epistemic_claims`), but only the selected final draft was checked.

**Options (a design decision for you).**
- Fall back to the best earlier draft that passes the integrity check.
- Return the draft with the flagged sentences marked or removed, keeping the label INCONCLUSIVE.

## 4. The critique loop pushes drafts toward the words the gate blocks

**What happened.** The same advisory weakness, W001, came back every cycle: "no evidence that these mechanisms ensure selective retention…". It was rediscovered 3 or more times. The revision plans answered it with "Add explicit evidence or performance metrics that demonstrate…".

On a design task there is no executable evidence, so the model adds evidence-style language instead. In both runs the flagged phrases first appear in the final draft, right after those plans: run 1 C3 has 1, and run 2 C5 has 2.

**Proposed fix.** When the task has no executable checks, have the critique ask for mechanisms, failure handling and a test plan, not evidence. Also tell the revision step not to state measured or observed results.

## 5. A revision changed nothing and still used a full cycle

Run 2's cycle 3 revision (call M24, prompt containing C2) returned C2 byte-for-byte. The engine recorded it as new candidate C3 and verified and judged it again. Counting the revision call itself, that cycle took 8 calls and about 3.4 minutes.

**Why the existing no-progress stop didn't fire (run 3).**
- Cycle 3 (C3 = C2) counted 1 stagnant cycle.
- Cycle 4 explored branches, and changed `branch_state` reset the count, even though C4 = C3.
- Cycle 5's three-word edit counted as new content.

The patience of 2 was never reached.

**Fix applied (uncommitted)** in `end_engine/engine.py`. When a revision returns its parent unchanged (same `substantive_text` as the progress check uses), it counts as a stagnant cycle. If that reaches `no_progress_patience`, the run stops with NO_PROGRESS before the duplicate is verified or judged. The duplicate is logged as an `unchanged_revision` step and is not added as a candidate. The answer comes from an already-evaluated candidate.

The rule does not apply in two cases:
- when mandatory blockers are pending (overclaims, format, minimum cycles, open branches);
- when a tool verifier is configured, because a re-check can then add executed evidence (`test_integrity_review` covers that case).

**Tests.**
- Two new tests are in `tests/test_colab_run_regressions.py`. The stop test fails on the original code.
- All existing tests pass unchanged: 309 engine tests and 13 pilot tests.
- An earlier version that stopped on the first unchanged revision broke 5 existing tests (patience semantics and the tool-verifier case), so it was dropped.

**Effect on run 3, worked out from its own records.** The run would have stopped right after the cycle 4 revision (C4 = C3), with the same answer (C1). Saved: 15 of 53 calls, 399 of 1,513 s (26%), and 100k of 320k tokens (31%).

**Not fixed.**
- Trivial edits (C5's three words) still count as progress.
- The planner still asks for empirical validation that a design task cannot have. Changing that prompt changes every run's model requests and needs a live run to judge.

## Run 3: both fixes applied (2026-11-23)

Notebook `END_COLAB_RUN3_FIXES.ipynb` patched the clone of `d9c5187`. The hashes in `summary.json` match the local fixed files. Settings: qwen3:14b, 5 cycles, L4, 16,384 context. Raw evidence: `D:\end_colab_run_20261123T174200Z.zip`.

| | Run 2 (unfixed, 8k context) | Run 3 (fixed, 16k context) |
| --- | --- | --- |
| END time / calls / tokens | 1,349 s / 55 / 263k | 1,515 s / 53 / 320k |
| Prompts cut / near limit | 6 / 2 | 0 / 0 (largest 10,920) |
| Returned answer | empty (withheld) | **C1, 8.7k chars**, label INCONCLUSIVE |
| Flagged sentences in any draft | C5: 2 | 0 in all drafts |

**What worked**
- The answer was returned, labelled INCONCLUSIVE.
- Every gate said "assessment requires evidence", which is the honest outcome for a design task with no executable checks.
- The engine picked C1 as best. C0 had the highest verifier score (0.729 vs 0.7), so verifier score did not drive selection here.

**What did not**
- **Cycles 3–5 changed almost nothing (#4 and #5 confirmed).** The revision plans for C2–C4 asked for "empirical validation through simulation or real-world testing". The model cannot produce that, so it returned its input. C2, C3 and C4 are byte-identical, and C5 differs from C4 by three words. From the cycle 3 revision onward, the calls took 907 s of the 1,512 s model time without a meaningful change.
- **The verifier still barely moved.** C1–C5 got identical dimension scores. C2–C4 are identical, so the same scores are expected there. C1 (8.7k chars) and C2 (12.4k chars) also scored the same, though. This run cannot show whether the fix changed anything for qwen3:14b. The 4b replay could (section 1).
- **A real technical error survived 5 cycles.** The returned answer, and DIRECT, recommend t-SNE to compress stored memory vectors (lines 42 and 93). t-SNE is a visualization method with no out-of-sample transform, so it is unsuitable for this. No judge flagged it.
- **The first draft is identical to the DIRECT answer.** C0 is byte-identical to DIRECT because the seeds and prompts match. In this run, END's only real change is C0 → C1: more named mechanisms (LRU, FAISS, embedding indexing, RL prioritization), with the same structure.

**Cost.** The returned answer cost about 250 times DIRECT's tokens (320k vs 1.3k) and 31 times its time.

## Run 4: all three fixes (2026-11-24)

Notebook `END_COLAB_RUN4_FIXES.ipynb`. The hashes of all 5 fixed files match the local ones, and 309/309 tests passed on Colab. Colab assigned an **A100 40GB**, not an L4, so floating-point differences changed the outputs from the first draft onward. Run 4 is not a like-for-like replay of run 3. Raw evidence: `D:\end_colab_run_20261124T145718Z.zip`.

| | Run 3 (L4) | Run 4 (A100) |
| --- | --- | --- |
| END time / calls / tokens | 1,515 s / 53 / 320k | 418 s / 53 / 242k |
| Revisions returning the parent unchanged | 2 of 5 (C3, C4) | 3 of 5 (C2, C4, C5) |
| Early stop | (rule not yet present) | **did not fire** |
| Returned answer | C1, INCONCLUSIVE | C3, 6.8k chars, INCONCLUSIVE |
| Flagged sentences | 0 | 0 |

**Why the early stop didn't fire.** The unchanged revisions were never consecutive in the progress count:
- C2 = C1 came after a real change.
- C3 changed.
- Cycle 4 explored branches, which reset the count, even though C4 = C3.
- C5 = C4 then started from 0.

As in run 3, `branch_state` changing without the answer changing defeated the patience rule. The engine fix works as designed but does not address this.

**Root cause, confirmed again.** All 5 revision plans asked for "references to real-world implementations or empirical studies" or "performance metrics from real-world implementations". The revision prompt rightly ignores invented evidence, so 3 of 5 revisions changed nothing.

**What END added.** C3 = C0 plus a rewritten considerations section (security via hashing and access control, consistency checks, bias detection, privacy). It cost 242k tokens and 7 minutes. DIRECT took 1.4k tokens and 17 s.

**Verifier.** Identical C4 and C5 got different scores (0.700 vs 0.657), so the verifier no longer echoes the previous result. Different C1 and C3 got identical scores, though, so on this task the 14b verifier is coarse and noisy rather than informative.

**Planner prompt change: tried, not effective locally, reverted.** `revision_planner.py` is back to the committed version and its guard test is removed. The replay script and output are kept as the record.

`revision_planner.py` now adds: "A revision cannot create evidence … ask instead for the concrete mechanism, how it fails…, a test or measurement plan…, or an explicitly stated limitation." A guard test is in `tests/test_colab_run_regressions.py`, and all 310 tests pass.

[planner_fix_replay.py](planner_fix_replay.py) re-sent run 4's five plan requests to local `qwen3:8b` with the old and the new prompt. qwen3:14b is not installed locally. Output: [planner_fix_replay_output.txt](planner_fix_replay_output.txt).

| Prompt | Changes matching evidence keywords | Read by hand as real evidence demands |
| --- | --- | --- |
| Old | 6 of 10 | about 4 |
| New | 6 of 11 | about 4 ("references to empirical studies", "prototype or simulation to validate…") |

The instruction is largely ignored. The plans follow the weakness they are asked to address, and that weakness is itself an evidence gap ("no evidence these mechanisms ensure…"), raised by the critique every cycle. A prompt line placed before about 7k tokens of JSON context does not override that. qwen3:14b might respond differently; run 5 would show it.

**Branch progress fix applied (uncommitted)** in `end_engine/core/progress.py`. When the candidate content is unchanged, a `branch_state` change no longer counts as progress. It is recorded under `ignored` in `cycle_progress`. Any other change (issues, claims, evidence, assumptions, contradictions) still counts. Pending branch work already blocks stopping through the "branch action pending" blocker.

- Two unit tests are in `tests/test_colab_run_regressions.py`, and both fail on the original code.
- The full suite passes: 311 engine tests and 13 pilot tests.

**Effect, worked out from the recorded runs (both rules together).**

| Run | Stops after | Saved calls | Saved time | Saved tokens | Answer |
| --- | --- | --- | --- | --- | --- |
| 3 | cycle 4 revision | 15 / 53 | 399 / 1,513 s (26%) | 100k / 320k (31%) | same (C1) |
| 4 | cycle 5 revision (before: no stop) | 6 / 53 | 27 / 416 s (6%) | 28k / 242k (11%) | same (C3) |

Run 4 saves little because its unchanged revisions were not consecutive (C2, then C4 and C5), and the budget ended at cycle 5 anyway. With a patience of 2, a single unchanged revision is still re-judged once by design.

**Still open.** Plans keep asking for evidence because the critique raises the same evidence-gap weakness every cycle. A prompt line did not fix that on qwen3:8b. A real fix probably belongs in how evidence-gap weaknesses are raised or resolved for tasks without executable checks.

## Run 5: four fixes, T4 (2026-11-24)

Notebook `END_COLAB_RUN5_FIXES.ipynb` patched all 6 files, and the hashes match the local ones. 311/311 tests passed on Colab. Colab assigned a **T4**. Raw evidence: `D:\end_colab_run_20261124T154157Z.zip`.

**The early stop fired as designed.**

| Cycle | Draft | Progress record |
| --- | --- | --- |
| 1 | C1 changed | progress |
| 2 | C2 = C1 | stagnant 1 |
| 3 | C3 changed | progress |
| 4 | C4 = C3, branches explored | `branch_state` ignored, stagnant 1 |
| 5 | revision returned C4 unchanged | stagnant 2, **stopped before re-judging** |

The run ended with NO_PROGRESS: "2 completed cycles without meaningful internal state change; revision 5 returned C4 unchanged". The last call was that revision. Re-judging C4 had taken 6 calls, 159 s and 27k tokens, which is what this saved.

**Result.** 48 calls, 1,666 s, 217k tokens, 0 failures, no flagged sentences.
- END returned **C0**, which is byte-identical to the DIRECT answer.
- The verifier scored C0 0.786, C1/C2 0.700 and C3/C4 0.686, and the engine kept the first draft.
- DIRECT produced the same text in 84 s and 1.3k tokens.

**Verifier.** Unlike runs 1–4, the score now separates drafts (0.786, 0.700, 0.686). Identical drafts got identical scores, so it is consistent for identical text and differs for different text.

**Unchanged revisions again 2 of 4** (C2 = C1, C4 = C3): every other revision is a no-op. The evidence-gap loop from section 4 is still the main cost.

## Not concluded

These runs are one task each, run once, with the same model acting as generator and judges. They show how the mechanisms behave. They say nothing about whether END is better or worse than DIRECT in general.
