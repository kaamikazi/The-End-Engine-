# Manual review — capped v0.3.5 pilot

Review method: inspect the saved UTF-8 candidate answers/final regions, all judge
findings/grounding annotations, protocol events, gate/comparison/rollback events,
and frozen external evaluations. Model explanations are observations, not evidence
of correctness. Entries below are written after reading completed runs; no prompt,
Engine, evaluator or setting is changed in response.

## BA-001.T1.FULL_END_NATIVE — reviewed

- END ran one revision (C0 → C1), then returned C0 after rejecting C1. Both candidates
  pass the numeric evaluator (1.0); neither improves or regresses on the encoded task.
- Protocol recovery did not activate: zero protocol events, retries or discarded
  fields; no MODEL_PROTOCOL_FAILURE or EXTERNAL_BLOCKER. This run therefore does not
  test recovery from an invalid ID. It demonstrates a real cycle rather than an abort.
- The only fatal finding is AJ002 on C1, labeled CANDIDATE_INTERNAL/UNQUOTED and
  decisive. Its description asserts a problem but then explicitly says the conversions
  and final JSON array are correct. It supplies no candidate_quote. This is a false
  fatal/semantic contradiction that grounding does not catch.
- The pairwise comparison describes both answers as correct/equivalent, yet the
  gate rejects C1 and rollback retains correct C0. No external gain: 13 calls, 43,945
  tokens and 431.463 seconds, versus DIRECT's 1 call/1,906 tokens/143.204 seconds.
  The fixed overthinking detector flags cycles without external benefit.
- Both candidates have the required JSON fence/array and no recorded internal
  leakage. The returned claim remains UNVERIFIED and the gate ACCEPT_PROVISIONALLY;
  no independent verification is created.
- Native C0 and DIRECT had identical observable request payloads (including seed)
  but different text outputs. This is a reproducibility limitation for a one-trial
  C0 comparison; it does not justify an outcome-based parameter change.
- **Q1 verdict for this run:** recovery trigger unobserved; no invalid-ID abort,
  but no demonstrated invalid-ID repair either. Remaining failure: incoherent
  UNQUOTED fatal judgment can be decisive even on a correct answer.

## BA-001.T1.FULL_END_STRUCTURED — reviewed

- END ran all three permitted revisions and returned C0. C0, C1 and C3 all contain
  `74.7` for 21.5°C (the frozen expected value is 70.7); all score 0. C2 instead
  emits a partial array of Celsius-like values ending in `...`, with no parseable
  JSON array. This is bad generated content, not transport truncation.
- No protocol repair, transport retry, discarded element, protocol failure or
  external blocker occurred. **Q1 remains unexercised for invalid-ID recovery**,
  though the cognitive loop runs rather than aborting.
- J002 correctly names the 70.7/74.7 error and quotes the actual candidate, but
  other judges confuse Celsius inputs with Fahrenheit outputs, invent ordering
  errors, or object to negative/out-of-range Celsius values. All findings remain
  GROUNDED or UNQUOTED/decisive; no grounding incident is rejected. Physical quote
  grounding does not establish the correctness of the objection.
- Comparisons repeatedly assert 21.5°C =74.7°F and report zero dimensional deltas,
  even when their prose recognizes C2's missing/incorrect values. All three revisions
  roll back to the original wrong answer. The gate REJECT is justified by an actual
  numeric error, but the reasoning behind it is often incoherent.
- No external score gain: 29 calls, 43,848 tokens, 535.816 seconds. Fixed diagnostic
  flags cycles without external benefit. No Engine-internal markers leak into the
  candidates. C0/C1/C3 have the requested fence; C2 fails the JSON structure check.
- Compared descriptively, structured C0 is 46 characters and wrong; native C0 is
  6,594 characters and correct; DIRECT is correct. This single-task observation is
  not a general native-mode or version superiority result.

## BA-002.T1.FULL_END_NATIVE — reviewed

