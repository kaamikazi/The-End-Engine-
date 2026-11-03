# END v1.0.2 → accepted v2.1 implementation masterplan

**IMPLEMENTATION_PLAN_READY_FOR_REVIEW. Planning only.** The proposed first authorization is A0, an isolated Windows feasibility slice. No production implementation, old-test migration, commit, push, merge, provider request, model download or benchmark is performed or authorized by this plan. Contract acceptance is not runtime acceptance. Human scientific approval remains pending.

## Exact baseline

| State | Identity | Meaning |
|---|---|---|
| Approved contract checkout | E:/END-v102-V21-Contract-Checkpoint; wip/end-v102-contract-v21-review; 783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e | Clean published local commit/tree, inspected offline; no fresh remote query |
| Original correction | E:/END-Cognitive-Architectures-Fix-v102; fix/cognitive-architectures-v102-f02; bc9bcbad8e9cb051d54c3b270e2e03d460858986 | Retained dirty/untracked correction research; not the same Git state |
| Earlier WIP | E:/END-v102-WIP-Checkpoint-20261019; wip/end-v102-contract-review-20261019; eadf1390c0631cfe30985744b38bb4df055acb87 | Separate preserved checkpoint |
| Source dependency closure | 246 manifest entries, identical in approved/correction states; root 1b92bad8dfdc527e367435d72ba0b5e29c87ecaa36e432eadff10f6818efe126 | Equality of source bytes does not merge branches or histories |
| Engine | 0.3.5.2; 29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82 | Fingerprint recomputed over Engine Python sources plus pyproject.toml using existing canonical map convention |
| Frozen evaluator | exp-pack-1.1.1-frozen; 725 files; root 23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09 | Existing read-only checker passes; no evaluator execution or repair |
| Accepted review | E:/The End Engine/v21_contract_acceptance_review/V21_CONTRACT_ACCEPTANCE_REVIEW_BUNDLE.zip; fa988f05f5d8620aeff46878542d2ef083f09e5b255b7bb5581b3c3b55ec6671 | Exact ZIP, CRC and every manifested member verified; FINAL_VERDICT bytes match separate report |

The accepted verdict is APPROVE_V21_CONTRACT_FOR_IMPLEMENTATION_PLANNING. Old author proposal files still say pending review; those historical bytes are preserved and do not supersede the later review. All 17 contract documents plus the validation summary were inspected from this Git tree, including the complete parsed schema, 87 field rows, 16 case rows and 15 downgrade rows. Required review inputs were inspected, including all 12 semantic and 57 structural cross-contract records. No required current input was missing. The previously unavailable original external IR101 bundle is an inherited evidence limitation; no execution of it is claimed.

## Nine gates and current status

IP01–IP09 retain their exact requirement text in IP01_IP09_TRACEABILITY.csv; no gate has been renamed. Each row specifies source symbols, modifications, positive/negative evidence, dependencies, risk, effort, acceptance and independent review. None is certified complete merely because code or a design interface exists.

| Gate | Current status | Planned delivery |
|---|---|---|
| IP01 | PARTIALLY_IMPLEMENTED | Actual all-writer/resource coverage and fail-closed enrollment/drain domain |
| IP02 | PARTIALLY_IMPLEMENTED | Proven lock order, bounded acquisition and nonowning same-cut source context |
| IP03 | NOT_IMPLEMENTED | Recursive pinned membership/content capture, explicit absences and sealed immutable manifest |
| IP04 | PARTIALLY_IMPLEMENTED | Mandatory witness predicates and scoped five-tier observations, all16 cases |
| IP05 | PARTIALLY_IMPLEMENTED | Strict source parsing, accepted structural schema and14 real external-evidence rules |
| IP06 | BLOCKED_BY_DEPENDENCY | Unchanged completed-source verifier bound to the same A/S cut |
| IP07 | PARTIALLY_IMPLEMENTED | Explicit opt-in adapter and bounded current/archived reader compatibility |
| IP08 | PARTIALLY_IMPLEMENTED | Executed CR2 Windows processes, exact faults, valid liveness, crash/fence/pin controls |
| IP09 | PARTIALLY_IMPLEMENTED | Versioned supersession only after separate authorization; all31 old outcomes retained |

## Selected minimal implementation direction

