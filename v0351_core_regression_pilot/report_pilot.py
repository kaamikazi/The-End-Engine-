"""Frozen replay-only derived metrics. Never rescores or writes historical artifacts."""
from collections import Counter
import csv
import json
from pathlib import Path
import shutil

OUT=Path(__file__).resolve().parent
CONDITIONS=('DIRECT','FULL_END_STRUCTURED','FULL_END_NATIVE')
TASKS=('BA-001','BA-002','BA-008','BA-009')


def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def metrics(record,evaluation,trajectory=None):
    from end_engine.core.output_format import final_answer_region
    t=trajectory or {};calls=record['calls'];purposes=Counter(c['purpose'] for c in calls)
    judge=sum(purposes[p] for p in ('judgment','comparison','adversarial_judgment','adversarial_tests','blinded_external_judgment'))
    verifier=purposes['verification'];end=record.get('end') or {};events=t.get('protocol_events',[])
    actions=Counter(e['action'] for e in events);stats=t.get('repair_statistics',{})
    findings=[{'judgment_id':j['judgment_id'],'candidate_id':j['candidate_id'],'kind':kind,**issue}
              for j in t.get('judgments',[])+t.get('adversarial_judgments',[])
              for kind in ('fatal_issues','major_issues','minor_issues') for issue in j[kind]]
    final=evaluation['final'];c0=evaluation['candidates'].get('C0');delta=final['score']-c0['score'] if c0 else None
    selected=evaluation['candidates'].get(end.get('returned_candidate_id'))
    c0_text=next((c['content'] for c in t.get('candidates',[]) if c['candidate_id']=='C0'),'')
    cycles=end.get('iterations',0);output=t.get('output_integrity',{})
    row={'run_id':record['run_id'],'task':record['task_id'],'condition':record['condition'],
         'external_score':final['score'],'passed':final['passed'],'format_ok':final['format_ok'],
         'wall_seconds':record['cost']['wall_ms']/1000,'total_model_calls':record['cost']['calls'],
         'generator_calls':len(calls)-judge-verifier,'judge_calls':judge,'verifier_calls':verifier,
         'protocol_repair_calls':sum(c.get('protocol_repair_call',False) for c in calls),
         'transport_retry_calls':sum(c['attempt']>1 for c in calls),'revision_calls':purposes['revision'],
         'tokens':record['cost']['total_tokens'],'known_partial_tokens':record['cost'].get('known_partial_tokens'),
         'prompt_tokens':record['cost']['prompt_tokens'],'output_tokens':record['cost']['completion_tokens'],
         'end_cycles':cycles,'calls_per_completed_cycle':len(calls)/cycles if cycles else None,
         'stop_reason':end.get('termination'),'quality_gate':end.get('quality_gate'),'acceptance_label':end.get('acceptance_label'),
         'external_blocker':end.get('termination')=='EXTERNAL_BLOCKER','model_protocol_failure':end.get('termination')=='MODEL_PROTOCOL_FAILURE',
         'execution_error':bool(record.get('error')),'repair_attempted':stats.get('repair_attempted',0),
         'repair_succeeded':stats.get('repair_succeeded',0),'repair_failed':stats.get('repair_failed',0),
         'repair_suppressed':stats.get('repair_suppressed',0),'invalid_elements_discarded':stats.get('invalid_elements_discarded',0),
         'calls_saved_by_suppression':stats.get('calls_saved_by_suppression',0),
         'repair_attempts':stats.get('repair_attempted',0),'repair_successes':stats.get('repair_succeeded',0),
         'discarded_protocol_elements':stats.get('invalid_elements_discarded',0),
         'rollback_count':len(end.get('rollback_events',[])),'c0_score':c0['score'] if c0 else None,
         'c0_format_ok':c0['format_ok'] if c0 else None,'c0_chars':c0['answer_chars'] if c0 else None,
         'c0_final_region_chars':len(final_answer_region(c0_text).strip()) if c0 else None,
         'final_chars':final['answer_chars'],'final_region_chars':len(final_answer_region(record['answer']).strip()),
         'selected_candidate_score':selected['score'] if selected else None,
         'score_delta':delta,'revision_value':('IMPROVED' if delta>0 else 'REGRESSED' if delta<0 else 'NEUTRAL') if delta is not None else None,
         'output_withheld':bool(output.get('blocked')),'output_integrity':output,'truncated_calls':record['cost']['truncated_text_answers'],
         'internal_leakage':sum(bool(c.get('internal_leakage')) for c in t.get('engine_checks',[])),
         'unsupported_claim_count':final['counters']['unsupported_claim_count'],
         'grounding_incidents':len(t.get('judge_groundings',[])),
         'decisive_judge_findings':sum(i.get('decisive',True) for i in findings),
         'nondecisive_judge_findings':sum(not i.get('decisive',True) for i in findings),
         'candidate_progression':evaluation.get('candidates',{}),'judge_findings':findings,
         'grounding_records':t.get('judge_groundings',[]),'protocol_events':events,
         'repair_statistics':stats,'repair_outcomes':t.get('repair_outcomes',[]),
         'epistemic_checks':t.get('epistemic_checks',[]),'cycle_progress':t.get('cycle_progress',[]),
         'no_progress_cycles':t.get('no_progress_cycles',0),'no_progress_stop':t.get('no_progress_stop',False),
         'mandatory_action_overrides':sum(bool(c['blockers']) for c in t.get('cycle_progress',[])),
         'operator_sequence':[s['data']['operator'] for s in t.get('steps',[]) if s['type']=='operator_selection'],
         'overthinking_signals':(evaluation.get('analysis') or {}).get('overthinking',[]),
         'error_records':record.get('error') or end.get('errors',[])}
    assert row['generator_calls']+judge+verifier==row['total_model_calls']
    return row


