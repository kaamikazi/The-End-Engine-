"""Check plan identities, exact requirements and preservation. No runtime tests."""
import ast,csv,hashlib,json,re,subprocess,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent;V=Path('E:/The End Engine/v21_contract_acceptance_review');W=Path('E:/END-v102-V21-Contract-Checkpoint');R=Path('E:/END-Cognitive-Architectures-Fix-v102')
required=['IMPLEMENTATION_MASTERPLAN.md','IP01_IP09_TRACEABILITY.csv','WRITER_DOMAIN_INVENTORY.csv','LOCK_ORDER_AND_DEADLOCK_ANALYSIS.md','R1_CAPTURE_DESIGN.md','R1_OBSERVATION_EXTRACTION.md','R3_VALIDATOR_AND_ADAPTER_DESIGN.md','R4_CALLER_COMPATIBILITY.md','R5_CR2_TEST_PLAN.md','PHASED_IMPLEMENTATION_ROADMAP.md','RESOURCE_AND_RISK_ESTIMATE.md','SOURCE_PRESERVATION.json','OPEN_ENGINEERING_RISKS.md','FIRST_IMPLEMENTATION_SLICE.md','FINAL_PLANNING_REPORT.md']
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(root),'-c','safe.directory='+root.as_posix(),*a],text=True).strip()
checks=[]
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
 if not condition:raise AssertionError(name)
