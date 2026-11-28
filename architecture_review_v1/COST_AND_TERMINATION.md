# Termination, computational cost and separate value axes

CALL_AUDIT joins every physical provider record to one trajectory model_call step and its request purpose. Tokens are provider-reported input+output, not estimates. Provider latency below excludes some wrapper/orchestration overhead. Sum physical provider latency is not calendar elapsed or sum whole-run wall; whole-run total is15,293.791163s. No monetary/electricity price is recorded, so currency cost is unknown. No current provider request was made to obtain it.

| Purpose | Calls | Tokens | Provider latency s | Observed direct output / value |
| --- | --- | --- | --- | --- |
| adversarial_judging | 60 | 190,188 | 3072.584698 | 60 adversarial opinions; genuine gaps plus false fatal/premise objections |
| adversarial_test_generation | 60 | 99,002 | 1905.703734 | 60 scenario proposals; no runtime tool execution |
| branch_activity | 8 | 11,954 | 218.088480 | 8 branch generation/evaluation/synthesis calls across2 ALTERNATIVE cycles; hypotheses only |
| candidate_comparison | 54 | 131,176 | 1596.414341 | 44 parent comparisons plus10 best-candidate comparisons; no score gains found |
| initial_generation | 16 | 26,672 | 1657.859163 | 16 C0s;10 score1; no verified evidence |
| model_verification | 60 | 124,625 | 830.337101 | 60 model assessments;0 executed evidence; opinions can change issues |
| operator_critique | 50 | 166,529 | 1668.741011 | 44 ingested critiques/57 finding occurrences;6 repair calls included |
| primary_judging | 60 | 178,230 | 1914.313098 | 60 primary opinions; findings/feedback, not evidence |
| revision_generation | 44 | 81,849 | 1590.585557 | 44 children;0 score gains,1 loss; mixed safety and format changes |
| revision_planning | 54 | 129,849 | 822.824361 | 44 plans;10 repair calls included; invalid/unavailable repair actions observed |

Operator execution and critique are the same physical stage here; do not double-count them. Trajectory judging, QualityGate, utility, claim extraction, audits, progress and final guards are deterministic/local computations: **zero additional model calls**. Other/unmapped purposes: zero in this completed FULL_END population. Protocol repair is an overlapping subset, **16 calls/53,418 tokens/458.637350s**, already in critique/planning. Old12 repairs fail with32 discarded elements; new4 yield3 accepted successes,1 failure and2 discarded elements; zero suppression activates in the newer completed pilot. Protocol success does not establish diagnosis truth.

## Calls associated with activity without encoded quality gain

- All44 revisions and their later judgments are in runs whose final score never exceeds C0; this is an outcome association, not a counterfactual attribution.
- 30 unchanged raw/historical-answer transitions:256 associated-cycle calls/590,742 tokens. They can still check safety or bounded properties; original delimiter limitations apply to answer-region identity.
- 28 exact repeated critique findings and1 tentative reformulation; cost cannot be split per finding because a call can contain several. CALL_AUDIT cycle join supplies conservative whole-cycle association, not a per-finding causal bill.
- 18 rollbacks old,0 new; discarded/empty plans in old BA-009 prevent valid repair instructions. Call-budget savings under a different policy are unobserved.
- 24 transitions enter from external score1: additional work might repair unmeasured safety/prose gaps, but no encoded gain and one encoded loss occur.

Answer-quality value: no measured gains; one measured loss, plus qualitative losses missed by rubric. Epistemic-safety value: new native BA-009 lowers established→likely in cycle2, but invents an ID; filters suppress some false premise/semantic allegations without verifying answer truth. Computational cost:466 calls/1,140,074 tokens/4h14m53.791s of completed FULL_END run wall. These three axes must not be collapsed to 'waste' or 'success'.

## Why continuation survives

Both pilots have22 cycles: one native BA-001 cycle, three each for the other seven runs. Each has seven BUDGET_EXHAUSTED and one ACCEPTED_PROVISIONALLY stop. Old no-progress reasons/counters were not recorded: missing, notzero. New has22 cycle-progress records, no NO_PROGRESS stop. Raw-content/proposed issue/claim/verifier churn resets counters without a score gain; some unchanged cycles increment counter. BA-002 structured reaches2 only at ordinary cap; BA-008 structured reaches2 but high-risk-assumption protection applies. New native BA-009 mandatory overclaim correction protects the useful second status-qualification attempt. No-progress absence alone is not a detector bug and does not authorize removing mandatory constraints.

Current v0.3.5.2 filters advisory issues/unverified claim/model verifier churn from progress, but content/branch/gate change can still be qualitative or adverse. It enforces cycle/operation/shared-call ceilings and lets mandatory actions block NO_PROGRESS, while stopping never creates acceptance. Default max_run_calls=None for baseline is a publication-independent research risk: finite cycles are not a global physical-call ceiling. Future runs must explicitly set one.

## Denominators and interrupted cost

Completed DIRECT+FULL pilots together:24 trials/474 calls/1,160,460 tokens/16,643.512606s; primary FULL totals exclude8 DIRECT calls/20,386 tokens/1,349.721443s. The pilot reports separately retain18 saved interrupted responses/21,041 tokens/463.146185s provider latency across both archives, plus3 started calls with unknown consumption. These partial numbers come from historical interruption records, not a complete cost census or independent fresh runs, and must not be added to44 completed cycles. No missing response tokens are silently zero-filled. Benchmark Alpha is further context, not pooled with these denominators.
