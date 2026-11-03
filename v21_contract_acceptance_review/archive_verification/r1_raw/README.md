# Independent R1 raw evidence

`inspect_retained_evidence.py` is a reviewer-owned standard-library, read-only probe. It never imports END source, executes a provider, acquires runtime locks or pretends to implement R1. It reads strict JSON witness fields, byte hashes, journal representations and complete fixture inventories. Missing original schema/compiler execution and absence of a coordinated domain prevent any runtime A/S claim.

`RETAINED_EVIDENCE_INSPECTION.json` is the initial direct external fixture inspection: sixteen cases,63 exact cited witnesses, zero hash mismatches. `RETAINED_EVIDENCE_ARCHIVED_COPY_RECHECK.json` independently reruns the same checks on copied inputs. `RETAINED_EVIDENCE_WITH_JOURNAL_CHECKS.json` adds explicit raw chain/identity/response comparisons, including original header/receipt commitment rejection after rehashing. None is the author's checker. A failed witness predicate here is retained evidence of an intentionally damaged fixture, not a discarded test failure.

`PRESERVED_INPUT_COPY_RECEIPT.json` records307 copied files/699754 bytes, all source/copy hashes equal:289 small synthetic fixture files plus18 contract documents. Copied identity paths remain original and intentionally do not become relocatable certificates. These controlled fixtures contain public/mock research inputs; they do not establish authenticated provider activity. Original directories are untouched.

Reproduce from an extracted bundle using its local Python and absolute bundle paths:

```powershell
python -B '<bundle>/r1_raw/inspect_retained_evidence.py' --fixture-root '<bundle>/r1_raw/retained_fixtures' --document-root '<bundle>/r1_raw/contract_documents' --output '<new-review-output.json>'
```

Use a fresh output path to preserve these existing receipts. The expected accounting-predicate failures are only full settlement-row equality for `ledger_disagreement`, and registered response existence/commitment resolution for `missing_response_anchor`. Journal representation checks fail in the named damaged cases. The moved journal's bytes are intact at its forensic location; the duplicated journal has two paths with identical bytes, and copied response records do not create another independent event.

`write_review_tables.py` serializes this reviewer's explicit per-case decisions and twenty prospective adversarial adjudications. It is not a runtime validator or migrated acceptance suite. `preserve_retained_inputs.py` copies only the exact recorded small synthetic inputs and reviewed docs with byte verification; it never repairs or relocates authoritative source records.
