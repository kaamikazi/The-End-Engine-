# Operator activation, information and quality value

Sources: all original selections/questions/operator_outcomes/critique steps identified in CYCLE_AUDIT, their wire requests in CALL_AUDIT, and current `cognition/policy.py`, `cognition/session.py:78`, `operators/base.py:31`. Each activation is a concrete critique call, not a candidate rewrite. The current utility formula multiplies relevance × predicted internal gain × issue value × novelty × task importance, minus repetition/cost plus meta adjustment. The information proxy counts new finding IDs, knowledge mutations and viable branches. Its HIGH label cannot certify new evidence or better answers.

The table's call/token totals include the **entire associated cycle**, including generation, judgments, verification and any branch work. They cannot be attributed causally to the operator. Direct operator inference is the critique purpose: 50 physical calls (44 regular+6 repair), 166,529 tokens. Planning repairs are separate. There is no randomized operator comparison.

| Operator / family | Activations | Internal gain levels | Direct critique calls / tokens | Associated cycle calls | Associated tokens | Associated provider seconds | Encoded gains / losses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALTERNATIVE / search | 2 | {"HIGH":2} | 2 / 4,320 | 26 | 46,270 | 639.581 | 0 / 0 |
| ASSUMPTION / epistemic | 4 | {"LOW":3,"ZERO":1} | 5 / 15,976 | 35 | 76,541 | 1042.393 | 0 / 0 |
| CONSTRAINT / constraint | 4 | {"LOW":3,"MEDIUM":1} | 4 / 8,969 | 34 | 57,762 | 909.778 | 0 / 0 |
| EVIDENCE / epistemic | 15 | {"MEDIUM":3,"LOW":9,"ZERO":2,"HIGH":1} | 17 / 61,280 | 127 | 318,042 | 3378.575 | 0 / 0 |
| HOW / foundational | 1 | {"LOW":1} | 1 / 2,520 | 9 | 15,332 | 364.050 | 0 / 0 |
| SECOND_ORDER_EFFECT / systemic | 4 | {"LOW":4} | 4 / 12,170 | 34 | 78,948 | 764.498 | 0 / 0 |
| SIMPLIFY / optimization | 1 | {"LOW":1} | 1 / 2,469 | 8 | 11,985 | 118.484 | 0 / 0 |
| VERIFY / epistemic | 13 | {"LOW":9,"ZERO":1,"MEDIUM":1,"HIGH":2} | 16 / 58,825 | 113 | 303,113 | 3909.439 | 0 / 1 |

The gain levels above include final branch enrichment: both ALTERNATIVE outcomes change LOW→HIGH because two branches per run are labelled viable/merged. Neither cycle acquires executed evidence or an external score gain. CYCLE_AUDIT preserves pre-branch and final information_gain separately; treating only the initial critique outcome as final would undercount this internal activity.

