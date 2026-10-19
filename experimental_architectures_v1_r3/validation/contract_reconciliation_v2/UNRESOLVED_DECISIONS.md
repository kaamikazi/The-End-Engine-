# Open decisions after v2 drafting

- Independent review of this v2 proposal is PENDING. R1's sixteen prior labels remain historical AMBIGUOUS_CONTRACT dispositions; mandatory scoped observations resolve the prospective design choice, not old API equivalence retroactively.
- Select supported public/internal API boundaries and compatibility policy after local/external consumer inventory. External consumers are unknown; no broad compatibility guarantee is claimed. Names execute_outcome_v2/end-run-outcome/2-proposal.1 are prospective, not shipped APIs or version bumps.
- Approve observation snapshot/coverage semantics under the cooperating-writer trust model, including missing/changed anchors and witness-only usage. No provider-signed cardinality or hostile-host completeness is claimed.
- Implement and independently validate the prospective adapter/claims/tests only under new scope. Current source still returns null aggregates and raw snapshots rather than the required structured claims.
- Human semantic adjudication, authenticated external human approval, live provider compatibility, contamination clearance and empirical evaluation remain PENDING or NOT_RUN. Existing mock trajectories do not prove improved reasoning.
- Public-disclosure clearance is independent of scientific freeze/review approval. Private reviewer archives, unapproved evaluator changes/holdouts and uncleared trajectories remain local. A safe WIP source checkpoint must avoid their unpublished ancestry and cannot rely on ignoring files only in its latest commit.

All original failed outcomes, reviewer fixture failure and first supplemental setup failure remain preserved in original evidence. This proposal task does not change source or historical assertions to obtain green results.
