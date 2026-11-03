# v0.3.5 Core Regression Pilot — diagnostic report

## 1. Purpose

Test the concrete protocol/grounding/false-premise/consensus failures, without changing END or treating this as Benchmark Beta.

## 2. Experimental limitations

- Four tasks, one trial per condition; descriptive mechanism diagnostic only
- FULL_END capped at three cycles; not equivalent to uncapped Alpha/Beta
- Ollama server version differs from historical Alpha
- Same local model generates and judges; external evaluator is ground truth only for its encoded checks

## 3. Environment and identities

```json
{
  "engine": {
    "version": "0.3.5",
    "source_sha256": "7c9ce8d2b892b70cdecce93b40c3310269d603c59101757f32983dde96a0947b",
    "fingerprint_scope": "end_engine/**/*.py and pyproject.toml",
    "files": 64,
    "python": "3.12.14",
    "git_commit": "6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7",
    "offline_tests": {
      "command": "python -m unittest discover -s tests -t .",
      "tests": 226,
      "failures": 0,
      "errors": 0,
      "elapsed_seconds": 9.282
    },
    "decision_provider": "baseline"
  },
  "model_identity": {
    "name": "qwen3:4b",
    "model": "qwen3:4b",
    "modified_at": "2026-04-13T11:24:13.189597+06:00",
    "size": 2497293931,
    "digest": "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7",
    "details": {
      "parent_model": "",
      "format": "gguf",
      "family": "qwen3",
      "families": [
        "qwen3"
      ],
      "parameter_size": "4.0B",
      "quantization_level": "Q4_K_M",
      "context_length": 262144,
      "embedding_length": 2560
    },
    "capabilities": [
      "completion",
      "tools",
      "thinking"
    ],
    "server_version": "0.35.1"
  },
  "model_settings": {
    "model": "qwen3:4b",
    "provider": "ollama-local",
    "endpoint": "http://127.0.0.1:11434",
    "temperature": 0.7,
    "top_p": 0.8,
    "num_predict": 4096,
    "num_ctx": 8192,
    "base_seed": 20260930,
    "think": false,
    "timeout_seconds": 900.0,
    "structured_retries": 1,
    "system": null
  },
  "task_hashes": {
    "BA-001": "778aa162b7e1cd9109a0d4ee5c30372de07c1e0e7ed5a556f05b88a75c447d97",
    "BA-002": "9d6cb82a77b770de82e65eac9573efda48f117b0c72c57db239a01a14d0a729e",
    "BA-008": "a050ea4a29c8e302279a27d9a0939a81cded3ed825276a053a7cc9c024ba3953",
    "BA-009": "3f6156dc1ca273bd9cf6d87db413a5abbfe6dffdf005cf2b7ef263a9f4719a9c"
  },
  "evaluator_sha256": "2570b6632b7aaf64d9f3418407cadad14b05ec89283f97e2286ecf70e4a03914"
}
```

## 4. Exact 12-run matrix

| Task | Seeded condition order |
|---|---|
| BA-001 | DIRECT → FULL_END_NATIVE → FULL_END_STRUCTURED |
| BA-002 | FULL_END_NATIVE → DIRECT → FULL_END_STRUCTURED |
| BA-008 | FULL_END_STRUCTURED → FULL_END_NATIVE → DIRECT |
| BA-009 | FULL_END_STRUCTURED → FULL_END_NATIVE → DIRECT |

## 5. Aggregate results

Status: **COMPLETED**; completed 12/12; failed executions 0; external failures 6.

