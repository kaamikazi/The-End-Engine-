"""Read-only research preservation/source reconciliation; writes only review artifacts."""
import ast
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
import preflight as p
import analyze as a

ROOT, OUT=p.ROOT,p.OUT
def readcsv(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    before=a.load(OUT/'PROTECTED_BEFORE.json');after=p.protected()
    changed=[name for name in before.keys() & after.keys() if before[name]!=after[name]]
    added=sorted(after.keys()-before.keys());removed=sorted(before.keys()-after.keys())
    assert not(changed or added or removed),(changed,added,removed)
    source=p.source();assert source==a.load(OUT/'SOURCE_BEFORE.json')
    base=a.load(OUT/'BASELINE.json')
    fingerprint=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert fingerprint==base['source_fingerprint']
    head=p.git('rev-parse','HEAD').strip();status=p.git('status','--short')
    assert head==base['git_head'];assert status==(OUT/'git-status-before.txt').read_text(encoding='utf-8')
    (OUT/'git-status-after.txt').write_text(status,encoding='utf-8',newline='\n')
    a.dump('SOURCE_AFTER.json',source);a.dump('PROTECTED_AFTER.json',after)

    cycles=a.load(OUT/'CYCLES.json');runs=a.load(OUT/'RUNS.json');candidates=a.load(OUT/'CANDIDATES.json')
    cc=readcsv('CYCLE_AUDIT.csv');tr=readcsv('CANDIDATE_TRANSITIONS.csv');calls=readcsv('CALL_AUDIT.csv')
    assert len(cc)==len(cycles)==len(tr)==44;assert len(candidates)==60 and len(runs)==16
    assert len(calls)==466;assert sum(int(c['tokens']) for c in calls)==1140074
    assert sum(c['model_calls'] for c in cycles)+sum(int(c['cycle'])==0 for c in calls)==466
    assert sum(c['tokens'] for c in cycles)+sum(int(c['tokens']) for c in calls if int(c['cycle'])==0)==1140074
    for c in calls:
        assert int(c['input_tokens'])+int(c['output_tokens'])==int(c['tokens'])
        assert (ROOT/c['source_wire']).is_file()
    source_refs=set()
    for r in runs:
        t=a.load(ROOT/r['trajectory']);e=a.load(ROOT/r['evaluation'])
        assert len([s for s in t['steps'] if s['type']=='operator_selection'])==r['cycles']
        assert not t['verifier_evidence']
        assert r['final_score']==e['final']['score'] and r['c0_score']==e['candidates']['C0']['score']
        group=[c for c in cycles if c['experiment_version']==r['version'] and c['run_id']==r['run_id']]
        assert len(group)==r['cycles']
        for c,outcome in zip(group,t['operator_outcomes']):
            assert json.loads(c['internal_information_gain'])==outcome['information_gain']
            child=next(x for x in t['candidates'] if x['candidate_id']==c['outgoing_candidate_id'])
            assert child['parent_candidate_id']==c['incoming_candidate_id']
            assert c['outgoing_external_score']==e['candidates'][child['candidate_id']]['score']
            assert c['incoming_external_score']==e['candidates'][c['incoming_candidate_id']]['score']
            prompt=next(s for s in t['steps'] if s['step']==c['revision_prompt_source_step'])
            assert prompt['type']=='model_call' and prompt['data']['request']['purpose']=='revision'
            assert c['reported_progress'] is None if r['version']=='0.3.5' else c['reported_progress'] is not None
        source_refs.update((r['trajectory'],r['evaluation']))

    controls=[];manifests={}
    for pilot in a.PILOTS:
        m=a.load(ROOT/pilot/'manifest.json');manifests[pilot]={'engine':m['engine'],'model_identity':m['model_identity'],
            'model_settings':m['model_settings'],'historical_task_hashes':m['task_hashes'],'historical_evaluator_sha256':m['evaluator_sha256']}
        assert m['engine']['version']==('0.3.5.1' if pilot.startswith('v0351') else '0.3.5')
        main_trajectories=list((ROOT/pilot/'trajectories').glob('*.jsonl'))
        assert len(main_trajectories)==8
        for tid,sha in m['task_hashes'].items():
            path=ROOT/pilot/'tasks'/f'{tid}.json';assert a.sha(path)==sha
            original=ROOT/'benchmark_alpha/tasks'/f'{tid}.json';assert a.sha(original)==sha
            controls.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha,'role':'historical frozen task'})
        for path in (ROOT/pilot/'bench/evaluators.py',ROOT/'benchmark_alpha/bench/evaluators.py'):
            assert a.sha(path)==m['evaluator_sha256']
            controls.append({'path':path.relative_to(ROOT).as_posix(),'sha256':a.sha(path),'role':'frozen external evaluator; not executed in review'})
    assert manifests[a.PILOTS[0]]['historical_task_hashes']==manifests[a.PILOTS[1]]['historical_task_hashes']

    partial=[];partial_calls=[]
    for pilot in a.PILOTS:
        for log in sorted((ROOT/pilot/'incomplete_attempts').rglob('*.jsonl')):
            lines=[json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line.strip()]
            files=list(log.parent.rglob('*.json'))
            assert len(files)==len(lines)
            partial.append({'pilot':pilot,'run_id':log.stem,'call_log':log.relative_to(ROOT).as_posix(),
                'saved_responses':len(lines),'known_tokens':sum(c['input_tokens']+c['output_tokens'] for c in lines),
                'known_provider_latency_seconds':sum(c['latency_ms'] for c in lines)/1000,
                'next_started_call_without_response':len(lines)+1,'unknown_consumption':True,
                'full_engine_trajectory_available':False,'complete_cycle_count':None,'external_candidate_evaluations':None,
                'source_files':{f.relative_to(ROOT).as_posix():a.sha(f) for f in (log,*files)}})
            for c in lines:
                wire=next(f for f in files if f.stem==f"{c['seq']:04d}")
                w=a.load(wire);assert w['purpose']==c['purpose'] and w['seq']==c['seq']
                partial_calls.append({'pilot':pilot,'run_id':log.stem,'archive':log.parent.name,'seq':c['seq'],
                    'purpose':c['purpose'],'protocol_repair':c['protocol_repair_call'],'tokens':c['input_tokens']+c['output_tokens'],
                    'provider_latency_seconds':c['latency_ms']/1000,'wire':wire.relative_to(ROOT).as_posix(),
                    'completed_trial':False,'external_score':'UNKNOWN: not evaluated','cycle_outcome':'UNKNOWN: trajectory not persisted'})
    assert sum(x['saved_responses'] for x in partial)==18
    assert sum(x['known_tokens'] for x in partial)==21041 and len(partial)==3
    a.dump('INCOMPLETE_ATTEMPTS.json',partial);a.csvfile('PARTIAL_CALL_AUDIT.csv',partial_calls)
    (OUT/'INCOMPLETE_ATTEMPTS.md').write_text('''# Interrupted historical attempts: separately audited

Three archived call logs contain18 saved responses/21,041 reported tokens/463.146185s provider latency, plus3 next-started requests without responses/known consumption. They are not three extra completed trials and do not supply full Engine trajectories. Only the newer interrupted BA-001 attempt reaches saved critique/plan/revision/verification; post-revision quality/rollback/termination and external evaluations are absent. The completed44-cycle audit therefore does not invent an extra completed cycle.

INCOMPLETE_ATTEMPTS.json inventories every archive/hash; PARTIAL_CALL_AUDIT.csv links each saved physical response to its original wire file. Old RESUME_RECORD.json and new INTERRUPTION_NOTES.md corroborate missing terminal requests. Two partial BA-001 repair responses still use invalid IDs, alleging imaginary comma/whitespace defects; a revision/verifier follows. This is partial continuation evidence, not a terminal repair success or an improvement score. No partial output is reused as live inference or substituted into a completed trial. All unknown costs/outcomes remain unknown.
''',encoding='utf-8',newline='\n')

    required=['IMPLEMENTATION_REPORT_v0.3.5.2.md','REVISION_VALUE_AUDIT_v0352.md',
        'v035_core_regression_pilot/REPORT.md','v035_core_regression_pilot/MANUAL_REVIEW.md',
        'v0351_core_regression_pilot/REPORT.md','v0351_core_regression_pilot/MANUAL_REVIEW.md','benchmark_alpha/REPORT.md']
    for name in required:assert (ROOT/name).is_file()
    inventory=Counter(name.split('/')[0] for name in before)
    source_symbols={}
    for filename in source:
        if filename.endswith('.py'):
            tree=ast.parse((ROOT/filename).read_text(encoding='utf-8-sig'))
            source_symbols[filename]=[{'name':node.name,'line':node.lineno,'kind':type(node).__name__}
                for node in ast.walk(tree) if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))]
    manifest={'research_title':'END Cognitive Architecture Review v1: Why Does Deliberation Fail to Improve Candidates?',
        'date':'2026-10-11','baseline':base,'offline_tests':a.load(OUT/'offline-tests.json'),
        'authority':'Original runtime records and preexisting external candidate evaluations; current code inspected; manual research labels are non-production and scoped.',
        'analysis_method':{'scripts':['preflight.py','analyze.py','review.py','author_reports.py','validate.py'],
            'reproduction':'Run analyze/review, author_reports, validate using Python3.12 -B; do not rerun preflight over exclusive baseline snapshots.',
            'retrospective_evaluator_executions':0,'engine_imports_by_historical_data_extraction':0,
            'live_model_calls':0,'runtime_network_attempts':0,
            'network_guard':'Offline unittest discovery/run only: socket DNS/connect/connect_ex/sendto and urllib open blocked. Analysis uses standard-library local file reads/parsing and read-only Git; no provider/network APIs.',
            'topic_vs_defect':'Selected-topic grounding is separate from critique allegation, valid plan and child outcome.',
            'issue_equivalence':'Run-scoped IDs/normalized exact text; changed same-polarity Jaccard>=.72 is tentative reformulation; unknown identity retained; no semantic proof.',
            'content_equivalence':'Raw equality, historical answer-region equality, normalized text and syntax parsing as data; no candidate-code execution.',
            'manual_labels':'Task-specific reviewed rules in review.py; failure categories overlap, qualitative score omissions retained.',
            'packaging':'User-requested local Markdown/CSV overrides report-app publication route.'},
        'historical_pilots':manifests,'historical_population':{'completed_full_end_runs':16,'cycles':44,'candidates':60,
            'physical_calls':466,'tokens':1140074,'external_scores_missing':0,'token_records_missing_in_primary':0,
            'old_no_progress_records_missing':22,'interrupted_attempts_separate':partial},
        'research_inventory_file_counts':dict(sorted(inventory.items())),
        'required_documents':[{'path':name,'sha256':before[name]} for name in required],
        'task_evaluator_controls':controls,'source_files_sha256':source,'code_symbols':source_symbols,
        'primary_trial_trajectory_evaluation_hashes':a.load(OUT/'SOURCE_RECORD_HASHES.json'),
        'physical_call_sources_sha256':{c['source_wire']:before[Path(c['source_wire']).as_posix()] for c in calls},
        'protected_all_original_files_sha256':before,
        'protection_scope':'Every file outside architecture_review_v1 and .git; source, tasks, evaluators, historical validation/benchmark/reports, caches and unrelated local records preserved. Git HEAD/short status separately checked.',
        'missing_required_files':[],
        'notes':['Git HEAD identical across dirty releases is not source-version identity.',
                 'Manifest initial Ollama drift flag is superseded by newer REPORT/FINAL_AUDIT postflight warning; original manifest unchanged.',
                 'No END Harness path was read or modified.']}
    a.dump('SOURCE_MANIFEST.json',manifest)

    missing_links=[]
    for doc in OUT.glob('*.md'):
        text=doc.read_text(encoding='utf-8')
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
            target=(doc.parent/link.split('#')[0])
            if not target.is_file():missing_links.append((doc.name,link))
    # FINAL_VALIDATION is written below, so its explicit documentation link is expected now.
    missing_links=[x for x in missing_links if x[1]!='FINAL_VALIDATION.json']
    assert not missing_links,missing_links
    stats=a.load(OUT/'SUMMARY.json')
    assert sum(stats['selected_issue_assessments'].values())==44
    assert sum(stats['primary_revision_diagnoses'].values())==44
    assert sum(stats['issue_identity_classes'].values())==57
    assert sum(stats['finding_occurrence_grounding'].values())==57
    assert sum(d['activations'] for d in stats['operator_costs'].values())==44
    assert sum(d['associated_cycle_calls'] for d in stats['operator_costs'].values())==386
    assert sum(d['calls'] for d in stats['purpose_costs'].values())==466
    assert sum(d['tokens'] for d in stats['purpose_costs'].values())==1140074
    assert all(x['B_candidate']=='C0' for x in stats['counterfactuals'])
    required_outputs=['REPORT.md','CYCLE_AUDIT.csv','CANDIDATE_TRANSITIONS.csv','OPERATOR_VALUE.md',
        'REVISION_FAILURES.md','QUALITYGATE_CALIBRATION.md','COUNTERFACTUAL_ANALYSIS.md',
        'ARCHITECTURE_PROPOSALS.md','EXPERIMENT_PLAN.md','SOURCE_MANIFEST.json','LIMITATIONS.md']
    assert all((OUT/f).is_file() for f in required_outputs)
    # Syntax-check the research scripts by parsing, without pycache/Engine imports/inference.
    for script in OUT.glob('*.py'):ast.parse(script.read_text(encoding='utf-8'))
    assert source==p.source() and after==p.protected()
    final={'passed':True,'protected_file_count':len(before),'engine_source_entries':len(source),
        'protected_file_sets_identical':True,'protected_hashes_identical':True,'source_fingerprint':fingerprint,
        'source_unchanged':True,'historical_research_unchanged':True,'task_evaluator_unchanged':True,
        'git_head':head,'git_head_unchanged':True,'git_short_status_unchanged':True,
        'source_links_exist':True,'all_required_deliverables_exist':True,
        'completed_full_end_runs':16,'cycles':44,'candidates':60,'candidate_transitions':44,
        'physical_calls_historical':466,'tokens_historical':1140074,'new_external_evaluator_executions':0,
        'primary_candidate_scores_missing':0,'primary_usage_records_missing':0,'old_progress_missing':22,
        'interrupted_saved_responses_separate':18,'interrupted_known_tokens':21041,'interrupted_unknown_started_calls':3,
        'live_model_calls':0,'runtime_inference_network_calls':0,'offline_guard_attempts':a.load(OUT/'offline-tests.json')['network_attempts'],
        'live_benchmarks_executed':False,'no_commit_push_tag_publication':True,
        'research_writes_only':'architecture_review_v1/',
        'manual_review_checks':{'counterfactuals_labeled':True,'hypotheses_uncertain_not_established':True,
            'falsifiable_proposals':3,'future_matrix_runs':24,'future_physical_call_ceiling':136,
            'future_token_ceiling':400000,'future_active_wall_seconds_ceiling':10800,'future_experiment_executed':False},
        'warnings':['No live v0.3.5.2 evaluation','Four repeatedly inspected tasks/one trial per mode/version',
            'Ollama server drift timing unknown','Frozen external rubric/answer-region omissions',
            'Manual labels not causal proofs','Interrupted consumption incompletely observed']}
    a.dump('FINAL_VALIDATION.json',final)
    artifacts={f.name:a.sha(f) for f in OUT.iterdir() if f.is_file() and f.name!='ARTIFACT_HASHES.json'}
    a.dump('ARTIFACT_HASHES.json',artifacts)
    print(json.dumps({k:final[k] for k in ('passed','protected_file_count','engine_source_entries','source_unchanged',
        'historical_research_unchanged','task_evaluator_unchanged','git_head_unchanged','cycles','candidates','live_model_calls','runtime_inference_network_calls')}))

if __name__=='__main__':main()
