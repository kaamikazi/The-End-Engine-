# Candidate selection calibration

Population: all60 historical candidates, not just returned answers. Original candidate-bound external records are copied by reference into CANDIDATE_CALIBRATION; internal judgments/gate/reasons/verification appear in CYCLE_AUDIT. Original comparator requests and results remain in the trajectory. These are repeated correlated observations from16 runs, so no independent calibration confidence interval is asserted.

| Internal gate | External pass | External fail | Total |
| --- | --- | --- | --- |
| ACCEPT_PROVISIONALLY | 3 | 0 | 3 |
| REVISE | 18 | 15 | 33 |
| REJECT | 12 | 12 | 24 |
| BLOCKED / ACCEPT_VERIFIED | 0 | 0 | 0 |
| Total | 33 | 27 | 60 |

12/24 rejection events contradict the frozen pass outcome **within its scope**; they are candidate-scoped rejection disagreements, not12 independent false world judgments. Many defects outside the rubric could still matter. 18/33 REVISE candidates pass externally, but REVISE includes incomplete scrutiny/uncertainty and is not REJECT or rollback. Provisional acceptance3/3 matches encoded pass, with zero verified acceptance and no newly executed evidence. This tiny selected acceptance sample does not establish specificity or absence of false acceptance elsewhere. All27 external failures are REJECT/REVISE; absence of ACCEPT_VERIFIED is an intended epistemic limit here.

Historical LLM verification reports passed for4 candidates (all externally pass), failed for56 (29 external pass,27 fail). These are **model judgments**, not deterministic verifier receipts. External evaluator executions happen outside END after the run; they cannot retrospectively supply runtime evidence authority. Basic Engine format/status checks are separate finite checks. Candidate mean judge score/confidence columns in CANDIDATE_CALIBRATION are descriptive; confidence is not correctness and its averaging is not used to choose a candidate.

## Traced disagreements

1. Old BA-001 native C1 receives a fatal adversarial finding that also admits conversions are correct, no exact quote, and REJECT; frozen score1. Trajectory `9cea722d-0dbe-43b8-9d30-24d6eac0befa.jsonl`, AJ002, C1. Returning C0 protects the score but the fatal rejection is unsupported.
2. Old BA-002 native C0–C3 all score1, all REJECT: original broken code/explanation is attributed to the repaired loop; actual quote occurrence is treated as semantic proof. Trajectory `6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl`, AJ001–AJ004. Structured provides a mixture of appropriately excluded task/hybrid quotes and false unquoted allegations; legitimate non-integer gap remains outside evaluator coverage.
3. New BA-001 structured all score1, gates REVISE: typed judge findings are excluded, but false verifier/critique completeness concerns continue. Trajectory `efa824fb-bbda-4138-9243-414e772ef1fb.jsonl`. A less decisive negative path does not prove useful revision or complete assessment.
4. New BA-008 native C0 score1→C1 .5, all gates REVISE, returned C1. Comparator prefers/credits explanation that is absent, no rollback. Trajectory `653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl`, first comparison and subsequent best comparison, C0/C1. This demonstrates failed preservation of best already-recorded answer; no generated improved child was discarded.
5. Old BA-008 native C0 explanation is qualitatively useful, removed in C1; frozen regex hides loss, all .5. Trajectory `91b86589-796e-4570-965b-bd025d7c7b87.jsonl`. External flatness cannot validate comparator's assertion of equivalent explanations.
6. New BA-009 native C2/C3 add unknown ID after status qualification. Accurate unknown-ID criticism is conservatively excluded as SEMANTIC_UNSUPPORTED; model comparison calls a model plan a user instruction. Trajectory `49544d22-83e0-49a8-9179-c3765116e44b.jsonl`, C2/C3, J003. Structured 'confirms' assertion escapes status checking: `2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl`, C1–C3. Final budget output is unaccepted/inconclusive, not a false ACCEPT_VERIFIED; nevertheless returned answer integrity is inadequate historically.

Links for these original trajectories and their external files are in REPORT's trace index and each CYCLE_AUDIT row. Both pilot MANUAL_REVIEW files corroborate these scoped readings; no old label or score was changed.

## Rollback, disagreement and scoring risk

18 rollback events occur in the older pilot; zero in the newer one. Many rollbacks concern identical/passing code or preserve an already wrong C0; one retains old code-only C1 after rejecting C3. None is shown to discard a higher external-scoring child. Current best selection ranks gates, uses advisory comparison preferences on ties, accounts for observed unsafe ties, and restores candidate-scoped snapshots. Current comparator itself remains model-advisory. Finite current reference/status/format checks improve authority handling offline; their live calibration is unmeasured.

Primary/adversarial verdict disagreement occurs in the examples above, but the configured secondary-primary dispute detector is absent (no secondary judge); adversarial disagreement is not automatically a DISPUTED event. Model confidence1 in old native BA-009 C1/C2 coexists with unsupported establishment. Comparator deltas can be allzero while its prose claims an improvement; protocol validity does not calibrate this. No deliberate score-gaming causal intervention was made. Repeated identical candidates with different IDs get new assessments; cache-by-ID does not avoid text-equivalent judgments.

Better-child-missed H5 is unsupported by the frozen score oracle: best recorded external score equals C0 in every run. Selection failure still matters for retaining good C0 and recognizing missing requirements/safety. Rubric omissions prevent declaring all ties equally good. No external score is proposed as a new runtime authority.