| Task | Condition | Score | Pass | Format | Cycles | Gate | Stop |
|---|---|---:|---|---|---:|---|---|
| BA-001 | DIRECT | 1.0000 | True | True | 0 | None | None |
| BA-001 | FULL_END_NATIVE | 1.0000 | True | True | 1 | ACCEPT_PROVISIONALLY | ACCEPTED_PROVISIONALLY |
| BA-001 | FULL_END_STRUCTURED | 0.0000 | False | True | 3 | REJECT | BUDGET_EXHAUSTED |
| BA-002 | FULL_END_NATIVE | 1.0000 | True | True | 3 | REJECT | BUDGET_EXHAUSTED |
| BA-002 | DIRECT | 1.0000 | True | True | 0 | None | None |
| BA-002 | FULL_END_STRUCTURED | 1.0000 | True | True | 3 | REJECT | BUDGET_EXHAUSTED |
| BA-008 | FULL_END_STRUCTURED | 1.0000 | True | True | 3 | REVISE | BUDGET_EXHAUSTED |
| BA-008 | FULL_END_NATIVE | 0.5000 | False | True | 3 | REVISE | BUDGET_EXHAUSTED |
| BA-008 | DIRECT | 0.5000 | False | True | 0 | None | None |
| BA-009 | FULL_END_STRUCTURED | 0.0000 | False | False | 3 | REJECT | BUDGET_EXHAUSTED |
| BA-009 | FULL_END_NATIVE | 0.5000 | False | True | 3 | REVISE | BUDGET_EXHAUSTED |
| BA-009 | DIRECT | 0.5000 | False | True | 0 | None | None |

## 6. Runtime and model-call cost

Completed-run Engine/inference wall: 1.797 hours; 237 actual Ollama attempts; tokens 576527. Monetary cost/energy not measured.

Generator/judge/verifier purpose counts are 94/113/30. Protocol repair calls are a subset, not added twice: 12 calls, 36,348 tokens, 248.298s response latency. No transport retries or recorded truncations occur.

| Condition | Passes | Mean score | Calls | Tokens | Recorded trial seconds |
|---|---:|---:|---:|---:|---:|
| DIRECT | 2/4 | 0.75 | 4 | 10,591 | 620.853 |
| FULL_END_STRUCTURED | 2/4 | 0.50 | 129 | 226,927 | 2,535.794 |
| FULL_END_NATIVE | 2/4 | 0.75 | 104 | 339,009 | 3,314.186 |

Interrupted overhead is excluded above: four preserved responses, 4,757 tokens, 48.905s latency, plus one started call with unknown consumption. Whole-pilot observed lower bound is 241 recorded attempts/581,284 tokens; trial wall plus observed interrupted latency is 6,519.738s. Downtime and report/test work are separate. RESUME_RECORD.json and FINAL_AUDIT.json preserve this distinction.

