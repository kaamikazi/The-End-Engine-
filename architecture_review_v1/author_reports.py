"""Author requested local research documents from reconciled saved records only."""
import json
import csv
from pathlib import Path
from collections import Counter
import analyze as a

OUT=a.OUT
S=a.load(OUT/'SUMMARY.json');C=a.load(OUT/'CYCLES.json');R=a.load(OUT/'RUNS.json')
with (OUT/'CALL_AUDIT.csv').open(encoding='utf-8',newline='') as stream:CALLS=list(csv.DictReader(stream))

def write(name,text):
    (OUT/name).write_text(text.strip()+'\n',encoding='utf-8',newline='\n')

def table(headers,rows):
    def cell(v):return str(v).replace('|',' / ').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(cell(x) for x in r)+' |\n' for r in rows)

def ref(r):return f"[{r['trajectory'].split('/')[-1]}](../{r['trajectory']})"

write('REPORT.md',f'''
# END Cognitive Architecture Review v1
## Why Does Deliberation Fail to Improve Candidates?

Read-only research, 2026-10-11. **Recommendation D: pause architecture development pending better evaluation.** This does not mean the historical failures are unexplained: unsupported issue inputs, invalid repair prescriptions, lost requirements and inaccurate comparisons are directly observable. It means these small, contaminated historical samples do not identify a dominant causal bottleneck or establish which production architecture to change next. The three proposed alternatives are hypotheses, not implementations or demonstrated improvements.

### Baseline and evidence authority

Actual Engine **0.3.5.2**, Python **3.12.14**, source fingerprint **29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82** over 70 Engine Python/pyproject entries. Git main, HEAD **6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7**, extensive pre-existing dirty work. [BASELINE.json](BASELINE.json), [git-status-before.txt](git-status-before.txt).

The guarded equivalent of `python -B -m unittest discover -s tests -t .` discovers **303 tests: 0 failures, 0 errors, 0 skipped, 0 runtime network attempts**, 21.975 seconds. [preflight.py](preflight.py) redirects temporary test fixtures into this review, disables bytecode and blocks DNS/socket/urllib runtime networking. [offline-tests.json](offline-tests.json), [complete test log](offline-tests.txt). Mock/scripted provider calls in offline tests are not live inference. These tests constrain behavior; they do not establish reasoning improvement.

Live observations below concern **v0.3.5 and v0.3.5.1 only**. v0.3.5.2 has no new live evaluation. Historical source fingerprints are recorded in the pilot manifests; Git HEAD alone cannot identify these dirty-tree versions. Both pilots use qwen3:4b, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`, temperature .7, top_p .8, prediction cap 4096, context 8192, think=false, timeout 900s. The newer pilot's server changed from .35.1 to .40.0 at an unknown time. Seed equality is not output equality. [old manifest](../v035_core_regression_pilot/manifest.json), [new report](../v0351_core_regression_pilot/REPORT.md).

Historical [Benchmark Alpha](../benchmark_alpha/REPORT.md) is context, not part of the44-cycle denominator: v0.3.4,96 completed trials (12 tasks×4 conditions×2 trials), stopped short of144 planned.22/24 FULL_END runs terminate as then-labelled EXTERNAL_BLOCKER, chiefly protocol/reference failures; only8 FULL_END cycles complete. FULL_END passes8/24 with mean score .3646, versus DIRECT15/24/.6458 and SELF_REFLECT16/24/.7738. Protocol failures, output truncation, differing conditions and narrow scoring prevent assigning this gap solely to cognition. Later pilots demonstrate completed cycles, but no encoded C0 improvement. Synthetic Beta/Jev validation records remain preserved; they supply no new empirical evidence here.

### Audited population and outcomes

Every completed FULL_END trial in both pilots is included, without outcome sampling: four already-inspected tasks × two generation modes × one trial × two versions. DIRECT trials and interrupted archives are contextual evidence, outside the primary denominator. All **60 candidate external evaluations already exist**; none was newly run, corrected or substituted. Scores remain the frozen rubric's observations, not complete answer truth.

{table(['Population','Runs','Cycles','Candidates','Calls','Tokens','Run wall seconds'],[
['v0.3.5 FULL_END',8,22,30,233,'565,936','5,849.980010'],
['v0.3.5.1 FULL_END',8,22,30,233,'574,138','9,443.811153'],
['Combined primary',16,44,60,466,'1,140,074','15,293.791163']])}

The 44 actual parent→child transitions have **0 encoded score improvements, 1 encoded regression and 43 equal scores**. Final versus C0: **0/16 improved, 15/16 equal, 1/16 regressed**; within each pilot, 0/8 improved. Mean C0 score .71875, actual final .6875. **10/16 C0s already score 1**, leaving only six runs with encoded headroom. There is no hidden higher-scoring generated candidate: the retrospective score oracle chooses C0 (tie preference) in every run. Zero newly executed evidence artifacts are present in the 16 runtime traces.

[CYCLE_AUDIT.csv](CYCLE_AUDIT.csv) contains every cycle, exact critique/plan/verifier/judgment records, prompt/wire references, selected-topic classification, missingness, incoming/child/effective candidates and cost. [CANDIDATE_TRANSITIONS.csv](CANDIDATE_TRANSITIONS.csv) retains overlapping score/content/format/safety dimensions. [CANDIDATE_CALIBRATION.csv](CANDIDATE_CALIBRATION.csv) covers all 60 candidates; [CALL_AUDIT.csv](CALL_AUDIT.csv) reconciles all 466 physical calls with trajectory steps and raw wire files. The 80 pre-cycle calls include 16 initial generations and 64 assessments; they are not 80 generations. Cycles account for 386 calls.

### What fails in the observable chain

1. **A check topic is mistaken for a demonstrated defect.** New BA-001 structured C0 is correct, yet completeness/misassignment objections and plans recur for three cycles. BA-002's repaired loop and guards are repeatedly confused with original buggy code. Positive statements such as 'the claim is supported' are stored as low-severity weaknesses. A selected sorting requirement can be legitimate while the ensuing critique incorrectly elevates the task's factual premise. The research labels deliberately distinguish these objects. [issue/operator audit](OPERATOR_VALUE.md), all per-cycle references below.
2. **Useful discovery does not guarantee a valid repair.** Old BA-009 recognizes evidence/uncertainty problems, but invalid target IDs cause usable changes to be discarded after failed repairs. New native BA-009 cycle 1 receives a valid Engine instruction to qualify unsupported establishment; C1 ignores it. Cycle 2's model plan places an unavailable-metrics statement in `evidence_used`, producing an undeclared ID. Structured plans ask for observations explicitly absent from the task. No acquisition mechanism exists. [revision audit](REVISION_FAILURES.md).
3. **Generation and selection lose satisfied requirements.** New BA-008 native C0 scores 1, C1 removes the requested explanation and scores .5. Plans call for clarification, not deletion; comparison imagines the explanation or reports no material gain/loss, and final selection retains C1. Old BA-008 has the same qualitative loss hidden by the frozen Markdown-sensitive regex. This is bad generation and failure to preserve C0; it is not evidence that an improved revision was generated then discarded. [selection calibration](QUALITYGATE_CALIBRATION.md).
4. **More state is not necessarily more knowledge.** Of 57 ingested critique-finding occurrences, 28 are exact normalized repeats, one a cautious reformulation, 22 new lexical proposals and six unresolved identity cases. These are not 57 proven defects. Thirty transitions have unchanged raw or historical answer regions; their cycles consume 256 calls/590,742 tokens. Model-derived checks and branches add opinions/hypotheses without new executed evidence. [cost](COST_AND_TERMINATION.md).

The current code addresses several integrity routes in the historical chain: shared assessment authority, actual answer scope, plan origins, reference deltas and filtered progress. Its operator utility still uses advisory severity and a bookkeeping-derived information-gain proxy. That is a testable risk, **not a live v0.3.5.2 failure observation**. The default baseline call ceiling is None, while finite cycle/operation caps remain; a future experiment must set an explicit shared call ceiling. [actual loop A–J](COGNITIVE_LOOP.md), [current implementation record](../IMPLEMENTATION_REPORT_v0.3.5.2.md).

### Competing bottlenecks, ranked by evidential support

Counts overlap and are diagnostic coverage, not attributable causal fractions. Ranking reflects directly observed mechanisms before unobserved model/generalization explanations. None proves exclusive causation.

{table(['Rank / hypothesis','Supporting evidence / potentially explained observations','Evidence against / uncertainty','Small discriminating test'],[
['1 H6 no new evidence','0 executed artifacts across 44 cycles; BA-009 metric gap never filled','Arithmetic/code repair can improve without new world observations. Absence of receipts does not prove all reasoning valueless.','Give finite failing checks to B versus same tasks without checks; measure grounded repairs.'],
['2 H1 issue discovery','18/44 primary BAD ISSUE diagnoses; 28/57 repeated findings; false completeness/guard/premise criticisms','Useful BA-009 gaps coexist; 22/44 selected topics are plausible, not demonstrated errors. BAD ISSUE labels concern critiques, not all topics.','Blindly adjudicate proposed defects and novelty against candidate/task before viewing final outcomes.'],
['3 H3 planning','11/44 primary GOOD ISSUE BAD PLAN; empty salvaged plans and unavailable-metric/citation actions','Malformed IDs are protocol rather than conceptual planning failures; structured real JSON repair overlaps generation.','Hold a grounded issue fixed; compare explicit bounded delta with model-derived plan.'],
['4 H9 protocol/format','16 repairs (old12 failed; new4 with3 success), old BA-009 empty plans; all8 structured BA-009 candidates lack JSON','Most runs finish; native failures persist without candidate JSON envelope. Historical delimiter/evaluator errors confound scoring.','Freeze authoritative answer span and runtime contracts; separate repair failure from repair quality.'],
['5 H7 overdeliberation','24/44 transitions enter from score1 candidates; first new BA-008 native cycle loses .5; 30 unchanged transitions','Only one encoded loss. Later native BA-009 cycle lowers certainty. Unknown longer-horizon benefits.','Preserve C0 with A unless bounded actionable failure exists; compare safety and improvement, not just cost.'],
['6 H4 generation','7/44 primary GOOD PLAN BAD GENERATION: six native BA-008 cycles and first new native BA-009','Other plans are invalid/empty, so failures cannot be assigned to generation. Preservation wording alone is not a perfect plan.','Supply identical independently adjudicated valid repair objectives across repetitions.'],
['7 H5 evaluation','12 REJECT gates on externally passing candidates; new passing C0 lost; unsupported fatal/confident claims','0 externally better child exists to be missed; rubric omits type/prose safety. Thus strong better-child hypothesis unsupported.','Measure pairwise choice against hidden quality/safety annotations and independently scored candidates.'],
['8 H2 utility','44 activations, no encoded gain; EVIDENCE15 and VERIFY13; utility learns internal activity proxies','No randomized operator intervention; poisoned issue input can explain apparently bad selection.','Match issue eligibility, randomize selector only; measure valid novel findings and downstream delta.'],
['9 H8 model capability','Same4B generator/judges; factual confusion, invalid IDs, instruction failures','Direct/C0 solve many tasks. No stronger-model contrast; server drift and sampling remain.','Only after protocol/task freeze, separately authorized model-factor comparison with digest/settings held per cell.']])}

### Recommendation and roadmap

**D** is the only recommendation. A requires demonstrated useful candidate improvement that is absent here. B requires generally useful issue discovery, which these traces do not establish beyond narrow cases. C requires most failures to originate upstream, but the conservative primary BAD ISSUE count is 18/44, not a majority; 11 plan failures and seven execution failures coexist, and stages overlap. Historical integrity fixes also mean the old observations cannot select a current production redesign confidently. D is a decision under uncertainty, not a claim of no architectural knowledge.

Next action: **freeze and independently review two fresh diagnostic tasks and their external scoring/safety contracts, including a deliberate passing-C0 case and a repairable failing case, before authorizing any experimental adapter or live request.** They must not be BA-001/002/008/009 variants with merely changed numbers. Establish that the rubric detects missing explanations, malformed output, unsupported certainty and undeclared citations; report any unmeasurable semantics. No task/evaluator is created in this investigation.

[ARCHITECTURE_PROPOSALS.md](ARCHITECTURE_PROPOSALS.md) specifies A sparse gating, B evidence/constraint repair and C bounded alternatives in 15 dimensions each. [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) specifies the future **24-run matrix**, physical ceiling **136 calls**, **400,000 tokens** and **3 hours** total, resumable but without budget reset. Historical purpose-weighted projection: ~273,440 tokens/~101 minutes before repair/overhead margin; completion is not guaranteed. It requires separate implementation and live-inference authorization. It is **NOT EXECUTED**.

### Trace index: every FULL_END run

{table(['Version','Run','Cycles','Actual parent→child lineage','C0 / returned score','Returned ID','Source'],[[r['version'],r['run_id'],r['cycles'],', '.join(f"{c['incoming_candidate_id']}→{c['outgoing_candidate_id']}" for c in C if c['experiment_version']==r['version'] and c['run_id']==r['run_id']),f"{r['c0_score']} / {r['final_score']}",r['returned'],ref(r)] for r in R])}

### Limitations and validation

[LIMITATIONS.md](LIMITATIONS.md) records ceiling effects, tiny correlated sample, unavailable independent evidence, observer/task contamination, rubric omissions, incomplete interrupted costs, version drift, unobserved counterfactual branches and the separation between historical findings and current code. [COUNTERFACTUAL_ANALYSIS.md](COUNTERFACTUAL_ANALYSIS.md) labels saved-output comparisons, oracle choice and policy-dependent unknowns.

All writes are confined to this review. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) inventories original source/records/task/evaluator hashes, source roles and analysis provenance. [FINAL_VALIDATION.json](FINAL_VALIDATION.json) checks whole-workspace file-set/hash preservation outside the review, Engine fingerprint, task/evaluator identity, CSV/source references and totals. No Engine/Harness/task/evaluator/prompt/config edit, version bump, commit, push, publication, model inference or live benchmark was performed.
''')

