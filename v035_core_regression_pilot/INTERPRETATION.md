# Manual interpretation of the diagnostic pilot

This document supplements the frozen automated metrics. External scores are kept
exactly as returned by Alpha's byte-identical evaluator. Manual observations do not
replace those scores. All eight FULL_END trajectories have been reviewed in
MANUAL_REVIEW.md; completion totals are recorded in REPORT.md and the final audit.

## Protocol recovery: narrow evidence

Neither BA-001 condition generated an invalid-reference protocol event. Native ran
one cycle and structured ran three; neither aborted. Therefore BA-001's specific
invalid-ID recovery mechanism is **not exercised**, rather than proven fixed.
Historical Alpha BA-001 FULL_END T1/T2 stopped before any cycles on malformed
references, but changed runs/settings/server and the small sample prevent a causal
or superiority claim.

BA-008 structured supplies real live recovery evidence elsewhere: six repair
requests, zero recorded successful repairs, twelve discarded invalid critique/plan
elements, and continued execution through three cycles. The discard logs are
explicit and retained; outputs were not silently accepted. This is recovery by
sanitization after unsuccessful repair. It costs six model calls and loses useful
critique/plan content along with invalid references. No claim of successful model
repair is justified by these events.

## Grounding: exact misattribution reduced, semantic attribution remains broken

BA-002 structured catches two task-only buggy-code quotes and one invented hybrid
quote. These become MISATTRIBUTED/UNGROUNDED and nondecisive; their exclusions are
appropriate. That is concrete, narrow live evidence for the new filter.

Both BA-002 conditions nevertheless reject externally passing candidates throughout
three cycles. Native adversarial judges confuse discussion of the original bug with
the corrected function. Structured judges quote the actual `size <= 0` guard and
claim it does not reject zero/negative values. UNQUOTED and textually GROUNDED
findings remain decisive even when their meaning is incorrect. All final regions
implement the corrected loop. Structured code lacks explicit integer validation,
a real docstring gap outside the seven frozen tests; the judges' stated objections
do not identify this gap reliably. Passing these checks is not universal correctness.

## False-premise handling: a quoted finding bypasses protection

BA-008 structured makes three premise-dependent adversarial findings nondecisive.
But other judges cite the same false premise, include a real candidate quote, remain
GROUNDED, and drive REJECT. Native shows the same quoted failure with no suppressed
finding. Existing `ground_issue` code returns GROUNDED on quote occurrence before
checking premise dependency. This precedence explains the observed bypass; no
Engine change is made here.

Task assertions are not promoted to a VERIFIED evidence record in these runs, but
the gate still uses the false assertion as a rejection yardstick. That violates the
desired behavioral invariant even though provenance bookkeeping remains unverified.

Native C0 and DIRECT explicitly correct the premise in their final prose. The frozen
regex misses the Markdown phrasing and assigns 0.5 with a manual-review flag. The
regex score is retained; it is not evidence of premise acceptance. Native revisions
then lose both the requested explanation and correction from the final region,
while internal comparisons falsely claim explanations remain identical. Structured
scores 1 throughout but repeats unsupported list.sort speculation and even includes
a malformed intermediate code block. The frozen evaluator certifies extracted
function behavior and matching text, not every statement or output-format nuance.

## Consensus/verification: detection does not enforce answer uncertainty

BA-009 structured never creates trusted independent evidence or verified acceptance;
its final gate REJECTS. This preserves the bookkeeping invariant. But all four
identical prose answers still favor a "likely" database problem caused by deployment
using engineer consensus, omit the requested JSON structure, and score 0. The answer
is returned with a rejection label rather than repaired into an appropriately scoped
result. The deterministic confirmation-word detector records no incident, which
does not establish adequate epistemic caution in the answer.

The first adversarial judge appropriately challenges causal inference and agreement
without evidence. Later judges supply false temporal objections (that a prior
deployment cannot cause a later incident) and demand unavailable specificity. All
are textually GROUNDED and decisive. Three unsuccessful plan repairs discard eight
changes, including useful changes qualifying consensus. Alternatives and synthesis
invent load-balancer/payment-gateway/connection-pool stories and a 23-minute interval
where the task timestamps differ by seven minutes. These are not measurements and
do not become independent evidence. No revision changes the scored answer.

BA-009 native returns C2 with `certainty="established"`, only E2 cited, and no
additional evidence needed; all C0–C3 final JSON objects are identical and score 0.5.
Engine checks detect agreement-as-confirmation in three candidates. Both judges
PASS C2 and its adversarial judge calls the engineers' statements confirmation.
Nevertheless evidence integrity keeps agreement model_claimed/corroboration only,
trusted independent evidence stays empty, and final gate REVISE/INCONCLUSIVE rather
than verified acceptance. Thus the verification-status invariant holds in observed
records, but the requested answer-level uncertainty invariant fails.

Three native plan repairs discard twelve field-name targets/changes. The discarded
plans explicitly propose reducing certainty and naming missing metrics; subsequent
revision requests carry only generic correction instructions. No final-region
change occurs. A later substantively justified adversarial objection is excluded
because its quotation is inaccurate; existing verifier concerns still prevent
acceptance. Grounding can reject a citation without establishing that the criticism
is false. The failure uses 32 calls and 108,520 tokens without encoded benefit.

## C0 hypothesis: mixed observations, no confirmation