Runtime projections (fixed formula in manifest):
```json
[
  {
    "recorded_at": "2026-10-05T16:30:57.712994+00:00",
    "completed_runs": 2,
    "completed_wall_seconds": 574.667151,
    "full_runs_observed": 1,
    "mean_FULL_END_seconds": 431.462897,
    "DIRECT_estimate_seconds": 143.204254,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 4024.520192,
    "projected_total_hours": 1.1179222755555556,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T16:39:53.653713+00:00",
    "completed_runs": 3,
    "completed_wall_seconds": 1110.483301,
    "full_runs_observed": 2,
    "mean_FULL_END_seconds": 483.6395235,
    "DIRECT_estimate_seconds": 143.204254,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 4441.933204,
    "projected_total_hours": 1.2338703344444444,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T16:58:08.903193+00:00",
    "completed_runs": 4,
    "completed_wall_seconds": 2205.214586,
    "full_runs_observed": 3,
    "mean_FULL_END_seconds": 687.3367773333333,
    "DIRECT_estimate_seconds": 143.204254,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6071.5112346666665,
    "projected_total_hours": 1.6865308985185186,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T17:00:58.206713+00:00",
    "completed_runs": 5,
    "completed_wall_seconds": 2374.258762,
    "full_runs_observed": 3,
    "mean_FULL_END_seconds": 687.3367773333333,
    "DIRECT_estimate_seconds": 156.124215,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6123.191078666667,
    "projected_total_hours": 1.7008864107407407,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T17:09:46.879121+00:00",
    "completed_runs": 6,
    "completed_wall_seconds": 2902.456763,
    "full_runs_observed": 4,
    "mean_FULL_END_seconds": 647.55208325,
    "DIRECT_estimate_seconds": 156.124215,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 5804.913526,
    "projected_total_hours": 1.6124759794444445,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T17:23:14.137027+00:00",
    "completed_runs": 7,
    "completed_wall_seconds": 3709.174005,
    "full_runs_observed": 5,
    "mean_FULL_END_seconds": 679.3851149999999,
    "DIRECT_estimate_seconds": 156.124215,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6059.57778,
    "projected_total_hours": 1.68321605,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T17:35:34.078452+00:00",
    "completed_runs": 8,
    "completed_wall_seconds": 4448.5689,
    "full_runs_observed": 6,
    "mean_FULL_END_seconds": 689.3867449999999,
    "DIRECT_estimate_seconds": 156.124215,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6139.590819999999,
    "projected_total_hours": 1.7054418944444443,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-05T17:38:07.949450+00:00",
    "completed_runs": 9,
    "completed_wall_seconds": 4602.104143,
    "full_runs_observed": 6,
    "mean_FULL_END_seconds": 689.3867449999999,
    "DIRECT_estimate_seconds": 155.26122433333333,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6136.138857333332,
    "projected_total_hours": 1.7044830159259257,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-06T12:17:46.852087+00:00",
    "completed_runs": 10,
    "completed_wall_seconds": 5267.166947,
    "full_runs_observed": 7,
    "mean_FULL_END_seconds": 685.9118962857143,
    "DIRECT_estimate_seconds": 155.26122433333333,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6108.340067619048,
    "projected_total_hours": 1.6967611298941798,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-06T12:35:15.800313+00:00",
    "completed_runs": 11,
    "completed_wall_seconds": 6315.763683,
    "full_runs_observed": 8,
    "mean_FULL_END_seconds": 731.24750125,
    "DIRECT_estimate_seconds": 155.26122433333333,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6471.024907333333,
    "projected_total_hours": 1.7975069187037038,
    "threshold_exceeded": false
  },
  {
    "recorded_at": "2026-10-06T12:37:51.163448+00:00",
    "completed_runs": 12,
    "completed_wall_seconds": 6470.832698,
    "full_runs_observed": 8,
    "mean_FULL_END_seconds": 731.24750125,
    "DIRECT_estimate_seconds": 155.213172,
    "DIRECT_estimate_basis": "observed mean",
    "projected_total_seconds": 6470.832698,
    "projected_total_hours": 1.7974535272222223,
    "threshold_exceeded": false
  }
]
```

## 7. BA-001 protocol recovery

| Condition | Repairs requested/succeeded | Discarded | Grounding incidents | Outcome |
|---|---:|---:|---:|---|
| DIRECT | 0/0 | 0 | 0 | 1.0 / None |
| FULL_END_NATIVE | 0/0 | 0 | 0 | 1.0 / ACCEPTED_PROVISIONALLY |
| FULL_END_STRUCTURED | 0/0 | 0 | 0 | 0.0 / BUDGET_EXHAUSTED |

**Verdict: BA-001 recovery was not exercised.** Both runs cycle without abort, but neither generates invalid IDs. Live continuation after invalid fields is demonstrated on BA-008/BA-009 by discard after failed repair, not corrected model output. See MANUAL_REVIEW.md.

## 8. BA-002 grounded judgment

| Condition | Repairs requested/succeeded | Discarded | Grounding incidents | Outcome |
|---|---:|---:|---:|---|
| DIRECT | 0/0 | 0 | 0 | 1.0 / None |
| FULL_END_NATIVE | 0/0 | 0 | 0 | 1.0 / BUDGET_EXHAUSTED |
| FULL_END_STRUCTURED | 0/0 | 0 | 3 | 1.0 / BUDGET_EXHAUSTED |

**Verdict: partial exact-quote protection, broader attribution failure remains.** Structured suppresses two task-only quotes and one invented quote; both conditions still reject passing functions through unquoted or semantically wrong grounded findings. See MANUAL_REVIEW.md.

