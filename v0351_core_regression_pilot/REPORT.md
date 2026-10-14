# v0.3.5.1 Core Regression Pilot Replay

## Postflight environment warning

Ollama was 0.35.1 at preflight and is 0.40.0 at postflight; model digest remains unchanged. The change time and per-session versions are unknown. All twelve outcomes are preserved, but this is not a clean server-version-controlled before/after replay. No further inference or compensating rerun was performed. See FINAL_AUDIT.json.

## Purpose and limitations

- Four tasks, one trial per condition; diagnostic only
- Same three-cycle cap and exposed seeds; sampling noise remains
- Same model generates and judges; external scoring only certifies encoded checks
- Safety withholding and selected-candidate/raw scores are distinct from returned-answer task quality
- Known frozen BA-008 premise regex can miss Markdown corrections; no score adjustments

## Preflight

Engine 0.3.5.1; fingerprint `c04475eafbf7bc13f3cd0f2c4a772db9113c23c25e3cf35dd0cdb8b853643077`; offline tests 262 passed.
Model `qwen3:4b`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`, preflight Ollama 0.35.1 (postflight 0.40.0; timing unknown). Engine/model settings untouched; baseline decisions only.
All task/evaluator/source hashes, generation settings and seeds are recorded in manifest.json before inference.

## Run status

COMPLETED: 12/12 completed; execution failures 0; external failures 4.

## Task results

| Task | DIRECT | STRUCTURED | NATIVE |
|---|---:|---:|---:|
| BA-001 | 1.0000 / Pass | 1.0000 / Pass | 1.0000 / Pass |
| BA-002 | 1.0000 / Pass | 1.0000 / Pass | 1.0000 / Pass |
| BA-008 | 1.0000 / Pass | 1.0000 / Pass | 0.5000 / Fail |
| BA-009 | 0.5000 / Fail | 0.0000 / Fail | 0.5000 / Fail |

## C0 to returned answer

| Run | C0 | Final | Delta/class | Selected raw | Withheld | Cycles | Gate / stop |
|---|---:|---:|---|---:|---|---:|---|
| BA-001.T1.FULL_END_NATIVE | 1.0 | 1.0 | 0.0 / NEUTRAL | 1.0 | False | 1 | ACCEPT_PROVISIONALLY / ACCEPTED_PROVISIONALLY |
| BA-001.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 0.0 / NEUTRAL | 1.0 | False | 3 | REVISE / BUDGET_EXHAUSTED |
| BA-002.T1.FULL_END_NATIVE | 1.0 | 1.0 | 0.0 / NEUTRAL | 1.0 | False | 3 | REVISE / BUDGET_EXHAUSTED |
| BA-002.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 0.0 / NEUTRAL | 1.0 | False | 3 | REVISE / BUDGET_EXHAUSTED |
| BA-008.T1.FULL_END_NATIVE | 1.0 | 0.5 | -0.5 / REGRESSED | 0.5 | False | 3 | REVISE / BUDGET_EXHAUSTED |
| BA-008.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 0.0 / NEUTRAL | 1.0 | False | 3 | REVISE / BUDGET_EXHAUSTED |
| BA-009.T1.FULL_END_NATIVE | 0.5 | 0.5 | 0.0 / NEUTRAL | 0.5 | False | 3 | REVISE / BUDGET_EXHAUSTED |
| BA-009.T1.FULL_END_STRUCTURED | 0.0 | 0.0 | 0.0 / NEUTRAL | 0.0 | False | 3 | REVISE / BUDGET_EXHAUSTED |

Candidate progression, formats and raw/final-region lengths are retained in diagnostics/*.json and results.csv. The frozen evaluator scores the actual returned answer, including empty withheld output.

## Before/after costs and mechanisms

| Condition | v0.3.5 calls / tokens / seconds | v0.3.5.1 calls / tokens / seconds |
|---|---|---|
| DIRECT | 4 / 10591 / 620.853 | 4 / 9795 / 728.869 |
| FULL_END_STRUCTURED | 129 / 226927 / 2535.794 | 127 / 230439 / 4426.767 |
| FULL_END_NATIVE | 104 / 339009 / 3314.186 | 106 / 343699 / 5017.044 |

Totals: 237 actual attempts; 583933 tokens; 2.826 completed-trial hours.

Descriptive costs only; no causal savings or general superiority claim. Interrupted attempts, if any, are preserved separately and require additional accounting.

## Repair, output integrity and no-progress observations

- BA-001.T1.FULL_END_NATIVE: attempted/succeeded/failed/suppressed=0/0/0/0; discarded=0; no-progress=0/False; withheld=False.
- BA-001.T1.FULL_END_STRUCTURED: attempted/succeeded/failed/suppressed=0/0/0/0; discarded=0; no-progress=1/False; withheld=False.
- BA-002.T1.FULL_END_NATIVE: attempted/succeeded/failed/suppressed=2/1/1/0; discarded=2; no-progress=0/False; withheld=False.
- BA-002.T1.FULL_END_STRUCTURED: attempted/succeeded/failed/suppressed=0/0/0/0; discarded=0; no-progress=2/False; withheld=False.
- BA-008.T1.FULL_END_NATIVE: attempted/succeeded/failed/suppressed=1/1/0/0; discarded=0; no-progress=0/False; withheld=False.
- BA-008.T1.FULL_END_STRUCTURED: attempted/succeeded/failed/suppressed=1/1/0/0; discarded=0; no-progress=2/False; withheld=False.
- BA-009.T1.FULL_END_NATIVE: attempted/succeeded/failed/suppressed=0/0/0/0; discarded=0; no-progress=1/False; withheld=False.
- BA-009.T1.FULL_END_STRUCTURED: attempted/succeeded/failed/suppressed=0/0/0/0; discarded=0; no-progress=0/False; withheld=False.

All stage failures, cycle progress reasons/blockers and extracted epistemic checks are retained in trajectories and diagnostics. No suppression activates and zero repair calls are deterministically avoided; no saved-token estimate is claimed.

## Manual mechanism verdicts and hostile review

All eight FULL_END trajectories were manually reviewed against all thirteen requested questions. See MANUAL_REVIEW.md and the final interpretation below; task pass alone is not mechanism success.

## Historical immutability

Hash snapshots are in preflight/protected-before.json; FINAL_AUDIT.json verifies the final state. No old output is replayed as a new model response.

## Recommendation

**B. TARGETED v0.3.5.2 REPAIR.** Specific output-integrity and legitimate-constraint counterexamples remain. The expensive revision loop also remains unproven. No larger experiment or repair is launched in this task.

## Final interpretation

### Final decision

**B. TARGETED v0.3.5.2 REPAIR.** The replay exposes concrete integrity counterexamples:
affirmative confirms prose escapes the status guard, genuine evidence-ID criticism
is suppressed, and full-task references are classified too broadly as descriptive.
These prevent concluding that the targeted safety mechanisms now work reliably.
No further experiment or implementation is launched by this recommendation.

This is a recommendation to correct demonstrated integrity failures, not an
assumption that another patch will make the revision loop useful. The deeper loop
concern remains substantial: 0/8 score improvements, one damaged passing C0,
unchanged 22 completed cycles, unreliable comparisons, and very large inference
budgets. A larger Beta is not justified by these results. This pilot cannot establish
general reasoning improvement, universal correctness, or production safety.

### Postflight environment warning

Ollama was **0.35.1 at preflight** and reports **0.40.0 at postflight**. Its model
digest remains identical. The external server changed at an unknown time during
this multi-session replay; per-session server versions were not persisted. Individual
trials therefore cannot be assigned confidently to a server version. No update was
installed or requested by this task. No further inference or compensating rerun
was performed after discovery. Raw outcomes and within-trajectory mechanism traces
are preserved, but this is not a clean server-version-controlled before/after replay.
Sampling and wall-time comparisons have this additional confound. The final audit
records a warning rather than an unqualified pass for environmental comparability.

### Procedural result and preflight

Exactly twelve fresh local trials completed, one per original task/condition, in
the historical manifest order. Zero execution failures, transport retries,
truncations, cloud, Gemini, TypeSafe or Jev calls. Four external task failures remain.
Only missing trials resumed after two interruptions; nine already completed trials
were preserved on the latest retry. Partial outputs were archived, never reused as
fresh model responses. Session gaps are not inference runtime.

Actual offline preflight: Python 3.12.14, 262 tests, zero failures/errors/skips,
zero blocked network attempts, 15.606 seconds. Command equivalent:
`python -B -m unittest discover -s tests -t .`, run through the recorded
network-blocked unittest API in `prepare.py`, with bytecode writes disabled.
Replay infrastructure: 13 tests passed. An initial synthetic fixture failure was
corrected before manifest freeze and before any inference; the initial failed log
is retained. No runner, evaluator, task, prompt, Engine or control was changed
after preflight. The output helper's calculations were also frozen.

Actual Engine version 0.3.5.1 and all 68 source-scope files match the implementation
record. Fingerprint:
`c04475eafbf7bc13f3cd0f2c4a772db9113c23c25e3cf35dd0cdb8b853643077`.
qwen3:4b digest:
`359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
Preflight Ollama 0.35.1 matched the historical pilot; postflight is 0.40.0 as noted
above. Temperature 0.7, top_p 0.8,
num_predict 4096, num_ctx 8192, think=false, timeout 900 seconds and the old
transport-retry allowance remain unchanged. Both FULL_END modes use baseline
decisions, repair-attempt cap one, cycle cap three, failure limit two and
no-progress patience two. Generation mode is their only configuration difference.