write('COGNITIVE_LOOP.md','''
# Actual cognitive loop: A–J

This reconstructs current v0.3.5.2 code. Historical pilots ran earlier dirty-tree versions: only saved requests/events establish their exact behavior. The loop is not strictly the conceptual diagram: initial verification and quality feedback happen **before the first operator selection**; every child is assessed before another operator; rollback can make the next child a sibling rather than a descendant of the latest candidate.

Code anchors: `end_engine/engine.py:99` (run), `:501` (structured/native generation), `:544` (critique recovery), `:612` (plan); `cognition/session.py:47,78` (state and gain); `cognition/policy.py:16` (utility); `core/weaknesses.py:9` (register); `core/revision_planner.py:10`; `quality/session.py:59,342,354,450` (assessment/restore/reconcile/finalize); `quality/gate.py:10`; `core/progress.py:31,44`; `core/termination.py`; `models/recording.py`; `experience/schema.py`; `experience/ledger.py`. Paths are relative to repository root; exact hashes are in SOURCE_MANIFEST. Historical step intervals and request paths are in CYCLE_AUDIT.

| Stage | A: inputs | B: genuinely new information possible | C: reinterpretation/repetition | D: candidate effect | E: internal-state effect | F: validation | G: inference | H: contamination risk | I: skip/repeat | J: without independent verification? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task and analysis | Original task, caller TaskContract, config/overrides | Explicit requirements; external data only if actually supplied | Heuristic complexity/dimensions; descriptive assertions remain assertions | None | Budget/coverage and task provenance | Types, finite contracts; optional LLM classification schema | Default 0; optional classifier call | Mistaking assertion for truth or requirement can poison all later checks | Once/run; mode/cycle override; fast analysis reduces cognition | Yes: classification is not truth validation |
| C0 generation | Native original task alone; structured task+generation instructions | Candidate solution; potentially valid new derivation | Prior model beliefs and task premises | Creates C0, raw and authoritative answer span | Lineage/strengths/confidence and Engine check | Schema for structured; nonempty native; answer-boundary parser and finite format checks | 1 plus bounded structured repair when triggered | Bad C0 becomes the referent for extraction and critique | Once; invalid output may terminate or repair | Yes |
| Candidate observation / CognitiveState | Actual answer, registry, score history, branches, knowledge | Extracted propositions and unresolved constraints, not verified world facts | Sentence/claim extraction and risk/coverage summaries | None | Claims, assumptions, current IDs, weakness snapshots, stagnation | Bounded IDs/enums; policy screens model promotions | 0 | Extraction can select filler; new IDs or coverage can overstate information | Non-fast candidate observation; state reconstructed multiple times | Yes |
| Initial/child verification | Task, inspected answer, recorded weaknesses and previous check | Trusted configured rules/tools can produce scoped finite results; LLM produces assessment | Same-model checking is another opinion | None | Verification score/issues/status proposals | Schemas and shared authority policy; BasicRules is limited; trusted tools use exact contracts | Historical LLM: 1/candidate; rules 0 model calls; tool collection separate | Unsupported negative or positive may distort risk/stop if authority boundary fails | Every newly assessed candidate; restore uses cached candidate-bound result | LLM yes; executed claims require actual checks |
| Quality issue discovery | Candidate, task, claims, proposed adversarial tests, optional tool evidence | Executed checker evidence when configured; finite output/reference violations | Primary/adversarial judge opinions, generated scenarios | None | Feedback weaknesses, judgments, claim validations, status audits | Schema/IDs, assessment policy, candidate/evidence scope, transition audits | Historical test generator+primary+adversary =3/candidate; optional secondary adds1; tool cost additional | Quotes do not prove defects; same model is not independent epistemic evidence | Quality session enabled by config or judge provider; cache by candidate ID | Yes for model discovery; no for earned execution authority |
| Operator selection | State, advisory/decisive weaknesses, claims/assumptions, coverage/history/budget | A new question/priority choice; no external observation | Predicted utility from bookkeeping gain, heuristic relevance/severity/repetition | None | Selected target, utility factors, used-operator sequence | Known operator/target types and finite utility factors; not quality calibrated | Baseline utility 0; optional LLM selector/decision routing adds calls | Advisory severity can dominate exploration; measured activity rewards may self-reinforce | After nonterminal assessment; explicit overrides; repetition/cost penalties; operations cap | Yes |
| Operator execution | Concrete question, task, inspected candidate, weakness/knowledge context | A new proposed defect, derivation or alternate hypothesis | Restatement/reframing of existing claims | Operator never rewrites candidate | Findings/claim/assumption proposals, dedup and coverage | Critique schema, reference salvage, shared authority; no independent semantic oracle | 1 critique plus max1 targeted repair per attempt subject to failure policy | Plausible criticism can become an inappropriate revision target; unsupported remains advisory currently | Once/selected cycle; recovery/suppression; can repeat IDs | Yes |
| Register / gain accounting | Normalized critique, pre-existing IDs, knowledge changes | Recorded state change; valid finite issue only when justified | Lexical ID reuse/rewriting; model support statements | None | Open/reopened weaknesses, occurrences, gain HIGH/MEDIUM/LOW/ZERO | ID/state validation; advisory cannot overwrite scoped validated concern | 0 | New IDs/knowledge changes/viable branches still feed gain; not independent information measure | Each critique; restore rolls back candidate state, history remains | Yes; current decisive flags restrict downstream authority, not exploratory utility |
| Branch exploration | Branch-capable operator, unresolved candidate, budget | Distinct alternative solutions/hypotheses; not new observations | Model branch scores and synthesis proposals | No candidate mutation until later generation from plan | ACTIVE/PROMISING/MERGED/REJECTED/EXHAUSTED branches and operation usage | Branch IDs/depth/goal/schema/adoption; rejected branch not imported | Branch generation + each branch evaluation + synthesis; actual historical 4 calls/search cycle | Invented causal stories/measurements or synthesis authority | Only eligible deep/critical search with capacity; bounded count/depth; failure skips locally | Yes |
| Revision planning | Task, inspected parent, critique, open weaknesses, optional synthesis/reframe | A proposed corrective action; Engine may append finite status/reference correction | Model restatement of issue and suggested effect | None directly | Labelled Change records and targeted IDs | Plan schema/existing IDs/salvage; origin hierarchy; bounded conflict screen | 1 plus max1 targeted repair; Engine appended changes 0 | Impossible metrics or fabricated citation requests can poison child; model plan is never a user command | Every completed cycle; empty salvage triggers generic rewrite; Engine correction survives invalid model targets | Yes, so plan validity is separate from protocol validity |
| Revision generation | Original task, actual parent answer, labelled changes | New candidate attempt; valid repair if model succeeds | Same answer/prose or repeated uncertain causal story | Creates child Cn with actual parent; all satisfied requirements requested to remain | Candidate snapshot, actual answer/claims, finite checks | Same generation/format/answer-boundary validation as C0; reference/status delta later | 1 plus bounded repair in structured mode | Lost explanation/format; invented facts or authority; irrelevant rewrites | Every cycle that reaches generation; optional budget interruption | Yes |
| Child judgment / comparison | Child, anonymous parent A/child B, task, optional trusted evidence | Candidate-bound checks and observed local deltas; opinions remain advisory | Repeated verification/judging and comparative confidence | None | Gate, comparison, audits, integrity cache | Same authority/scope checks; compare schema does not guarantee correct preference | Verify+tests+2 judges; comparison1, another if best differs from parent; local trajectory audit0 | Comparator can hallucinate retained explanation; rank may hide quality/safety differences | Each uncached child; cache avoids reassessing same ID, not identical text with new ID | Yes for opinions; verified acceptance requires scoped executed support |
| Gate / best / rollback | Candidate-bound assessment, finite checks, register, support and branch state | Decision about admissibility within recorded scope | Gate ranks REJECT0/BLOCKED1/REVISE2/provisional3/verified4; advisory comparison tie choice | Chooses best; may restore earlier candidate as current | Candidate-specific state restored; history retained and applicable later concerns reconciled | Mandatory constraints, failed checks, scope/authority restrictions; no external rubric | 0 beyond recorded comparisons | Wrong assessment/tie preference can preserve poorer answer; rollback is not a quality oracle | Rejection or decisive severe regression can rollback; final selects best then reconciles | Provisional yes; verified no unsupported confidence alone |
| Termination / final guard | Gate/verification, budgets, progress/blockers, original lineage and selected candidate | Stop cause and uncertainty; finite final reference/status/leakage check | Internal stagnation/coverage heuristics | Returns best actual answer or withholds unresolved integrity violation | Termination, latest/best IDs, output-integrity and acceptance labels | Hard cycle/operation/call caps, mandatory blockers, scoped final guard | 0 | False progress can extend loop; false blockers protect unnecessary work; safe withholding can reduce usefulness | Loop repeats until acceptance/budget/no-progress/other; cap precedence and mandatory actions matter | Yes to stopping; stopping never creates verification or acceptance |
| Recording/accounting | Detached requests/responses/tool calls, reported usage, errors, wall clock | Auditable receipts of actual calls and state transitions | Serialization/summaries | None | Steps, physical call IDs, errors, usage and atomic ledger file | Deep copies, JSON schema/finite values; reserved shared budgets | 0 extra model calls | Missing provider usage stays missing; honest recording does not validate answer truth | Every attempted call, including repairs/errors; final atomic save | Yes |

The 16 historical FULL_END runs used no trusted tool verifier. Consequently the possible independent-information branch in this table was not exercised. The 44 operator activations create proposed findings/questions, not independent observations; new derivations could still be useful, but encoded improvements are absent in this sample. Current v0.3.5.2 authority checks filter how opinions affect gate/progress; they do not turn utility/gain into an external quality metric.
''')