Add a separate observation package under the future path experimental_architectures_v1_r3/src/observation_v21/. This path and every API proposed below are NEW, not existing capabilities. Preserve all existing source entry points. The first release should observe existing runs, not wrap execute() or execute a run itself. Existing F01 publication and F02 eligibility stay authoritative for source artifacts; R1 observation authority never replaces them.

Choose **quiescence-first strong capture**, conditional on an independently accepted operational enrollment proof. A new opt-in domain controller must own admission for the actual shared resource, block new cooperating writers, drain every admitted process/thread through all finally/logging writes, and only then enter the existing L1 → distinct outer L2 → ordinary L3 capture order. No legacy writer is automatically covered because the controller exists. A0 must establish whether this deployment can satisfy the accepted enrollment/draining requirements without F01 edits. A1 cannot enable A/S until that proof is accepted. Active, unknown, unsupported or unenrolled writers leave I/X; observed interference yields U. The plan does not substitute a stopped-looking process, PID check, boolean or hash for coverage proof.

This bounded profile avoids first changing shared Ledger, Gateway, constructors, native baseline or F01 code. Live online enrollment is a separately scoped later capability, not a hidden prerequisite that authorizes edits to those modules. If quiescence cannot be proved under supported operations, the implementation remains lower-authority; it must stop rather than add unsafe lock wrappers or silently change the contract. A0 is a rejection gate for this strategy, not a claim that the strategy is already verified.

## Module boundaries proposed for later approval

| New module | Responsibility | Existing symbols read/reused, not replaced |
|---|---|---|
| domain.py | Resource/code/participant profile; drain/admission epoch proof | Actual Ledger/Gateway/Publication lifecycles in writer inventory |
| guards.py, native_pins.py | Existing-file-only timed L1/L2 and own read handles | Publication._LOCAL_LOCKS discipline; native sharing technique in EvidencePin.pin; never EvidencePin.__enter__ |
| grounding.py, source_context.py | Bind existing request/identity/ledger and nonowning verifier | Publication._verify_completed/verify_semantics/release; Ledger state/summary through existing L3 |
| namespace.py, capture.py, parse_sources.py | Full membership/type/file-ID/bytes/absence cut and immutable seal | strict_json.loads/canonical/sha with exact source formats |
| predicates.py, observations.py | Witness graph and source-group claims | Read and differentially compare reconcile/journals/StageCompiler._compile; do not call current graph VERIFIED a new proof |
| validation.py, semantic_rules.py, versioning.py | Three validation layers and version routing | Accepted schema exact bytes; established Draft-07 validator as an isolated optional dependency |
| adapter.py, diagnostic_store.py | read_outcome_v21 / observe_run_v21 over existing evidence; optional unique diagnostic record | No call to Session/execute/_build/publish/restore/close_generation; no source writes |

Tests belong in a new future cr2_v21_tests/ namespace outside existing tests/ discovery, with A0 feasibility tests outside the implementation package until authorized. Names in this table are design proposals. Real existing references are verified against AST symbols in _evidence/SOURCE_SYMBOLS.json; forty concrete writer entries plus one explicitly UNKNOWN external actor are in WRITER_DOMAIN_INVENTORY.csv.

## Review sequence and source protection

A0 feasibility → A1 audited domain → B read-only capture/source proof → C observation predicates → D real schema/semantic validation → E opt-in projection/readers → F versioned CR2 → G fresh independent implementation acceptance. Pure structural work in D may be prepared alongside C, but no evidence eligibility claim precedes B/IP06. Each slice has an independent stop gate and explicit future authorization. PHASED_IMPLEMENTATION_ROADMAP.md gives exact future files, interfaces, tests and rollback boundaries.

Do not run existing validate.py as a convenient green check: it writes validation outputs, invokes twelve-cell mock wiring and hardcodes older success expectations. Historical244=222PASS/16FAIL/6ERROR;154=146PASS/8FAIL;49=48PASS/1FAIL remain recorded. Later regressions must use an isolated source copy and separate output roots, with every outcome retained. No new old-suite failure is acceptable merely because known failures exist.

SOURCE_PRESERVATION.json and _evidence/IDENTITY.json record this task's actual hashes/Git states. Planning consistency checks do not count as implementation tests. Source-preservation success does not establish model performance, provider transport or human approval.
