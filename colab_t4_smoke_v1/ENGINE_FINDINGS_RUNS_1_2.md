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

## Graded run: the pilot's 4 tasks, T4 (2026-11-25)

Commit `6338ccb`, qwen3:4b (same build as the pilot, digest `359d7dd4…`), 3 cycles, `num_ctx` 16384, pilot seed 20261005. 311 offline tests passed. One trial per task and condition.

| Condition | Score now | Pilot score | Time | Calls | Tokens |
| --- | --- | --- | --- | --- | --- |
| DIRECT | 3.5/4 | 3.5/4 | 250 s | 4 | 12k |
| FULL_END_NATIVE | 2.5/4 | 3.0/4 | 1,938 s | 121 | 414k |
| FULL_END_STRUCTURED | 3.0/4 | 3.0/4 | 952 s | 110 | 226k |

| Task | DIRECT | NATIVE | STRUCTURED |
| --- | --- | --- | --- |
| BA-001 | 1 | 1 (NO_PROGRESS) | 1 (NO_PROGRESS) |
| BA-002 | 1 | 1 (INCONCLUSIVE) | 1 (INCONCLUSIVE) |
| BA-008 | 0.5 (code had an IndentationError) | 0.5 (premise never corrected) | 1 (NO_PROGRESS) |
| BA-009 | 1 | **0 (answer withheld)** | 0 (no JSON block in any draft) |

DIRECT used the same seed as the pilot but produced different text (different token counts). BA-008 went 1 → 0.5 and BA-009 went 0.5 → 1. Single-trial scores therefore move by ±0.5 from sampling alone, and none of the differences above is significant.

**END added nothing on 6 of 8 runs.** It returned its first draft C0 in 6 runs. The unchanged-revision stop fired 3 times (BA-001 both modes, BA-008 structured), as designed.

### 6. Negated sentences are flagged as overclaims, and a correct answer was withheld

BA-009 native: drafts C2 and C3 both scored **1.0** with the grader (certainty "hypothesis", missing evidence named). The engine returned C3 and withheld it. All three sentences that triggered the withholding say the cause is *not* confirmed:

- "…which is correct because we don't have the database metrics to confirm."
- "We don't have evidence to confirm, so it's a hypothesis."
- "We can change "was" to "is hypothesized to be" to avoid implying it's confirmed."

`NEGATION` in `quality/epistemic.py` lists `doesn't`, `can't` and `couldn't`, but not `don't`, `didn't`, `haven't`, `isn't`, `won't`, `without`, `lack` or `avoid`. C1 had two more of the same ("we don't have evidence to confirm that"). With these forms recognised, C3 has no flags left, so it would have been returned and the run would score 1.0 (native total 3.5/4).

The same check also flagged purpose clauses, for example "requires further investigation into database-specific metrics to confirm the exact impact" (pilot BA-009). It names a check that has not been done, not a confirmed result.

**Fix (2026-11-25, not yet run on Colab).** `NEGATION` now treats any n't contraction like "not". It also recognises "without", "lack", "unable to", "yet to" and "avoid implying/claiming…", and these absence words stop at "and"/"but", so "shipped without downtime and was verified" is still a claim. A new `PURPOSE` rule skips "to confirm" and "to be verified", except after "able" or "managed".

The change only removes flags. Replayed over the recorded pilot and graded-run drafts, it clears exactly the 5 negated BA-009 sentences and nothing else. C1's real overclaims ("so that part is established") and C0's `certainty=established` are still flagged. 20 sentences were added to the tables in `tests/test_colab_run_regressions.py`; 311 tests and the pilot's 13 pass.

### 7. Format violations block stopping but never reach the reviser

BA-009 structured: every draft was plain prose without the required ```` ```json ```` block. The engine detected this each cycle (`mandatory deterministic output-format revision` blocker, gate reason "does not follow the task's required output format"). None of the three revision plans asked for the format, because the planner sees only the critique and the weakness registry, and format violations are added to neither. The pilot scored 0 here for the same reason.

The plans instead asked to "quantify the database impact (e.g. 'query latency increased by X ms')", which the task's evidence cannot support.

**Fix (2026-11-25, not yet run on Colab).** When the current draft fails the deterministic format check, the engine now adds an ENGINE_DERIVED change to the revision plan. It works like the existing changes for bad references and overclaims, and covers internal leakage too. The change names each violation (for example "missing the required ```json code block") and says not to add claims or evidence to satisfy the format. It also records a `format_revision_required` step in the trajectory.
- Structured mode receives the change in `revision_plan`.
- Native mode receives it as a `[ENGINE_DERIVED]` line in the revision prompt.

