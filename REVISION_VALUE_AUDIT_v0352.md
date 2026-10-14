# Revision-value audit for v0.3.5.2

Read-only investigation dated 2026-10-09. Frozen v0.3.5.1 trajectories and external evaluations are the evidence; nothing is rescored or relabelled in the historical directories.
The server drifted from Ollama 0.35.1 to 0.40.0 at an unknown time. Four tasks/one trial, same-model judging, frozen rubric gaps and raw-region ambiguity limit causal/general conclusions.

## Finding

The dominant observed chain is additional model opinions → more issues/plans/judgments → similar or worse answers. Zero of eight final scores improve, seven are neutral and one regresses. No executed external evidence is acquired in any run. Native BA-009 does make a useful status downgrade, but introduces a false citation; the score stays unchanged.
These are structural revision/assessment problems that the integrity patch cannot make a generator or comparison model solve. Operator selection follows the supplied concern state; these traces do not isolate intrinsic ranking failure from poisoned issue inputs. More cycles are not presumed beneficial.

## Per-run frozen costs and outcomes

| Run | C0 → final | Revisions | Calls | Tokens | Judge / critique / verification / repair calls | C0 preservation |
|---|---|---:|---:|---:|---|---|
| BA-001.T1.FULL_END_NATIVE | 1.0 → 1.0 | 1 | 13 | 43,453 | 7 / 1 / 2 / 0 | equal or better by score |
| BA-001.T1.FULL_END_STRUCTURED | 1.0 → 1.0 | 3 | 31 | 51,154 | 17 / 3 / 4 / 0 | equal or better by score |
| BA-002.T1.FULL_END_NATIVE | 1.0 → 1.0 | 3 | 32 | 91,718 | 16 / 4 / 4 / 2 | equal or better by score |
| BA-002.T1.FULL_END_STRUCTURED | 1.0 → 1.0 | 3 | 31 | 54,482 | 17 / 3 / 4 / 0 | equal or better by score |
| BA-008.T1.FULL_END_NATIVE | 1.0 → 0.5 | 3 | 31 | 94,332 | 16 / 4 / 4 / 1 | equal or better by score |
| BA-008.T1.FULL_END_STRUCTURED | 1.0 → 1.0 | 3 | 31 | 64,100 | 16 / 4 / 4 / 1 | equal or better by score |
| BA-009.T1.FULL_END_NATIVE | 0.5 → 0.5 | 3 | 30 | 114,196 | 16 / 3 / 4 / 0 | equal or better by score |
| BA-009.T1.FULL_END_STRUCTURED | 0.0 → 0.0 | 3 | 34 | 60,703 | 16 / 3 / 4 / 0 | equal or better by score |

## BA-001.T1.FULL_END_NATIVE

1. C0: Correct fenced temperature array.
2. Selected concerns: A low finding restates correct conversions; not a demonstrated defect.
3. Real/plausible/unsupported/false distinction: A low finding restates correct conversions; not a demonstrated defect.
4. Operators: EVIDENCE.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Add explicit rounding to one decimal place for all converted temperatures.
7. Response to selected issue: No new facts; same correct array after one revision. C0 is returned.
8. New defects/lost requirements: No new facts; same correct array after one revision. C0 is returned.
9. Frozen progression: {"C0": 1.0, "C1": 1.0}; actual returned score 1.0.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=ACCEPT_PROVISIONALLY; C1=ACCEPT_PROVISIONALLY. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 13 calls, 43,453 tokens, 517.659s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: ISSUE-IDENTIFICATION FAILURE, TERMINATION / COST FAILURE. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/3273ea96-7d7c-41fc-8b2c-aea0ec39f73b.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-001.T1.FULL_END_STRUCTURED

