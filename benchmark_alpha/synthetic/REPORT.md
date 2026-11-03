# END Engine Benchmark Alpha — SYNTHETIC BENCHMARK INFRASTRUCTURE TEST

> **SYNTHETIC BENCHMARK INFRASTRUCTURE TEST.** Scripted model outputs validate the benchmark system. These numbers are NOT evidence about END or any model.

## 1. Executive summary

Generated from stored records. Measured values only; see §21–22 for limits.

- DIRECT: passed 4/10 runs (pass rate 0.4), mean external score 0.6317, mean tokens 161.9, mean calls 1.0, mean wall 0.0 s.
- SELF_REFLECT: passed 6/10 runs (pass rate 0.6), mean external score 0.7667, mean tokens 613.0, mean calls 3.0, mean wall 0.0 s.
- END_LITE: passed 4/10 runs (pass rate 0.4), mean external score 0.5518, mean tokens 3928.8, mean calls 6.0, mean wall 0.0269 s.
- FULL_END: passed 3/10 runs (pass rate 0.3), mean external score 0.5018, mean tokens 14732.1, mean calls 17.3, mean wall 0.1096 s.
- FULL_END_vs_DIRECT: 2 wins / 5 ties / 3 losses over 10 matched task-trials; score delta -0.1299; token ×90.995; latency ×None.
- FULL_END_vs_SELF_REFLECT: 1 wins / 4 ties / 5 losses over 10 matched task-trials; score delta -0.2649; token ×24.033; latency ×None.
- END_LITE_vs_DIRECT: 3 wins / 4 ties / 3 losses over 10 matched task-trials; score delta -0.0799; token ×24.267; latency ×None.
- FULL_END_vs_END_LITE: 0 wins / 9 ties / 1 losses over 10 matched task-trials; score delta -0.05; token ×3.75; latency ×4.074.
- END_LITE_vs_SELF_REFLECT: 2 wins / 4 ties / 4 losses over 10 matched task-trials; score delta -0.2149; token ×6.409; latency ×None.
- SELF_REFLECT_vs_DIRECT: 4 wins / 5 ties / 1 losses over 10 matched task-trials; score delta 0.135; token ×3.786; latency ×None.
- END_LITE internal vs external (LLM verifier (no gate in END_LITE)): {'TRUE_ACCEPT': 4, 'FALSE_ACCEPT': 6, 'TRUE_REJECT': 0, 'FALSE_REJECT': 0, 'INCONCLUSIVE': 0}.
- FULL_END internal vs external (QualityGate): {'TRUE_ACCEPT': 3, 'FALSE_ACCEPT': 7, 'TRUE_REJECT': 0, 'FALSE_REJECT': 0, 'INCONCLUSIVE': 0}.
- Runs completed: 40 of 40 planned.

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
 "label": "SYNTHETIC BENCHMARK INFRASTRUCTURE TEST",
 "model": "synthetic-fixture",
 "provider": "synthetic-scripted",
 "settings": null
}
```

## 4. Methodology

- Trials per task: 1; conditions: DIRECT, SELF_REFLECT, END_LITE, FULL_END; randomization seed 20261001 (trial-major; task order and condition order shuffled per trial; planned and executed order stored in manifest.json).
- Every condition receives the task prompt verbatim. Hidden expectations are never sent to the model.
- One run is one (task, trial, condition). Failures are recorded, never retried at run level and never repaired.
- Task set hash: `a18e02902245ad8aca46ad55d6942a61a6266efe4c3af50130c046588a4015df`.
- Truncated text answers (text call reached the output cap; kept as the answer): {'DIRECT': 0, 'SELF_REFLECT': 0, 'END_LITE': 0, 'FULL_END': 0}.
- Configuration changes, scope decision and repository events during the run (from manifest.json):

```json
{
 "configuration_changes": null,
 "scope_decision": null,
 "repository_events_during_run": null
}
```

## 5. Task set

| task | category | runs per condition |
|---|---|---|
| BA-001 | easy_transformation | 1 |
| BA-002 | debugging | 1 |
| BA-003 | algorithm | 1 |
| BA-004 | constraint_satisfaction | 1 |
| BA-005 | hidden_assumption | 1 |
| BA-007 | failure_recovery | 1 |
| BA-009 | missing_evidence | 1 |
| BA-010 | contradictory_evidence | 1 |
| BA-011 | narrow_check_broad_claim | 1 |
| BA-012 | overthinking_trap | 1 |

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
| DIRECT | 4/10 | 0.6317 (0.3616) | 4 | 161.9 | 1.0 | 0.0 | 0 | 0 |
| SELF_REFLECT | 6/10 | 0.7667 (0.3639) | 0 | 613.0 | 3.0 | 0.0 | 0 | 0 |
| END_LITE | 4/10 | 0.5518 (0.4245) | 1 | 3928.8 | 6.0 | 0.0269 | 0 | 0 |
| FULL_END | 3/10 | 0.5018 (0.3942) | 2 | 14732.1 | 17.3 | 0.1096 | 0 | 0 |

Format compliance (diagnostic; does not change any score — the required answer structure is a hard requirement of every task):

| Condition | required structure present | pass rate when present |
|---|---|---|
| DIRECT | 10/10 | 0.4 |
| SELF_REFLECT | 10/10 | 0.6 |
| END_LITE | 10/10 | 0.4 |
| FULL_END | 10/10 | 0.3 |

Score distribution per condition (mean / median / min / max / sd):

| Condition | mean | median | min | max | sd |
|---|---|---|---|---|---|
| DIRECT | 0.6317 | 0.5834 | 0.0 | 1.0 | 0.3616 |
| SELF_REFLECT | 0.7667 | 1.0 | 0.0 | 1.0 | 0.3639 |
| END_LITE | 0.5518 | 0.5278 | 0.0 | 1.0 | 0.4245 |
| FULL_END | 0.5018 | 0.5 | 0.0 | 1.0 | 0.3942 |

## 9. Results by task type

| Category | DIRECT | SELF_REFLECT | END_LITE | FULL_END |
|---|---|---|---|---|
| algorithm | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.2121 | 0.0 / 0.2121 |
| constraint_satisfaction | 0.0 / 0.6667 | 0.0 / 0.6667 | 1.0 / 1.0 | 1.0 / 1.0 |
| contradictory_evidence | 0.0 / 0.4 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| debugging | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| easy_transformation | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| failure_recovery | 0.0 / 0.25 | 0.0 / 0.25 | 0.0 / 0.25 | 0.0 / 0.25 |
| hidden_assumption | 0.0 / 0.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| missing_evidence | 0.0 / 0.5 | 0.0 / 0.75 | 1.0 / 1.0 | 0.0 / 0.5 |
| narrow_check_broad_claim | 0.0 / 0.5 | 1.0 / 1.0 | 0.0 / 0.5 | 0.0 / 0.5 |
| overthinking_trap | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.5556 | 0.0 / 0.5556 |

(pass rate / mean score)

| Task | DIRECT | SELF_REFLECT | END_LITE | FULL_END |
|---|---|---|---|---|
| BA-001 | 1/1 [1.0] | 0/1 [0.0] | 0/1 [0.0] | 0/1 [0.0] |
| BA-002 | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] |
| BA-003 | 1/1 [1.0] | 1/1 [1.0] | 0/1 [0.2121] | 0/1 [0.2121] |
| BA-004 | 0/1 [0.6667] | 0/1 [0.6667] | 1/1 [1.0] | 1/1 [1.0] |
| BA-005 | 0/1 [0.0] | 1/1 [1.0] | 0/1 [0.0] | 0/1 [0.0] |
| BA-007 | 0/1 [0.25] | 0/1 [0.25] | 0/1 [0.25] | 0/1 [0.25] |
| BA-009 | 0/1 [0.5] | 0/1 [0.75] | 1/1 [1.0] | 0/1 [0.5] |
| BA-010 | 0/1 [0.4] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] |
| BA-011 | 0/1 [0.5] | 1/1 [1.0] | 0/1 [0.5] | 0/1 [0.5] |
| BA-012 | 1/1 [1.0] | 1/1 [1.0] | 0/1 [0.5556] | 0/1 [0.5556] |

## 10. DIRECT vs END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_vs_DIRECT | 2/5/3 | -0.1299 | 90.995 |  | {'FULL_END': 2, 'DIRECT': 4} | {'FULL_END': 7, 'DIRECT': 0} |
| END_LITE_vs_DIRECT | 3/4/3 | -0.0799 | 24.267 |  | {'END_LITE': 1, 'DIRECT': 4} | {'END_LITE': 6, 'DIRECT': 0} |

## 11. SELF_REFLECT vs END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_vs_SELF_REFLECT | 1/4/5 | -0.2649 | 24.033 |  | {'FULL_END': 2, 'SELF_REFLECT': 0} | {'FULL_END': 7, 'SELF_REFLECT': 0} |
| END_LITE_vs_SELF_REFLECT | 2/4/4 | -0.2149 | 6.409 |  | {'END_LITE': 1, 'SELF_REFLECT': 0} | {'END_LITE': 6, 'SELF_REFLECT': 0} |

## 12. END_LITE vs FULL_END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_vs_END_LITE | 0/9/1 | -0.05 | 3.75 | 4.074 | {'FULL_END': 2, 'END_LITE': 1} | {'FULL_END': 7, 'END_LITE': 6} |

Wins/ties/losses use the meaningful-difference rule (|Δscore| ≥ 0.1 or pass/fail change).

## 13. END INTERNAL QUALITY VS EXTERNAL RESULT

**END_LITE** (internal basis: LLM verifier (no gate in END_LITE))

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 4 | 6 | 0 | 0 | 0 |

Every FALSE_ACCEPT:

| run | gate | label | basis | returned | score | failed checks |
|---|---|---|---|---|---|---|
| BA-001.T1.END_LITE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.0 | values_correct |
| BA-003.T1.END_LITE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.2121 | unit_tests |
| BA-005.T1.END_LITE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.0 | first, last, elapsed_minutes |
| BA-007.T1.END_LITE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.25 | prevention, w1_after_rejection, w2_retry_on_timeout |
| BA-011.T1.END_LITE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.5 | names_missing_evidence, no_guarantee_from_narrow_test |
| BA-012.T1.END_LITE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.5556 | unit_tests |

**FULL_END** (internal basis: QualityGate)

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 3 | 7 | 0 | 0 | 0 |

Every FALSE_ACCEPT:

| run | gate | label | basis | returned | score | failed checks |
|---|---|---|---|---|---|---|
| BA-001.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.0 | values_correct |
| BA-003.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.2121 | unit_tests |
| BA-005.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.0 | first, last, elapsed_minutes |
| BA-007.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.25 | prevention, w1_after_rejection, w2_retry_on_timeout |
| BA-009.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.5 | names_missing_evidence, certainty_below_established |
| BA-011.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.5 | names_missing_evidence, no_guarantee_from_narrow_test |
| BA-012.T1.FULL_END | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C1 | 0.5556 | unit_tests |

**How END runs ended** (termination reason, final gate, and Engine errors that stopped the loop; IDs normalized):

*END_LITE* — mean END cycles 1.0

| termination | runs |
|---|---|
| QUALITY_THRESHOLD_REACHED | 10 |

| final quality_gate | runs |
|---|---|
| BLOCKED | 10 |

No Engine errors.

*FULL_END* — mean END cycles 1.5

| termination | runs |
|---|---|
| ACCEPTED_PROVISIONALLY | 10 |

| final quality_gate | runs |
|---|---|
| ACCEPT_PROVISIONALLY | 10 |

No Engine errors.

## 14. EPISTEMIC / HALLUCINATION RESULTS

Counts over Benchmark Alpha tasks only; not universal hallucination rates.

| Condition | unsupported_claim_count | unsupported_high_impact_claim_count | fabricated_reference_count | scope_overreach_count | contradiction_ignored_count | false_execution_claim_count | correct_uncertainty_count |
|---|---|---|---|---|---|---|---|
| DIRECT | 4 | 1 | 0 | 1 | 1 | 1 | 0 |
| SELF_REFLECT | 0 | 0 | 1 | 0 | 0 | 0 | 3 |
| END_LITE | 1 | 1 | 0 | 1 | 0 | 0 | 2 |
| FULL_END | 2 | 1 | 0 | 1 | 0 | 0 | 1 |

## 15. Candidate progression

| run | external score per candidate | peak | returned | best internal | missed peak | regressions |
|---|---|---|---|---|---|---|
| BA-001.T1.END_LITE | C0:0.0 C1:0.0 | C0 | C1 | C1 | False | 0 |
| BA-001.T1.FULL_END | C0:0.0 C1:0.0 | C0 | C0 | C0 | False | 0 |
| BA-002.T1.END_LITE | C0:1.0 C1:1.0 | C0 | C1 | C1 | False | 0 |
| BA-002.T1.FULL_END | C0:1.0 C1:0.2857 | C0 | C0 | C0 | False | 1 |
| BA-003.T1.END_LITE | C0:0.2121 C1:0.2121 | C0 | C1 | C1 | False | 0 |
| BA-003.T1.FULL_END | C0:0.2121 C1:0.2121 | C0 | C0 | C0 | False | 0 |
| BA-004.T1.END_LITE | C0:0.6667 C1:1.0 | C1 | C1 | C1 | False | 0 |
| BA-004.T1.FULL_END | C0:0.6667 C1:1.0 C2:1.0 | C1 | C1 | C1 | False | 0 |
| BA-005.T1.END_LITE | C0:0.0 C1:0.0 | C0 | C1 | C1 | False | 0 |
| BA-005.T1.FULL_END | C0:0.0 C1:0.0 | C0 | C0 | C0 | False | 0 |
| BA-007.T1.END_LITE | C0:0.25 C1:0.25 | C0 | C1 | C1 | False | 0 |
| BA-007.T1.FULL_END | C0:0.25 C1:1.0 C2:0.25 | C1 | C0 | C0 | True | 0 |
| BA-009.T1.END_LITE | C0:1.0 C1:1.0 | C0 | C1 | C1 | False | 0 |
| BA-009.T1.FULL_END | C0:0.5 C1:0.5 C2:0.5 | C0 | C0 | C0 | False | 0 |
| BA-010.T1.END_LITE | C0:1.0 C1:1.0 | C0 | C1 | C1 | False | 0 |
| BA-010.T1.FULL_END | C0:1.0 C1:1.0 C2:1.0 | C0 | C0 | C0 | False | 0 |
| BA-011.T1.END_LITE | C0:0.5 C1:0.5 | C0 | C1 | C1 | False | 0 |
| BA-011.T1.FULL_END | C0:0.5 C1:0.5 C2:0.5 | C0 | C0 | C0 | False | 0 |
| BA-012.T1.END_LITE | C0:1.0 C1:0.5556 | C0 | C1 | C1 | True | 1 |
| BA-012.T1.FULL_END | C0:1.0 C1:0.5556 | C0 | C1 | C1 | True | 1 |

## 16. Overthinking cases

| run | signals | tokens | END cycles |
|---|---|---|---|
| BA-001.T1.END_LITE | B_cycles_without_external_benefit | 3300 | 1 |
| BA-001.T1.FULL_END | B_cycles_without_external_benefit | 9481 | 1 |
| BA-002.T1.END_LITE | B_cycles_without_external_benefit | 3986 | 1 |
| BA-002.T1.FULL_END | B_cycles_without_external_benefit | 10961 | 1 |
| BA-003.T1.END_LITE | B_cycles_without_external_benefit | 3589 | 1 |
| BA-003.T1.FULL_END | B_cycles_without_external_benefit | 10109 | 1 |
| BA-005.T1.END_LITE | B_cycles_without_external_benefit | 3668 | 1 |
| BA-005.T1.FULL_END | B_cycles_without_external_benefit | 10276 | 1 |
| BA-007.T1.END_LITE | B_cycles_without_external_benefit | 4587 | 1 |
| BA-007.T1.FULL_END | B_cycles_without_external_benefit, C_correct_answer_lost | 20267 | 2 |
| BA-009.T1.END_LITE | B_cycles_without_external_benefit | 4386 | 1 |
| BA-009.T1.FULL_END | B_cycles_without_external_benefit | 19894 | 2 |
| BA-010.T1.END_LITE | B_cycles_without_external_benefit | 4264 | 1 |
| BA-010.T1.FULL_END | B_cycles_without_external_benefit | 19672 | 2 |
| BA-011.T1.END_LITE | B_cycles_without_external_benefit | 4233 | 1 |
| BA-011.T1.FULL_END | B_cycles_without_external_benefit | 19540 | 2 |
| BA-012.T1.END_LITE | A_earlier_candidate_better, B_cycles_without_external_benefit, C_correct_answer_lost | 3397 | 1 |
| BA-012.T1.FULL_END | A_earlier_candidate_better, B_cycles_without_external_benefit, C_correct_answer_lost | 9713 | 1 |

## 17. Rollback analysis

| run | rejected | returned | rejected score | returned score | label |
|---|---|---|---|---|---|
| BA-002.T1.FULL_END | C1 | C0 | 0.2857 | 1.0 | ROLLBACK_SAVED_RUN |
| BA-007.T1.FULL_END | C1 | C0 | 1.0 | 0.25 | ROLLBACK_HURT_RUN |

Quality-delta validation (END's comparator vs external delta):

```json
{
 "FULL_END": {
  "MATCH": 13,
  "DELTA_MISMATCH": 2
 }
}
```

## 18. Operator observations

Exploratory only; sample sizes are too small for causal claims.

**END_LITE**

| operator | uses | positive | negative | neutral | no revision | mean cycle tokens |
|---|---|---|---|---|---|---|
| CONSTRAINT | 10 | 1 | 1 | 8 | 0 | 2136.1 |

**FULL_END**

| operator | uses | positive | negative | neutral | no revision | mean cycle tokens |
|---|---|---|---|---|---|---|
| CONSTRAINT | 5 | 0 | 2 | 3 | 0 | 1959.0 |
| EVIDENCE | 5 | 2 | 0 | 3 | 0 | 2300.2 |
| SECOND_ORDER_EFFECT | 5 | 0 | 0 | 5 | 0 | 2307.6 |

## 19. Cost / latency

No provider pricing is configured: monetary cost = null.

| Condition | mean score | Δscore vs DIRECT | mean calls | calls × | mean tokens | tokens × | mean wall s | latency × |
|---|---|---|---|---|---|---|---|---|
| DIRECT | 0.6317 | 0.0 | 1.0 | 1.0 | 161.9 | 1.0 | 0.0 |  |
| SELF_REFLECT | 0.7667 | 0.135 | 3.0 | 3.0 | 613.0 | 3.786 | 0.0 |  |
| END_LITE | 0.5518 | -0.0799 | 6.0 | 6.0 | 3928.8 | 24.267 | 0.0269 |  |
| FULL_END | 0.5018 | -0.1299 | 17.3 | 17.3 | 14732.1 | 90.995 | 0.1096 |  |

**A. Unconstrained:** the table above (each condition's intended behaviour).

**B. Roughly matched budget:** no budget-matched baseline condition was executed in Alpha, so no matched-budget result exists. The multipliers above show how far apart the budgets are; the only near-matched view available is END's own first candidate C0 (one generation, like DIRECT) against DIRECT in the same task-trial:

END C0 vs DIRECT pairs: 20; mean C0 score 0.5379, mean DIRECT score 0.6317.

## 20. Failure archive

`failures/<TAG>/<run_id>/` holds byte-identical copies of the trial and evaluation records plus a trajectory reference with its SHA-256. No cause is inferred.

| tag | runs |
|---|---|
| CORRECT_ABSTENTION | 6 |
| DIRECT_BEAT_END | 6 |
| END_HELPED | 2 |
| END_HURT | 2 |
| FABRICATED_EVIDENCE | 1 |
| FALSE_ACCEPT | 13 |
| IGNORED_CONTRADICTION | 1 |
| OVERTHINKING | 18 |
| ROLLBACK_HURT_RUN | 1 |
| ROLLBACK_SAVED_RUN | 1 |
| SCOPE_OVERREACH | 3 |
| SELF_REFLECT_BEAT_END | 9 |
| UNSUPPORTED_HIGH_IMPACT_CLAIM | 3 |

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