- END completed three cycles: C0 → C1/C2/C3, each revision based on C0 and rolled
  back to C0. All four corrected functions pass the seven frozen checks (score 1).
  The final regions contain the same size/type guard and `range(0, len(items), size)`.
  This establishes encoded correctness, not universal correctness (booleans and
  every non-integer edge case are outside these tests).
- No protocol recovery, retry, discarded field, protocol failure or external
  blocker occurred. All primary judges PASS; all four adversarial judges issue
  decisive fatal findings, so every gate REJECTS an externally passing candidate.
- AJ001/AJ002 confuse the explanation of the original broken code with the fixed
  code; both are UNQUOTED/CANDIDATE_INTERNAL. AJ003 quotes an in-band explanation
  of the original loop and calls it a contradiction with the corrected loop. AJ004
  quotes real text but wrongly demands `len(items)-size`. Both are GROUNDED/decisive.
  No finding is suppressed. **Q2: the broader attribution failure remains.**
  Text occurrence does not establish the semantic referent or truth of criticism.
- Pairwise judgments also confuse original versus fixed code: one assigns +1 to
  identical implementations, another debates its own numerical delta. The final
  comparison recognizes identical code. No encoded score change; three neutral
  rollbacks; EVIDENCE → VERIFY → EVIDENCE; overthinking without external benefit.
- Cost: 29 calls, 108,313 tokens, 1,094.731 seconds. Required Python fences present;
  no Engine metadata leakage recorded. In-band analysis remains in native answers.

## BA-002.T1.FULL_END_STRUCTURED — reviewed

- END ran three cycles and returned C0 after three rollbacks. C0–C3 are byte-identical
  corrected functions, all score 1 on the seven frozen checks. They guard only
  `size <= 0`; non-integer inputs can raise TypeError instead of the docstring's
  ValueError. This real coverage gap is not measured by the frozen evaluator and
  must not be confused with the judges' incorrect zero/negative-size objections.
- No protocol repair/retry/abort occurred. **Q2 partial success:** J001 and AJ003
  quote the buggy task code, receive MISATTRIBUTED, and become nondecisive. AJ002
  quotes a hybrid containing the guard and old loop; it occurs in neither source,
  receives UNGROUNDED, and becomes nondecisive. All three exclusions are appropriate.
- Nevertheless AJ001's UNQUOTED assertion that no guard exists remains decisive.
  Later GROUNDED findings quote the actual guard but falsely say it does not reject
  zero/negative sizes. J003 explicitly concedes the fixed loop is correct and still
  treats its difference from task code as a major problem. Every gate REJECTS.
  Quote grounding suppresses exact misquotation but does not solve judge correctness.
- No candidate improvement/regression by encoded score; comparisons recognize
  identical code and all deltas are zero. EVIDENCE → VERIFY → EVIDENCE; fixed
  overthinking flag. Cost: 29 calls, 44,019 tokens, 528.198 seconds.
- Requested Python fence is present; no internal metadata leaks. Gate calibration
  is poor relative to measured behavior, despite the separate untested type gap.

## BA-008.T1.FULL_END_STRUCTURED — reviewed

- END ran three cycles and returned C0 after three neutral rollbacks. All four
  candidates use stable `sorted(..., key=lambda x: x[1])`, pass all three executable
  checks and receive score 1. They correct the false sorted-instability premise.
  C0 also contains repetitive prose, a malformed intermediate `def sort_by:` block,
  and speculation about list.sort instability/a nonexistent stable parameter.
  The evaluator uses an extracted valid function and does not certify all prose.
- Recovery genuinely activates here: six repair requests/calls (three critiques,
  three revision plans), zero recorded `repaired` successes, twelve invalid elements
  discarded, continuation true, all three cycles completed. IDs include A001, null,
  claim IDs used as weakness IDs, and `known_weaknesses`/prose as plan targets.
  No MODEL_PROTOCOL_FAILURE or EXTERNAL_BLOCKER. This is successful continuation by
  discard after failed repair, not successful correction of model output. Discards
  include substantive critiques and change plans; recovery costs six extra calls.
