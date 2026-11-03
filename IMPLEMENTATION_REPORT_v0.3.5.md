# END Engine v0.3.5 implementation report — Protocol Robustness + Grounded Judgment

- **Date:** 2026-10-01.
- **Scope:** a narrow reliability release driven by failures observed in Benchmark Alpha (v0.3.4).
- **What was not done:**
  - no live model calls, no Benchmark Beta;
  - no Harness edits;
  - no change to any Benchmark Alpha artifact;
  - no training, RAG, retrieval or new providers.
- **Earlier reports:** preserved; the v0.3.4 report is byte-identical in `IMPLEMENTATION_REPORT_v0.3.4.md`.

> **v0.3.5 has not been shown to improve END's answers.** It changes how END handles malformed model output and how it
> weighs judge findings. Whether that changes external results is for Benchmark Beta to measure.

## 1. Baseline (before any change)

| | |
|---|---|
| Engine version | 0.3.4 |
| Source fingerprint | `d1a9f68bb8cacf1e4dc4384180d5b6971bebb8209b34ea50f1bb94939ceed7a2` |
| Engine tests | **164/164 OK** (`validation_v035/engine-tests-before.txt`) |
| Benchmark Alpha infrastructure tests | **18/18 OK** |
| Python | 3.12.1 |
| Git | commit `6b2ff6e` ("Initial public release of END Engine"). `end_engine/` and `tests/` were clean against it. The only uncommitted changes were the completed Benchmark Alpha artifacts. |

**Alpha snapshot.** All 836 Benchmark Alpha files were hashed before the first edit (`validation_v035/alpha-immutability.txt`).

**Git access.** Git refused to run because `.git` is owned by another Windows account. After checking that the
repository config is benign (no hooks, no fsmonitor), git commands were run read-only with a one-off
`-c safe.directory`. No configuration was changed.

## 2. Benchmark Alpha failures that motivated this release

The run used `qwen3:4b` (Q4_K_M, local Ollama): 12 tasks × 4 conditions × 2 trials = 96 runs.

**Protocol failures:**
- FULL_END ended in `EXTERNAL_BLOCKER` in 22 of 24 runs, and END_LITE in 17 of 24.
- FULL_END averaged 0.33 END cycles.
- Almost every abort came from one malformed field: a weakness ID that did not exist (`C0`, `E1`, `completeness`,
  `correctness`, `prevention`, `timezone_ambiguity`, `root_cause`, …), or a non-promising branch adoption.

**Candidate quality:**
- END's first candidate scored a mean of 0.35, against DIRECT's 0.65.
- It had the task's required output structure in 23 of 48 runs, against DIRECT's 36 of 48.
- One answer leaked END internals into the user-facing text (BA-011.T2.END_LITE).

**Judgment failures:**
- Judges attributed task code to the candidate (BA-002.T2).
- Judges treated a false task premise as truth (BA-008.T2).
- Answers presented engineers' agreement as "independently confirmed" (BA-009).

## 3. Root causes found in the code

**Protocol failures.**
- *Reference checks raised plain `ValueError`.* Every validation of model-produced identifiers did so:
  - `WeaknessRegistry.ingest` (critique) and `apply_updates` (verification);
  - `RevisionPlanner.plan`;
  - `SynthesisPlanner.synthesize`;
  - `KnowledgeRegister.update/ingest`.
- *Parse and schema errors did too,* in `RecordingProvider` and `schema.validate`.
- *One handler turned everything into `EXTERNAL_BLOCKER`.* `EndEngine.run` had a single `except Exception` that
  classified all of these as external.
- *No stage could recover.* None validated elements individually or retried, so one bad ID ended the run.

**C0 generation.**
- The answer was produced inside a JSON `content` field, with the prompt "Produce an initial answer to the task. State
  assumptions and material limitations."
- Nothing in it told the model to keep the task's output format.
- **Alpha records:** C0's median length was 794 characters, against 12,793 for DIRECT.
- Revision requests carried internal plans with weakness IDs, which is where leakage came from.

