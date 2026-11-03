"""Additive result normalization only; existing baseline execution is untouched."""
import json
from dataclasses import asdict
from pathlib import Path
from cognitive_architecture_lab_v1.src.interfaces.contracts import Candidate,RunResult,canonical
from native_model_integration_v1.src.baseline_adapters.run import run_baseline
from native_model_integration_v1.src.provider_protocol.wire import sha
from .session import execute
from .baseline_contract import admit
from .publication import Publication
from .journals import verify_native_records
class BaselineRecoveryBlocked(RuntimeError):pass
from ..adapters.script import Script,gate,select

def baseline(request,directory,ledger):
    contract=admit(request) # no mkdir, journal, registration or dispatch before admission
    store=Publication(directory,request,request,ledger,result_name='COMMON_RESULT.json',mode='NATIVE_BASELINE')
    try:
        with store.lock():
            if store.final.exists():return store.verify_completed()
            store.claim()
            if any(a['run_id']==request.run_id for a in ledger.state()['attempts']):
                store.event('BASELINE_PARTIAL_RUN_BLOCKED_NO_REPLAY');raise BaselineRecoveryBlocked('Original baseline cannot safely replay a partially executed cell')
            r=run_baseline(request.public_task_payload,request.condition_id,directory,run_id=request.run_id,mode='three_cycles' if request.condition_id=='FROZEN_CURRENT_END' else 'progress',shared_ledger=ledger)
            summary=ledger.summary(request.run_id);rows=summary['attempts'];candidates=[]
            if request.condition_id=='FROZEN_CURRENT_END':
                gen=[a for a in rows if json.loads(a['purpose'])['purpose'] in ('initial_candidate','revision') and a.get('candidate')]
                for i,c in enumerate((r.get('engine_trajectory') or {}).get('candidates',[])):
                    candidates.append(Candidate(c['candidate_id'],c.get('answer_content') or c['content'],gen[i]['attempt_id'],(c['parent_candidate_id'],) if c.get('parent_candidate_id') else (),True))
                final=(r.get('engine_trajectory') or {}).get('final_candidate_id')
            else:
                gen=[a for a in rows if json.loads(a['purpose'])['purpose'] in ('direct_answer','self_reflect_initial','self_reflect_revision') and a.get('candidate')]
                for i,a in enumerate(gen):candidates.append(Candidate('C'+str(i),a['response_text'],a['attempt_id'],('C0',) if i else (),True))
                final=candidates[-1].candidate_id if candidates else None
            reason=r['termination_reason'];reason={'ACCEPTED_PROVISIONALLY':'COMPLETED','ACCEPTED_HIGH_CONFIDENCE':'COMPLETED','INCONCLUSIVE':'UNRESOLVED','MODEL_PROTOCOL_FAILURE':'PROTOCOL_FAILURE'}.get(reason,reason)
            result=RunResult(request.run_id,request.condition_id,request.task_id,request.model_identity,{'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','native_baseline_unchanged':True},candidates[0].candidate_id if candidates else None,final,tuple(candidates),{c.candidate_id:list(c.parent_ids) for c in candidates},tuple(rows),len(rows),summary['input_tokens'],summary['output_tokens'],summary['total_tokens'],summary['wall_time'],reason,{'effective_attempt_limit':36},{'unknown_usage_attempts':summary['unknown_usage_attempts']},({'original_native_termination':r['termination_reason'],'actual_delivered_answer':r['FINAL']},),(),()).validate()
            out={'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','request':asdict(request),'result':result.data(),'C0':r['C0'],'FINAL':r['FINAL'],'generation_closed':r['generation_closed'],'provider_records':r['provider_records'],'original_baseline_record':'MOCK_REPLAY.json','scientific_scores':None}
            out['effective_ledger_request']=asdict(request);out['baseline_contract']=contract
            out['journal_integrity']=verify_native_records(store,out['provider_records']);out['durable_journal_hashes']={}
            return store.publish(out)
    finally:store.release()

def wiring_script(task):
    # Independent canned responses, not exposed fixture answers or quality claims.
    initial={'mock_wiring_only':task['task_id'],'synthetic_response':True}
    return Script({'INITIAL':[initial],'SPARSE_GATE':[gate()],'REPAIR_INVENTORY':[{'findings':[]}],'ALTERNATIVE_REQUIREMENTS':[initial|{'approach':'requirements'}],'ALTERNATIVE_CONSTRAINTS':[initial|{'approach':'constraints'}],'ALTERNATIVE_SELECTION':[select()]})
