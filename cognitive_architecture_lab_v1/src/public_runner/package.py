"""Trusted public-input construction; these checks are NOT an OS sandbox."""
import hashlib,json,os,stat
from pathlib import Path,PurePosixPath,PureWindowsPath
from ..interfaces.contracts import public_task,canonical

def approved_path(root,relative):
    if not isinstance(relative,str) or '\\' in relative or ':' in relative:raise ValueError('Noncanonical input path')
    p=PurePosixPath(relative)
    if p.is_absolute() or PureWindowsPath(relative).is_absolute() or not relative or any(x in ('..','.') for x in relative.split('/')):raise ValueError('Traversal rejected')
    root=Path(root).absolute();target=root.joinpath(*p.parts)
    # Check each reparse point, including the supplied root and its ancestors. Trusted builder only.
    for part in (target,*target.parents):
        info=part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:raise ValueError('Links/reparse points not approved')
    if not target.is_file():raise ValueError('Expected regular public file')
    return target

def build_package(root,approved):
    if not approved:raise ValueError('Empty public allowlist')
    result=[]
    for relative,expected in sorted(approved.items()):
        path=approved_path(root,relative);data=path.read_bytes();actual=hashlib.sha256(data).hexdigest()
        if actual!=expected:raise ValueError('Approved public bytes changed')
        task=public_task(json.loads(data.decode('utf-8')))
        result.append({'path':relative,'source_sha256':actual,'task':task})
    if len({e['task']['task_id'] for e in result})!=len(result):raise ValueError('Duplicate public task identity')
    return json.dumps({'schema_version':'public-input-package-v1','files':result},ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')

def minimal_environment(temp_root):
    # Child import isolation is measured separately and grants no filesystem security.
    return {'SYSTEMROOT':os.environ.get('SYSTEMROOT',r'C:\Windows'),'TEMP':str(temp_root),'TMP':str(temp_root),'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'}
