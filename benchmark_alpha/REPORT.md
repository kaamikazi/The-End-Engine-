# END Engine Benchmark Alpha — Benchmark Alpha live run



## 1. Executive summary

Generated from stored records. Measured values only; see §21–22 for limits.

- DIRECT: passed 15/24 runs (pass rate 0.625), mean external score 0.6458, mean tokens 3147.75, mean calls 1.0, mean wall 192.1073 s.
- SELF_REFLECT: passed 16/24 runs (pass rate 0.6667), mean external score 0.7738, mean tokens 14850.8333, mean calls 3.0, mean wall 590.0425 s.
- END_LITE: passed 8/24 runs (pass rate 0.3333), mean external score 0.3371, mean tokens 7579.7083, mean calls 4.5, mean wall 95.2327 s.
- FULL_END: passed 8/24 runs (pass rate 0.3333), mean external score 0.3646, mean tokens 12666.9167, mean calls 7.1667, mean wall 196.0316 s.
- FULL_END_vs_DIRECT: 4 wins / 10 ties / 10 losses over 24 matched task-trials; score delta -0.2812; token ×4.024; latency ×1.02.
- FULL_END_vs_SELF_REFLECT: 5 wins / 6 ties / 13 losses over 24 matched task-trials; score delta -0.4092; token ×0.853; latency ×0.332.
- END_LITE_vs_DIRECT: 3 wins / 11 ties / 10 losses over 24 matched task-trials; score delta -0.3087; token ×2.408; latency ×0.496.
- FULL_END_vs_END_LITE: 1 wins / 23 ties / 0 losses over 24 matched task-trials; score delta 0.0275; token ×1.671; latency ×2.058.
- END_LITE_vs_SELF_REFLECT: 4 wins / 6 ties / 14 losses over 24 matched task-trials; score delta -0.4367; token ×0.51; latency ×0.161.
- SELF_REFLECT_vs_DIRECT: 7 wins / 13 ties / 4 losses over 24 matched task-trials; score delta 0.128; token ×4.718; latency ×3.071.
- END_LITE internal vs external (LLM verifier (no gate in END_LITE)): {'TRUE_ACCEPT': 0, 'FALSE_ACCEPT': 0, 'TRUE_REJECT': 16, 'FALSE_REJECT': 8, 'INCONCLUSIVE': 0}.
- FULL_END internal vs external (QualityGate): {'TRUE_ACCEPT': 0, 'FALSE_ACCEPT': 0, 'TRUE_REJECT': 0, 'FALSE_REJECT': 2, 'INCONCLUSIVE': 22}.
- Runs completed: 96 of 144 planned (stop after trial 2: 96 runs (12 tasks x 4 conditions x 2 trials) instead of the planned 144; decided by user).

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

## 2. Engine identity

```json
{
 "files": 52,
 "fingerprint_scope": "end_engine/**/*.py and pyproject.toml",
 "git_commit": null,
 "git_status": "not a git repository",
 "source_sha256": "d1a9f68bb8cacf1e4dc4384180d5b6971bebb8209b34ea50f1bb94939ceed7a2",
 "version": "0.3.4"
}
```

## 3. Model / provider identity

```json
{
 "model": "qwen3:4b",
 "model_identity": {
  "context_length": 262144,
  "details": {
   "context_length": 262144,
   "embedding_length": 2560,
   "families": [
    "qwen3"
   ],
   "family": "qwen3",
   "format": "gguf",
   "parameter_size": "4.0B",
   "parent_model": "",
   "quantization_level": "Q4_K_M"
  },
  "digest": "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7",
  "name": "qwen3:4b",
  "server_version": "0.35.0"
 },
 "provider": "ollama-local",
 "same_model_all_conditions": true,
 "settings": {
  "context_limit_reported": 262144,
  "context_window_requested": 8192,
  "max_output_tokens": 4096,
  "seed": "per call: sha256(base_seed=20260930, trial seed, call index)",
  "structured_retries": 1,
  "system_instructions": null,
  "temperature": 0.7,
  "thinking": false,
  "timeout_seconds": 900.0,
  "top_p": 0.8
 }
}
```

