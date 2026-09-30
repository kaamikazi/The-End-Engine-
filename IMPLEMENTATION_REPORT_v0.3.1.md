# END Engine v0.3.1 implementation report

- **Date:** 2026-09-30.
- **Scope:** a focused audit-policy fix. The v0.3 report is preserved unchanged as [IMPLEMENTATION_REPORT_v0.3.md](IMPLEMENTATION_REPORT_v0.3.md).
- **Before editing:** the full **115-test baseline passed**. The source was snapshotted: tree manifest `a397aeeb20d862da17e5fbb71e9e1a5a1e255a95bbe252de45da72b42c3963a3`, source fingerprint `11895bb98ac917622ac726dcced72f7e433ff10d503ba34e08a0c15ff835b4b9`.
- **What was not used:** no live model, no Harness smoke, no budget change. The END Harness and its experiment evidence were read only.

## Identification

| | Version | Source fingerprint (`end_engine/**/*.py` + `pyproject.toml`, as computed by the Harness) |
|---|---|---|
| Before | 0.3.0 | `11895bb98ac917622ac726dcced72f7e433ff10d503ba34e08a0c15ff835b4b9` |
| **After** | **0.3.1** | **`7a0b36decba87d3587699aa91f213c5279c812049632f37b865947ad3a0d6c16`** |

- The full-tree manifests are `validation_v031/engine-tree-before.json` and `validation_v031/engine-tree-after.json`.
- The identity and changed-file list are in `validation_v031/engine-identity.json`.
- The trajectory schema stays `3.0`. The new fields and step types are additive.

## Evidence: the diagnosis was confirmed, not assumed

