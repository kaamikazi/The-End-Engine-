# END Engine Benchmark Beta — SYNTHETIC BENCHMARK INFRASTRUCTURE TEST

> **SYNTHETIC BENCHMARK INFRASTRUCTURE TEST.** Scripted model outputs validate the benchmark system. These numbers are NOT evidence about END or any model.

## 1. Executive summary

Generated from stored records. Measured values only; see §21–22 for limits.

- DIRECT: passed 4/10 runs (pass rate 0.4), mean external score 0.6317, mean tokens 161.9, mean calls 1.0, mean wall 0.0 s.
- SELF_REFLECT: passed 6/10 runs (pass rate 0.6), mean external score 0.7667, mean tokens 613.0, mean calls 3.0, mean wall 0.0 s.
- END_LITE_NATIVE: passed 4/10 runs (pass rate 0.4), mean external score 0.5518, mean tokens 3655.2, mean calls 6.0, mean wall 0.0267 s.
- FULL_END_NATIVE: passed 3/10 runs (pass rate 0.3), mean external score 0.5018, mean tokens 16466.9, mean calls 17.3, mean wall 0.1204 s.
- FULL_END_STRUCTURED: passed 3/10 runs (pass rate 0.3), mean external score 0.5018, mean tokens 16864.8, mean calls 17.3, mean wall 0.1258 s.
- FULL_END_NATIVE_vs_DIRECT: 2 wins / 5 ties / 3 losses over 10 matched task-trials; score delta -0.1299; token ×101.71; latency ×None.
- FULL_END_STRUCTURED_vs_DIRECT: 2 wins / 5 ties / 3 losses over 10 matched task-trials; score delta -0.1299; token ×104.168; latency ×None.
- END_LITE_NATIVE_vs_DIRECT: 3 wins / 4 ties / 3 losses over 10 matched task-trials; score delta -0.0799; token ×22.577; latency ×None.
- FULL_END_NATIVE_vs_SELF_REFLECT: 1 wins / 4 ties / 5 losses over 10 matched task-trials; score delta -0.2649; token ×26.863; latency ×None.
- FULL_END_STRUCTURED_vs_SELF_REFLECT: 1 wins / 4 ties / 5 losses over 10 matched task-trials; score delta -0.2649; token ×27.512; latency ×None.
- END_LITE_NATIVE_vs_SELF_REFLECT: 2 wins / 4 ties / 4 losses over 10 matched task-trials; score delta -0.2149; token ×5.963; latency ×None.
- FULL_END_NATIVE_vs_FULL_END_STRUCTURED: 0 wins / 10 ties / 0 losses over 10 matched task-trials; score delta 0.0; token ×0.976; latency ×0.957.
- FULL_END_NATIVE_vs_END_LITE_NATIVE: 0 wins / 9 ties / 1 losses over 10 matched task-trials; score delta -0.05; token ×4.505; latency ×4.509.
- SELF_REFLECT_vs_DIRECT: 4 wins / 5 ties / 1 losses over 10 matched task-trials; score delta 0.135; token ×3.786; latency ×None.
- END_LITE_NATIVE internal vs external (LLM verifier (no gate in END_LITE_NATIVE)): {'TRUE_ACCEPT': 4, 'FALSE_ACCEPT': 6, 'TRUE_REJECT': 0, 'FALSE_REJECT': 0, 'INCONCLUSIVE': 0}.
- FULL_END_NATIVE internal vs external (QualityGate): {'TRUE_ACCEPT': 3, 'FALSE_ACCEPT': 7, 'TRUE_REJECT': 0, 'FALSE_REJECT': 0, 'INCONCLUSIVE': 0}.
- FULL_END_STRUCTURED internal vs external (QualityGate): {'TRUE_ACCEPT': 3, 'FALSE_ACCEPT': 7, 'TRUE_REJECT': 0, 'FALSE_REJECT': 0, 'INCONCLUSIVE': 0}.
- Runs completed: 50 of 50 planned.

## 2. Engine identity

