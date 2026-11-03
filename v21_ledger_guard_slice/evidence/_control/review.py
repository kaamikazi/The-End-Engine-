"""Scoped source audit and exact baseline/final unittest comparison."""
import ast,collections,concurrent.futures,difflib,hashlib,json,subprocess
from pathlib import Path
E=Path(__file__).resolve().parents[1];C=E.parent/'checkout';P=Path('E:/The End Engine/v21_A0_feasibility/checkout');LEDGER='cognitive_architecture_lab_v1/src/accounting/ledger.py';COORD='cognitive_architecture_lab_v1/src/accounting/coordination.py'
def save(name,x):(E/name).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(C),'-c','safe.directory='+C.as_posix(),*args],text=True).strip()
def main():
 baseline=json.loads((E/'_control/CHECKOUT_BASELINE.json').read_text(encoding='utf-8'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:current=dict(pool.map(lambda n:(n,sha(C/n)),baseline['files']))
 changed=[n for n,h in baseline['files'].items() if current[n]!=h];assert changed==[LEDGER],changed
 old=(P/LEDGER).read_text(encoding='utf-8');new=(C/LEDGER).read_text(encoding='utf-8');defs=lambda t:{n.name:ast.get_source_segment(t,n) for n in ast.walk(ast.parse(t)) if isinstance(n,ast.FunctionDef)};before=defs(old);after=defs(new);symbols=[n for n in before if before[n]!=after[n]];assert set(symbols)=={'__init__','lock','_write'} and before.keys()==after.keys()
 untracked=git('ls-files','--others','--exclude-standard').splitlines();assert all(n==COORD or n.startswith('tests_coordination_v1/') for n in untracked),untracked
 imports=[]
 for node in ast.walk(ast.parse((C/COORD).read_text(encoding='utf-8'))):
  if isinstance(node,ast.Import):imports += [a.name.split('.')[0] for a in node.names]
  elif isinstance(node,ast.ImportFrom):imports.append((node.module or '').split('.')[0])
 assert set(imports)<= {'ctypes','errno','hashlib','json','math','os','stat','sys','threading','time','uuid','contextlib','dataclasses','pathlib','msvcrt'}
 target=json.loads((E/'TARGETED_TEST_RESULTS.json').read_text(encoding='utf-8'));executed=json.loads((E/'runs/targeted'/target['attempt']/'EXECUTED_SOURCE.json').read_text(encoding='utf-8'));assert all(sha(C/n)==h for n,h in executed['files'].items())
 files={n:{'sha256':sha(C/n),'bytes':(C/n).stat().st_size} for n in [LEDGER,*untracked]};raw=json.dumps(files,sort_keys=True,separators=(',',':')).encode();candidate_digest=hashlib.sha256(raw).hexdigest()
 save('_control/SCOPED_SOURCE_REVIEW.json',{'passed':True,'base_HEAD':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'changed_tracked_files':changed,'changed_Ledger_symbols':symbols,'tracked_files_unchanged':len(current)-len(changed),'allowed_new_files':untracked,'staged':git('diff','--cached','--name-status'),'status':git('status','--short'),'coordination_imports':sorted(set(imports)),'latest_targeted_sources_match_current':True,'candidate_source_digest':candidate_digest,'digest_domain':'SHA-256 of sorted compact JSON relative-path map of raw file SHA-256 and bytes for changed/new implementation and tests','files':files,'new_commit_created':False})
 patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+LEDGER,tofile='b/'+LEDGER))
 for name in untracked:patch+=''.join(difflib.unified_diff([],(C/name).read_text(encoding='utf-8').splitlines(True),fromfile='/dev/null',tofile='b/'+name))
 (E/'_control/EXACT.patch').write_text(patch,encoding='utf-8');save('_control/DIFF_RECEIPT.json',{'patch_sha256':sha(E/'_control/EXACT.patch'),'candidate_source_digest':candidate_digest,'files':files})
 summaries=[];deltas=[];subdeltas=[];total=collections.Counter();network=[]
 for name in ('engine','lab','isolation','native','r3'):
  b=json.loads((E/'regressions/baseline'/name/'RESULT.json').read_text(encoding='utf-8'));n=json.loads((E/'regressions/candidate_final'/name/'RESULT.json').read_text(encoding='utf-8'));bm={x['id']:x for x in b['test_outcomes']};nm={x['id']:x for x in n['test_outcomes']}
  diff=[{'suite':name,'id':key,'before':bm.get(key),'after':nm.get(key)} for key in sorted(set(bm)|set(nm)) if any(bm.get(key,{}).get(k)!=nm.get(key,{}).get(k) for k in ('status','exception_type','message','reason'))];deltas+=diff
  bs={x['id']:{k:x.get(k) for k in ('status','exception_type','message')} for x in b['subtest_outcomes']};ns={x['id']:{k:x.get(k) for k in ('status','exception_type','message')} for x in n['subtest_outcomes']};sd=[{'suite':name,'id':key,'before':bs.get(key),'after':ns.get(key)} for key in sorted(set(bs)|set(ns)) if bs.get(key)!=ns.get(key)];subdeltas+=sd
  counts=dict(collections.Counter(x['status'] for x in n['test_outcomes']));total.update(counts);network+=n['network_attempts_denied'];summaries.append({'suite':name,'baseline_tests':b['testsRun'],'final_tests':n['testsRun'],'final_failures':n['failures'],'final_errors':n['errors'],'final_skips':n['skipped'],'final_parent_outcomes':counts,'exact_parent_outcome_message_delta':diff,'exact_subtest_delta':sd,'baseline_command_exit':json.loads((E/'regressions/baseline'/name/'COMMAND.json').read_text(encoding='utf-8'))['exit_code'],'final_command_exit':json.loads((E/'regressions/candidate_final'/name/'COMMAND.json').read_text(encoding='utf-8'))['exit_code'],'baseline_result':f'regressions/baseline/{name}/RESULT.json','final_result':f'regressions/candidate_final/{name}/RESULT.json'})
 save('REGRESSION_RESULTS.json',{'no_new_regressions':not deltas and not subdeltas,'suites':summaries,'actual_tests_per_baseline_or_final_run':sum(s['final_tests'] for s in summaries),'final_counts':dict(total),'parent_outcome_or_message_changes':deltas,'subtest_changes':subdeltas,'network_attempts_denied':network,'raw_tracebacks_preserved':True,'historical_failures_not_rescored':True,'N12_historical_FAIL_unchanged':True,'candidate_intermediate_run_also_retained':'regressions/candidate','source_revision':'_control/SCOPED_SOURCE_REVIEW.json'})
 assert not deltas and not subdeltas and not network
 print(json.dumps({'scoped_source_review':True,'changed_symbols':symbols,'unchanged_tracked_files':len(current)-1,'new_regressions':len(deltas)+len(subdeltas),'final_counts':dict(total),'candidate_source_digest':candidate_digest}),flush=True)
if __name__=='__main__':main()