op_descriptions={
'EVIDENCE':('epistemic','Unverified claim/evidence-gap topics; severity/relevance gain beats repetition penalties','Temperature rounding, chunk requirements, BA-009 causal support, or generic evidence','Supported-claim statements, original/fixed-code confusion, genuine absent-metric concern; old native BA-009 also filler target','Some actionable status/evidence gaps in BA-009, mixed with redundant/invalid allegations','Candidate text or supplied task facts only; no new measurements','Often same answer; new BA-009 structured adds unsupported confirmation','No encoded gain; valid missing-evidence observation does not yield valid repair','Same causal gap is revisited by VERIFY/SECOND_ORDER; 15 selections are not 15 discoveries'),
'VERIFY':('epistemic','Untested assumption or unverified claim with high risk; exact utility factors stored per selection','Chunk code requirement, stable-sort premise/goal, BA-009 certainty','Same-model checks/critique and repeated uncertainty assertions','Legitimate request to check a claim; most proposed failure assertions not demonstrated','No executed tests or external retrieval; proposed stability test remains illustrative','BA-008 native first child loses explanation; new native BA-009 second child lowers certainty and invents ID','0 encoded gains, 1 encoded loss; narrow safety qualification also occurs','Repeats EVIDENCE topics and task-induced assumptions; not independent confirmation'),
'ASSUMPTION':('epistemic','High-risk extracted/model assumption and repetition/coverage policy','Stable-sort goal versus task factual premise','Premise-conflict concerns and clarification requests','No demonstrated sorting-code failure; normative goal mistaken for untested factual defect','No independent evidence','Code-only native answer persists; structured stability test/text unchanged','No encoded gain; no new verified support','Reuses prior VERIFY premise concern'),
'CONSTRAINT':('constraint','Uncovered completeness/correctness or high-severity registered concern','Temperature ordering/completeness; old native sort explanation','Incorrect ordering criticism or repeated premise conflict','True old numeric defect exists but this critique misdiagnoses it; new temperatures already correct','Frozen external checks exist after runtime, not available to operator','Most identical; old temperature C2 malformed arose in different EVIDENCE cycle','No encoded gain; does not isolate/fix remaining true error','Same purported ordering/assignment errors recur'),
'HOW':('foundational','New structured BA-001 high completeness weakness feeds mechanism selection','Repair allegedly missing/misassigned conversions','Mechanism-focused misassignment allegation','Contradicted within saved numeric/position checks','No new evidence','Formatting/wording only; values already correct','No encoded gain','Reformulates prior CONSTRAINT completeness concern'),
'SIMPLIFY':('optimization','Old structured BA-001 generic clarity dimension remains eligible','Ordering/validation presentation','Restated ordering error and output-order request','Does not identify real wrong 74.7 result','No new evidence','Reproduces original wrong numeric array; rollback restores same wrong C0','No encoded gain','Same ordering criticism from CONSTRAINT/EVIDENCE'),
'SECOND_ORDER_EFFECT':('systemic','Deep missing-evidence task; generic failure-mode coverage becomes eligible','BA-009 causal limitations and missing observations','Repeated metric-gap critique and causal-effects concerns','Missing evidence/status can be real; metric insertion is not a feasible acquisition action','No new observations','Old answer unchanged; new native repeats invented ID; new structured paraphrases unsafe conclusion','No encoded gain; no independent causal support','Revisits EVIDENCE/VERIFY gap rather than resolving it'),
'ALTERNATIVE':('search','Uncovered alternatives/low-value history and bounded branch eligibility','BA-009 competing causal explanations','Alternative hypotheses, branch judgments and synthesis; metric-gap critique persists','New possibilities exist; none independently discriminated or shown to correct output','8 branch-associated calls across 2 search cycles; 0 executed evidence','Old answer unchanged; new structured adds defensive causal prose, not JSON','No encoded gain; diversity is not verified causal information','Repeats absent-metric concern while generating alternate stories')}

optext='''# Operator activation, information and quality value

Sources: all original selections/questions/operator_outcomes/critique steps identified in CYCLE_AUDIT, their wire requests in CALL_AUDIT, and current `cognition/policy.py`, `cognition/session.py:78`, `operators/base.py:31`. Each activation is a concrete critique call, not a candidate rewrite. The current utility formula multiplies relevance × predicted internal gain × issue value × novelty × task importance, minus repetition/cost plus meta adjustment. The information proxy counts new finding IDs, knowledge mutations and viable branches. Its HIGH label cannot certify new evidence or better answers.

The table's call/token totals include the **entire associated cycle**, including generation, judgments, verification and any branch work. They cannot be attributed causally to the operator. Direct operator inference is the critique purpose: 50 physical calls (44 regular+6 repair), 166,529 tokens. Planning repairs are separate. There is no randomized operator comparison.

'''
operator_table=[]
for op,d in S['operator_costs'].items():
    group=[c for c in C if c['selected_operator']==op]
    ids={(c['experiment_version'],c['run_id'],c['cycle_index']) for c in group}
    direct=[c for c in CALLS if c['category']=='operator_critique' and (c['version'],c['run_id'],int(c['cycle'])) in ids]
    operator_table.append([f"{op} / {d['family']}",d['activations'],a.packed(d['internal_gain_levels']),
        f"{len(direct)} / {sum(int(c['tokens']) for c in direct):,}",d['associated_cycle_calls'],
        f"{d['associated_cycle_tokens']:,}",f"{sum(c['provider_latency_seconds'] for c in group):.3f}",
        f"{d['positive_external_transitions']} / {d['negative_external_transitions']}"])