**Judge grounding.**
- Judge issues had no candidate-quote or claim-type fields, and judges got no source provenance.
- Every fatal or major issue counted toward the gate and became a critical or high weakness, whatever its basis.
- So an objection quoting the *task* could reject a correct candidate, and so could one that rested on a task
  premise.

## 4. Protocol-error taxonomy

`end_engine/models/protocol.py` defines `ModelProtocolError`, a `ValueError` subclass so that component callers stay
compatible, with these categories:

| Category | Meaning |
|---|---|
| `MODEL_PROTOCOL_SCHEMA_FAILURE` | Unparseable or schema-invalid output |
| `MODEL_PROTOCOL_INVALID_REFERENCE` | An unknown or duplicate weakness, claim, assumption, branch or operator ID |
| `MODEL_PROTOCOL_INVALID_TRANSITION` | Adopting a non-promising branch |
| `MODEL_PROTOCOL_UNGROUNDED_FINDING` | Reserved. Ungrounded judge findings are handled by grounding (§7), not raised. |
| `MODEL_PROTOCOL_REPAIR_EXHAUSTED` | Bounded repair did not yield usable output |

Effect on termination:
- **Invalid model output.** `StopReason.MODEL_PROTOCOL_FAILURE` (new, additive), with `termination.category` set to
  the protocol category.
- **Provider exceptions** (unavailable, transport, timeout, external budget). `EXTERNAL_BLOCKER`, with category
  `EXTERNAL_FAILURE`.
- **Providers can opt in.** A provider may raise `ModelProtocolError` itself to report a model-output failure.
- **Returned candidate already evaluated.** After a protocol failure, the gate of a returned candidate whose evaluation
  completed stands. It is capped at `ACCEPT_PROVISIONALLY`, with the reason "Model protocol failure stopped further
  scrutiny".
- **Nothing evaluated yet.** The run is `BLOCKED`/`INCOMPLETE`, with a protocol reason.

## 5. Recovery behaviour

`EngineConfig.protocol_repair_attempts` defaults to 1, accepts 0–3, and 0 disables repair. Every step is a
`protocol_event` that records:
- the stage and category;
- the validation error and the invalid values;
- the action: `repair_requested`, `repaired`, `invalid_elements_discarded`, `invalid_targets_discarded`,
  `invalid_updates_rejected`, `synthesis_discarded`, `branch_exploration_skipped` or `repair_exhausted`;
- what was kept or discarded, and whether the run continued.

| Stage | Behaviour |
|---|---|
| Any structured call | `RecordingProvider` re-issues the request once with `protocol_repair` (the error and the rejected output) and records both calls. |
| Critique | Unknown weakness IDs and unknown or duplicate knowledge updates get one repair listing the valid IDs. Invalid elements left after repair are discarded and the valid remainder is used. Same-output creations (a new assumption updated in the same critique) count as valid. |
| Revision plan | One repair. Unknown targets are removed. A change whose targets were all unknown is discarded, never re-targeted. Custom planners keep their own behaviour. |
| Verification | Updates are judged individually (unknown, duplicate, missing reason). An `LLMVerifier` gets one repair. Valid updates are applied and rejected ones recorded. |
| Branch synthesis | One repair. A still-invalid synthesis is discarded: nothing is adopted, promising branches become `EXHAUSTED`, rejected ones stay `REJECTED`. The adoption invariant is unchanged. Failed branch exploration is skipped locally. |
| LLM operator selection | An unknown operator is an `INVALID_REFERENCE` protocol failure. |

**Invariants kept:**
- Invalid identifiers are never mapped to real ones.
- No replacement content is manufactured.
- Repair is bounded.
- Provider failures are never retried as model-output problems.

## 6. C0 generation changes

- **New, opt-in:** `EngineConfig(candidate_generation="native")`.
  - The initial candidate is generated as free text, and the request is the task itself (no context, no schema),
    exactly what a direct call sends.
  - Revisions receive the task, the previous answer and the plan's actions, with no weakness or candidate IDs.
  - They are told to follow the task's output format and not to mention the process.
  - `known_strengths` stays empty and `confidence` stays null; nothing is invented.