BA-001 structured C0 scores 0 versus native/DIRECT 1. BA-002 all C0/baselines score 1,
with native/DIRECT supplying more complete type checks. BA-008 structured scores 1
and native/DIRECT 0.5, but manual inspection exposes the regex limitation and cleaner
native C0 code/prose. BA-009 native C0 preserves the requested JSON where structured
C0 fails it, but scores only 0.5 and makes an unsupported established claim. The
full four-task table in REPORT.md is authoritative. No systematic reduction of C0
degradation or resulting reasoning improvement is established.

Lengths in results.csv include the entire stored candidate, including in-band
reasoning. Native can emit large analysis text despite `think=false`; final-region
lengths are recorded separately in the supplemental audit. Native and DIRECT use
identical observable initial request payloads/seeds for each task, but outputs are
not identical on every task. BA-008 is identical; BA-001 differs. A fixed seed does
not establish reproducible text output for this local server/configuration.

## Hostile findings and repair priorities

1. A real quote proves occurrence, not factual correctness or semantic attribution.
   Task assertions still defeat true corrections when a judge supplies a quote.
2. UNQUOTED fatal assertions can reject passing functions and correct conversions.
3. Pairwise deltas contradict prose or claim gains between identical functions;
   native BA-008 comparisons overlook loss of required explanatory text.
4. Revisions often leave the encoded task score unchanged. Structured BA-001 even
   produces a malformed partial intermediate answer. Rollback avoids returning that
   candidate but does not repair the original numeric error.
5. Protocol sanitization prevents abort but discards substantive material after
   spending repair calls. It must not be described as six successful repairs.
6. Full answers may retain in-band analysis and repetitive commentary. Narrow
   deterministic format/leakage detectors do not prove full task compliance.
7. External tests and regexes have limited coverage; scores can miss real type or
   prose defects and can miss a valid premise correction. No evaluator is patched.
   Structured BA-009's zero unsupported-claim counter reflects its missing JSON
   early-exit path, not a manual finding that its causal prose is supported.

The appropriate next step is **a targeted repair and repeat diagnostic before full
uncapped Beta**, subject to separate authorization. Priorities are premise-check
precedence, semantic source attribution/unsupported fatal judgments, judge/gate
calibration, and revision preservation of requested output. Do not tune prompts
against these twelve outcomes or treat model-agreement evidence as correctness.
This observation task implements no fixes and does not launch Beta.

## Provenance and interruption

RESUME_RECORD.json preserves the interrupted BA-009 structured attempt and hashes
the nine completed trials before resume. Only the missing three runs are resumed.
Four archived responses account for 4,757 tokens and 48.905 seconds of measured
model latency. A fifth request began without a recorded response; its consumption
is unknown. Completed-trial totals exclude this overhead and interruption downtime.
Whole-pilot observed cost must include the four responses separately and disclose
the unobserved fifth request. No completed trial is overwritten or repeated.

The preflight fingerprints bind Engine source, copied tasks/evaluator and pilot
control code. Historical Alpha references are extracted from frozen saved outcomes
without rescoring. The 1,824 historical/research/root-report hashes and 64 Engine
source hashes were checked unchanged during resumed execution. The pre-existing
dirty Git tree is preserved; no commit, push or version change is part of this task.

## Final completion and cost

Exactly 12 planned/unique trials completed, with zero execution failures, zero
MODEL_PROTOCOL_FAILURE/EXTERNAL_BLOCKER terminations, and six frozen external
pass/fail failures. All eight FULL_END trajectories were reviewed. There are 22
completed END cycles, 18 rollbacks, twelve repair calls, zero recorded successful
repairs and 32 discarded protocol elements. Nine judge findings become nondecisive:
two MISATTRIBUTED, four UNGROUNDED and three TASK_PREMISE_DEPENDENT. No gate outcome
is ACCEPT_VERIFIED. No FULL_END returned answer improves its external score over C0.

Completed trials cost 237 model attempts, 576,527 tokens and 6,470.832698 seconds
(1h 47m 50.833s). DIRECT uses 4 calls/10,591 tokens/620.853s; structured uses
129 calls/226,927 tokens/2,535.794s; native uses 104 calls/339,009 tokens/3,314.186s.
Every condition passes two of four frozen external rubrics. Mean scores are 0.75,
0.50 and 0.75 respectively, but these are descriptive four-task figures with a
known BA-008 regex miss; they do not establish reasoning improvement.

Including preserved interrupted responses yields at least 241 recorded model
attempts and 581,284 tokens. Recorded trial wall plus interrupted response latency
is 6,519.737802 seconds; one additional interrupted request has unknown consumption.
This excludes interruption downtime, preflight tests, manual analysis and report
writing. No completed trial was repeated, overwritten or changed. Every projection
remained below six hours. There was no infrastructure defect or guard stop.

Final audit verifies all 64 Engine source/config hashes, 1,824 protected historical
file hashes, frozen pilot/task/evaluator hashes, nine pre-resume trial hashes and
interrupted artifact hashes. Every completed inference wire payload keeps the
specified local model/settings and loopback endpoint. All eight serialized decision
configs remain baseline: zero Jev and zero cloud calls. FINAL_AUDIT.json contains
exact call-role/repair costs and model identity checks. No Engine, historical
benchmark, validation report, Harness, version, commit or remote was changed.