optext+=table(['Operator / family','Activations','Internal gain levels','Direct critique calls / tokens','Associated cycle calls','Associated tokens','Associated provider seconds','Encoded gains / losses'],operator_table)
optext+='\nThe gain levels above include final branch enrichment: both ALTERNATIVE outcomes change LOW→HIGH because two branches per run are labelled viable/merged. Neither cycle acquires executed evidence or an external score gain. CYCLE_AUDIT preserves pre-branch and final information_gain separately; treating only the initial critique outcome as final would undercount this internal activity.\n'
questions=['1 Why selected?','2 Intended issue?','3 Actual output?','4 New actionable weakness?','5 New evidence?','6 Candidate altered?','7 Useful revision?','8 Later improvement?','9 Repetition?','10 Cost?']
for op,values in op_descriptions.items():
    family,why,target,output,new,evidence,altered,useful,repeat=values;d=S['operator_costs'][op]
    answers=[why,target,output,new,evidence,altered,useful,'No later encoded improvement in any associated run; unmeasured semantic effects remain unknown',repeat,f"{d['activations']} activations; {d['associated_cycle_calls']} associated cycle calls / {d['associated_cycle_tokens']:,} tokens; exact critique versus other purposes in CALL_AUDIT"]
    examples=[c for c in C if c['selected_operator']==op]
    optext+=f'\n## {op} — {family}\n\n'+table(['Question','Observed answer'],zip(questions,answers))
    optext+='\nSource cycles: '+ '; '.join(f"{c['experiment_version']} {c['run_id']} #{c['cycle_index']} ([trajectory](../{c['source_trajectory']}), steps {c['source_step_start']}–{c['source_step_end_exclusive'] or 'termination'})" for c in examples)+'.\n'
optext+='''
## Conservative issue equivalence and authority

57 ingested critique-finding occurrences, **not all discovered issues**: judge feedback, extracted claims/assumptions and selected generic dimension topics are separate populations. Stable issue IDs are scoped by version/run, never joined across runs. Exact normalized text is REPEATED; changed text with the same polarity heuristic and token Jaccard ≥.72 is a tentative REFORMULATED proposal; reused IDs with incompatible/different wording are UNKNOWN. New unmatched text is DISTINCT_LEXICAL_PROPOSAL. Negation/numbers/operators are retained in normalization; this still cannot establish semantic equivalence. The same ID can change meaning; a new ID can repeat an old issue. Run-local occurrence history is used even across state restoration, with uncertainty explicit.

| Identity class | Occurrences / 57 | Interpretation |
| --- | --- | --- |
| New lexical proposals | 22 (38.6%) | Not 22 genuine actionable discoveries |
| Exact normalized repeats | 28 (49.1%) | Repeated proposition text; may be valid unresolved concern |
| Tentative reformulation | 1 (1.8%) | Lexical proposal, not semantic proof |
| Unknown | 6 (10.5%) | ID reuse/changed proposition cannot be safely merged |

**Genuinely distinct validated issue proportion cannot be determined.** All 57 occurrences originate in MODEL_CRITIQUE; none has a newly acquired executed-evidence receipt in these runs. That is an authority observation, not proof that all 57 statements are false or ungrounded: BA-009's stipulated missing metrics and literal format/status gaps can be grounded without world evidence; several 'findings' merely state a claim is supported. ISSUE_EQUIVALENCE includes the contextual grounding review separately from identity. Do not add ungrounded as a mutually exclusive lexical bucket or interpret its absence as validation.

The 44 selected topics separately comprise 22 plausible-but-unverified, 12 generic/unknown, six unsupported, two contradicted within frozen coverage and two deterministically grounded status/evidence-gap targets; externally demonstrated selected defects: zero under this conservative topic definition. Target novelty: 34 first-selected ID/text combinations, nine repeated same-ID/text, one reworded same-ID. First selection is not first issue creation or new knowledge. Legitimate sorting requirements are plausible topics; their premise-dependent critique is assessed separately. Unsupported ≠ false; unknown ≠ contradicted.

Severity inflation is visible in new structured BA-001: correct output receives high completeness/misassignment concerns, and in BA-008: premise-induced high assumptions protect continuation. Resolution failure includes BA-009 stale 'established' concern after enum qualification, plus original gaps retained after no-op revisions. Positive low-severity 'supported' findings can inflate activity without a defect. Current v0.3.5.2 separates advisory from decisive authority, but utility/gain still warrant a controlled test. No operator earns a general causal usefulness ranking from these 44 correlated cycles.
'''
optext+='\n## Occurrence-level grounding, separate from identity\n\n'
optext+=table(['Local manual scope label','Occurrences /57','Meaning'],[[name,f"{n} ({100*n/57:.1f}%)",{
    'GROUNDED_SCOPED_OBSERVATION':'16 observations include10 already-satisfied positive requirements/behavior and6 repeated BA-009 absence/status gaps; not16 novel defects or world-truth proofs',
    'CONTRADICTED_WITHIN_SCOPE':'Ordering/completeness/absent-guard/original-loop allegations conflict with saved code/positions and finite rubric coverage',
    'UNSUPPORTED_CANDIDATE_DEFECT':'11 ungrounded defect inferences from task factual conflicts or normative goals; unsupported does not mean false',
    'PLAUSIBLE_BUT_UNVERIFIED':'Scope/attribution/type/causal-support inference merits investigation; no defect conclusion',
    'UNKNOWN':'Falsifiable-check sufficiency or stale concern/current-answer attribution cannot be safely adjudicated'}[name]] for name,n in S['finding_occurrence_grounding'].items()])
optext+='\nThese task-specific research annotations are in ISSUE_EQUIVALENCE. They are orthogonal to lexical novelty: the11 unsupported-defect occurrences (19.3%) may also repeat earlier wording. Four unknown (7.0%) remain separate from15 plausible/unverified (26.3%). The16 scoped observations cannot establish the genuinely distinct actionable discovery fraction; many restate satisfied requirements or a gap already noticed in pre-cycle judgment. No perfect semantic or causal classification is claimed.\n'
write('OPERATOR_VALUE.md',optext)

rev='''# Revision chain failure analysis

All 44 revisions are inspected from selected topic → exact critique → plan → saved revision request → child → evaluation/selection. CYCLE_AUDIT contains the ten required planning/generation dimensions as separate fields, exact original plan/critique objects, preservation instruction, output-contract result, authority/citation change and prompt/wire references. Primary categories are manual diagnostic labels, not mutually exclusive causal proofs. Revision generation consumes 44 calls/81,849 tokens; planner consumes 54 calls/129,849 tokens including ten repairs. No new evaluation was executed.

| Primary label | Cycles / 44 | Scope |
| --- | --- | --- |
| BAD ISSUE | 18 | Critique falsely diagnoses correct ordering/guards or elevates task premise; selected topic can still be valid |
| GOOD ISSUE, BAD PLAN | 11 | Recognized bounded gap, but empty salvaged prescription or unavailable metric/citation insertion |
| GOOD PLAN, BAD GENERATION | 7 | Six native sort clarification attempts fail to preserve/supply explanation; first newer native certainty correction ignored |
| NEUTRAL REVISION | 8 | Already-satisfied temperature/code requirement, no encoded gain |
| GOOD REVISION, BAD SELECTION | 0 demonstrated | No higher-scoring child exists to be discarded; loss of a good C0 is a different selection failure |
| INSUFFICIENT EVIDENCE | Not a forced primary residual | Unknown semantic quality/plan sufficiency remain explicit within rows; categories do not establish exhaustive causes |

The three newer structured BA-009 cycles also carry a generation-failure overlap: independently actionable JSON format never repaired. The primary bad-plan label recognizes that requested metrics cannot be manufactured. An empty plan after failed ID salvage must not be called a valid plan that generation failed to execute. This differs from the earlier audit's broad aggregate recommendation and warrants independent rechecking of causal assumptions.

## Concrete counterexamples

- Old structured BA-001: C0/C1/C3 contain 74.7 rather than frozen expected 70.7; the useful J002 numeric finding exists, but plans repeatedly prescribe order/loop changes. C2 is a partial malformed array. Scores all0 do not erase that additional regression.
- BA-002: native has type/positive-size guard and full range. Structured guards `size<=0` but not all non-integers; a passing seven-case rubric does not verify that full docstring contract. False 'no guard' criticism is distinct from that real uncovered gap. No plan isolates and repairs it.
- New native BA-008: C0 correct+explanation → C1 code only,1→.5; C2/C3 do not restore explanation despite explicit plans. Comparisons miss the loss. Old native likewise loses explanation but regex leaves all scores .5.
- Old BA-009: actual critiques identify uncertainty gaps despite meaningless/generic selection; all changes in the recorded plans are discarded after unsuccessful ID repairs. Revision fallback repeats unsafe certainty or non-JSON prose.
- New native BA-009: C1 ignores a valid Engine-authored qualify/remove instruction. C2 obeys part of a model plan by reducing established→likely, but adds `database_metrics_unavailable` to a closed evidence-ID list. The nonexistent ID is not evidence that metrics were acquired. C3 retains it. No overall encoded gain.
- New structured BA-009: plan requests missing latency metrics; C1 instead adds unsupported 'evidence used confirms' authority; C2/C3 preserve it and never produce required JSON. Alternatives are hypotheses, not observations.

## Every transition with trace and diagnostic rationale

'''
rev+=table(['Version / run / cycle','Parent→child / score','Primary and overlapping categories','Observed issue/plan/generation failure','Source steps / revision prompt'],[[f"{c['experiment_version']} {c['run_id']} #{c['cycle_index']}",f"{c['incoming_candidate_id']}→{c['outgoing_candidate_id']} / {c['incoming_external_score']}→{c['outgoing_external_score']}",c['revision_failure_categories'],c['manual_review_rationale'],f"[trajectory](../{c['source_trajectory']}) steps {c['source_step_start']}–{c['source_step_end_exclusive'] or 'termination'}, request step {c['revision_prompt_source_step']}"] for c in C])
rev+='\nPlans/preservation findings were reviewed as task-specific saved evidence, not used to train a general semantic classifier. Human labels cannot determine the outcome of an unseen corrected plan; that requires a controlled future intervention.\n'
write('REVISION_FAILURES.md',rev)