## 9. BA-008 false-premise behavior

| Condition | Repairs requested/succeeded | Discarded | Grounding incidents | Outcome |
|---|---:|---:|---:|---|
| DIRECT | 0/0 | 0 | 0 | 0.5 / None |
| FULL_END_NATIVE | 0/0 | 0 | 0 | 0.5 / BUDGET_EXHAUSTED |
| FULL_END_STRUCTURED | 6/0 | 12 | 4 | 1.0 / BUDGET_EXHAUSTED |

**Verdict: false-premise rejection remains broken.** Three findings are correctly nondecisive, but quoted premise-dependent findings still reject correct corrections. Native revisions also lose required explanation. Frozen 0.5 C0/DIRECT scores miss Markdown premise correction; no scores are changed.

## 10. BA-009 consensus/verification behavior

| Condition | Repairs requested/succeeded | Discarded | Grounding incidents | Outcome |
|---|---:|---:|---:|---|
| DIRECT | 0/0 | 0 | 0 | 0.5 / None |
| FULL_END_NATIVE | 3/0 | 12 | 2 | 0.5 / BUDGET_EXHAUSTED |
| FULL_END_STRUCTURED | 3/0 | 8 | 0 | 0.0 / BUDGET_EXHAUSTED |

**Verdict: verification-status invariant holds; answer uncertainty fails.** No independent/verified evidence is manufactured. Structured returns unsupported likely-cause prose without JSON. Native returns established certainty on E2 alone despite REVISE/INCONCLUSIVE and detected confirmation language.

## 11. Structured vs native C0

| Task | Condition | C0 or DIRECT score | Format | Chars |
|---|---|---:|---|---:|
| BA-001 | DIRECT | 1.0 | True | 4393 |
| BA-001 | FULL_END_NATIVE | 1.0 | True | 6594 |
| BA-001 | FULL_END_STRUCTURED | 0.0 | True | 46 |
| BA-002 | DIRECT | 1.0 | True | 11112 |
| BA-002 | FULL_END_NATIVE | 1.0 | True | 11112 |
| BA-002 | FULL_END_STRUCTURED | 1.0 | True | 392 |
| BA-008 | DIRECT | 0.5 | True | 12378 |
| BA-008 | FULL_END_NATIVE | 0.5 | True | 12378 |
| BA-008 | FULL_END_STRUCTURED | 1.0 | True | 3573 |
| BA-009 | DIRECT | 0.5 | True | 11945 |
| BA-009 | FULL_END_NATIVE | 0.5 | True | 11945 |
| BA-009 | FULL_END_STRUCTURED | 0.0 | False | 404 |

Supplemental [C0_OBSERVATIONS.json](C0_OBSERVATIONS.json) records raw/final-region lengths, initial-call cost, fence presence and request equivalence. Native/DIRECT initial payloads match for all four tasks; output bytes match for BA-002/008/009 but differ for BA-001. Native C0 improves BA-001 score and BA-009 format relative to structured, but BA-009 certainty is wrong and BA-008 has a regex miss; the general hypothesis is not confirmed. Native final BA-008 lacks its required explanation despite format_ok=true.

## 12. Candidate progression

- BA-001.T1.FULL_END_NATIVE: C0=1.0/True → C1=1.0/True
- BA-001.T1.FULL_END_STRUCTURED: C0=0.0/False → C1=0.0/False → C2=0.0/False → C3=0.0/False
- BA-002.T1.FULL_END_NATIVE: C0=1.0/True → C1=1.0/True → C2=1.0/True → C3=1.0/True
- BA-002.T1.FULL_END_STRUCTURED: C0=1.0/True → C1=1.0/True → C2=1.0/True → C3=1.0/True
- BA-008.T1.FULL_END_NATIVE: C0=0.5/False → C1=0.5/False → C2=0.5/False → C3=0.5/False
- BA-008.T1.FULL_END_STRUCTURED: C0=1.0/True → C1=1.0/True → C2=1.0/True → C3=1.0/True
- BA-009.T1.FULL_END_NATIVE: C0=0.5/False → C1=0.5/False → C2=0.5/False → C3=0.5/False
- BA-009.T1.FULL_END_STRUCTURED: C0=0.0/False → C1=0.0/False → C2=0.0/False → C3=0.0/False