## 4. Methodology

- Trials per task: 3; conditions: DIRECT, SELF_REFLECT, END_LITE, FULL_END; randomization seed 20261001 (trial-major; task order and condition order shuffled per trial; planned and executed order stored in manifest.json).
- Every condition receives the task prompt verbatim. Hidden expectations are never sent to the model.
- One run is one (task, trial, condition). Failures are recorded, never retried at run level and never repaired.
- Task set hash: `9e177f6d6be25acf82010d898e42a86c7a4d516af882eaa1725bcb5efe468ca6`.
- Truncated text answers (text call reached the output cap; kept as the answer): {'DIRECT': 9, 'SELF_REFLECT': 12, 'END_LITE': 0, 'FULL_END': 0}.
- Configuration changes, scope decision and repository events during the run (from manifest.json):

```json
{
 "configuration_changes": [
  {
   "affected_completed_runs": [],
   "at_run_count": 0,
   "change": "fresh start with num_predict 4096 and truncated text kept",
   "reason": "see aborted_sessions/session1_num_predict_2048/NOTE.md"
  },
  {
   "affected_completed_runs": [],
   "at_run_count": 6,
   "change": "transport timeout_seconds 300 -> 900",
   "preserved_original": "aborted_sessions/session2_transport_timeout/",
   "re_executed": [
    "BA-003.T1.SELF_REFLECT"
   ],
   "reason": "timeout was below the time needed for the 4096-token output cap; BA-003.T1.SELF_REFLECT timed out"
  },
  {
   "at_run_count": 80,
   "change": "none (settings unchanged); one run re-executed",
   "preserved_original": "aborted_sessions/session3_server_connection_reset/",
   "re_executed": [
    "BA-003.T2.DIRECT"
   ],
   "reason": "Ollama connection reset at 21:15Z when the controlling session ended"
  }
 ],
 "scope_decision": {
  "by": "user",
  "decided": "2026-09-30",
  "decision": "stop after trial 2: 96 runs (12 tasks x 4 conditions x 2 trials) instead of the planned 144",
  "reason": "projected ~7 further hours for trial 3 on the local GPU",
  "trial_3": "not run"
 },
 "repository_events_during_run": [
  {
   "engine_source_fingerprint_after": "d1a9f68bb8cacf1e4dc4384180d5b6971bebb8209b34ea50f1bb94939ceed7a2 (unchanged)",
   "event": "git repository initialised and commit 6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7 'Initial public release of END Engine' made outside this session at about 2026-09-30T20:55Z",
   "files_changed_outside_benchmark": [
    ".gitignore (modified)",
    ".gitattributes (added)",
    "README.md (modified)"
   ],
   "note": "git metadata read from .git files; the repository is owned by another Windows account, so git commands were not run",
   "observed": "2026-10-01T04:52Z"
  }
 ]
}
```

## 5. Task set

| task | category | runs per condition |
|---|---|---|
| BA-001 | easy_transformation | 2 |
| BA-002 | debugging | 2 |
| BA-003 | algorithm | 2 |
| BA-004 | constraint_satisfaction | 2 |
| BA-005 | hidden_assumption | 2 |
| BA-006 | software_architecture | 2 |
| BA-007 | failure_recovery | 2 |
| BA-008 | misleading_premise | 2 |
| BA-009 | missing_evidence | 2 |
| BA-010 | contradictory_evidence | 2 |
| BA-011 | narrow_check_broad_claim | 2 |
| BA-012 | overthinking_trap | 2 |

Task definitions (prompt, constraints, evaluation type, expected properties, failure conditions): `tasks/BA-*.json`.

## 6. Conditions