def summarize():
    from .run_pilot import write_json
    if not (OUT/'manifest.json').exists():return
    manifest=load(OUT/'manifest.json');rows=[];pending=[]
    for path in sorted((OUT/'trials').glob('*.json')):
        record=load(path);evpath=OUT/'evaluations'/path.name
        if not evpath.exists():pending.append(record['run_id']);continue
        evaluation=load(evpath);trajectory=load(OUT/'trajectories'/record['end']['trajectory_file']) if record.get('end') else None
        row=metrics(record,evaluation,trajectory);rows.append(row);write_json(OUT/'diagnostics'/path.name,row)
        if (not row['passed'] or row['output_withheld'] or row['grounding_incidents'] or row['repair_attempted']
                or row['repair_suppressed'] or row['no_progress_stop'] or row['overthinking_signals']):
            archive=OUT/'failures'/record['run_id'];archive.mkdir(parents=True,exist_ok=True)
            for source,name in ((path,'trial.json'),(evpath,'evaluation.json'),(OUT/'diagnostics'/path.name,'diagnostics.json')):
                if not (archive/name).exists():shutil.copyfile(source,archive/name)
            write_json(archive/'reference.json',{'trajectory_file':(record.get('end') or {}).get('trajectory_file'),
                'wire_directory':'../../wire/'+record['run_id'],'safety_withheld':row['output_withheld']})
    bulky={'candidate_progression','judge_findings','grounding_records','protocol_events','repair_statistics',
           'repair_outcomes','epistemic_checks','cycle_progress','operator_sequence','overthinking_signals','error_records','output_integrity'}
    fields=[k for k in rows[0] if k not in bulky] if rows else ['run_id','task','condition','external_score']
    with (OUT/'results.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    aggregate={}
    for condition in CONDITIONS:
        group=[r for r in rows if r['condition']==condition]
        keys=('wall_seconds','total_model_calls','judge_calls','verifier_calls','revision_calls','protocol_repair_calls',
              'repair_attempted','repair_succeeded','repair_failed','repair_suppressed','invalid_elements_discarded','end_cycles')
        aggregate[condition]={**{k:sum(r[k] for r in group) for k in keys},'runs':len(group),'passed':sum(r['passed'] for r in group),
            'mean_external_score':sum(r['external_score'] for r in group)/len(group) if group else None,
            'tokens':sum(r['tokens'] for r in group) if all(r['tokens'] is not None for r in group) else None,
            'output_withheld':sum(r['output_withheld'] for r in group),'no_progress_stops':sum(r['no_progress_stop'] for r in group)}
    historical=load(OUT/'historical_v035_reference.json')
    summary={'experiment':manifest['experiment'],'status':manifest['status'],'planned':12,'completed':len(rows),
             'incomplete_evaluations':pending,'failed_executions':sum(r['execution_error'] or r['external_blocker'] or r['model_protocol_failure'] for r in rows),
             'failed_external_outcomes':sum(not r['passed'] for r in rows),'total_wall_seconds':sum(r['wall_seconds'] for r in rows),
             'total_model_calls':sum(r['total_model_calls'] for r in rows),
             'total_tokens':sum(r['tokens'] for r in rows) if all(r['tokens'] is not None for r in rows) else None,
             'aggregates':aggregate,'runs':rows,'jev_calls':0,'typesafe_calls':0,'gemini_calls':0,'cloud_calls':0,
             'FULL_END_revision_values':dict(Counter(r['revision_value'] for r in rows if r['condition']!='DIRECT')),
             'safety_withheld':sum(r['output_withheld'] for r in rows),'historical_v035_aggregates':historical['aggregates'],
             'historical_v035_repair_attempts':sum(r['repair_attempts'] for r in historical['runs']),
             'historical_v035_repair_successes':sum(r['repair_successes'] for r in historical['runs']),
             'limitations':['Four tasks, one trial per condition; diagnostic only','Same three-cycle cap and exposed seeds; sampling noise remains',
                'Same model generates and judges; external scoring only certifies encoded checks',
                'Safety withholding and selected-candidate/raw scores are distinct from returned-answer task quality',
                'Known frozen BA-008 premise regex can miss Markdown corrections; no score adjustments']}
    write_json(OUT/'summary.json',summary)
    lines=['# v0.3.5.1 Core Regression Pilot Replay','',
        '## Purpose and limitations','',*['- '+s for s in summary['limitations']],'',
        '## Preflight','',f"Engine {manifest['engine']['version']}; fingerprint `{manifest['engine']['source_sha256']}`; offline tests {manifest['engine']['offline_tests']['tests']} passed.",
        f"Model `{manifest['model_identity']['name']}`, digest `{manifest['model_identity']['digest']}`, Ollama {manifest['model_identity']['server_version']}. Defaults untouched; baseline decisions only.",
        'All task/evaluator/source hashes, generation settings and seeds are recorded in manifest.json before inference.',
        '', '## Run status','',f"{manifest['status']}: {len(rows)}/12 completed; execution failures {summary['failed_executions']}; external failures {summary['failed_external_outcomes']}.",
        '', '## Task results','', '| Task | DIRECT | STRUCTURED | NATIVE |','|---|---:|---:|---:|']
    for task in TASKS:
        parts=[]
        for condition in CONDITIONS:
            r=next((r for r in rows if r['task']==task and r['condition']==condition),None)
            parts.append(f"{r['external_score']:.4f} / {'Pass' if r['passed'] else 'Fail'}" if r else 'NOT RUN')
        lines.append('| '+task+' | '+' | '.join(parts)+' |')
    lines+=['','## C0 to returned answer','', '| Run | C0 | Final | Delta/class | Selected raw | Withheld | Cycles | Gate / stop |',
            '|---|---:|---:|---|---:|---|---:|---|']
    for r in rows:
        if r['condition']!='DIRECT':lines.append(f"| {r['run_id']} | {r['c0_score']} | {r['external_score']} | {r['score_delta']} / {r['revision_value']} | {r['selected_candidate_score']} | {r['output_withheld']} | {r['end_cycles']} | {r['quality_gate']} / {r['stop_reason']} |")
    lines+=['','Candidate progression, formats and raw/final-region lengths are retained in diagnostics/*.json and results.csv. The frozen evaluator scores the actual returned answer, including empty withheld output.',
        '', '## Before/after costs and mechanisms','', '| Condition | v0.3.5 calls / tokens / seconds | v0.3.5.1 calls / tokens / seconds |','|---|---|---|']
    for c in CONDITIONS:
        a=historical['aggregates'][c];b=aggregate[c];lines.append(f"| {c} | {a['model_calls']} / {a['tokens']} / {a['wall_seconds']:.3f} | {b['total_model_calls']} / {b['tokens']} / {b['wall_seconds']:.3f} |")
    lines+=['','Totals: '+str(summary['total_model_calls'])+' actual attempts; '+str(summary['total_tokens'])+' tokens; '+f"{summary['total_wall_seconds']/3600:.3f} completed-trial hours.",
        '', 'Descriptive costs only; no causal savings or general superiority claim. Interrupted attempts, if any, are preserved separately and require additional accounting.',
        '', '## Repair, output integrity and no-progress observations','']
    for r in rows:
        if r['condition']!='DIRECT':lines.append(f"- {r['run_id']}: attempted/succeeded/failed/suppressed={r['repair_attempted']}/{r['repair_succeeded']}/{r['repair_failed']}/{r['repair_suppressed']}; discarded={r['invalid_elements_discarded']}; no-progress={r['no_progress_cycles']}/{r['no_progress_stop']}; withheld={r['output_withheld']}.")
    lines+=['','All stage failures, suppression activations, cycle progress reasons/blockers and extracted epistemic checks are retained in trajectories and diagnostics. Exact saved token counts are unknown.',
        '', '## Manual mechanism verdicts and hostile review','',
        'See MANUAL_REVIEW.md. Final verdicts require all eight FULL_END trajectories; task pass alone is not mechanism success.',
        '', '## Historical immutability','', 'Hash snapshots are in preflight/protected-before.json; FINAL_AUDIT.json verifies the final state. No old output is replayed as a new model response.',
        '', '## Recommendation','', 'Pending completed diagnostic and all manual reviews. No larger experiment is automatically launched.']
    if (OUT/'INTERPRETATION.md').exists():lines+=['','## Final interpretation','',(OUT/'INTERPRETATION.md').read_text(encoding='utf-8')]
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return summary
