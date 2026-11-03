"""Reviewer-only administrative audit; does not import or execute A0/runtime code."""
from pathlib import Path
import ast, base64, collections, ctypes, datetime, hashlib, json, platform, sys
from ctypes import wintypes as wt

ROOT = Path(__file__).resolve().parent.parent
A = Path('E:/The End Engine/v21_A0_feasibility')
B = Path('E:/The End Engine/v21_A0_collector_correction')
I = Path('E:/The End Engine/v21_A0_blocker_investigation')
RUN = ROOT / 'runs/independent_001'
CASE = RUN / 'A0-18'
FILES = ['README.md', 'probe_runner.py', 'probe_workers.py', 'test_lock_domain_feasibility.py', 'source_profile.json', 'result_schema.json']
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, x): p.write_text(json.dumps(x, indent=2, allow_nan=False) + '\n', encoding='utf-8')
def defs(p):
    source = p.read_text(encoding='utf-8')
    return {a.name: ast.get_source_segment(source, a) for a in ast.parse(source).body if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
def verify_manifest(root, manifest):
    entries = read(manifest)['files']
    return {'manifest': str(manifest), 'manifest_sha256': sha(manifest), 'entries': len(entries), 'mismatches': [n for n, v in entries.items() if not (root / n).is_file() or sha(root / n) != v['sha256']]}

original = A / 'runs/attempt_002/executed_scaffolding'
static = {'changed_files': [n for n in FILES if (original / n).read_bytes() != (ROOT / 'harness' / n).read_bytes()], 'six_file_hashes': {}, 'definition_changes': {}}
for n in FILES:
    static['six_file_hashes'][n] = {'historical': sha(original / n), 'corrected_author': sha(B / 'harness' / n), 'reviewer_copy': sha(ROOT / 'harness' / n), 'actually_executed_archive': sha(RUN / 'executed_harness' / n)}
for n in ['probe_workers.py', 'test_lock_domain_feasibility.py']:
    old, new = defs(original / n), defs(ROOT / 'harness' / n)
    static['definition_changes'][n] = {'added': sorted(set(new) - set(old)), 'removed': sorted(set(old) - set(new)), 'modified': sorted(k for k in old if k in new and old[k] != new[k])}
source_manifest = read(A / 'runs/attempt_002/EXECUTED_SOURCE_RECEIPT.json')['unchanged_implementation_sources']
static['source_manifest_entries'] = len(source_manifest)
static['source_manifest_mismatches'] = [n for n, v in source_manifest.items() if sha(A / 'checkout' / n) != v['sha256']]
static['recursive_scoring_unchanged'] = defs(original / 'test_lock_domain_feasibility.py')['recursive'] == defs(ROOT / 'harness/test_lock_domain_feasibility.py')['recursive']
static['driver_sha256'] = {'author': sha(B / '_control/targeted_rerun.py'), 'reviewer_exact_copy': sha(ROOT / '_control/targeted_rerun.py')}
static['saved_two_file_diffs_equal_independently_generated_diffs'] = {n: (RUN / (n + '.diff')).read_bytes() == (B / 'runs/attempt_001' / (n + '.diff')).read_bytes() for n in static['changed_files']}
static['preserved_evidence_manifest_checks'] = [verify_manifest(A, A / '_control/EVIDENCE_FILE_HASHES.json'), verify_manifest(I, I / '_evidence/INVESTIGATION_FILE_HASHES.json'), verify_manifest(B, B / '_control/EVIDENCE_FILE_HASHES.json')]

inventories = {}
for phase in ['PRE', 'POST']:
    p = CASE / (phase + '_NAMESPACE_INVENTORY.json')
    j = read(p)
    bad = []
    for e in j['entries'] + j['external_active_controls']:
        if e['read_status'] == 'BYTES_CAPTURED':
            raw = base64.b64decode(e['raw_base64'], validate=True)
            if hashlib.sha256(raw).hexdigest() != e['sha256'] or len(raw) != e['captured_bytes']: bad.append(e['path'])
    inventories[phase] = {'file_sha256': sha(p), 'entry_count': len(j['entries']), 'categories': dict(collections.Counter(e['category'] for e in j['entries'])), 'required_read_failures': j['required_read_failures'], 'collection_complete_for_declared_A0_policy': j['collection_complete_for_declared_A0_policy'], 'raw_digest_or_size_mismatches': bad, 'active_controls': [{k: e.get(k) for k in ['path', 'relative_path', 'category', 'read_status', 'sha256', 'raw_base64', 'identity', 'descriptor_is_owned']} for e in j['entries'] + j['external_active_controls'] if e.get('active')]}
pre, post = read(CASE / 'PRE_NAMESPACE_INVENTORY.json'), read(CASE / 'POST_NAMESPACE_INVENTORY.json')
pre_paths = {e['relative_path'] for e in pre['entries']}
post_paths = {e['relative_path'] for e in post['entries']}
actual_paths = {p.relative_to(CASE / 'copy').as_posix() for p in (CASE / 'copy').rglob('*')}
inventories['post_membership_omissions'] = sorted(actual_paths - post_paths)
inventories['post_membership_extra_claims'] = sorted(post_paths - actual_paths)
inventories['added_members'] = sorted(post_paths - pre_paths)
inventories['removed_members'] = sorted(pre_paths - post_paths)
inventories['captured_file_vs_actual_mismatches'] = [e['relative_path'] for e in post['entries'] if e['read_status'] == 'BYTES_CAPTURED' and sha(CASE / 'copy' / e['relative_path']) != e['sha256']]
pending = read(CASE / 'copy/budget.json.pending')
ledger = read(CASE / 'copy/budget.json')
canonical = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
mutation = read(CASE / 'PENDING_MUTATION_RECEIPT.json')
mutation['independently_recomputed'] = {'pending_sha256': sha(CASE / 'copy/budget.json.pending'), 'main_ledger_sha256': sha(CASE / 'copy/budget.json'), 'pending_envelope_checksum_valid': hashlib.sha256(canonical(pending['state'])).hexdigest() == pending['state_sha256'], 'main_envelope_checksum_valid': hashlib.sha256(canonical(ledger['state'])).hexdigest() == ledger['state_sha256'], 'foreign_registration_in_pending_only': 'A0_UNENROLLED_REGISTER' in pending['state']['runs'] and 'A0_UNENROLLED_REGISTER' not in ledger['state']['runs'], 'attempt_arrays_identical': pending['state']['attempts'] == ledger['state']['attempts'], 'attempt_rows': len(ledger['state']['attempts'])}

kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetVolumeInformationW.argtypes = [wt.LPCWSTR, wt.LPWSTR, wt.DWORD, ctypes.POINTER(wt.DWORD), ctypes.POINTER(wt.DWORD), ctypes.POINTER(wt.DWORD), wt.LPWSTR, wt.DWORD]
kernel.GetVolumeInformationW.restype = wt.BOOL
vol, fs = ctypes.create_unicode_buffer(261), ctypes.create_unicode_buffer(261)
serial, maximum, flags = wt.DWORD(), wt.DWORD(), wt.DWORD()
volume_root = ROOT.drive + '\\'
if not kernel.GetVolumeInformationW(volume_root, vol, len(vol), ctypes.byref(serial), ctypes.byref(maximum), ctypes.byref(flags), fs, len(fs)): raise ctypes.WinError(ctypes.get_last_error())
environment = {'python': sys.version, 'python_executable': sys.executable, 'platform': platform.platform(), 'volume': volume_root, 'filesystem': fs.value, 'volume_serial': format(serial.value, '08x'), 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
historical = read(A / 'runs/attempt_002/RUN_RESULT.json')
author = read(B / 'runs/attempt_001/TARGETED_RESULT.json')
targeted = read(RUN / 'TARGETED_RESULT.json')
child = read(CASE / 'CHILD_COLLECTION_RECEIPT.json')
resource = read(CASE / 'RESOURCE_RELEASE_RECEIPT.json')
raw_audit = {'scope': 'READ_ONLY_ADMINISTRATIVE_AUDIT_NOT_AN_ADDITIONAL_A0_CONTROL', 'static': static, 'independent_inventories': inventories, 'independent_mutation': mutation, 'resource_release': resource, 'environment': environment, 'independent_targeted_result_sha256': sha(RUN / 'TARGETED_RESULT.json')}
save(ROOT / '_control/INDEPENDENT_EVIDENCE_AUDIT.json', raw_audit)
checks = {
    'narrow_two_file_diff': static['changed_files'] == ['probe_workers.py', 'test_lock_domain_feasibility.py'] and static['definition_changes']['probe_workers.py'] == {'added': ['collect_a018_namespace'], 'removed': [], 'modified': []} and static['definition_changes']['test_lock_domain_feasibility.py'] == {'added': [], 'removed': [], 'modified': ['case18']},
    'exact_harness_and_driver_copies': all(len(set(v[k] for k in ['corrected_author', 'reviewer_copy', 'actually_executed_archive'])) == 1 for v in static['six_file_hashes'].values()) and len(set(static['driver_sha256'].values())) == 1,
    'source_hashes_and_saved_evidence_match_manifests': not static['source_manifest_mismatches'] and all(not m['mismatches'] for m in static['preserved_evidence_manifest_checks']),
    'operational_controls_explicit_and_active_visible': len(inventories['POST']['active_controls']) == 3 and all(e['category'] == 'A_OPERATIONAL_CONTROL' and e['read_status'] == 'NOT_READ_ACTIVE_LOCK_CONTROL' and e['sha256'] is None and e['raw_base64'] is None and e['descriptor_is_owned'] for e in inventories['POST']['active_controls']),
    'pending_fully_captured': mutation['pending_entry']['category'] == 'C_PENDING_TEMPORARY_EVIDENCE' and mutation['pending_entry']['read_status'] == 'BYTES_CAPTURED' and inventories['added_members'] == ['budget.json.pending'],
    'unknown_members_visible_without_coverage_promotion': inventories['POST']['categories']['D_UNKNOWN_UNEXPECTED_MEMBER'] == 12 and not inventories['post_membership_omissions'] and not inventories['post_membership_extra_claims'],
    'main_ledger_bytes_unchanged': mutation['main_ledger_sha256'] == child['worker_result']['events'][1]['ledger_before'] == child['worker_result']['events'][1]['ledger_after'] == mutation['independently_recomputed']['main_ledger_sha256'],
    'foreign_registration_recorded': mutation['independently_recomputed']['foreign_registration_in_pending_only'] and mutation['independently_recomputed']['attempt_arrays_identical'],
    'no_fabricated_captured_hashes': all(not inventories[q]['raw_digest_or_size_mismatches'] for q in ['PRE', 'POST']) and not inventories['captured_file_vs_actual_mismatches'],
    'native_handles_released_on_observed_path': resource['owned_guard_fds_closed'] and resource['pin_handles_closed'] and len(resource['guard_reacquisitions']) == 3 and len(resource['write_delete_access_checks']) == 22,
    'no_provider_or_reservation_calls_observed': not any(targeted['parent_tripwire_counters'].values()) and not any(child['worker_result']['counters'].values()),
    'independent_exact_negative_pass': targeted['status'] == 'PASS' and targeted['executed_controls'] == 1 and read(ROOT / '_control/COMMAND_EXIT.json')['observed_exit_code'] == 0 and child['exit_code'] == 0 and child['worker_result']['events'][0]['winerror'] == 5,
    'strong_authority_not_awarded': targeted['strong_profile_supported'] is False and targeted['A_or_S_awarded'] is False and targeted['material_blocker'] is True,
    'ntfs_native_environment': environment['filesystem'] == 'NTFS',
}
result = {'collector_verdict': 'A0_COLLECTOR_INDEPENDENTLY_ACCEPTED' if all(checks.values()) else 'A0_COLLECTOR_REVIEW_FAILED', 'reviewer_role': 'Fresh independent context separate from correction author; no correction implementation written by this reviewer', 'scope': 'Exact corrected A0-18 negative evidence collector only; no runtime/strong-profile acceptance', 'source_commit': '783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e', 'historical_A0': {'counts': dict(collections.Counter(r['status'] for r in historical['rows'])), 'saved_historical_report_driver_exit': 1, 'retained_A0_18_status': 'ERROR', 'source': str(A / 'runs/attempt_002/RUN_RESULT.json')}, 'corrected_author_owned': {'counts': {author['status']: author['executed_controls']}, 'recorded_driver_exit': read(B / '_control/EXACT_COMMAND.json')['observed_exit_code'], 'source': str(B / 'runs/attempt_001/TARGETED_RESULT.json')}, 'independent_reviewer': {'counts': {targeted['status']: 1, 'FAIL': 0, 'ERROR': 0}, 'executed_controls': targeted['executed_controls'], 'requested_vector_ids': ['A0-18'], 'actual_driver_exit': read(ROOT / '_control/COMMAND_EXIT.json')['observed_exit_code'], 'child_exit': child['exit_code'], 'child_pid': child['pid'], 'writer_operation': child['worker_result']['events'][0], 'elapsed_seconds': targeted['elapsed_seconds'], 'parent_tripwires': targeted['parent_tripwire_counters'], 'child_tripwires': child['worker_result']['counters'], 'new_provider_calls': 0, 'new_reserved_attempts': 0, 'attempts_preserved_from_fixture': 1, 'strong_profile_supported': False, 'A_or_S_awarded': False, 'material_blocker': True}, 'checks': checks, 'failed_checks': [k for k,v in checks.items() if not v], 'inventory_summary': inventories, 'mutation_summary': mutation['independently_recomputed'], 'resource_release': resource, 'static_review': static, 'environment': environment, 'provider_zero_basis': 'Exact reviewed driver/case18/child contain no inference path; parent and child network/dispatch/reservation tripwires are zero. Copied fixture evidence is not a new provider event or authenticated provider origin.', 'preservation_bound': 'All source/evidence remain read only to this reviewer; saved source and three evidence manifests independently match. Broad fresh before/after membership, byte and Git preservation is owned separately by the coordinating reviewer in PRESERVATION.json.', 'limits': ['No full A0 runner executed.', 'One independent execution; no code repair or rerun to green.', 'No new arbitrary unknown-member, unreadable-file, reparse, or forced cleanup-error injection was authorized or executed.', 'Release demonstrated for the observed completed path only; no universal handle-leak proof.', 'Non-atomic namespace inventory is A0 evidence; it is not a common membership/content cut.', 'Active lock bytes intentionally not read and not hashed while held.', 'No production observer, A1 enrollment, live inference, benchmark or scientific performance claim.'], 'raw_evidence': {'audit': str(ROOT / '_control/INDEPENDENT_EVIDENCE_AUDIT.json'), 'copy_receipt': str(ROOT / '_control/COPY_RECEIPT.json'), 'command': str(ROOT / '_control/EXACT_COMMAND.json'), 'exit': str(ROOT / '_control/COMMAND_EXIT.json'), 'stdout': str(ROOT / '_control/TARGETED_STDOUT.txt'), 'stderr': str(ROOT / '_control/TARGETED_STDERR.txt'), 'result': str(RUN / 'TARGETED_RESULT.json')}}
save(ROOT / 'COLLECTOR_RETEST_RESULTS.json', result)
print(json.dumps({'collector_verdict': result['collector_verdict'], 'failed_checks': result['failed_checks'], 'historical': result['historical_A0']['counts'], 'author': result['corrected_author_owned']['counts'], 'independent': result['independent_reviewer']['counts'], 'environment': environment}))