```json
{
 "END_LITE": {
  "adversarial_judge": null,
  "engine_config": {
   "enable_branching": false,
   "meta_check_interval": 1000,
   "post_acceptance_cycles": 0,
   "quality_evaluation": false
  },
  "judge_provider": null,
  "max_cycles": 2,
  "mode": "normal",
  "secondary_judge": null,
  "tool_verifier": null
 },
 "FULL_END": {
  "adversarial_judge": "defaults to the primary judge (same model)",
  "engine_config": "EngineConfig() defaults (branching on, post_acceptance_cycles 0, judge_min_confidence 0.75)",
  "judge_provider": "ModelJudgeProvider(same model transport)",
  "max_cycles": null,
  "mode": null,
  "secondary_judge": null,
  "tool_verifier": null
 }
}
```
DIRECT: one text generation. SELF_REFLECT: answer → self-critique → one revision (three text generations).

## 7. External evaluation methodology

Deterministic evaluators only (executable unit tests in an isolated interpreter after an AST whitelist, known answers, a constraint validator, fixed-option structured rubrics, evidence-JSON validators with regex checks). No model judge contributes to any score. Hallucination counters cover only the designed failure classes. Answers with ambiguous wording are flagged for manual review (see summary.json `review_flags`).

## 8. Overall results

| Condition | Pass rate | Mean score (sd) | Unsupported claims | Mean tokens | Mean calls | Mean wall s | Run errors | END EXTERNAL_BLOCKER |
|---|---|---|---|---|---|---|---|---|
| DIRECT | 15/24 | 0.6458 (0.4773) | 0 | 3147.75 | 1.0 | 192.1073 | 0 | 0 |
| SELF_REFLECT | 16/24 | 0.7738 (0.3711) | 1 | 14850.8333 | 3.0 | 590.0425 | 0 | 0 |
| END_LITE | 8/24 | 0.3371 (0.4792) | 0 | 7579.7083 | 4.5 | 95.2327 | 0 | 17 |
| FULL_END | 8/24 | 0.3646 (0.4833) | 0 | 12666.9167 | 7.1667 | 196.0316 | 0 | 22 |

Format compliance (diagnostic; does not change any score — the required answer structure is a hard requirement of every task):

| Condition | required structure present | pass rate when present |
|---|---|---|
| DIRECT | 18/24 | 0.8333 |
| SELF_REFLECT | 21/24 | 0.7619 |
| END_LITE | 11/24 | 0.7273 |
| FULL_END | 12/24 | 0.6667 |

Score distribution per condition (mean / median / min / max / sd):

| Condition | mean | median | min | max | sd |
|---|---|---|---|---|---|
| DIRECT | 0.6458 | 1.0 | 0.0 | 1.0 | 0.4773 |
| SELF_REFLECT | 0.7738 | 1.0 | 0.0 | 1.0 | 0.3711 |
| END_LITE | 0.3371 | 0.0 | 0.0 | 1.0 | 0.4792 |
| FULL_END | 0.3646 | 0.0 | 0.0 | 1.0 | 0.4833 |

## 9. Results by task type

| Category | DIRECT | SELF_REFLECT | END_LITE | FULL_END |
|---|---|---|---|---|
| algorithm | 0.0 / 0.0 | 1.0 / 1.0 | 0.5 / 0.5454 | 0.5 / 0.5 |
| constraint_satisfaction | 0.0 / 0.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| contradictory_evidence | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| debugging | 1.0 / 1.0 | 0.0 / 0.2857 | 1.0 / 1.0 | 1.0 / 1.0 |
| easy_transformation | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| failure_recovery | 0.0 / 0.0 | 0.0 / 0.625 | 0.5 / 0.5 | 0.5 / 0.875 |
| hidden_assumption | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| misleading_premise | 0.5 / 0.75 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| missing_evidence | 1.0 / 1.0 | 0.5 / 0.875 | 0.0 / 0.0 | 0.0 / 0.0 |
| narrow_check_broad_claim | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| overthinking_trap | 1.0 / 1.0 | 0.5 / 0.5 | 1.0 / 1.0 | 1.0 / 1.0 |
| software_architecture | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