The four task files and alpha-3 evaluator are byte-identical to the historical
pilot/Alpha. Same order and exposed per-call seeds do not guarantee identical
sampling. Fresh C0 differences, including the interrupted/resumed BA-001 attempt,
demonstrate that limitation. Historical outputs were read as evidence, not rescored
or substituted into the replay. All runtime projections stayed below six hours.

### Before/after mechanism verdicts

| Mechanism | v0.3.5 historical observation | v0.3.5.1 replay verdict |
|---|---|---|
| BA-002 semantic false reject | Real quote could support false attribution and rejection | Narrow typed finding path succeeds: all 13 model allegations across both modes are nondecisive; no judge-driven REJECT/rollback. False verifier/critique concerns still drive REVISE. Overall semantic reliability is not established. |
| BA-008 premise elevation | Correct contradiction of the false factual premise caused rejection | Typed judge premise exclusions work, but false premise still becomes authoritative in verification/critique, driving REVISE in both modes. Genuine prescriptive evidence-ID concerns are suppressed elsewhere. Overall invariant fails. |
| BA-009 output overclaim | Native returned established from E2 agreement alone | Native detects C0/C1 overclaim and deterministic revision eventually lowers it to likely; no verified evidence is earned. Structured returns unsupported evidence-confirms prose with zero extracted checks. Broad earned-status invariant fails. |
| BA-001 invalid structured references | Unexercised | Unexercised in both completed trials. Interrupted structured attempt has separately preserved invalid-ID/repair observations; not pooled into the matrix. |
| Successful repairs | 0 of 12 attempts | 3 of 4 attempts genuinely accepted and used; protocol success does not prove criticism truth. |
| Repair suppression | Not available | 0 activations/calls avoided; failure threshold not reached naturally, so unexercised. |
| FULL_END improved versus C0 | 0/8 | 0/8; seven neutral, one regressed. |
| NO_PROGRESS stops | Not available | 0; same 22 completed FULL_END cycles. No premature useful stop observed. |
| Structured calls / tokens | 129 / 226,927 | 127 / 230,439 |
| Native calls / tokens | 104 / 339,009 | 106 / 343,699 |

