# R1 observation extraction plan

IP04 is partially implemented by existing execution-only witnesses and reconciliation, not by a new authority extractor. Future observations.py/predicates.py consume only SealedCapture and qualified original recording/capture evidence. Do not accept current graph.overall or a caller's VERIFIED flag as the input authority.

## Predicate pipeline

| Proposed predicate | Exact captured conditions | Failing condition and surviving authority |
|---|---|---|
| Grounded identity | Existing abc-r2-run-v1 exact requested/effective canonical digests; run/task/condition/output/ledger/mode match actual profile | Ungrounded run: typed rejection; do not fabricate an envelope |
| Global ledger | Exact envelope state/state_sha256; lab-ledger-v1, admitted limits/runs; IDs are exact integers in global order1..N with no duplicates before own projection | Preserve contradictory raw rows as observations, never rebuild/deduplicate; own zero/count cannot come from damaged global state |
| Reservation/dispatch group | Original abc-r3-reservation-v1 + abc-r2-dispatch-anchor-v1, matching run/aid/identity; reservation purpose/ceilings/start; exact sealed intent, task/call/stage, compiler references/settings/wire/provenance | Two copies of one source are not two channels. One supported source gives RECORDED_IDENTITY; independently matching original pair gives only its scoped corroboration |
| Settlement | Exact abc-r3-settlement-v1 schema; full canonical recorded row equals current captured row; raw dispatch and response-file commitments match | Missing/contradictory row retains original metadata as observed/conflicting; no complete current usage |
| Response dimension | Registered response file at exact expected path; kind/run/aid/stage/last-record/raw commitment and settlement binding | Moved receipt stays forensic; cannot satisfy expected registered absence. Explicit matching NO_RESPONSE for failed/interrupted settlement differs from disappeared expected response |
| Full visible accounting set | Proven A/S common cut, all original mandatory witness dimensions for every covered ID, complete classified namespace, no unbound eligible extra/orphan, uniqueness and source identity | Closed => A; stable missing/unknown/conflicting witness with facts => S; in-cut change/domain breach => U; no cut => I/X |
| Raw integrity | Exact journal header/tail record chain, index/order, schema, base64/raw/decoded bytes, registered commitments and exact provider receipt/ledger types | Raw BLOCKED is independent of an intact accounting identity graph and vetoes normal source certification/complete totals |
| Complete costs | A + current source provenance VERIFIED + actual closed generation + exact full reservation/settlement/raw/usage coverage; no unknown/outstanding/conflicting costs; nonnegative valid per-field values and exact sums | complete_totals=null with explicit reason; preserve known subsets at named scope. Never unknown→0/refund |

Canonical source identity/state/record hashes use the existing strict_json canonical domain; evidence_ref and publication hashes cover exact raw captured bytes. No Unicode/newline reencoding. New inventory/content digests include sorted canonical names, types/file IDs, hashes and explicit absences, not only expected files. Each origin reference includes its qualified execution/capture channel; matching bytes alone do not authenticate that origin.

## Emission algorithm proposed for later implementation

First derive the set of every supportable fact from captured source formats and checked original origin channels. Assign a narrow source-group scope before aggregation. Emit all justified facts, including negative coverage/failed dimension diagnostics; compare emitted IDs/refs against the derived fact set so a failed overall proof cannot silently erase valid lower observations. Do not treat arbitrary bytes as typed candidate/attempt facts.

Then apply accepted priority U > A/S > I > X. A/S requires the full domain/cut, not timestamped reads. A versus S depends on accounting graph closure, not whether the raw response is valid. I has no graph-wide absence/completeness assertion. U retains only independently safe lower facts with null strong digests; no automatic same-epoch recovery to A. X has no supportable attempt/candidate association, empty observations and an explicit unsupported reason; it is not zero historical attempts.