write('QUALITYGATE_CALIBRATION.md','''
# Candidate selection calibration

Population: all60 historical candidates, not just returned answers. Original candidate-bound external records are copied by reference into CANDIDATE_CALIBRATION; internal judgments/gate/reasons/verification appear in CYCLE_AUDIT. Original comparator requests and results remain in the trajectory. These are repeated correlated observations from16 runs, so no independent calibration confidence interval is asserted.

| Internal gate | External pass | External fail | Total |
| --- | --- | --- | --- |
| ACCEPT_PROVISIONALLY | 3 | 0 | 3 |
| REVISE | 18 | 15 | 33 |
| REJECT | 12 | 12 | 24 |
| BLOCKED / ACCEPT_VERIFIED | 0 | 0 | 0 |
| Total | 33 | 27 | 60 |

12/24 rejection events contradict the frozen pass outcome **within its scope**; they are candidate-scoped rejection disagreements, not12 independent false world judgments. Many defects outside the rubric could still matter. 18/33 REVISE candidates pass externally, but REVISE includes incomplete scrutiny/uncertainty and is not REJECT or rollback. Provisional acceptance3/3 matches encoded pass, with zero verified acceptance and no newly executed evidence. This tiny selected acceptance sample does not establish specificity or absence of false acceptance elsewhere. All27 external failures are REJECT/REVISE; absence of ACCEPT_VERIFIED is an intended epistemic limit here.

Historical LLM verification reports passed for4 candidates (all externally pass), failed for56 (29 external pass,27 fail). These are **model judgments**, not deterministic verifier receipts. External evaluator executions happen outside END after the run; they cannot retrospectively supply runtime evidence authority. Basic Engine format/status checks are separate finite checks. Candidate mean judge score/confidence columns in CANDIDATE_CALIBRATION are descriptive; confidence is not correctness and its averaging is not used to choose a candidate.

## Traced disagreements

1. Old BA-001 native C1 receives a fatal adversarial finding that also admits conversions are correct, no exact quote, and REJECT; frozen score1. Trajectory `9cea722d-0dbe-43b8-9d30-24d6eac0befa.jsonl`, AJ002, C1. Returning C0 protects the score but the fatal rejection is unsupported.
2. Old BA-002 native C0–C3 all score1, all REJECT: original broken code/explanation is attributed to the repaired loop; actual quote occurrence is treated as semantic proof. Trajectory `6ba9d7f7-a7fe-496e-a8f3-d4887cdc0bae.jsonl`, AJ001–AJ004. Structured provides a mixture of appropriately excluded task/hybrid quotes and false unquoted allegations; legitimate non-integer gap remains outside evaluator coverage.
3. New BA-001 structured all score1, gates REVISE: typed judge findings are excluded, but false verifier/critique completeness concerns continue. Trajectory `efa824fb-bbda-4138-9243-414e772ef1fb.jsonl`. A less decisive negative path does not prove useful revision or complete assessment.
4. New BA-008 native C0 score1→C1 .5, all gates REVISE, returned C1. Comparator prefers/credits explanation that is absent, no rollback. Trajectory `653df055-ef1a-43ea-84b2-3d9b6c25bb0f.jsonl`, first comparison and subsequent best comparison, C0/C1. This demonstrates failed preservation of best already-recorded answer; no generated improved child was discarded.
5. Old BA-008 native C0 explanation is qualitatively useful, removed in C1; frozen regex hides loss, all .5. Trajectory `91b86589-796e-4570-965b-bd025d7c7b87.jsonl`. External flatness cannot validate comparator's assertion of equivalent explanations.
6. New BA-009 native C2/C3 add unknown ID after status qualification. Accurate unknown-ID criticism is conservatively excluded as SEMANTIC_UNSUPPORTED; model comparison calls a model plan a user instruction. Trajectory `49544d22-83e0-49a8-9179-c3765116e44b.jsonl`, C2/C3, J003. Structured 'confirms' assertion escapes status checking: `2965e080-5879-496e-89b9-c8d1368bb1ee.jsonl`, C1–C3. Final budget output is unaccepted/inconclusive, not a false ACCEPT_VERIFIED; nevertheless returned answer integrity is inadequate historically.

Links for these original trajectories and their external files are in REPORT's trace index and each CYCLE_AUDIT row. Both pilot MANUAL_REVIEW files corroborate these scoped readings; no old label or score was changed.

## Rollback, disagreement and scoring risk

18 rollback events occur in the older pilot; zero in the newer one. Many rollbacks concern identical/passing code or preserve an already wrong C0; one retains old code-only C1 after rejecting C3. None is shown to discard a higher external-scoring child. Current best selection ranks gates, uses advisory comparison preferences on ties, accounts for observed unsafe ties, and restores candidate-scoped snapshots. Current comparator itself remains model-advisory. Finite current reference/status/format checks improve authority handling offline; their live calibration is unmeasured.

Primary/adversarial verdict disagreement occurs in the examples above, but the configured secondary-primary dispute detector is absent (no secondary judge); adversarial disagreement is not automatically a DISPUTED event. Model confidence1 in old native BA-009 C1/C2 coexists with unsupported establishment. Comparator deltas can be allzero while its prose claims an improvement; protocol validity does not calibrate this. No deliberate score-gaming causal intervention was made. Repeated identical candidates with different IDs get new assessments; cache-by-ID does not avoid text-equivalent judgments.

Better-child-missed H5 is unsupported by the frozen score oracle: best recorded external score equals C0 in every run. Selection failure still matters for retaining good C0 and recognizing missing requirements/safety. Rubric omissions prevent declaring all ties equally good. No external score is proposed as a new runtime authority.
''')

cost='''# Termination, computational cost and separate value axes

CALL_AUDIT joins every physical provider record to one trajectory model_call step and its request purpose. Tokens are provider-reported input+output, not estimates. Provider latency below excludes some wrapper/orchestration overhead. Sum physical provider latency is not calendar elapsed or sum whole-run wall; whole-run total is15,293.791163s. No monetary/electricity price is recorded, so currency cost is unknown. No current provider request was made to obtain it.

'''
cost+=table(['Purpose','Calls','Tokens','Provider latency s','Observed direct output / value'],[[k,d['calls'],f"{d['tokens']:,}",f"{d['provider_latency_seconds']:.6f}",{
'initial_generation':'16 C0s;10 score1; no verified evidence',
'revision_generation':'44 children;0 score gains,1 loss; mixed safety and format changes',
'operator_critique':'44 ingested critiques/57 finding occurrences;6 repair calls included',
'revision_planning':'44 plans;10 repair calls included; invalid/unavailable repair actions observed',
'model_verification':'60 model assessments;0 executed evidence; opinions can change issues',
'primary_judging':'60 primary opinions; findings/feedback, not evidence',
'adversarial_judging':'60 adversarial opinions; genuine gaps plus false fatal/premise objections',
'adversarial_test_generation':'60 scenario proposals; no runtime tool execution',
'candidate_comparison':'44 parent comparisons plus10 best-candidate comparisons; no score gains found',
'branch_activity':'8 branch generation/evaluation/synthesis calls across2 ALTERNATIVE cycles; hypotheses only'}[k]] for k,d in S['purpose_costs'].items()])
cost+='''
Operator execution and critique are the same physical stage here; do not double-count them. Trajectory judging, QualityGate, utility, claim extraction, audits, progress and final guards are deterministic/local computations: **zero additional model calls**. Other/unmapped purposes: zero in this completed FULL_END population. Protocol repair is an overlapping subset, **16 calls/53,418 tokens/458.637350s**, already in critique/planning. Old12 repairs fail with32 discarded elements; new4 yield3 accepted successes,1 failure and2 discarded elements; zero suppression activates in the newer completed pilot. Protocol success does not establish diagnosis truth.

## Calls associated with activity without encoded quality gain

- All44 revisions and their later judgments are in runs whose final score never exceeds C0; this is an outcome association, not a counterfactual attribution.
- 30 unchanged raw/historical-answer transitions:256 associated-cycle calls/590,742 tokens. They can still check safety or bounded properties; original delimiter limitations apply to answer-region identity.
- 28 exact repeated critique findings and1 tentative reformulation; cost cannot be split per finding because a call can contain several. CALL_AUDIT cycle join supplies conservative whole-cycle association, not a per-finding causal bill.
- 18 rollbacks old,0 new; discarded/empty plans in old BA-009 prevent valid repair instructions. Call-budget savings under a different policy are unobserved.
- 24 transitions enter from external score1: additional work might repair unmeasured safety/prose gaps, but no encoded gain and one encoded loss occur.

Answer-quality value: no measured gains; one measured loss, plus qualitative losses missed by rubric. Epistemic-safety value: new native BA-009 lowers established→likely in cycle2, but invents an ID; filters suppress some false premise/semantic allegations without verifying answer truth. Computational cost:466 calls/1,140,074 tokens/4h14m53.791s of completed FULL_END run wall. These three axes must not be collapsed to 'waste' or 'success'.

## Why continuation survives

Both pilots have22 cycles: one native BA-001 cycle, three each for the other seven runs. Each has seven BUDGET_EXHAUSTED and one ACCEPTED_PROVISIONALLY stop. Old no-progress reasons/counters were not recorded: missing, notzero. New has22 cycle-progress records, no NO_PROGRESS stop. Raw-content/proposed issue/claim/verifier churn resets counters without a score gain; some unchanged cycles increment counter. BA-002 structured reaches2 only at ordinary cap; BA-008 structured reaches2 but high-risk-assumption protection applies. New native BA-009 mandatory overclaim correction protects the useful second status-qualification attempt. No-progress absence alone is not a detector bug and does not authorize removing mandatory constraints.

Current v0.3.5.2 filters advisory issues/unverified claim/model verifier churn from progress, but content/branch/gate change can still be qualitative or adverse. It enforces cycle/operation/shared-call ceilings and lets mandatory actions block NO_PROGRESS, while stopping never creates acceptance. Default max_run_calls=None for baseline is a publication-independent research risk: finite cycles are not a global physical-call ceiling. Future runs must explicitly set one.

## Denominators and interrupted cost

Completed DIRECT+FULL pilots together:24 trials/474 calls/1,160,460 tokens/16,643.512606s; primary FULL totals exclude8 DIRECT calls/20,386 tokens/1,349.721443s. The pilot reports separately retain18 saved interrupted responses/21,041 tokens/463.146185s provider latency across both archives, plus3 started calls with unknown consumption. These partial numbers come from historical interruption records, not a complete cost census or independent fresh runs, and must not be added to44 completed cycles. No missing response tokens are silently zero-filled. Benchmark Alpha is further context, not pooled with these denominators.
'''
write('COST_AND_TERMINATION.md',cost)