(pass rate / mean score)

| Task | DIRECT | SELF_REFLECT | END_LITE | FULL_END |
|---|---|---|---|---|
| BA-001 | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-002 | 2/2 [1.0, 1.0] | 0/2 [0.2857, 0.2857] | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] |
| BA-003 | 0/2 [0.0, 0.0] | 2/2 [1.0, 1.0] | 1/2 [0.0909, 1.0] | 1/2 [0.0, 1.0] |
| BA-004 | 0/2 [0.0, 0.0] | 2/2 [1.0, 1.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-005 | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-006 | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-007 | 0/2 [0.0, 0.0] | 0/2 [0.75, 0.5] | 1/2 [1.0, 0.0] | 1/2 [1.0, 0.75] |
| BA-008 | 1/2 [1.0, 0.5] | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] |
| BA-009 | 2/2 [1.0, 1.0] | 1/2 [1.0, 0.75] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-010 | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-011 | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] | 0/2 [0.0, 0.0] | 0/2 [0.0, 0.0] |
| BA-012 | 2/2 [1.0, 1.0] | 1/2 [0.0, 1.0] | 2/2 [1.0, 1.0] | 2/2 [1.0, 1.0] |

## 10. DIRECT vs END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_vs_DIRECT | 4/10/10 | -0.2812 | 4.024 | 1.02 | {'FULL_END': 0, 'DIRECT': 0} | {'FULL_END': 0, 'DIRECT': 0} |
| END_LITE_vs_DIRECT | 3/11/10 | -0.3087 | 2.408 | 0.496 | {'END_LITE': 0, 'DIRECT': 0} | {'END_LITE': 0, 'DIRECT': 0} |

## 11. SELF_REFLECT vs END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_vs_SELF_REFLECT | 5/6/13 | -0.4092 | 0.853 | 0.332 | {'FULL_END': 0, 'SELF_REFLECT': 1} | {'FULL_END': 0, 'SELF_REFLECT': 0} |
| END_LITE_vs_SELF_REFLECT | 4/6/14 | -0.4367 | 0.51 | 0.161 | {'END_LITE': 0, 'SELF_REFLECT': 1} | {'END_LITE': 0, 'SELF_REFLECT': 0} |

## 12. END_LITE vs FULL_END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_vs_END_LITE | 1/23/0 | 0.0275 | 1.671 | 2.058 | {'FULL_END': 0, 'END_LITE': 0} | {'FULL_END': 0, 'END_LITE': 0} |

Wins/ties/losses use the meaningful-difference rule (|Δscore| ≥ 0.1 or pass/fail change).

## 13. END INTERNAL QUALITY VS EXTERNAL RESULT

**END_LITE** (internal basis: LLM verifier (no gate in END_LITE))

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 0 | 0 | 16 | 8 | 0 |

**FULL_END** (internal basis: QualityGate)

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 0 | 0 | 0 | 2 | 22 |

**How END runs ended** (termination reason, final gate, and Engine errors that stopped the loop; IDs normalized):

*END_LITE* — mean END cycles 0.5833

| termination | runs |
|---|---|
| EXTERNAL_BLOCKER | 17 |
| BUDGET_EXHAUSTED | 7 |

| final quality_gate | runs |
|---|---|
| BLOCKED | 24 |

| Engine error (stage: message) | runs |
|---|---|
| verification: Invalid or duplicate weakness update: <id> | 6 |
| critique: Critique references unknown weakness <id>:completeness | 2 |
| critique: Critique references unknown weakness <id> | 2 |
| verification: Invalid or duplicate weakness update: timezone_ambiguity | 1 |
| verification: Invalid or duplicate weakness update: w2_retry_on_timeout | 1 |
| verification: Invalid or duplicate weakness update: problem_statement_confusion | 1 |
| verification: Invalid or duplicate weakness update: root_cause | 1 |
| verification: Invalid or duplicate weakness update: known_strengths | 1 |
| verification: Invalid or duplicate weakness update: E1 | 1 |
| verification: Invalid or duplicate weakness update: Unicode handling | 1 |