## EVIDENCE — epistemic

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | Unverified claim/evidence-gap topics; severity/relevance gain beats repetition penalties |
| 2 Intended issue? | Temperature rounding, chunk requirements, BA-009 causal support, or generic evidence |
| 3 Actual output? | Supported-claim statements, original/fixed-code confusion, genuine absent-metric concern; old native BA-009 also filler target |
| 4 New actionable weakness? | Some actionable status/evidence gaps in BA-009, mixed with redundant/invalid allegations |
| 5 New evidence? | Candidate text or supplied task facts only; no new measurements |
| 6 Candidate altered? | Often same answer; new BA-009 structured adds unsupported confirmation |
| 7 Useful revision? | No encoded gain; valid missing-evidence observation does not yield valid repair |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Same causal gap is revisited by VERIFY/SECOND_ORDER; 15 selections are not 15 discoveries |
| 10 Cost? | 15 activations; 127 associated cycle calls / 318,042 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-001.T1.FULL_END_NATIVE #1 ([trajectory](../v035_core_regression_pilot/trajectories/9cea722d-0dbe-43b8-9d30-24d6eac0befa.jsonl), steps 23–termination); 0.3.5 BA-001.T1.FULL_END_STRUCTURED #2 ([trajectory](../v035_core_regression_pilot/trajectories/02835fa6-600d-4e78-b878-3d5f65e4c344.jsonl), steps 64–103); 0.3.5 BA-002.T1.FULL_END_NATIVE #1 ([trajectory](../v035_core_regression_pilot/trajectories/6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl), steps 39–84); 0.3.5 BA-002.T1.FULL_END_NATIVE #3 ([trajectory](../v035_core_regression_pilot/trajectories/6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl), steps 129–termination); 0.3.5 BA-002.T1.FULL_END_STRUCTURED #1 ([trajectory](../v035_core_regression_pilot/trajectories/42be76c1-49bc-4a96-bba0-a3d55d5e7af3.jsonl), steps 29–73); 0.3.5 BA-002.T1.FULL_END_STRUCTURED #3 ([trajectory](../v035_core_regression_pilot/trajectories/42be76c1-49bc-4a96-bba0-a3d55d5e7af3.jsonl), steps 117–termination); 0.3.5 BA-008.T1.FULL_END_STRUCTURED #3 ([trajectory](../v035_core_regression_pilot/trajectories/ca37375d-c022-4ffa-a2b5-5d641b59cf35.jsonl), steps 147–termination); 0.3.5 BA-009.T1.FULL_END_NATIVE #1 ([trajectory](../v035_core_regression_pilot/trajectories/b3c8b8d8-2388-40c0-9e2c-c75a679ef56e.jsonl), steps 27–67); 0.3.5 BA-009.T1.FULL_END_STRUCTURED #1 ([trajectory](../v035_core_regression_pilot/trajectories/67a5c2d9-fcf4-4c27-81a1-67a9076ba93f.jsonl), steps 24–64); 0.3.5.1 BA-001.T1.FULL_END_NATIVE #1 ([trajectory](../v0351_core_regression_pilot/trajectories/3273ea96-7d7c-41fc-8b2c-aea0ec39f73b.jsonl), steps 25–termination); 0.3.5.1 BA-002.T1.FULL_END_NATIVE #1 ([trajectory](../v0351_core_regression_pilot/trajectories/41b7f53a-d785-4d23-8549-5c7a5927f1a4.jsonl), steps 50–99); 0.3.5.1 BA-002.T1.FULL_END_STRUCTURED #1 ([trajectory](../v0351_core_regression_pilot/trajectories/5969e198-03ed-4a17-b05b-9fefe5ee4dc4.jsonl), steps 29–72); 0.3.5.1 BA-002.T1.FULL_END_STRUCTURED #2 ([trajectory](../v0351_core_regression_pilot/trajectories/5969e198-03ed-4a17-b05b-9fefe5ee4dc4.jsonl), steps 72–115); 0.3.5.1 BA-009.T1.FULL_END_NATIVE #1 ([trajectory](../v0351_core_regression_pilot/trajectories/49544d22-83e0-49a8-9179-c3765116e44b.jsonl), steps 33–75); 0.3.5.1 BA-009.T1.FULL_END_STRUCTURED #1 ([trajectory](../v0351_core_regression_pilot/trajectories/2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl), steps 24–66).