counter='''# Recorded-state counterfactuals

No alternative policy was executed or replayed as new inference. A changed adoption/stop decision changes later candidate context, prompts, seeds/state and potentially outputs; continuing along the original recorded future path is generally invalid. Saved score comparisons are observations of recorded artifacts, not guaranteed prospective effects. Actual safety withholding/final reconciliation may differ on early stops.

| Policy | Status | What is known | What is not known |
| --- | --- | --- | --- |
| A preserve C0, no revision | OBSERVABLE FROM RECORDED ARTIFACTS for C0 text/score; full safe return PARTIALLY RECONSTRUCTABLE | All16 C0 scores and texts; mean .71875, versus actual .6875; protects newer BA-008 explanation | Changed policy safety guard/output/termination; actual inference savings and future behavior |
| B best external-scored recorded candidate | OBSERVABLE FROM RECORDED ARTIFACTS; RETROSPECTIVE ORACLE UPPER BOUND | Every run's max score equals C0 (tie preference), mean .71875 | Runtime cannot see these external scores; equal-score candidates may differ in safety; no admissible oracle runtime policy |
| C stop after first cycle | OBSERVABLE FROM RECORDED ARTIFACTS for effective post-rollback state; full policy PARTIALLY RECONSTRUCTABLE | First effective candidate score mean .6875, same aggregate as actual final; newer BA-008 already loses explanation | Early final best selection/reconciliation/guard and missing future evidence; misses native BA-009 second-cycle status qualification |
| D revise only actionable grounded issues | PARTIALLY RECONSTRUCTABLE eligibility; SPECULATIVE / REQUIRES NEW INFERENCE after divergence | Two selected topics deterministically grounded, other34 plausible/unknown and8 unsupported/contradicted; useful downstream gaps can differ from selected topic | Scores/future outputs/cost under filtered discovery, corrected plans or alternative state; no invented zero-regression/gain estimate |
| E reject unsupported authority additions | PARTIALLY RECONSTRUCTABLE for local saved deltas; SPECULATIVE / REQUIRES NEW INFERENCE after divergence | New native BA-009 C2 invents ID; new structured BA-009 C1 adds confirmation; can flag these deltas | Whether retaining earlier unsafe/malformed parent is admissible or yields better final response; later recovery and total cost |

D cannot simply select the two grounded-target rows: a generic evidence topic can produce a real downstream format/status issue, while a plausible topic can produce a false critique. Eligibility needs an issue-target/constraint/evidence link, not arbitrary task-specific retrospective filtering. E must not preserve established C0 just because the proposed child adds a citation; bounded safety correction or withholding may still be required. Lowering status and inventing an ID can overlap as safety improvement and regression.

## Every run: observed score comparisons

'''
counter+=table(['Version / run','Actual final','A C0','B oracle / candidate','C first effective / score','D/E future'],[[f"{r['version']} {r['run_id']}",r['actual_final_score'],r['A_c0_score'],f"{r['B_oracle_score']} / {r['B_candidate']}",f"{r['C_after_first_cycle_effective_id']} / {r['C_after_first_cycle_score']}",'UNKNOWN after policy divergence'] for r in S['counterfactuals']])
counter+='''
Source references: REPORT trace index, RUNS.json and each CYCLE_AUDIT first-cycle row; candidate scores remain their original evaluation files. B's tie preference is an analysis convention, not evidence that C0 is safest. Historical old native BA-008 regex limitation biases score comparisons and hides explanation preservation value. There are0 higher-scoring recorded children to reveal a strong missed-improvement selection bottleneck. Savings based on omitting recorded calls can be an arithmetic ceiling for a literal replay only; no exact actual savings are claimed for new inference.
'''
write('COUNTERFACTUAL_ANALYSIS.md',counter)

invariants='''
### Shared non-negotiable invariants

MODEL AGREEMENT IS NOT VERIFICATION. Task text is not automatic external truth; model plans are proposals, not user instructions. No revision manufactures evidence. Only actual configured candidate-bound checks can earn scoped support; confidence/agreement cannot promote unverified claims. Failed scoped deterministic checks remain consequential. Mandatory constraints cannot be bypassed by acceptance or early stopping. Lineage, best/latest IDs, rollback reasons and all physical calls remain auditable and bounded. External side effects need authorization. Jev stays optional and supplies no evidence authority; all proposed first experiments use baseline decisions. Checkers do not prove universal correctness. A guard may withhold unsafe output while external task quality fails; report both.
'''
proposals='''# Three competing experimental designs — NOT IMPLEMENTED

These are competing causal interventions, not proven replacements. Keep current Engine source frozen. Any later prototype must be a separately authorized isolated experimental adapter with its own fingerprint and invariant tests. All use the same initial-generation mode, model/settings, answer-scope/evidence safeguards and external measurement contract. No benchmark-specific repair prompt or hidden scoring key enters runtime.

'''+invariants
dimensions=['1 Core hypothesis','2 Components retained','3 What changes','4 Removed/bypassed','5 Required information','6 Why might improve answers','7 Why might fail','8 Inference structure','9 Compatibility','10 Safety/evidence invariants','11 Minimal implementation slice (future only)','12 Falsifiable prediction','13 External measurements','14 Stop criteria','15 Cost risks']
designs={
'A — Sparse deliberation with revision gating':[
'Grounded actionable failure eligibility plus C0 preservation reduces harmful/redundant rewrites without losing valid corrections.',
'Candidate/answer scope, lineage, finite contract/status/reference checks, optional scoped checker, ledger/budget and auditable rollback/withholding.',
'One bounded issue probe only when finite uncertainty/actionability warrants it; explicit eligibility record and retain-C0 default. One repair maximum; outcome measured against the targeted invariant.',
'Routine full primary/adversarial/test generation on every text-equivalent candidate; utility-driven multi-cycle churn and broad rewrite fallback when no actionable defect exists.',
'Actual C0; task constraints versus assertions; candidate-bound failure or explicit unresolved requirement; required safety actions and absence of independent observations.',
'Protects new BA-008 explanation and avoids already-satisfied temperature repairs; relevant bounded failures can still trigger one correction.',
'Misses subtle unmeasured defects; imperfect eligibility may protect wrong C0 or overtrigger. Lack of world evidence may require uncertainty rather than a correctness verdict.',
'C0=1; if eligible, probe/critique1 + revision1 + advisory recheck/comparison1; maximum4 physical calls including any replacements, not4 plus unlimited repair. Deterministic checks add0 model calls.',
'Experimental condition ID, additive gate-decision and skipped-stage records; no reinterpretation of old trajectories. Preserve schema/Engine API via adapter; no claim of native internal policy equivalence.',
'Shared invariants; hard failed constraints cannot be accepted by sparse stop; unsupported status/reference additions corrected or withheld; retain reasons for every skipped stage.',
'Read-only C0 observer + eligibility record + single repair path + unchanged-scope fallback. No production utility edits or new operators needed for the slice.',
'On fresh passing-C0 cases: fewer meaningful regressions than frozen END with preserved quality/safety. On repairable failures: positive final-minus-C0 must occur; lower calls alone fails answer-improvement criterion.',
'C0/final correctness, missing constraints, issue precision/recall on bounded labels, eligibility decisions, regression/safety/withholding, meaningful delta and full cost.',
'One repair/no eligible issue/end-of-budget; unresolved mandatory safety ends with explicit failure/withholding. Halt study on authority invariant violation.',
'Eligibility probe can be as expensive as critique; false eligibility wastes capped calls; too little scrutiny can conceal real safety cost.'
],
'B — Evidence/constraint-directed repair':[
'A bounded failure→specific delta→preservation/check contract outperforms generic plans on repairable cases, even with the same issue and model.',
'Task/answer provenance, candidate lineage, scoped trusted checker interface, evidence contracts/reference registry, guards, rollback and ledger/accounting.',
'Maintain one repair objective: failed constraint/claim, allowed data, proposed measurable delta, unaffected invariants, and explicit evidence-acquisition availability. Unsupported causal gap maps to request/qualify, not fabricated metrics.',
'Broad open-weakness shopping, severity-driven correction, unbounded model-plan instruction authority and generic rewrite after unusable plan.',
'Grounded finite issue, actual parent text, checker scope or literal task constraint, permitted evidence IDs, known unavailable information and preservation requirements. Hidden external evaluator forbidden.',
'Targets old numeric/type/format defects rather than ordering noise; prevents BA-009 unavailable-metric insertion and protects explanation/key contracts.',
'Cannot repair unknown root cause without observations; constraints may be uncheckable; model can ignore valid delta. Overconservative grounding may suppress a real defect.',
'C0=1 + bounded issue probe1 + objective/plan1 + revision1 + advisory comparison1; maximum5 physical calls. Trusted local finite checks are0 inference; paid/external acquisition excluded.',
'Additive RepairObjective research record and links to original issues/constraints; existing CheckContract lifecycle retained. Keep source/prompt changes isolated in future adapter and hash it separately.',
'Shared invariants; unavailable data explicitly remains unavailable; new cited IDs must belong to registry, model-origin plan cannot expand task/evidence authority; scoped failed check prevents acceptance.',
'One closed repair objective with deterministic preservation checklist, no new general planner framework. Generate one complete child, audit its objective delta and reference/status change.',
'Among independently adjudicated valid objectives, more positive C0→final deltas and fewer unrelated contract losses than frozen END/A; if generation still fails valid plans, H4 gains support over H3.',
'Issue validity, plan executability, target repaired, preservation loss, unknown-reference/overclaim changes, quality/safety delta, objective count, calls/tokens/time and failures.',
'No supported executable objective: retain C0/qualify or withhold; one child maximum. Failed/check-unknown objective remains disclosed. Stop on any unsupported support promotion.',
'Objective/contract setup adds tokens; trusted checks can be costly outside inference; preserving too much may freeze wrong structure; world-data acquisition would require a new authorized budget.'
],
'C — Bounded independent alternatives and grounded comparison':[
'Different complete approaches escape a local rewrite loop; bounded diversity plus scoped selection provides better candidates than repeated plan-conditioned edits.',
'C0 retention, branch IDs/lineage and branch budget, authoritative answer scope, registered evidence/checker contracts, guarded comparison/selection, rollback and ledger.',
'When the same grounded failure justifies exploration, generate exactly two complete independent alternatives directly from original task plus allowed data, without inheriting prior critique/plan text. Compare all candidates on retained constraints.',
'Multi-step causal-story synthesis and recursive branch depth; repeated same-parent rewrites; automatic adoption merely because a model branch is PROMISING.',
'Original task/allowed evidence, a bounded trigger, C0 and two full solutions; measurable scoped checks and uncertainty. Diversity text is not independent world evidence.',
'May escape wrong74.7 or local explanatory collapse; C0 remains available and hidden evaluation measures candidate-set potential separately from selected final.',
'Same model may generate correlated wrong candidates; advisory comparator can still miss the best. Alternative causal stories are not observations, and merging can manufacture authority.',
'C0=1 + two alternative generations2 + one advisory comparison1; ordinary4, hard maximum5 including one permitted repair within cap. No recursive branches/synthesis/revision loop.',
'Condition ID with parent=C0 plus sibling alternative IDs; preserve original histories, mark independent prompt provenance. New adapter can reuse bounded branch/compare records but must not relabel hypotheses as evidence.',
'Shared invariants; checks apply to each actual candidate, not transferred receipts. Mandatory format/safety filters precede preference; unknown branches retained as unknown, no discarded-branch importing.',
'Two independently prompted complete candidates, one comparison over admissible set, C0 fallback. No new general tree-search engine or optimizer.',
'More distinct admissible candidates and higher externally scored candidate-set maximum than A/B; if potential rises but selected quality does not, H5 is implicated. Diversity without quality/safety gain falsifies claimed benefit.',
'Candidate-set maximum is a retrospective diagnostic only, distinctness/proposition overlap, chosen-candidate regret, final-minus-C0, regressions, safety and whole branch cost.',
'Exactly two alternatives then compare once or deterministic fallback; no tie retries. All unsafe candidates→explicit failure/withholding; hard budget exhaustion reported.',
'Additional full generations are historically the slowest call type; comparison can be bottleneck or target for verbosity bias; two alternatives do not establish broad search superiority.'
]}
for name,values in designs.items():
    assert len(values)==15
    proposals+=f'\n## {name}\n\n'+table(['Dimension','Proposal'],zip(dimensions,values))
