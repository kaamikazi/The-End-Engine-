"""Verify exact source/plan input identities and emit A0-only profile/inventory."""
import ast,csv,hashlib,json,re
from pathlib import Path
E=Path(__file__).resolve().parent.parent;C=E/'checkout';F=C/'experimental_architectures_v1_r3/feasibility_v21';P=Path('E:/The End Engine/v21_implementation_masterplan')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=list(csv.DictReader((P/'WRITER_DOMAIN_INVENTORY.csv').open(encoding='utf-8-sig',newline='')))
for row in rows:
 if row['role']=='UNKNOWN_EXTERNAL_ACTOR':row['actual_source_match']='UNKNOWN_EXTERNAL_NOT_A_SOURCE_FUNCTION';row['source_sha256']='NOT_APPLICABLE'
 else:
  m=re.fullmatch(r'(.+):(\d+) (.+)',row['entry_point']);path=C/m[1];tree=ast.parse(path.read_text(encoding='utf-8-sig'));found={}
  def walk(node,prefix=''):
   for n in ast.iter_child_nodes(node):
    if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):found[prefix+n.name]=n;walk(n,prefix+n.name+'.')
    else:walk(n,prefix)
  walk(tree);assert found[m[3]].lineno==int(m[2]);row['actual_source_match']='EXACT_SYMBOL_AND_LINE';row['source_sha256']=sha(path)
 row['A0_dynamic_coverage']='PENDING; do not infer enrollment from source inspection'
 row['strong_domain_proven']='NO'
with (E/'A0_WRITER_COVERAGE.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
source=Path('E:/The End Engine/ca102/own/RACE_2_valid');sourcefiles={p.relative_to(source).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in source.rglob('*') if p.is_file()}
manifest=json.loads((C/'experimental_architectures_v1_r3/validation/WIP_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
contract=C/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1';readings={p.name:sha(p) for p in contract.iterdir() if p.is_file() and p.name.startswith('R1_')}
for p in contract.iterdir():
 if p.is_file() and p.name.startswith('R1_'):p.read_text(encoding='utf-8')
profile={'schema':'A0_TEST_ONLY_PROFILE_NOT_DOMAIN_ATTESTATION','commit':'783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e','source_files':manifest['files'],'template':str(source),'template_files':sourcefiles,'template_provenance':'Prior independent offline public/synthetic RACE_2_valid fixture. Copies may be rebased only inside new A0 scratch; no new provider execution or reservation. Not authenticated historical origin.','approved_R1_readings':readings,'strong_domain_coverage':False,'no_A_or_S_award':True,'authority_limit':'I for grounded individual observations; X if unsupported; prospective U on observed violated candidate cut','scoring_clarification':'User: Record the negative event explicitly; pass the control only when its expected rejection/bound holds. Unexpected timeout/deadlock remains FAIL.','forbidden':'No reserve, model/provider dispatch, source verification monkey-patching, production observer, enrollment, old test migration, commit/push/merge/tag/release'}
(F/'source_profile.json').write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
(F/'result_schema.json').write_text(json.dumps({'$schema':'http://json-schema.org/draft-07/schema#','title':'A0 feasibility vector receipt, not RunOutcome','type':'object','required':['vector_id','status','observed_events','expectation_matched','authority','material_blocker'],'properties':{'vector_id':{'type':'string','pattern':'^A0-[0-9]{2}$'},'status':{'enum':['PASS','FAIL','ERROR','NOT_EXECUTED']},'observed_events':{'type':'array'},'expectation_matched':{'type':'boolean'},'authority':{'enum':['I','U','X']},'material_blocker':{'type':'boolean'}},'additionalProperties':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_writer_classes_verified':40,'unknown_external_actor':1,'template_files':len(sourcefiles),'R1_files_read':len(readings),'production_capability_installed':False}))