result={'scope':'Planning document and mechanical source-preservation validation, NOT implementation tests','implementation_tests_executed':0,'historical_suites_rerun':False,'checks':checks}
try:
 check('all15 required deliverables present and nonempty',all((P/n).is_file() and (P/n).stat().st_size for n in required))
 trace=rows(P/'IP01_IP09_TRACEABILITY.csv');exact={}
 for line in (V/'IMPLEMENTATION_PREREQUISITES.md').read_text(encoding='utf-8').splitlines():
  if re.match(r'\| IP0[1-9] \|',line):a=[x.strip() for x in line.split('|')];exact[a[1]]=a[3]
 check('nine exact unrenamed requirements, verbatim',len(trace)==9 and {r['ID']:r['exact_requirement'] for r in trace}==exact)
 check('every prerequisite has all required planning fields',all(all(v.strip() for v in r.values()) for r in trace))
 allowed={'EXISTING_AND_VERIFIED','PARTIALLY_IMPLEMENTED','NOT_IMPLEMENTED','UNKNOWN','BLOCKED_BY_DEPENDENCY'}
 check('only requested status labels; no gate falsely complete',all(r['status'] in allowed and r['status']!='EXISTING_AND_VERIFIED' for r in trace))
 writers=rows(P/'WRITER_DOMAIN_INVENTORY.csv');idx={(r['path'],r['symbol']):r['line'] for r in json.loads((H/'SOURCE_SYMBOLS.json').read_text(encoding='utf-8'))}
 check('41 identified writer or actor rows, complete fields',len(writers)==41 and all(all(v.strip() for v in r.values()) for r in writers))
 for r in writers[:-1]:
  match=re.fullmatch(r'(.+):(\d+) (.+)',r['entry_point']);check('actual writer symbol '+r['writer_id'],match is not None and idx.get((match[1],match[3]))==int(match[2]))
 check('external actor explicitly UNKNOWN, not guessed function',writers[-1]['role']=='UNKNOWN_EXTERNAL_ACTOR')
 old=rows(Path('E:/The End Engine/v2_contract_acceptance_review_20261020/review/V2_31_TEST_COVERAGE_MATRIX.csv'));mapped=rows(H/'CR2_HISTORICAL_MAPPING.csv')
 check('31 unique original outcomes mapped without dropping IDs',len(mapped)==31 and {r['original_test_id'] for r in mapped}=={r['OLD_TEST_ID'] for r in old})
 byid={r['OLD_TEST_ID']:r for r in old}
 check('original assertions, mutations, scientific intent and statuses unchanged',all(all(r[a]==byid[r['original_test_id']][b] for a,b in [('original_assertion_VERBATIM','ORIGINAL_ASSERTION'),('original_mutation_VERBATIM','ORIGINAL_MUTATION'),('original_invariant_VERBATIM','ORIGINAL_SCIENTIFIC_INTENT'),('historical_status','HISTORICAL_STATUS')]) for r in mapped))
 check('all future CR2 paths outside historical tests discovery',all(r['future_file']=='experimental_architectures_v1_r3/cr2_v21_tests/test_historical_contracts.py' for r in mapped))
 cases=rows(H/'R1_SIXTEEN_EXECUTABLE_PREDICATE_PLAN.csv');st=json.loads((H/'STATIC_INSPECTION.json').read_text(encoding='utf-8'))
 check('16 exact cases and63 retained refs; conditional14 and2 limits',len(cases)==16 and sum(len(json.loads(r['exact_retained_refs'])) for r in cases)==63 and len([r for r in cases if r['strong_case_expected'].startswith('A:')])==14)
 scen=rows(H/'CR2_SNAPSHOT_SCENARIO_PLAN.csv');dg=rows(H/'R1_APPROVED_DOWNGRADE_TRACE.csv')
 check('20 approved snapshot scenarios and15 downgrade rows retained',len(scen)==20 and len(dg)==15)
 check('17 fault-free counterparts plus3 already-positive primaries, no duplicated budget',sum('already positive' in r['planned_positive_counterpart'] for r in scen)==3)
 check('87field rows and14normative semantic rules inspected',len(st['contract_csvs']['R3_NORMATIVE_FIELD_MATRIX.csv']['records'])==87 and len(st['semantic_rules'])==14)
 check('all14semantic IDs explicitly planned',all('| '+r['id']+' |' in (P/'R3_VALIDATOR_AND_ADAPTER_DESIGN.md').read_text(encoding='utf-8') for r in st['semantic_rules']))
 seams=[r['test'].split('.')[-1] for r in json.loads((H/'TEST_SYMBOLS.json').read_text(encoding='utf-8')) if r['path']=='experimental_architectures_v1_r3/tests/corrections/test_publication_guard.py']
 check('all13actual publication seam test names retained',len(seams)==13 and all(n in (P/'R5_CR2_TEST_PLAN.md').read_text(encoding='utf-8') for n in seams))
 doc='\n'.join((P/n).read_text(encoding='utf-8') for n in required if n.endswith('.md'))
 check('canonical new CR2 namespace; no stale draft path', 'tests/cr2_v21/' not in doc)
 check('A0 exactly20named vectors and explicit nonauthorization',len(re.findall(r'\| A0-\d\d \|',(P/'FIRST_IMPLEMENTATION_SLICE.md').read_text(encoding='utf-8')))==20 and 'NOT AUTHORIZED' in (P/'FIRST_IMPLEMENTATION_SLICE.md').read_text(encoding='utf-8'))
 check('no proposed production package or test migration created',not (W/'experimental_architectures_v1_r3/src/observation_v21').exists() and not (R/'experimental_architectures_v1_r3/src/observation_v21').exists() and not (W/'experimental_architectures_v1_r3/cr2_v21_tests').exists())
 preservation=json.loads((P/'SOURCE_PRESERVATION.json').read_text(encoding='utf-8'));check('full protected hash/Git comparison passed',preservation['passed'])
 before=json.loads((H/'BEFORE.json').read_text(encoding='utf-8'));membership={}
 for label,root,expected in [('approved_checkpoint',W,set(before['v21_checkpoint'])),('original_correction',R,set(before['correction'])|set(before['original_v21'])),('approved_review',V,set(before['approved_review']))]:
  actual={str(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts};membership[label]={'files':len(actual),'added':sorted(actual-expected),'removed':sorted(expected-actual)}
  check('complete final file membership '+label,actual==expected)
 initial=json.loads((H/'IDENTITY.json').read_text(encoding='utf-8'))
 for label in ['approved_checkpoint','original_correction','prior_WIP']:
  entry=initial[label];root=Path(entry['root']);check('final Git state '+label,git(root,'rev-parse','HEAD')==entry['HEAD'] and git(root,'branch','--show-current')==entry['branch'] and git(root,'status','--porcelain=v1')==entry['status'] and git(root,'diff','--cached','--name-status')==entry['staged'])
 (H/'FINAL_MEMBERSHIP_CHECK.json').write_text(json.dumps(membership,indent=2)+'\n')
 preservation['complete_final_membership_check']='_evidence/FINAL_MEMBERSHIP_CHECK.json';(P/'SOURCE_PRESERVATION.json').write_text(json.dumps(preservation,indent=2)+'\n')
 result.update(passed=True,required_deliverables=15,IP_requirements=9,writer_actor_entries=41,actual_source_writer_symbols=40,historical_outcomes=31,historical_case_predicates=16,snapshot_scenarios=20,downgrade_rows=15,preserved_native_seams=13,semantic_rule_plans=14,planning_verdict='IMPLEMENTATION_PLAN_READY_FOR_REVIEW')
except Exception as e:
 result.update(passed=False,error=type(e).__name__+': '+str(e),traceback=traceback.format_exc())
attempt=1
while (H/('planning_validation_attempt_'+str(attempt).zfill(2)+'.json')).exists():attempt+=1
attempt_path=H/('planning_validation_attempt_'+str(attempt).zfill(2)+'.json');attempt_path.write_text(json.dumps(result,indent=2)+'\n')
result['preserved_attempt_receipt']=attempt_path.name
(H/'PLANNING_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','traceback']}))
if not result['passed']:raise SystemExit(1)
manifest={p.relative_to(P).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in P.rglob('*') if p.is_file() and p.name!='PLAN_FILE_HASHES.json'}
(H/'PLAN_FILE_HASHES.json').write_text(json.dumps({'files':manifest,'scope':'Local planning artifacts only; no publication or implementation acceptance'},indent=2)+'\n')