*FULL_END* — mean END cycles 0.3333

| termination | runs |
|---|---|
| EXTERNAL_BLOCKER | 22 |
| BUDGET_EXHAUSTED | 2 |

| final quality_gate | runs |
|---|---|
| BLOCKED | 22 |
| REJECT | 2 |

| Engine error (stage: message) | runs |
|---|---|
| verification: Invalid or duplicate weakness update: <id> | 7 |
| revision_plan: Revision plan targets unknown weakness IDs | 7 |
| critique: Unknown knowledge ID or missing evidence: <id> | 2 |
| verification: Invalid or duplicate weakness update: completeness | 2 |
| verification: Invalid or duplicate weakness update: prevention | 1 |
| verification: Invalid or duplicate weakness update: correctness | 1 |
| verification: Invalid or duplicate weakness update: E1 | 1 |
| branch_exploration: Cannot adopt from a non-promising branch | 1 |

## 14. EPISTEMIC / HALLUCINATION RESULTS

Counts over Benchmark Alpha tasks only; not universal hallucination rates.

| Condition | unsupported_claim_count | unsupported_high_impact_claim_count | fabricated_reference_count | scope_overreach_count | contradiction_ignored_count | false_execution_claim_count | correct_uncertainty_count |
|---|---|---|---|---|---|---|---|
| DIRECT | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| SELF_REFLECT | 1 | 0 | 0 | 0 | 0 | 0 | 5 |
| END_LITE | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FULL_END | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 15. Candidate progression

| run | external score per candidate | peak | returned | best internal | missed peak | regressions |
|---|---|---|---|---|---|---|
| BA-001.T1.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-001.T1.FULL_END | C0:0.0 | C0 | C0 |  | False | 0 |
| BA-001.T2.END_LITE | C0:0.0 C1:0.0 C2:0.0 | C0 | C2 | C2 | False | 0 |
| BA-001.T2.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-002.T1.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-002.T1.FULL_END | C0:1.0 | C0 | C0 |  | False | 0 |
| BA-002.T2.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-002.T2.FULL_END | C0:1.0 C1:1.0 C2:1.0 C3:1.0 | C0 | C0 | C0 | False | 0 |
| BA-003.T1.END_LITE | C0:0.0 C1:0.0909 C2:0.0909 | C1 | C2 | C2 | False | 0 |
| BA-003.T1.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-003.T2.END_LITE | C0:1.0 C1:1.0 C2:1.0 | C0 | C2 | C2 | False | 0 |
| BA-003.T2.FULL_END | C0:1.0 | C0 | C0 |  | False | 0 |
| BA-004.T1.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-004.T1.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-004.T2.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-004.T2.FULL_END | C0:0.0 | C0 | C0 |  | False | 0 |
| BA-005.T1.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-005.T1.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-005.T2.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-005.T2.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-006.T1.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-006.T1.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-006.T2.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-006.T2.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-007.T1.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-007.T1.FULL_END | C0:1.0 | C0 | C0 |  | False | 0 |
| BA-007.T2.END_LITE | C0:0.0 C1:0.0 C2:0.0 | C0 | C2 | C2 | False | 0 |
| BA-007.T2.FULL_END | C0:0.75 | C0 | C0 |  | False | 0 |
| BA-008.T1.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-008.T1.FULL_END | C0:1.0 | C0 | C0 |  | False | 0 |
| BA-008.T2.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-008.T2.FULL_END | C0:1.0 C1:1.0 C2:1.0 C3:1.0 | C0 | C0 | C0 | False | 0 |
| BA-009.T1.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-009.T1.FULL_END | C0:0.0 | C0 | C0 |  | False | 0 |
| BA-009.T2.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-009.T2.FULL_END | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-010.T1.END_LITE | C0:0.0 | C0 | C0 | C0 | False | 0 |
| BA-010.T1.FULL_END | C0:0.0 | C0 | C0 |  | False | 0 |
| BA-010.T2.END_LITE | C0:0.0 C1:0.0 C2:0.0 | C0 | C2 | C2 | False | 0 |
| BA-010.T2.FULL_END | C0:0.0 | C0 | C0 |  | False | 0 |
| BA-011.T1.END_LITE | C0:0.0 C1:0.0 C2:0.0 | C0 | C2 | C2 | False | 0 |
| BA-011.T1.FULL_END | C0:0.0 C1:0.0 C2:0.0 | C0 | C0 | C0 | False | 0 |
| BA-011.T2.END_LITE | C0:0.0 C1:0.0 C2:0.0 | C0 | C2 | C2 | False | 0 |
| BA-011.T2.FULL_END | C0:0.0 | C0 | C0 |  | False | 0 |
| BA-012.T1.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-012.T1.FULL_END | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-012.T2.END_LITE | C0:1.0 | C0 | C0 | C0 | False | 0 |
| BA-012.T2.FULL_END | C0:1.0 | C0 | C0 |  | False | 0 |

