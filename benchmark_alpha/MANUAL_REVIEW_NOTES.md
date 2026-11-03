## Hand-selected cases (MANUAL; read in full by the analyst)

| Run | Why it matters | What the records show |
|---|---|---|
| `BA-008.T2.FULL_END` | END amplified a false premise | Every candidate correctly said `sorted()` is stable. Primary and adversarial judges gave REJECT for C0–C3 *because* "the problem statement explicitly states that sorted() is not stable". The final gate was REJECT; the returned C0 is externally correct, so this is a FALSE_REJECT. |
| `BA-002.T2.FULL_END` | Judge hallucination | All four candidates pass every unit test. The judges rejected each one, quoting the task's original buggy `range(0, len(items) - size, size)` as if it were in the candidate. This caused 3 neutral rollbacks (29 calls, 44.7k tokens) and the run was returned with gate REJECT. |
| `BA-001.T2.FULL_END` | Easy task lost to END's first draft | C0 computed 36.6 °C → 67.9 and 21.5 °C → 60.7. Verification then produced a weakness update for a nonexistent ID, giving EXTERNAL_BLOCKER, and this C0 was returned. DIRECT and SELF_REFLECT were correct in both trials. |
| `BA-005.T1.FULL_END` | Hidden assumption not caught | C0 compared local clock times: "first E1 … last E3 … 295 minutes", in prose, with no JSON. The run aborted at verification. DIRECT got E2/E1/30 in both trials. |
| `BA-009.T2.FULL_END` | Model agreement treated as confirmation | "Two on-call engineers independently confirmed the database as the culprit". The answer hedges but anchors on that consensus. The format failed (prose). |
| `BA-010.T1.END_LITE` | Contradiction resolved by fiat | Names both artifacts, then concludes the function "does not correctly handle an empty configuration file, with a high degree of certainty". |
| `BA-011.T2.END_LITE` | END internals leaked into the answer | The answer discusses "the candidate's revision plan" and "W001" instead of answering the user. The substance (no guarantee) is correct; the format is not. |
| `BA-002.T1.SELF_REFLECT` | Self-reflection broke a correct answer | The initial answer passed 7/7 tests; the revised answer fails 5/7. The same happened in T2. |
| `BA-004.T1.SELF_REFLECT` | Self-reflection fixed an answer | The initial schedule was truncated or invalid; the revision satisfies all six constraints. Every other condition failed BA-004 in both trials. |
| `BA-007.T1.DIRECT` | Baseline failure mode: truncation | The answer was cut off at 4096 tokens inside its reasoning, with no final JSON. All 9 DIRECT failures are like this. |
