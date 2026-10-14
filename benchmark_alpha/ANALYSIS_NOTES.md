### 1b. Analyst reading of the data (MANUAL — written after inspecting the records; not computed)

**Scope of what ran.** One model (`qwen3:4b` Q4_K_M, local Ollama), 12 tasks, 4 conditions, **2 trials (96 runs)**.
The plan was 3 trials (144 runs); trial 3 was not run, by the user's decision, because the local GPU needed about
7 more hours. Every number here comes from these 96 runs only.

**Headline.** On this task set and model, FULL_END passed **8/24** runs, versus 15/24 for DIRECT and 16/24 for
SELF_REFLECT. It used 4.0× DIRECT's tokens and 7.2× its calls, at about the same latency. END_LITE also passed 8/24.
**There is no measurable reason in Benchmark Alpha to believe END v0.3.4 is better than the baselines on these tasks.**
SELF_REFLECT was the strongest condition, but it also broke 4 previously correct answers.

**Why END performed as it did (observed directly in the trajectories):**

1. **The END loop almost never ran.**
   - **FULL_END:** 22 of 24 runs ended in `EXTERNAL_BLOCKER`, with a mean of 0.33 END cycles.
   - **END_LITE:** 17 of 24 ended in `EXTERNAL_BLOCKER`, with a mean of 0.58 cycles.
   - **The cause in every case is the Engine's strict validation of model output:**
     - the verifier's `weakness_updates` named IDs that do not exist (`C0`, `completeness`, `E1`, `timezone_ambiguity`, …);
     - critiques or revision plans referenced unknown weakness IDs;
     - one branch synthesis tried to adopt from a non-promising branch.
   - **The effect:** v0.3.4 treats one malformed model field as fatal for the whole loop and returns its first
     candidate, C0. So END's answers are, almost always, its unrevised C0.
2. **END's C0 is weaker than DIRECT's answer.** Mean external score is 0.35 for END C0 against 0.65 for DIRECT, over
   48 pairs.
   - END requests the candidate inside a JSON field, and the model then writes a short answer with little worked
     reasoning. Examples: BA-001 got 36.6 °C → 67.9 °F and 21.5 °C → 60.7 °F; BA-005 compared local clock times.
   - END often drops the task's required output format and answers in prose: END has the required structure in 11–12
     of 24 runs, against 18 of 24 for DIRECT.
3. **END's wins are DIRECT's truncations.** All 9 DIRECT failures are answers cut off at the 4096-token output cap while
   the model was still reasoning in-band. FULL_END beat DIRECT only on BA-003.T2, BA-007.T1, BA-007.T2 (all DIRECT
   truncations) and BA-008.T2 (DIRECT did not question the false premise).
4. **END's internal quality judgments did not track external correctness.**
   - **FULL_END:** the QualityGate accepted nothing, so there were 0 true accepts and 0 false accepts. 22 runs were
     inconclusive (blocked), and both decided runs were **FALSE_REJECT** (the gate gave REJECT; the answers were correct).
   - **BA-002.T2:** the judges rejected four correct candidates while quoting the buggy loop from the *task text*, as if
     the candidate contained it.
   - **BA-008.T2:** the judges rejected every candidate *for correctly stating that `sorted()` is stable*, citing the
     task's false premise. END's evaluator amplified the misleading premise; the returned answer was still correct.
   - **END_LITE:** the LLM verifier never passed a returned candidate (0 of 24), giving 16 TRUE_REJECT and 8
     FALSE_REJECT. It does not discriminate.
5. **Rollback, overthinking and operators: END barely revised, so little to measure.**
   - 8 rollback events occurred, in 3 runs. All are ROLLBACK_NEUTRAL: the rejected and the returned candidates scored
     the same, and in two of the runs the rejections were themselves false.
   - No MISSED_PEAK or REGRESSION occurred, and no END revision changed an external score.
   - The 10 OVERTHINKING tags are all type B: cycles and cost without external benefit.
   - Operator effects: 0 positive and 0 negative revisions.
6. **Epistemic slice.**
   - *Counted:* END produced no fabricated references, no scope overreach and no false execution claims.
   - *But:* it also earned 0 correct-uncertainty credit, because its evidence-task answers failed the required JSON
     format and score 0 there. Read by hand, ignoring format, 7 of those 12 answers are substantively sound:
     - BA-011 (narrow check, broad claim): 4 of 4 refuse the guarantee.
     - BA-010 (contradictory evidence): 3 of 4 keep the conflict open. BA-010.T1.END_LITE resolves it by fiat
       ("with a high degree of certainty").
     - BA-009 (missing evidence): 0 of 4. All lean on the engineers' agreement, and BA-009.T2.FULL_END calls it
       "independently confirmed".
   - *The baselines:* DIRECT got 6 correct-uncertainty answers and SELF_REFLECT got 5, with 1 unsupported established
     root cause (BA-009.T2).

**Answers to the benchmark's questions (Benchmark Alpha only).**

| Question | Answer |
|---|---|
| Did END ever make a correct answer worse? | Not measurably. Its revisions were rare and externally neutral. SELF_REFLECT did, 4 times. |
| Did rollback actually help? | No observed effect: 8 events, all neutral. |
| Did END internally misjudge failures? | Yes: 10 FALSE_REJECT (2 FULL_END, 8 END_LITE). FULL_END had 22 inconclusive runs and no accepts at all. |
| How much inference did END consume? | FULL_END: 12.7k tokens and 7.2 calls per run on average (4.0× DIRECT's tokens), despite mostly aborting early. |

**Configuration caveats that shape these results.**
- **In-band reasoning.** `qwen3:4b` reasons in-band even with `think: false`. Free-text conditions use that space and
  sometimes run out of it. END's JSON-field answers get little of it.
- **Two transport fixes before the main data.** The output cap and the timeout were each corrected once before the main
  data were collected; see Methodology.
- **A post-hoc detector correction.** One evaluator correction was made after the results were seen: the
  false-execution pattern counted "if we run B at time 0" (scheduling language) as a test-execution claim. It was
  narrowed and every run was re-scored. It removed exactly 2 spurious END counts and changed no pass/fail result.
