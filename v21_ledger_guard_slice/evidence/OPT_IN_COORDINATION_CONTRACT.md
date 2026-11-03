# Opt-in Ledger coordination contract

Implemented only in the approved isolated worktree. Python3.12.14/Windows11/NTFS were tested. No new dependency or environment/global activation switch. No snapshot/cost/source-certificate mechanism is implemented.

```python
from pathlib import Path
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from cognitive_architecture_lab_v1.src.accounting.coordination import Coordinator

path = Path(existing_synthetic_directory) / "budget.json"
coordinator = Coordinator.create(path)  # one-time explicit control bootstrap
ledger = Ledger(path, coordination=coordinator)
peer = Ledger(path, coordination=Coordinator.attach(path))
with coordinator.acquire():
    state = ledger.state()  # checked logical L2 reentry, ordinary L3
```

The parent must already exist. Neither opt-in Ledger.__init__ nor Coordinator.create creates parent directories. Bootstrap exclusively creates only `<ledger>.coordination-v1.lock`, writes byte0 plus bounded canonical metadata, flushes/fsyncs and closes. Attach opens existing control without creation, repair or replacement. A bootstrap crash can leave an invalid control; it stays evidence and fails closed, not automatically fixed. Control bootstrap precedes participating ledger transactions and is not a claim that all parent membership is frozen.

Constructor opts in only through the explicit `coordination` argument. `Ledger(path)` remains legacy even if a coordinator file exists or an environment variable is set; that writer/reader is unenrolled. A nonowning context must explicitly carry `_coordination`; there is no discovery from path alone. This follows the current approval's explicit opt-in/default-compatibility rule, and is narrower than earlier proposals that contemplated automatic same-path discovery. Every admitted participating Ledger object must be configured by its caller. Bare old/default clients are an acknowledged coverage limitation, not silently included.

Resource identity is the canonical ledger namespace, actual parent device/inode and immutable preexisting guard device/inode/domain metadata. It is not the replaceable ledger inode: successful atomic replacement changes that inode. Windows existing8.3 names use realpath canonicalization; raw stream/trailing/device names are refused, reparse components are rejected before realpath, hard-linked ledger/control files are refused, and case aliases use one domain. Guard metadata is canonical/bounded and self-binds its file identity. This is local consistency/coordination, not authentication against a malicious host.

Acquire L2 before L3, including before opening/initializing its one-byte control. Registration, reservation and settlement enter through the unchanged Ledger methods' common lock. `_write` checks **already held** L2 and tracked L3 ownership; it never acquires L2. Guard scope includes pending creation, write, flush/fsync, replacement attempt and exception unwinding. Opt-in uses exclusive `xb` for pending: stale pending causes FileExistsError and remains intact. Default `wb`/replace behavior remains unchanged. No old pending file is deleted, repaired or converted into a witness by this patch.

An internal process/kernel-file identity registry shares an RLock across explicit Coordinator instances. It is ownership bookkeeping, not mutable configuration. Only same-thread checked logical L2 reentry skips a second OS byte lock. Other threads contend under the configured deadline; other processes use the same native byte lock. Recursive L3 or a first L2 request while a tracked current-module L3 is held rejects before locking. This cannot inspect or enroll arbitrary old-code inner-lock holders. Cross-module duplicate loading of the same coordinator file is refused in opt-in mode.

Timeout is a finite non-bool number >0 and <=5 seconds (default0.5). One shared remaining deadline bounds the thread-mutex/native-lock waits; this is not a hard real-time guarantee for arbitrary filesystem I/O. Native contention is conservatively returned as CoordinationBusy/L2_CONTENTION_DEADLINE with the native cause retained. Control/config/ownership mismatches raise deterministic CoordinationError codes; actual OS errors remain precise OS errors rather than assumed WinError5. API catches do not normalize them into successful source certification.

Release drops tracked L3, unlocks/closes original L3, then releases logical/native L2 and the thread mutex on every normal/exception exit. Process death releases kernel handles; actual killed-worker tests verify subsequent use. No abandoned-live-thread takeover or hostile-host guarantee is implemented. Supported/tested profile is one canonical local Windows/NTFS resource and reviewed module origin; remote/mapped volumes, arbitrary copied runtimes and untested reparse/short-alias creation modes have no independent native acceptance here.

D stays unchanged and precedes L2 where present. The future observer order is existing L1→L2→ordinary L3, with no mutating constructor or owner/fence claim; source-core test39 exercised exactly that order on rebased synthetic evidence. Never hold L3 across an unchanged helper, wrap an existing D-taking operation in L2 first, or claim kernel byte-lock recursion.

No changes to budgets, row/summary arithmetic, request construction, dispatch, candidates, old F01/F02/F03/F04 checks or algorithms. Existing trusted source manifests are preserved. Registry/schema/owner/capture proofs needed for full observation authority remain future work.
