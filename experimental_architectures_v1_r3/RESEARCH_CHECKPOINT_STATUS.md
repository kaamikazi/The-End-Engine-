# END v1.0.2 source checkpoint — WIP

ENGINEERING STATUS: WIP

CERTIFICATION CORRECTION: Implemented locally; focused controls passed. Exact current correction source is copied without alteration.

CONTRACT REVIEW: REVISE_CONTRACT_PROPOSAL. A new v2 proposal is CONTRACT_REVISION_READY_FOR_REVIEW (documentation only); independent approval of v2 is pending. Current implementation does not implement required v2 observations or schema.

HISTORICAL ACCEPTANCE: Unresolved.

CURRENT UNIT TESTS: 222 pass, 16 fail, 6 error, 0 skip (244).

REVIEWER CONTRACTS: 146 pass, 8 fail (154). Prior 49: 48 pass, 1 fail. Reviewer-designed 62 observations:61 pass,1 retained fixture-expectation failure. Author 37 reexecution is separately 37 pass. These retained baselines are not newly green results.

INDEPENDENT HUMAN APPROVAL: Pending. Prior review was fresh AI review, not authenticated external human audit.

LIVE MODEL COMPATIBILITY: Pending.

EMPIRICAL BENCHMARK: Not run.

Green focused controls do not supersede historical failures. Mock-wiring outcomes are diagnostic, not empirical model performance. This branch is not a release, acceptance decision or implementation of the v2 proposal.

## Reproduce the current source unit suite offline

Use Python 3.12 on Windows local NTFS (F01 native read-share denial/leases/hard links are required). Set PYTHONDONTWRITEBYTECODE=1, then from experimental_architectures_v1_r3 run `python -B -m unittest discover -s tests -t . -v`. The recorded current acceptance failures/errors are expected evidence, not targets to hide. The native bridge is exercised only with canned Script data by tests; do not call providers or Ollama. Validation summaries record actual new checkpoint execution separately.

## Provenance and public scope

The checkpoint starts at the already-public Engine checkpoint 6f4da3f1e30a842ab37adb7a9be12a0222a80054. Source bytes originate from local bc9bcbad8e9cb051d54c3b270e2e03d460858986 plus its separately hashed uncommitted certification correction. This is a selective source snapshot, not a merge/cherry-pick/history rewrite of the eight unpublished research commits. Their history remains local unchanged.

Only necessary source/tests, explicitly public/synthetic input definitions, runtime integrity metadata, the new proposal and concise WIP records are included. Engine/baseline source already on the public base is unchanged. Private reviewer archives/scripts/raw reports, frozen v1.1.1 payload/fixtures/rubrics, generated trajectories, raw logs and original proposal/support duplicates are deliberately excluded. Private reviewer-suite sources are not distributed here; their results are historical observations with independent-review receipt hashes, not a claim those private suites can be reconstructed from this public branch.

The frozen evaluator is independently verified locally at root 23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09 (725 files); it is not newly uploaded. Engine 0.3.5.2 fingerprint 29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82 is unchanged. Existing public evaluation exposure is not resolved or expanded by uploading new evaluator bytes. Opaque integrity hashes are not scientific approval or provider-authenticated provenance.