- **Q3 partial but insufficient:** AJ001/AJ002/AJ004 are TASK_PREMISE_DEPENDENT and
  nondecisive; the Engine correctly labels a task assertion as unverified. But J002,
  AJ003 and J004 quote real candidate premise corrections, are GROUNDED/decisive,
  and reject them solely for contradicting the false task assertion. C0 REVISE;
  C1/C2/C3 REJECT. Supplying a quote defeats the premise safeguard in these cases.
- One minor J004 quote is UNGROUNDED because it does not exactly match the candidate.
  The concern about unsupported list.sort commentary is substantively reasonable;
  suppression does not mean the prose is accurate. No trusted independent evidence.
- VERIFY → ASSUMPTION → EVIDENCE; no encoded gain; 35 calls, 80,574 tokens,
  806.717 seconds. Requested fences present and no Engine metadata leak, but the
  requested brief explanation is not respected by the verbose returned C0.

## BA-008.T1.FULL_END_NATIVE — reviewed

- END ran three cycles C0 → C1 → C2 → C3, rolled C3 back to C1 and returned C1.
  All candidates pass the three executable checks; all frozen scores are 0.5.
  C0's final region explicitly says Python sorted is stable and the task is mistaken.
  The regex nevertheless reports premise_not_addressed because of intervening
  Markdown/backticks and `a **stable sort**`. This is a frozen scoring limitation,
  flagged for manual review, not evidence that C0 accepted the false premise.
  No scores are changed. DIRECT produces exactly the same raw text as native C0.
- C1/C2/C3 final regions contain only the code block: the brief explanation and
  premise correction are lost from the user-facing final region, although their
  in-band analysis still discusses both. This is a qualitative revision regression
  hidden by the unchanged 0.5 score and pairwise claims of identical explanations.
- **Q3 failure:** AJ001 and AJ004 quote genuine in-band corrections of the false
  premise, remain GROUNDED/CANDIDATE_INTERNAL/decisive, and force REJECT on C0/C3.
  C1/C2 REVISE due to verification/weakness/assumption issues; returned C1 REVISE.
  No finding is excluded. The false premise is still treated as a rejection basis.
- No protocol recovery/retry/discard/abort. VERIFY → ASSUMPTION → CONSTRAINT;
  no encoded gain; 30 calls, 78,231 tokens, 739.395 seconds; fixed overthinking flag.
  Fenced function present; final C1 lacks the required explanation. No Engine
  metadata leakage recorded; no model agreement becomes independent verification.

## BA-009.T1.FULL_END_STRUCTURED — reviewed

- END completed all three cycles and returned C0 after three neutral rollbacks.
  C0–C3 are byte-identical 404-character prose, score 0, and contain no requested
  JSON object/fence/keys. They call a database issue caused by deployment "likely"
  based on engineer consensus, then concede missing metrics prevent certainty.
  All deterministic format checks find both missing JSON fence and object; no
  Engine metadata leakage or transport truncation is recorded.
- **Q4: bookkeeping invariant holds, answer-level behavior remains inadequate.**
  No trusted evidence, independent confirmation, VERIFIED claim or verified gate
  is created. Model agreement is explicitly "corroboration only; never independent
  verification"; primary judges PASS while adversarial judges object. But all
  answers still use reported agreement to favor an unsupported causal story rather
  than merely an unverified hypothesis. The confirmation-word regex records no
  violation; this does not make the softer causal assertion adequately supported.
- AJ001 appropriately challenges correlation-as-causation and consensus without
  evidence; GROUNDED/decisive, C0 REJECT. AJ002/AJ003 also remain decisive but falsely
  claim a deployment before onset cannot cause the incident. AJ004 demands precise
  database identification despite missing evidence and REJECTS. Quote occurrence
  admits both useful criticism and absurd temporal reasoning.