There are 51 model grounding incidents: 40 TASK_PREMISE_DEPENDENT,
10 SEMANTIC_UNSUPPORTED and one semantic UNSUPPORTED with a mismatched quote.
All are nondecisive. Engine-derived epistemic feedback in native BA-009 is separate
and remains actionable. Excluding every model finding is not proof of correctness:
J003 in native BA-009 accurately identifies the fabricated evidence ID but becomes
SEMANTIC_UNSUPPORTED; AJ002 in structured BA-009 accurately identifies unsupported
confirmation but becomes premise-dependent. These are preserved conservative
filter counterexamples. Independent scoped-evidence overrides are unexercised live.

### C0, actual output and format

The main report task table and C0 table use the frozen evaluator, including the
actual returned output rather than a selected unsafe raw candidate. There is no
withheld output in this replay. The C0/revision progression is:

| Task / mode | C0 → C1 → C2 → C3 scores | C0 raw / frozen final-region chars | Returned chars | C0 / returned format | Revisions |
|---|---|---:|---:|---|---:|
| BA-001 structured | 1 → 1 → 1 → 1 | 46 / 46 | 46 | Pass / Pass | 3 |
| BA-001 native | 1 → 1 | 6,594 / 44 | 44 | Pass / Pass | 1 |
| BA-002 structured | 1 → 1 → 1 → 1 | 623 / 623 | 623 | Pass / Pass | 3 |
| BA-002 native | 1 → 1 → 1 → 1 | 7,670 / 7,670 | 431 | Pass / Pass | 3 |
| BA-008 structured | 1 → 1 → 1 → 1 | 2,219 / 2,219 | 1,259 | Pass / Pass | 3 |
| BA-008 native | 1 → 0.5 → 0.5 → 0.5 | 12,015 / 12,015 | 84 | Pass / Pass | 3 |
| BA-009 structured | 0 → 0 → 0 → 0 | 404 / 404 | 870 | Fail / Fail | 3 |
| BA-009 native | 0.5 → 0.5 → 0.5 → 0.5 | 11,945 / 227 | 254 | Pass / Pass | 3 |

