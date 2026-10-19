"""Reproduce unchanged supplied review contracts on a fresh offline source copy.

python -B validate_final_f02.py --output-dir E:/short/new-review [--only PROBE_ID]
Use Python3.12 and native Windows filesystem permissions. No inference.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output-dir',required=True);parser.add_argument('--only');args=parser.parse_args()
 dest=Path(args.output_dir).resolve();dest.mkdir(parents=True,exist_ok=False);src=dest/'s';src.mkdir()
 files=json.loads((OUT/'validation/REGRESSION_INPUTS.json').read_text())['files']
 for name,digest in files.items():
  p=ROOT/name;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==digest,name;q=src/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 for directory in ('src','tests','public_inputs'):
  shutil.copytree(OUT/directory,src/OUT.name/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for n in ('PROMPT_HASHES.json','APPROVED_PUBLIC_INPUTS.json'):
  q=src/OUT.name/'validation'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((OUT/'validation'/n).read_bytes())
 for n in ('fresh_probes.py','supplemental_probes.py','sitecustomize.py'):
  (dest/n).write_bytes((OUT/'validation/final_f02/reviewer_source'/n).read_bytes())
 before={p.relative_to(src).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file()};(dest/'source_hashes_before.json').write_text(json.dumps(before))
 reports=[];commands=[];env={**os.environ,'PYTHONPATH':str(dest),'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'}
 scripts=[('fresh_probes.py','fresh_results.json')] if args.only else [('fresh_probes.py','fresh_results.json'),('supplemental_probes.py','supplemental_results.json')]
 for script,report in scripts:
  cmd=[sys.executable,'-B',str(dest/script)]+(['--only',args.only] if args.only else [])
  r=subprocess.run(cmd,cwd=dest,env=env,capture_output=True,text=True,timeout=600);(dest/(script+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8');commands.append({'command':cmd,'exit_code':r.returncode});reports.append(json.loads((dest/report).read_text()))
 probes=[p for r in reports for p in r['probes']];after={p.relative_to(src).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file()}
 result={'count':len(probes),'passed':sum(p['pass_or_fail']=='PASS' for p in probes),'failed':sum(p['pass_or_fail']!='PASS' for p in probes),'commands':commands,'source_unchanged':before==after,'live_model_calls':0,'independent_acceptance':False}
 (dest/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return not(result['source_unchanged'] and result['failed']==0 and len(probes)==(1 if args.only else 154) and all(c['exit_code']==0 for c in commands))
if __name__=='__main__':raise SystemExit(main())
