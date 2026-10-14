# END Engine v0.3.4 implementation report

- **Date:** 2026-09-30.
- **Scope:** an offline review of the 0.3.3 evidence-integrity implementation, focused on scope provenance and final
  rollback reporting. It fixes three defects the review demonstrated.
- **Earlier reports:** the 0.3.3 report is preserved byte-identical as
  [IMPLEMENTATION_REPORT_v0.3.3.md](IMPLEMENTATION_REPORT_v0.3.3.md), next to the older ones.
- **What was not done:** no live model call, download, new provider, budget or threshold change, or Harness edit, and no
  change to historical evidence.
- **Harness left unchanged:** the SHA-256 of all 335 Harness files, including both preserved smokes, is identical before
  and after (`validation_v034/harness-unchanged.txt`).
- **Terminology:** these checks are not hallucination detection or fact-checking. They check how model statements use
  evidence recorded in the run. The README now describes the actual coverage and the remaining gaps.

## Identification

| | Version | Source fingerprint (`end_engine/**/*.py` + `pyproject.toml`, computed by the Harness's `_source_identity`) |
|---|---|---|
| Before | 0.3.3 | `3e57f6753d880bb54190a27b58640e5fdf853c56f9b6cd4bc92d44fbd01076f9` (matches the 0.3.3 report) |
| **After** | **0.3.4** | **`d1a9f68bb8cacf1e4dc4384180d5b6971bebb8209b34ea50f1bb94939ceed7a2`** |

**Baseline:** **154/154 OK** on Python 3.12.1, run with `-B`, `PYTHONDONTWRITEBYTECODE=1` and a working directory
outside the tree (`validation_v034/engine-tests-before.txt`). The project requires Python ≥ 3.11. The default `python`
on this PATH is 3.10, which also passed 154/154 but was not used for any record.

## 1. Where CL001's trusted scope comes from

The record is smoke `8b553c71`, trajectory SHA-256 `cac07b1b…4a1`, Engine 0.3.2. CL001's text is "The declared
development checks pass for this task input."

| Origin | Fields |
|---|---|
| **Recorded in the original run** | **Claim creation.** `claim_discovered` CL001 at step 3, one step after candidate C0, with no model call in between. The configuration records `components.claim_extractor = "CheckBinding"`. |
| | **Receipt `02941036…`.** Check `scheduling.development` v1, `PASS`. `supported_scopes = [<CL001 text>]`, `targets = ["CL001"]`. Bound to C0 and to the artifact `3e3c4b8f…`. Its observations say "development subset only; PASS is not final task success". |
| | **`verifier_evidence` (step 11).** Targets `["CL001"]`. **No contract, and no phase.** |
| | **Claim validation.** `claim_validation` `SUPPORTED` (step 16). |
| **Trusted application configuration** (Harness code, not a model) | `tasks.DEV_SCOPE` (the CL001 text). |
| | `task_binding(task)` is a `CheckBinding(scopes=(DEV_SCOPE,))`. It is used both as the claim extractor and as the claim-to-check mapping. |
| | `development_registry` registers `supported_scopes=(DEV_SCOPE,)`. |
| | `development_check` checks only the schema, job IDs and precedence. |
| | `HarnessToolVerifier.mappings` maps by exact text. `CheckExecutor` sets `targets` only for mapped claims whose scope the checker returned, and `validate_receipt` checks that again. |
| **Introduced by the replay fixture** | Only labels: `_label`, the source hash and the Engine identity. |
| | The candidates, receipts, judgments and adversarial judgments are byte-equal to the trajectory (checked). No contract, phase or scope was added. |
| | The replay *test's* gate call supplies a synthetic `VerificationResult` and no cognitive state. That is a reconstruction of gate inputs, not history. |

**A correction to the 0.3.3 report.** The 0.3.3 report said "Harness receipts do not declare scope." That is imprecise:
receipts declare `supported_scopes` and `targets`. What END lacks is a `CheckContract` (phase, declared statements and an
artifact hash in END's terms), and END receives only `targets`.

**Verdict: CL001's `verified` status is justified, narrowly.**
- Why it holds:
  - The claim is literally the checker's registered scope statement.
  - Trusted code mapped it by exact text.
  - The PASS is bound to C0.
- Its limits:
  - It says nothing about capacity or horizon, and C0's gate correctly stays `ACCEPT_PROVISIONALLY`.
  - The justification rests on trusted Harness configuration. END cannot see that scope in the evidence it receives.

**The four properties the review was asked to confirm:**

| Property | Result in 0.3.3 | Now |
|---|---|---|
| A receipt's existence alone does not prove support | Held for claims (support needs `targets`). **Failed at the gate:** a PASS covering nothing gave `ACCEPT_VERIFIED`. | Fixed (defect 2) |
| Model-supplied targets, statements, phase or scope cannot expand coverage | Targets, phase and contract come only from trusted tool code. **Failed for claim status:** a model could present its own `NOT_APPLICABLE` as Engine-written. | Fixed (defect 1) |
| Missing scope cannot silently become full-task verification | **Failed:** a check with no targets and no contract gave `ACCEPTED_HIGH_CONFIDENCE`. | Fixed (defect 2). The narrow final-scope phrase list remains a documented gap. |
| A legitimate narrow claim stays supported by a trusted contract | Held | Still held. Covered by positive tests, and CL001 is still `verified` in both reassessments. |

## 2. Integrity reporting after rollback

**Reproduction (SYNTHETIC, offline).** Candidates C0, C1 and C2 are byte-identical. C0 is `ACCEPT_VERIFIED`. C1's
adversarial judge raises a minor issue targeting CL001. C1 is `ACCEPT_PROVISIONALLY` with "Contradictory evidence…
CL001", and the run returns C0.

In 0.3.3 the following all showed nothing of C1's finding:
- the final gate (`ACCEPT_VERIFIED`, `ACCEPTED_HIGH_CONFIDENCE`);
- `scorecard.known_uncertainties`, `scorecard.unresolved_concerns` and `scorecard.evidence_integrity`;
- the reconciliation record (`changed: false`).

The same happened with a trusted check that failed on C1's identical bytes: C1 was `REVISE`, C0 was returned
`ACCEPT_VERIFIED`, and the failure was invisible.

**The correction.** `identical_content_findings` in `integrity.py` is called from `reconcile`. It does not transfer
findings merely because the bytes match:

| Finding on a byte-identical sibling | Treatment |
|---|---|
| Contradiction about a claim or concern, or a trusted check of a claim that failed | Content-related. It stays unresolved and visible in `final_reconciliation.integrity_findings.applicable`, `scorecard.evidence_integrity.identical_content_findings` and the reconciled reasons. It caps acceptance at `ACCEPT_PROVISIONALLY` and is never converted into a failure. Applicability is `demonstrated` when the failed check binds this exact content (`artifact_sha256`), and `undetermined` otherwise. |
| The same finding, when the concern was later resolved on that content by a transition audited `VALID` | `resolved_later`; no cap |
| Citation error by the sibling's judge (`wrong_candidate`, `nonexistent`) | Listed in `not_transferred` (kind `evidence_integrity`, category `citation`), not applied |
| Out-of-scope statement by the sibling's judge | Listed (`statement_scope`) |
| The sibling's check was bound to a different artifact, or a claim status or mapping in its scope | Listed (`process`, `claim_status`) |

**What stays exactly as recorded:**
- candidate selection;
- rollback events;
- historical `quality_gate_decisions` and `evidence_integrity` records;
- termination causes.

Tests cover each of these, including an explicit C1→C0 rollback caused by a `REJECT`.

## 3. OFFLINE_REASSESSMENT of the preserved smokes

`validation_v034/offline_reassessment.py` produces `offline-reassessment.json` and `.txt`. It opens both trajectories
read-only and hashes them. Recorded judgments go through the real judge parser, recorded receipts are used as recorded,
and the current `ClaimValidator`, `ResolutionAuditor`, `EvidenceIntegrity` and `identical_content_findings` do the rest.

| Smoke (Engine at record) | Historical | OFFLINE_REASSESSMENT (0.3.4) | Differences explained |
|---|---|---|---|
| `8b553c71` (0.3.2), C0/C1 identical | `ACCEPTED_PROVISIONALLY`, gate `ACCEPT_PROVISIONALLY`, returns C0 | Same decision. **C0** has CL001 `verified`; `AJ001.uncertainties[0]` is `unsupported` (it cites the development receipt for "…fully satisfied"). **C1** is clean. Nothing identical-content applies. | One added reason: "Evidence used outside its checked scope was not counted: AJ001.uncertainties[0]". It is the 0.3.3 scope rule, and 0.3.4 changes nothing here. |
| `71532008` (0.3.0), C0/C1 identical | `EXTERNAL_BLOCKER` (Harness `model_attempts_exhausted`), final `BLOCKED`/`INCOMPLETE`, C0 returned | **C0** and **C1** have no integrity findings. All four judge citations resolve `valid`. The final stays `BLOCKED`/`INCOMPLETE` with no added reason. | None from integrity. One **non-integrity** difference: under the 0.3.1 policy, C1's `W001` `accepted_risk` audits `WEAKLY_SUPPORTED`, not the recorded `INVALID`. C1's recorded `REVISE` is therefore not re-derived. |

The validations re-computed for all four evaluations equal the recorded ones. There are no new `unresolved` or
`wrong_candidate` findings in real Gemini text, which answers the 0.3.3 report's recommendation.

**Limitations of the reassessment.**
- **The gate is derived, not re-executed.** The live cognitive-state object and some gate inputs were not persisted.
  Because integrity only adds uncertainties after every `REVISE`/`REJECT`/`BLOCKED` return, an `ACCEPT_*` decision gains
  them and any other decision is unaffected. The derivation relies on that.
- **Reconstructed inputs, kept separate in the output:**
  - which claim-status updates the Engine wrote (from step order);
  - the claim, weakness and assumption state at each evaluation.
- **No hypothetical inputs are used.** The SYNTHETIC mutations remain only in the tests.
- **The runs never exercised the paths these fixes target.** In both runs no judge issue targeted a recorded ID, so
  contradiction handling has never met real judge output.

## 4. Defects fixed

Each fix has a regression test written before the fix. `validation_v034/regression-tests-on-pristine-0.3.3.txt` runs
the **final** tests against a pristine 0.3.3 source, rebuilt by reversing these edits; its fingerprint equals
`3e57f675…`. On that source exactly these 9 tests fail and the other 155 pass.

| # | Defect | Fix | Tests (negative, then positive) |
|---|---|---|---|
| 1 | **Claim-status provenance by wording.** `integrity.py` treated any claim evidence starting "Executed evidence references: " as Engine-written. A critique `claim_updates` entry setting `NOT_APPLICABLE` with that prefix, even citing an invented `E-C0-9`, turned a provisional run into `ACCEPT_VERIFIED`. | `QualitySession` records the exact `(claim, status, evidence)` updates it wrote. `assess(..., engine_evidence=)` uses only those; any other status is model-set, and its references are resolved. | `test_engine_wording_does_not_make_model_status_engine_written`, `test_critique_cannot_disguise_non_applicability_as_engine_support`; positive: `test_status_written_by_the_engine_keeps_engine_provenance`, plus the verified control run |
| 2 | **A receipt covering nothing gave verified acceptance.** An executed PASS with no targets, or with a target naming nothing recorded, satisfied "executed evidence attached". | The integrity uncertainty "Executed checks cover no recorded claim or concern: …" is added when no untampered PASS targets a recorded claim, weakness or assumption. It caps at provisional and is never a failure. | `test_receipt_covering_nothing_does_not_permit_verified_acceptance`; positive: `test_narrowly_scoped_coverage_still_verifies` (a claim target, and a weakness target) |
| 3 | **Integrity findings of byte-identical candidates were invisible after the run returned C0.** | `identical_content_findings`, as described in section 2 | `test_content_contradiction_on_identical_candidate_stays_visible`, `test_explicit_rollback_keeps_rollback_and_reports_applicable_conflict`, `test_failed_check_bound_to_identical_content_is_applicable`; negative: `test_judge_citation_errors_and_process_failures_are_listed_not_transferred`, `test_contradiction_resolved_later_by_validated_transition_is_not_reraised` |

**Existing tests changed (fixtures only, because of defect 2).** Four tests used an untargeted check as their "verified"
control. Each now targets a trusted claim through a `claim_extractor`, and every assertion is unchanged. All four also
pass on pristine 0.3.3.
- `test_quality.test_complete_verified_acceptance_requires_tool_evidence`
- `test_final_reconciliation.test_accepted_low_risk_stays_visible_and_blocks_verified_acceptance`
- `test_final_reconciliation.test_judgment_of_identical_content_is_reported_as_undetermined_not_transferred`
- `test_evidence_integrity.LifecycleTests.test_invented_judge_citation_no_longer_aborts_the_run_and_blocks_verified`

The `run_engine` helpers gained an optional `claim_extractor` argument.

**Two expectations corrected while the tests were being written.** Neither was a behaviour change; both are stricter
than first written.
- In the live spoof run, the model's `E-C0-1` is cited while C1 is being evaluated, so it is correctly
  `wrong_candidate`.
- A check bound to a different artifact is also listed as `claim_status`.

## Tests

- **Engine: 164/164 OK** (`validation_v034/engine-tests-after.txt`): 154 existing tests plus 10 new ones in
  `tests/test_integrity_review.py`. No `__pycache__` was created.
- **Harness: 149/149 OK** through its supported runner, `tools/run_tests.py --engine-source "E:\The End Engine"`, run
  from outside the Harness tree (`validation_v034/harness-tests.txt`). The controlled load recorded Engine **0.3.4**,
  source `d1a9f68b…ced7a2`.

## Changed files

**Source:**
- `end_engine/quality/integrity.py` (+89/−8): provenance, coverage uncertainty, `identical_content_findings`, and a
  corrected docstring;
- `end_engine/quality/session.py` (+25/−7): records Engine-written updates, extends `reconcile`, adds a scorecard field;
- `pyproject.toml`: 0.3.4.

**Tests:**
- new `tests/test_integrity_review.py`;
- fixture-only edits in `tests/test_quality.py`, `tests/test_final_reconciliation.py` and
  `tests/test_evidence_integrity.py`.

**Documentation:**
- `README.md`: the corrected integrity section, with coverage and remaining gaps;
- this report;
- `IMPLEMENTATION_REPORT_v0.3.3.md` (a copy of the previous report).

**Validation records:** `validation_v034/`.

## Compatibility

- **Additive fields:**
  - `final_reconciliation.integrity_findings`;
  - `not_transferred` entries of kind `evidence_integrity`;
  - `scorecard.evidence_integrity.identical_content_findings`;
  - `EvidenceIntegrity.assess(engine_evidence=())`.
- The trajectory schema stays `3.0`, and older trajectories load as before.
- **Callers of `assess` that omit `engine_evidence`** now treat prefixed evidence text as model-written. This is safe:
  it never grants trust.
- **Intended behaviour changes:**
  - A run whose executed checks cover nothing recorded, and a returned candidate with applicable sibling conflicts, are
    now `ACCEPT_PROVISIONALLY` instead of `ACCEPT_VERIFIED`.
  - Nothing becomes `REVISE`, `REJECT` or `BLOCKED` because of these changes.
- **Harness 0.3.2 as used in the smokes** is unaffected: its receipts always target the mapped scope claim.

## Out-of-scope observation (not changed)

`tests/fixtures/recorded_71532008_audit.json` labels `a397aeeb…` as `engine_source_sha256_at_record`. That value is
the 0.3.0 *tree manifest* hash. The smoke manifest records the source fingerprint as `11895bb9…`. This is a labelling
error in a 0.3.1 test extract; no test depends on it.

## Recommendation: another live smoke is not warranted now

Another live integration smoke would add little useful evidence about these changes:
- **The fixes are deterministic** and fully exercised offline. The paths they touch are these, and a live run cannot
  be steered into any of them within the authorized budget:
  - model-written claim updates that imitate Engine wording;
  - untargeted receipts, which the Harness never emits;
  - conflicts on byte-identical siblings.
- **Both smokes already give the evidence a live run would add:**
  - the real judge text replays without false positives;
  - the recorded decisions are unchanged apart from the documented scope reason.

The largest remaining unknown is whether real judges ever target recorded IDs; in both runs they never did, so
contradiction handling has not met real output. One more smoke would be weak evidence on that point. If that becomes
the question, it is better answered by offline replay of existing records, or by a separately authorized run with
unchanged limits.
