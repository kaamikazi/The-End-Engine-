"""Render independent decisions; reads inputs, writes only NEW review CSVs."""
import csv,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
V2=Path('E:/END-v102-WIP-Checkpoint-20261019/experimental_architectures_v1_r3/validation/contract_reconciliation_v2')
PRIOR=Path('E:/The End Engine/contract_adjudication_v102_20261019')
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def emit(name,items):
    with (OUT/name).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
case_reasons={
'changed_wire':'Mutated request bytes cannot match dispatch commitment; original reservation/dispatch/settlement/response identity remains [1].',
'changed_wire_digest':'Changed journal digest does not change the separately retained dispatch/settlement graph identity.',
'changed_decoded_response':'Tail decoded text disagrees with original bytes; original settlement and response commitment remain separately bound.',
'invalid_base64':'Raw bytes cannot be decoded from damaged tail, but recorded settlement/response anchor still support one anchored identity.',
'changed_response_digest':'Altered tail digest cannot override independently retained original response commitment and settlement.',
'missing_settled_journal':'Registered journal absence prevents wire certification; intact independent graph still identifies the original reservation once.',
'duplicate_attempt_file':'Copied journal adds no independently reserved ID; graph set is [1], not two provider events.',
'duplicate_response_record':'Third response record corrupts wire chain but does not add an independently reserved/settled identity.',
'wrong_stage':'Wrong damaged header stage cannot relabel independently bound INITIAL reservation/dispatch and settled handle.',
'wrong_run':'Foreign damaged header run cannot reassign the separately run-bound original reservation and dispatch.',
'wrong_attempt':'Header attempt999 is not a new independent reservation; original anchored ID remains1.',
'incorrect_record_order':'Reversed wire records fail wire ordering; independent reservation/dispatch/settlement ordering remains one identity.',
'settled_torn_tail':'Settled torn append is not a benign unresolved attempt; independent complete graph retains one recorded identity.',
'ledger_disagreement':'Reservation/dispatch binding survives, but original settlement != current ledger response; refreshed checksum is not authority.',
'recomputed_hashes_still_fail_anchor':'Rehashed substituted wire cannot replace original dispatch/settlement commitment; independently retained graph remains one identity.',
'missing_response_anchor':'Reservation/dispatch survive; registered response path missing despite retained renamed bytes. No silent repair/full graph claim.'}
ins=json.loads((OUT/'REVIEWER_HISTORICAL_EVIDENCE_INSPECTION.json').read_bytes())
ins={r['case']:r for r in ins['cases']}
items=[]
for r in rows(V2/'R1_SIXTEEN_CASE_MATRIX.csv'):
    n=r['CASE'];e=ins[n];coherent=r['GRAPH_DISPOSITION']=='COHERENT'
    items.append({'CASE':n,'HISTORICAL_TEST_ID':r['HISTORICAL_TEST_ID'],'EXACT_MUTATION':r['EXACT_MUTATION'],
    'INDIVIDUAL_DECISION':'ACCEPT_WITH_CONDITIONS','EVIDENCE_TARGET_SUPPORTED':True,
    'SUPPORTED_NUMERIC_OBSERVATION':1,'SUPPORTED_IDS':'[1]',
    'ACCEPTED_TIER':'INDEPENDENTLY_VERIFIED_ATTEMPT_CARDINALITY_WITHIN_VISIBLE_COHERENT_GRAPH' if coherent else 'CORROBORATED_RESERVATION_DISPATCH_IDENTITY_ONLY',
    'CASE_SPECIFIC_REASON':case_reasons[n],
    'MATRIX_ANCHOR_HASHES_MATCH':all(a['matches_matrix'] for a in e['anchors'].values()),
    'EXACT_ANCHORS':r['SUPPORTING_ANCHORS'],
    'SETTLEMENT_EQUALS_CURRENT_LEDGER':e['settlement_equals_current_row'],
    'RESPONSE_COMMITMENT_RESOLVES':e['response_commitment_matches'],
    'USAGE_OBSERVATION':'Recorded10/5/15 corroborated settlement metadata; current damaged raw receipt/wire not certified' if coherent else 'Original witness10/5/15 observation only; named current binding/content conflict',
    'COMPLETE_RUN_PHYSICAL_ATTEMPTS':'null / NOT_CERTIFIED','COMPLETE_RUN_USAGE':'null / UNKNOWN_OR_INCONSISTENT_COST',
    'COMPLETE_RUN_CERTIFICATION_PERMITTED':False,'CURRENT_V2_IMPLEMENTED':False,
    'MANDATORY_REMAINING_CONDITION':'R1-SNAPSHOT-01 stable identity/ledger/content/inventory snapshot and missing-witness downgrade; preserve raw evidence/no replay/no refund/no new normal RESULT/prepared; R3 exact envelope',
    'EVIDENCE_REFERENCE':str(Path(e['fixture_path']))+'; ../probes/V2_ADVERSARIAL_RESULTS.json#WITNESS_'+n+'; REVIEWER_HISTORICAL_EVIDENCE_INSPECTION.json',
    'ORIGIN_LIMITATION':'Controlled local writer mock evidence, not provider-authenticated inference or erased-event lifetime completeness',
    'HISTORICAL_OUTCOME':'FAIL_UNCHANGED'})
