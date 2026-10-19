# R3 — prospective tagged union and candidate authority

Proposed envelope ID: `end-run-outcome/2-proposal.1`, paired with contract_version `end-certification-contract-v2-proposal.1`. No runtime/schema version is changed in this task. Current normal records retain implementation_version `1.0.1` and lack both schema_version and is_completed_result. Current blocked diagnostics use abc-r3-blocked-recovery-v1 with is_completed_result=false. Graph revision1.0.2 is not an output-union discriminator.

## Artifact discriminators

| artifact_class | Required completion meaning | New RESULT/normal prepared certificate | Candidate/accounting authority |
|---|---|---|---|
| NORMAL_COMPLETED_RESULT | is_completed_result=true means persisted terminal binding verified, not answer correctness | Only through current F01 verification/lease/pins/exclusive link | Eligible supported selection/lineage; R1 authority still explicit |
| UNKNOWN_OR_INTERRUPTED_RUN | Persisted restricted terminal can be true; scientific success remains false | Allowed only if no contradictory BLOCKED evidence, compatible termination and valid closure | Known reservations can coexist with unknown usage; only supported candidates, no invented candidate for unresolved call |
| NON_CERTIFYING_INTEGRITY_DIAGNOSTIC | is_completed_result=false; certification.status=NOT_CERTIFIED | No new normal RESULT or normal prepared anchor | Mandatory scoped R1 observations and preserved candidate/handle observations; no certified selected FINAL |
| PROVENANCE_INTEGRITY_FAILURE | Typed rejection, optionally surfaced via the noncertifying diagnostic; never a success alias | Preserve any preexisting suspect final; no replacement | Failed invariants and raw observations remain distinct from trusted history |

The envelope MUST keep artifact_class, provenance_status, termination_reason, candidate_authority, accounting_authority and scientific_scores separate. All engineering diagnostic scores remain null. VERIFIED provenance is not universal correctness; INVALID_RESPONSE is a termination reason, UNKNOWN generally an attempt status.

## Candidate forms

| State | Required representation | Forbidden inference |
|---|---|---|
| SELECTED_AND_PROVENANCE_CERTIFIED | Existing eligible candidate ID/content hash, run/attempt ID, parent IDs and bound output handle; current publication verifies all bindings | Does not certify semantic truth or intelligence |
| OBSERVED_INCOMPLETE_PROVENANCE | Observation object: original source bytes/hash, candidate/handle IDs if evidenced, authority tier, missing dimensions | No trusted selection or complete lineage |
| PRESERVED_C0 | Intact partial-history recovery retains the original first candidate, identity and handle; positive recovery must still select valid C0 under existing policy | Do not create C0 merely by assigning index0 to an uncertain row |
| KNOWN_UNCERTIFIED_CANDIDATE | Content/ID recorded but publication/provenance not eligible; preserved as observed history | No FINAL promotion because content exists |
| MISSING_CANDIDATE | availability=MISSING, expected source/identity and failed check; content null only because unavailable | Do not manufacture answer, ID, zero candidates or a replacement |
| UNAVAILABLE_LINEAGE | lineage=null with reason and observed individual parent references separately retained | Do not invent parentage from stage order |

Output handles require exact run/task/call binding, distinct format/identity, original sealed wire/provenance hashes, settled-before-use order, settlement-witness equality and same handle referenced by later control requests. A diagnostic may expose an observed handle while its binding is UNVERIFIED/INCONSISTENT. Unbound or rebound handles cannot authorize references or selection. Missing original candidate bytes stay missing.

## Absent / null / empty / observed / selected

- Absent means a field is outside this artifact schema/version; e.g. current diagnostic lacks result.final_candidate and top-level C0/FINAL. Do not access it as a RunResult.
- Null means a defined field is unavailable, unknown or has no eligible selection, with its explicit reason. It never means zero, an empty set, or a lost-but-reconstructable answer.
- [] or {} means the covered collection is known empty, requiring coverage authority. Corrupt evidence cannot prove emptiness.
- Explicit observation means source-grounded content/identity is retained with authority and limitations. It is not selected or certified.
- Selected and provenance-certified means eligible selection binding has actually passed normal verification. Model-generated content remains semantically unverified.

In prospective diagnostics `selected_candidate=null` is mandatory with selection_status=NOT_CERTIFIED; candidate_observations contains supported individual observations. Legacy top-level C0/FINAL are not synthesized. An existing prior selected result can be preserved as `prior_result_observation` with currently_verified=false, not copied into selected_candidate.

## Compatibility and consumers

Use a separately authorized opt-in adapter/entry point to emit the v2 union; retain current APIs and recorded files. A legacy normal reader must first validate the full legacy payload/publication/identity contract via the appropriate verifier; absence of a diagnostic tag alone is not sufficient. A diagnostic reader recognizes an exact diagnostic schema plus false completion flag. Unknown, contradictory or mixed tags fail closed. No historical file is relabeled or rewritten.

Affected callers include tests/helpers.py ScenarioCase, tests/accounting/test_resources.py, tests/corrections/{test_f02,test_interactions,test_provenance_r3,test_recovery_hold}.py, src/shared/wiring.py, reproduce.py/validation scripts and private reviewer finalizers. They read final_candidate, all_generated_candidates, generation_closed, provider_records or artifact_payload_sha256 directly. External consumers are unknown. Inventory and old/new-reader tests are approval gates, not presumed complete. Diagnostics are not evaluator inputs. Keep valid C0, numeric-invalid raw candidate/no FINAL, missing candidate/handle and interrupted unknown-usage positives and negatives separately.
