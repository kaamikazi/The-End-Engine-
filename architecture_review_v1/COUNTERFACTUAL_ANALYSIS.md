# Recorded-state counterfactuals

No alternative policy was executed or replayed as new inference. A changed adoption/stop decision changes later candidate context, prompts, seeds/state and potentially outputs; continuing along the original recorded future path is generally invalid. Saved score comparisons are observations of recorded artifacts, not guaranteed prospective effects. Actual safety withholding/final reconciliation may differ on early stops.

| Policy | Status | What is known | What is not known |
| --- | --- | --- | --- |
| A preserve C0, no revision | OBSERVABLE FROM RECORDED ARTIFACTS for C0 text/score; full safe return PARTIALLY RECONSTRUCTABLE | All16 C0 scores and texts; mean .71875, versus actual .6875; protects newer BA-008 explanation | Changed policy safety guard/output/termination; actual inference savings and future behavior |
| B best external-scored recorded candidate | OBSERVABLE FROM RECORDED ARTIFACTS; RETROSPECTIVE ORACLE UPPER BOUND | Every run's max score equals C0 (tie preference), mean .71875 | Runtime cannot see these external scores; equal-score candidates may differ in safety; no admissible oracle runtime policy |
| C stop after first cycle | OBSERVABLE FROM RECORDED ARTIFACTS for effective post-rollback state; full policy PARTIALLY RECONSTRUCTABLE | First effective candidate score mean .6875, same aggregate as actual final; newer BA-008 already loses explanation | Early final best selection/reconciliation/guard and missing future evidence; misses native BA-009 second-cycle status qualification |
| D revise only actionable grounded issues | PARTIALLY RECONSTRUCTABLE eligibility; SPECULATIVE / REQUIRES NEW INFERENCE after divergence | Two selected topics deterministically grounded, other34 plausible/unknown and8 unsupported/contradicted; useful downstream gaps can differ from selected topic | Scores/future outputs/cost under filtered discovery, corrected plans or alternative state; no invented zero-regression/gain estimate |
| E reject unsupported authority additions | PARTIALLY RECONSTRUCTABLE for local saved deltas; SPECULATIVE / REQUIRES NEW INFERENCE after divergence | New native BA-009 C2 invents ID; new structured BA-009 C1 adds confirmation; can flag these deltas | Whether retaining earlier unsafe/malformed parent is admissible or yields better final response; later recovery and total cost |

D cannot simply select the two grounded-target rows: a generic evidence topic can produce a real downstream format/status issue, while a plausible topic can produce a false critique. Eligibility needs an issue-target/constraint/evidence link, not arbitrary task-specific retrospective filtering. E must not preserve established C0 just because the proposed child adds a citation; bounded safety correction or withholding may still be required. Lowering status and inventing an ID can overlap as safety improvement and regression.

## Every run: observed score comparisons

| Version / run | Actual final | A C0 | B oracle / candidate | C first effective / score | D/E future |
| --- | --- | --- | --- | --- | --- |
| 0.3.5 BA-001.T1.FULL_END_NATIVE | 1.0 | 1.0 | 1.0 / C0 | C0 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5 BA-001.T1.FULL_END_STRUCTURED | 0.0 | 0.0 | 0.0 / C0 | C0 / 0.0 | UNKNOWN after policy divergence |
| 0.3.5 BA-002.T1.FULL_END_NATIVE | 1.0 | 1.0 | 1.0 / C0 | C0 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5 BA-002.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 1.0 / C0 | C0 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5 BA-008.T1.FULL_END_NATIVE | 0.5 | 0.5 | 0.5 / C0 | C1 / 0.5 | UNKNOWN after policy divergence |
| 0.3.5 BA-008.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 1.0 / C0 | C0 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5 BA-009.T1.FULL_END_NATIVE | 0.5 | 0.5 | 0.5 / C0 | C0 / 0.5 | UNKNOWN after policy divergence |
| 0.3.5 BA-009.T1.FULL_END_STRUCTURED | 0.0 | 0.0 | 0.0 / C0 | C0 / 0.0 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-001.T1.FULL_END_NATIVE | 1.0 | 1.0 | 1.0 / C0 | C1 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-001.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 1.0 / C0 | C1 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-002.T1.FULL_END_NATIVE | 1.0 | 1.0 | 1.0 / C0 | C1 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-002.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 1.0 / C0 | C1 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-008.T1.FULL_END_NATIVE | 0.5 | 1.0 | 1.0 / C0 | C1 / 0.5 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-008.T1.FULL_END_STRUCTURED | 1.0 | 1.0 | 1.0 / C0 | C1 / 1.0 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-009.T1.FULL_END_NATIVE | 0.5 | 0.5 | 0.5 / C0 | C1 / 0.5 | UNKNOWN after policy divergence |
| 0.3.5.1 BA-009.T1.FULL_END_STRUCTURED | 0.0 | 0.0 | 0.0 / C0 | C1 / 0.0 | UNKNOWN after policy divergence |

Source references: REPORT trace index, RUNS.json and each CYCLE_AUDIT first-cycle row; candidate scores remain their original evaluation files. B's tie preference is an analysis convention, not evidence that C0 is safest. Historical old native BA-008 regex limitation biases score comparisons and hides explanation preservation value. There are0 higher-scoring recorded children to reveal a strong missed-improvement selection bottleneck. Savings based on omitting recorded calls can be an arithmetic ceiling for a literal replay only; no exact actual savings are claimed for new inference.