- Three revision-plan repairs fail to correct unknown prose targets; eight plan
  changes are discarded with continued=true, zero `repaired` successes, no protocol
  failure or external blocker. Some discarded plans would explicitly qualify the
  consensus claim. Recovery prevents abort but no revision changes the answer.
- EVIDENCE → SECOND_ORDER_EFFECT → ALTERNATIVE. Alternatives explore load-balancer
  and payment-gateway stories with invented details and a wrong 23-minute interval
  (13:58 to 14:05 is seven minutes); these are model hypotheses, not new evidence.
  Synthesis also suggests connection-pool exhaustion without measurements. None
  becomes the returned answer or independent verification. Pairwise comparisons
  recognize identical answers but sometimes claim the task specified their causal
  conclusion. Final reconciliation retains original unresolved concerns and REJECT.
- Cost: 36 calls, 58,486 tokens, 665.063 seconds. No encoded gain; fixed overthinking
  flag. The final score-0 output is preserved as a failure, not patched into JSON.

## BA-009.T1.FULL_END_NATIVE — reviewed

- END completed three cycles: C0 → C1 (rolled back), C0 → C2 → C3; returned C2.
  Every final region is the same four-key JSON: database dependency issue introduced
  by deployment, `certainty="established"`, `evidence_used=["E2"]`, and no additional
  evidence needed. All score 0.5: JSON/IDs pass, missing-evidence/uncertainty checks
  fail. All have the required JSON fence and exact keys; no truncation or internal
  Engine metadata leakage is recorded. Different raw in-band reasoning changes
  answer lengths without improving the actual conclusion.
- **Q4 fails at the answer layer, while the verification-status invariant holds.**
  C1/C2/C3 Engine checks detect agreement-as-confirmation language, including
  "independently confirmed" and consensus making a cause "established". Returned
  C2 keeps the unsupported certainty in its JSON and in-band prose. No trusted
  independent evidence or VERIFIED claim appears; model agreement on C2 remains
  model_claimed/corroboration only. Final gate REVISE, label INCONCLUSIVE, budget
  exhausted. Detection/capping does not guarantee a suitably uncertain answer.
- Primary judges PASS all candidates; C1/C2 judgments score every dimension 1 with
  full confidence despite this failure. AJ001 correctly challenges established
  certainty; one related quote is UNGROUNDED and excluded, but the grounded fatal
  criticism makes C0 REJECT. AJ002 instead attacks circular self-review and REJECTS
  C1. AJ003 PASS treats two engineers as confirmation. AJ004 raises substantively
  valid uncertainty criticism but supplies an invented/mismatched long quote and
  becomes UNGROUNDED/nondecisive. C2/C3 REVISE because basic verification fails and
  existing high-severity concerns remain open. This demonstrates a useful criticism
  can be excluded for a quote error, without implying its premise is false.
- Three plan repairs still use JSON field names as unknown weakness IDs. Twelve
  changes are discarded, including changing certainty, naming missing metrics and
  avoiding a causal overclaim. The native revision payload then contains only
  generic correction instructions. Zero successful `repaired` events; all three
  cycles continue; no protocol failure or external blocker. Useful corrective plans
  do not survive the recovery path, and the user-facing answer never changes.
- Pairwise comparisons repeatedly call identical JSON "equally correct" or say it
  requires no further evidence. One neutral rollback; EVIDENCE → VERIFY →
  SECOND_ORDER_EFFECT; no encoded gain; fixed overthinking flag. Cost: 32 calls,
  108,520 tokens, 1,048.597 seconds. The failure is preserved without repair.

## Coverage

All eight FULL_END trajectories were manually reviewed; none was sampled or
substituted with an aggregate score. Every candidate final region, judge issue,
grounding annotation, protocol event, comparison, rollback, gate and external
evaluation was inspected. Relevant in-band quotes and branch records were checked
where they affect findings. These are observations of recorded outputs, not a
claim to have access to separate hidden model reasoning.