## VERIFY — epistemic

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | Untested assumption or unverified claim with high risk; exact utility factors stored per selection |
| 2 Intended issue? | Chunk code requirement, stable-sort premise/goal, BA-009 certainty |
| 3 Actual output? | Same-model checks/critique and repeated uncertainty assertions |
| 4 New actionable weakness? | Legitimate request to check a claim; most proposed failure assertions not demonstrated |
| 5 New evidence? | No executed tests or external retrieval; proposed stability test remains illustrative |
| 6 Candidate altered? | BA-008 native first child loses explanation; new native BA-009 second child lowers certainty and invents ID |
| 7 Useful revision? | 0 encoded gains, 1 encoded loss; narrow safety qualification also occurs |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Repeats EVIDENCE topics and task-induced assumptions; not independent confirmation |
| 10 Cost? | 13 activations; 113 associated cycle calls / 303,113 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-002.T1.FULL_END_NATIVE #2 ([trajectory](../v035_core_regression_pilot/trajectories/6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl), steps 84–129); 0.3.5 BA-002.T1.FULL_END_STRUCTURED #2 ([trajectory](../v035_core_regression_pilot/trajectories/42be76c1-49bc-4a96-bba0-a3d55d5e7af3.jsonl), steps 73–117); 0.3.5 BA-008.T1.FULL_END_NATIVE #1 ([trajectory](../v035_core_regression_pilot/trajectories/91b86589-796e-4570-965b-bd025d7c7b87.jsonl), steps 32–69); 0.3.5 BA-008.T1.FULL_END_STRUCTURED #1 ([trajectory](../v035_core_regression_pilot/trajectories/ca37375d-c022-4ffa-a2b5-5d641b59cf35.jsonl), steps 42–92); 0.3.5 BA-009.T1.FULL_END_NATIVE #2 ([trajectory](../v035_core_regression_pilot/trajectories/b3c8b8d8-2388-40c0-9e2c-c75a679ef56e.jsonl), steps 67–104); 0.3.5.1 BA-002.T1.FULL_END_NATIVE #2 ([trajectory](../v0351_core_regression_pilot/trajectories/41b7f53a-d785-4d23-8549-5c7a5927f1a4.jsonl), steps 99–142); 0.3.5.1 BA-002.T1.FULL_END_NATIVE #3 ([trajectory](../v0351_core_regression_pilot/trajectories/41b7f53a-d785-4d23-8549-5c7a5927f1a4.jsonl), steps 142–termination); 0.3.5.1 BA-002.T1.FULL_END_STRUCTURED #3 ([trajectory](../v0351_core_regression_pilot/trajectories/5969e198-03ed-4a17-b05b-9fefe5ee4dc4.jsonl), steps 115–termination); 0.3.5.1 BA-008.T1.FULL_END_NATIVE #1 ([trajectory](../v0351_core_regression_pilot/trajectories/653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl), steps 34–79); 0.3.5.1 BA-008.T1.FULL_END_NATIVE #3 ([trajectory](../v0351_core_regression_pilot/trajectories/653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl), steps 120–termination); 0.3.5.1 BA-008.T1.FULL_END_STRUCTURED #1 ([trajectory](../v0351_core_regression_pilot/trajectories/79ec91f1-7b59-4a33-8a53-4613af251c8e.jsonl), steps 37–78); 0.3.5.1 BA-008.T1.FULL_END_STRUCTURED #2 ([trajectory](../v0351_core_regression_pilot/trajectories/79ec91f1-7b59-4a33-8a53-4613af251c8e.jsonl), steps 78–117); 0.3.5.1 BA-009.T1.FULL_END_NATIVE #2 ([trajectory](../v0351_core_regression_pilot/trajectories/49544d22-83e0-49a8-9179-c3765116e44b.jsonl), steps 75–123).