assert len(items)==16 and len({r['CASE'] for r in items})==16
emit('V2_R1_SIXTEEN_CASE_DECISIONS.csv',items)

old={r['OLD_TEST_ID']:r for r in rows(PRIOR/'review/END_CONTRACT_31_FAILURES.csv')}
classification={r['HISTORICAL_TEST_ID']:r for r in rows(V2/'FAILURE_CLASSIFICATION_V2.csv')}
replacement=rows(V2/'REPLACEMENT_TEST_MATRIX_V2.csv')
assert len(old)==len(classification)==len(replacement)==31
assert set(old)==set(classification)=={r['OLD_TEST_ID'] for r in replacement}
hist={r['test']:r['status'] for r in json.loads((PRIOR/'probes/CURRENT244.json').read_bytes())['records']}
others={
'test_torn_final_journal_append_recovers_without_dispatch':('Retains raw candidate/handle and no replay; valid intact-partial C0 counterpart preserves availability without unsafe selected BLOCKED result.','Require scoped count1 as well as candidate byte comparison, no FINAL/RESULT/prepared, no reset; exact torn input and intact C0 control.'),
'test_corrupt_journal_then_stale_finalization_cannot_replace_blocked_record':('Admit stale object before mutation so direct finalization is actually exercised; independent new-admission rejection plus valid immutable-result return preserve original intent.','Retain original complete bad-record fault, stale-before-mutation object, hold/diagnostic evidence/no replay and valid stale return with byte identity.'),
'test_serializer_fallback_does_not_conceal_journal_failure':('Reject BLOCKED before serializer fallback; still require finite canonical diagnostic and valid-history serialization fallback; unrelated errors remain visible.','Preserve NaN-note plus corrupt-journal conjunction, canonical diagnostic/no new certificate, and separate safe-provenance fallback and unrelated-exception propagation.'),
'test_simultaneous_finalizers_with_missing_journal_keep_failure_explicit':('Pre-admission rendezvous permits measuring rejected workers; original two processes and additional four-process stress plus valid publication retain exclusion/liveness.','Retain exact missing/moved journal, original2processes and4process vectors, all outcomes/joins/dispatches/bytes, no final/prepared and valid counterpart.'),
'test_W_torn_journal_remains_diagnosable':('Typed direct rejection plus grounded orchestration diagnostic preserves diagnosability and raw torn settled history without certification.','Exact settled torn input, typed direct hold, execute diagnostic, unchanged bytes, no replay/reset/new normal certificate; valid recovery counterpart.'),
'test_corrupt_journal_finalization_remains_blocked':('Direct finish is not a normal BLOCKED-result producer; paired execute diagnostic preserves explicit failure/evidence.','Exact original corrupt suffix, grounded direct/execute paths, no replay/no normal final/prepared and valid finalization.'),
'FINAL_JOURNAL_HASH_MISMATCH':('Direct completed verifier must reject while existing final remains immutable; orchestration diagnostic is a bounded versioned exception/return distinction.','Retain exact final journal mutation and old RESULT/prepared/ledger/wire hashes, direct rejection, no certified old return/replay and valid completion counterpart.')}
items=[]
for r in replacement:
    n=r['OLD_TEST_ID'];p=old[n];c=classification[n]
    if 'JournalIntegrityTests.test_' in n:
        case=n.rsplit('test_',1)[1]
        reason=case_reasons[case]+' Mandatory scoped numeric availability preserves the old separable accounting property.'
        cond='Exact original mutator, scoped value1/IDs/63-entry case anchors at correct14/2 tier; failed dimensions, no new certificate/replay/reset and all post-mutation bytes preserved; resolve R1 snapshot and R3 schema.'
        status='FAIL'
    elif n.startswith('RACE_'):
        i=int(n.rsplit('_',1)[1]);vec=[(0,0,0,0),(0,.015,.03,.045),(.045,.03,.015,0),(.02,0,.04,.01)][i]
        reason='Retains four actual OS workers and vector '+str(vec)+' with pre-admission synchronization; rejected corrupt admission no longer pretends to contend for normal publication. Paired valid history proves liveness/exclusivity.'
        cond='Exact complete-extraJSON fault' if 'journal-corrupt' in n else 'Exact moved registered response receipt and preserved bytes'
        cond+='; four processes/vector'+str(vec)+'; inspect every PID/exit/outcome, joins, no replay/no new normal prepared/final and input hashes; paired valid C0/handle publication, stale/existing-completion and F01 crash/fence/pin prerequisites.'
        status='FAIL'
    else:
        reason,cond=others[n.rsplit('.',1)[-1]];status=hist.get(n,'FAIL')
    items.append({'OLD_TEST_ID':n,'ORIGINAL_SOURCE_REFERENCE':p['ORIGINAL_SOURCE'],
        'ORIGINAL_ASSERTION':p['ORIGINAL_ASSERTION'],'ORIGINAL_MUTATION':p['ORIGINAL_MUTATION'],
        'ORIGINAL_SCIENTIFIC_INTENT':p['ORIGINAL_INTENT'],
        'PREVIOUS_INDEPENDENT_CLASSIFICATION':p['REVIEW_FINDING'],
        'V2_AUTHOR_CLASSIFICATION':c['INDEPENDENT_REVIEWER_CLASSIFICATION'],
        'THIS_REVIEW_CLASSIFICATION':p['REVIEW_FINDING'],
        'PROPOSED_NEW_TEST_ID':r['PROPOSED_NEW_TEST_ID'],'PROPOSED_NEW_ASSERTION':r['NEW_ASSERTION'],
        'PROPERTY_PRESERVATION_DECISION':'ACCEPT_WITH_CONDITIONS',
        'INDEPENDENT_REASON':reason,'REQUIRED_COVERAGE_AND_CONDITIONS':cond,
        'UNRESOLVED_DESIGN_DEPENDENCIES':'R1-SNAPSHOT-01/R1-WITNESS-02 and R3-UNION-01/R3-FIELDS-02 where applicable; R4/R5 execution gates remain',
        'HISTORICAL_STATUS':status+'_UNCHANGED','OLD_ASSERTION_EDITED_OR_SKIPPED':False,
        'NEW_TEST_IMPLEMENTATION_OR_EXECUTION_ACCEPTED':False,
        'EVIDENCE_REFERENCE':'Prior unchanged244/154/49 and END_CONTRACT_31_FAILURES.csv; v2 exact row; fresh58 bounded controls (not31 migrated tests)'})
emit('V2_31_TEST_COVERAGE_MATRIX.csv',items)
print(json.dumps({'cases':16,'mappings':31,'historical_fail':sum(r['HISTORICAL_STATUS']=='FAIL_UNCHANGED' for r in items),'historical_error':sum(r['HISTORICAL_STATUS']=='ERROR_UNCHANGED' for r in items)}))
