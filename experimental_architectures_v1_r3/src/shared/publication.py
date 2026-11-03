"""Cross-process publication with OS leases, fences and exclusive hard links.
Protects cooperating trusted orchestrators and detects accidental artifact damage.
It is not malicious-host tamper resistance or a hardware power-loss guarantee.
"""
import json,os,secrets,time,threading,weakref
from contextlib import contextmanager
_LOCAL_LOCKS={}
_ACTIVE=weakref.WeakValueDictionary()
_INSTANCES=weakref.WeakSet()
from pathlib import Path
from runtime_isolation_v1.src.trusted_transport.transport import dispatch_lock,GenerationClosed
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
from .strict_json import read,canonical,sha,DataFault
if not __debug__:raise RuntimeError('ABC_R2_OPTIMIZED_PYTHON_UNSUPPORTED')
class ArtifactIntegrity(BoundaryError):pass
class RunBusy(BoundaryError):pass
class StaleOwner(BoundaryError):pass
class PublicationFailure(RuntimeError):pass

def durable(path,value,exclusive=False):
    raw=canonical(value);pending=path.with_name(path.name+'.'+secrets.token_hex(8)+'.pending')
    with pending.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    try:
        if exclusive:os.link(pending,path)
        else:os.replace(pending,path)
    finally:
        if pending.exists():pending.unlink()

def exclusive_publish(pending,final):
    # The link syscall atomically fails if final exists. It never replaces final.
    from .publication_guard import before_exclusive_link
    before_exclusive_link(pending,final)
    os.link(pending,final)