## 16. Overthinking cases

| run | signals | tokens | END cycles |
|---|---|---|---|
| BA-001.T2.END_LITE | B_cycles_without_external_benefit | 13972 | 2 |
| BA-002.T2.FULL_END | B_cycles_without_external_benefit | 44656 | 3 |
| BA-003.T1.END_LITE | B_cycles_without_external_benefit | 18019 | 2 |
| BA-003.T2.END_LITE | B_cycles_without_external_benefit | 25148 | 2 |
| BA-007.T2.END_LITE | B_cycles_without_external_benefit | 26116 | 2 |
| BA-008.T2.FULL_END | B_cycles_without_external_benefit | 55522 | 3 |
| BA-010.T2.END_LITE | B_cycles_without_external_benefit | 14967 | 2 |
| BA-011.T1.END_LITE | B_cycles_without_external_benefit | 17259 | 2 |
| BA-011.T1.FULL_END | B_cycles_without_external_benefit | 45360 | 2 |
| BA-011.T2.END_LITE | B_cycles_without_external_benefit | 15501 | 2 |

## 17. Rollback analysis

| run | rejected | returned | rejected score | returned score | label |
|---|---|---|---|---|---|
| BA-002.T2.FULL_END | C1 | C0 | 1.0 | 1.0 | ROLLBACK_NEUTRAL |
| BA-002.T2.FULL_END | C2 | C0 | 1.0 | 1.0 | ROLLBACK_NEUTRAL |
| BA-002.T2.FULL_END | C3 | C0 | 1.0 | 1.0 | ROLLBACK_NEUTRAL |
| BA-008.T2.FULL_END | C1 | C0 | 1.0 | 1.0 | ROLLBACK_NEUTRAL |
| BA-008.T2.FULL_END | C2 | C0 | 1.0 | 1.0 | ROLLBACK_NEUTRAL |
| BA-008.T2.FULL_END | C3 | C0 | 1.0 | 1.0 | ROLLBACK_NEUTRAL |
| BA-011.T1.FULL_END | C1 | C0 | 0.0 | 0.0 | ROLLBACK_NEUTRAL |
| BA-011.T1.FULL_END | C2 | C0 | 0.0 | 0.0 | ROLLBACK_NEUTRAL |

