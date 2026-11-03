"""Compare preserved JSON state and copy unchanged scoring bytes; no experiments."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;A=Path('E:/The End Engine/v21_A0_feasibility');copy=A/'runs/attempt_002/A0-18/copy'
ledger=json.loads((copy/'budget.json').read_text(encoding='utf-8'));pending=json.loads((copy/'budget.json.pending').read_text(encoding='utf-8'));a=ledger['state'];b=pending['state']
delta={'added_run_keys':sorted(set(b['runs'])-set(a['runs'])),'removed_run_keys':sorted(set(a['runs'])-set(b['runs'])),'existing_run_contracts_changed':[k for k in a['runs'] if a['runs'][k]!=b['runs'].get(k)],'other_state_fields_changed':[k for k in set(a)|set(b) if k!='runs' and a.get(k)!=b.get(k)],'attempt_arrays_identical':a['attempts']==b['attempts'],'attempt_row_count':len(a['attempts']),'ledger_state_sha256_field':ledger['state_sha256'],'pending_state_sha256_field':pending['state_sha256'],'method':'Read-only comparison of already-preserved raw files, not a new mutation test'}
assert delta['added_run_keys']==['A0_UNENROLLED_REGISTER'] and not delta['removed_run_keys'] and not delta['existing_run_contracts_changed'] and not delta['other_state_fields_changed'] and delta['attempt_arrays_identical']
(H/'STATE_DELTA.json').write_text(json.dumps(delta,indent=2)+'\n',encoding='utf-8')
source=A/'scoring_clarification_20261021/A0_NEGATIVE_CONTROL_SCORING.json';data=source.read_bytes();scores=json.loads(data);required=['observed_event','expected_event','elapsed_time','bound_satisfied','control_verdict','feasibility_implication'];assert all(all(k in x for k in required) for x in scores['records']) and len(scores['records'])==4
dest=H/'NEGATIVE_SCORING_VERBATIM.json';dest.write_bytes(data)
(H/'NEGATIVE_SCORING_COPY_RECEIPT.json').write_text(json.dumps({'original':str(source),'verbatim_copy':str(dest),'sha256':hashlib.sha256(data).hexdigest(),'records':4,'required_six_fields':required,'source_bytes_modified':False,'control_statuses_modified':False,'new_tests':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps(delta))
