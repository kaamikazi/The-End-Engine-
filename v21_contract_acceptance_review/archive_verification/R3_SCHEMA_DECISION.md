# Independent R3 decision

**ACCEPT for separately authorized implementation planning.** I found no demonstrated material R3 specification contradiction. This is contract acceptance within my assigned R3/cross-contract scope, not runtime acceptance, migration authorization, empirical performance evidence or authenticated human scientific approval.

I am a fresh independent AI reviewer, not the v2.1 author. I read the complete user task, all seventeen v2.1 specification documents plus DOCUMENT_VALIDATION_SUMMARY.json, and the previous V2_INDEPENDENT_REVIEW.md. I inspected the actual unchanged Publication._verify_completed/verify_semantics and certification.require_certification_eligible source for cross-axis consistency. I did not import an author checker or execute the runtime, provider, benchmark, historical suites or new capture protocol. Only reviewer-owned artifacts were written. The reviewed schema raw SHA-256 is `ab900d6d1c40eea67dbe9f4f4c31fcbb90cadaddbdcbfa56c090aa742d72ced9` at the supplied checkpoint `783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e`; checkpoint Git identity is separately coordinated, not established by the schema hash.

## Independent standard validation

Installed **python-jsonschema 4.26.0**, running under the existing Python 3.10.11 executable with `-B`, accepts the schema against the Draft-07 metaschema. All 91 local `$ref` occurrences resolve without network access. No packages were installed or downloaded. The primary Python 3.12 environment has no native jsonschema installation; an attempted read-only reuse of Python 3.10 site-packages fails because compiled `rpds.rpds` is incompatible/unavailable to 3.12. The reproduced traceback is retained as `r3_raw/PRIMARY312_IMPORT_FAILURE.txt`. It is a setup failure, not a passing contract assertion or a source defect.

The independently authored script produced **1,161 structural fixture expectations: 1,161 matched; 63 structurally accepted, 1,098 rejected; zero multi-member cases**. This includes a 540-cell independently specified variant/provenance/reason/snapshot matrix, required and nested-required omissions, additional properties throughout instantiated nested objects, all forbidden outer legacy fields with several values, malformed enum/version/boolean combinations, candidate/lineage/handle branches, numeric lower bounds, nullable versus missing fields, diagnostic publication branches and typed errors outside the union. Draft-07 mathematically integral floats are accepted as integers; booleans, zero attempt IDs and fractional IDs are rejected. Field-matrix checks cover all 87 rows' base definitions and required/forbidden presence; no discrepancy was found. Conditional matrix cells still defer to the referenced schema rather than flattening its `anyOf` logic.

Thirty-five independent synthetic semantic controls and eight strict-parser controls also matched expectations. Those controls use explicit reviewer-owned synthetic external facts; they do not verify a real source artifact, writer-domain attestation, guard, read pin or capture. Raw fixtures, rejected-instance errors, semantic failures and scripts are retained. Initial 874-case/34-control summary and script are retained in `r3_raw/first_run`; the expansion added nested-required omissions and negative total bounds, not assertion weakening. No reviewer contract assertion failed in either run. Historical failures and unavailable historical external bundles have not been relabeled or rerun.

## Partition and preserved meaning

The required `variant` property has a different constant in each top-level `oneOf` branch (schema lines 1880 onward). Hence any structural instance can satisfy at most one branch, independently of finite fixture coverage. Required versions and closed envelope grammar prevent a missing/mixed discriminator from matching. The fixture matrix checks the remaining routing constraints rather than using branch selection as the expected answer.

The normative routing is explicit in R3_EXCLUSIVE_OUTCOME_UNION.md:5–12. VERIFIED with COMPLETED/NO_ACTIONABLE_REVISION/INVALID_RESPONSE/PROTOCOL_FAILURE permits NORMAL; VERIFIED with the five restricted reasons permits RESTRICTED. INTERRUPTED or UNKNOWN provenance permits RESTRICTED only with its seven allowed reasons. BLOCKED never permits either eligible member. Persisted verified INTERRUPTED matches RESTRICTED only; uncertain COMPLETED/NO_ACTIONABLE_REVISION matches neither. Typed ArtifactIntegrity/RecoveryIntegrityHold remains an exception category outside serialization.

