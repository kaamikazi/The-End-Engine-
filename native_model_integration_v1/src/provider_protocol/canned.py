"""Deterministic trusted test script. Never a model or evaluator. No live fallback."""
import json
from end_engine.models.mock import MockProvider
from end_engine.quality.mock import MockJudgeProvider
from v0351_core_regression_pilot.bench.providers import JUDGE_PURPOSES
from .wire import SETTINGS

def completion(text='SYNTHETIC_WIRING_ONLY',**changes):
    r={'model':SETTINGS.model,'created_at':'2000-01-01T00:00:00Z','response':text,'done':True,'done_reason':'stop','total_duration':1000000,'load_duration':1000,'prompt_eval_count':10,'prompt_eval_duration':1000,'eval_count':5,'eval_duration':1000};r.update(changes)
    return json.dumps(r,allow_nan=False).encode()
class CannedScript:
    def __init__(self,mode='progress',fault_purpose='critique'):
        self.mode=mode;self.fault_purpose=fault_purpose;self.positions={};self.mock=MockProvider();self.judge=MockJudgeProvider()
    def reply(self,request,structured,seq):
        p=request.purpose;n=self.positions.get(p,0);self.positions[p]=n+1
        if self.mode=='failure':raise RuntimeError('Synthetic transport failure')
        if self.mode=='interrupt':raise KeyboardInterrupt()
        if self.mode=='unknown_usage':
            r=json.loads(completion('SYNTHETIC_WIRING_ONLY'));r.pop('prompt_eval_count');return json.dumps(r).encode()
        if self.mode=='all_repairs' and structured and n%2==0:return completion('not valid JSON')
        if self.mode=='invalid_reference' and p=='critique' and n==0:return completion(json.dumps({'summary':'Synthetic invalid reference','findings':[{'weakness_id':'UNKNOWN','type':'constraint','severity':'high','description':'Synthetic allegation','evidence':'Synthetic text'}]}))
        if self.mode=='repair' and p==self.fault_purpose and n<2:return completion('not valid JSON')
        if not structured:
            index=0 if self.mode in ('stagnant','no_progress') else n if p=='revision' else 0
            return completion(json.dumps({'synthetic_wiring_only':True,'stage':p if self.mode not in ('stagnant','no_progress') else 'same','sequence':index}))
        if p=='branch_generation':return completion(json.dumps({'branches':[{'hypothesis':'Synthetic option '+str(i),'content':'Synthetic component only, not a task solution.'} for i in range(request.context['max_branches'])]}))
        if p in JUDGE_PURPOSES:
            content=self.judge.evaluate(request).content
        else:content=self.mock.generate_structured(request).content
        if self.mode in ('no_progress','three_cycles'):
            if p=='critique':content={'summary':'No actionable fixture defect','findings':[]}
            if p=='revision_plan':content={'changes':[]}
            if p=='verification':content={**content,'passed':False,'remaining_issues':['Synthetic inconclusive model opinion'],'weakness_updates':[]}
        return completion(json.dumps(content,ensure_ascii=False))
