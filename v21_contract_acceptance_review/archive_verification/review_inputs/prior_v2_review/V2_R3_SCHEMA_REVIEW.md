# Independent R3 schema review

**REVISE.** The candidate authority and no-selection rules are substantially improved, but the advertised complete tagged union is not yet a complete, mutually discriminated contract. This is a documentation design gap, not a failure of a shipped v2 parser; none exists.

`R3_CANDIDATE_SCHEMA_V2.md:3` correctly separates current legacy implementation_version 1.0.1 (no schema/completion tag), current abc-r3-blocked-recovery-v1 diagnostics and the prospective end-run-outcome/2-proposal.1 envelope. Graph revision 1.0.2 is not an output discriminator. Lines 31–37 correctly distinguish absent, null and known-empty, require diagnostic selected_candidate=null / NOT_CERTIFIED, retain candidate observations, and prohibit synthesized legacy C0/FINAL. Existing suspect selections belong under prior_result_observation with currently_verified=false.

## Material findings

**R3-UNION-01 — variant partition and rejection representation.** Lines 9–12 do not define a deterministic partition. NORMAL_COMPLETED_RESULT describes verified persisted terminal bindings, while UNKNOWN_OR_INTERRUPTED_RUN may also be a verified persisted terminal. A valid recovered C0 with verified provenance and termination_reason=INTERRUPTED fits both descriptions. The proposal must specify whether class follows provenance uncertainty, terminal reason, or another explicit predicate, including verified-provenance failed/invalid terminals and successful persisted restricted terminals. The completion flag for UNKNOWN_OR_INTERRUPTED_RUN is described as 'can be true' without defining false versus absent states. PROVENANCE_INTEGRITY_FAILURE is described as a typed rejection optionally surfaced via a diagnostic rather than a clearly specified serialized member or an explicitly separate exception channel. Specify one interpretation and its exact allowed field/value combinations.

**R3-FIELDS-02 — required/forbidden fields are incomplete.** The general absent/null/empty definitions are sound but do not tell a producer or validator, for each of the four variants, which selection, observation, certification, accounting, result/payload and completion fields must exist, must be absent, may be null or must be known-empty. Only diagnostic selection has a concrete requirement. The envelope's version strings are named but not fully tied to a required field table. State allowed provenance/termination/selection/certification combinations, including absence of any eligible candidate, preserved valid C0 plus an unresolved later attempt, missing bytes, unavailable lineage and prior-result observations. A reader must not have to choose a convention to implement 'mixed tags fail closed'. A finite normative truth table is sufficient; implementing a parser is outside this task.

These are material because two implementers can otherwise choose different valid classes or fields for the same evidence, and compatibility tests could each pass against a different assumed model. A reviewer-authored schema model can demonstrate underdetermination; it cannot supply missing author contract rules or count as v2 runtime conformance.

## Candidate and handle review

The documented run/task/call/attempt binding, original wire/provenance hashes, settled-before-use ordering, distinct handle identity, settlement equality and parent references preserve the scientific property. Observed content is not selected content. Fresh numeric-invalid control retains the original generated raw answer while final_candidate and FINAL are null. Graph probes reject missing candidates and rebound handles. Valid STOP retains C0. Legitimate interrupted recovery retains known reservations/candidates without inventing an answer for an unresolved call. Do not demote all valid C0 observations simply because an unrelated later cost is unknown.

Missing candidate bytes must stay explicitly missing; null cannot fabricate identity or lineage. Empty observations require known coverage, not merely a failed parse. Candidate/lineage status also needs a per-variant representation so a restricted but valid retained selection cannot be confused with a diagnostic uncertified selection.

## Required compatibility checks

1. Archived original legacy normal records remain readable only through their original complete payload/publication/identity verification, including valid completed, failed, invalid, interrupted, unknown-cost and zero-attempt terminals. No historical bytes/tags are rewritten.
2. Current abc-r3-blocked-recovery-v1 with false completion cannot pass a legacy normal reader; missing final_candidate/C0/FINAL cannot be interpreted as a successful empty answer.
3. Every exact v2 variant is accepted only by an opted-in v2 reader after its own full discriminator/field validation; legacy readers reject the v2 envelope even if it carries a verified legacy payload observation.
4. Unknown versions/classes, version mismatch, missing required completion flag, contradictory normal/diagnostic tags, BLOCKED+normal certificate, diagnostic+selected FINAL, false/true/null/absent flag substitutions and payload/outer-envelope disagreements fail closed.
5. Candidate byte/hash/identity/handle loss or rebinding, invalid numeric selection, missing/unavailable lineage and noncertified prior-result selection fail; valid C0 and restricted interrupted recovery remain usable.

`R3:41` says unknown/mixed forms fail closed and calls for an opt-in adapter; this is the correct policy. Known tests/helpers and wiring consumers access legacy fields directly (`R3:43`), so this policy must be implemented and tested at the reader boundary. External consumers remain unknown. A documentation instruction cannot retroactively make an arbitrary existing legacy consumer safe.