Quality-delta validation (END's comparator vs external delta):

```json
{
 "FULL_END": {
  "MATCH": 5,
  "PARTIAL_MISMATCH": 2,
  "UNCLASSIFIED": 1
 }
}
```

## 18. Operator observations

Exploratory only; sample sizes are too small for causal claims.

**END_LITE**

| operator | uses | positive | negative | neutral | no revision | mean cycle tokens |
|---|---|---|---|---|---|---|
| CONSTRAINT | 5 | 0 | 0 | 5 | 0 | 4842.0 |
| EVIDENCE | 6 | 0 | 0 | 6 | 0 | 7116.5 |
| HOW | 1 | 0 | 0 | 1 | 0 | 5453.0 |
| VERIFY | 2 | 0 | 0 | 2 | 0 | 5898.0 |

**FULL_END**

| operator | uses | positive | negative | neutral | no revision | mean cycle tokens |
|---|---|---|---|---|---|---|
| ALTERNATIVE | 1 | 0 | 0 | 0 | 1 | 9267.0 |
| ASSUMPTION | 1 | 0 | 0 | 1 | 0 | 6222.0 |
| CONSTRAINT | 4 | 0 | 0 | 0 | 4 | 3655.5 |
| EVIDENCE | 9 | 0 | 0 | 4 | 5 | 4894.8 |
| SECOND_ORDER_EFFECT | 1 | 0 | 0 | 1 | 0 | 5753.0 |
| VERIFY | 2 | 0 | 0 | 2 | 0 | 5510.5 |

## 19. Cost / latency

No provider pricing is configured: monetary cost = null.

| Condition | mean score | Δscore vs DIRECT | mean calls | calls × | mean tokens | tokens × | mean wall s | latency × |
|---|---|---|---|---|---|---|---|---|
| DIRECT | 0.6458 | 0.0 | 1.0 | 1.0 | 3147.75 | 1.0 | 192.1073 | 1.0 |
| SELF_REFLECT | 0.7738 | 0.128 | 3.0 | 3.0 | 14850.8333 | 4.718 | 590.0425 | 3.071 |
| END_LITE | 0.3371 | -0.3087 | 4.5 | 4.5 | 7579.7083 | 2.408 | 95.2327 | 0.496 |
| FULL_END | 0.3646 | -0.2812 | 7.1667 | 7.167 | 12666.9167 | 4.024 | 196.0316 | 1.02 |

**A. Unconstrained:** the table above (each condition's intended behaviour).

**B. Roughly matched budget:** no budget-matched baseline condition was executed in Alpha, so no matched-budget result exists. The multipliers above show how far apart the budgets are; the only near-matched view available is END's own first candidate C0 (one generation, like DIRECT) against DIRECT in the same task-trial:

END C0 vs DIRECT pairs: 48; mean C0 score 0.349, mean DIRECT score 0.6458.

## 20. Failure archive

`failures/<TAG>/<run_id>/` holds byte-identical copies of the trial and evaluation records plus a trajectory reference with its SHA-256. No cause is inferred.

| tag | runs |
|---|---|
| CORRECT_ABSTENTION | 11 |
| DIRECT_BEAT_END | 20 |
| FALSE_REJECT | 10 |
| OVERTHINKING | 10 |
| SELF_REFLECT_BEAT_END | 27 |

## 21. Limitations

- Benchmark Alpha is small; trial counts are far too small for statistical significance.
- Results are specific to this model, these settings and this 12-task set.
- Hallucination measurements cover only the designed failure classes, via task-specific patterns; they can miss or mis-flag wording (see review flags).
- Model judges can be wrong; here END's internal judges are the same model as the generator.
- Public benchmark contamination may exist for classic problems (e.g. meeting rooms, palindromes).
- FULL_END has no tool verifier and uses a same-model judge, so it cannot reach ACCEPT_VERIFIED by design.
- END structured calls get one retry after a parse/schema/length failure (same policy for all structured calls); DIRECT and SELF_REFLECT make only text calls.

## 22. What Benchmark Alpha does NOT prove

- A positive result does not prove general reasoning improvement.
- A negative result does not prove END can never work.
- No result here generalizes beyond this model, task set and configuration.