- **Default unchanged:** `"structured"` keeps byte-identical v0.3.4 generation requests.
- **Why native is opt-in, not the default.**
  - *The Harness's fixture generators* raise on `generate()`, so making native the default would break an existing
    integration. That is a stated stop condition.
  - *Changing the structured prompt broke a comparability guarantee.* An intermediate version of this release changed
    the structured prompt, and a read-only Harness test failed because its DIRECT baseline mirrors END's C0 request
    byte for byte. That change was reverted.
- **Engine checks in both modes** (`end_engine/core/output_format.py`, provenance `ENGINE_DERIVED`, recorded in
  `engine_checks`):
  - **Format.** Explicit requirements (a required fenced block language, "JSON object"/"JSON array") and violations.
  - **Leakage.** Engine-internal markers not mentioned by the task: weakness or claim IDs, "candidate Cn", "revision
    plan", Engine machinery.
  - **Consensus.** Answers presenting agreement as confirmation.
  - **Effect on the gate.** A format violation or a leak is a task-constraint violation, so the gate gives `REVISE`.
    Consensus-as-confirmation adds uncertainty.

## 7. Judge-grounding architecture

- **Typed judge context.** The existing keys stay, for existing judge providers. Added:
  - a `sources` block: TASK is `TASK_PROVIDED` and may contain false premises; CANDIDATE is the only text attributable
    to the candidate; EVIDENCE is labelled;
  - a `provenance` label on every evidence item;
  - prompt rules to keep sources apart, a definition of each `claim_type`, "a task premise is not a verified fact",
    and "agreement is consensus, not verification".
- **Issue schema.** Optional `claim_type`, `candidate_quote` and `task_reference`. Judges cannot set `grounding` or
  `decisive`.
- **Grounding** (`end_engine/quality/grounding.py`, deterministic):

| Status | When | Decisive |
|---|---|---|
| `GROUNDED` | The quote occurs in the candidate | yes |
| `UNQUOTED` | No quote, and nothing contradicts the attribution (pre-0.3.5 behaviour) | yes |
| `TASK_CONSTRAINT` | Declared as a task-constraint finding | yes |
| `MISATTRIBUTED` | The quote, or a backtick span of 12 or more characters, occurs only in the task | no |
| `UNGROUNDED` | The declared quote occurs in neither the candidate nor the task | no |
| `TASK_PREMISE_DEPENDENT` | The objection contrasts the candidate's statement with the task's assertion (and is not about output format), or cites the task as its basis | no |
| `REQUIRES_EXTERNAL_VALIDATION` | `EXTERNAL_FACT` without executed evidence of this candidate cited | no |

**How the gate uses grounding.**
- Only decisive findings count as fatal, major, `REJECT` or `REVISE` reasons, or become weaknesses.
- When every fatal or major issue of a judgment is non-decisive, that judgment's negative verdict, action and scores do
  not drive `REVISE`/`REJECT`.
- Non-decisive findings are recorded in `judge_groundings` and `fatal_issues` (with their grounding), and listed as
  uncertainty.
- Rollback can therefore no longer be caused by a misattributed finding.
- Evidence integrity ignores non-decisive issues as opposing stances.
- Grounded defects, task-constraint violations and failed executed checks keep their full effect.

## 8. Minimal provenance semantics

`quality.state.Provenance` has these values:
- `TASK_PROVIDED`, `CANDIDATE`, `ENGINE_DERIVED`;
- `EXECUTED_CHECK`, `REGISTERED_EVIDENCE`;
- `MODEL_JUDGMENT`, `MODEL_CONSENSUS`, `REPORTED_CONSENSUS`;
- `UNKNOWN`.

Existing evidence types map onto it: `EXECUTED_EVIDENCE` is `EXECUTED_CHECK`, and `MODEL_JUDGMENT` is
`MODEL_JUDGMENT`. It does not create a parallel ontology.

**Consensus.** A model-set claim status whose stated support is agreement gets `ClaimIntegrity.consensus`
(`REPORTED_CONSENSUS` or `MODEL_CONSENSUS`). Its reason says it is agreement, not verification. It adds the
uncertainty "Agreement is recorded as consensus, not verification", and it is never verified by agreement.

## 9. Regression tests (`tests/test_v035_regressions.py`, 18 tests, all SYNTHETIC)