Three tests were added in `tests/test_colab_run_regressions.py`. The structured and native tests fail without the fix. A control checks that no change is added when the format is already met. 314 tests and the pilot's 13 pass.

Still open: whether qwen3:4b in structured mode will put a fenced ```json block inside the JSON `content` string when asked. Only a Colab run can show that.

## Graded run 2: fixes 6 and 7 applied, T4 (2026-11-25)

Same setup as the first graded run. The two fixes were applied as a local patch on `6338ccb` (`END_COLAB_GRADED_FIXES_2.ipynb`); 314 offline tests passed on Colab.

| Condition | Score now | Graded run 1 | Pilot | Time | Calls | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| DIRECT | 3.5/4 | 3.5/4 | 3.5/4 | 244 s | 4 | 12k |
| FULL_END_NATIVE | 2.5/4 | 2.5/4 | 3.0/4 | 1,692 s | 106 | 348k |
| FULL_END_STRUCTURED | 3.0/4 | 3.0/4 | 3.0/4 | 862 s | 104 | 204k |

Every per-task score is the same as in graded run 1. DIRECT produced byte-identical token counts, so it reproduced exactly with the seed this time. END used 10–16% fewer tokens, mostly because three BA-001/BA-002 runs stopped a cycle earlier. BA-008 structured used more (45k → 73k).

Every draft graded with the pilot grader (gate decision after the slash):

| Run | Drafts | Returned |
| --- | --- | --- |
| BA-008 native | C0=0.5, C1=0.5, C2=0, C3=0 | C0 (0.5) |
| BA-009 native | C0=0.5, **C1=1.0/BLOCKED**, C2=0/REVISE, C3=0.75/REVISE | C3, **withheld (0)** |
| BA-009 structured | C0–C3 all 0, byte-identical | C0 (0) |

**Fix 6 (negation)** was not exercised. Replaying the old and new rules over all 26 drafts gives the same 11 flags. The one negated sentence in BA-009 C1 ("cannot be confirmed without database metrics") was already treated as negated by the old rule.

**Fix 7 (format) works in native mode, not in structured mode.**
- Native BA-009: C2 hit the 4,096-token limit inside its reasoning and had no JSON block. The format change was sent, and C3 restored the block.
- Native BA-008: the change asked for the missing explanation outside the code. The model added it, but *inside* the ```` ```python ```` block, which broke the code (C2 and C3 scored 0). The engine still returned C0, so the score did not drop.
- Structured BA-009: all three revision requests carried the format change in `revision_plan`. qwen3:4b returned C0 byte-for-byte each time, including `known_strengths` and `confidence` (122 output tokens every time). It ignored the whole plan, not only the format change.

### 8. An unsafe later draft replaces a safe best draft, and the answer is withheld

BA-009 native, C1:

```json
{"conclusion": "The root cause is a database issue (as identified by on-call engineers), but the specific cause (e.g., dependency bumps) cannot be confirmed without database metrics, traces, or query logs.",
 "certainty": "hypothesis", "evidence_used": ["E1", "E2"], "additional_evidence_needed": ["database metrics", "traces", "query logs"]}
```

The grader scored it 1.0. It had no overclaims and the right format. Its gate was BLOCKED only because an advisory model concern was not validated. The next revision went back to `"certainty": "established"` ("two engineers said it"). The judge scored C2 and C3 1.0 on every dimension, and the pairwise comparison preferred them.

`QualitySession` ranks gates REJECT < BLOCKED < REVISE < ACCEPT. C2's REVISE outranked C1's BLOCKED, so C2 became the best draft even though it had overclaims, and C3 followed. The `unsafe_tie` guard (`quality/session.py`, around line 299) only applies when the gates are equal. At the end, output integrity withheld C3, so END returned nothing. If C1 had stayed best, END native would have scored 3.0/4 and BA-009 1.0.

**Fix (2026-11-26, not yet run on Colab)** in `quality/session.py`. A draft the final output-integrity check would withhold no longer replaces a best draft it would return, even with a higher gate. The one exception is a best draft whose gate is REJECT. "Would withhold" now uses the same criteria as the final check: overclaims, bad references, an ambiguous answer region and, new here, Engine-internal leakage. A clean draft still replaces an unsafe best, as before. The returned answer can now be BLOCKED/INCONCLUSIVE instead of empty.

