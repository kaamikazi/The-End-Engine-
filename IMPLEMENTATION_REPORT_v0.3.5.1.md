# END Engine v0.3.5.1 — Semantic Grounding + Epistemic Output Integrity

Implementation and deterministic offline validation only. No live pilot, Alpha,
Beta, Beta-Gemini, Jev A/B or TypeSafe smoke was executed. No reasoning or answer
improvement is claimed. No commit or push was made.

## 1. Empirical motivation

The frozen v0.3.5 pilot completed four tasks × three conditions × one trial = 12
runs. None of its eight FULL_END runs improved final external score over C0.
Structured used 129 calls/226,927 tokens; native used 104 calls/339,009 tokens.
Exact quotation filtering helped, but semantic misattribution, quoted false-premise
objections and unsupported user-facing establishment claims remained. Twelve repair
calls produced zero recorded successes and discarded 32 elements. BA-001 did not
exercise invalid-ID recovery; this release does not claim that pilot revalidated it.

Read-only references: `v035_core_regression_pilot/REPORT.md`, `MANUAL_REVIEW.md`,
`FINAL_AUDIT.json` and all six requested BA-002/008/009 FULL_END trajectories.
`validation_v0351/observed-mechanisms.json` preserves their exact diagnostic excerpts;
no external result was rescored or fed into production logic.

## 2. Baseline state

| Property | Recorded value |
|---|---|
| Package version | 0.3.5 |
| Source fingerprint | `7c9ce8d2b892b70cdecce93b40c3310269d603c59101757f32983dde96a0947b` |
| Source scope | Canonical sorted SHA-256 manifest of `end_engine/**/*.py` and `pyproject.toml`, 64 files |
| Python | 3.12.14, bundled local runtime |
| Git commit | `6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7` |
| Baseline Engine suite | 226 tests, 0 failures/errors/skips |
| Runtime networking | Blocked; 0 attempts observed |
| Decision default | baseline |

Git was already dirty from prior research/implementation work. Its initial status
is preserved in `validation_v0351/git-status-before.txt`. Per-command safe.directory
was used; no Git configuration or history was changed. All 2,145 files in the five
required historical directories were hashed before edits, including the complete
pilot directory, and remain byte-identical with no additions/deletions.

## 3. BA-002 root cause

`ground_issue` previously returned decisive GROUNDED immediately on quote occurrence.
Judges could quote the real size guard and falsely assert that it did not reject
zero/negative inputs, or confuse discussion of original buggy code with the fixed
implementation. UNQUOTED objections could also remain decisive. Text occurrence
established attribution but not the alleged behavior.

The correction separates textual and semantic annotations. Code-behavior inferences
and original/fixed-source contradictions without scoped support become nondecisive
uncertainties. A deterministic checker declaration for the exact artifact can
contradict or substantiate an explicitly scoped alleged defect. It proves only that
property, not universal candidate correctness.

## 4. BA-008 root cause

Premise dependency was checked after quotation, so adding a real quote bypassed the
task-premise protection. The task could effectively become a factual yardstick.
Checks of task authority and external support now precede acceptance of quotation
as a deciding interpretation. No production code names BA tasks or Python sorting
facts; fixtures use generic delivery/validation examples as well as controlled
historical mechanism patterns.

## 5. BA-009 root cause

Evidence integrity correctly kept agreement unverified, but that did not constrain
the actual answer. The pilot returned native JSON with `certainty="established"`,
only engineer chat cited, and no additional evidence requested, despite a
REVISE/INCONCLUSIVE gate. Consensus detection added uncertainty but did not require
correction of the assertion or prevent its return. The old claim extractor also
missed ordinary status-bearing JSON targets.

The new check extracts bounded explicit epistemic assertions into the existing
claim register, checks their candidate/target/scope against executed contracts,
requires targeted revision and performs a final return check independent of gate
acceptance. Internal verification bookkeeping and displayed status can no longer
diverge for the recognized assertions.

## 6. Repair inefficiency root cause

Pilot repairs returned schema-valid data that still targeted prose, JSON field
names or the wrong identifier register. Allowed IDs were available but buried in
context. Critique and plan stages repeatedly reproduced the same malformed pattern.
Discarding whole invalid-target changes erased useful uncertainty corrections, and
native revision fell back to generic instructions. Parse/schema recovery and
reference recovery could also request separate repairs of the same result.

The zero-success pilot count was real for its recorded reference repairs, not a
hidden set of successful corrections. A provider returning text or valid JSON alone
is insufficient success accounting. New counters acknowledge reference-sensitive
results only after Engine validation and use. Initial plan/critique contexts now
expose allowed weakness IDs explicitly; plan instructions distinguish IDs from
field names and allow an honest empty target list.

## 7. Semantic-grounding design