1. C0: Correct fenced temperature array.
2. Selected concerns: False critical completeness/misassignment allegations; verifier falsely disputes correct values.
3. Real/plausible/unsupported/false distinction: False critical completeness/misassignment allegations; verifier falsely disputes correct values.
4. Operators: CONSTRAINT → HOW → CONSTRAINT.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Correct the temperature conversions for 36.6°C, 100°C, and 21.5°C to ensure all values are accurately converted to Fahrenheit; Fix the conversion mechanism to ensure each output value is correctly mapped to its original input position using a loop that iterates over the input list and applies the conversion formula to each element in sequence; Implement a loop that iterates over each input temperature, converts it to Fahrenheit using the formula F = (C × 9/5) + 32, and stores the result in a new list while maintaining the original order of input values..
7. Response to selected issue: Arrays are identical or whitespace variants. Verifier/issue wording churn resets progress.
8. New defects/lost requirements: Arrays are identical or whitespace variants. Verifier/issue wording churn resets progress.
9. Frozen progression: {"C0": 1.0, "C1": 1.0, "C2": 1.0, "C3": 1.0}; actual returned score 1.0.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 31 calls, 51,154 tokens, 1170.278s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: MODEL FAILURE, ISSUE-IDENTIFICATION FAILURE, JUDGE FAILURE, TERMINATION / COST FAILURE. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/efa824fb-bbda-4138-9243-414e772ef1fb.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-002.T1.FULL_END_NATIVE

1. C0: Correct size/type guard and full chunk loop, plus explanation.
2. Selected concerns: False missing-guard/original-code attribution; later all-case testing is a plausible uncertainty.
3. Real/plausible/unsupported/false distinction: False missing-guard/original-code attribution; later all-case testing is a plausible uncertainty.
4. Operators: EVIDENCE → VERIFY → VERIFY.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Add validation for `size` being a positive integer; Correct the loop range from `range(0, len(items) - size, size)` to `range(0, len(items), size)`; Remove the incorrect range calculation in the loop; Change the range in the loop from `range(0, len(items) - size, size)` to `range(0, len(items), size)`.
7. Response to selected issue: The corrected function remains unchanged. New low findings and in-band claim churn supply opinions, not checks.
8. New defects/lost requirements: The corrected function remains unchanged. New low findings and in-band claim churn supply opinions, not checks.
9. Frozen progression: {"C0": 1.0, "C1": 1.0, "C2": 1.0, "C3": 1.0}; actual returned score 1.0.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 32 calls, 91,718 tokens, 1113.710s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: ISSUE-IDENTIFICATION FAILURE, JUDGE FAILURE, TERMINATION / COST FAILURE, EXTERNAL EVALUATOR LIMITATION. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/41b7f53a-d785-4d23-8549-5c7a5927f1a4.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-002.T1.FULL_END_STRUCTURED

1. C0: Passing chunk function with size<=0 guard; type/comment gaps outside the rubric.
2. Selected concerns: Verifier falsely alleges empty/single/oversized failures; low critiques describe supported claims.
3. Real/plausible/unsupported/false distinction: Verifier falsely alleges empty/single/oversized failures; low critiques describe supported claims.
4. Operators: EVIDENCE → EVIDENCE → VERIFY.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Fix the pre-loop check to ensure `size` is a positive integer by raising ValueError for non-positive `size`; Adjust the range to `range(0, len(items), size)` to ensure all items are processed without exceeding the list length; Add a comment to clarify that the size check is a prerequisite for the loop to avoid infinite loops or index errors; Adjust the range function to use `range(0, len(items), size)` instead of `range(0, len(items) - size, size)`; Add pre-loop check for size <= 0 to ensure positive integer; Adjust range to use `range(0, len(items), size)` instead of `range(0, len(items) - size, size)`.
7. Response to selected issue: All candidate texts are identical. The real untested type/comment issues are not repaired.
8. New defects/lost requirements: All candidate texts are identical. The real untested type/comment issues are not repaired.
9. Frozen progression: {"C0": 1.0, "C1": 1.0, "C2": 1.0, "C3": 1.0}; actual returned score 1.0.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 31 calls, 54,482 tokens, 997.154s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: ISSUE-IDENTIFICATION FAILURE, JUDGE FAILURE, TERMINATION / COST FAILURE, EXTERNAL EVALUATOR LIMITATION. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/5969e198-03ed-4a17-b05b-9fefe5ee4dc4.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-008.T1.FULL_END_NATIVE

