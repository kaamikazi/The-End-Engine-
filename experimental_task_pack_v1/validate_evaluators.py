"""Run offline evaluator tests/fixtures; preserve every numbered validation attempt."""
import json
from pathlib import Path
import socket
import sys
import time
import unittest
from unittest.mock import patch
import urllib.request
from experimental_task_pack_v1.evaluators import evaluate_answer
from experimental_task_pack_v1.tests.test_evaluators import fixtures

OUT=Path(__file__).resolve().parent;VAL=OUT/'validation'
def run():
    VAL.mkdir(exist_ok=True);number=len(list(VAL.glob('evaluator-attempt-*.json')))+1
    prefix=f'evaluator-attempt-{number:02d}';attempts=[]
    def blocked(*args,**kwargs):attempts.append('blocked');raise AssertionError('No network in evaluator validation')
    start=time.perf_counter()
    with (VAL/(prefix+'.txt')).open('w',encoding='utf-8') as stream:
        with patch.object(socket.socket,'connect',blocked),patch.object(socket.socket,'connect_ex',blocked), \
            patch.object(socket.socket,'sendto',blocked),patch.object(socket,'getaddrinfo',blocked), \
            patch.object(urllib.request.OpenerDirector,'open',blocked):
            suite=unittest.defaultTestLoader.discover(str(OUT/'tests'),top_level_dir=str(OUT.parent))
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    rows=[];disagreements=[]
    for f in fixtures():
        r=evaluate_answer(f['task_id'],f['candidate_content'],**f['evaluation_options']);e=f['expected'];mismatches=[]
        for key in ('overall_pass','task_success'):
            if r[key]!=e[key]:mismatches.append(key)
        if r['safety']['outcome']!=e['safety_outcome']:mismatches.append('safety_outcome')
        for name,wanted in e['dimensions'].items():
            for key in ('score','status'):
                if r['dimensions'][name][key]!=wanted[key]:mismatches.append(name+'.'+key)
        for required,actual in (('required_contract_errors',r['dimensions']['output_contract_compliance']['violations']),
            ('required_safety_violations',r['safety']['violations']),('required_review_reasons',r['safety']['review_reasons'])):
            if not set(e[required])<=set(actual):mismatches.append(required)
        row={'fixture_id':f['fixture_id'],'expected':e,'actual':r,'matches_all_labels':not mismatches,'mismatches':mismatches}
        rows.append(row)
        if mismatches:disagreements.append({'fixture_id':f['fixture_id'],'mismatches':mismatches})
    def error_count(expected,actual):return sum(expected(f['expected']) and actual(r['actual']) for f,r in zip(fixtures(),rows))
    metrics={'known_pass_cases':sum(f['expected']['overall_pass'] is True for f in fixtures()),
        'known_fail_cases':sum(f['expected']['overall_pass'] is False for f in fixtures()),
        'review_required_cases':sum(f['expected']['overall_pass'] is None for f in fixtures()),
        'false_acceptance':error_count(lambda e:e['overall_pass'] is False,lambda r:r['overall_pass'] is True),
        'false_rejection':error_count(lambda e:e['overall_pass'] is True,lambda r:r['overall_pass'] is False),
        'false_formatting_failure':error_count(lambda e:e['dimensions']['output_contract_compliance']['score']==1,lambda r:r['dimensions']['output_contract_compliance']['score']==0),
        'missed_requirement_violation':error_count(lambda e:e['dimensions']['requirement_preservation']['score'] is not None and e['dimensions']['requirement_preservation']['score']<1,lambda r:r['dimensions']['requirement_preservation']['score']==1),
        'missed_unsupported_citation':error_count(lambda e:e['dimensions']['unsupported_citation_evidence']['score']==0,lambda r:r['dimensions']['unsupported_citation_evidence']['score']!=0),
        'false_unsupported_citation_detection':error_count(lambda e:e['dimensions']['unsupported_citation_evidence']['score']==1,lambda r:r['dimensions']['unsupported_citation_evidence']['score']==0),
        'inappropriate_safety_upgrade':error_count(lambda e:e['dimensions']['epistemic_safety']['score']!=1,lambda r:r['dimensions']['epistemic_safety']['score']==1),
        'ambiguous_cases_silently_accepted':error_count(lambda e:e['overall_pass'] is None,lambda r:r['overall_pass'] is True)}
    denominators={'false_acceptance':metrics['known_fail_cases'],'false_rejection':metrics['known_pass_cases'],
        'false_formatting_failure':sum(f['expected']['dimensions']['output_contract_compliance']['score']==1 for f in fixtures()),
        'missed_requirement_violation':sum(f['expected']['dimensions']['requirement_preservation']['score'] is not None and f['expected']['dimensions']['requirement_preservation']['score']<1 for f in fixtures()),
        'missed_unsupported_citation':sum(f['expected']['dimensions']['unsupported_citation_evidence']['score']==0 for f in fixtures()),
        'false_unsupported_citation_detection':sum(f['expected']['dimensions']['unsupported_citation_evidence']['score']==1 for f in fixtures()),
        'inappropriate_safety_upgrade':sum(f['expected']['dimensions']['epistemic_safety']['score']!=1 for f in fixtures()),
        'ambiguous_cases_silently_accepted':metrics['review_required_cases']}
    report={'attempt':number,'date':'2026-10-12','tests_run':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'skipped':len(result.skipped),'elapsed_seconds':round(time.perf_counter()-start,3),
        'network_attempts':len(attempts),'fixture_count':len(rows),'fixture_label_disagreements':disagreements,
        'passed':result.wasSuccessful() and not attempts and not disagreements,'metrics':metrics,'metric_denominators':denominators,'fixtures':rows,
        'independent_review_status':'PENDING','live_model_calls':0,'untrusted_code_execution':False}
    (VAL/(prefix+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (VAL/'RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='fixtures'}))
    return report['passed']
if __name__=='__main__':sys.exit(0 if run() else 1)
