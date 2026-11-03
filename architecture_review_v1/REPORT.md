# END Cognitive Architecture Review v1
## Why Does Deliberation Fail to Improve Candidates?

Read-only research, 2026-10-11. **Recommendation D: pause architecture development pending better evaluation.** This does not mean the historical failures are unexplained: unsupported issue inputs, invalid repair prescriptions, lost requirements and inaccurate comparisons are directly observable. It means these small, contaminated historical samples do not identify a dominant causal bottleneck or establish which production architecture to change next. The three proposed alternatives are hypotheses, not implementations or demonstrated improvements.

### Baseline and evidence authority

Actual Engine **0.3.5.2**, Python **3.12.14**, source fingerprint **29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82** over 70 Engine Python/pyproject entries. Git main, HEAD **6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7**, extensive pre-existing dirty work. [BASELINE.json](BASELINE.json), [git-status-before.txt](git-status-before.txt).

The guarded equivalent of `python -B -m unittest discover -s tests -t .` discovers **303 tests: 0 failures, 0 errors, 0 skipped, 0 runtime network attempts**, 21.975 seconds. [preflight.py](preflight.py) redirects temporary test fixtures into this review, disables bytecode and blocks DNS/socket/urllib runtime networking. [offline-tests.json](offline-tests.json), [complete test log](offline-tests.txt). Mock/scripted provider calls in offline tests are not live inference. These tests constrain behavior; they do not establish reasoning improvement.

