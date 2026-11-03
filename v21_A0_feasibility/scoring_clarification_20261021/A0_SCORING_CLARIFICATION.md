# A0 negative-control scoring clarification — 2026-10-21

Approved scoring is applied only to preserved recursive-lock negatives A0-04/A0-05 in both attempts. All four satisfy their original explicit bounded-sentinel expectation. Raw evidence, original PASS/FAIL/ERROR/NOT_EXECUTED statuses, source and probe scripts remain unchanged. These are retrospective annotations, not new test executions.

| Attempt | Vector | Measured sentinel duration (s) | Explicit bound (s) | Control verdict |
|---|---|---|---|---|
| attempt_001 | A0-04 | 0.6089999999994689 | <3 | PASS |
| attempt_001 | A0-05 | 0.6099999999996726 | <3 | PASS |
| attempt_002 | A0-04 | 0.6090000000003783 | <3 | PASS |
| attempt_002 | A0-05 | 0.6099999999996726 | <3 | PASS |

The 0.6-second timed-wait threshold and three-second overall sentinel bound are separate. The recorded duration includes termination/join overhead; a separate exact watchdog-trigger timestamp was not recorded and is not invented. Every record contains observed_event, expected_event, elapsed_time, bound_satisfied, control_verdict and feasibility_implication. Expected child exit1/blocked operations remain visible and are not described as successful lock acquisition or safe production reentrancy.

**A0_FEASIBILITY_BLOCKED remains.** Attempt_002 remains19 PASS/1 ERROR; attempt_001 remains10 PASS/1 FAIL/9 NOT_EXECUTED. The separate real-writer mutation and A0-18 collection error are unresolved. The earlier A0 stop rule for a real writer changing evidence outside the declared domain remains applicable. This scoring-only clarification does not authorize restarting probes across that stop or starting A1.

All721 previously manifested evidence file hashes were verified unchanged. No new feasibility probes, implementation edits, reservations, dispatches, provider calls, benchmarks, commits or pushes occurred.