The hypothesis came from the Harness diagnosis, `E:\The End Harness\output\diagnosis-71532008\`. I checked it against the preserved trajectory of live smoke `71532008`, reading it only (`validation_v031/recorded-chain-71532008.json`).

- C0 and C1 `content` are byte-identical.
- The critique raised W001: severity **low**, type `untested_guarantee`.
- The verifier moved W001 from `open` to `accepted_risk`, with a 206-character justification (step 38).
- `ResolutionAuditor` returned `INVALID`, "Status label lacks a supporting targeted revision or evidence". It accepts only executed evidence targeting W001, or a content change.
- `QualitySession` turned that INVALID audit into a non-fatal `JudgeIssue`, ingested at the fixed severity **"high"**, which became W002.
- W002 was in `high_severity_weaknesses` when C1's gate ran. The gate returned `REVISE`, even though both C1 judgments were `PASS` / `ACCEPT` with no issues and the C1 development evidence passed.
- A second cycle started. The 15th request then hit the Harness's 14-request cap.

A synthetic reconstruction run against the **pristine 0.3.0** source reproduces the same pattern: W002 is created as high, C1 is REVISE, 22 requests are used, and the run ends `BUDGET_EXHAUSTED`. The pattern is identical whether the justification is good, empty, or the concern is high severity.

## Policy (what changed)

### 1. Audit failures are procedural, not candidate defects (`quality/session.py`)

An `INVALID` resolution or assumption audit no longer creates a new weakness at the fixed severity "high". Instead, `QualitySession._reject_transition`:

- **Rejects the unsupported transition.**
  - A weakness is reopened (`open`) at **its own severity**, recorded as a `weakness_status_change` with `source: "resolution_audit"`. Its status reason reads "Unsupported transition to … rejected by audit: …".
  - An assumption is reset to `UNTESTED` through the normal knowledge update, and the reset is recorded.
- **Keeps the failure visible.**
  - It records an `audit_failure` step containing the target, kind, audited transition, criteria gaps, the action taken, the retained severity, and `new_weakness_created: false`.
  - The audit stays `INVALID` in `resolution_audits` / `assumption_audits`.
  - The trajectory judge still reports `resolution_integrity: LOW`.
  - The gate still adds the audit's reason to its `REVISE` reasons. That gate rule is unchanged.
- **Preserves escalation for serious concerns.** A reopened high or critical weakness still produces "Unresolved high-severity weaknesses remain" and keeps termination going. A reset HIGH/CRITICAL-risk assumption still produces "Severe assumptions remain untested".
- **Is not re-reported.** Because the revert is the latest transition for that target, the same unsupported transition is not audited again for later candidates.
- **Leaves judges' findings alone.** Major issues from judges still become `high` weaknesses, and fatal issues become `critical`.

### 2. Explicit criteria for accepting a risk without changing candidate bytes (`quality/audits.py`)

A weakness moved to `accepted_risk` without targeted executed evidence and without a targeted content revision is `WEAKLY_SUPPORTED` only if **all** of the following hold:

1. Severity is `low` or `medium`.
2. The justification has at least 40 characters after collapsing whitespace, and does not merely restate the concern.
3. No executed evidence for this candidate failed.
4. Both an independent judgment and an adversarial judgment **of this candidate** exist, and every one is `PASS` / `ACCEPT` with no fatal or major issues.

Otherwise the audit is `INVALID`, with the reason "Risk acceptance does not meet criteria: …" and the unmet `criteria_gaps`. The concern then stays unresolved, as described in section 1.

A non-empty explanation alone therefore never suffices. Corroborating judgment IDs are recorded in `corroborating_judgments`, and they are model judgments, never `supporting_artifacts`. `ResolutionAudit` gains the additive fields `transition`, `corroborating_judgments` and `criteria_gaps`.

These rules are unchanged: `resolved` or `invalidated` without a revision or evidence stays `INVALID`, the rule for a changed-and-targeted revision still gives `WEAKLY_SUPPORTED`, and targeted executed evidence still gives `VALID`.

### 3. An accepted risk is never verification (`quality/gate.py`)

If any `accepted_risk` / `ACCEPTED_RISK` transition is relied on (audited `VALID` or `WEAKLY_SUPPORTED`), the gate adds the uncertainty "Accepted risks remain unverified: <ids>". This caps the decision at `ACCEPT_PROVISIONALLY`, even when targeted executed evidence exists. Thresholds, decision order and all other rules are unchanged.

### Unchanged by design

- Minimum and mandatory revision cycles (`min_cycles`) and termination.
- Quality thresholds and confidence floors.
- Best-candidate selection and rollback.
- Budget semantics, and the mapping of external budget exceptions to `EXTERNAL_BLOCKER`.
- The Harness is not involved at all: there is no acceptance override, and post-run reference information is not visible to the Engine.

## Changed behaviour on the reported pattern

The synthetic reconstruction below uses `tests/test_audit_policy.py::ReportedScenarioGenerator` with a judge that shares the generator's model identity, as the live run did.

| Scenario | 0.3.0 | 0.3.1 |
|---|---|---|
| Low concern; justified `accepted_risk` corroborated by PASS judges; identical revision | W002 high created; C1 `REVISE`; 22 requests; `BUDGET_EXHAUSTED` | C1 audit `WEAKLY_SUPPORTED`; C1 gate `ACCEPT_PROVISIONALLY` with "Accepted risks remain unverified: W001"; **13 requests**; `ACCEPTED_PROVISIONALLY` |
| Same, with an empty or short justification ("Accepted.") | same as above | audit `INVALID`; W001 reopened at **low**; no meta-weakness; C1 `REVISE` for the audit reason; the concern stays open through later cycles |
| High concern with a justified `accepted_risk` | same as above | audit `INVALID` (severity requires revision or evidence); W001 reopened as **high**; C1 `REVISE` with "Unresolved high-severity weaknesses remain"; further cycle; `BUDGET_EXHAUSTED` from the cycle cap |

The recorded fragment of smoke `71532008` is replayed offline and labelled as such in `tests/fixtures/recorded_71532008_audit.json`. Under 0.3.0 it audited `INVALID`. It now audits `WEAKLY_SUPPORTED`, corroborated by `J002` and `AJ002`. Its gate is `ACCEPT_PROVISIONALLY`, with "Generator and judge share model identity" and "Accepted risks remain unverified: W001".

## Tests

- **Engine suite:** **127/127 OK** after the changes (115 existing plus 12 new), run with `-B`, `PYTHONDONTWRITEBYTECODE=1` and a working directory outside the tree. Logs are in `validation_v031/engine-tests-before.txt` and `validation_v031/engine-tests-after.txt`.
- **New tests** in `tests/test_audit_policy.py`. All are synthetic, except one labelled offline replay:
  - The reported low-severity concern on an unchanged candidate: the audit is `WEAKLY_SUPPORTED` and never verified, and the end-to-end run finishes in 13 requests.
  - Unsupported or empty accepted-risk justifications: empty, short, restating, uncorroborated, adversarial objection, missing adversarial judgment, failed executed evidence, and judgments of another candidate. All are `INVALID` with the matching gap, and the gate returns `REVISE`.
  - Genuine high or critical concerns: they cannot be risk-accepted, they escalate, and they remain unresolved end to end.
  - Audit failures stay visible without severity inflation: the weakness is reopened at its own severity, an `audit_failure` step is recorded, no `judge_feedback` weakness is created, the failure is not re-reported, and `resolution_integrity` is LOW.
  - The assumption path: at LOW risk it resets without escalation, and at HIGH risk it still escalates.
  - Judges' major issues still become `high` weaknesses.
  - Existing acceptance and rollback: the deployment scenario still returns C3 via rollback with `ACCEPT_VERIFIED`, and the `resolved`/`VALID` rules are unchanged.
  - The offline replay of the recorded audit fragment.
- **Harness compatibility** (read-only run of the unchanged Harness suite against 0.3.1): **148/149**. The only failure is `tests/test_integration.py:137` in the Harness, which pins the literal `version == "0.3.0"`. Fingerprint reproducibility in that same test passes. The log is `validation_v031/harness-compat-tests.txt`.

## Remaining limitations

- **The final gate describes the best candidate's own evaluation.** This is pre-existing behaviour, confirmed on 0.3.0.
  - When C0 is kept as best, the returned gate and scorecard come from C0's evaluation, which was made before any later concern existed. This holds even if the later candidate is byte-identical and a concern about it was found afterwards, including an unresolved high-severity one.
  - The concern, its audit and C1's gate remain in the trajectory.
  - Changing this would alter best-candidate and rollback semantics, so it was left for a separate decision.
- **Corroboration is model-based.** PASS judgments are correlated when judge and generator share a model. Acceptance therefore remains provisional, and the uncertainty says so.
- **The 40-character threshold and the low/medium severity set are policy constants.** The severity comes from the model's critique, and a mis-rated severity is still possible.
- **Reverting a transition overrides the verifier's status label for that target.** The original label remains in the trajectory history.
- **Budget stops are still `EXTERNAL_BLOCKER`.** Harness budget exceptions are still mapped that way; this is the existing integration gap.

## Readiness

- **Engine side:** 0.3.1 (`7a0b36de…6c16`) is ready for the same bounded Harness smoke. On a synthetic reconstruction of the reported pattern it finishes within 13 requests, and escalation for genuine defects is preserved.
- **Before launching:**
  - `E:\The End Harness\tests\test_integration.py:137` needs its version pin updated, which is a Harness edit outside this task.
  - The smoke manifest will record the new Engine identity automatically.
- **Not guaranteed:** whether a live model produces a justification and judgments that meet the criteria. The smoke has not been launched.
