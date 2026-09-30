# END Engine v0.3.2 implementation report

- **Date:** 2026-09-30.
- **Scope:** a focused fix for stale final evaluations of restored candidates.
- **Earlier reports:** the v0.3.1 report is preserved unchanged as [IMPLEMENTATION_REPORT_v0.3.1.md](IMPLEMENTATION_REPORT_v0.3.1.md), and the v0.3 report as [IMPLEMENTATION_REPORT_v0.3.md](IMPLEMENTATION_REPORT_v0.3.md).
- **Before editing:** the **127-test 0.3.1 baseline passed** (`validation_v032/engine-tests-before.txt`), and the tree was snapshotted (`validation_v032/engine-tree-before.json`).
- **What was not done:** no live model calls, no smoke, no budget or threshold changes. Historical Harness experiment directories are unchanged.

## Identification

| | Version | Source fingerprint (`end_engine/**/*.py` + `pyproject.toml`, as computed by the Harness) |
|---|---|---|
| Before | 0.3.1 | `7a0b36decba87d3587699aa91f213c5279c812049632f37b865947ad3a0d6c16` |
| **After** | **0.3.2** | **`5ea97d2f7170a8d4d928d9e088b6d3d0f6d3425cdea5f28628ac545c8db5c314`** |

- **Changed:** `end_engine/engine.py` (+2 lines), `end_engine/quality/session.py` (96 changed lines), `pyproject.toml`, `README.md` and this report.
- **Added:** `tests/test_final_reconciliation.py` and `validation_v032/`.
- The identity is recorded in `validation_v032/engine-identity.json`. The trajectory schema stays `3.0`; the new key and step are additive.

## Reproduced failure (real Engine lifecycle, offline providers)

I reproduced the failure on 0.3.1 with the synthetic high-severity scenario from `tests/test_audit_policy.py`:

- **The run:**
  - All candidates are byte-identical.
  - The critique of C0, made *after* C0's gate, raised W001 (high).
  - C1's `accepted_risk` was rejected, so W001 reopened.
  - C1 and C2 were `REVISE`.
  - Termination was `BUDGET_EXHAUSTED`, with the explanation "Unresolved high-severity weaknesses remain".
- **The stale final fields:** END returned C0, and the final fields carried C0's pre-concern evaluation:

  | Field | Value |
  |---|---|
  | `final_result.quality_gate` | `ACCEPT_PROVISIONALLY` |
  | `acceptance_label` | `ACCEPTED_PROVISIONAL` |
  | `scorecard` | only "Generator and judge share model identity" |
  | final `weaknesses` | `[]` |
  | final cognitive state | no high-severity concerns |

- **Why:**
  - `EndEngine.run` restores the best candidate's evaluation-time snapshot (`quality.restore`).
  - `QualitySession.finalize` reported that candidate's cached gate.
  - Neither considered events after its evaluation, including concerns raised by critiquing the returned candidate itself.
- **How the report was verified:** by running and inspecting the fields directly, not from the earlier report.

## Fix

`QualitySession.reconcile(final_candidate_id, record, registry)` runs once in `EndEngine.run`, right after the existing restore of the returned candidate. It makes **no model calls**.

1. **Selection and rollback are unchanged.** The same candidate is returned, including C0 or a rollback target.
2. **Scope.** It starts from the returned candidate's own evaluated state and looks only at steps after that candidate's gate. It walks the recorded steps and assigns each status transition to the candidate being verified or audited at that point.
3. **Applied** (demonstrably applicable to the returned content):
   - findings from critiques of **byte-identical** candidates;
   - status transitions made on byte-identical candidates, when the latest audit of that transition in the same content scope is `VALID` or `WEAKLY_SUPPORTED`.

   A later valid resolution therefore stays resolved and is not resurrected.
4. **Not applied, but recorded** with a reason:
   - transitions made on different content;
   - transitions rejected by audit (the concern keeps its previous status);
   - transitions not audited in this content scope (these add the uncertainty "Unaudited status transitions were not applied");
   - judge feedback and `audit_failure` of other identical-content candidates. These are candidate-scoped: a judgment is made under that candidate's evidence scope, and an audit failure is procedural. Identical content alone does not transfer them. Judge feedback adds "Applicability undetermined for findings from judgments of identical content", which caps acceptance at provisional. Audit failures are listed only.
5. **Final assessment.**
   - A later unresolved high or critical concern moves the final decision to `REVISE`, unless the decision is already stricter.
   - An applicable accepted risk, an unaudited transition or undetermined applicability caps `ACCEPT_VERIFIED` at `ACCEPT_PROVISIONALLY`.
   - Lower-severity open concerns are reported without changing the decision, as the gate already does.
   - Thresholds are unchanged.
