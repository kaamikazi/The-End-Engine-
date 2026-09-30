# END Engine v0.3.3 implementation report

- **Date:** 2026-09-30.
- **Scope:** focused evidence-integrity protections against hallucinated or unsupported claims.
- **Earlier reports:** preserved unchanged as [IMPLEMENTATION_REPORT_v0.3.2.md](IMPLEMENTATION_REPORT_v0.3.2.md), [_v0.3.1](IMPLEMENTATION_REPORT_v0.3.1.md) and [_v0.3](IMPLEMENTATION_REPORT_v0.3.md).
- **Before editing:** the 0.3.2 baseline of **135/135** passed (`validation_v033/engine-tests-before.txt`), and the tree was snapshotted (`validation_v033/engine-tree-before.json`, 166 files).
- **What was not done:**
  - no live model calls, no smoke;
  - no web search, browsing or database;
  - no budget, threshold, termination, selection or rollback changes;
  - no Harness changes, and no second Harness gate.
- **Integrity of other directories:**
  - The Harness tree and the preserved smoke `output/antigravity-smoke-v032/8b553c71-…` were unchanged: the file list, sizes and mtimes of the Harness, and the SHA-256 of all 22 smoke files, match before and after.
  - The replay fixture is a read-only extract.

## Identification

| | Version | Source fingerprint (`end_engine/**/*.py` + `pyproject.toml`, computed by the Harness's controlled load) |
|---|---|---|
| Before | 0.3.2 | `5ea97d2f7170a8d4d928d9e088b6d3d0f6d3425cdea5f28628ac545c8db5c314` |
| **After** | **0.3.3** | **`3e57f6753d880bb54190a27b58640e5fdf853c56f9b6cd4bc92d44fbd01076f9`** |

**Changed** (101 changed source lines, plus the new module):

| File | Change |
|---|---|
| `end_engine/quality/state.py` | `CheckContract`; `EvidenceArtifact.contract`, `ClaimValidationResult.out_of_scope_artifacts` and `Judgment.unresolved_evidence`, all additive with defaults |
| `end_engine/quality/audits.py` | scope-aware `ClaimValidator`; a transition is not validated by a check of a different artifact |
| `end_engine/quality/judges.py` | an unknown citation is kept and flagged instead of raising; a missing contract is left out of the judge context |
| `end_engine/quality/gate.py` | optional `integrity` input, which adds uncertainties only |
| `end_engine/quality/session.py` | runs and records integrity; validates contracts; adds `scorecard.evidence_integrity`; de-duplicates `known_uncertainties` |
| `end_engine/verification/tool_verifier.py` | `ToolCheck.contract`, validated |
| `end_engine/experience/schema.py` | new `evidence_integrity` collection |
| `pyproject.toml` | version 0.3.3 |
| `README.md` | documentation |
| `tests/test_quality.py` | one test replaced; see "Tests" |

- **Added:**
  - `end_engine/quality/integrity.py`;
  - `tests/test_evidence_integrity.py`;
  - `tests/fixtures/recorded_8b553c71_integrity.json`;
  - `validation_v033/`;
  - `IMPLEMENTATION_REPORT_v0.3.2.md`.
- The trajectory schema stays `3.0`. The new keys and step are additive, and older trajectories still load.

## Evidence model

**Trusted evidence.** Only an `EXECUTED_EVIDENCE` artifact that the configured tool verifier produced for the candidate being evaluated counts. The tool verifier is trusted code: the Harness check executor, or a `CallableToolVerifier` callback. The session already rejects evidence bound to another candidate or of an unknown type, and now also rejects a malformed contract.

A PASS supports claim X only if all of the following hold:

1. X's ID is in the artifact's `targets`.
2. If the optional `CheckContract.artifact_sha256` is set, it equals the SHA-256 of the candidate's exact UTF-8 content. Otherwise the artifact supports nothing, and "Executed evidence checked a different artifact" is added.
3. If `CheckContract.claims` is non-empty, X's normalized text is one of those declared statements.
4. If X is a final-task or complete-correctness statement, the contract declares `phase="final"`. Evidence without a contract has an undeclared phase and never qualifies.

**Contradiction by a failed check.** A failed check contradicts X only when it is bound to this candidate and this artifact.

**Declared but not enforced.** `CheckContract.check_id`, `properties`, `version` and `bounds` are recorded and shown to judges, but not enforced. The artifact hash already binds the checked version of the candidate.

**Legacy evidence.** Evidence without a contract, such as current Harness receipts, keeps its 0.3.2 target-based meaning, with an undeclared phase. The Harness already assigns targets only by exact trusted scope text.

**Model-reported (never trusted):**
- judge verdicts, scores, confidences, uncertainties and issue text;
- `MODEL_JUDGMENT` artifacts;
- statuses a model sets through critique `claims`/`claim_updates`, including `SUPPORTED` and `NOT_APPLICABLE`;
- risk acceptance;
- transition rationales;
- model agreement, which is recorded as corroboration only.

**Unknown (not visible to END):**
- anything the checker did not declare;
- final-task outcomes. The Harness's reference evaluation runs after submission and is never visible to END.
- the underlying model activity behind a provider invocation.

**States** (each claim or statement keeps the path in `history`; the last entry is its status):
- `model_claimed`, then `evidence_referenced`, then `evidence_validated`, then `checker_supported`, then `verified`;
- or it ends in `unresolved` or `unsupported`.
- `evidence_referenced` and `checker_supported` are intermediate. `verified` is reached only by a claim with an in-scope trusted PASS and no contradiction.

**References.**
- **Sources scanned:** judge evidence lists, issue evidence and text, judge uncertainties, model-authored claim evidence, and transition rationales made on this candidate.
- **Forms recognised:** execution UUIDs, `receipts/….json` sources, hashes of 12 to 64 hex characters, END IDs (`E-C…`, `AT…`, `J…`, `AJ…`, `CL…`, `W…`, `A…`) and `step N`.
- **Resolution:** each is resolved against the recorded `verifier_evidence`, candidates, tests, judgments, claims, weaknesses, assumptions and step count. The result is `valid`, `nonexistent`, `wrong_candidate` or `wrong_artifact`.
- **Not transferred by identical content:** a reference to another candidate's record is `wrong_candidate` even when the two contents are byte-identical.

**Contradictions.** For each claim, weakness or assumption ID:
- **Support:** in-scope trusted PASSes, and PASS judgments citing an artifact that targets the ID.
- **Opposition:** trusted FAILs on this artifact, and judge issues of any severity that target the ID.

When both exist, END records the conflict with both sides. It never selects a side by order, recency or confidence; a test shows that reversing the order gives the same result.

## How the gate uses it

- **Uncertainties added.** Integrity adds these to the existing uncertainty list, so each caps the decision at `ACCEPT_PROVISIONALLY`:
  - "Unresolved evidence references kept as cited…";
  - "Evidence used outside its checked scope was not counted…";
  - "Contradictory evidence or judgments remain unresolved…";
  - "Model-asserted claim status has no trusted evidence…";
  - "Executed evidence checked a different artifact…".
- **No new failures.** Integrity never adds a `REVISE`, `REJECT` or `BLOCKED` reason. Missing or invalid evidence is therefore never turned into a fabricated failure.
- **Existing rules still apply unchanged.** A real failed check gives `REVISE`, or `REJECT` for a HIGH claim. Judge findings, disputes and thresholds are unchanged.
- **Engine authority is unchanged:** acceptance, rollback, candidate selection, budgets, termination reasons and the 0.3.2 reconciliation. The gate result feeds candidate ranking as before.
- **Final result and scorecard.** `scorecard.evidence_integrity` reports the returned candidate's view:
  - `not_verified`, with a reason for each item;
  - `unresolved_references`, `contradictions`, `trusted_evidence` and `model_agreement`;
  - `accepted_risks`;
  - `blocks_verified_acceptance`.

  Records of other candidates stay in the `evidence_integrity` collection.

## Claims now blocked or kept unresolved (offline examples)

`validation_v033/integrity-before-after.txt` runs the same SYNTHETIC scenarios through the pristine 0.3.2 copy and through 0.3.3:

| Scenario | 0.3.2 | 0.3.3 |
|---|---|---|
| A development PASS targets "The schedule passes the final evaluation." | `ACCEPT_VERIFIED` | `ACCEPT_PROVISIONALLY`; the claim is `unsupported` (development-scope evidence cannot support a final-task claim) |
| A judge cites nonexistent `E-C0-9` | `ValueError`. In a run this gives `EXTERNAL_BLOCKER`/`BLOCKED` with 0 judgments recorded (checked on the pristine copy). | The run continues. The judgment is kept with `unresolved_evidence: ["E-C0-9"]` and the reference is `nonexistent`. The result is `ACCEPT_PROVISIONALLY`. |
| A checker PASS on CL001, while an adversarial *minor* issue targets CL001 | `ACCEPT_VERIFIED` | `ACCEPT_PROVISIONALLY`; the contradiction is recorded with both sides, and CL001 is `unresolved` |
| The model sets CL001 to `NOT_APPLICABLE` with an explanation only | `ACCEPT_VERIFIED` | `ACCEPT_PROVISIONALLY`; `model_claimed` |
| A judge says "E-C0-1 shows all constraints are satisfied" (E-C0-1 is a development check) | `ACCEPT_PROVISIONALLY` (as a plain judge uncertainty) | still provisional; the statement is now explicitly `unsupported` (scope) |

These are also covered by tests:
- a PASS targeting a claim outside the contract's declared statements gives `unsupported`;
- a PASS bound to a different artifact hash supports nothing;
- a claim citing an invented execution UUID is `unresolved`;
- two or three agreeing judges plus a `MODEL_JUDGMENT` artifact give `evidence_validated`, never `verified`;
- an accepted risk stays `unresolved`.

**OFFLINE REPLAY of smoke 8b553c71** (recorded C0, receipt `02941036-e406-4136-8cb8-e25f8eafc920`, J001 and AJ001 replayed through the real judge parser, validator, integrity and gate):
- CL001 "The declared development checks pass for this task input." is `verified`: a development claim inside development scope.
- AJ001's uncertainty ("…independent evaluation confirmed resource capacity and horizon constraints are fully satisfied.") is preserved verbatim, and is `unsupported`: it cites a valid receipt, but the receipt is development-scope and the statement is about complete correctness.
- The gate is `ACCEPT_PROVISIONALLY`, as recorded. It keeps both recorded reasons and adds "Evidence used outside its checked scope was not counted: AJ001.uncertainties[0]".

SYNTHETIC mutations of that replay:
- Mapping the receipt onto "Resource capacity and horizon constraints are fully satisfied." gives `unsupported`.
- C1's judge citing C0's receipt gives `wrong_candidate`, even though C0 and C1 are byte-identical.

## Tests

- **Engine: 154/154 OK**, run with `-B`, `PYTHONDONTWRITEBYTECODE=1` and a working directory outside the tree (`validation_v033/engine-tests-after.txt`).
  - That is the 135 baseline tests, one of them replaced, plus 19 new tests in `tests/test_evidence_integrity.py`.
  - No `__pycache__` file was added.
- **Replaced test.** `test_unknown_judge_evidence_is_rejected` expected `CandidateJudge` to raise. It became `test_unknown_judge_evidence_is_kept_flagged_and_not_repaired`, which asserts that the citation is preserved as written and flagged. The run-level consequence is covered by a lifecycle test. This is the one intended behaviour change for existing callers.
- **New tests** (all offline; synthetic providers, plus the labelled replay):
  - a nonexistent reference;
  - a claim citing an invented receipt;
  - a valid reference to the wrong candidate, for both identical and different content;
  - a development PASS as final-task proof, with and without a contract, and the `phase="final"` counterpart;
  - development evidence cited for a complete-correctness statement;
  - a PASS outside the declared statements;
  - a check of a different artifact;
  - an invalid contract phase;
  - a narrowly scoped trusted claim, `verified` → `ACCEPT_VERIFIED`;
  - two agreeing judges with no trusted evidence;
  - model-asserted `NOT_APPLICABLE`;
  - a checker/judgment contradiction;
  - contradictory checks, independent of order;
  - an accepted risk;
  - a lifecycle run with an invented judge citation. The control reaches `ACCEPT_VERIFIED`; with the invented citation the run completes `ACCEPT_PROVISIONALLY` rather than `EXTERNAL_BLOCKER`.
  - a lifecycle rollback C1 → C0, where C0's unsupported claim stays listed in `scorecard.evidence_integrity`;
  - deployment acceptance and rollback unchanged: C3, `ACCEPT_VERIFIED`, nothing blocking;
  - two replay tests.
- **Unchanged behaviour** is covered by the existing reconciliation, audit-policy, budget and quality suites, all of which pass unmodified.
- **Harness compatibility:** **149/149 OK** against 0.3.3 (`validation_v033/harness-tests.txt`), using a Harness-controlled load that recorded version 0.3.3 and source `3e57f675…76f9`.
  - The Harness constructs `EvidenceArtifact` positionally with 7 fields, which remains valid.
  - Its receipts carry no contract, so they keep the 0.3.2 meaning.
  - Nothing in the Harness depended on the removed `ValueError`.
  - **Engine 0.3.3 is compatible with Harness 0.3.2 as used in the smoke.** The Harness itself was not changed.

## Known limitations

- **Bounded reference detection.** Only the explicit forms listed above are recognised. Prose such as "the earlier test" or a paraphrased artifact name is not treated as a citation. A short prefix of a hash or UUID (fewer than 12 hex characters) is not detected.
- **The final-scope pattern** is a short phrase list, not a fact checker. A final-task claim worded differently can still be supported by development evidence that targets it. The main protection remains that trusted code decides the `targets`.
- **Declared statements** in a contract match normalized exact text.
- **Unscanned texts.** Critique findings and weakness texts are not scanned. Weakness transitions audited in an earlier candidate's scope are not re-scanned.
- **Per-candidate scope.** Integrity is evaluated per candidate. Reconciliation does not carry integrity findings across byte-identical candidates, and later findings on identical content are not merged.
- **Harness evidence** has no contract yet. It cannot bind the artifact hash in END's terms: the Harness checks canonicalized JSON, whose hash can differ from the raw candidate bytes. It also cannot declare `phase="final"`, which is correct, because END never sees final evaluation.

## Recommendation before any future live run

The smallest useful offline review is to **replay the Engine 0.3.3 evaluation stage over both preserved smokes, read-only, and compare the gate outcomes and integrity records with the recorded ones**:

1. Extend the replay pattern in `tests/test_evidence_integrity.py` to the 0.3.0 smoke `71532008` (its judgments, receipts and claims).
2. Confirm that there is no new `unresolved` reference or `wrong_candidate` false positive in real Gemini judge text, for example UUIDs or hashes the judges quoted.
3. Confirm that no recorded decision becomes stricter for reasons other than documented scope rules.
4. Review `scorecard.evidence_integrity` of a synthetic Harness run for readability.

This needs no model call and no Harness change. Only after that review, and with explicit authorization, should a live smoke with unchanged limits be considered.
