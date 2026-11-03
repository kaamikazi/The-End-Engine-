"""Check reviewer deliverables and seal a local byte receipt; no test rerun."""
import csv, hashlib, io, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = ['A0_INDEPENDENT_REVIEW.md', 'COLLECTOR_RETEST_RESULTS.json', 'WRITER_DOMAIN_FINDING.md', 'EXPERIMENT_MINIMUM_EVIDENCE.md', 'PATH_A_VS_PATH_B.md', 'ACCOUNTING_VALIDITY_MATRIX.csv', 'NEXT_SLICE_RECOMMENDATION.md', 'PRESERVATION.json', 'FINAL_DECISION.json']
checks = {}
for name in required:
    text = (root / name).read_text(encoding='utf-8')
    checks[name] = {'present': True, 'nonempty': bool(text.strip())}
    assert text.strip()
    if name.endswith('.json'):
        json.loads(text)
rows = list(csv.DictReader(io.StringIO((root / 'ACCOUNTING_VALIDITY_MATRIX.csv').read_text(encoding='utf-8'))))
assert len(rows) == len({r['case_id'] for r in rows})
assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
conditions = ['DIRECT', 'SELF_REFLECT', 'FROZEN_CURRENT_END', 'SPARSE_DELIBERATION', 'DIRECTED_REPAIR', 'BOUNDED_ALTERNATIVES']
assert all(any(row['condition_scope'] == condition for row in rows) for condition in conditions)
preservation = json.loads((root / 'PRESERVATION.json').read_text(encoding='utf-8'))
assert preservation['passed'] and preservation['prior_protected_inventory_matches']['passed']
collector = json.loads((root / 'COLLECTOR_RETEST_RESULTS.json').read_text(encoding='utf-8'))
assert collector['independent_reviewer']['executed_controls'] == 1
assert collector['independent_reviewer']['actual_driver_exit'] == 0
assert collector['independent_reviewer']['counts'] == {'PASS': 1, 'FAIL': 0, 'ERROR': 0}
assert collector['historical_A0']['counts'] == {'PASS': 19, 'ERROR': 1}
receipt = {'scope': 'Administrative completeness/parse checks only, not additional A0 executions or scientific tests', 'required_deliverables': checks, 'required_file_count': len(required), 'accounting_matrix_rows': len(rows), 'six_explicit_condition_rows': conditions, 'protected_inventory_files_verified': preservation['unique_files_hashed_after'], 'passed': True}
(root / '_control/DELIVERABLE_VERIFICATION.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
manifest_path = root / '_control/REVIEW_FILE_HASHES.json'
files = {p.relative_to(root).as_posix(): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and p != manifest_path}
manifest = {'purpose': 'Local integrity receipt, not authenticated human approval or provider origin', 'self_excluded': '_control/REVIEW_FILE_HASHES.json', 'files': files}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'required_files': len(required), 'matrix_rows': len(rows), 'sealed_files': len(files), 'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'passed': True}), flush=True)
