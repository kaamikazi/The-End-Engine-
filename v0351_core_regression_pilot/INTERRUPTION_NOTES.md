# Interrupted attempt — separate from the twelve completed-trial matrix

On user retry, the previous Python process was absent. Its stale status recorded
BA-001.T1.FULL_END_STRUCTURED call 12 (adversarial tests), with no saved response.
Cause of interruption is unknown. Two completed trials were hashed and preserved;
only missing trials resumed. Raw partial artifacts were archived automatically.

The interrupted attempt has eleven saved responses: 13,717 tokens and 345.755007
seconds of observed response latency. One additional started call has unknown
consumption. Completed-trial totals exclude this overhead; final whole-replay
accounting must add it separately and retain the unknown component.

Two protocol repair calls are observable in the archived call log:

- Call 7, critique, 1,907 tokens. Its response still uses unknown weakness ID
  `C0:formatting_error`. It alleges a trailing comma and invalid leading space in
  an array that has no trailing comma and permits whitespace. No scope proof supports
  this allegation.
- Call 9, revision plan, 806 tokens. Its response still targets unknown ID `W0`.
  It proposes removing the same imaginary comma/invalid whitespace.

Call 10 performs a revision and call 11 verifies it, so execution demonstrably
continues after the bad reference/plan outputs. The full trajectory and terminal
repair counters were not persisted before interruption. Thus these observations
are partial live recovery evidence, not another completed trial or a final
successful-repair verdict. They must not be pooled silently into completed-run
repair statistics. No model output from this attempt is reused as fresh inference.

The interrupted C0 contained 74.7 for 21.5°C, whereas the resumed fresh C0 contains
70.7 under the same frozen settings/seed scheme. This is an additional sampling/
reproducibility limitation, not an Engine revision or a causal version benefit.

## Second interruption and resume

On the next user retry, process 9896 was absent, with nine completed trials and
stale BA-009 structured call 4 (judgment) status. Approval review had previously
become unavailable because of its usage limit; the exact cause/timing of process
termination is unknown. All nine completed trial hashes and frozen source/history
were verified before resuming only BA-009 structured, native and direct.

The interrupted BA-009 structured attempt has three saved responses, 2,567 tokens
and 68.486074 seconds of observed response latency. Call 4 started but has no
saved response; its consumption is unknown. These partial outputs were archived
under `incomplete_attempts/BA-009.T1.FULL_END_STRUCTURED/20261007T170700192533/`
and verified against `RESUME_RECORD_2.json` in `RESUME_ARCHIVE_INDEX_2.json`.
No partial response is reused as a new trial response. No repair call appears
in these three saved responses.

Across both interruptions: fourteen saved responses, 16,284 tokens and 414.241081
seconds of observed latency, plus two started calls with unknown consumption.
This is extra overhead beyond the twelve completed-trial totals. Session gaps
are not inference runtime and are not pooled into completed-trial wall time.
