# Benchmark Beta-Gemini (prepared, not run)

A **separate** experiment that answers one question: does END Engine v0.3.5 improve `gemini-3.8-flash` relative to
DIRECT and SELF_REFLECT on the same model, the same tasks and the same evaluators?

## What it does not answer

- **v0.3.4 vs v0.3.5.** No v0.3.4 Gemini control has been run.
- **Anything about Qwen.** Benchmark Alpha (`benchmark_alpha/`, qwen3:4b, v0.3.4) stays the frozen historical Qwen
  baseline. The local-Qwen v0.3.5 Beta attempt (`benchmark_beta/aborted_local_qwen_attempt/`) is incomplete
  (2 of 120 runs) and is not a result.
- **Gemini and Qwen are never mixed.**

## Design

| Item | Value |
|---|---|
| Conditions | DIRECT, SELF_REFLECT, END_LITE_NATIVE, FULL_END_NATIVE, FULL_END_STRUCTURED |
| Runs | 12 tasks × 2 trials = 120 runs, seed 20261103 |
| Tasks | `tasks/`: Alpha task pack, hash `9e177f6d…`, byte-identical |
| Evaluators | `bench/evaluators.py`, byte-identical to Alpha's (`2570b663…`) |
| Engine | v0.3.5 (fingerprint `520d2052…`), unmodified |
| END settings | `protocol_repair_attempts=1`; `candidate_generation` native for END_LITE_NATIVE and FULL_END_NATIVE, structured for FULL_END_STRUCTURED |

**Model settings (`bench/gemini.py`):**
- `gemini-3.8-flash`, temperature 0.7, topP 0.8, maxOutputTokens 4096;
- `thinkingLevel=low` (thinking cannot be disabled on this model);
- no tools, grounding, code execution or system instruction;
- one transport retry for malformed structured output;
- bounded backoff on HTTP 429/500/503.

**API key:** read only from `GEMINI_API_KEY` at request time and sent only in the `x-goog-api-key` header. It is
never written to source, artifacts, manifests, logs, prompts or git.

## Commands (run from this folder)

```
python -B -m unittest discover -s tests -t .
python -B -m bench.cli preflight
python -B -m bench.cli probe
python -B -m bench.cli live . --trials 2
```

- **preflight:** no network.
- **probe:** exactly one tiny request; writes `PROBE.json`, which never contains the key.
- **live:** only after the estimate in `ESTIMATE.md` is approved.