Revisions, judging and stopping are unchanged; only the choice of the returned draft is affected. In this run, C1 would have stayed best, and its output-integrity check finds nothing, so END should have returned C1 (grader 1.0).

Two tests were added in `tests/test_colab_run_regressions.py` (`SafeBestDraftTests`): a clean BLOCKED C0 is kept over an overclaiming REVISE C1, which fails without the fix; and a clean revision still replaces an overclaiming draft. 316 tests and the pilot's 13 pass.

### 9. Structured revisions on qwen3:4b copy the draft

BA-009 structured shows the structured reviser can return its input unchanged even with a concrete plan. In this run, the unchanged-revision stop did not fire either, because the model's revision plans added new weaknesses each cycle, so `issue_state` kept changing. Not yet investigated: whether the revision prompt or schema encourages copying (the current draft is in the context as `CURRENT_CANDIDATE` and `candidate`, with the same field names as the output schema).

## Graded run 3: fixes 6, 7 and 8 applied, T4 (2026-11-26)

Same setup again (`END_COLAB_GRADED_FIXES_3.ipynb`, local patch on `6338ccb`); 316 offline tests passed on Colab.

| Condition | Run 3 | Run 2 | Run 1 | Pilot | Time | Calls | Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DIRECT | 3.5/4 | 3.5/4 | 3.5/4 | 3.5/4 | 261 s | 4 | 12k |
| FULL_END_NATIVE | **3.5/4** | 2.5/4 | 2.5/4 | 3.0/4 | 2,077 s | 119 | 417k |
| FULL_END_STRUCTURED | 3.0/4 | 3.0/4 | 3.0/4 | 3.0/4 | 855 s | 95 | 185k |

END native matched DIRECT for the first time in these runs. It did so at about 34× DIRECT's tokens. DIRECT reproduced exactly again.

Every draft graded with the pilot grader:

| Run | Drafts | Returned |
| --- | --- | --- |
| BA-002 native | C0=1/BLOCKED, C1=1/BLOCKED, C2=0.29/REVISE (leaks "revision plan"), C3=1/BLOCKED | C0 (1.0) |
| BA-008 native | C0=0.5, C1=0.5, C2=0, C3=1.0 (cut off, see 10) | C0 (0.5) |
| BA-009 native | C0=0.5, C1=0 (cut off), C2=0.75, **C3=1.0/BLOCKED** | C3 (1.0, certainty "likely") |
| BA-009 structured | C0–C3 all 0, byte-identical (as in run 2) | C0 (0) |

**Fix 8 decided BA-002 native, not BA-009.** Both conclusions come from replaying the old selection rule on the recorded gates.
- BA-009 native: C0–C2 all overclaimed. C3 was the first clean draft, and the old rule's `safer_tie` would also have picked it. This BA-009 point comes from the model writing a clean final draft this time.
- BA-002 native: C2 leaked Engine text, and its REVISE gate outranked C0's BLOCKED. The old rule did not count leakage as unsafe, so C2 would have become best. C3 (BLOCKED, ranked lower) could not replace it, and the final check would have withheld C2, so the answer would have been empty. The new rule kept C0 (1.0).

With one trial per task, 2.5 → 3.5 is still within sampling noise. One of the two points is attributable to a fix.

### 10. Cut-off drafts are evaluated as answers

3 of 12 native revisions across runs 2 and 3 hit the 4,096-token limit inside the model's reasoning (`done_reason: length`, no `</think>`). Runs 2 BA-009 C2, 3 BA-009 C1 and 3 BA-008 C3. Each became a full candidate. Its answer region is the whole unfinished reasoning, which then gets judged, critiqued and checked for overclaims (run 2 BA-009 C2 got 9 overclaim flags, all from reasoning text).

The pilot grader scored run 3 BA-008 C3 1.0, because the reasoning contains a correct function and says "sorted() is actually stable". That is a grader artifact, not an answer. The engine kept C0 there, which was right.

Not fixed. Options: treat a cut-off native response as a format failure, retry it once with the same plan, or raise `num_predict`.

## Not concluded

These runs are one task each, run once, with the same model acting as generator and judges. They show how the mechanisms behave. They say nothing about whether END is better or worse than DIRECT in general.
