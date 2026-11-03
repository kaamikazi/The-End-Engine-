"""Read-only historical evidence inspection for independent v2 review.
No runtime import or source/test/evidence mutation. Creates NEW review receipt only.
"""
import csv, hashlib, json
from pathlib import Path

OUT=Path(__file__).resolve().parent
V2=Path('E:/END-v102-WIP-Checkpoint-20261019/experimental_architectures_v1_r3/validation/contract_reconciliation_v2')
PRIOR=Path('E:/The End Engine/contract_adjudication_v102_20261019')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
rows=list(csv.DictReader((V2/'R1_SIXTEEN_CASE_MATRIX.csv').open(encoding='utf-8-sig',newline='')))
old=read(PRIOR/'probes/REVIEWER_OWNED_RESULTS.json')
reported={r['id']:r for r in old['rows']}
observations=[]
for row in rows:
    name=row['CASE']; d=Path('E:/The End Engine/ca102/own')/('ACCOUNT_'+name)
    records={}
    for a in json.loads(row['SUPPORTING_ANCHORS']):
        p=d/a['path']
        records[a['path']]={'exists':p.is_file(),'sha256':sha(p) if p.is_file() else None,'matrix_sha256':a['sha256'],'matches_matrix':p.is_file() and sha(p)==a['sha256']}
    identity=read(d/'publication/IDENTITY.json')
    identity_sha=sha(d/'publication/IDENTITY.json')
    reservation=read(d/'publication/attempts/000001.reservation.json')
    dispatch=read(d/'publication/attempts/000001.json')
    settlement=read(d/'publication/attempts/000001.settlement.json')
    ledger=read(d/'budget.json')['state']['attempts']
    own=[a for a in ledger if a['run_id']==identity['run_id']]
    receipt=d/'publication/attempts/000001.response.json'
    rd_ids=[v['attempt_id'] for v in (reservation,dispatch)]
    orig=reported['ACCOUNT_'+name]['outcome']
    observations.append({'case':name,'fixture_path':str(d),'anchors':records,
        'identity_sha256':identity_sha,
        'run_identity_match':all(v['run_id']==identity['run_id'] and v['identity_sha256']==identity_sha for v in (reservation,dispatch,settlement)),
        'reservation_dispatch_ids':rd_ids,'own_ledger_ids':[a['attempt_id'] for a in own],
        'reservation_fields_equal':all(reservation['reservation'][k]==own[0][k] for k in ('attempt_id','run_id','purpose','token_ceiling','seconds_ceiling','started_unix')),
        'settlement_equals_current_row':settlement['settlement']==own[0],
        'dispatch_commitment_matches':settlement['dispatch_anchor_sha256']==sha(d/'publication/attempts/000001.json'),
        'registered_response_exists':receipt.is_file(),
        'response_commitment_matches':receipt.is_file() and settlement['response_anchor_sha256']==sha(receipt),
        'recorded_settlement_usage':{k:settlement['settlement'][k] for k in ('input_tokens','output_tokens','total_tokens')},
        'historical_reviewer_graph':orig['graph'],'historical_reviewer_journal_overall':orig['journal']['overall'],
        'historical_reviewer_status':reported['ACCOUNT_'+name]['status'],
        'historical_no_replay':orig['new_dispatches']==[],
        'historical_inputs_preserved':orig['immutable_inputs'],
        'current_fixture_result_exists':(d/'RESULT.json').exists(),
        'evidence_origin':'Prior fresh-AI reviewer controlled mock fixture; current hash match establishes byte continuity only. Not new execution, provider attestation, hostile-host authenticity or whole-run completeness.'})
manifest=read(V2/'PROPOSAL_FILE_HASHES.json')
receipt={'scope':'Read-only current-byte comparison to specified prior controlled mock evidence; no runtime/proposed adapter executed',
    'proposal_hashes':{n:{'expected':v,'actual':sha(V2/n),'match':v==sha(V2/n)} for n,v in manifest['files'].items()},
    'cases':observations,
    'counts':{'cases':len(observations),'matrix_anchor_entries':sum(len(r['anchors']) for r in observations),
              'matrix_anchor_matches':sum(x['matches_matrix'] for r in observations for x in r['anchors'].values()),
              'settlement_equal':sum(r['settlement_equals_current_row'] for r in observations),
              'response_commitment_matches':sum(r['response_commitment_matches'] for r in observations)},
    'limitations':['Historical fixture hashes do not authenticate historical origin','Saved historical assertions are inspected, not freshly executed by this script','Copied evidence is path-bound forensic evidence; not a relocatable normal certificate']}
p=OUT/'REVIEWER_HISTORICAL_EVIDENCE_INSPECTION.json'
with p.open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(receipt['counts']))