## ASSUMPTION — epistemic

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | High-risk extracted/model assumption and repetition/coverage policy |
| 2 Intended issue? | Stable-sort goal versus task factual premise |
| 3 Actual output? | Premise-conflict concerns and clarification requests |
| 4 New actionable weakness? | No demonstrated sorting-code failure; normative goal mistaken for untested factual defect |
| 5 New evidence? | No independent evidence |
| 6 Candidate altered? | Code-only native answer persists; structured stability test/text unchanged |
| 7 Useful revision? | No encoded gain; no new verified support |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Reuses prior VERIFY premise concern |
| 10 Cost? | 4 activations; 35 associated cycle calls / 76,541 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-008.T1.FULL_END_NATIVE #2 ([trajectory](../v035_core_regression_pilot/trajectories/91b86589-796e-4570-965b-bd025d7c7b87.jsonl), steps 69–101); 0.3.5 BA-008.T1.FULL_END_STRUCTURED #2 ([trajectory](../v035_core_regression_pilot/trajectories/ca37375d-c022-4ffa-a2b5-5d641b59cf35.jsonl), steps 92–147); 0.3.5.1 BA-008.T1.FULL_END_NATIVE #2 ([trajectory](../v0351_core_regression_pilot/trajectories/653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl), steps 79–120); 0.3.5.1 BA-008.T1.FULL_END_STRUCTURED #3 ([trajectory](../v0351_core_regression_pilot/trajectories/79ec91f1-7b59-4a33-8a53-4613af251c8e.jsonl), steps 117–termination).

## CONSTRAINT — constraint

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | Uncovered completeness/correctness or high-severity registered concern |
| 2 Intended issue? | Temperature ordering/completeness; old native sort explanation |
| 3 Actual output? | Incorrect ordering criticism or repeated premise conflict |
| 4 New actionable weakness? | True old numeric defect exists but this critique misdiagnoses it; new temperatures already correct |
| 5 New evidence? | Frozen external checks exist after runtime, not available to operator |
| 6 Candidate altered? | Most identical; old temperature C2 malformed arose in different EVIDENCE cycle |
| 7 Useful revision? | No encoded gain; does not isolate/fix remaining true error |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Same purported ordering/assignment errors recur |
| 10 Cost? | 4 activations; 34 associated cycle calls / 57,762 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-001.T1.FULL_END_STRUCTURED #1 ([trajectory](../v035_core_regression_pilot/trajectories/02835fa6-600d-4e78-b878-3d5f65e4c344.jsonl), steps 25–64); 0.3.5 BA-008.T1.FULL_END_NATIVE #3 ([trajectory](../v035_core_regression_pilot/trajectories/91b86589-796e-4570-965b-bd025d7c7b87.jsonl), steps 101–termination); 0.3.5.1 BA-001.T1.FULL_END_STRUCTURED #1 ([trajectory](../v0351_core_regression_pilot/trajectories/efa824fb-bbda-4138-9243-414e772ef1fb.jsonl), steps 25–66); 0.3.5.1 BA-001.T1.FULL_END_STRUCTURED #3 ([trajectory](../v0351_core_regression_pilot/trajectories/efa824fb-bbda-4138-9243-414e772ef1fb.jsonl), steps 109–termination).

## HOW — foundational

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | New structured BA-001 high completeness weakness feeds mechanism selection |
| 2 Intended issue? | Repair allegedly missing/misassigned conversions |
| 3 Actual output? | Mechanism-focused misassignment allegation |
| 4 New actionable weakness? | Contradicted within saved numeric/position checks |
| 5 New evidence? | No new evidence |
| 6 Candidate altered? | Formatting/wording only; values already correct |
| 7 Useful revision? | No encoded gain |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Reformulates prior CONSTRAINT completeness concern |
| 10 Cost? | 1 activations; 9 associated cycle calls / 15,332 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5.1 BA-001.T1.FULL_END_STRUCTURED #2 ([trajectory](../v0351_core_regression_pilot/trajectories/efa824fb-bbda-4138-9243-414e772ef1fb.jsonl), steps 66–109).

## SIMPLIFY — optimization

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | Old structured BA-001 generic clarity dimension remains eligible |
| 2 Intended issue? | Ordering/validation presentation |
| 3 Actual output? | Restated ordering error and output-order request |
| 4 New actionable weakness? | Does not identify real wrong 74.7 result |
| 5 New evidence? | No new evidence |
| 6 Candidate altered? | Reproduces original wrong numeric array; rollback restores same wrong C0 |
| 7 Useful revision? | No encoded gain |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Same ordering criticism from CONSTRAINT/EVIDENCE |
| 10 Cost? | 1 activations; 8 associated cycle calls / 11,985 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-001.T1.FULL_END_STRUCTURED #3 ([trajectory](../v035_core_regression_pilot/trajectories/02835fa6-600d-4e78-b878-3d5f65e4c344.jsonl), steps 103–termination).