proposals+='''
## Distinguishing the interventions

A tests whether a scarce repair trigger plus preservation suffices. B tests executable repair prescriptions after fixing issue eligibility. C tests candidate diversity and selector regret. Common provenance/check guards are retained across all three, rather than giving one condition privileged hidden evaluator access. These interventions change different call structures, so report both capped native costs and outcome deltas; do not call any successful solely for efficiency. Stronger-model routing and evidence acquisition are later separate factors, not silently bundled into a winning architecture. No design may promise to infer absent causal data by additional opinions.
'''
write('ARCHITECTURE_PROPOSALS.md',proposals)

write('EXPERIMENT_PLAN.md','''
# Minimum viable experiment — NOT EXECUTED

Purpose: distinguish redundant deliberation, invalid objective formation, generation failure and selection regret on fresh measurable cases. This is a diagnostic screen, not a powered benchmark or evidence of general intelligence. No task, evaluator, adapter, prompt or live call is created by this document. Recommendation D first requires the evaluation contract to be frozen and independently reviewed; prototypes and inference each require separate authorization.

## Exact first matrix

Two new, independently authored diagnostic tasks, **P1/P2 identifiers are placeholders, not existing files**. Each task must contain a clearly bounded constraint/epistemic element and an objective external rubric, selected before viewing any model output. Seek a mix of naturally solvable and repairable difficulties; do not replace an unexpectedly correct C0 after seeing it. P1 can be a constraint-preservation/explanation task; P2 a finite-evidence/repair task where information absence cannot be repaired by fabrication. Neither reuses Alpha's four repeatedly inspected prompts or expected answers. These two tasks cannot span all possible END use cases.

| Condition | Frozen task cells | Replicates / pre-registered seeds | Runs | Physical calls/run ceiling | Whole-condition ceiling |
| --- | --- | --- | --- | --- | --- |
| DIRECT | P1,P2 |2 each |4 |1 |4 |
| SELF_REFLECT | P1,P2 |2 each |4 |3 |12 |
| Frozen current END 0.3.5.2 | P1,P2 |2 each |4 |16 |64 |
| A sparse gating | P1,P2 |2 each |4 |4 |16 |
| B directed repair | P1,P2 |2 each |4 |5 |20 |
| C bounded alternatives | P1,P2 |2 each |4 |5 |20 |
| Total |2 tasks×6 conditions×2 repeats |2 frozen seed identifiers |24 |— |136 |

Frozen END uses native generation, quality enabled with the historical same-model primary/adversarial setup, baseline decisions, one cognitive-cycle cap, no optional secondary/routing provider; explicit max_run_calls16. All other settings, artifact scopes and current source fingerprint frozen before inference. This bounded control is current policy **under an explicit one-cycle experiment override**, not a rerun of the three-cycle pilots and not evidence about benefits beyond one cycle. The explicit maximum remains binding even if it interrupts mandatory repair: record inconclusive/failure, never increase it. DIRECT and all initial generators use the same original task and common model settings; A/B/C are future experimental adapters with separately frozen hashes.

Use two externally fixed seeds (e.g. S1/S2 values chosen in preregistration); publish the entire schedule and per-call seed derivation. Block-randomize the six conditions within task×seed, record hardware/load. Each run performs its own initial generation: **no C0 pooling/replay as a live response**. Same seed does not guarantee identical C0s. Compare within-run final−C0, then condition distributions; direct score differences alone conflate initial sampling. A later shared-C0 intervention would be a distinct preregistered experiment.

## Budget estimate from historical physical purposes

Ordinary calls per task×seed block: DIRECT1 + SELF_REFLECT3 + END13 + A4 + B5 + C4 =30, or120 for four blocks. Physical maxima reserve12 additional END calls and4 C repair calls, totaling136. A/B repair attempts replace work inside their caps rather than increasing counts. Global repair count is not an extra unbounded allowance.

Purpose-weighted estimate for ordinary120:32 initial/alternative generation,16 critiques,16 revisions,8 planning,16 comparison,8 each verification/test-generation/primary/adversarial. Multiply each by its observed mean tokens/latency in SUMMARY.purpose_costs: **273,439.738 tokens,6,052.746910s (~101min)** provider latency. If all16 reserved repair calls resemble historical repairs, add53,418 tokens/458.637350s (~7.6min), giving ~326,858 tokens/~109min before orchestration/checker overhead. Historical whole-run wall varied sharply between versions/server conditions; these are estimates, not guaranteed costs. Full alternative-generation latency may differ from C0; confidence bounds are unavailable. Flat120×overall call means would underweight slow initial generation.

Hard global boundaries: **136 physical attempts,400,000 provider input+output tokens,3h cumulative active wall time**, including resumed sessions/checkpoints/scoring overhead. Per-run wall cap15min (remaining global time takes precedence), per-request timeout no more than remaining run/global time or900s. Count attempts before dispatch, including failure/repair/transport requests. No silent retry, timeout retry, tie-expansion, extra seed, extra task or budget reset. A timeout ends that run with preserved incomplete records; global invariant/unknown consumption can halt the study. Do not launch another call unless bounded input+output token allowance fits the remaining budget: for the historical8192 context/4096 output settings, conservatively reserve12,288 tokens per call, then release unused reservation after valid reported usage. Verify provider enforcement/token semantics beforehand; if trustworthy bounds or usage are unavailable, stop rather than claim a hard consumption cap. Missing usage never equals zero.

This plan is for an already available authorized local runtime, with **zero authorized paid-provider spend**. No credits/dependencies/models are purchased/installed. A cloud substitution requires a new explicitly approved currency budget and provider-specific immutable identity/cost contract; current reports contain no trustworthy monetary price. Caller wall timeout does not prove the server stopped inference: require cancellation support or record outstanding/unknown consumption and halt; do not continue under a false hard-cost claim.

## Frozen measurement contract and preregistration

Before inference: freeze task bytes, evaluation code/environment/expected answers, runtime constraints/allowed evidence, architecture-adapter/source hashes, model digest/quantization/settings, server version, hardware, schedule/seeds, scoring rules and thresholds. Independent reviewer checks rubric sensitivity on authored fixtures including missing required explanation, invalid JSON, invented reference, wrong numeric fact, unsupported confirmation and warranted uncertainty. These fixture checks validate measurement coverage, not cognitive improvement. Raw outputs are never patched to make scoring easy. Authoritative answer span and raw container both saved; external scoring uses the predeclared returned-answer scope consistently. Unparseable/withheld answers are failures/zero under registered usability rules, plus separate safety labels.

External evaluator runs **after final runtime artifact freeze**, hidden from runtime policies, planners/judges/selectors. B may use explicitly supplied task constraints and trusted development check contracts; it cannot use held-out evaluator code/expected keys/scores. Passing development checks only supports their stated properties. No external-rubric score appears in runtime selection. Blind safety/semantic annotation uses saved text and source evidence, not model confidence; disagreements/unknowns are retained.

Measures per run: C0 and every candidate/final quality; final−C0 and improvement frequency; score and semantic/format regressions; verified scoped support/failed checks/authority upgrades/unknown citations/withholding; physical attempts and reported/missing tokens; provider latency versus run/cumulative wall; currency cost if authorized; operator counts and valid novel issue precision; executable-plan validity; meaningful revision count (target fixed plus preserved constraints, not text difference); branch distinctness and post-run oracle regret; transport/protocol/budget failures/timeouts. Report intended24 and completed counts, include incomplete cells in failure rate, do not silently analyze completers only. Candidate-set oracle is retrospective diagnostic only.

Screen success criteria, fixed before inference: **quality improvement requires ≥2 runs with positive final−C0 across both tasks, positive mean delta, no task-mean loss versus DIRECT and no substantive regression/authority invariant breach in reviewed outputs**. Safety improvements are separately counted and cannot alone satisfy answer-quality criterion. A/B/C design-specific predictions in ARCHITECTURE_PROPOSALS must also hold (A preservation; B target repair; C candidate-set potential and selected outcome). Fewer calls or elaborate reasoning alone fails. These thresholds are a continuation screen, not statistical proof: n4/condition is too small for reliable superiority/noninferiority claims. Zero recorded regressions does not establish zero risk.

Variance: report all two replicate values, per-task mean/range and condition distribution; a two-observation SD is descriptive only. Do not treat44 historical cycles or repeated candidate scores as independent trials. Do not cherry-pick best seed. If both fresh tasks have passing C0s with no measurable repair opportunity, report a ceiling-limited screen and stop; no output-dependent substitution. Hypothesis localization uses issue→plan→generation→selection annotations: invalid issue supports H1, invalid plan given valid issue H3, ignored valid plan H4, increased candidate-set oracle but poor selection H5. Shared confounders/unknown adjudication stay visible. No causal claim from these annotations alone.

## Holdout, checkpointing and drift

Reserve a separate **four fresh holdout tasks**, identities/hashes committed in the future research manifest but content not inspected by architecture authors until designs frozen. No holdout inference included in the24-run authorization/caps. Confirmatory budget and model choice require a separate request after the screen; freeze chosen architecture without tuning to P1/P2 or old Alpha. A screen passing does not authorize scale-up or publish a release.

Immutable run directory and manifest before first call; durable call-start reservation then response/error artifact, candidate lineage and atomic final checkpoint. Completed trials never overwritten/replayed as fresh. Resume only truly unstarted/missing cells, with aggregate reservations/calls/tokens/active elapsed carried forward. Interrupted/unknown requests are retained with conservative reservation; never automatically rerun them. Hash verification precedes every resumed session. No edits to frozen source/task/evaluator/settings after results begin; any justified change creates a new experiment needing authorization rather than splicing results.

Record server version/digest at session start/end and immediately before every trial; record restart/update events and configuration in each trial manifest. Detect drift→stop, preserve all records and disclose version assignment uncertainty; do not compensate with extra trials. The historical .35.1→.40.0 unknown-time drift must not recur silently. Version monitoring consumes transport/preflight requests, not model inference, but must be authorized as part of the future live experiment. No such request was made during this review.
''')