Every variant fixes `answer_success=NOT_ASSERTED`, `scientific_score_available=false`, `scientific_score_status=NOT_COMPUTED`, and `scientific_score=null`. Artifact persistence is scoped to the referenced source file, distinct from envelope persistence and answer correctness. A diagnostic cannot select a candidate, carry a normal source-publication descriptor, or label candidate/handle bindings source-certified. Outer `result`, `C0`, `FINAL`, old completion flags and legacy payload fields fail closed even when null/false. A version-aware reader must route before shape projection; compatibility with arbitrary noncompliant unknown readers is explicitly not promised.

## Structural versus complete normative acceptance

Draft-07 does **not** enforce `x-semantic-rules`. The independent standard validator intentionally accepts structurally correct counterexamples such as a same-hash foreign source path, a rehashed substitute answer, a wrong selected reference, missing actual cut proof, an unsupported known-empty history and false graph cardinality. The separate synthetic semantic controls reject those under E01/E02/A02/C01/C02/C03/P01. These are demonstrated boundaries of standard schema validation, not contract defects: R3_EXCLUSIVE_OUTCOME_UNION.md:34 explicitly requires structural validation **and** all trusted-evidence rules. A producer/reader that implements only Draft-07 would violate the contract.

The full rule audit is in R3_SEMANTIC_RULE_AUDIT.md. The checks are sufficiently precise and testable for planning: trusted independent evidence predicates resolve source origin, same-cut authority, references, candidate identity, graph coverage and arithmetic. These remain mandatory future engineering, not implemented behavior.

## Cross-contract result and classifications

`R1_R3_CROSS_CONTRACT_TESTS.json` preserves separate R1 and source-verification axes. A guarded S observation can coexist with an independently valid legacy terminal, with new complete totals null. I/U/X cannot make a current eligible v2.1 view. An A graph count on BLOCKED raw provenance remains diagnostic and never overrides source rejection. An uncertain restricted terminal may preserve a bound C0 while later cost is unknown, with partial accounting. A prior immutable RESULT can be referenced forensically with `currently_verified=false` while current verification rejects it. A generic error is not a grounded diagnostic cause.

**BLOCKING_CONTRACT_DEFECT:** none demonstrated within this scope.

**IMPLEMENTATION_PREREQUISITE:** trusted same-cut F01 source verification, audited L1/L2 writer coverage and native pins, immutable captured-byte refs, independent origin checks, strict parsing, all fourteen semantic rules, opt-in reader routing and retained R4/R5 execution tests. Existing code is not falsely claimed to implement them. Required L2 coverage/ordering can fall back to I/X rather than making an unjustified strong claim; no impossible guarantee was established in this review.

**SCIENTIFIC_LIMITATION:** recorded local evidence cannot establish provider inference, authenticated provider billing, answer correctness, empirical model performance or hostile-host security. The contract states those limits honestly.

**OPTIONAL_ENHANCEMENT:** clearer A04 wording could replace its informal `INCONSISTENT` shorthand with the actual `INCONSISTENT_WITH_CURRENT_ROW` enum where appropriate. This is nonblocking: the actual schema enum is exact, `OBSERVED` is an expressly legal retention path, arithmetic and complete-cost prohibitions remain precise, and there is no demonstrated impossible/unsafe required serialization.

Reproduce with the installed interpreter:

```powershell
& 'C:\Users\imran\AppData\Local\Programs\Python\Python310\python.exe' -B 'E:\The End Engine\v21_contract_acceptance_review\r3_raw\independent_r3_review.py'
```

Machine-readable counts and limits are in R3_STANDARD_VALIDATOR_RESULTS.json. Review assertion success does not authorize implementation or replace later acceptance.