## SECOND_ORDER_EFFECT — systemic

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | Deep missing-evidence task; generic failure-mode coverage becomes eligible |
| 2 Intended issue? | BA-009 causal limitations and missing observations |
| 3 Actual output? | Repeated metric-gap critique and causal-effects concerns |
| 4 New actionable weakness? | Missing evidence/status can be real; metric insertion is not a feasible acquisition action |
| 5 New evidence? | No new observations |
| 6 Candidate altered? | Old answer unchanged; new native repeats invented ID; new structured paraphrases unsafe conclusion |
| 7 Useful revision? | No encoded gain; no independent causal support |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Revisits EVIDENCE/VERIFY gap rather than resolving it |
| 10 Cost? | 4 activations; 34 associated cycle calls / 78,948 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-009.T1.FULL_END_NATIVE #3 ([trajectory](../v035_core_regression_pilot/trajectories/b3c8b8d8-2388-40c0-9e2c-c75a679ef56e.jsonl), steps 104–termination); 0.3.5 BA-009.T1.FULL_END_STRUCTURED #2 ([trajectory](../v035_core_regression_pilot/trajectories/67a5c2d9-fcf4-4c27-81a1-67a9076ba93f.jsonl), steps 64–104); 0.3.5.1 BA-009.T1.FULL_END_NATIVE #3 ([trajectory](../v0351_core_regression_pilot/trajectories/49544d22-83e0-49a8-9179-c3765116e44b.jsonl), steps 123–termination); 0.3.5.1 BA-009.T1.FULL_END_STRUCTURED #2 ([trajectory](../v0351_core_regression_pilot/trajectories/2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl), steps 66–106).

## ALTERNATIVE — search

| Question | Observed answer |
| --- | --- |
| 1 Why selected? | Uncovered alternatives/low-value history and bounded branch eligibility |
| 2 Intended issue? | BA-009 competing causal explanations |
| 3 Actual output? | Alternative hypotheses, branch judgments and synthesis; metric-gap critique persists |
| 4 New actionable weakness? | New possibilities exist; none independently discriminated or shown to correct output |
| 5 New evidence? | 8 branch-associated calls across 2 search cycles; 0 executed evidence |
| 6 Candidate altered? | Old answer unchanged; new structured adds defensive causal prose, not JSON |
| 7 Useful revision? | No encoded gain; diversity is not verified causal information |
| 8 Later improvement? | No later encoded improvement in any associated run; unmeasured semantic effects remain unknown |
| 9 Repetition? | Repeats absent-metric concern while generating alternate stories |
| 10 Cost? | 2 activations; 26 associated cycle calls / 46,270 tokens; exact critique versus other purposes in CALL_AUDIT |

Source cycles: 0.3.5 BA-009.T1.FULL_END_STRUCTURED #3 ([trajectory](../v035_core_regression_pilot/trajectories/67a5c2d9-fcf4-4c27-81a1-67a9076ba93f.jsonl), steps 104–termination); 0.3.5.1 BA-009.T1.FULL_END_STRUCTURED #3 ([trajectory](../v0351_core_regression_pilot/trajectories/2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl), steps 106–termination).

## Conservative issue equivalence and authority

