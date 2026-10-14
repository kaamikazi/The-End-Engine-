# END Engine v0.3.5.2 — Unified Assessment Integrity + Revision Provenance

Corrective implementation and offline validation dated 2026-10-09. No revision
architecture rebuild, new operator/judge, retrieval, live provider call, benchmark,
commit, tag, push or publication. Synthetic tests do not demonstrate improved reasoning.

## Baseline and forensic evidence

Actual baseline: version **0.3.5.1**, Python **3.12.14**,
Git main at `6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7`, with extensive pre-existing dirty work.
Fingerprint `c04475eafbf7bc13f3cd0f2c4a772db9113c23c25e3cf35dd0cdb8b853643077` over 68 Engine Python files/pyproject
entries. The guarded full baseline discovered **262 tests: 0 failures, 0 errors,
0 skipped, 0 runtime network attempts**. Schema remains 3.0 in strict mode,
2.0 in legacy mode; historical 1.0/2.0/3.0 loading is retained.

The first restricted-environment baseline run stalled in a scripted fixture and
was stopped before source edits. Its partial log is preserved. The identical
network-blocked suite passed under the local execution context in 14.443 seconds;
no Engine fix was made to obtain that baseline result. `baseline-interruption.json`
records the distinction. Initial implementation/fixture failures are also retained,
not relabelled as successful tests.

Reviewed README, current/previous implementation reports, both frozen pilots'
reports/manual reviews, the v0351 final audit, original BA-002/008/009 trajectories
in both pilots, and all eight v0351 FULL_END trajectories for revision-value analysis.
`observed-assessment-paths.json` preserves the relevant exact concerns/plans/gates.
The pilot's Ollama 0.35.1→0.40.0 drift remains an unknown-time confound; no
clean causal performance comparison is claimed.

## Confirmed root causes

1. Critique findings were directly ingested into severity/state; verifier negatives
   reached quality gating separately from judge grounding. A false premise or
   unsupported behavioral allegation could still force correction through those paths.
2. Quote occurrence did not establish an alleged defect. The earlier task-reference
   fallback also misclassified full/mixed task references, sometimes suppressing real
   reference/constraint criticism.
3. Model plans were flattened into instructions without a reliable origin hierarchy.
   BA-009's plan told generation to add an invented evidence ID, which comparisons
   then called a user instruction. No actual evidence was acquired.
4. Past-status matching missed affirmative confirms prose. Internal UNVERIFIED
   bookkeeping therefore did not always constrain the actual returned wording.
5. Counting all backticks for answer selection confused incidental prose with code
   fences, while some assessors/claim extraction saw raw in-band reasoning instead
   of the displayed answer. Candidate/receipt hashes did not identify that distinction.
6. Progress observations counted new unsupported issues, unverified claim churn and
   unvalidated verifier changes as information; mandatory actions/cap timing explain
   some other continuations. Zero historical stops alone does not prove a detector bug.

## Shared assessment authority boundary

`quality/assessment.py` defines the small immutable `AssessmentFinding` and run-local
`AssessmentAuthorityPolicy`. It reuses Provenance, JudgeIssue/Grounding, claim IDs,
evidence artifacts/contracts and weakness records. Records contain producer, source
and premise origins, candidate/optional claim target, quote, alleged defect, rationale,
reference/scope, grounding, authority and disposition. A model cannot write Engine
annotations through its response schema. Assessment IDs/evidence are reset each run.

Task instructions and assertions, candidate content, model critique/judgment/plans,
Engine-derived checks, registered evidence and executed checks remain distinct.
MODEL_REVISION_PLAN never becomes TASK_INSTRUCTION. Reference registration is not
independent support. Only candidate-bound executed checks authorize supported claims
within their actual coverage; agreement and model confidence never supply it.

Unsupported concerns remain recorded and targetable as advisory weaknesses or
investigation requests. Their severity cannot alone create a demonstrated high defect.
Unknown verification may BLOCK completed assessment without falsely proving candidate
failure or being inverted into a successful verifier result. Known false-premise,
misattributed and precisely contradicted concerns do not independently decide failure.
Valid finite constraints and literal scoped checker propositions stay actionable.