class Publication:
    def __init__(self,directory,request,effective,ledger,*,result_name='RESULT.json',mode='ARCHITECTURE'):
        self.directory=Path(directory).resolve();self.directory.mkdir(parents=True,exist_ok=True)
        self.request=request;self.effective=effective;self.ledger=ledger;self.mode=mode
        self.final=self.directory/result_name;self.guard=self.directory/'.publication.lock';self.meta=self.directory/'publication';self.meta.mkdir(exist_ok=True)
        self.lease_path=self.meta/'owner.lock';self.owner_path=self.meta/'owner.json';self.token=secrets.token_hex(16);self.fence=None;self.fd=None;self.detached=False
        for name in ('events','prepared','attempts'):(self.meta/name).mkdir(exist_ok=True)
        from dataclasses import asdict
        self.identity={'schema_version':'abc-r2-run-v1','implementation':'1.0.1','run_id':request.run_id,'condition_id':request.condition_id,'task_id':request.task_id,'requested_sha256':sha(canonical(asdict(request))),'effective_sha256':sha(canonical(asdict(effective))),'ledger_path':str(ledger.path.resolve()),'output_directory':str(self.directory),'result_name':result_name,'mode':mode}
        self.identity_sha=sha(canonical(self.identity))
        with self.lock():
            binding=self.meta/'IDENTITY.json'
            if binding.exists():
                if read(binding)!=self.identity:raise ArtifactIntegrity('RUN_IDENTITY_CHANGED')
            else:durable(binding,self.identity,True)
            bindings=ledger.path.with_name(ledger.path.name+'.r2_bindings');bindings.mkdir(exist_ok=True)
            with dispatch_lock(bindings/'bindings.lock'):
                global_binding=bindings/(sha(request.run_id.encode())+'.json')
                if global_binding.exists():
                    if read(global_binding)!=self.identity:raise ArtifactIntegrity('RUN_RELOCATED_OR_REBOUND_TO_DIFFERENT_CONTRACT')
                else:durable(global_binding,self.identity,True)
        self.context=None;_INSTANCES.add(self)
    @contextmanager
    def lock(self):
        key=str(self.guard);local=_LOCAL_LOCKS.setdefault(key,threading.RLock())
        with local:
            with dispatch_lock(self.guard):yield
    def event(self,code,**fields):
        value={'schema_version':'abc-r2-event-v1','code':code,'run_id':self.request.run_id,'session_token':self.token,'fence':self.fence,'unix_time':time.time(),**fields}
        durable(self.meta/'events'/(secrets.token_hex(16)+'.json'),value,True)
    def _take_lease(self):
        other=_ACTIVE.get(str(self.lease_path))
        if other is not None and other is not self and other.fd is not None:raise RunBusy('ACTIVE_SAME_PROCESS_OWNER')
        f=self.lease_path.open('a+b');f.seek(0,2)
        if f.tell()==0:f.write(b'0');f.flush()
        f.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            f.close();raise RunBusy('ACTIVE_RUN_OWNER') from None
        self.fd=f;_ACTIVE[str(self.lease_path)]=self
    def _owner(self):
        if not self.owner_path.exists():
            prior=any((self.meta/'attempts').glob('*.json')) or any((self.meta/'prepared').glob('*.json'))
            if not prior:
                for event in (self.meta/'events').glob('*.json'):
                    if read(event).get('code')=='OWNER_CLAIMED':prior=True;break
            if prior:raise ArtifactIntegrity('PREVIOUS_OWNER_METADATA_MISSING')
            return {'fence':0}
        owner=read(self.owner_path)
        if set(owner)!={'fence','token','pid','identity_sha256'} or type(owner['fence']) is not int or owner['fence']<1 or type(owner['pid']) is not int or owner['pid']<1 or type(owner['token']) is not str or len(owner['token'])!=32 or owner['identity_sha256']!=self.identity_sha:raise ArtifactIntegrity('OWNER_METADATA_CORRUPT')
        return owner
    def claim(self):
        # Caller holds publication lock; the lease survives between dispatches.
        if self.detached:raise StaleOwner('DETACHED_SESSION_CANNOT_RECLAIM')
        if self.fd is None:self._take_lease()
        try:owner=self._owner()
        except (ValueError,TypeError,KeyError,BoundaryError) as error:
            self.event('OWNER_METADATA_REJECTED',exception_type=type(error).__name__);self.release();raise ArtifactIntegrity('OWNER_METADATA_NOT_VERIFIED') from error
        if self.fence is None:
            orphans=[p.name for p in self.directory.glob('RESULT.*.pending')]
            if orphans:self.event('ORPHAN_PENDING_FILES_PRESERVED',files=sorted(orphans))
            self.fence=owner['fence']+1;durable(self.owner_path,{'fence':self.fence,'token':self.token,'pid':os.getpid(),'identity_sha256':self.identity_sha});self.event('OWNER_CLAIMED')
        elif owner.get('token')!=self.token or owner.get('fence')!=self.fence:
            self.release();raise StaleOwner('STALE_FENCING_TOKEN')
    def release(self):
        if self.fd is not None:
            f=self.fd;self.fd=None
            if _ACTIVE.get(str(self.lease_path)) is self:_ACTIVE.pop(str(self.lease_path),None)
            try:
                f.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
                else:
                    import fcntl
                    fcntl.flock(f,fcntl.LOCK_UN)
            finally:f.close()
    def detach(self):
        self.event('OWNER_DETACHED_NO_REPLAY');self.release();self.detached=True
    def before_dispatch(self):
        if self.final.exists():
            self.verify_completed();self.event('POST_COMPLETION_DISPATCH_REJECTED');raise GenerationClosed('COMPLETED_RESULT_IMMUTABLE')
        self.claim()
    def attempt_anchor(self,attempt_id):return self.meta/'attempts'/(str(attempt_id).zfill(6)+'.json')
    def response_anchor(self,attempt_id):return self.meta/'attempts'/(str(attempt_id).zfill(6)+'.response.json')
    def verify_completed(self):
        try:return self._verify_completed()
        except (OSError,ValueError,KeyError,TypeError,AssertionError,BoundaryError) as e:
            self.event('COMPLETED_RESULT_INTEGRITY_FAILURE',exception_type=type(e).__name__)
            raise ArtifactIntegrity('COMPLETED_RESULT_NOT_VERIFIED') from e
    def _verify_completed(self):
        data=read(self.final);payload=dict(data);expected=payload.pop('artifact_payload_sha256');assert sha(canonical(payload))==expected
        assert data['implementation_version']=='1.0.1' and data['publication_identity_sha256']==self.identity_sha
        from dataclasses import asdict
        assert canonical(data['request'])==canonical(asdict(self.request))
        assert canonical(data['effective_ledger_request'])==canonical(asdict(self.effective))
        prepared=self.meta/'prepared'/(data['publication']['token']+'.json');anchor=read(prepared)
        assert anchor['identity_sha256']==self.identity_sha and anchor['result_file_sha256']==sha(self.final.read_bytes()) and anchor['payload_sha256']==expected
        owner=read(self.owner_path);assert owner['token']==data['publication']['token'] and owner['fence']==data['publication']['fence']
        return self.verify_semantics(data)
    def verify_semantics(self,data):
        from .certification import require_certification_eligible
        require_certification_eligible(self,data)
        self.request.wire();self.effective.wire()
        assert sha(canonical(data['request']))==self.identity['requested_sha256'] and sha(canonical(data['effective_ledger_request']))==self.identity['effective_sha256']
        result=data['result'];summary=self.ledger.summary(self.request.run_id);assert canonical(result['model_invocations'])==canonical(summary['attempts']) and result['physical_attempts']==summary['physical_attempts']
        for k in ('input_tokens','output_tokens','total_tokens'):assert result[k]==summary[k]
        assert result['wall_time']==summary['wall_time'] and result['run_id']==self.request.run_id and result['condition_id']==self.request.condition_id and result['task_id']==self.request.task_id
        assert data['scientific_scores'] is None
        candidates=result['all_generated_candidates'];ids=[]
        for c in candidates:
            assert c['candidate_id'] not in ids and all(x in ids for x in c['parent_ids']);ids.append(c['candidate_id'])
            assert sha(c['answer'].encode())==c['answer_sha256']
            row=next(a for a in summary['attempts'] if a['attempt_id']==c['attempt_id']);assert row['state']=='SUCCEEDED' and row.get('candidate') and row['response_text']==c['answer']
        if self.mode=='ARCHITECTURE':
            from ..prompts.registry import STAGES
            generated=[a['attempt_id'] for a in summary['attempts'] if a['state']=='SUCCEEDED' and a.get('candidate') and STAGES.get(json.loads(a['purpose'])['purpose'],{}).get('kind')=='candidate']
        else:
            generated=[a['attempt_id'] for a in summary['attempts'] if a['state']=='SUCCEEDED' and a.get('candidate') and json.loads(a['purpose'])['purpose'] in ('initial_candidate','revision','direct_answer','self_reflect_initial','self_reflect_revision')]
        assert [c['attempt_id'] for c in candidates]==generated
        assert result['candidate_lineage']=={c['candidate_id']:list(c['parent_ids']) for c in candidates}
        assert result['initial_candidate']==(ids[0] if ids else None) and result['final_candidate'] in [None,*ids]
        assert data['C0']==(candidates[0]['answer'] if candidates else None)
        selected=next((c['answer'] for c in candidates if c['candidate_id']==result['final_candidate']),None);assert data['FINAL']==selected
        from runtime_isolation_v1.src.trusted_transport.transport import Gateway
        # Closure is read using the unchanged inherited integrity checks.
        holder=object.__new__(Gateway);holder.closed=self.ledger.path.with_suffix('.closed.json');closed=holder._closed_runs()[self.request.run_id]
        assert canonical(closed)==canonical(data['generation_closed']) and closed['attempts_sha256']==sha(canonical(summary['attempts']))
        if result['termination_reason'] in ('COMPLETED','NO_ACTIONABLE_REVISION'):assert not closed['outstanding_or_unknown_cost']
        from .journals import verify_journals,verify_native_records
        report=verify_journals(self) if self.mode=='ARCHITECTURE' else verify_native_records(self,data['provider_records'])
        assert canonical(report)==canonical(data['journal_integrity'])
        assert data['durable_journal_hashes']==report['trusted_hashes']
        return data
    def publish(self,data):
        # Caller holds publication lock and owns the lease/fence.
        if self.final.exists():return self.verify_completed()
        self.claim();data.update(implementation_version='1.0.1',publication_identity_sha256=self.identity_sha,publication={'token':self.token,'fence':self.fence})
        payload=dict(data);payload.pop('artifact_payload_sha256',None);data['artifact_payload_sha256']=sha(canonical(payload))
        try:self.verify_semantics(data)
        except (AssertionError,KeyError,TypeError,ValueError) as error:
            self.event('RESULT_SEMANTICS_REJECTED',exception_type=type(error).__name__);raise ArtifactIntegrity('RESULT_SEMANTICS_NOT_BOUND_TO_DURABLE_LEDGER') from error
        raw=(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        pending=self.directory/('RESULT.'+self.token+'.pending')
        # An orphan pending file cannot serve as an ownership token or be overwritten.
        with pending.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        prepared={'identity_sha256':self.identity_sha,'payload_sha256':data['artifact_payload_sha256'],'result_file_sha256':sha(raw),'token':self.token,'fence':self.fence}
        anchor=self.meta/'prepared'/(self.token+'.json')
        if anchor.exists():
            if read(anchor)!=prepared:raise ArtifactIntegrity('CONFLICTING_PREPARED_PAYLOAD')
        else:durable(anchor,prepared,True)
        # Revalidate while read handles deny mutation of the exact evidence,
        # prepared anchor and pending bytes through the native exclusive link.
        # The run lease/fence and exclusive publication semantics are unchanged.
        from .publication_guard import EvidencePin, denied_evidence_write
        with EvidencePin(self,pending,anchor,raw,prepared) as pin:
            try:self.verify_semantics(data)
            except (AssertionError,KeyError,TypeError,ValueError,OSError) as error:
                self.event('PUBLICATION_REVALIDATION_REJECTED',exception_type=type(error).__name__)
                raise ArtifactIntegrity('EVIDENCE_CHANGED_BEFORE_PUBLICATION') from error
            try:exclusive_publish(pending,self.final)
            except FileExistsError:
                self.event('COMPETING_FINAL_PUBLICATION');return self.verify_completed()
            except OSError as e:
                if denied_evidence_write(e,pin):
                    self.event('PUBLICATION_EVIDENCE_MUTATION_DENIED',exception_type=type(e).__name__)
                    raise ArtifactIntegrity('EVIDENCE_MUTATION_AT_PUBLICATION_REJECTED') from e
                self.event('EXCLUSIVE_PUBLICATION_FAILED',exception_type=type(e).__name__);raise PublicationFailure('NO_RESULT_PUBLISHED') from e
        # Removal is cleanup only; publication does not depend on removing this hard link.
        try:pending.unlink()
        except OSError:self.event('PUBLISHED_PENDING_CLEANUP_FAILED')
        return data