1. C0: Passing stable-sort function with explicit false-premise correction and explanation.
2. Selected concerns: False task premise becomes authority in verifier/critique; selected high assumption has no independent support.
3. Real/plausible/unsupported/false distinction: False task premise becomes authority in verifier/critique; selected high assumption has no independent support.
4. Operators: VERIFY → ASSUMPTION → VERIFY.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Clarify that Python's built-in sorted() is stable in Python 3, resolving the factual error; Address the misconception by explaining that the problem's requirement for a stable sort is met by Python's built-in sorted() due to its inherent stability; Add clarification that Python 3's `sorted()` is stable to the explanation; Clarify the problem's misconception about Python's stability in the explanation; Add explicit clarification in the explanation that Python 3's `sorted()` is stable; Adjust the explanation to state that the problem's premise about `sorted()` being unstable is incorrect for Python 3.
7. Response to selected issue: The first revision removes the requested explanation, scores 0.5 instead of 1, and is retained. Comparisons miss the loss.
8. New defects/lost requirements: The first revision removes the requested explanation, scores 0.5 instead of 1, and is retained. Comparisons miss the loss.
9. Frozen progression: {"C0": 1.0, "C1": 0.5, "C2": 0.5, "C3": 0.5}; actual returned score 0.5.
10. Replacement/regression: passing C0 replaced with worse C1; explanation lost.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 31 calls, 94,332 tokens, 2098.151s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: ISSUE-IDENTIFICATION FAILURE, REVISION-PLANNING FAILURE, REVISION-GENERATION FAILURE, JUDGE FAILURE, QUALITYGATE FAILURE, TERMINATION / COST FAILURE. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-008.T1.FULL_END_STRUCTURED

1. C0: Passing stable-sort function with verbose/partly false prose.
2. Selected concerns: False-premise evidence/assumption concerns; no executed check supports them.
3. Real/plausible/unsupported/false distinction: False-premise evidence/assumption concerns; no executed check supports them.
4. Operators: VERIFY → VERIFY → ASSUMPTION.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Add a test to verify that `sorted` is stable by default in Python using a list of tuples with equal ages; Include a comment in the code explaining that `sorted` is stable by default and the problem statement's claim of instability is incorrect; Add explicit test for stability using a list of tuples with equal ages to confirm that `sorted` preserves original order for equal ages; Add a falsifiable test case that explicitly checks the stability of `sorted` under the problem's conditions (e.g., equal ages) to confirm the claim that `sorted` is stable; Add explicit test for stability of `sorted` with equal ages; Include a falsifiable check in the code by adding a test for equal age tuples.
7. Response to selected issue: First revision trims prose/adds an illustrative test; later answers are identical. False list.sort commentary remains.
8. New defects/lost requirements: First revision trims prose/adds an illustrative test; later answers are identical. False list.sort commentary remains.
9. Frozen progression: {"C0": 1.0, "C1": 1.0, "C2": 1.0, "C3": 1.0}; actual returned score 1.0.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 31 calls, 64,100 tokens, 1365.104s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: ISSUE-IDENTIFICATION FAILURE, REVISION-GENERATION FAILURE, JUDGE FAILURE, TERMINATION / COST FAILURE, EXTERNAL EVALUATOR LIMITATION. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/79ec91f1-7b59-4a33-8a53-4613af251c8e.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-009.T1.FULL_END_NATIVE