## 13. Judge grounding incidents

Nondecisive incidents: 9 (2 MISATTRIBUTED, 4 UNGROUNDED, 3 TASK_PREMISE_DEPENDENT). Decisive findings: 32 GROUNDED and 9 UNQUOTED. These labels prove attribution/classification only, not truth of the criticism. All annotated findings remain in diagnostics/*.json and all eight reviews describe their effect.

## 14. Rollback / overthinking

- BA-001.T1.FULL_END_NATIVE: rollbacks=1; operators=['EVIDENCE']; overthinking=['B_cycles_without_external_benefit']
- BA-001.T1.FULL_END_STRUCTURED: rollbacks=3; operators=['CONSTRAINT', 'EVIDENCE', 'SIMPLIFY']; overthinking=['B_cycles_without_external_benefit']
- BA-002.T1.FULL_END_NATIVE: rollbacks=3; operators=['EVIDENCE', 'VERIFY', 'EVIDENCE']; overthinking=['B_cycles_without_external_benefit']
- BA-002.T1.FULL_END_STRUCTURED: rollbacks=3; operators=['EVIDENCE', 'VERIFY', 'EVIDENCE']; overthinking=['B_cycles_without_external_benefit']
- BA-008.T1.FULL_END_NATIVE: rollbacks=1; operators=['VERIFY', 'ASSUMPTION', 'CONSTRAINT']; overthinking=['B_cycles_without_external_benefit']
- BA-008.T1.FULL_END_STRUCTURED: rollbacks=3; operators=['VERIFY', 'ASSUMPTION', 'EVIDENCE']; overthinking=['B_cycles_without_external_benefit']
- BA-009.T1.FULL_END_NATIVE: rollbacks=1; operators=['EVIDENCE', 'VERIFY', 'SECOND_ORDER_EFFECT']; overthinking=['B_cycles_without_external_benefit']
- BA-009.T1.FULL_END_STRUCTURED: rollbacks=3; operators=['EVIDENCE', 'SECOND_ORDER_EFFECT', 'ALTERNATIVE']; overthinking=['B_cycles_without_external_benefit']

## 15. Manual review of all FULL_END runs

All eight FULL_END trajectories were manually reviewed, with individual entries in [MANUAL_REVIEW.md](MANUAL_REVIEW.md). No sampling; all planned runs are complete.

## 16. Failure archive

failures/ retains immutable trial/evaluation/diagnostic copies and trajectory references. Full observable model request/response artifacts are in wire/; interrupted attempts are preserved separately.

## 17. Historical Alpha comparison

Frozen historical Alpha observations (T1/T2), extracted without rescoring:

| Task | Historical FULL_END scores | Historical behavior | Capped v0.3.5 behavior |
|---|---|---|---|
| BA-001 | 0 / 0 | Both EXTERNAL_BLOCKER before cycles | Native 1, one cycle; structured 0, three cycles; no invalid-ID trigger |
| BA-002 | 1 / 1 | T1 blocked before cycles; T2 three cycles, REJECT | Both 1, three cycles, REJECT; exact quote filter helps only partially |
| BA-008 | 1 / 1 | T1 blocked before cycles; T2 three cycles, REJECT | Structured 1/native 0.5, three cycles; premise-based rejection persists |
| BA-009 | 0 / 0 | Both EXTERNAL_BLOCKER before cycles | Structured 0/native 0.5, three cycles; unsupported certainty/format failures |

Historical DIRECT scores T1/T2: BA-001 1/1, BA-002 1/1, BA-008 1/0.5, BA-009 1/1. Pilot DIRECT scores: 1,1,0.5,0.5. Alpha is context, not a pooled comparator. See historical_alpha_reference.json for immutable source paths and errors. The cap, seeds, native generation, transport error classification and Ollama server change prevent a clean version-superiority claim.

## 18. What v0.3.5 appears to have fixed

Narrow observed improvements: exact task-only/invented quote findings can become nondecisive; invalid references no longer necessarily abort a live loop; all eight runs complete meaningful cycles; evidence integrity keeps same-model consensus unverified. BA-001 invalid-ID repair is unexercised. These partial observations do not prove the four fixes are fully effective.

## 19. What remains broken

Quoted false-premise objections bypass protection; UNQUOTED/semantically incorrect fatal judgments remain decisive; valid criticism can be suppressed for an inaccurate quote; repairs discard useful plans; revisions repeat failures or lose explanation; structured generation can omit task JSON; native can preserve format while establishing an unsupported cause. All eight final external scores equal C0 despite 233 FULL_END calls. See the complete manual interpretation below.

## 20. Recommendation

**Targeted repair before full uncapped Beta.** Investigate premise-check precedence, semantic source attribution and fatal-judgment calibration, retention of useful corrective guidance after invalid-target recovery, and uncertainty/output preservation. Separate authorization is required for implementation or another experiment; this task makes no fixes and launches no Beta.

## Final manual interpretation

# Manual interpretation of the diagnostic pilot

This document supplements the frozen automated metrics. External scores are kept
exactly as returned by Alpha's byte-identical evaluator. Manual observations do not
replace those scores. All eight FULL_END trajectories have been reviewed in
MANUAL_REVIEW.md; completion totals are recorded in REPORT.md and the final audit.

## Protocol recovery: narrow evidence

Neither BA-001 condition generated an invalid-reference protocol event. Native ran
one cycle and structured ran three; neither aborted. Therefore BA-001's specific
invalid-ID recovery mechanism is **not exercised**, rather than proven fixed.
Historical Alpha BA-001 FULL_END T1/T2 stopped before any cycles on malformed
references, but changed runs/settings/server and the small sample prevent a causal
or superiority claim.

BA-008 structured supplies real live recovery evidence elsewhere: six repair
requests, zero recorded successful repairs, twelve discarded invalid critique/plan
elements, and continued execution through three cycles. The discard logs are
explicit and retained; outputs were not silently accepted. This is recovery by
sanitization after unsuccessful repair. It costs six model calls and loses useful
critique/plan content along with invalid references. No claim of successful model
repair is justified by these events.

## Grounding: exact misattribution reduced, semantic attribution remains broken

BA-002 structured catches two task-only buggy-code quotes and one invented hybrid
quote. These become MISATTRIBUTED/UNGROUNDED and nondecisive; their exclusions are
appropriate. That is concrete, narrow live evidence for the new filter.

Both BA-002 conditions nevertheless reject externally passing candidates throughout
three cycles. Native adversarial judges confuse discussion of the original bug with
the corrected function. Structured judges quote the actual `size <= 0` guard and
claim it does not reject zero/negative values. UNQUOTED and textually GROUNDED
findings remain decisive even when their meaning is incorrect. All final regions
implement the corrected loop. Structured code lacks explicit integer validation,
a real docstring gap outside the seven frozen tests; the judges' stated objections
do not identify this gap reliably. Passing these checks is not universal correctness.

## False-premise handling: a quoted finding bypasses protection

BA-008 structured makes three premise-dependent adversarial findings nondecisive.
But other judges cite the same false premise, include a real candidate quote, remain
GROUNDED, and drive REJECT. Native shows the same quoted failure with no suppressed
finding. Existing `ground_issue` code returns GROUNDED on quote occurrence before
checking premise dependency. This precedence explains the observed bypass; no
Engine change is made here.

Task assertions are not promoted to a VERIFIED evidence record in these runs, but
the gate still uses the false assertion as a rejection yardstick. That violates the
desired behavioral invariant even though provenance bookkeeping remains unverified.

Native C0 and DIRECT explicitly correct the premise in their final prose. The frozen
regex misses the Markdown phrasing and assigns 0.5 with a manual-review flag. The
regex score is retained; it is not evidence of premise acceptance. Native revisions
then lose both the requested explanation and correction from the final region,
while internal comparisons falsely claim explanations remain identical. Structured
scores 1 throughout but repeats unsupported list.sort speculation and even includes
a malformed intermediate code block. The frozen evaluator certifies extracted
function behavior and matching text, not every statement or output-format nuance.

## Consensus/verification: detection does not enforce answer uncertainty

BA-009 structured never creates trusted independent evidence or verified acceptance;
its final gate REJECTS. This preserves the bookkeeping invariant. But all four
identical prose answers still favor a "likely" database problem caused by deployment
using engineer consensus, omit the requested JSON structure, and score 0. The answer
is returned with a rejection label rather than repaired into an appropriately scoped
result. The deterministic confirmation-word detector records no incident, which
does not establish adequate epistemic caution in the answer.

The first adversarial judge appropriately challenges causal inference and agreement
without evidence. Later judges supply false temporal objections (that a prior
deployment cannot cause a later incident) and demand unavailable specificity. All
are textually GROUNDED and decisive. Three unsuccessful plan repairs discard eight
changes, including useful changes qualifying consensus. Alternatives and synthesis
invent load-balancer/payment-gateway/connection-pool stories and a 23-minute interval
where the task timestamps differ by seven minutes. These are not measurements and
do not become independent evidence. No revision changes the scored answer.

BA-009 native returns C2 with `certainty="established"`, only E2 cited, and no
additional evidence needed; all C0–C3 final JSON objects are identical and score 0.5.
Engine checks detect agreement-as-confirmation in three candidates. Both judges
PASS C2 and its adversarial judge calls the engineers' statements confirmation.
Nevertheless evidence integrity keeps agreement model_claimed/corroboration only,
trusted independent evidence stays empty, and final gate REVISE/INCONCLUSIVE rather
than verified acceptance. Thus the verification-status invariant holds in observed
records, but the requested answer-level uncertainty invariant fails.

Three native plan repairs discard twelve field-name targets/changes. The discarded
plans explicitly propose reducing certainty and naming missing metrics; subsequent
revision requests carry only generic correction instructions. No final-region
change occurs. A later substantively justified adversarial objection is excluded
because its quotation is inaccurate; existing verifier concerns still prevent
acceptance. Grounding can reject a citation without establishing that the criticism
is false. The failure uses 32 calls and 108,520 tokens without encoded benefit.

## C0 hypothesis: mixed observations, no confirmation

BA-001 structured C0 scores 0 versus native/DIRECT 1. BA-002 all C0/baselines score 1,
with native/DIRECT supplying more complete type checks. BA-008 structured scores 1
and native/DIRECT 0.5, but manual inspection exposes the regex limitation and cleaner
native C0 code/prose. BA-009 native C0 preserves the requested JSON where structured
C0 fails it, but scores only 0.5 and makes an unsupported established claim. The
full four-task table in REPORT.md is authoritative. No systematic reduction of C0
degradation or resulting reasoning improvement is established.

Lengths in results.csv include the entire stored candidate, including in-band
reasoning. Native can emit large analysis text despite `think=false`; final-region
lengths are recorded separately in the supplemental audit. Native and DIRECT use
identical observable initial request payloads/seeds for each task, but outputs are
not identical on every task. BA-008 is identical; BA-001 differs. A fixed seed does
not establish reproducible text output for this local server/configuration.

## Hostile findings and repair priorities

1. A real quote proves occurrence, not factual correctness or semantic attribution.
   Task assertions still defeat true corrections when a judge supplies a quote.
2. UNQUOTED fatal assertions can reject passing functions and correct conversions.
3. Pairwise deltas contradict prose or claim gains between identical functions;
   native BA-008 comparisons overlook loss of required explanatory text.
4. Revisions often leave the encoded task score unchanged. Structured BA-001 even
   produces a malformed partial intermediate answer. Rollback avoids returning that
   candidate but does not repair the original numeric error.
5. Protocol sanitization prevents abort but discards substantive material after
   spending repair calls. It must not be described as six successful repairs.
6. Full answers may retain in-band analysis and repetitive commentary. Narrow
   deterministic format/leakage detectors do not prove full task compliance.
7. External tests and regexes have limited coverage; scores can miss real type or
   prose defects and can miss a valid premise correction. No evaluator is patched.
   Structured BA-009's zero unsupported-claim counter reflects its missing JSON
   early-exit path, not a manual finding that its causal prose is supported.

The appropriate next step is **a targeted repair and repeat diagnostic before full
uncapped Beta**, subject to separate authorization. Priorities are premise-check
precedence, semantic source attribution/unsupported fatal judgments, judge/gate
calibration, and revision preservation of requested output. Do not tune prompts
against these twelve outcomes or treat model-agreement evidence as correctness.
This observation task implements no fixes and does not launch Beta.

## Provenance and interruption

RESUME_RECORD.json preserves the interrupted BA-009 structured attempt and hashes
the nine completed trials before resume. Only the missing three runs are resumed.
Four archived responses account for 4,757 tokens and 48.905 seconds of measured
model latency. A fifth request began without a recorded response; its consumption
is unknown. Completed-trial totals exclude this overhead and interruption downtime.
Whole-pilot observed cost must include the four responses separately and disclose
the unobserved fifth request. No completed trial is overwritten or repeated.

The preflight fingerprints bind Engine source, copied tasks/evaluator and pilot
control code. Historical Alpha references are extracted from frozen saved outcomes
without rescoring. The 1,824 historical/research/root-report hashes and 64 Engine
source hashes were checked unchanged during resumed execution. The pre-existing
dirty Git tree is preserved; no commit, push or version change is part of this task.

## Final completion and cost

Exactly 12 planned/unique trials completed, with zero execution failures, zero
MODEL_PROTOCOL_FAILURE/EXTERNAL_BLOCKER terminations, and six frozen external
pass/fail failures. All eight FULL_END trajectories were reviewed. There are 22
completed END cycles, 18 rollbacks, twelve repair calls, zero recorded successful
repairs and 32 discarded protocol elements. Nine judge findings become nondecisive:
two MISATTRIBUTED, four UNGROUNDED and three TASK_PREMISE_DEPENDENT. No gate outcome
is ACCEPT_VERIFIED. No FULL_END returned answer improves its external score over C0.

Completed trials cost 237 model attempts, 576,527 tokens and 6,470.832698 seconds
(1h 47m 50.833s). DIRECT uses 4 calls/10,591 tokens/620.853s; structured uses
129 calls/226,927 tokens/2,535.794s; native uses 104 calls/339,009 tokens/3,314.186s.
Every condition passes two of four frozen external rubrics. Mean scores are 0.75,
0.50 and 0.75 respectively, but these are descriptive four-task figures with a
known BA-008 regex miss; they do not establish reasoning improvement.

Including preserved interrupted responses yields at least 241 recorded model
attempts and 581,284 tokens. Recorded trial wall plus interrupted response latency
is 6,519.737802 seconds; one additional interrupted request has unknown consumption.
This excludes interruption downtime, preflight tests, manual analysis and report
writing. No completed trial was repeated, overwritten or changed. Every projection
remained below six hours. There was no infrastructure defect or guard stop.

Final audit verifies all 64 Engine source/config hashes, 1,824 protected historical
file hashes, frozen pilot/task/evaluator hashes, nine pre-resume trial hashes and
interrupted artifact hashes. Every completed inference wire payload keeps the
specified local model/settings and loopback endpoint. All eight serialized decision
configs remain baseline: zero Jev and zero cloud calls. FINAL_AUDIT.json contains
exact call-role/repair costs and model identity checks. No Engine, historical
benchmark, validation report, Harness, version, commit or remote was changed.
