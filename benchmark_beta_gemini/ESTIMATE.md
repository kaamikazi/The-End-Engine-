# Benchmark Beta-Gemini — pre-launch estimate (NOT RUN)

- **Status:** prepared, not launched. Awaiting approval of these numbers, and a `GEMINI_API_KEY` for the one-request
  probe.
- **Design:** 5 conditions × 12 tasks × 2 trials = **120 runs**, seed 20261103.
- **Model:** `gemini-3.8-flash`, the same for every condition.

## Basis

- **Measured:**
  - one completed local-Qwen FULL_END_NATIVE DEEP run under v0.3.5: 66 calls; 246,501 input and 34,028 output tokens
    (3,735 input / 516 output per call);
  - Alpha's DIRECT (1 call, ~150 input, ~3,000 output) and SELF_REFLECT (3 calls, ~8,500 input, ~6,400 output) runs.
- **Assumption:** Gemini prompts are the same rendered text, so input tokens are similar. Visible output will likely be
  shorter (no in-band reasoning), but hidden thinking at `thinkingLevel=low` is billed as output.
- **Task mix:** the Engine's own analysis puts 6 of the 12 tasks in DEEP mode (up to 6 cycles, with branching) and 6 in
  NORMAL mode (up to 3 cycles).

## Requests

| Condition / group | Runs | Calls per run | Requests |
|---|---|---|---|
| DIRECT | 24 | 1 | 24 |
| SELF_REFLECT | 24 | 3 | 72 |
| END_LITE_NATIVE (normal, 2 cycles, no judges) | 24 | ~12 | ~288 |
| FULL_END_* on NORMAL tasks (≤ 3 cycles) | 24 | ~38 | ~912 |
| FULL_END_* on DEEP tasks (≤ 6 cycles + branching) | 24 | ~66 | ~1,584 |
| **Total** | 120 | | **≈ 2,900** |

With transport retries and protocol repairs, about 3,000; the upper bound is **≈ 3,500**.

## Tokens

| Group | Runs | Tokens per run | Total |
|---|---|---|---|
| DIRECT | 24 | ~2k | ~0.05M |
| SELF_REFLECT | 24 | ~10k | ~0.24M |
| END_LITE_NATIVE | 24 | ~37k | ~0.9M |
| FULL_END on NORMAL tasks | 24 | ~160k | ~3.8M |
| FULL_END on DEEP tasks | 24 | ~280k | ~6.7M |
| **Central total** | | | **≈ 11.7M** |

- **Split:** about 10.3M input and 1.4M output, plus hidden thinking (roughly 0.5–1k per call at `low`, about +1.5–3M
  output).
- **Planning maximum:** about **16M input and 5M output**, i.e. 1.5× the central figure plus the full thinking
  allowance.

## Cost (if billed at the paid tier)

Official prices (ai.google.dev/gemini-api/docs/pricing) until 2026-12-31: **$0.75 per 1M input, $3.75 per 1M output,
thinking included**. They double from 2027-01-01.

| Case | Cost |
|---|---|
| Central | 10.3M × $0.75 + (1.4M + ~2M thinking) × $3.75 ≈ **$20** |
| **Maximum** | 16M × $0.75 + 5M × $3.75 ≈ **$31** |
| If run after 2026-12-31 | ≈ $62 maximum |

No grounding, search, code execution, tools or context caching are used, so there are no other charges.

## Rate limits and tier

- **Not published.** Google shows per-model limits for each project only in Google AI Studio
  (ai.google.dev/gemini-api/docs/rate-limits).
- **Free tier:** one unofficial developer report (discuss.ai.google.dev, 2026-09-03) states **20 requests per day** for
  `gemini-3.8-flash`. At that rate, 3,000 requests would take about 150 days, so **the free tier is not viable**. Even
  a 1,500-per-day free limit (an unverified third-party claim) would take about 2 days.
- **Tier 1:** requires a linked Cloud billing account.
- **Google AI Pro:** the API documentation does not tie API quota to a Google AI Pro (consumer) subscription.
  **Assume it does not apply.** Check your project's tier and limits in AI Studio.
- **What the transport does:** HTTP 429/500/503 get bounded backoff (honouring `retryDelay`). A quota that stays
  exhausted fails the run as an *external* failure, recorded, never retried indefinitely.

## Runtime

- The run is sequential (randomized order as designed).
- At about 3–8 s per call, 3,000 calls take **≈ 4–7 hours**; the range is 3–10 hours depending on latency and thinking.
- At Tier 1, request-per-minute limits should not bind at ~10 requests per minute.
- **Not affected by the local machine:** inference runs remotely, so the laptop only needs to stay online and awake.