1. C0: JSON: established cause, E2 alone, no additional evidence requested.
2. Selected concerns: Real missing-evidence/status concern; Engine detects established. Subsequent plan wrongly adds an evidence-ID string.
3. Real/plausible/unsupported/false distinction: Real missing-evidence/status concern; Engine detects established. Subsequent plan wrongly adds an evidence-ID string.
4. Operators: EVIDENCE → VERIFY → SECOND_ORDER_EFFECT.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Add explicit evidence gap note; Preserve substantive possibilities, but remove or qualify unsupported claims of confirmation, establishment or verification. Retain the requested answer format. No independent executed evidence covers these assertions: The root cause was a database dependency issue introduced by the checkout-service v4.2.1 deployment.; Add explicit statement that database metrics are unavailable to the evidence_used list; Update the epistemic status to 'likely' by acknowledging the on-call engineers' statements as strong evidence but not definitive; Preserve substantive possibilities, but remove or qualify unsupported claims of confirmation, establishment or verification. Retain the requested answer format. No independent executed evidence covers these assertions: The root cause was a database dependency issue introduced by the checkout-service v4.2.1 deployment.; Add explicit statement that database metrics are unavailable to the evidence_used list; Update epistemic status from 'established' to 'likely'.
7. Response to selected issue: Second revision reduces certainty to likely but fabricates database_metrics_unavailable; third repeats it. No new evidence enters.
8. New defects/lost requirements: Second revision reduces certainty to likely but fabricates database_metrics_unavailable; third repeats it. No new evidence enters.
9. Frozen progression: {"C0": 0.5, "C1": 0.5, "C2": 0.5, "C3": 0.5}; actual returned score 0.5.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 30 calls, 114,196 tokens, 1287.524s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: REVISION-PLANNING FAILURE, REVISION-GENERATION FAILURE, JUDGE FAILURE, QUALITYGATE FAILURE, TERMINATION / COST FAILURE. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/49544d22-83e0-49a8-9179-c3765116e44b.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## BA-009.T1.FULL_END_STRUCTURED

1. C0: Unformatted prose favoring a database/deployment cause while admitting missing metrics.
2. Selected concerns: Real format/evidence gaps mixed with excessive demands for unavailable query specifics.
3. Real/plausible/unsupported/false distinction: Real format/evidence gaps mixed with excessive demands for unavailable query specifics.
4. Operators: EVIDENCE → SECOND_ORDER_EFFECT → ALTERNATIVE.
5. New information: model proposals only; zero newly executed evidence artifacts.
6. Requested revisions: Add specific database query latency metrics from the latency increase period; Add specific database query latency metrics from the latency increase period (14:05-14:40 UTC); Add quantitative evidence for database query latency during the latency spike period (14:05-14:40 UTC) to the candidate's evidence; Clarify the candidate's statement to explicitly state that the lack of database metrics does not invalidate the database as the root cause but requires further investigation into database-specific metrics to confirm the exact impact.
7. Response to selected issue: Revisions add unsupported evidence-confirms wording. Branches generate cache/payment hypotheses, not observations; JSON stays missing.
8. New defects/lost requirements: Revisions add unsupported evidence-confirms wording. Branches generate cache/payment hypotheses, not observations; JSON stays missing.
9. Frozen progression: {"C0": 0.0, "C1": 0.0, "C2": 0.0, "C3": 0.0}; actual returned score 0.0.
10. Replacement/regression: no measured final-score regression; qualitative defects are not ruled out.
11. QualityGate: C0=REVISE; C1=REVISE; C2=REVISE; C3=REVISE. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.
12. Rollback: 0; no rollback protects the lost BA-008 native explanation.
13. Cost to final: 34 calls, 60,703 tokens, 894.231s.
14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.
15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.

Overlapping failure categories: REVISION-PLANNING FAILURE, REVISION-GENERATION FAILURE, JUDGE FAILURE, QUALITYGATE FAILURE, TERMINATION / COST FAILURE, EXTERNAL EVALUATOR LIMITATION. Operator-selection failure remains unisolated rather than asserted.
Frozen source: `v0351_core_regression_pilot/trajectories/2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`.

## Progress attribution

Every one of the 22 v0.3.5.1 cycles is listed below. `validation_v0352/progress-attribution.json` also covers 22 older v0.3.5 cycles (44 total); old no-progress counters/reasons were not recorded and stay unknown. Data includes before/after candidate, issue creation/closure, grounding, claim/evidence/verifier/gate changes, branch/rollback events and actual reset/blocker fields.
SUBSTANTIVE describes a meaningful content change, not guaranteed improvement. ADMINISTRATIVE / BOOKKEEPING covers opinions/identities/support records without new evidence. WORDING_ONLY identifies unchanged propositions with presentation changes. UNKNOWN is used for absent/no-reset data and unestablished semantic effects.

