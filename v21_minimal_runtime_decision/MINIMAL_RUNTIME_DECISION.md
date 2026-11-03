# Minimal runtime remediation decision

**HYBRID_BOUNDARY_RECOMMENDED**

Design analysis only. No proposed runtime mechanism is implemented or authorized. The exact first separately authorizable production slice is an opt-in outer shared-ledger guard at `cognitive_architecture_lab_v1/src/accounting/ledger.py` (Ledger.__init__, lock, _write) plus a new stdlib-only coordination module and new isolated tests. It is a small patch for the demonstrated register/pending edge, **not** full writer enrollment or complete accounting. See FIRST_PRODUCTION_CHANGE_PROPOSAL.md.

## Evidence and source result

Approved contract commit: `783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e`. The previous study remains WRITER_EXCLUSION_BLOCKER:17 PASS/1 FAIL across18 distinct controls; twelve fault categories, N01/N02 sharing one actual register event; six derived mock legacy core positives. N12 remains FAIL. The six EXP-001 sources contain41 mock rows/615 synthetic tokens, no new model call or measured provider usage. No tests or probes were rerun here.

Static source analysis read **419 Python files**, parsed them without runtime imports and retained **1404 candidate call edges**. Four production Ledger._write calls (constructor/register/reserve/finish) all sit under self.lock; the fifth direct candidate is the existing canary test under ledger.lock. This proves a narrow auditable source choke point, not a universal call graph or host actor exclusion. COMPLETE_WRITER_CALL_GRAPH.csv explicitly retains unresolved receivers and test/history paths instead of misattributing every register/finish to this Ledger. Its completeness is bounded to the enumerated source set, not reflection/foreign code.

Ledger-only coordination cannot freeze closure, journals, durable events/bindings or constructor/recovery directories. The source trace identifies those additional shared sinks and the current L1-protected routes. Existing D precedes Ledger calls; blindly wrapping an operation in L2 before D or making L3 recursively reentrant is unsafe. New source guard order must keep D→L2→L3 when D is present, existing L1→L2 capture with no D/B calls inside, and G creation/drain before L1. Ordinary source helpers under owned L2 need checked logical outer reentry only.

## Why this recommendation

The intended complete-cost claim requires authoritative membership/content and original complete usage evidence at its certification boundary. It does not require strong authority for every exploratory field. The hybrid policy reuses existing lower diagnostics and existing L1, while every relevant mutable input to a requested authoritative cut still joins the minimal storage/creation domain. It adds no separate general I/X observer project. A and C share the same minimum relevant-writer safety obligations; no artificial source-line or effort saving is claimed over Option A. I/X-only cannot support complete cost, but can accompany a separately approved narrower quality-only protocol.

Complete scoped enrollment is **not one tiny implementation slice**: independent closure write, pending/append/event sinks, pre-lock directory creation and error/finally routes remain outside Ledger. Native physical witnesses are a distinct missing mechanism, not fixed by any lock. Native1/3/29 fixture rows have zero independent native reservation/dispatch/settlement files, while architecture2/2/4 rows retain them. NativeCompiler differs from StageCompiler; the proposed exact-field native witness profile must be independently admitted without changing the accepted contract or old F02 checker. Missing original evidence is never recreated.

The full bounded route is: first ledger guard slice → remaining relevant namespace/creation storage boundaries → native execution witnesses and admitted native parser → accepted recursive same-cut source/cost validation. Each is separately scoped and independently accepted; no first patch emits A/S or COMPLETE. Existing IP01–IP09 remain unfulfilled where not implemented. These are precise source/acceptance boundaries, not another request for broad feasibility exercises.

## Study readiness and limitations

Study A answer-quality is conditionally possible without complete costs if original outputs, tasks/settings/condition identities, independent source eligibility, frozen external evaluation, exclusions and failure handling are preregistered and accepted. It is **not live-ready**: existing native F03 admission and both transports are explicitly offline/canned; later versioned live admission/transport/provider validation needs separate approval while preserving the existing gates. Quality-only cannot claim equal measured compute, efficiency, or a new v2.1 eligible view from I/X.

Study B quality per computational cost remains blocked until every included run has complete same-cut original physical/usage evidence and comparable metric semantics. Fixture sums, reservation ceilings and known subsets do not supply complete totals. Missing/contradictory usage stays null and blocks the affected comparison. There is no inferred billing, authenticated inference, reasoning-improvement or semantic correctness result.

N12's errno13 is compatible with documented CRT sharing denial but does not establish historical WinError5. A versioned meaningful-operation test is specified separately; the original failure is never rescaled/rescored. Published API documentation is used for that design explanation; no new native operation was executed.

## Deliverables and next review

WRITER_ENROLLMENT_DELTA.md enumerates each exact boundary, lock/crash/compatibility obligations and why forty separate edits are unnecessary. NATIVE_WITNESS_DESIGN.md specifies execution-only hooks, phases, failure policy and fixed-schema native mapping. SIX_CONDITION_DURABILITY_GAPS.csv has60 condition/category rows. OPTION_A_B_C_COMPARISON.md gives explicit estimates (A/C20–35 engineer-days+8–12 review-days; first slice3–5+2–3, all estimates). QUALITY_ONLY_VS_COST_STUDY.md separates scientific endpoints. N12_TEST_CONTRACT_ANALYSIS.md and INDEPENDENT_ACCEPTANCE_GATES.md preserve exact failures and prerequisites. SOURCE_PRESERVATION.json and the final local integrity receipt cover unchanged original sources/evidence/Git state.

No Engine0.3.5.2, Harness, frozen evaluator, task/prompt/settings/ceiling, A/B/C algorithm, F01/F02/F03/F04 behavior or historical evidence change. No production implementation, test execution, inference, benchmark, provider request, commit, push, merge or release. Fresh implementation acceptance and human scientific adjudication are pending; this report does not fabricate either.

The completed before/after read-only inventory verified 52890 protected files with no byte/member or Git state changes. This is preservation evidence, not runtime acceptance or a writer-exclusion proof.