Optional finding fields: `source_claim`, `alleged_defect`, `basis`. Optional claim
types include CANDIDATE_INTERNAL, TASK_CONSTRAINT, EXTERNAL_FACTUAL, EPISTEMIC_STATUS
and the legacy EXTERNAL_FACT spelling. Models cannot set Engine grounding annotations.

The Engine records `textual_grounding` separately from `semantic_grounding`:

| Semantic result | Decisive | Basis |
|---|---|---|
| SEMANTIC_SUPPORTED | yes | Relevant exact-artifact executed contract establishes the scoped defect |
| SEMANTIC_CONTRADICTED | no | Relevant exact-artifact executed contract contradicts it |
| SEMANTIC_UNSUPPORTED | no | Interpretation lacks bounded support, or executed checks conflict |
| TASK_PREMISE_DEPENDENT | no | Descriptive/ambiguous task assertion is the alleged factual support |
| REQUIRES_EXTERNAL_VALIDATION | no | An external factual objection lacks scoped executed support |

Existing MISATTRIBUTED/UNGROUNDED exclusions remain. Recognized real prescriptive
violations remain decisive. The semantic check recognizes only explicit polarity
of otherwise matching declared propositions; it does not solve arbitrary entailment.
Evidence must be EXECUTED_EVIDENCE, belong to the candidate, bind the exact content
hash and declare the matching statement/property and bounds. Unrelated tests,
other candidates and wrong artifacts cannot override an objection. Conflicting
checks remain unresolved regardless of artifact order.

Nondecisive findings remain in judgments, fatal-issue records and judge_groundings
with their complete argument. They cannot independently create a weakness, reject
a candidate or trigger rollback. A failed scoped check and real task constraint
retain their force. Other legacy undeclared findings retain compatibility behavior
where no evidence-dependent inference is detected; this is a documented limitation.

## 8. Task premise versus task constraint

`TaskContract` is optional caller metadata containing bounded tuples of
prescriptive_constraints/descriptive_assertions plus a mandatory-revision flag.
The two classifications cannot contain the same assertion. Contracts are recorded
and supplied to judges, but remain TASK_PROVIDED rather than evidence of world truth.

Without metadata, a conservative fallback recognizes explicit imperatives and
hypotheticals in matching task sentences. A judge declaring TASK_CONSTRAINT cannot
grant factual authority to a descriptive statement. Ambiguous/descriptive wording
does not independently prove candidate error. An explicit "For this hypothetical,
assume X" remains binding. Independent, scoped executed evidence can establish an
otherwise descriptive factual objection. Task text and judge confidence cannot.

## 9. Epistemic output integrity

The existing ClaimExtractor/KnowledgeRegister receives recognized epistemic targets,
including those expressed through JSON certainty/confidence/status/verification/
verified/confirmed fields. Enum separators are normalized; UNVERIFIED/NOT_VERIFIED
are not affirmative verification. Probability-style confidence=1 is recognized;
other numeric scales are not interpreted as proof.

Explicit affirmative verified/confirmed/established/proven/proved/certain/
demonstrated/validated assertions require an exact targeted executed contract.
Negative, hypothetical and conditional forms are handled separately. Human/model/
decision agreement, model receipts, untargeted PASS, wrong artifacts and conflicting
checks cannot authorize status. The small ceiling is UNVERIFIED versus
VERIFIED_WITHIN_SCOPE, reusing existing evidence semantics rather than introducing
a global truth ladder. Universal wording cannot be authorized by a narrow check.

Overclaims create ENGINE_DERIVED weaknesses and a bounded corrective instruction
appended after model-plan salvage. Thus malformed IDs cannot erase the instruction
to preserve possibilities while qualifying unsupported establishment. At equal
gate rank, a safe status revision outranks an overclaim, while gate requirements and
severe-regression/rollback rules remain intact. Safety does not promote verification.

If the selected candidate still overclaims at termination, its raw content stays in
the ledger, `output_integrity.blocked=true`, the scorecard/result are
BLOCKED/INCONCLUSIVE and `EngineResult.answer` is empty. It is not silently rewritten
or passed off as accepted. Callers must handle that blocked result.

Final assertion checks, format checks and displayed output use the same final answer
region. A standalone `</think>` terminator outside code fences separates observable
provider deliberation from the displayed answer; inline/literal markers are kept.
Raw candidate hashes remain the evidence-binding source. No separate hidden reasoning
is inspected or disclosed. Unreviewably large/deep outputs are conservatively blocked.
Bounds: 32,000 final-region characters, 32 assertions, eight JSON blocks, depth five
and 64 entries per object/list. No model call is added for inspection.

## 10. Repair suppression and accounting