BA-008 native drops the requested explanation and loses a passing C0. Its Python
fence still passes the coarse format check. BA-009 native exchanges a failed
certainty check for a fabricated-reference failure while still failing the
missing-evidence check. BA-009 structured never repairs its detected JSON format.
Manual review finds additional false prose/type/comment defects that the rubric
does not measure. Historical pass-count differences largely reflect fresh C0s and
rubric coverage, not demonstrated revision value or a causal version effect.

The frozen final-region helper fails on BA-002/BA-008 native C0s because incidental
unmatched triple-backtick text makes it treat the real standalone thinking delimiter
as inside a fence. Those large frozen region lengths are reported faithfully,
not silently corrected. Returned FULL_END answers do not expose those prefixes;
DIRECT retains its original raw-output behavior. No Engine ledger/ID metadata leak
or truncated call was recorded. In-band reasoning/presentation is a separate concern.

### Epistemic safety

Native BA-009 has UNVERIFIED claims and no candidate-bound executed support.
C0/C1's established enum is extracted, made an Engine concern, and produces a
deterministic qualify/remove revision instruction. C1 ignores it; C2/C3 lower the
enum to likely. Final guard action is allow. No output is withheld and no unsafe
residual block is exercised live. Negated uncertainty is not falsely blocked.

Structured BA-009's actual C3 says the evidence confirms the database as root cause
despite no database observations. The present-tense confirms form escapes the bounded
recognizer. A different clause denying exact certainty does not negate that positive
claim. Zero extracted checks and a rubric unsupported-claim counter of zero cannot
be read as safe output: the malformed JSON prevents normal rubric claim scoring.
The safety benefit in native is narrow and real procedurally; it is not task-score
improvement, proof of causal correctness, or success of the overall output invariant.

### Repair behavior and cost

| Run / stage | First observed repair outcome | Second stage failure | Suppression / later repair calls avoided |
|---|---|---|---|
| BA-002 native / critique | Failed: string null references persist; two elements discarded | None | 0 / 0 |
| BA-002 native / revision_plan | Succeeded: repaired plan accepted and used | None | 0 / 0 |
| BA-008 structured / critique | Succeeded: null references repaired and output ingested | None | 0 / 0 |
| BA-008 native / critique | Succeeded: null references repaired and output ingested | None | 0 / 0 |

