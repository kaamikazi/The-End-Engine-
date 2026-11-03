# R3 validator and opt-in adapter plan

No schema edits or adapter implementation are made. Accepted raw schema SHA-256: ab900d6d1c40eea67dbe9f4f4c31fcbb90cadaddbdcbfa56c090aa742d72ced9. Preserve exact end-outcome/2.1-proposal.1 and end-certification/2.1-proposal.1. Its 24 definitions,87 field rows and14 semantic rules are normative. Optional A04 wording clarification is not required for this implementation and is not authorization to edit the schema.

## Three distinct validation stages

1. STRICT_SOURCE_PARSING: source-format-aware strict_json.loads on captured raw bytes; reject duplicate keys at all depths, nonfinite constants/overflow, invalid encoding, size/depth/node excess and wrong exact source types before information is lost. Keep canonical raw versus logical digest domains distinct. Draft-07 integral numeric values follow Draft-07; legacy witness exact-int rules remain separate. Do not modify F04.
2. STRUCTURAL_VALIDATION: installed established Draft-07 implementation checks exact pinned schema, local-only refs, required/forbidden/nullable/additionalProperties/oneOf/enum/nested/bounds branches. Fail startup if schema hash or validator capability differs. No remote ref resolution. Structural pass says nothing about source origin, selection, graph authority or provider events.
3. EXTERNAL_EVIDENCE_SEMANTIC_VALIDATION: all14 rules below against actual SealedCapture, independently recomputed graph and same-cut SourceProof. Serialized statuses, a caller's dictionary, public constructor flags or a synthetic oracle are not proof objects. A trusted local producer profile remains a declared cooperative trust assumption, not cryptographic human/provider authentication.

New proposed APIs: validation.validate_structure, semantic_rules.validate_evidence, versioning.route_reader and adapter.observe_run_v21 / read_outcome_v21. They are not existing functions. Validators should return explicit stage/rule failures internally; the public adapter retains typed exceptions for inputs outside the accepted union rather than serializing arbitrary errors.

## Real-evidence implementation of all fourteen rules

| Rule | Planned implementation input and check | Required positive / negative |
|---|---|---|
| J01 | Original raw tokens + bounded strict parser; duplicates/nonfinite before dict projection | Valid finite exponent/integral value; nested duplicate/NaN/Infinity/overflow/bool-as-source-ID rejection |
| E01 | Actual unchanged completed-core SourceProof bound to same held A/S cut, exact raw source/path/run/task/condition/identity/closure/report/candidates | Genuine current source positive; old proof, other capture/task/path with same hash, forged status negative |
| E02 | Actual controller enrollment/epoch, guard and pin evidence, full inventory and mandatory witness graph | Complete stable cut positive; absent domain/mandatory reservation, excluded writer or equality-only proof negative |
| A01 | Independently derived supported-fact set; emitted scoped claims and refs must cover it exactly without invention; resolve capture raw bytes/origin | Retained narrow group positive; omitted justified fact, foreign run/capture or missing ref negative |
| A02 | Verified closed graph ID set, tier A, exact sorted IDs/scope/cardinality equality | Positive1 and positively empty0; count2/ID1, orphan or unproved zero negative |
| A03 | Exact original execution-channel identity/intent/crosslink evidence, distinct channels | Original reservation+dispatch positive; copies/hard links/relabelled channels negative |
| A04 | Typed captured usage and settlement bindings/arithmetic; raw receipt status independent | Corroborated recorded10/5/15 with declared raw failure; conflicting usage retained OBSERVED, never complete/corroborated |
| A05 | A + current VERIFIED source + closure/full covered raw/usage/settlement set; exact sums/no unknown/outstanding | Complete known source positive; subset, unknown, bad raw, unclosed or inconsistent totals negative |
| C01 | Original captured candidate/attempt/content/digests and earlier lineage/initial identity, not array guess | Original bound content positive; rehashed substitute, guessed C0 or later parent negative |
| C02 | Selected ref resolves uniquely to PRESENT eligible source-bound candidate and actual handle/run/task/call/attempt/wire/provenance/settlement/order proof | Valid selected C0 positive; missing/rebound/foreign/duplicate/unavailable handle negative |
| C03 | Diagnostic no selection; known-empty requires positive complete empty history; restricted preserves justified C0 | Restricted C0 + unknown later usage positive; diagnostic FINAL or unsupported empty history negative |
| P01 | Exact referenced source-file bytes/hash/path basename; separate unique diagnostic record; immutable suspect prior only | RESULT/COMMON source proof and memory-only diagnostic positive; different path/hash, normal prepared diagnostic target or false persistence negative |
| V01 | Deterministic grounded-cause-first routing, then actual source provenance/reason; typed category outside serialization | Verified INTERRUPTED restricted; uncertain COMPLETED, BLOCKED eligible or generic-error diagnostic negative |
| L01 | Exact opt-in schema+contract route before shape; legacy normal uses original full verifier; current hold is diagnostic | Archived/current normal positive at old reader; mixed/unknown tags, forged legacy fields, current hold as RunResult negative |