`RepairPolicy` lives on one trajectory and is shared by generation, judges,
critique/plan/verification reference checks and synthesis. Default cumulative
failure limit is two per stage; a new run starts fresh. Configuration
`repair_failure_limit` accepts integers >=2.

At most one targeted repair is made per malformed result. Nested schema/reference
repairs cannot add a second attempt. Legacy protocol_repair_attempts values 2/3
still load but positive values execute one attempt; zero disables it. Repeated
futility suppresses later requests and records the reason. Valid remainder is
salvaged; unknown IDs are never mapped and rejected synthesis is never adopted.
Unparseable essential results without a usable remainder still stop honestly as
MODEL_PROTOCOL_FAILURE, not fabricated candidates or EXTERNAL_BLOCKER.

`repair_statistics` records repair_attempted, repair_succeeded, repair_failed,
repair_suppressed, invalid_elements_discarded, failures_by_stage and pending stages.
`repair_outcomes` acknowledges accepted-and-used output. Unconsumed pending repairs
are closed as failed on termination. Legacy protocol_events remain available.
Avoided provider-invocation counts are recorded when knowable; exhausted call-budget
cases report unknown savings. Hypothetical token savings are not fabricated.

## 11. Internal no-progress termination

After quality evaluation and any rollback, InternalProgress compares the restored
candidate and existing issue, claim-support, assumption, evidence, verifier, gate,
contradiction and branch states. It does not read external scores. Metadata IDs,
timestamps, occurrence counters and provider deliberation do not by themselves
count as progress. Punctuation/filler normalize; JSON key order and valid Python
formatting normalize through syntax inspection without execution. Identifiers,
negation, values and substantive changes remain distinguishable.

Two consecutive completed stagnant cycles permit NO_PROGRESS (configurable
no_progress_patience>=2). Meaningful changes reset the counter. Revision followed
by rollback to the same starting state is not progress. Mandatory revision,
deterministic format/verifier failure, pending recovery/branches, minimum/critical
scrutiny, high-risk assumptions, custom termination policy and required
post-acceptance probes prevent this shortcut. Hard call/cycle ceilings still apply.

NO_PROGRESS and gate acceptance are separate. Existing best-candidate selection,
restoration and final reconciliation remain. The trace records cycle_progress
reasons/blockers, no_progress_cycles and no_progress_stop. No extra model call is
made to assess progress. The detector is deliberately conservative; semantic
paraphrases can still evade it and mandatory work may consume the whole cap.

## 12. Offline tests

| Suite | Actual result |
|---|---|
| Baseline full suite | 226/226 pass |
| New v0.3.5.1 regressions | 36/36 pass |
| Final full suite | 262/262 pass, zero failures/errors/skips |

All required S1–S17 cases are covered. Additional controls cover unrelated/wrong
artifact evidence, conflicting checks in both orders, nested/enum JSON and negation,
bounded scan failure, malformed schema plus invalid IDs without double repair,
qualified revision selection, restored-state rollback, JSON/code normalization,
literal markers, final format and additive serialization. S1/S2 execute controlled
literal test functions inside trusted offline fixture callbacks. Production code
does not execute arbitrary generated code.

Three existing v0.3.5 test expectations changed deliberately:

- R4: a historical repair setting of 2 now allows one repair, not two.
- R11: the legitimate behavioral-defect positive control now includes a real scoped
  deterministic failing chunk test; quote existence alone is no longer its proof.
- R10: unsupported independent-confirmation output requires REVISE and final
  withholding, rather than merely ACCEPT_PROVISIONALLY.

No existing test was removed. The other 223 baseline tests retain their expectations.
Full suite: `python -m unittest discover -s tests -t .`; regression pack:
`python -B -m unittest tests.test_v0351_regressions`. Validation used the bundled
Python 3.12.14 with PYTHONDONTWRITEBYTECODE=1 through
`python -B -m validation_v0351.run_offline tests`. Socket connection, UDP, DNS and
urllib opening are blocked during test discovery/execution; all recorded attempts
are zero. Existing decision-provider tests retain their offline fake-client cases;
new release validation uses baseline defaults and never enables a live Jev adapter.

## 13. Schema, serialization, replay and changed files

Trajectory schema remains 3.0 with additive optional issue annotations and
repair_outcomes/repair_statistics/epistemic_checks/cycle_progress/output_integrity
observations. Old 1.0/2.0/3.0 records still load through unchanged serializer/ledger
contracts; existing compatibility tests pass. NO_PROGRESS is an additional stop
string. Consumers with closed stop enums must recognize it. Model/provider replay
and optional decision replay code were not changed. Exact old requests are not
promised to match the intentionally updated judge/repair prompts of a new version.

