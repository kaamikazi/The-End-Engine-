# Lock order and deadlock analysis

This is static planning against exact source symbols, not a runtime feasibility proof. WRITER_DOMAIN_INVENTORY.csv gives all forty observed entry classes and the explicit unknown administrative/dynamic actor. _evidence/STATIC_CALL_SITES.csv and ORIGINAL_WORKTREE_CALL_SITES.csv preserve the search evidence. Source at 783aa1d remains unchanged.

## Actual locks and gaps

| Identity | Current implementation | Important constraint |
|---|---|---|
| L1 | Publication.lock: per-path threading.RLock then dispatch_lock(.publication.lock) | Native byte lock is not assumed recursively reentrant; an RLock around it does not prove native recursion safe |
| D | Gateway.guard / NativeGateway.guard: ledger.path.with_suffix('.boundary.lock') | Covers ordinary reserve/dispatch/closure, not register, all direct Ledger users or later reservation/settlement hooks |
| L3 | Ledger.lock: ledger suffix+.lock, native blocking byte lock | state/summary and verifier reacquire it repeatedly; observer cannot hold it across source core |
| Binding lock | Publication.__init__: ledger filename+.r2_bindings/bindings.lock under internal L1 | Separate resource; constructor also creates identity/directories and cannot be an observation factory |
| Owner lease | Publication._take_lease, claim, release | Held across operations, protects fence/token; never acquired/transferred/released by observer |
| Read pins | EvidencePin.pin via CreateFileW, GENERIC_READ/FILE_SHARE_READ | Protect already opened files only; no directory-entry freeze; its publication context requires pending/prepared/owner and is not reusable wholesale |

Ledger constructors/register/reserve/finish use only L3. Session.call has L1 around Gateway D/L3 but reservation and settlement witnesses are outside D. Publication.event and detach/error finally paths can write after a nominal operation. NativeGateway.register bypasses D; MockSession can use the same Ledger directly. Exact type checks in Gateway/ArchitectureGateway/NativeGateway reject a naive Ledger proxy/subclass; globally monkey-patching methods is not a safe enrollment strategy. StageTransport/journal hooks are publicly callable helpers with caller-dependent locks.

## Selected planned capture order

The proposed observation L2 is a distinct **outer domain**, not L3 and not automatically existing D. Use one canonical actual-ledger resource identity, binding path, file IDs and participant code hashes. Do not choose a new lock pathname per caller. A0 must test the native identity/alias rules and shared-resource mapping; A1 owns its final reviewed profile.

For the initial strong profile, the controller blocks all new cooperative admission and drains already admitted mutators before taking any L1/L2 capture guard. Waiting for a child that might still need L1 while holding L1 is forbidden. The controller must account for constructors, library users, background finally/logging, baseline trajectory writes and every L3 user. Only a controller with actual exhaustive enrolled/deployment coverage may establish an epoch; ordinary direct callers are not magically enrolled. Domain control files, process admission tokens and the operational proof are new infrastructure, not unauthenticated caller flags. Their schema/state machine and producer provenance require A0/A1 review. No durable active-count repair is inferred from PID reuse or a missing file.

After drain/admission exclusion is proven: acquire the same existing L1 with its in-process local-lock discipline, then new L2; verify the epoch/admission exclusion and no bypassing inner-lock users; enter B. Do not hold L3. The unchanged completed core may acquire/release ordinary L3. Existing D and binding locks must have no active holders or future writers in this epoch. Seal before E; release pins, L2, L1, then release admission exclusion. No two runs' L1 locks are acquired together. Shared-ledger observation uses one L2 and validates global rows/closure before own projection.

This is a planned implementation of accepted enrollment/draining, not an exemption from it. A0/A1 independent reviewers must accept that the actual controller exclusion proves the same cooperating membership/content domain required by R1. If it does not, **A/S stays disabled**; use I/X and request any needed separate scope. The plan does not claim current infrastructure proves this domain or that live callers already follow its order.

## Concrete cycles and prohibitions

| Bad operation | Cycle/failure | Planned prohibition and evidence |
|---|---|---|
| Hold L3, call _verify_completed | Core summary/state waits on same nonreentrant L3 | Observer never holds L3; real child timeout sentinel plus positive core return |
| Wrap Session.call in existing D | Inherited Gateway.reserve_request/dispatch reacquire D | No blanket wrapper; D remains unchanged, initial domain drains the whole caller |
| Hold native L1, construct Session/Publication | Constructor Publication.lock reacquires L1 and creates inputs | Ground via existing records and nonowning context, no constructor |
| Hold L2 while waiting for a writer that still needs L1 | Observer or another caller can hold L1 waiting for L2 | Drain before L1/L2; no control-plane wait for mutating child under capture guards |
| Holder of L2 takes another run's L1 | Cross-run L1→L2 inversion | Never acquire a second L1 or run callbacks while L2 held |
| Pin .lock control files denying write share, then call old Ledger.state | Ledger opens .lock a+b, potentially incompatible with read-only pin | Classify operational lock handles separately from historical data; do not write-deny-pin L3 lockfile; require preexisting nonempty control file and audited no deletion/replacement. Test separately |
| Use public verify_completed wrapper on rejection | Writes a new input event during cut | Call unchanged _verify_completed core only; logging for the new API deferred until after E |
| Reuse EvidencePin.__enter__ for an observer | Requires a publisher's pending/prepared, owner fd/token and installs _CURRENT | New PinSet implements only reviewed native read-handle technique; F01 code/_CURRENT untouched |
| Import Publication as both src.shared and a second package identity | Separate in-process lock/owner maps with same native resources | One reviewed canonical module origin; duplicate loaded origins fail preflight; no import alias tricks |

The existing L1/D/L3 helpers open a+b and may initialize a byte. A read-only observer must use existing-file-only bounded acquisition for L1/L2, must never create their paths, and must preflight the old L3 lock required by the core. Missing or empty control file is unavailable/operational failure, not permission to initialize. Data pins cannot be used to defeat the existing core's legitimate lock access. Identity checks and failure cleanup are A0 acceptance questions, not assumed implementations.

## Bounds and failure behavior

At most two guard/pin acquisition attempts; every guard wait <=5 seconds. Use a monotonic clock and pass the remaining <=5s budget through the in-process and native portions of that guard acquisition. Finite polling may wait for a lock, never poll evidence until an integrity fault disappears. Total wall time also includes two guards per acquisition, preflight, capture, source verification and cleanup; do not misreport the rule as a universal five- or ten-second operation limit. Pre-B inability may retry once after releasing resources. Stable missing/conflicting evidence returns S/lower facts without retry. Any known B..E domain/membership/content violation returns U and invalidates the epoch; no automatic new epoch. Unrelated I/O/programming errors propagate.

Process termination cannot return an unsealed view or preserve lost RAM. OS handles must release; a later invocation must prove a new epoch, preserve existing files and perform no provider replay. A0 tests live-owner exclusion, kill/reacquire and stale-controller/participant evidence explicitly. Native NTFS tests require genuine process handles/file identities and no sequential mock of byte-lock behavior.

## Scope consequences

No Engine/Harness change is necessary for the selected initial observation-only profile. Native baseline and shared-library code remain unchanged; supported legacy participants must instead be proven drained. Online interception of Ledger initialization/register/state, inherited Gateway internals, baseline admission or Publication constructor/event/claim behavior is **not** included automatically. If feasibility requires those edits, produce an exact separate source-scope request before implementation; never alter F01 ownership/fences/pins/exclusive publication or F02/F03/F04 to make enrollment easier.
