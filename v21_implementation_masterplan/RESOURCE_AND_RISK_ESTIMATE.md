# Resource and risk estimates

All future effort/runtime ranges below are **planning assumptions**, not measured v2.1 implementation performance. Assumptions: one experienced Python/Windows engineer, one independent reviewer available at gates, local Windows/NTFS scratch, existing public/synthetic inputs and no model runtime. An engineering day means roughly6 focused engineering hours. No schedule or hardware performance guarantee is made.

## Evidence available for calibration

_evidence/DEPENDENCY_AND_TIMING_INSPECTION.json preserves58 elapsed_seconds fields from the previous V2_ADVERSARIAL_RESULTS.json. Observed range0–5.234000000000378 seconds; median0.2180000000007567 seconds. Their sum57.2649999999976 seconds is the sum of recorded heterogeneous probe fields, **not** full-suite wall time. Some entries are document/model checks, others bounded current-runtime/process controls. They measure neither future capture nor the whole244/154/49 or CR2 suite. No new timing experiment was run. Protected-file hashing in this task is maintenance, not an Engine performance measurement.

## Per-slice budget

| Slice | Engineer days | Reviewer days | Complexity / main concurrency or compatibility risk | Planned test vectors / type | Assumed offline validation time |
|---|---|---|---|---|---|
| A0 |2–3|1|Critical: native recursion, existing-file control locks, nonowning core and drain proof |20 named feasibility vectors, real children, timed negative sentinels, kill/cleanup and valid publication |5–15min ordinary run;45–120min repeated diagnostic batch including bounded timeout cases/setup |
| A1 |3–5|1–2|Critical: complete actual-ledger participant coverage and admission exclusion; no default source interface changes |90 planned vectors: two coverage controls per41 writer/actor rows +8 lifecycle/epoch controls |15–45min with native/process coverage; no measured result |
| B |5–8|2–3|Critical: recursive inventory/pins/absence/ABA, source-core L3 and cleanup |45 vectors:20 primary scenarios (17 fault and3 positive) +17 distinct positive counterparts +8 cleanup boundaries; fifteen downgrade rows traced, not extra counted |15–45min ordinary native batch; longer on repeated contention |
| C |3–5|1–2|High: origin and count/cost authority; missing candidate/handle facts |50 vectors:16×2 conditional authorities,14 claim controls,2 zero,2 unknown usage |1–5min, predominantly immutable-buffer fixtures plus B-produced evidence |
| D |4–6|1–2|High: real semantic predicates versus shape, strict numeric parsing, isolated3.12 dependency compatibility |1240 vectors:1161 standard seed +35 synthetic semantic seed +8 parser seed +28 real-evidence rule pairs +8 bounds |1–5min assuming local installed compatible validator; environment preparation is separate effort |
| E |3–5|1–2|High: reader versions, source-mode handling, exception and diagnostic persistence boundaries |52 budget groups:30 current API cells +14 reader/error +8 mode/candidate boundaries; actual parameterized subcases recorded later |2–10min plus captured source preparation |
| F |4–7|2–3|Critical: real schedules, valid liveness, missing workers, crash/fences and last native seam |53 primary vectors:20 races +13 seams +8 crash +4 owner +4 stale/existing +4 interruption;31 historic property mappings overlap these/C/E |20–60min;2–4h adversarial repeat batch including retained failures and native setup |
| G |1–2|2–3|High: impartial review, source/evidence identity, complete old/new regression accounting |All mandatory new rosters plus original current/reviewer/prior and unaffected source suites in separate outputs; no assumed final count |60–180min broad offline acceptance batch and hashes; human/AI report review time is separate |

Total allocation:25–41 engineering days and11–18 reviewer days, before rework or unavailable dependency/platform delays. IP traceability rows share these slice budgets; do not sum IP effort independently. D pure-structure preparation can overlap C, but real source semantics cannot precede B/IP06. Independent G review must have no implementation authorship conflict. AI review remains distinct from authenticated human scientific adjudication.

Counts are planned **vectors/budget groups**, not measured unittest methods, exhaustive schedules or invented passes. Thirty-one mapped historical properties are not an extra31 races; four vector/cardinality dimensions and thirteen seams remain explicit. Before implementation acceptance, publish an exact case/parameter/worker manifest and actual PASS/FAIL/ERROR/BLOCKED/SKIP totals. Existing historical totals stay attributed to their old rosters.

## Windows/NTFS and environment requirements

Use genuine local Windows handles, stable canonical volume/file identities, byte-range locking, real hard links and separate OS workers. Validate case-fold/reparse/hard-link/alias behavior, write/delete share denial, file replacement, process death, lock release and cleanup under the actual supported filesystem. Do not generalize to network filesystems or hardware power-loss. A sandbox lacking native os.link/share operations yields an unmet native gate, not evidence that the property passed.

Working source runtime is Python3.12 with Engine>=3.11; optimized -O is rejected by existing r3 publication source. Future established-validator setup must be isolated and compatible with3.12. Review used jsonschema4.26.0 already installed under3.10; its compiled rpds cannot be reused under3.12. Package installation/wheel acquisition, transitive hash/license checks and a new environment require separate authorization; no package or model is downloaded here. Root Engine dependencies/packaging remain unchanged.

Planning storage allowance: source copies, raw fixture/capture buffers, subprocess logs and append-only checkpoints can exceed the small report size. Assume1–3GB free scratch and2–4 simultaneously running workers per race, with deterministic output caps and no model memory. These are conservative capacity allowances, not measured dataset requirements. If evidence exceeds a cap, record an actual bounded failure; never truncate an inventory while retaining A authority. Archive/export policy is a later local evidence decision, not permission to delete research or use Git LFS.

## Critical path and potential strategy invalidators

A0 native/nonowning/core/control-file tests → A1 actual writer coverage → B common cut/source binding → C/D trusted claims and semantic rules → E opt-in integration → F full native acceptance → G fresh review. A0/A1 may invalidate the **quiescence-first implementation strategy** if no supported controller can prove complete drain/exclusion without forbidden source changes. That would not retroactively invalidate the approved contract: strong capability remains disabled, I/X remains safe, and any online enrollment/source expansion needs a new scoped engineering decision. Other high-impact delays are incompatible native pin/control semantics, inability to invoke unchanged core without mutation, and unavailable matching validator dependency. These are explicit stop gates, not hidden schedule padding or authority to change scientific contracts.