## Union projection and API boundary

| View | Conditions before return |
|---|---|
| ELIGIBLE_NORMAL_TERMINAL | Existing source verified in same A/S cut; VERIFIED provenance; COMPLETED/NO_ACTIONABLE_REVISION/INVALID_RESPONSE/PROTOCOL_FAILURE |
| ELIGIBLE_RESTRICTED_TERMINAL | Same source requirement; VERIFIED with INTERRUPTED/BUDGET_EXHAUSTED/TIME_EXHAUSTED/EXTERNAL_BLOCKER/UNRESOLVED, or INTERRUPTED/UNKNOWN provenance with those five plus INVALID_RESPONSE/PROTOCOL_FAILURE |
| NONCERTIFYING_DIAGNOSTIC | Recognized grounded cause first: INTEGRITY_HOLD has actual BLOCKED; snapshot/unsupported causes have UNKNOWN and I/U/X; no selected certified candidate or normal source descriptor |
| Typed error, outside union | Ungrounded request, unrelated I/O/programming/source-verifier errors, unsupported combination; no invented fourth JSON member |

Verified persisted INTERRUPTED is always restricted. Uncertain COMPLETED/NO_ACTIONABLE_REVISION is never accepted. A source-valid legacy terminal can have S new accounting and null stronger totals. I/U/X cannot produce a current eligible view. A strong count over BLOCKED raw evidence remains noncertifying, never complete cost. A stable A/S source verification failure for another reason is not snapshot-unavailable; propagate the real error with captured observations.

Every returned member keeps answer_success NOT_ASSERTED, scientific_score_available false, scientific_score null and NOT_COMPUTED. No outer/embedded result/C0/FINAL/old completion payload, even null/false. Missing/unknown candidates differ from positively empty history. Valid old C0 can remain selected only under genuine source proof; invalid later raw content is retained without selecting it. All envelope fields derive from trusted immutable facts, not caller patches.

The observer adapter reads existing runs and never calls execute(), Session.finish(), _build(), restore_without_dispatch(), publish() or close_generation(). Existing execute return/exception behavior remains unchanged. Expose the new interface only through a separately named opt-in module/launcher, not the existing root Engine console script or pyproject package discovery. Preflight a single canonical existing src/shared module origin to avoid duplicate in-process owner/lock maps.

## Persistence without circular hashes

Default is in-memory envelope. Eligible publication.sha256 hashes the existing immutable source artifact; artifact_persisted refers to that source, not the returned envelope. Optional diagnostic persistence writes a distinct uniquely named diagnostic evidence record AFTER E under publication/recovery_holds/<new-id>.json, with no embedded legacy RunResult and no self-hash field. Compute the exact raw record hash, then build/validate the returned envelope referencing it. The record is the referenced diagnostic artifact; the envelope is a separate view, so no file must contain its own raw SHA-256. No RESULT/COMMON_RESULT, source prepared anchor or existing record is written/overwritten. An output storage failure propagates; it cannot return persisted=true. A later capture inventories the new known diagnostic metadata as such, not an additional attempt.

## Dependency and test gates

Root pyproject has no mandatory dependencies and packages end_engine only; do not edit it for this feature. The review's established jsonschema4.26.0 lives in Python3.10; Engine runtime requires>=3.11 and working runtime is3.12. Reusing its compiled rpds package in3.12 failed and is not an implementation strategy. Future D needs explicit authorization for an isolated optional validator environment with matching3.12 wheels, pinned direct/transitive identities and license/dependency review. Do not install/download now. If unavailable, new validated outcome API remains unavailable/typed error; do not silently ship the author subset checker as equivalent standard validation.

Planned D vectors: retain all1161 independent structural fixtures,35 explicitly synthetic semantic fixtures and8 strict-parser fixtures as a separate review seed corpus; add28 actual captured-evidence controls (one positive/negative per14 rules) and8 parser/resource boundaries =1240 planned vectors. Synthetic oracles remain labeled and cannot discharge real origin/capture predicates. Actual source/capture/adapter end-to-end tests arrive through B/C/E/F. No measured future runtime or all-instance proof is claimed.
