# R1 — mandatory scoped accounting observations

This is a prospective normative contract, not current output. Requirements below become binding only after separate review and a separately authorized implementation. Overall BLOCKED prevents complete-run certification but MUST NOT erase independently justified observations. Full-run null is not a substitute for required narrow information.

## Claim object and mandatory dimensions

Every accounting claim MUST carry: claim_kind; value (number, ID set, usage object or null); evidence_authority; scope (run identity, attempt IDs, covered source set and exclusions); anchors (repository/run-relative paths and exact SHA-256, independently captured when available); verification_status; limitations; complete_run_certification_permitted. Claims with different trust tiers MUST NOT share a single undifferentiated trusted=true flag. Hashes of current bytes are observations, not authenticity guarantees.

| Kind | Value allowed | Required authority/checks | Scope and limitation | Full certification |
|---|---|---|---|---|
| RECORDED_ATTEMPT_OBSERVATION | Visible ID(s)/count or null | A retained source asserts the identity; label uncorroborated if only mutable ledger | Visible recorded claim only, not occurrence/uniqueness/provider inference | false |
| CORROBORATED_RESERVATION_DISPATCH_IDENTITY | IDs and distinct count | Unchanged independently captured reservation and dispatch witnesses, run/identity/stage binding, no ID duplication; no counting file copies as new events | Corroborated recorded event in stated anchor set; RESERVED need not have dispatched | false when overall BLOCKED |
| INDEPENDENTLY_VERIFIED_ATTEMPT_CARDINALITY | Exact distinct visible anchored count | Full graph-only ordering/identity/uniqueness/bidirectional coverage across ledger and independent witnesses, stable snapshot, explicit covered set | Corroborated recorded-attempt cardinality within that set, not authenticated inference or proof against erased events outside trusted-writer model | false when overall BLOCKED |
| SUPPORTED_SETTLEMENT_RESPONSE_BINDING | Per-attempt status/commitments | Exact settlement equality and independently captured dispatch/response commitments; current raw response validity assessed separately | Commitment or metadata binding may survive damaged wire; never label damaged raw journal historically trustworthy | false when overall BLOCKED |
| INDEPENDENTLY_VERIFIED_USAGE_OBSERVATION | Per-attempt recorded input/output/total and provenance tier | Verify type/nonnegative/finite/sum constraints, independent settlement commitment and source equality; raw provider receipt checked independently where available | Recorded metadata corroboration is explicitly distinct from raw receipt validation, complete cost and provider attestation | false when overall BLOCKED |
| COMPLETE_RUN_ACCOUNTING | Complete counts/totals only if justified, otherwise null | Complete scoped reservation set, settlement/usage coverage, closure, no unresolved usage, full current provenance and publication eligibility | Exact total within declared local writer/accounting model; does not measure reasoning quality | ONLY if all required provenance/closure/F01 conditions pass; never BLOCKED |
| UNKNOWN_OR_INCONSISTENT_COST | null full totals, named supported observations/subsets | Missing or contradictory cost coverage identified, not silently summed away | Unknown is not zero/refund, known subset is not total | false |

`physical_attempts` historically counts reserved ledger rows, including failures, cancellations and outstanding reservations. It is not a count of authenticated provider inference calls. The prospective field `observed_anchored_attempt_cardinality` MUST use the scoped authority object above; it MUST NOT silently reinterpret the old RunResult field. Synthetic Script dispatch instrumentation corroborates a test setup but cannot retroactively become durable production evidence.

## Sixteen cases: required information, not blanket null or blanket legacy 1

R1_SIXTEEN_CASE_MATRIX.csv treats each exact mutation separately and lists source-specific anchor hashes. Fourteen coherent independent graphs support IDs [1] and distinct recorded cardinality1 in their visible covered set, even while wire provenance is BLOCKED. All fourteen MUST expose that numeric scoped observation with the graph tier. A copied journal/third response record contributes no new ID. Wrong run/stage/attempt in a damaged wire header cannot override independent run-bound witnesses. Rehashed substituted wire cannot overrule the original dispatch commitment.

For ledger_disagreement, reservation/dispatch witnesses still corroborate one visible event, but current ledger content conflicts with original settlement. For missing_response_anchor, reservation/dispatch still corroborate one event, while registered settlement-response binding is incomplete. Both MUST expose the narrower numeric identity observation and failed dimensions; neither may claim graph-complete or trusted settlement authority. A renamed preserved receipt may be inspected and hashed as forensic evidence; it MUST NOT be restored, renamed into validity or silently treated as the missing registered anchor.

Original settlement metadata 10/5/15 remains reportable as a labeled witness observation in all cases where its own bytes/identity can be read and checked. In fourteen cases it is corroborated recorded settlement metadata with intact response commitment; current damaged raw response is not thereby validated. In the other two it is an original-witness observation with current binding/content conflict explicitly recorded. Full-run total_tokens and complete accounting remain unverified/null. Neither a checksum-refreshed damaged ledger nor a correct token arithmetic sum can manufacture complete-run authority.

## Unknown, zero and incomplete distinctions

- Unknown count: no justified coverage/identity; numeric value null with reason. Do not infer zero from an empty/erased mutable ledger.
- Observed incompletely settled attempt: identity/count can be known while settlement/cost remains unknown; preserve reservation and no-replay charge.
- Corroborated count: stable independently verified scoped set supports exact distinct cardinality; do not claim more than its scope.
- Fully verified accounting: all completeness/settlement/closure/provenance gates pass; publication still requires unchanged F01 mechanisms.
- Corrupt evidence: retain bytes, errors and any separately supported observations; block trust promotion.
- Zero is allowed only for a verified empty covered set with explicit completeness authority and no contradictory independent attempts. Null, empty, missing and zero MUST remain distinct.

## Prospective example (no current implementation claim)

```json
{"contract_version":"end-certification-contract-v2-proposal.1","overall_provenance":"BLOCKED","accounting_observations":[{"claim_kind":"INDEPENDENTLY_VERIFIED_ATTEMPT_CARDINALITY","value":1,"evidence_authority":"INDEPENDENT_VISIBLE_RESERVATION_DISPATCH_SETTLEMENT_GRAPH","scope":{"attempt_ids":[1],"coverage":"declared run-bound visible witness set","excludes":"authenticated inference and erased events outside trust model"},"anchors":[{"path":"publication/attempts/000001.reservation.json","sha256":"EXACT_OBSERVED_HASH_REQUIRED"}],"verification_status":"CORROBORATED_WITHIN_SCOPE","limitations":["current raw wire is corrupt"],"complete_run_certification_permitted":false}],"complete_run_accounting":{"physical_attempts":null,"total_tokens":null,"status":"NOT_CERTIFIED"}}
```

The example's hash marker is a documentation placeholder, forbidden in a real observation. Actual per-case witnesses/hashes are in the matrix. Observation reads must be snapshot-consistent or individually timestamped/hashed with inconsistency explicitly reported; a changed anchor set invalidates the stronger claim, not every surviving narrower fact. No new settlement witness may be fabricated during recovery.

Acceptance proposal: sixteen versioned controls require the mandatory tier-specific value/IDs/anchors and failed dimensions, plus raw preservation, no normal final/prepared certificate, no replay and no budget reset. Independent positives include genuinely unknown identities, zero justified empty history, unknown usage with known reservation, duplicate/orphan/rebound attempts and inconsistent/absent settlements. No old assertion is edited or automatically restored.
