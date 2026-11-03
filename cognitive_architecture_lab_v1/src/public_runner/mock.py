"""Scripted deterministic test transport ONLY. Never connects a real backend.
This mock is trusted local code, not an isolated process. No A/B/C strategy.
"""
import hashlib
from ..interfaces.contracts import Candidate,RunResult,canonical
class MockSession:
    def __init__(self,request,ledger):
        self.request=request;self.ledger=ledger;ledger.register(request);self.candidates=[];self.visible=[];self.errors=[]
        for a in ledger.summary(request.run_id)['attempts']:
            if a.get('candidate'):
                c=a['candidate'];self.candidates.append(Candidate(c['candidate_id'],a['response_text'],a['attempt_id'],tuple(c['parent_ids']),c['complete']))
            if a.get('error_code'):self.errors.append({'attempt_id':a['attempt_id'],'code':a['error_code'],'retained_output':a.get('response_text')})
    def dispatch(self,answer,*,purpose='candidate',parents=(),complete=True,input_tokens=3,output_tokens=2,seconds=.01,failure=None):
        # Scripted answer comes from the test, never the evaluator or a model.
        if not isinstance(answer,str):raise ValueError('Mock text required')
        if purpose not in ('candidate','critique','decision','verification','alternative','protocol_repair','retry','selection','judge'):raise ValueError('Unknown call purpose')
        if any(p not in {c.candidate_id for c in self.candidates} for p in parents):raise ValueError('Unknown parent')
        wire=self.request.wire_bytes();i=self.ledger.reserve(self.request.run_id,purpose,100,.1)
        self.visible.append(wire)
        h=hashlib.sha256(answer.encode('utf-8')).hexdigest()
        candidate=None
        if purpose in ('candidate','alternative') and (not failure or answer):
            c=Candidate(f'c{len(self.candidates)}',answer,i,tuple(parents),complete and not bool(failure))
            candidate={'candidate_id':c.candidate_id,'parent_ids':list(c.parent_ids),'complete':c.complete}
        self.ledger.finish(i,state=failure or 'SUCCEEDED',input_tokens=input_tokens,output_tokens=output_tokens,seconds=seconds,error_code=failure,response_sha256=h,response_text=answer,candidate=candidate)
        if candidate:self.candidates.append(c)
        if failure:self.errors.append({'attempt_id':i,'code':failure,'retained_output':answer})
        return c if candidate else None
    def result(self,termination='COMPLETED',final=None):
        s=self.ledger.summary(self.request.run_id)
        initial=self.candidates[0].candidate_id if self.candidates else None
        if final is None:final=self.candidates[-1].candidate_id if self.candidates else None
        candidates=tuple(self.candidates) # Global durable attempt IDs, shared across cells.
        return RunResult(self.request.run_id,self.request.condition_id,self.request.task_id,self.request.model_identity,
            {'transport':'deterministic-mock','security_boundary':'NONE','model_digest':self.request.model_digest},initial,final,candidates,
            {c.candidate_id:list(c.parent_ids) for c in candidates},tuple(s['attempts']),s['physical_attempts'],s['input_tokens'],s['output_tokens'],s['total_tokens'],s['wall_time'],termination,
            {'halted':s['halted']},{'outstanding_attempts':s['outstanding_attempts'],'unknown_usage_attempts':s['unknown_usage_attempts']},
            (self.request.private_metadata(),),(),tuple(self.errors)).validate()