6. **Immutability and provenance.**
   - `quality_gate_decisions` and cached evaluations are not modified.
   - A `final_reconciliation` step and key record: the basis, identical-content candidates, the evaluation step, the original and reconciled gates, applicable later concerns with provenance, applied, ignored and not-transferred items, and `model_calls: 0`.
   - The final `weaknesses` and last cognitive state show the reconciled applicable concerns, keeping their severity and status.
   - `scorecard.unresolved_concerns` lists open concerns and accepted risks.
7. **Documented meanings** (also in the README):
   - The returned answer is `best_candidate_id` / `final_candidate_id`.
   - `quality_gate`, `acceptance_label` and `scorecard` give the reconciled assessment of that answer.
   - `termination` says why the loop stopped, and is not changed.
   - Budget exhaustion stays `BUDGET_EXHAUSTED`. An external stop stays `EXTERNAL_BLOCKER` / `BLOCKED` / `INCOMPLETE`, and the applicable concerns are still added to the reported reasons.

## Behaviour after the fix (same synthetic scenarios)

| Scenario | 0.3.1 final | 0.3.2 final |
|---|---|---|
| High concern on identical content; C0 returned; `BUDGET_EXHAUSTED` | `ACCEPT_PROVISIONALLY`, no concerns listed | **`REVISE`**; W001 high/open listed; termination `BUDGET_EXHAUSTED` kept |
| Justified low risk validated on identical C1; C0 returned | `ACCEPT_PROVISIONALLY` (C0's own reasons only) | `ACCEPT_PROVISIONALLY` with "Accepted risks remain unverified: W001"; W001 `accepted_risk` visible |
| Same with an independent judge (C0 `ACCEPT_VERIFIED` at its own gate) | **`ACCEPT_VERIFIED`** | `ACCEPT_PROVISIONALLY`; the accepted risk is never verification |
| Empty justification; C1 audit failure | `ACCEPT_PROVISIONALLY`, no concerns | `ACCEPT_PROVISIONALLY`; C1's audit failure not transferred; W001 low/open listed |
| Deployment rollback C4 → C3 | `ACCEPT_VERIFIED` | unchanged; `changed: false`; C4's regression and judge findings do not touch C3 |

## Tests

- **Engine:** **135/135 OK** (127 existing plus 8 new), run with `-B`, `PYTHONDONTWRITEBYTECODE=1` and a working directory outside the tree (`validation_v032/engine-tests-after.txt`).
- **New tests** in `tests/test_final_reconciliation.py`. All are synthetic:
  - C0 is restored after a byte-identical C1 acquires an unresolved high-severity content concern.
  - A legitimately accepted low risk stays visible and blocks verified acceptance.
  - A concern validly resolved later, by a `VALID` targeted executed check, is not resurrected.
  - A defect only in a different candidate does not contaminate the returned candidate.
  - A candidate-specific audit failure is not transferred.
  - A judgment of identical content is reported as undetermined, not transferred.
  - Budget exhaustion keeps its cause while reporting concerns, for both the cycle cap and an external stop.
  - Existing acceptance and rollback are intact.
  - Each test checks that no model call happens after termination.
- **Harness, against 0.3.2:** **149/149 OK** (`validation_v032/harness-tests.txt`). `tests/test_integration.py::test_engine_source_fingerprint_is_reproducible` now reads the expected version independently from the selected checkout's `pyproject.toml` with `tomllib`. It checks the version format, asserts that the recorded version and source path match, and keeps the fingerprint-reproducibility check.

## Remaining limitations

- **Applicability means byte-identical content.**
  - A semantically equivalent candidate with different bytes does not share concerns.
  - A concern raised on different content is not transferred, even if it might also hold for the returned answer.
  - These cases are not inferred, and nothing is reported for them.
- **Judge feedback on identical content is not transferred.** Judgments depend on each candidate's evidence set, so they are reported as undetermined and cap acceptance at provisional. The Engine cannot establish their applicability from its current data model.
- **Only the latest same-scope audit of a transition counts.** Audits made in a different candidate's scope are ignored for the returned candidate.
- **`verification` stays the returned candidate's own verifier result.** A later verifier view of identical content is not merged.
- **Reconciliation never re-judges.** An answer returned as `REVISE` means known applicable concerns are unresolved. It is not a new model assessment.

## Readiness

Engine 0.3.2 (`5ea97d2f…c314`) and the Harness (149/149 against it) are ready for **one repeat of the existing Gemini smoke with unchanged limits**: 3 probes plus one END run with at most 14 invocations, 17 in total, 600 s and 90 s per call. The smoke manifest will record the new Engine identity. The smoke has not been launched. Its outcome depends on live model behaviour, and a `REVISE` or `BLOCKED` final assessment would be a legitimate result, not a failure of this fix.
