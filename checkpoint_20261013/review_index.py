"""Read-only inspection of explicitly staged paths before each checkpoint commit."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from sync_audit import ROOT,OUT,GIT,git,sha
group=sys.argv[1];plan=json.loads((OUT/'STAGING_PLAN.json').read_text());expected=set(plan['groups'][group]['paths'])
paths=set(git('diff','--cached','--name-only','-z',raw=True).decode('utf-8').split('\0'))-{''}
assert paths==expected,{'unexpected':sorted(paths-expected),'missing':sorted(expected-paths)}
assert not git('diff','--cached','--diff-filter=D','--name-only').strip()
assert not any('.env'==Path(p).name or p.endswith(('.zip','.pyc','.paths')) or any(x in ('__pycache__','.venv','scratch','staging_review') for x in Path(p).parts) or 'harness' in Path(p).parts[0].lower() for p in paths)
index={}
for entry in git('ls-files','--stage','-z',raw=True).decode().split('\0'):
    if not entry:continue
    meta,path=entry.split('\t',1);mode,oid,stage=meta.split()
    if path in paths:assert mode in ('100644','100755') and stage=='0';index[path]=oid
oids=[index[p] for p in sorted(paths)]
r=subprocess.run([*GIT,'cat-file','--batch'],cwd=ROOT,input=('\n'.join(oids)+'\n').encode(),capture_output=True,check=True)
batch=r.stdout;cursor=0;findings=[];inventory=[]
secret=[re.compile(p) for p in (r'AIza[0-9A-Za-z_-]{30,}',r'ghp_[0-9A-Za-z]{30,}|github_pat_[0-9A-Za-z_]{30,}',r'\bsk-[0-9A-Za-z_-]{20,}|\bhf_[0-9A-Za-z]{25,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
for path in sorted(paths):
    end=batch.index(b'\n',cursor);header=batch[cursor:end].decode().split();cursor=end+1;n=int(header[2]);content=batch[cursor:cursor+n];cursor+=n+1
    assert header[1]=='blob' and n<=10*1024*1024
    h=hashlib.sha256(content).hexdigest();assert h==sha(ROOT/path),'Index bytes differ from reviewed working file: '+path
    try:text=content.decode('utf-8')
    except UnicodeError:
        assert path=='validation_v035/deterministic-demos.txt';text=content.decode('cp1252')
    if any(p.search(text) for p in secret):findings.append({'path':path,'type':'Possible credential signature; value not disclosed'})
    inventory.append({'path':path,'size_bytes':n,'sha256':h})
assert not findings,findings
folder=OUT/'staging_review';folder.mkdir(exist_ok=True)
for label,args in [('stat',['diff','--cached','--stat']),('name-status',['diff','--cached','--name-status']),('text-diff',['diff','--cached','--no-ext-diff'])]:
    (folder/(group+'-'+label+'.txt')).write_bytes(git(*args,raw=True))
check=subprocess.run([*GIT,'diff','--cached','--check'],cwd=ROOT,capture_output=True)
(folder/(group+'-whitespace-check.txt')).write_bytes(check.stdout+check.stderr)
data={'group':group,'file_count':len(paths),'size_bytes':sum(x['size_bytes'] for x in inventory),'index_matches_reviewed_working_bytes':True,'secrets_found':findings,'deletions':0,'zip_cache_environment_harness_paths':0,'diff_check_exit_code':check.returncode,'whitespace_note':'Historical working bytes are preserved; existing whitespace is not cleaned for publication. New checkpoint files must have no whitespace errors.','inventory':inventory}
if check.returncode:
    data['existing_whitespace_findings']=len(check.stdout.decode('utf-8').splitlines())
portable_check=subprocess.run([*GIT,'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=ROOT,capture_output=True)
(folder/(group+'-crlf-whitespace-check.txt')).write_bytes(portable_check.stdout+portable_check.stderr)
data['crlf_aware_diff_check_exit_code']=portable_check.returncode
data['crlf_aware_whitespace_findings']=len(portable_check.stdout.decode('utf-8').splitlines())
if portable_check.returncode:
    assert not any(line.startswith('checkpoint_20261013/') or line.startswith('.gitignore:') for line in portable_check.stdout.decode('utf-8').splitlines()),'New checkpoint whitespace issue'
(folder/(group+'-review.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in data.items() if k!='inventory'}))