| Case | What it checks |
|---|---|
| R1 | An unknown weakness in a critique gets one repair. Invalid elements are discarded, the loop continues, and no weakness is named "completeness". The repair request lists the allowed IDs. A repaired variant is also tested. |
| R2 | Unknown targets in a revision plan are removed. A change with only unknown targets is discarded, never re-mapped. |
| R3 | An unknown (`C0`) and a duplicate verification update are rejected; the valid `W001` update is applied. |
| R4 | Repeated invalid output stops after exactly 1, 2 or 3 calls for repair settings 0, 1 or 2, as `MODEL_PROTOCOL_FAILURE`, with a persisted trace. Reference failures are also bounded. |
| R5 | Real provider failures (RuntimeError, ConnectionError, TimeoutError) stay `EXTERNAL_BLOCKER` with no repair. |
| Branch | A forbidden adoption is repaired or discarded and never applied. A provider failure in synthesis still raises. |
| R6 | Native C0's request is the task verbatim; the answer keeps the task's JSON format. |
| R7 | Internals never enter the native revision prompt. A leaking candidate gets `REVISE`, and the clean C0 is returned. |
| C0 A/B | The same scripted answer in both modes: metadata stays separate, the structured request is unchanged from v0.3.4, and sidecar records round-trip. **This checks separation only, not quality.** |
| R8 | Task code attributed to the candidate is `MISATTRIBUTED`: no `REJECT`, rollback or weakness, and the incident is recorded. |
| R11 | The same objection on a candidate that does contain the code is still `REJECT`, with or without a quote. |
| R9 | A premise contradiction is `TASK_PREMISE_DEPENDENT`, and an unsupported `EXTERNAL_FACT` is non-decisive. With an executed check cited, it is decisive. |
| R12 | A real task-constraint violation still gives `REVISE` (judge finding and engine format check). A format contrast is not treated as a premise. |
| R10 | Agreement is recorded as consensus, never verified. An answer saying "independently confirmed" caps an otherwise executed-evidence-backed run at provisional. Plain reporting ("both engineers wrote…") is not flagged. |
| Other | Ungrounded quotes; typed judge sources; native mode is opt-in; protocol errors remain `ValueError`. |

## 10. Existing tests changed

One test changed, in `tests/test_end_engine.py`: `test_malformed_output_is_retained_and_stops_cleanly`.

| | |
|---|---|
| Old expectation | One malformed critique gives `EXTERNAL_BLOCKER`. |
| Why Alpha disproved it | A model's malformed output is not an external dependency failure. Treating it as one ended 22 of 24 FULL_END runs. |
| New expectation | It gets one bounded repair; if that is malformed too, the run is `MODEL_PROTOCOL_FAILURE` with category `MODEL_PROTOCOL_REPAIR_EXHAUSTED`. |
| Kept from the old test | Both outputs are retained and the trajectory persists. |
| Why it is safer | Failures are categorized truthfully and recovered within a bound. |

No other existing test was modified, and all of them pass.

## 11. Serialization and schema compatibility

- **Schema version.** Unchanged at `3.0`. Every change is additive:
  - trajectory collections `protocol_events`, `judge_groundings` and `engine_checks`;
  - `termination.category` and `errors[].category`;
  - optional judge-issue fields `claim_type`, `candidate_quote`, `task_reference`, `grounding` and `decisive`;
  - `ClaimIntegrity.consensus`.
- **Old records.** v1.0, v2.0 and 3.0 records still load (the existing schema tests pass).
- **New `StopReason.MODEL_PROTOCOL_FAILURE`.** A consumer that only knows the old values sees a new string.
- **Harness (read-only, 148/149).** Its tree hashes were unchanged before and after the run. One test,
  `test_preflight_failure_blocks_all_later_live_work_in_plan`, expects exactly 3 provider calls when every structured
  response is malformed. v0.3.5's default bounded repair makes 4. The Harness still reaches `BLOCKED` as before.
  Setting `EngineConfig(protocol_repair_attempts=0)` restores v0.3.4 call accounting exactly. The Harness was not
  modified.

