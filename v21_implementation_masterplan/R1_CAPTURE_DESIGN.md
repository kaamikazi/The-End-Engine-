# Proposed R1 read-only capture design

All names under src/observation_v21/ are NEW proposed APIs. This document implements no source. It retains R1-GUARDED-CUT-2.1 exactly: common membership/content cut or downgrade; <=2 acquisition attempts, <=5s per guard wait; no in-epoch retry after known violation.

## Proposed API and state boundaries

| Proposed API/type | Input → output | Side-effect boundary |
|---|---|---|
| grounding.ground_existing_run | Declared root/request/resource profile → GroundedRun | Read only; validate request/effective identity digests, actual canonical paths and existing control/data files; no Session/Publication/Ledger constructors |
| domain.acquire_capture_epoch | Audited participant/resource/code profile → qualified epoch capability or Unavailable | Initial strong mode drains all supported callers before capture; no capability from boolean/hash alone |
| guards.acquire_existing_guard | Existing canonical resource, deadline → owned guard handle | Existing files only, reviewed local/native identity; no owner lease/fence |
| namespace.enumerate_complete | Grounded roots/registered paths → immutable entry descriptors | Recursive names/types/IDs/links, expected absences, known metadata and unexpected members; no glob-only coverage |
| native_pins.PinSet | Actual existing data descriptors → owned read handles | GENERIC_READ, deny write/delete; operational lock files separately classified; finally closes only owned handles |
| capture.read_buffers | Pinned handles → immutable raw-byte map | Read through the acquired handles; verify file IDs/length/digests; never reopen for new authority after E |
| parse_sources.parse_captured_sources | Immutable bytes + reviewed source-format version → typed parsed facts/failures | Strict duplicate-key/finite parsing; exact baseline canonical hash domains; no repair |
| predicates.classify_graph | Captured facts + domain/absence/origin evidence → A/S or lower facts | Global ledger integrity before own rows; mandatory reservation, no current graph-overall shortcut |
| source_context.verify_existing_source | Grounded nonowning context + held A/S capture → SourceProof or typed failure | Invoke unchanged Publication._verify_completed including independent F02 eligibility, no public logging wrapper |
| capture.seal_capture | Buffers, entry IDs, absences, facts, failures and source proof → SealedCapture | Canonical immutable manifest/digest; trusted local producer provenance is separate from digest |
| capture.capture_observations_v21 | GroundedRun + policy → SealedCapture or typed operational error | Release pins/L2/L1 on every path before return; capture itself never persists a normal result |

The standalone capture returns a separately versioned evidence manifest, not a RunOutcome or certificate. An eligible outcome additionally needs the unchanged source check; missing RESULT does not automatically become a generic diagnostic. Lower facts can accompany a typed error without forcing an unsupported serialized member.

## Exact step plan

1. Resolve preexisting run root and identity/request/effective/ledger bindings; reject aliases/path escapes and unsupported source mode. Bind to current code/format digests. Validate configured ledger limits from an admitted resource profile, not an arbitrary rehashed envelope. A grounded caller request must match the original canonical identity; no guessed run ID.
2. Establish audited domain coverage. Initial strong profile is post-drain only. If coverage is missing, independently acquire/read safe single-source groups and produce I, or X if no supportable attempt fact. Unknown run grounding raises a typed error. These are not fabricated corruption.
3. Under proven admission exclusion, acquire existing L1 then distinct L2, both bounded. B begins only after the epoch and guards are validated. The observer holds no L3, lease or fence.
4. Inventory the entire relevant run namespace, actual shared ledger/closure/bindings and all registered witness/raw paths. Include directories, moved/temporary/unknown files, prepared/source/owner references, explicit expected absences and global rows. Resolve file identities, volume identity, hard-link aliases, reparse points and case-fold collisions without following unsafe links. Unknown entries never vanish from the manifest.
5. Pin all existing historical data files before reading. Native operational guard/lease files are descriptors/control resources, not data pins that block the unchanged lock helpers. Validate preexisting L3 control-file presence/nonempty identity without initializing it. Native file replacement/sharing behavior must pass A0; unsupported platform or resource conditions do not get a strong claim.
6. Read immutable handle-owned buffers; parse exact versioned formats. Check reservation order/types globally, ledger checksum/limits/runs, own IDs, original source channels, dispatch intent/reference/settings, response commitment, settlement row equality, closure/owner/prepared/source identity. Record all failed dimensions and raw validity separately.
7. Re-enumerate complete membership/types/IDs/registered absences and verify pinned buffers/content and context bindings while guards remain held. Equality is only an assertion under independently proven exclusion; known ABA/domain violation invalidates the epoch even if final bytes match.
8. Independently classify A versus S based on mandatory accounting graph closure, or U on observed violation. A corrupt/missing known raw journal can leave A recorded cardinality while raw provenance BLOCKED prohibits eligible outcome/complete totals. Unknown possible attempts prevent A. Preserve every supported narrower fact.
9. If the caller requests an eligible view, invoke the existing completed-source core in the same held A/S cut. Bind SourceProof to exact source raw bytes/path/run/task/condition/request/closure/provenance/candidates/capture ID. A failed F02 check can ground an integrity diagnostic; unrelated integrity/storage/programming errors remain errors, with retained observations. No source check at I/U/X.
10. Seal before E. Manifest includes protocol/capture/resource/domain/code identities, ordered B/seal/E events, complete inventory/absence/file-ID/raw hashes, original-origin references, witness crosslinks, failures, per-claim authority and source proof. E is release after seal. Return only immutable buffers/values, not live handles claimed as future proof.