## Assessment entry points and downstream effects

| Entry point | Authority handling | Permitted downstream effect |
|---|---|---|
| Critique | Policy normalization before weakness/knowledge ingestion; proposed support intercepted | Advisory target creation or validated scoped concern; no model-only claim promotion |
| LLM verification | Raw/effective assessments retained; policy validates negatives/updates; trusted scope reconsidered after collection | Genuine finite/scoped failures remain actionable; unvalidated negatives are uncertainty |
| Primary/secondary/adversarial judge | Every issue plus summary passes the shared policy; exact answer used | Decisive supported findings may affect gate/rollback; unsupported scores/verdicts cannot prove failure |
| Revision comparison | Candidate answer spans; model origin/decisive=false recorded | Advisory candidate preference, no unproven severe-regression rejection/rollback |
| Revision planning | Original task hierarchy, bounded conflict screen, labelled Change origins | Lower-trust proposals; Engine corrections survive malformed/contrary model plans |
| Branch/synthesis | Original task and actual current answer, explicit MODEL_REVISION_PLAN origin; existing branch-ID/adoption checks | Advisory alternatives/components, never an evidence receipt or user instruction |
| Claim/evidence validation | Existing exact candidate/target/artifact/phase contracts | Only actual checker support can change support state |
| Resolution/assumption audits | Existing scoped audits retained; authority of the underlying concern is preserved | Unsupported transitions rejected/recorded, no advisory-to-proven escalation |
| Trajectory judgment/gaming | Actual answer inspected; heuristic gaming findings normalized; procedural branch invariant retained | Descriptive diagnostics or justified integrity restriction, not proof from raw opinion counts |
| QualityGate | Decisive flags, uncertainty disposition, finite/reference/status checks and mandatory caller actions | Existing acceptance/termination separation; genuine scoped rejection remains possible |
| Rollback/restoration/reconciliation | Candidate-bound cache and actual answer identity; advisory severity does not acquire force later | Preserve real regressions/conflicts and current candidate scope; no new model calls |
| Final return guard | Same authoritative output span, status scope, reference registry, ambiguity and leakage | Withhold unsafe/uninspected output; preserve original raw candidate and reasons |

## Task and revision provenance

Task classification now handles multiple matching sentences and marks mixed/unmatched
references uncertain. Caller contracts remain explicit normative metadata, not proof
of world facts. Finite prescriptive checks cover JSON/fences, strict JSON, entry count,
literal JSON fields, explanation presence, Python literal external imports and bounded
hypothetical states. Ambiguous/uncheckable semantics remain advisory; there is no
arbitrary constraint/entailment solver or task-specific benchmark behavior.

Both revision modes explicitly separate original task, actual current candidate,
labelled Engine/model plans, constraints and unverified findings. Invalid plan actions
that override requested JSON/explanation or the original goal are ignored and traced.
Model factual assertions remain proposals, not accepted evidence. Generation, evaluation,
operator ranking, providers, call caps and repair budgets are not rebuilt.

## Evidence transitions, citations and output guard

`quality/revision_integrity.py` records bounded parent→child reference changes,
registered evidence before/after, newly registered artifacts, removals/additions,
answer/raw hashes and violations. Existing references can be reformatted or newly
referenced; explicit user references remain user-provided. Possible/hypothetical
sources may be discussed. Unknown references in a closed declared registry and
unregistered independent-authority assertions create targeted correction/guard
violations, without asserting that an external source definitely does not exist.
Only receipts from configured trusted checker code can supply execution authority.

The status recognizer extends the existing bounded English/JSON checks to affirmative
source-authority verbs and check-passed statements, with negation, quotation, attribution,
hypotheticals and scope controls. Narrow checks cannot authorize universal proof.
Failed/conflicting/wrong-candidate/wrong-artifact checks do not authorize status.
The final guard withholds unresolved status/reference violations, ambiguous extraction
and internal leakage; this is separate from external task usability/score.

## Authoritative answer and serialization