## 12. Final test counts

| Suite | Before | After |
|---|---|---|
| Engine (`tests/`) | 164/164 | **182/182** (164 existing, 1 changed, plus 18 new) |
| v0.3.5 regression suite | — | **18/18** |
| Benchmark Alpha infrastructure | 18/18 | **18/18** |
| Harness (read-only, through its runner) | 149/149 (on v0.3.4) | 148/149 (see §11) |

**Other checks:**
- **Deterministic demos.** `demo`, `demo_v02` and `demo_v03` all run, writing to a scratch directory. `demo_v03` still
  accepts C3 with `ACCEPT_VERIFIED` (`validation_v035/deterministic-demos.txt`).
- **Synthetic Alpha scenarios.** Re-run into a scratch directory, they produced the same tags as under v0.3.4.
- **Alpha immutability.** All 836 Benchmark Alpha files are byte-identical before and after
  (`validation_v035/alpha-immutability.txt`).
- **No live run.** No Benchmark Beta run and no live model call took place.

## 13. Source fingerprint

| | Version | Fingerprint (`end_engine/**/*.py` + `pyproject.toml`) |
|---|---|---|
| Before | 0.3.4 | `d1a9f68bb8cacf1e4dc4384180d5b6971bebb8209b34ea50f1bb94939ceed7a2` |
| **After** | **0.3.5** | **`520d2052832eaee93f7c8931e028762c7008006ae61f2fdc7ec6589d7e4bd448`** (55 files) |

**Changed files** (git, against `6b2ff6e`, LF line endings as committed): +490/−86 lines across these files.
- **Engine:**
  - `engine.py`, `config.py`;
  - `core/state.py`, `core/weaknesses.py`, `core/revision_planner.py`;
  - `cognition/branches.py`, `cognition/knowledge.py`;
  - `models/recording.py`, `operators/base.py`, `experience/schema.py`, `verification/llm_verifier.py`;
  - `quality/state.py`, `quality/schema.py`, `quality/judges.py`, `quality/providers.py`, `quality/session.py`,
    `quality/gate.py`, `quality/integrity.py`.
- **Other:** `pyproject.toml`, `tests/test_end_engine.py`.

**New files:**
- `end_engine/models/protocol.py`, `end_engine/quality/grounding.py`, `end_engine/core/output_format.py`;
- `tests/test_v035_regressions.py`;
- `benchmark_beta/PLAN.md`;
- `validation_v035/`;
- `IMPLEMENTATION_REPORT_v0.3.4.md` (a preserved copy), and this report.

`README.md` was also updated.

**A process note.** Intermediate edit scripts wrote CRLF line endings. They were restored to the repository's LF
convention before the final tests and fingerprint.

## 14. Known limitations

- **Unproven.** Nothing here shows better answers. Benchmark Beta must measure blockers, cycles, pass rate, C0 quality
  and the three judgment failures.
- **The default generation path is unchanged.** C0 degradation in structured mode remains; the fix is the opt-in native
  mode.
- **The grounding heuristics are deliberately narrow.** They are verbatim quote matching, backtick spans of 12 or more
  characters, and phrase patterns for task-premise reliance and format constraints. Judges can still word a
  premise-based objection in ways the patterns miss, or label a constraint finding so that it is treated as a premise.
- **Consensus detection is phrase-based.** It covers only explicit agreement wording.
- **Repairs cost model calls**, and they change call accounting for integrations (§11).
- **Provider-side validation stays external.** A transport that validates JSON itself and raises its own error, as the
  Harness's Ollama adapter does, is still an external failure unless it raises `ModelProtocolError`.
- **`MODEL_PROTOCOL_UNGROUNDED_FINDING`** is reserved and not raised; ungrounded findings are handled by grounding.

## 15. Benchmark Beta plan

`benchmark_beta/PLAN.md` describes:
- the same tasks (hash `9e177f6d…`), evaluators (`alpha-3`), model and settings as Alpha;
- the measures to compare against Alpha's values;
- run options (96 to 120 runs, about 5–7 hours locally).

**Open decision:** whether Beta's END conditions use native generation, structured generation, or both. Beta needs
separate authorization.
