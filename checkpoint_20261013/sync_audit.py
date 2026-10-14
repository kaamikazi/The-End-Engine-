"""Read-only local/committed-content inventory for the authorised checkpoint."""
import collections,csv,hashlib,json,re,subprocess,sys,tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
GIT=['git','--no-optional-locks','-c','safe.directory=E:/The End Engine']
def git(*args,raw=False):
    r=subprocess.run([*GIT,*args],cwd=ROOT,capture_output=True)
    if r.returncode and args==('submodule','status'):
        index=subprocess.run([*GIT,'ls-files','--stage'],cwd=ROOT,capture_output=True,check=True).stdout
        assert not (ROOT/'.gitmodules').exists() and not any(x.startswith(b'160000 ') for x in index.splitlines())
        return b'' if raw else 'No submodules (.gitmodules absent; index contains no gitlinks); child submodule command unavailable in sandbox\n'
    r.check_returncode()
    return r.stdout if raw else r.stdout.decode('utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def classify(rel):
    parts=Path(rel).parts;top=parts[0]
    if any(p in ('__pycache__','.venv','venv','build','dist','scratch','node_modules') for p in parts) or rel.endswith(('.pyc','.zip','.tmp')) or top.endswith('.egg-info'):return 'G','EXCLUDE','Generated cache/environment/build/extraction scratch or duplicate ZIP'
    if top=='end_engine' or rel=='pyproject.toml':return 'A','INCLUDE','Engine implementation/runtime packaging'
    if top=='tests':return 'B','INCLUDE','Engine offline tests'
    if top.startswith('experimental_task_pack_'):return 'F','INCLUDE','Versioned evaluator source/tasks/fixtures/contracts/results/provenance'
    if top=='trajectories':return 'G','EXCLUDE','Existing ignored demo/runtime trajectory directory'
    if parts[-1] in ('live_progress.log',):return 'G','EXCLUDE','Transient progress log; scientific trial/call ledgers remain included'
    if top in ('benchmark_alpha','benchmark_beta','benchmark_beta_gemini','v035_core_regression_pilot','v0351_core_regression_pilot','architecture_review_v1','independent_review_package_v1'):
        if Path(rel).suffix=='.py' or 'tasks' in parts or 'schemas' in parts:return 'D','INCLUDE','Research source/definitions/schema'
        return 'E','INCLUDE','Historical research evidence/report/manifest/ledger preserved verbatim'
    if top.startswith('validation_') or top.startswith('demo'):return 'E','INCLUDE','Versioned validation/compatibility/demo evidence'
    if Path(rel).suffix in ('.md','.toml','.ps1') or top=='docs':return 'C','INCLUDE','Documentation/runtime instructions'
    if top.startswith('.') and top not in ('.gitignore','.gitattributes'):return 'H','REVIEW','Hidden local configuration; inspect before disclosure'
    return 'C','INCLUDE','Repository source/documentation'
def baseline():
    assert not (OUT/'LOCAL_BASELINE.json').exists()
    commands=[('root',['rev-parse','--show-toplevel']),('prefix',['rev-parse','--show-prefix']),('status-short',['status','--short']),('status-branch',['status','--branch']),('branches',['branch','-vv']),('remotes',['remote','-v']),('log',['log','--oneline','--decorate','-15']),('diff-stat',['diff','--stat']),('diff-name-status',['diff','--name-status']),('staged-stat',['diff','--cached','--stat']),('ignored',['status','--short','--ignored']),('submodules',['submodule','status']),('refs',['show-ref'])]
    root=git('rev-parse','--show-toplevel').strip();assert Path(root).resolve()==ROOT
    assert git('remote','get-url','origin').strip()=='https://github.com/kaamikazi/The-End-Engine-.git'
    assert not git('diff','--cached','--name-only').strip(),'Existing staged work requires preservation-specific staging plan'
    for name,args in commands:(OUT/(name+'-before.txt')).write_text(git(*args),encoding='utf-8',newline='\n')
    raw=git('status','--porcelain=v1','-z','--untracked-files=all',raw=True).decode('utf-8');entries=[]
    for entry in raw.split('\0'):
        if not entry:continue
        state=entry[:2];rel=entry[3:]
        entries.append({'path':rel,'state':state})
    tracked=set(git('ls-files','-z',raw=True).decode().split('\0'))-{''}
    ignored=set(git('ls-files','--others','--ignored','--exclude-standard','-z',raw=True).decode().split('\0'))-{''}
    rows=[];hashes={};nested=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT).as_posix()
        if '.git' in p.relative_to(ROOT).parts:
            if p.name=='.git' and p!=ROOT/'.git':nested.append(rel)
            continue
        if not p.is_file() or p.is_relative_to(OUT):continue
        category,decision,reason=classify(rel);size=p.stat().st_size;h=sha(p);hashes[rel]=h
        if rel in ignored:decision='EXCLUDE';reason='Already ignored local material'
        if size>10*1024*1024:decision='HOLD_LARGE_LOCAL_ONLY';reason='Above10MiB: retain exact original, record hash/path; no publication without explicit artifact decision'
        rows.append({'path':rel,'size_bytes':size,'sha256':h,'tracked':rel in tracked,'ignored':rel in ignored,'category':category,'recommendation':decision,'reason':reason})
    save('LOCAL_FILE_HASHES_BEFORE.json',hashes)
    with (OUT/'FILE_INVENTORY.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    save('DIRTY_INVENTORY.json',entries)
    src={p.relative_to(ROOT).as_posix():sha(p) for p in sorted([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])}
    fp=hashlib.sha256(json.dumps(src,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'];assert version=='0.3.5.2' and fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    data={'root':str(ROOT),'origin':git('remote','get-url','origin').strip(),'original_head':git('rev-parse','HEAD').strip(),'original_branch':git('branch','--show-current').strip(),'engine_version':version,'engine_fingerprint':fp,'changed_counts':dict(collections.Counter(x['state'] for x in entries)),'local_file_count':len(rows),'local_size_bytes':sum(r['size_bytes'] for r in rows),'nested_git':nested,'submodules':git('submodule','status'),'recommendation_counts':dict(collections.Counter(r['recommendation'] for r in rows)),'size_thresholds':{str(m)+'MiB':[{'path':r['path'],'size_bytes':r['size_bytes'],'sha256':r['sha256']} for r in rows if r['size_bytes']>m*1024*1024] for m in (10,25,50,100)},'per_directory':{k:{'files':sum(r['path'].split('/')[0]==k for r in rows),'bytes':sum(r['size_bytes'] for r in rows if r['path'].split('/')[0]==k)} for k in sorted({r['path'].split('/')[0] for r in rows})}}
    save('LOCAL_BASELINE.json',data);print(json.dumps({k:data[k] for k in ('root','origin','original_head','original_branch','engine_version','engine_fingerprint','changed_counts','local_file_count','local_size_bytes','nested_git','size_thresholds','recommendation_counts')}))
def security():
    rows=list(csv.DictReader((OUT/'FILE_INVENTORY.csv').open(encoding='utf-8')));findings=[];flags=[];scanned=0
    patterns=[('Gemini key',r'AIza[0-9A-Za-z_-]{30,}'),('GitHub token',r'ghp_[0-9A-Za-z]{30,}|github_pat_[0-9A-Za-z_]{30,}'),('Provider key',r'\bsk-[0-9A-Za-z_-]{20,}|\bhf_[0-9A-Za-z]{25,}'),('Private key',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    def inspect(text,location,history=False):
        for label,pattern in patterns:
            if re.search(pattern,text):findings.append({'location':location,'type':label,'history':history})
        for m in re.finditer(r'''(?i)(?:api[_-]?key|password|access[_-]?token|authorization|bearer)\s*[=:]\s*["']([^"'\r\n]{12,})["']''',text):
            value=m.group(1)
            if not any(x in value.lower() for x in ('example','placeholder','test','dummy','redacted','os.environ','getenv','environ.get','bearer {','f"','f\'','self.','config.','error','none','not_set')):
                flags.append({'location':location,'type':'Credential-assignment candidate; local review required','history':history,'line':text[:m.start()].count('\n')+1})
        if re.search(r'(?i)(?:C:[\\/]+Users[\\/]|(?:localhost|127\.0\.0\.1):|https?://[^\s"<>]*(?:internal|private))',text):flags.append({'location':location,'type':'Development path/local endpoint marker','history':history})
    for row in rows:
        if row['recommendation']!='INCLUDE':continue
        p=ROOT/row['path']
        if p.name in ('.env','credentials.json','id_rsa','id_ed25519') or p.name.startswith('.env.') or p.suffix.lower() in ('.pem','.key','.pfx'):findings.append({'location':row['path'],'type':'Credential filename','history':False});continue
        try:text=p.read_text(encoding='utf-8')
        except UnicodeError:
            raw=p.read_bytes()
            if p.suffix=='.txt' and not any(x<32 and x not in (9,10,13) for x in raw):
                text=raw.decode('cp1252');flags.append({'location':row['path'],'type':'Legacy Windows CP1252 text log, preserved bytes','history':False})
            elif raw.startswith((b'\xff\xfe',b'\xfe\xff')):text=raw.decode('utf-16')
            else:findings.append({'location':row['path'],'type':'Unexpected binary proposed for publication','history':False});continue
        inspect(text,row['path']);scanned+=1
    # Inspect every unique blob reachable from local history without altering refs.
    objects=git('rev-list','--objects','--all').splitlines();history_scanned=0
    batch=subprocess.run([*GIT,'cat-file','--batch'],cwd=ROOT,input=('\n'.join(x.split(' ')[0] for x in objects)+'\n').encode(),capture_output=True,check=True).stdout
    cursor=0
    for item in objects:
        oid,_,name=item.partition(' ')
        end=batch.index(b'\n',cursor);header=batch[cursor:end].decode().split();cursor=end+1
        size=int(header[2]);data=batch[cursor:cursor+size];cursor+=size+1
        if header[1]!='blob':continue
        try:text=data.decode('utf-8')
        except UnicodeError:continue
        inspect(text,oid+':'+name,True);history_scanned+=1
    save('SECURITY_SCAN.json',{'proposed_text_files_scanned':scanned,'history_text_blobs_scanned':history_scanned,'possible_secret_findings':findings,'review_markers':flags,'secret_values_reported':False,'scan_scope':'Proposed included files and reachable history; excluded archives/environments not staged','passed_automatic_signatures':not findings})
    print(json.dumps({'proposed_text_files_scanned':scanned,'history_text_blobs_scanned':history_scanned,'possible_secret_findings':findings,'assignment_review_markers':[x for x in flags if x['type'].startswith('Credential')],'development_marker_count':sum(x['type'].startswith('Development') for x in flags)}))
if __name__=='__main__':
    {'baseline':baseline,'security':security}[sys.argv[1]]()