Modified source files:
`end_engine/__init__.py`, `config.py`, `engine.py`,
`cognition/branches.py`, `cognition/knowledge.py`,
`core/output_format.py`, `core/revision_planner.py`, `core/state.py`,
`experience/schema.py`, `models/recording.py`, `operators/base.py`,
`quality/gate.py`, `quality/grounding.py`, `quality/judges.py`, `quality/schema.py`,
`quality/session.py`, `quality/state.py`, and `pyproject.toml`.

New source files: `core/task_contract.py`, `core/progress.py`, `models/repair.py`,
`quality/epistemic.py`. Other changes: README, the three expectations in
`tests/test_v035_regressions.py`, new `tests/test_v0351_regressions.py`, this report
and `validation_v0351/`. The current Git diff also contains pre-existing v0.3.5/Jev
work, so `validation_v0351/source-before.json` is the release baseline. All files
under `end_engine/decisions/` remain unchanged. No separate Harness file was touched.

## 14. Version and final fingerprint

Version: **0.3.5.1**, not 0.3.6. 0.3.6 remains reserved/proposed for the separate
experimental Jev routing release. This bump records the corrective release, not
live transport or routing validation.

Final source fingerprint (68 files; same canonical manifest scope as baseline):

`c04475eafbf7bc13f3cd0f2c4a772db9113c23c25e3cf35dd0cdb8b853643077`

See `validation_v0351/identity-after.json`, `source-after.json`, test JSON/logs and
`history-audit.json`. All 2,145 protected files are unchanged with no additions.
No secrets were added to source or reports; credential-like literal scanning of
changed/new source found none. Credentials are not printed in this report.

## 15. Known limitations

- Offline synthetic validation does not demonstrate better live reasoning or lower
  real-model cost. Grounding still cannot decide arbitrary truth or entailment.
- Semantic evidence matching uses explicit propositions, polarity and trusted
  checker declarations. Ambiguous wording may remain unsupported; bad checker
  contracts remain the caller's trust boundary. Legacy undeclared findings can
  still be misinterpreted outside detected evidence-dependent patterns.
- Task classification and final status extraction are bounded English/JSON
  heuristics. Unrecognized paraphrases, alternative schemas, implicit factual
  overclaims and multilingual phrasing are not universally understood. Conservative
  mismatches/budget limits may withhold otherwise useful output.
- A declared narrow scope must match the assertion/contract literally. This avoids
  widening evidence but can reject legitimate differently worded scope statements.
- Blocking preserves the raw candidate for research but returns an empty answer;
  downstream consumers must surface the blocked result and reasons. It does not
  automatically produce a new safe model answer after the cycle budget ends.
- No-progress ignores some cosmetic differences, not every semantic paraphrase.
  Mandatory/high-risk work can still consume every permitted cycle. Only prevented
  invocations are counted; actual token/time savings await live measurement.

## 16. Exact recommendation for the separately authorized pilot replay

Ready for a new **diagnostic replay of the same 12-run design**, not full Beta.
Do not run it until separately authorized, and do not resume/overwrite the frozen
v035_core_regression_pilot directory: its runner binds the old source fingerprint
and its 12 trials are complete.

Use a separate new directory, such as `v0351_core_regression_pilot/`, with a new
manifest recording this version/fingerprint, baseline tests and provider identity.
Copy the same four Alpha task files and alpha-3 evaluator byte-for-byte. Preserve
seed 20261005 and the exact old condition order:

| Task | Order |
|---|---|
| BA-001 | DIRECT, FULL_END_NATIVE, FULL_END_STRUCTURED |
| BA-002 | FULL_END_NATIVE, DIRECT, FULL_END_STRUCTURED |
| BA-008 | FULL_END_STRUCTURED, FULL_END_NATIVE, DIRECT |
| BA-009 | FULL_END_STRUCTURED, FULL_END_NATIVE, DIRECT |

One trial each. Both FULL_END conditions use max_cycles=3,
protocol_repair_attempts=1, repair_failure_limit=2, no_progress_patience=2 and
decision.provider=baseline, differing only in candidate_generation. No supplemental
task-contract metadata should be added to these historical task prompts.

Use the same local qwen3:4b digest
`359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`, temperature .7,
top_p .8, num_predict 4096, num_ctx 8192, think=false, timeout 900s and the same
recorded per-task seed scheme. Verify/record the Ollama version (old pilot .35.1).
Retain the six-hour projection guard and immediate durable per-trial records;
resume only missing runs. No Jev, cloud provider, additional conditions/trials or
benchmark merging. Manually review all eight new FULL_END trajectories, including
overclaim blocking, retained corrections, suppression and NO_PROGRESS rather than
interpreting empty output as a transport error. Preserve the known BA-008 regex
limitation without changing its frozen score. Compare outcomes and actual call/
token costs descriptively; no superiority claim is justified before that replay.
