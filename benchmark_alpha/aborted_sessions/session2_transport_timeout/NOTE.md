# Run re-executed after an infrastructure timeout (original preserved)

BA-003.T1.SELF_REFLECT failed with `transport_error: timed out`: the benchmark transport timeout (300 s) was shorter
than the time the model needs to produce the permitted 4096 output tokens (~14 tok/s for long outputs). The
self-critique call was cut by the harness, not by the condition. The timeout was raised to 900 s; every other run
completed before this point had no call longer than 78 s, so it was unaffected. This record is exactly as written;
the run was executed again in the main benchmark under the 900 s timeout.