57 ingested critique-finding occurrences, **not all discovered issues**: judge feedback, extracted claims/assumptions and selected generic dimension topics are separate populations. Stable issue IDs are scoped by version/run, never joined across runs. Exact normalized text is REPEATED; changed text with the same polarity heuristic and token Jaccard ≥.72 is a tentative REFORMULATED proposal; reused IDs with incompatible/different wording are UNKNOWN. New unmatched text is DISTINCT_LEXICAL_PROPOSAL. Negation/numbers/operators are retained in normalization; this still cannot establish semantic equivalence. The same ID can change meaning; a new ID can repeat an old issue. Run-local occurrence history is used even across state restoration, with uncertainty explicit.

| Identity class | Occurrences / 57 | Interpretation |
| --- | --- | --- |
| New lexical proposals | 22 (38.6%) | Not 22 genuine actionable discoveries |
| Exact normalized repeats | 28 (49.1%) | Repeated proposition text; may be valid unresolved concern |
| Tentative reformulation | 1 (1.8%) | Lexical proposal, not semantic proof |
| Unknown | 6 (10.5%) | ID reuse/changed proposition cannot be safely merged |

**Genuinely distinct validated issue proportion cannot be determined.** All 57 occurrences originate in MODEL_CRITIQUE; none has a newly acquired executed-evidence receipt in these runs. That is an authority observation, not proof that all 57 statements are false or ungrounded: BA-009's stipulated missing metrics and literal format/status gaps can be grounded without world evidence; several 'findings' merely state a claim is supported. ISSUE_EQUIVALENCE includes the contextual grounding review separately from identity. Do not add ungrounded as a mutually exclusive lexical bucket or interpret its absence as validation.

The 44 selected topics separately comprise 22 plausible-but-unverified, 12 generic/unknown, six unsupported, two contradicted within frozen coverage and two deterministically grounded status/evidence-gap targets; externally demonstrated selected defects: zero under this conservative topic definition. Target novelty: 34 first-selected ID/text combinations, nine repeated same-ID/text, one reworded same-ID. First selection is not first issue creation or new knowledge. Legitimate sorting requirements are plausible topics; their premise-dependent critique is assessed separately. Unsupported ≠ false; unknown ≠ contradicted.

Severity inflation is visible in new structured BA-001: correct output receives high completeness/misassignment concerns, and in BA-008: premise-induced high assumptions protect continuation. Resolution failure includes BA-009 stale 'established' concern after enum qualification, plus original gaps retained after no-op revisions. Positive low-severity 'supported' findings can inflate activity without a defect. Current v0.3.5.2 separates advisory from decisive authority, but utility/gain still warrant a controlled test. No operator earns a general causal usefulness ranking from these 44 correlated cycles.

## Occurrence-level grounding, separate from identity

| Local manual scope label | Occurrences /57 | Meaning |
| --- | --- | --- |
| GROUNDED_SCOPED_OBSERVATION | 16 (28.1%) | 16 observations include10 already-satisfied positive requirements/behavior and6 repeated BA-009 absence/status gaps; not16 novel defects or world-truth proofs |
| CONTRADICTED_WITHIN_SCOPE | 11 (19.3%) | Ordering/completeness/absent-guard/original-loop allegations conflict with saved code/positions and finite rubric coverage |
| UNSUPPORTED_CANDIDATE_DEFECT | 11 (19.3%) | 11 ungrounded defect inferences from task factual conflicts or normative goals; unsupported does not mean false |
| PLAUSIBLE_BUT_UNVERIFIED | 15 (26.3%) | Scope/attribution/type/causal-support inference merits investigation; no defect conclusion |
| UNKNOWN | 4 (7.0%) | Falsifiable-check sufficiency or stale concern/current-answer attribution cannot be safely adjudicated |

These task-specific research annotations are in ISSUE_EQUIVALENCE. They are orthogonal to lexical novelty: the11 unsupported-defect occurrences (19.3%) may also repeat earlier wording. Four unknown (7.0%) remain separate from15 plausible/unverified (26.3%). The16 scoped observations cannot establish the genuinely distinct actionable discovery fraction; many restate satisfied requirements or a gap already noticed in pre-cycle judgment. No perfect semantic or causal classification is claimed.