write('LIMITATIONS.md','''
# Limits, confounders and hostile alternatives

1. **Historical version scope.** Only v0.3.5/.3.5.1 have saved live pilots here; current0.3.5.2 source is verified offline, not live. Its integrity changes address several observed paths. Old performance cannot be silently transferred to current behavior. Old source fingerprints are manifest records, not fully reconstructed historical executable environments.
2. **Small contaminated sample.**16 FULL runs, four selected tasks, one trial per condition/version;44 cycles and60 candidates are correlated. Tasks have been inspected repeatedly and informed fixes. No representative sampling, held-out confirmation or statistical causal attribution exists. Other task domains may benefit.
3. **Ceiling effect.**10/16 C0s score1, only six have rubric headroom.0/8 twice is not proof that useful reasoning is impossible. Conversely none of the six remaining cases gains encoded quality; ceiling alone is not a complete explanation.
4. **Evaluation omissions.** Frozen BA-008 regex can miss Markdown premise corrections; native delimiter extraction can retain in-band prefixes; code evaluator tests only finite cases and may extract one valid function from faulty surrounding prose. BA-002 non-integer/boolean semantics and comments are not fully checked. Malformed BA-009 JSON can bypass claim-oriented counters. Equal scores do not mean equal safety/quality. No historical scores/labels were changed or retrospectively reevaluated.
5. **Independent evidence absent.** No runtime trusted tool verifier/executed evidence; model-generated tests/hypotheses and same-model judgments are not independent evidence. New logical derivations could still be valid without new observations, so H6 is a necessary limitation for missing-data tasks, not a universal explanation.
6. **Model/runtime factors.** One qwen3:4b digest; no stronger-model contrast. Temperature/sampling, seed imperfections, in-band deliberation, context/output caps and hardware/load can influence outputs. New pilot server drift .35.1→.40.0 has unknown timing; old Alpha.35.0 versus old pilot.35.1 also differs. Identical request bytes/seeds sometimes produce different responses. No version-causal wall/quality comparison is justified.
7. **Protocol and valid plans.** Some valid conceptual changes are discarded for invalid IDs, so bad-plan category includes protocol mediation. A model ignoring a vague generic fallback does not demonstrate failure to execute a good plan. Valid preservation wording may still be insufficient for a complex rewrite. Narrow tasks and three-cycle caps could hide longer-horizon gains; no evidence permits paying for them here.
8. **Unknown semantic ground truth.** Issue equivalence is normalized text/ID plus cautious Jaccard/polarity, not semantic entailment. Selected topic differs from critique allegation and repair objective. Manual categories are local interpretations with stated reasons, not universal automatic labels. None of57 model findings has new executed support, but some finite/task-stipulated observations are grounded. Unsupported does not mean false. Genuinely distinct validated proportion is unavailable.
9. **Selection ambiguity.** No higher-scoring child exists, weakening the stronger H5 claim that generated gains are hidden. Good C0 preservation fails once on score and also qualitatively in old BA-008. Safety/format losses can be outside score. REVISE/provisional/stop labels cannot be treated as false rejection/verification interchangeably.
10. **Progress missingness.** Old cycle-progress counters/reasons are absent, notzero. New22 records show churn, caps and mandatory blockers; no NO_PROGRESS stop is not by itself a detector defect. Current progress filtering is not empirically measured for useful stopping or saved cost.
11. **Cost bounds.** Completed physical usage is known and reconciled; provider latency differs from wrapper and run wall. Interrupted3 started calls have unknown consumption, no complete energy/currency record. Per-finding causal cost cannot be split from multi-finding calls. No exact counterfactual savings claim.
12. **Counterfactual identity.** A/C saved text/state scores are observable but changed guard/reconciliation/future outputs are partial. B is an unavailable-runtime retrospective oracle. D/E only label eligibility/local transitions; outcomes after divergence require new inference and are not invented.
13. **Alternative explanations.** Better independent judges might detect useful unscored corrections; uncertainty handling may improve despite flat score; stronger model could execute valid plans; protocol caps may create artificial failures; entirely different tasks may reward branches. No intervention rules these out. Persistent malformed format and ignored valid corrections still provide concrete counterexamples to treating activity as quality.
14. **Recommended experiment.**Two tasks/two repeats cannot estimate broad superiority or rare safety rates. Expected ~101min uses old purpose means with significant drift and output-size uncertainty; hard caps may end incomplete. No claim of a powered or guaranteed-complete study; holdout needs separate later authorization.
15. **Scope and packaging.**The Data analysis/report skill's evidence principles were used; its web/report-app publication route was skipped because this user explicitly requires local research Markdown/CSV and prohibits publication. All new scripts/artifacts live only in architecture_review_v1. No Engine/Harness or historical file was changed. No new task/evaluator, adapter, architecture or live experiment was implemented.

Missing data remain blank/null/UNKNOWN: old no-progress records, external world truth, untested semantics, causal operator attribution, currency/electricity cost, interrupted request consumption and unobserved counterfactual branches. Primary revision categories summarize the available local failure chain without closing these uncertainties. Recommendation D preserves the option to discover a useful architecture through better measurements; it is not a claim that END is universally invalid.
''')

print('Authored',len(list(OUT.glob('*.md'))),'Markdown reports from reconciled historical data; no inference.')