## Reuse proof obligations

Existing strict_json.loads, canonical and sha are pure bounded parsing/hash helpers and can be called on captured bytes without file mutation. Their numeric/source semantics remain exact; F04 is not edited. StageCompiler._compile/catalog perform local source verification and in-memory compilation; admit only the exact public registry/settings and source origins. This does not authorize a model call. Review any imported dependency for top-level effects before using it in the new runtime.

Current reconcile and verify_journals reopen mutable paths and shallow-glob directories; they are not the new capture parser or five-tier extractor. Reuse them only as unchanged source-core checks under an independently established pinned cut and as differential references. New pinned-buffer parsing is necessary for lower observations and exhaustive membership. Do not weaken their source gate or retrofit historical witnesses.

Publication._verify_completed and verify_semantics are reused unchanged, not reimplemented. The proposed source context is a constructor-free grounded Publication-compatible instance with all original read methods, exact request/effective/mode/identity/paths and a verified existing Ledger-compatible read context. fd=None, no lease/token ownership and no _ACTIVE registration; Publication.release therefore has no owner descriptor to release. No monkey-patching verification, replacing F02 methods or invoking __init__ is permitted. A0/B must prove this exact method closure causes no filesystem mutation or ownership effects. If it cannot, source eligibility remains unavailable and requires separate scope rather than a substituted verifier.

The old ledger constructor is mutating; the proposed read context must expose the unchanged state/summary semantics with a preexisting actual path/limits/L3 identity. A0 must demonstrate ordinary L3 acquisition does not initialize or mutate a missing/empty control file and does not conflict with data pins. Merely object-allocating a facade is not validation of its grounding or safety.

## Failure and cleanup matrix

| Boundary | Outcome | Cleanup / retry |
|---|---|---|
| Ungrounded identity/request/resource | Typed operational/integrity rejection, no fabricated envelope | Close any read handles; no retry to invent context |
| Domain unproved | I supported groups or X; possible grounded UNKNOWN diagnostic only at adapter | No A/S/source eligibility; no fabricated zero |
| Guard/pin acquisition before B unavailable | Release acquired resources; one optional retry | <=2 attempts total; each guard <=5s; final I/X or actual error |
| Stable absent/conflicting witness | S if stable cut and facts; retain failed dimension | No semantic retry, repair, refund or replay |
| Any B..E mutation/assurance violation | U and invalidated epoch | Preserve safe lower facts, no strong retry in epoch |
| Parsing/source verification failure | Grounded BLOCKED only if actual F02 rejection; otherwise typed error | Always release own pins/L2/L1; no public-wrapper event inside cut |
| Process termination/unsealed RAM lost | No successful capture/view | OS releases handles; retain existing evidence, start a separately proved epoch later |
| Persisted capture/diagnostic output fails after E | Actual storage error | Never set artifact_persisted true or overwrite original source |

ExitStack-style ownership bookkeeping is proposed for new resources; reverse cleanup must not call Publication.detach/release on an existing owner. Planned capture failure at every acquired-handle count, both guard boundaries, after parsing, before/after seal and core rejection must prove no leaks or input mutations. Resource limits on capture size/names are operational bounded failures, never a reason to silently truncate inventory and keep A.