| Run / cycle | Original reported reasons | Counter | Diagnostic classification | Interpretation |
|---|---|---:|---|---|
| BA-001.T1.FULL_END_NATIVE / 1 | issue_state, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-001.T1.FULL_END_STRUCTURED / 1 | issue_state, verifier_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-001.T1.FULL_END_STRUCTURED / 2 | issue_state, verifier_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-001.T1.FULL_END_STRUCTURED / 3 | none | 1 | UNKNOWN | no observed substantive gain |
| BA-002.T1.FULL_END_NATIVE / 1 | candidate_content, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-002.T1.FULL_END_NATIVE / 2 | issue_state, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-002.T1.FULL_END_NATIVE / 3 | issue_state, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-002.T1.FULL_END_STRUCTURED / 1 | issue_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-002.T1.FULL_END_STRUCTURED / 2 | none | 1 | UNKNOWN | no observed substantive gain |
| BA-002.T1.FULL_END_STRUCTURED / 3 | none | 2 | UNKNOWN | no observed substantive gain |
| BA-008.T1.FULL_END_NATIVE / 1 | candidate_content, issue_state, claim_support_state | 0 | SUBSTANTIVE | harmful: explanation removed, external score 1→0.5 |
| BA-008.T1.FULL_END_NATIVE / 2 | claim_support_state, verifier_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-008.T1.FULL_END_NATIVE / 3 | candidate_content, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-008.T1.FULL_END_STRUCTURED / 1 | candidate_content, issue_state, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-008.T1.FULL_END_STRUCTURED / 2 | none | 1 | UNKNOWN | no observed substantive gain |
| BA-008.T1.FULL_END_STRUCTURED / 3 | none | 2 | UNKNOWN | no observed substantive gain |
| BA-009.T1.FULL_END_NATIVE / 1 | issue_state, claim_support_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |
| BA-009.T1.FULL_END_NATIVE / 2 | candidate_content, claim_support_state, verifier_state | 0 | SUBSTANTIVE | mixed: lower status, newly fabricated citation, score unchanged |
| BA-009.T1.FULL_END_NATIVE / 3 | none | 1 | UNKNOWN | no observed substantive gain |
| BA-009.T1.FULL_END_STRUCTURED / 1 | candidate_content, issue_state | 0 | SUBSTANTIVE | harmful: unsupported confirmation added, score unchanged |
| BA-009.T1.FULL_END_STRUCTURED / 2 | candidate_content | 0 | WORDING_ONLY | model-state/wording change, no independently acquired evidence or score improvement |
| BA-009.T1.FULL_END_STRUCTURED / 3 | candidate_content, branch_state | 0 | ADMINISTRATIVE / BOOKKEEPING | model-state/wording change, no independently acquired evidence or score improvement |

## Cost interpretation and architectural implications

The eight FULL_END runs consume 233 calls and 574,138 tokens over 22 cycles; all four-task completed trials total 237 calls/583,933 tokens. Judge/verification loops repeatedly revisit unchanged or externally neutral candidates. Repairs fix protocol structure, not substantive truth. BA-008 native damages an already passing answer; BA-009 plans manufacture authority rather than acquire evidence. The historical absence of NO_PROGRESS stops alone is not proof of a detector defect: cap timing and mandatory assumptions also explain continuation.
The patch only removes concrete invalid progress signals: advisory issue creation, unverified claim churn, and unvalidated model-verifier opinion changes. It retains authoritative issue resolution, registered executed checks, candidate content, gate/contradiction changes and mandatory-action protection. No external scores enter production. There is no measured saving estimate, no counterfactual inference, and no revision architecture rebuild.
Recommendation after integrity validation: **B. RECONSIDER REVISION ARCHITECTURE BEFORE MORE INFERENCE.** The observed loop cannot reliably select a real correctable issue, plan a valid correction, preserve requirements, or compare resulting answers. Integrity tests can constrain authority; they cannot demonstrate useful revision ability. Future design investigation should distinguish evidence acquisition and constraint preservation from additional opinions before authorizing more inference.