Candidate.content remains raw research content. Additive answer_content/status/reason
fields select the actual answer. ModelResponse optionally supplies an adapter-owned
verbatim span; otherwise line-aware wrapper/fence parsing is used. Inline backticks
and literal markers inside real code fences do not become boundaries. Multiple/empty
or obscured wrapper boundaries are ambiguous and cannot be silently accepted.

Claims, critics, verifiers, judges, comparisons, planners, branches, trusted tool
checks and final guard use the same inspected answer. Checker contracts bind the
inspected answer hash; raw-response hashes are stored separately. A caller that
previously checked raw native deliberation must update to the authoritative answer
scope, rather than transfer a raw-container receipt silently. Legacy plain-content
contracts behave identically. Schema additions are optional; no old record/fixture
is destructively migrated or rewritten. Existing model/decision replay tests pass.

## Justified no-progress change and read-only revision-value audit

Only concrete invalid signals are excluded: advisory issue creation, unverified claim
churn and unvalidated verifier opinions. Validated concern resolution, registered
executed evidence, substantive content, relevant support/contradiction/gate/branch
state remain observable. Required revision/verification, deterministic checks,
recovery, critical scrutiny and budgets remain protected. NO_PROGRESS never accepts.

`REVISION_VALUE_AUDIT_v0352.md` addresses all fifteen questions for each of eight
v0351 FULL_END runs. `progress-attribution.json` covers their 22 cycles plus 22 older
pilot cycles; unavailable old reset reasons/counters stay unknown. Historical labels,
external scores and evaluator/task code are unchanged. No external scoring enters END.

The observed chain is usually additional opinions → more concerns/plans/judgments →
similar/worse candidate. Seven final scores are neutral, one regresses, none improves.
No new executed evidence is acquired. Native BA-009 reduces a status overclaim but
adds a false citation. BA-008 native removes a passing explanation. Operator ranking
cannot be isolated as intrinsically wrong from poisoned issue inputs. The eight runs
cost 233 calls/574,138 tokens; all twelve cost 237/583,933. No actual saving or broader
reasoning improvement is inferred. The architecture itself is not rebuilt here.

## Tests and changed prior expectations

Baseline: 262/262 pass. Final prior test IDs: 262/262 pass. New dedicated regressions:
41/41 pass, covering T1–T24 plus negative/adversarial controls, actual answer/hash scope,
scoped verifier overrides, run isolation and plan prompt origin. Combined discovery:
**303 tests, 0 failures, 0 errors, 0 skipped; runtime network attempts 0; live model
calls 0**. Tests use deterministic scripted/mock providers and local checker fixtures.

Commands: `python -B -m unittest discover -s tests -t .` and
`python -B -m unittest tests.test_v0352_regressions`, run through the recorded guarded
API in `validation_v0352/run_offline.py`. Socket connect/connect_ex/sendto, DNS and
urllib opening are blocked during discovery/execution. Actual logs/JSON are retained.
The early two additional-control failures were fixture misuse of MockProvider's
scripted APIs, with their failed logs preserved; they were corrected without changing
what the controls require.

Twenty-three prior test methods retain their IDs but update expectations that treated
model-only negatives/support as facts, required synthetic model-only success, assumed
old request bytes, or inferred rollback from unsupported opinions. No test was deleted
or renamed. `changed-expectations.json` lists every method, old method fingerprint and
reason. Real scoped failure/recovery, mandatory-action, acceptance/rollback, serialization
and baseline-disabled decision controls continue to pass. Specific changes:

- `tests/test_audit_policy.py::test_empty_justification_keeps_concern_open_at_its_severity`: Invalid retirement of an advisory proposal is recorded/reopened, not promoted into a demonstrated candidate defect.
- `tests/test_audit_policy.py::test_genuine_high_severity_concern_still_escalates_and_remains_unresolved`: Severity alone is not evidence; actual scoped high failures remain covered by S2/R11 and trusted-check lifecycle controls.
- `tests/test_audit_policy.py::test_unsupported_assumption_transition_resets_without_severity_inflation`: Model assumption support is intercepted before it alters authority; no unsupported transition is applied and then undone.
- `tests/test_end_engine.py::test_weaknesses_persist_without_verifier_resolution`: Advisory findings persist and remain targetable, but do not override an independently configured rule verifier.
- `tests/test_final_reconciliation.py::test_c0_restored_after_identical_c1_acquires_unresolved_high_concern`: Reconciliation cannot turn a later ungrounded model allegation into a proven high defect; raw history and uncertainty remain.
- `tests/test_final_reconciliation.py::test_budget_exhaustion_keeps_its_cause_and_reports_applicable_concerns`: A model allegation no longer forces a budget stop; an explicit probe keeps the intended interruption/termination test exercised.
- `tests/test_integrity_review.py::test_critique_cannot_disguise_non_applicability_as_engine_support`: Model NOT_APPLICABLE/support updates stay proposals before knowledge mutation, while a real scoped claim still verifies.
- `tests/test_integrity_review.py::test_content_contradiction_on_identical_candidate_stays_visible`: An unsupported model opposition is retained as an advisory assessment, not promoted into an executed-evidence contradiction.
- `tests/test_integrity_review.py::test_explicit_rollback_keeps_rollback_and_reports_applicable_conflict`: A model-set fatal label lacks scope proof; it cannot force rejection/rollback. Trusted-failure rollback controls remain unchanged.
- `tests/test_integrity_review.py::test_contradiction_resolved_later_by_validated_transition_is_not_reraised`: The ungrounded model stance is not an evidence contradiction; the real scoped retirement still applies and is not resurrected.
- `tests/test_cognitive_brain.py::test_deep_run_branches_questions_and_synthesis_are_real_stages`: Model-only state/support assertions no longer complete scrutiny; bounded compatibility and goal preservation still tested.
- `tests/test_cognitive_brain.py::test_critical_demo_is_bounded_and_does_not_replace_goal`: Model-only state/support assertions no longer complete scrutiny; bounded compatibility and goal preservation still tested.
- `tests/test_evidence_integrity.py::test_missing_evidence_stays_visible_after_rollback`: The best candidate is retained with scope uncertainty; a model allegation alone no longer emits a rollback event.
- `tests/test_final_reconciliation.py::test_candidate_specific_audit_failure_is_not_transferred`: An invalid retirement is recorded but cannot promote the underlying advisory concern into a proven defect.
- `tests/test_quality.py::test_controlled_regression_returns_best_and_retains_latest`: The unvalidated C2 concern blocks completed assessment without proving failure; C4 executed failure still rolls back to verified C3.
- `tests/test_quality.py::test_fatal_revision_cannot_receive_good_revision_label`: A model-set fatal label without a demonstrated contract violation does not establish a bad revision.
- `tests/test_quality.py::test_successful_correction_gets_recovery_transition_label`: A real scoped check can verify the correction; the initial model-only allegation did not establish a rejected failure to recover from.
- `tests/test_quality.py::test_legacy_demos_remain_compatible_but_unjudged`: The production fixture cannot close its candidate assumptions using model-only support updates; unjudged labels remain blocked/inconclusive.
- `tests/test_v0351_regressions.py::test_safe_status_revision_wins_equal_gate_rank_without_verified_promotion`: Unsupported model verification is inconclusive, not a demonstrated defect; safe output and no-progress nonacceptance remain protected.
- `tests/test_v0351_regressions.py::test_S17_no_progress_does_not_create_acceptance`: Unsupported model verification is inconclusive, not a demonstrated defect; safe output and no-progress nonacceptance remain protected.
- `tests/test_v035_regressions.py::test_C0_AB_structured_vs_native_metadata_stays_separate`: Structured requests intentionally add source labels; native initial requests and output/protocol separation remain unchanged.
- `tests/test_v035_regressions.py::test_R12_real_task_constraint_violation_still_counts`: Validated finite findings use the Engine mechanical reason rather than treating the model wording as proof.
- `tests/test_v035_regressions.py::test_R9_contradicting_a_task_premise_is_not_a_defect`: A bare executed-ID string supplies no artifact/coverage declaration; scoped full-artifact positive controls remain in S1/S2/T4.