Live observations below concern **v0.3.5 and v0.3.5.1 only**. v0.3.5.2 has no new live evaluation. Historical source fingerprints are recorded in the pilot manifests; Git HEAD alone cannot identify these dirty-tree versions. Both pilots use qwen3:4b, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`, temperature .7, top_p .8, prediction cap 4096, context 8192, think=false, timeout 900s. The newer pilot's server changed from .35.1 to .40.0 at an unknown time. Seed equality is not output equality. [old manifest](../v035_core_regression_pilot/manifest.json), [new report](../v0351_core_regression_pilot/REPORT.md).

Historical [Benchmark Alpha](../benchmark_alpha/REPORT.md) is context, not part of the44-cycle denominator: v0.3.4,96 completed trials (12 tasks×4 conditions×2 trials), stopped short of144 planned.22/24 FULL_END runs terminate as then-labelled EXTERNAL_BLOCKER, chiefly protocol/reference failures; only8 FULL_END cycles complete. FULL_END passes8/24 with mean score .3646, versus DIRECT15/24/.6458 and SELF_REFLECT16/24/.7738. Protocol failures, output truncation, differing conditions and narrow scoring prevent assigning this gap solely to cognition. Later pilots demonstrate completed cycles, but no encoded C0 improvement. Synthetic Beta/Jev validation records remain preserved; they supply no new empirical evidence here.

### Audited population and outcomes

Every completed FULL_END trial in both pilots is included, without outcome sampling: four already-inspected tasks × two generation modes × one trial × two versions. DIRECT trials and interrupted archives are contextual evidence, outside the primary denominator. All **60 candidate external evaluations already exist**; none was newly run, corrected or substituted. Scores remain the frozen rubric's observations, not complete answer truth.

| Population | Runs | Cycles | Candidates | Calls | Tokens | Run wall seconds |
| --- | --- | --- | --- | --- | --- | --- |
| v0.3.5 FULL_END | 8 | 22 | 30 | 233 | 565,936 | 5,849.980010 |
| v0.3.5.1 FULL_END | 8 | 22 | 30 | 233 | 574,138 | 9,443.811153 |
| Combined primary | 16 | 44 | 60 | 466 | 1,140,074 | 15,293.791163 |


The 44 actual parent→child transitions have **0 encoded score improvements, 1 encoded regression and 43 equal scores**. Final versus C0: **0/16 improved, 15/16 equal, 1/16 regressed**; within each pilot, 0/8 improved. Mean C0 score .71875, actual final .6875. **10/16 C0s already score 1**, leaving only six runs with encoded headroom. There is no hidden higher-scoring generated candidate: the retrospective score oracle chooses C0 (tie preference) in every run. Zero newly executed evidence artifacts are present in the 16 runtime traces.

[CYCLE_AUDIT.csv](CYCLE_AUDIT.csv) contains every cycle, exact critique/plan/verifier/judgment records, prompt/wire references, selected-topic classification, missingness, incoming/child/effective candidates and cost. [CANDIDATE_TRANSITIONS.csv](CANDIDATE_TRANSITIONS.csv) retains overlapping score/content/format/safety dimensions. [CANDIDATE_CALIBRATION.csv](CANDIDATE_CALIBRATION.csv) covers all 60 candidates; [CALL_AUDIT.csv](CALL_AUDIT.csv) reconciles all 466 physical calls with trajectory steps and raw wire files. The 80 pre-cycle calls include 16 initial generations and 64 assessments; they are not 80 generations. Cycles account for 386 calls.

### What fails in the observable chain

1. **A check topic is mistaken for a demonstrated defect.** New BA-001 structured C0 is correct, yet completeness/misassignment objections and plans recur for three cycles. BA-002's repaired loop and guards are repeatedly confused with original buggy code. Positive statements such as 'the claim is supported' are stored as low-severity weaknesses. A selected sorting requirement can be legitimate while the ensuing critique incorrectly elevates the task's factual premise. The research labels deliberately distinguish these objects. [issue/operator audit](OPERATOR_VALUE.md), all per-cycle references below.
2. **Useful discovery does not guarantee a valid repair.** Old BA-009 recognizes evidence/uncertainty problems, but invalid target IDs cause usable changes to be discarded after failed repairs. New native BA-009 cycle 1 receives a valid Engine instruction to qualify unsupported establishment; C1 ignores it. Cycle 2's model plan places an unavailable-metrics statement in `evidence_used`, producing an undeclared ID. Structured plans ask for observations explicitly absent from the task. No acquisition mechanism exists. [revision audit](REVISION_FAILURES.md).
3. **Generation and selection lose satisfied requirements.** New BA-008 native C0 scores 1, C1 removes the requested explanation and scores .5. Plans call for clarification, not deletion; comparison imagines the explanation or reports no material gain/loss, and final selection retains C1. Old BA-008 has the same qualitative loss hidden by the frozen Markdown-sensitive regex. This is bad generation and failure to preserve C0; it is not evidence that an improved revision was generated then discarded. [selection calibration](QUALITYGATE_CALIBRATION.md).
4. **More state is not necessarily more knowledge.** Of 57 ingested critique-finding occurrences, 28 are exact normalized repeats, one a cautious reformulation, 22 new lexical proposals and six unresolved identity cases. These are not 57 proven defects. Thirty transitions have unchanged raw or historical answer regions; their cycles consume 256 calls/590,742 tokens. Model-derived checks and branches add opinions/hypotheses without new executed evidence. [cost](COST_AND_TERMINATION.md).

The current code addresses several integrity routes in the historical chain: shared assessment authority, actual answer scope, plan origins, reference deltas and filtered progress. Its operator utility still uses advisory severity and a bookkeeping-derived information-gain proxy. That is a testable risk, **not a live v0.3.5.2 failure observation**. The default baseline call ceiling is None, while finite cycle/operation caps remain; a future experiment must set an explicit shared call ceiling. [actual loop A–J](COGNITIVE_LOOP.md), [current implementation record](../IMPLEMENTATION_REPORT_v0.3.5.2.md).

### Competing bottlenecks, ranked by evidential support

Counts overlap and are diagnostic coverage, not attributable causal fractions. Ranking reflects directly observed mechanisms before unobserved model/generalization explanations. None proves exclusive causation.

| Rank / hypothesis | Supporting evidence / potentially explained observations | Evidence against / uncertainty | Small discriminating test |
| --- | --- | --- | --- |
| 1 H6 no new evidence | 0 executed artifacts across 44 cycles; BA-009 metric gap never filled | Arithmetic/code repair can improve without new world observations. Absence of receipts does not prove all reasoning valueless. | Give finite failing checks to B versus same tasks without checks; measure grounded repairs. |
| 2 H1 issue discovery | 18/44 primary BAD ISSUE diagnoses; 28/57 repeated findings; false completeness/guard/premise criticisms | Useful BA-009 gaps coexist; 22/44 selected topics are plausible, not demonstrated errors. BAD ISSUE labels concern critiques, not all topics. | Blindly adjudicate proposed defects and novelty against candidate/task before viewing final outcomes. |
| 3 H3 planning | 11/44 primary GOOD ISSUE BAD PLAN; empty salvaged plans and unavailable-metric/citation actions | Malformed IDs are protocol rather than conceptual planning failures; structured real JSON repair overlaps generation. | Hold a grounded issue fixed; compare explicit bounded delta with model-derived plan. |
| 4 H9 protocol/format | 16 repairs (old12 failed; new4 with3 success), old BA-009 empty plans; all8 structured BA-009 candidates lack JSON | Most runs finish; native failures persist without candidate JSON envelope. Historical delimiter/evaluator errors confound scoring. | Freeze authoritative answer span and runtime contracts; separate repair failure from repair quality. |
| 5 H7 overdeliberation | 24/44 transitions enter from score1 candidates; first new BA-008 native cycle loses .5; 30 unchanged transitions | Only one encoded loss. Later native BA-009 cycle lowers certainty. Unknown longer-horizon benefits. | Preserve C0 with A unless bounded actionable failure exists; compare safety and improvement, not just cost. |
| 6 H4 generation | 7/44 primary GOOD PLAN BAD GENERATION: six native BA-008 cycles and first new native BA-009 | Other plans are invalid/empty, so failures cannot be assigned to generation. Preservation wording alone is not a perfect plan. | Supply identical independently adjudicated valid repair objectives across repetitions. |
| 7 H5 evaluation | 12 REJECT gates on externally passing candidates; new passing C0 lost; unsupported fatal/confident claims | 0 externally better child exists to be missed; rubric omits type/prose safety. Thus strong better-child hypothesis unsupported. | Measure pairwise choice against hidden quality/safety annotations and independently scored candidates. |
| 8 H2 utility | 44 activations, no encoded gain; EVIDENCE15 and VERIFY13; utility learns internal activity proxies | No randomized operator intervention; poisoned issue input can explain apparently bad selection. | Match issue eligibility, randomize selector only; measure valid novel findings and downstream delta. |
| 9 H8 model capability | Same4B generator/judges; factual confusion, invalid IDs, instruction failures | Direct/C0 solve many tasks. No stronger-model contrast; server drift and sampling remain. | Only after protocol/task freeze, separately authorized model-factor comparison with digest/settings held per cell. |


### Recommendation and roadmap

**D** is the only recommendation. A requires demonstrated useful candidate improvement that is absent here. B requires generally useful issue discovery, which these traces do not establish beyond narrow cases. C requires most failures to originate upstream, but the conservative primary BAD ISSUE count is 18/44, not a majority; 11 plan failures and seven execution failures coexist, and stages overlap. Historical integrity fixes also mean the old observations cannot select a current production redesign confidently. D is a decision under uncertainty, not a claim of no architectural knowledge.

Next action: **freeze and independently review two fresh diagnostic tasks and their external scoring/safety contracts, including a deliberate passing-C0 case and a repairable failing case, before authorizing any experimental adapter or live request.** They must not be BA-001/002/008/009 variants with merely changed numbers. Establish that the rubric detects missing explanations, malformed output, unsupported certainty and undeclared citations; report any unmeasurable semantics. No task/evaluator is created in this investigation.

[ARCHITECTURE_PROPOSALS.md](ARCHITECTURE_PROPOSALS.md) specifies A sparse gating, B evidence/constraint repair and C bounded alternatives in 15 dimensions each. [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) specifies the future **24-run matrix**, physical ceiling **136 calls**, **400,000 tokens** and **3 hours** total, resumable but without budget reset. Historical purpose-weighted projection: ~273,440 tokens/~101 minutes before repair/overhead margin; completion is not guaranteed. It requires separate implementation and live-inference authorization. It is **NOT EXECUTED**.

### Trace index: every FULL_END run

| Version | Run | Cycles | Actual parent→child lineage | C0 / returned score | Returned ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 0.3.5 | BA-001.T1.FULL_END_NATIVE | 1 | C0→C1 | 1.0 / 1.0 | C0 | [9cea722d-0dbe-43b8-9d30-24d6eac0befa.jsonl](../v035_core_regression_pilot/trajectories/9cea722d-0dbe-43b8-9d30-24d6eac0befa.jsonl) |
| 0.3.5 | BA-001.T1.FULL_END_STRUCTURED | 3 | C0→C1, C0→C2, C0→C3 | 0.0 / 0.0 | C0 | [02835fa6-600d-4e78-b878-3d5f65e4c344.jsonl](../v035_core_regression_pilot/trajectories/02835fa6-600d-4e78-b878-3d5f65e4c344.jsonl) |
| 0.3.5 | BA-002.T1.FULL_END_NATIVE | 3 | C0→C1, C0→C2, C0→C3 | 1.0 / 1.0 | C0 | [6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl](../v035_core_regression_pilot/trajectories/6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl) |
| 0.3.5 | BA-002.T1.FULL_END_STRUCTURED | 3 | C0→C1, C0→C2, C0→C3 | 1.0 / 1.0 | C0 | [42be76c1-49bc-4a96-bba0-a3d55d5e7af3.jsonl](../v035_core_regression_pilot/trajectories/42be76c1-49bc-4a96-bba0-a3d55d5e7af3.jsonl) |
| 0.3.5 | BA-008.T1.FULL_END_NATIVE | 3 | C0→C1, C1→C2, C2→C3 | 0.5 / 0.5 | C1 | [91b86589-796e-4570-965b-bd025d7c7b87.jsonl](../v035_core_regression_pilot/trajectories/91b86589-796e-4570-965b-bd025d7c7b87.jsonl) |
| 0.3.5 | BA-008.T1.FULL_END_STRUCTURED | 3 | C0→C1, C0→C2, C0→C3 | 1.0 / 1.0 | C0 | [ca37375d-c022-4ffa-a2b5-5d641b59cf35.jsonl](../v035_core_regression_pilot/trajectories/ca37375d-c022-4ffa-a2b5-5d641b59cf35.jsonl) |
| 0.3.5 | BA-009.T1.FULL_END_NATIVE | 3 | C0→C1, C0→C2, C2→C3 | 0.5 / 0.5 | C2 | [b3c8b8d8-2388-40c0-9e2c-c75a679ef56e.jsonl](../v035_core_regression_pilot/trajectories/b3c8b8d8-2388-40c0-9e2c-c75a679ef56e.jsonl) |
| 0.3.5 | BA-009.T1.FULL_END_STRUCTURED | 3 | C0→C1, C0→C2, C0→C3 | 0.0 / 0.0 | C0 | [67a5c2d9-fcf4-4c27-81a1-67a9076ba93f.jsonl](../v035_core_regression_pilot/trajectories/67a5c2d9-fcf4-4c27-81a1-67a9076ba93f.jsonl) |
| 0.3.5.1 | BA-001.T1.FULL_END_NATIVE | 1 | C0→C1 | 1.0 / 1.0 | C0 | [3273ea96-7d7c-41fc-8b2c-aea0ec39f73b.jsonl](../v0351_core_regression_pilot/trajectories/3273ea96-7d7c-41fc-8b2c-aea0ec39f73b.jsonl) |
| 0.3.5.1 | BA-001.T1.FULL_END_STRUCTURED | 3 | C0→C1, C1→C2, C2→C3 | 1.0 / 1.0 | C0 | [efa824fb-bbda-4138-9243-414e772ef1fb.jsonl](../v0351_core_regression_pilot/trajectories/efa824fb-bbda-4138-9243-414e772ef1fb.jsonl) |
| 0.3.5.1 | BA-002.T1.FULL_END_NATIVE | 3 | C0→C1, C1→C2, C2→C3 | 1.0 / 1.0 | C1 | [41b7f53a-d785-4d23-8549-5c7a5927f1a4.jsonl](../v0351_core_regression_pilot/trajectories/41b7f53a-d785-4d23-8549-5c7a5927f1a4.jsonl) |
| 0.3.5.1 | BA-002.T1.FULL_END_STRUCTURED | 3 | C0→C1, C1→C2, C2→C3 | 1.0 / 1.0 | C0 | [5969e198-03ed-4a17-b05b-9fefe5ee4dc4.jsonl](../v0351_core_regression_pilot/trajectories/5969e198-03ed-4a17-b05b-9fefe5ee4dc4.jsonl) |
| 0.3.5.1 | BA-008.T1.FULL_END_NATIVE | 3 | C0→C1, C1→C2, C2→C3 | 1.0 / 0.5 | C1 | [653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl](../v0351_core_regression_pilot/trajectories/653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl) |
| 0.3.5.1 | BA-008.T1.FULL_END_STRUCTURED | 3 | C0→C1, C1→C2, C2→C3 | 1.0 / 1.0 | C1 | [79ec91f1-7b59-4a33-8a53-4613af251c8e.jsonl](../v0351_core_regression_pilot/trajectories/79ec91f1-7b59-4a33-8a53-4613af251c8e.jsonl) |
| 0.3.5.1 | BA-009.T1.FULL_END_NATIVE | 3 | C0→C1, C1→C2, C2→C3 | 0.5 / 0.5 | C3 | [49544d22-83e0-49a8-9179-c3765116e44b.jsonl](../v0351_core_regression_pilot/trajectories/49544d22-83e0-49a8-9179-c3765116e44b.jsonl) |
| 0.3.5.1 | BA-009.T1.FULL_END_STRUCTURED | 3 | C0→C1, C1→C2, C2→C3 | 0.0 / 0.0 | C3 | [2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl](../v0351_core_regression_pilot/trajectories/2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl) |


### Limitations and validation

[LIMITATIONS.md](LIMITATIONS.md) records ceiling effects, tiny correlated sample, unavailable independent evidence, observer/task contamination, rubric omissions, incomplete interrupted costs, version drift, unobserved counterfactual branches and the separation between historical findings and current code. [COUNTERFACTUAL_ANALYSIS.md](COUNTERFACTUAL_ANALYSIS.md) labels saved-output comparisons, oracle choice and policy-dependent unknowns.

All writes are confined to this review. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) inventories original source/records/task/evaluator hashes, source roles and analysis provenance. [FINAL_VALIDATION.json](FINAL_VALIDATION.json) checks whole-workspace file-set/hash preservation outside the review, Engine fingerprint, task/evaluator identity, CSV/source references and totals. No Engine/Harness/task/evaluator/prompt/config edit, version bump, commit, push, publication, model inference or live benchmark was performed.