| Claim kind | Executable evidence predicate before emission | Positive and negative plan |
|---|---|---|
| RECORDED_IDENTITY | One readable strictly typed source names this run/attempt with exact retained raw ref; authority no stronger than origin | Original reservation positive; foreign/invalid identity negative; unknown origin unverified |
| CORROBORATED_RESERVATION_DISPATCH | Both independently recorded original channels bind exact reservation identity and sealed intent | Original pair positive; copied/relabelled same source negative |
| CORROBORATED_IDENTITY_GROUP | At least two named distinct execution channels, exact cross-bindings; state which mandatory dimension failed | Dispatch+settlement with missing reservation positive; duplicated paths/hard links negative |
| ANCHORED_GRAPH_CARDINALITY | Tier A, GUARDED_VISIBLE_GRAPH, exact same sorted distinct own IDs in verified graph/value/scope; cardinality=len(IDs); no unknown members | One exact identity positive; unknown orphan/cardinality mismatch negative; positive zero only complete positively empty set |
| SETTLEMENT_METADATA | Original settlement record, exact status of current-row/dispatch/response equality; retain contradictions without changing them | Matching usage10/5/15 positive; ledger disagreement remains original observation, not current corroboration |
| RESPONSE_COMMITMENT | Actual registered anchor and source binding or explicit expected absence/NO_RESPONSE evidence | Matching receipt positive; moved/rebound commitment negative |
| USAGE_METADATA | Exact token/seconds types, arithmetic when known, source refs/status and raw-validation dimension separate | Known subset with null total positive; negative/nonfinite/10+5=16 promoted corroboration negative |

All claims carry actual capture/run/attempt scope, source_refs, verification_status, limitations and full_run_certification_permitted=false. Every supported count describes recorded identities in that exact set, never actual model inference. A positive scoped count cannot override a BLOCKED journal.

## Sixteen original mutations

_evidence/R1_SIXTEEN_EXECUTABLE_PREDICATE_PLAN.csv preserves every original ID, exact retained witness refs/hashes, capture predicate, two planned authority cases and usage limits. Use the exact MUTATIONS dictionary and helper bodies in tests/corrections/test_f02.py; do not replace recomputed hashes, duplicated record/file, reordered records, moved journal/receipt, invalid base64 or torn append with generic corruption.

Fourteen conditional A-count1 cases: changed_wire, changed_wire_digest, changed_decoded_response, invalid_base64, changed_response_digest, missing_settled_journal, duplicate_attempt_file, duplicate_response_record, wrong_stage, wrong_run, wrong_attempt, incorrect_record_order, settled_torn_tail, recomputed_hashes_still_fail_anchor. The complete independent accounting graph and a **new real A cut/domain** must first hold. Raw provenance remains BLOCKED; totals null and no normal certificate. A known moved/identical raw representation may be classified as the same identity only by exact captured identity/content/chain evidence; undecidable extra evidence prevents A.

ledger_disagreement and missing_response_anchor retain the original reservation/dispatch identity1 only within that group's scope. Under proven stable cut they are S, with the failed settlement or registered response dimension explicit. Without a common cut, each of all16 cases can retain I per-source/group identity1 if independently justified; otherwise X, not guessed1 or zero. The archived historical fixtures have at most I because they contain no new guarded-cut proof. Freshly reexecuted future fixtures must record their own actual capture, not retroactively stamp A on old evidence.

Planned C catalogue:32 vectors (each16 with proven cut and no-cut I),14 claim-family positive/negative vectors,2 empty/zero controls and2 unknown-cost controls =50 planned observation vectors. They are not executed or installed in this task. The fifteen approved downgrade rows and twenty scenario decisions are carried into B as exact expected limits, including stable fault versus in-cut violation, timeout, alias/hard-link/case collision, nested/temp record, exclusion failure and process death. Test every supported narrow fact survives when the strong predicate fails.

## Candidate and handle observations

Use only original captured candidate IDs/attempts/source content. PRESENT content digest must match original source bytes, not a self-rehashed replacement. Missing bytes stay MISSING with null content/hash and reason; do not infer original C0 from the first remaining array entry. Parent IDs must refer to earlier verified candidates and bound ancestry. Handle proof binds original run/task/call/attempt/wire/provenance/settlement and settled-before-reference order. Distinguish OBSERVED/CORROBORATED_NOT_CERTIFIED from SOURCE_VERIFIED_BINDING.

Observed candidates may survive BLOCKED evidence with no selection. A restricted valid source may retain an independently supported valid C0 while later cost is unknown. Diagnostics never select; X cannot simultaneously assert a typed grounded candidate/attempt association. Selection, source provenance, accounting completeness, artifact persistence, answer correctness and score availability remain separate axes. No extractor computes a scientific score.