## Files changed and preserved boundaries

New production modules are assessment.py and revision_integrity.py. Other modifications
are integration points, additive state/response/schema fields, task/output parsing,
provenance-labelled prompts and validated-progress filtering. The exact release-baseline
file-hash delta is in changed-files.json. The Git patch includes earlier uncommitted
v035/Jev work, so it is not misrepresented as a clean release-only diff.

- `README.md`
- `end_engine/cognition/branches.py`
- `end_engine/cognition/knowledge.py`
- `end_engine/cognition/session.py`
- `end_engine/cognition/state.py`
- `end_engine/core/output_format.py`
- `end_engine/core/progress.py`
- `end_engine/core/revision_planner.py`
- `end_engine/core/state.py`
- `end_engine/core/task_contract.py`
- `end_engine/core/termination.py`
- `end_engine/core/weaknesses.py`
- `end_engine/engine.py`
- `end_engine/experience/schema.py`
- `end_engine/models/base.py`
- `end_engine/models/recording.py`
- `end_engine/operators/base.py`
- `end_engine/quality/assessment.py`
- `end_engine/quality/audits.py`
- `end_engine/quality/comparison.py`
- `end_engine/quality/epistemic.py`
- `end_engine/quality/gate.py`
- `end_engine/quality/grounding.py`
- `end_engine/quality/integrity.py`
- `end_engine/quality/judges.py`
- `end_engine/quality/revision_integrity.py`
- `end_engine/quality/session.py`
- `end_engine/quality/state.py`
- `end_engine/verification/llm_verifier.py`
- `pyproject.toml`
- `tests/test_audit_policy.py`
- `tests/test_cognitive_brain.py`
- `tests/test_end_engine.py`
- `tests/test_evidence_integrity.py`
- `tests/test_final_reconciliation.py`
- `tests/test_integrity_review.py`
- `tests/test_quality.py`
- `tests/test_v0351_regressions.py`
- `tests/test_v0352_regressions.py`
- `tests/test_v035_regressions.py`

All decision routing/provider files, operator definitions, selection policy and question
selector remain byte-identical to the baseline. No SDK, dependency, provider, Actions,
release/tag or Harness modification is introduced. Historical benchmark/task/evaluator,
validation and implementation-report records remain byte-identical (2,619 files).
The ordinary Git whitespace check treats Windows CRLF as trailing whitespace; the
per-command Windows-EOL-aware check passes without global Git changes or unnecessary
line-ending rewrites. Credential-pattern scanning finds no literal credentials/private
keys in changed source/test/docs; values are never printed.

## Known limits

This is a bounded integrity policy, not a universal truth or entailment engine. Unusual
English, multilingual/implicit authority claims, arbitrary citation schemas, dynamic
imports and uncheckable requirements may stay uncertain or escape recognized patterns.
Proper registration does not prove source contents. Callers/checker contracts remain a
trust boundary; exact scope matching may conservatively block useful paraphrases.
Unknown verification/ambiguous output may reduce usability. Advisory preferences can
still select an inferior candidate not distinguished by a finite check; the historical
revision-value problem remains. No live-model improvement or cost saving is claimed.

## Version, fingerprint and final decision

Version: **0.3.5.2** (not 0.3.6). Final canonical source-manifest fingerprint over 70
Engine Python/pyproject entries:

`29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82`

See identity-after.json/source-after.json, guarded suite records, history-audit.json,
credential-scan.json and final-summary.json. Git HEAD remains the baseline commit;
no commit, tag, push or publication. Live model calls **0**; benchmark **NOT EXECUTED**.

**B. RECONSIDER REVISION ARCHITECTURE BEFORE MORE INFERENCE.** Historical evidence
already shows structural issue selection, planning, generation and comparison failures.
Integrity controls prevent authority escalation; passing their offline tests does not
show that another twelve-run pilot would produce useful revision gains. No new pilot
or architecture implementation is authorized/launched by this recommendation.