Other completed runs have no repair attempt. Totals: attempted 4, succeeded 3,
failed 1, suppressed 0, discarded 2. No stage has two failed repairs, so stage
futility suppression is unexercised. Actual wire repair calls and logical attempt
counters agree at four. No saved-token estimate is made; deterministically avoided
repair calls are zero. The interrupted attempt's two observed repair calls and
unknown terminal counters remain outside these completed-trial statistics.

| Condition | Completed cycles | Judge / verifier / repair / revision calls | Total calls per completed cycle | Tokens | Wall time |
|---|---:|---|---:|---:|---|
| DIRECT | — | 0 / 0 / 0 / 0 | — | 9,795 | 12m 08.869s |
| STRUCTURED | 12 | 66 / 16 / 1 / 12 | 10.583 | 230,439 | 1h 13m 46.767s |
| NATIVE | 10 | 55 / 14 / 3 / 10 | 10.600 | 343,699 | 1h 23m 37.044s |

Completed-trial total: **237 calls, 583,933 tokens, 10,172.679908 seconds
(2h 49m 32.680s)**. Historical completed trials used 237 calls, 576,527 tokens,
6,470.832698 seconds. Thus actual call count is unchanged, tokens slightly higher,
and measured wall time substantially higher. Hardware/runtime load and model/judge
sampling vary; these are descriptive differences, not causal savings estimates.

Both interrupted attempts add fourteen saved responses, 16,284 tokens and
414.241081 seconds of observed latency, plus two started calls with unknown
consumption. Known recorded whole-replay responses total 251 and known tokens
600,217; actual attempts/consumption are higher because of those unknown calls.
Completed-trial wall plus recorded partial response latency is 10,586.920989 seconds;
this is not total calendar elapsed time or a complete measure of interrupted runtime.
Historical interruption overhead is likewise separate from the old completed totals.

### No-progress behavior and hostile review

Per-cycle reasons, counters and blockers for every run are preserved in diagnostics
and each manual entry. No NO_PROGRESS stop, premature useful stop, or acceptance
via no-progress occurred. BA-002 structured reaches counter two only at the ordinary
three-cycle cap. BA-008 structured reaches two while a task-induced high-risk
assumption protects continuation. Native BA-009's mandatory first-cycle protection
permits the useful second status correction; its third identical final JSON still
consumes budget. Other runs count raw words, active claims, reworded objections or
verifier state as progress without improving external answer quality. Zero replay
rollbacks mean rollback-to-identical-state behavior is unexercised here.

Hostile review preserves these failure classes: prescriptive-reference classifier
overreach; conservative loss of legitimate evidence/citation criticism; false-premise
authority through verifier/critique; confirms guard escape; raw-answer delimiter
failure; model plans treated as user authority; lingering epistemic weaknesses after
status correction; wrong model comparisons; failure to repair known formatting;
and expensive churn that removes a useful explanation. Some are continuing
architectural problems, some newly exposed correction boundaries; this single trial
does not prove all were caused by v0.3.5.1. All eight trajectories were inspected
against all thirteen manual-review questions. No controls were changed to improve
these outcomes, and no extra live trial was added.

### Historical immutability and artifact scope

`FINAL_AUDIT.json` records final source, frozen control/task/evaluator, protected
file-set/hash, completed-trial preservation, raw call/cost, configuration and Git
checks. Its historical audit compares all 2,182 preflight-protected files, including
all 373 old-pilot files, Alpha/Beta/Beta-Gemini, Jev/v0351 validation, implementation
reports and README. All are unchanged. Exact snapshots are in `preflight/` and
`postflight/`. Other local work is retained; the repository was already dirty.
Git HEAD is unchanged. No commit, push, publication, version bump, Engine edit,
benchmark resumption or END Harness modification was performed.

All new outputs remain under `v0351_core_regression_pilot/`: the twelve durable
trials/evaluations, eight trajectories, all raw wire/call logs, diagnostics, failure
archives, interrupted-attempt archives, manifest, summary, CSV and authored reports.
No research evidence was deleted or silently excluded. Recommendation B is the sole
recommended next action; it is not authorization to implement it in this task.