```json
{
 "files": 55,
 "fingerprint_scope": "end_engine/**/*.py and pyproject.toml",
 "git_commit": null,
 "git_status": "not a git repository",
 "source_sha256": "520d2052832eaee93f7c8931e028762c7008006ae61f2fdc7ec6589d7e4bd448",
 "version": "0.3.5"
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

- Trials per task: 1; conditions: DIRECT, SELF_REFLECT, END_LITE_NATIVE, FULL_END_NATIVE, FULL_END_STRUCTURED; randomization seed 20261102 (trial-major; task order and condition order shuffled per trial; planned and executed order stored in manifest.json).
- Every condition receives the task prompt verbatim. Hidden expectations are never sent to the model.
- One run is one (task, trial, condition). Failures are recorded, never retried at run level and never repaired.
- Task set hash: `a18e02902245ad8aca46ad55d6942a61a6266efe4c3af50130c046588a4015df`.
- Truncated text answers (text call reached the output cap; kept as the answer): {'DIRECT': 0, 'SELF_REFLECT': 0, 'END_LITE_NATIVE': 0, 'FULL_END_NATIVE': 0, 'FULL_END_STRUCTURED': 0}.
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
 "END_LITE_NATIVE": {
  "adversarial_judge": null,
  "engine_config": {
   "candidate_generation": "native",
   "enable_branching": false,
   "meta_check_interval": 1000,
   "post_acceptance_cycles": 0,
   "protocol_repair_attempts": 1,
   "quality_evaluation": false
  },
  "judge_provider": null,
  "max_cycles": 2,
  "mode": "normal",
  "secondary_judge": null,
  "tool_verifier": null
 },
 "FULL_END_NATIVE": {
  "adversarial_judge": "defaults to the primary judge (same model)",
  "candidate_generation": "native",
  "engine_config": "EngineConfig() defaults (branching on, post_acceptance_cycles 0, judge_min_confidence 0.75) + protocol_repair_attempts=1",
  "judge_provider": "ModelJudgeProvider(same model transport)",
  "max_cycles": null,
  "mode": null,
  "secondary_judge": null,
  "tool_verifier": null
 },
 "FULL_END_STRUCTURED": {
  "adversarial_judge": "defaults to the primary judge (same model)",
  "candidate_generation": "structured",
  "engine_config": "EngineConfig() defaults (branching on, post_acceptance_cycles 0, judge_min_confidence 0.75) + protocol_repair_attempts=1",
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
| END_LITE_NATIVE | 4/10 | 0.5518 (0.4245) | 1 | 3655.2 | 6.0 | 0.0267 | 0 | 0 |
| FULL_END_NATIVE | 3/10 | 0.5018 (0.3942) | 2 | 16466.9 | 17.3 | 0.1204 | 0 | 0 |
| FULL_END_STRUCTURED | 3/10 | 0.5018 (0.3942) | 2 | 16864.8 | 17.3 | 0.1258 | 0 | 0 |

Format compliance (diagnostic; does not change any score — the required answer structure is a hard requirement of every task):

| Condition | required structure present | pass rate when present |
|---|---|---|
| DIRECT | 10/10 | 0.4 |
| SELF_REFLECT | 10/10 | 0.6 |
| END_LITE_NATIVE | 10/10 | 0.4 |
| FULL_END_NATIVE | 10/10 | 0.3 |
| FULL_END_STRUCTURED | 10/10 | 0.3 |

Score distribution per condition (mean / median / min / max / sd):

| Condition | mean | median | min | max | sd |
|---|---|---|---|---|---|
| DIRECT | 0.6317 | 0.5834 | 0.0 | 1.0 | 0.3616 |
| SELF_REFLECT | 0.7667 | 1.0 | 0.0 | 1.0 | 0.3639 |
| END_LITE_NATIVE | 0.5518 | 0.5278 | 0.0 | 1.0 | 0.4245 |
| FULL_END_NATIVE | 0.5018 | 0.5 | 0.0 | 1.0 | 0.3942 |
| FULL_END_STRUCTURED | 0.5018 | 0.5 | 0.0 | 1.0 | 0.3942 |

## 9. Results by task type

| Category | DIRECT | SELF_REFLECT | END_LITE_NATIVE | FULL_END_NATIVE | FULL_END_STRUCTURED |
|---|---|---|---|---|---|
| algorithm | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.2121 | 0.0 / 0.2121 | 0.0 / 0.2121 |
| constraint_satisfaction | 0.0 / 0.6667 | 0.0 / 0.6667 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| contradictory_evidence | 0.0 / 0.4 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| debugging | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| easy_transformation | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| failure_recovery | 0.0 / 0.25 | 0.0 / 0.25 | 0.0 / 0.25 | 0.0 / 0.25 | 0.0 / 0.25 |
| hidden_assumption | 0.0 / 0.0 | 1.0 / 1.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| missing_evidence | 0.0 / 0.5 | 0.0 / 0.75 | 1.0 / 1.0 | 0.0 / 0.5 | 0.0 / 0.5 |
| narrow_check_broad_claim | 0.0 / 0.5 | 1.0 / 1.0 | 0.0 / 0.5 | 0.0 / 0.5 | 0.0 / 0.5 |
| overthinking_trap | 1.0 / 1.0 | 1.0 / 1.0 | 0.0 / 0.5556 | 0.0 / 0.5556 | 0.0 / 0.5556 |

(pass rate / mean score)

| Task | DIRECT | SELF_REFLECT | END_LITE_NATIVE | FULL_END_NATIVE | FULL_END_STRUCTURED |
|---|---|---|---|---|---|
| BA-001 | 1/1 [1.0] | 0/1 [0.0] | 0/1 [0.0] | 0/1 [0.0] | 0/1 [0.0] |
| BA-002 | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] |
| BA-003 | 1/1 [1.0] | 1/1 [1.0] | 0/1 [0.2121] | 0/1 [0.2121] | 0/1 [0.2121] |
| BA-004 | 0/1 [0.6667] | 0/1 [0.6667] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] |
| BA-005 | 0/1 [0.0] | 1/1 [1.0] | 0/1 [0.0] | 0/1 [0.0] | 0/1 [0.0] |
| BA-007 | 0/1 [0.25] | 0/1 [0.25] | 0/1 [0.25] | 0/1 [0.25] | 0/1 [0.25] |
| BA-009 | 0/1 [0.5] | 0/1 [0.75] | 1/1 [1.0] | 0/1 [0.5] | 0/1 [0.5] |
| BA-010 | 0/1 [0.4] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] | 1/1 [1.0] |
| BA-011 | 0/1 [0.5] | 1/1 [1.0] | 0/1 [0.5] | 0/1 [0.5] | 0/1 [0.5] |
| BA-012 | 1/1 [1.0] | 1/1 [1.0] | 0/1 [0.5556] | 0/1 [0.5556] | 0/1 [0.5556] |

## 10. DIRECT vs END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_NATIVE_vs_DIRECT | 2/5/3 | -0.1299 | 101.71 |  | {'FULL_END_NATIVE': 2, 'DIRECT': 4} | {'FULL_END_NATIVE': 7, 'DIRECT': 0} |
| FULL_END_STRUCTURED_vs_DIRECT | 2/5/3 | -0.1299 | 104.168 |  | {'FULL_END_STRUCTURED': 2, 'DIRECT': 4} | {'FULL_END_STRUCTURED': 7, 'DIRECT': 0} |
| END_LITE_NATIVE_vs_DIRECT | 3/4/3 | -0.0799 | 22.577 |  | {'END_LITE_NATIVE': 1, 'DIRECT': 4} | {'END_LITE_NATIVE': 6, 'DIRECT': 0} |

## 11. SELF_REFLECT vs END

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_NATIVE_vs_SELF_REFLECT | 1/4/5 | -0.2649 | 26.863 |  | {'FULL_END_NATIVE': 2, 'SELF_REFLECT': 0} | {'FULL_END_NATIVE': 7, 'SELF_REFLECT': 0} |
| FULL_END_STRUCTURED_vs_SELF_REFLECT | 1/4/5 | -0.2649 | 27.512 |  | {'FULL_END_STRUCTURED': 2, 'SELF_REFLECT': 0} | {'FULL_END_STRUCTURED': 7, 'SELF_REFLECT': 0} |
| END_LITE_NATIVE_vs_SELF_REFLECT | 2/4/4 | -0.2149 | 5.963 |  | {'END_LITE_NATIVE': 1, 'SELF_REFLECT': 0} | {'END_LITE_NATIVE': 6, 'SELF_REFLECT': 0} |
| SELF_REFLECT_vs_DIRECT | 4/5/1 | 0.135 | 3.786 |  | {'SELF_REFLECT': 0, 'DIRECT': 4} | {'SELF_REFLECT': 0, 'DIRECT': 0} |

## 12. END variants: native vs structured C0, full vs lite

| Comparison | W/T/L | Score delta | Token × | Latency × | Unsupported claims | False accepts |
|---|---|---|---|---|---|---|
| FULL_END_NATIVE_vs_FULL_END_STRUCTURED | 0/10/0 | 0.0 | 0.976 | 0.957 | {'FULL_END_NATIVE': 2, 'FULL_END_STRUCTURED': 2} | {'FULL_END_NATIVE': 7, 'FULL_END_STRUCTURED': 7} |
| FULL_END_NATIVE_vs_END_LITE_NATIVE | 0/9/1 | -0.05 | 4.505 | 4.509 | {'FULL_END_NATIVE': 2, 'END_LITE_NATIVE': 1} | {'FULL_END_NATIVE': 7, 'END_LITE_NATIVE': 6} |

Wins/ties/losses use the meaningful-difference rule (|Δscore| ≥ 0.1 or pass/fail change).

## 13. END INTERNAL QUALITY VS EXTERNAL RESULT

**END_LITE_NATIVE** (internal basis: LLM verifier (no gate in END_LITE_NATIVE))

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 4 | 6 | 0 | 0 | 0 |

Every FALSE_ACCEPT:

| run | gate | label | basis | returned | score | failed checks |
|---|---|---|---|---|---|---|
| BA-001.T1.END_LITE_NATIVE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.0 | values_correct |
| BA-003.T1.END_LITE_NATIVE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.2121 | unit_tests |
| BA-005.T1.END_LITE_NATIVE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.0 | first, last, elapsed_minutes |
| BA-007.T1.END_LITE_NATIVE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.25 | prevention, w1_after_rejection, w2_retry_on_timeout |
| BA-011.T1.END_LITE_NATIVE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.5 | names_missing_evidence, no_guarantee_from_narrow_test |
| BA-012.T1.END_LITE_NATIVE | BLOCKED | INCONCLUSIVE | llm_verifier_passed=True | C1 | 0.5556 | unit_tests |

**FULL_END_NATIVE** (internal basis: QualityGate)

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 3 | 7 | 0 | 0 | 0 |

Every FALSE_ACCEPT:

| run | gate | label | basis | returned | score | failed checks |
|---|---|---|---|---|---|---|
| BA-001.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.0 | values_correct |
| BA-003.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.2121 | unit_tests |
| BA-005.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.0 | first, last, elapsed_minutes |
| BA-007.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.25 | prevention, w1_after_rejection, w2_retry_on_timeout |
| BA-009.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.5 | names_missing_evidence, certainty_below_established |
| BA-011.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.5 | names_missing_evidence, no_guarantee_from_narrow_test |
| BA-012.T1.FULL_END_NATIVE | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C1 | 0.5556 | unit_tests |

**FULL_END_STRUCTURED** (internal basis: QualityGate)

| TRUE_ACCEPT | FALSE_ACCEPT | TRUE_REJECT | FALSE_REJECT | INCONCLUSIVE |
|---|---|---|---|---|
| 3 | 7 | 0 | 0 | 0 |

Every FALSE_ACCEPT:

| run | gate | label | basis | returned | score | failed checks |
|---|---|---|---|---|---|---|
| BA-001.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.0 | values_correct |
| BA-003.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.2121 | unit_tests |
| BA-005.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.0 | first, last, elapsed_minutes |
| BA-007.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.25 | prevention, w1_after_rejection, w2_retry_on_timeout |
| BA-009.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.5 | names_missing_evidence, certainty_below_established |
| BA-011.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C0 | 0.5 | names_missing_evidence, no_guarantee_from_narrow_test |
| BA-012.T1.FULL_END_STRUCTURED | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONAL | quality_gate=ACCEPT_PROVISIONALLY | C1 | 0.5556 | unit_tests |

**How END runs ended** (termination reason, final gate, and Engine errors that stopped the loop; IDs normalized):

*END_LITE_NATIVE* — mean END cycles 1.0

| termination | runs |
|---|---|
| QUALITY_THRESHOLD_REACHED | 10 |

| final quality_gate | runs |
|---|---|
| BLOCKED | 10 |

No Engine errors.

*FULL_END_NATIVE* — mean END cycles 1.5

| termination | runs |
|---|---|
| ACCEPTED_PROVISIONALLY | 10 |

| final quality_gate | runs |
|---|---|
| ACCEPT_PROVISIONALLY | 10 |

No Engine errors.

*FULL_END_STRUCTURED* — mean END cycles 1.5

| termination | runs |
|---|---|
| ACCEPTED_PROVISIONALLY | 10 |

| final quality_gate | runs |
|---|---|
| ACCEPT_PROVISIONALLY | 10 |

No Engine errors.

## 13b. v0.3.5 PROTOCOL ROBUSTNESS AND GROUNDING

Repairs are END protocol repairs (trajectory protocol_events). Transport retries are the benchmark transport's own single retry of a malformed structured response, counted separately.

| measure | END_LITE_NATIVE | FULL_END_NATIVE | FULL_END_STRUCTURED |
|---|---|---|---|
| candidate_generation | native | native | structured |
| external_blocker | 0 | 0 | 0 |
| model_protocol_failure | 0 | 0 | 0 |
| repairs_attempted | 0 | 0 | 0 |
| repairs_succeeded | 0 | 0 | 0 |
| elements_discarded_events | 0 | 0 | 0 |
| repair_exhausted_events | 0 | 0 | 0 |
| runs_with_repair | 0 | 0 | 0 |
| runs_continued_after_repair | 0 | 0 | 0 |
| transport_retries | 0 | 0 | 0 |
| mean_end_cycles | 1.0 | 1.5 | 1.5 |
| pass_rate | 0.4 | 0.3 | 0.3 |
| c0_format_ok | 10/10 | 10/10 | 10/10 |
| final_format_ok | 10/10 | 10/10 | 10/10 |
| engine_check_internal_leakage_any | 0 | 0 | 0 |
| engine_check_consensus_any | 0 | 0 | 0 |

C0 external score by condition (generation mode in the table above):

| condition | C0 mean | median | min | max | n |
|---|---|---|---|---|---|
| END_LITE_NATIVE | 0.5629 | 0.5834 | 0.0 | 1.0 | 10 |
| FULL_END_NATIVE | 0.5129 | 0.5 | 0.0 | 1.0 | 10 |
| FULL_END_STRUCTURED | 0.5129 | 0.5 | 0.0 | 1.0 | 10 |

Judge findings classified non-decisive by v0.3.5 grounding (counts by status):

```json
{
 "END_LITE_NATIVE": {},
 "FULL_END_NATIVE": {},
 "FULL_END_STRUCTURED": {}
}
```

**Historical comparison with Benchmark Alpha (END v0.3.4, different session and seed; read only):**

| Alpha (v0.3.4) measure | value |
|---|---|
| FULL_END pass rate (Alpha v0.3.4) | 8/24 |
| END_LITE pass rate (Alpha v0.3.4) | 8/24 |
| FULL_END EXTERNAL_BLOCKER (Alpha) | 22/24 |
| END_LITE EXTERNAL_BLOCKER (Alpha) | 17/24 |
| FULL_END mean END cycles (Alpha) | 0.3333 |
| END C0 mean external score (Alpha, both END conditions) | 0.349 |
| DIRECT pass rate (Alpha) | 15/24 |
| SELF_REFLECT pass rate (Alpha) | 16/24 |

| Beta condition | pass | EXTERNAL_BLOCKER | MODEL_PROTOCOL_FAILURE | mean cycles | C0 mean |
|---|---|---|---|---|---|
| DIRECT | 4/10 |  |  |  |  |
| SELF_REFLECT | 6/10 |  |  |  |  |
| END_LITE_NATIVE | 4/10 | 0 | 0 | 1.0 | 0.5629 |
| FULL_END_NATIVE | 3/10 | 0 | 0 | 1.5 | 0.5129 |
| FULL_END_STRUCTURED | 3/10 | 0 | 0 | 1.5 | 0.5129 |

## 14. EPISTEMIC / HALLUCINATION RESULTS

Counts over Benchmark Alpha tasks only; not universal hallucination rates.

| Condition | unsupported_claim_count | unsupported_high_impact_claim_count | fabricated_reference_count | scope_overreach_count | contradiction_ignored_count | false_execution_claim_count | correct_uncertainty_count |
|---|---|---|---|---|---|---|---|
| DIRECT | 4 | 1 | 0 | 1 | 1 | 1 | 0 |
| SELF_REFLECT | 0 | 0 | 1 | 0 | 0 | 0 | 3 |
| END_LITE_NATIVE | 1 | 1 | 0 | 1 | 0 | 0 | 2 |
| FULL_END_NATIVE | 2 | 1 | 0 | 1 | 0 | 0 | 1 |
| FULL_END_STRUCTURED | 2 | 1 | 0 | 1 | 0 | 0 | 1 |

## 15. Candidate progression

| run | external score per candidate | peak | returned | best internal | missed peak | regressions |
|---|---|---|---|---|---|---|
| BA-001.T1.END_LITE_NATIVE | C0:0.0 C1:0.0 | C0 | C1 | C1 | False | 0 |
| BA-001.T1.FULL_END_NATIVE | C0:0.0 C1:0.0 | C0 | C0 | C0 | False | 0 |
| BA-001.T1.FULL_END_STRUCTURED | C0:0.0 C1:0.0 | C0 | C0 | C0 | False | 0 |
| BA-002.T1.END_LITE_NATIVE | C0:1.0 C1:1.0 | C0 | C1 | C1 | False | 0 |
| BA-002.T1.FULL_END_NATIVE | C0:1.0 C1:0.2857 | C0 | C0 | C0 | False | 1 |
| BA-002.T1.FULL_END_STRUCTURED | C0:1.0 C1:0.2857 | C0 | C0 | C0 | False | 1 |
| BA-003.T1.END_LITE_NATIVE | C0:0.2121 C1:0.2121 | C0 | C1 | C1 | False | 0 |
| BA-003.T1.FULL_END_NATIVE | C0:0.2121 C1:0.2121 | C0 | C0 | C0 | False | 0 |
| BA-003.T1.FULL_END_STRUCTURED | C0:0.2121 C1:0.2121 | C0 | C0 | C0 | False | 0 |
| BA-004.T1.END_LITE_NATIVE | C0:0.6667 C1:1.0 | C1 | C1 | C1 | False | 0 |
| BA-004.T1.FULL_END_NATIVE | C0:0.6667 C1:1.0 C2:1.0 | C1 | C1 | C1 | False | 0 |
| BA-004.T1.FULL_END_STRUCTURED | C0:0.6667 C1:1.0 C2:1.0 | C1 | C1 | C1 | False | 0 |
| BA-005.T1.END_LITE_NATIVE | C0:0.0 C1:0.0 | C0 | C1 | C1 | False | 0 |
| BA-005.T1.FULL_END_NATIVE | C0:0.0 C1:0.0 | C0 | C0 | C0 | False | 0 |
| BA-005.T1.FULL_END_STRUCTURED | C0:0.0 C1:0.0 | C0 | C0 | C0 | False | 0 |
| BA-007.T1.END_LITE_NATIVE | C0:0.25 C1:0.25 | C0 | C1 | C1 | False | 0 |
| BA-007.T1.FULL_END_NATIVE | C0:0.25 C1:1.0 C2:0.25 | C1 | C0 | C0 | True | 0 |
| BA-007.T1.FULL_END_STRUCTURED | C0:0.25 C1:1.0 C2:0.25 | C1 | C0 | C0 | True | 0 |
| BA-009.T1.END_LITE_NATIVE | C0:1.0 C1:1.0 | C0 | C1 | C1 | False | 0 |
| BA-009.T1.FULL_END_NATIVE | C0:0.5 C1:0.5 C2:0.5 | C0 | C0 | C0 | False | 0 |
| BA-009.T1.FULL_END_STRUCTURED | C0:0.5 C1:0.5 C2:0.5 | C0 | C0 | C0 | False | 0 |
| BA-010.T1.END_LITE_NATIVE | C0:1.0 C1:1.0 | C0 | C1 | C1 | False | 0 |
| BA-010.T1.FULL_END_NATIVE | C0:1.0 C1:1.0 C2:1.0 | C0 | C0 | C0 | False | 0 |
| BA-010.T1.FULL_END_STRUCTURED | C0:1.0 C1:1.0 C2:1.0 | C0 | C0 | C0 | False | 0 |
| BA-011.T1.END_LITE_NATIVE | C0:0.5 C1:0.5 | C0 | C1 | C1 | False | 0 |
| BA-011.T1.FULL_END_NATIVE | C0:0.5 C1:0.5 C2:0.5 | C0 | C0 | C0 | False | 0 |
| BA-011.T1.FULL_END_STRUCTURED | C0:0.5 C1:0.5 C2:0.5 | C0 | C0 | C0 | False | 0 |
| BA-012.T1.END_LITE_NATIVE | C0:1.0 C1:0.5556 | C0 | C1 | C1 | True | 1 |
| BA-012.T1.FULL_END_NATIVE | C0:1.0 C1:0.5556 | C0 | C1 | C1 | True | 1 |
| BA-012.T1.FULL_END_STRUCTURED | C0:1.0 C1:0.5556 | C0 | C1 | C1 | True | 1 |

## 16. Overthinking cases

| run | signals | tokens | END cycles |
|---|---|---|---|
| BA-001.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 3039 | 1 |
| BA-001.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 10882 | 1 |
| BA-001.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 11187 | 1 |
| BA-002.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 3714 | 1 |
| BA-002.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 12350 | 1 |
| BA-002.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 12666 | 1 |
| BA-003.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 3328 | 1 |
| BA-003.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 11508 | 1 |
| BA-003.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 11813 | 1 |
| BA-005.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 3393 | 1 |
| BA-005.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 11663 | 1 |
| BA-005.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 11982 | 1 |
| BA-007.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 4306 | 1 |
| BA-007.T1.FULL_END_NATIVE | B_cycles_without_external_benefit, C_correct_answer_lost | 22337 | 2 |
| BA-007.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit, C_correct_answer_lost | 22824 | 2 |
| BA-009.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 4097 | 1 |
| BA-009.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 21965 | 2 |
| BA-009.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 22454 | 2 |
| BA-010.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 3977 | 1 |
| BA-010.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 21732 | 2 |
| BA-010.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 22228 | 2 |
| BA-011.T1.END_LITE_NATIVE | B_cycles_without_external_benefit | 3953 | 1 |
| BA-011.T1.FULL_END_NATIVE | B_cycles_without_external_benefit | 21614 | 2 |
| BA-011.T1.FULL_END_STRUCTURED | B_cycles_without_external_benefit | 22100 | 2 |
| BA-012.T1.END_LITE_NATIVE | A_earlier_candidate_better, B_cycles_without_external_benefit, C_correct_answer_lost | 3136 | 1 |
| BA-012.T1.FULL_END_NATIVE | A_earlier_candidate_better, B_cycles_without_external_benefit, C_correct_answer_lost | 11115 | 1 |
| BA-012.T1.FULL_END_STRUCTURED | A_earlier_candidate_better, B_cycles_without_external_benefit, C_correct_answer_lost | 11422 | 1 |

## 17. Rollback analysis

| run | rejected | returned | rejected score | returned score | label |
|---|---|---|---|---|---|
| BA-002.T1.FULL_END_NATIVE | C1 | C0 | 0.2857 | 1.0 | ROLLBACK_SAVED_RUN |
| BA-002.T1.FULL_END_STRUCTURED | C1 | C0 | 0.2857 | 1.0 | ROLLBACK_SAVED_RUN |
| BA-007.T1.FULL_END_NATIVE | C1 | C0 | 1.0 | 0.25 | ROLLBACK_HURT_RUN |
| BA-007.T1.FULL_END_STRUCTURED | C1 | C0 | 1.0 | 0.25 | ROLLBACK_HURT_RUN |

Quality-delta validation (END's comparator vs external delta):

```json
{
 "FULL_END_NATIVE": {
  "MATCH": 13,
  "DELTA_MISMATCH": 2
 },
 "FULL_END_STRUCTURED": {
  "MATCH": 13,
  "DELTA_MISMATCH": 2
 }
}
```

## 18. Operator observations

Exploratory only; sample sizes are too small for causal claims.

**END_LITE_NATIVE**

| operator | uses | positive | negative | neutral | no revision | mean cycle tokens |
|---|---|---|---|---|---|---|
| CONSTRAINT | 10 | 1 | 1 | 8 | 0 | 1978.7 |

**FULL_END_NATIVE**

| operator | uses | positive | negative | neutral | no revision | mean cycle tokens |
|---|---|---|---|---|---|---|
| CONSTRAINT | 5 | 0 | 2 | 3 | 0 | 1806.0 |
| EVIDENCE | 5 | 2 | 0 | 3 | 0 | 2139.2 |
| SECOND_ORDER_EFFECT | 5 | 0 | 0 | 5 | 0 | 2146.6 |

**FULL_END_STRUCTURED**

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
| END_LITE_NATIVE | 0.5518 | -0.0799 | 6.0 | 6.0 | 3655.2 | 22.577 | 0.0267 |  |
| FULL_END_NATIVE | 0.5018 | -0.1299 | 17.3 | 17.3 | 16466.9 | 101.71 | 0.1204 |  |
| FULL_END_STRUCTURED | 0.5018 | -0.1299 | 17.3 | 17.3 | 16864.8 | 104.168 | 0.1258 |  |

**A. Unconstrained:** the table above (each condition's intended behaviour).

**B. Roughly matched budget:** no budget-matched baseline condition was executed, so no matched-budget result exists. The multipliers above show how far apart the budgets are; the only near-matched view available is END's own first candidate C0 (one generation, like DIRECT) against DIRECT in the same task-trial:

END C0 vs DIRECT pairs: 30; mean C0 score 0.5295, mean DIRECT score 0.6317.

## 20. Failure archive

`failures/<TAG>/<run_id>/` holds byte-identical copies of the trial and evaluation records plus a trajectory reference with its SHA-256. No cause is inferred.

| tag | runs |
|---|---|
| CORRECT_ABSTENTION | 7 |
| DIRECT_BEAT_END | 9 |
| END_HELPED | 3 |
| END_HURT | 3 |
| FABRICATED_EVIDENCE | 1 |
| FALSE_ACCEPT | 20 |
| IGNORED_CONTRADICTION | 1 |
| OVERTHINKING | 27 |
| ROLLBACK_HURT_RUN | 2 |
| ROLLBACK_SAVED_RUN | 2 |
| SCOPE_OVERREACH | 4 |
| SELF_REFLECT_BEAT_END | 14 |
| UNSUPPORTED_HIGH_IMPACT_CLAIM | 4 |

## 21. Limitations

- Benchmark Beta is small (12 tasks × 2 trials); far too small for statistical significance.
- Results are specific to this model, these settings and this 12-task set.
- Hallucination measurements cover only the designed failure classes, via task-specific patterns; they can miss or mis-flag wording (see review flags).
- Model judges can be wrong; here END's internal judges are the same model as the generator.
- Public benchmark contamination may exist for classic problems (e.g. meeting rooms, palindromes).
- FULL_END conditions have no tool verifier and use a same-model judge, so they cannot reach ACCEPT_VERIFIED by design.
- The transport retries a malformed structured response once (as in Alpha); after that, the failure is raised as a model-protocol error, so END v0.3.5 classifies it as MODEL_PROTOCOL_* and may make its own repair call.
- Alpha numbers are historical (v0.3.4, earlier session, different seed); Alpha and Beta baselines are separate samples.

## 22. What Benchmark Beta does NOT prove

- A positive result does not prove general reasoning improvement.
- A negative result does not prove END can never work.
- No result here generalizes beyond this model, task set and configuration.
