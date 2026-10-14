"""Build explicit staging lists and publication policy; no Git mutation."""
import collections,csv,hashlib,json,subprocess,sys
from pathlib import Path
from sync_audit import ROOT,OUT,git,save,sha
rows=list(csv.DictReader((OUT/'FILE_INVENTORY.csv').open(encoding='utf-8')))
before=json.loads((OUT/'LOCAL_FILE_HASHES_BEFORE.json').read_text());after={p:sha(ROOT/p) for p in before if (ROOT/p).is_file()}
changed=[p for p,h in before.items() if after.get(p)!=h]
assert changed==['.gitignore'],changed
save('LOCAL_FILE_HASHES_AFTER_POLICY.json',after)
refs=git('for-each-ref','--format=%(refname:short) %(objectname) %(subject)','refs/remotes/origin')
save('REMOTE_AUDIT.json',{'fetch_succeeded':True,'origin_url':git('remote','get-url','origin').strip(),'push_url':git('remote','get-url','--push','origin').strip(),'origin_main':git('rev-parse','origin/main').strip(),'ahead_behind':git('rev-list','--left-right','--count','HEAD...origin/main').strip(),'remote_refs':refs,'pull_merge_performed':False})
eligible={r['path'] for r in rows if r['recommendation']=='INCLUDE'}|{'.gitignore'}
raw=git('status','--porcelain=v1','-z','--untracked-files=all',raw=True).decode('utf-8')
entries=[{'state':e[:2],'path':e[3:]} for e in raw.split('\0') if e]
groups={str(i):[] for i in range(1,5)};excluded=[]
for entry in entries:
    rel=entry['path'];p=ROOT/rel
    if rel.startswith('checkpoint_20261013/') and p.is_file() and not any(x in ('scratch','staging_review') for x in p.relative_to(OUT).parts) and p.name!='SYNC_RECEIPT.json' and p.suffix!='.paths':eligible.add(rel)
    if rel not in eligible or entry['state']==' D' or not p.is_file():excluded.append(entry);continue
    if p.stat().st_size>10*1024*1024:raise AssertionError('Large staging proposal: '+rel)
    top=rel.split('/')[0]
    group='1' if top in ('end_engine','tests','pyproject.toml','.gitignore') else '4' if top.startswith('experimental_task_pack_') else '3' if top in ('benchmark_alpha','benchmark_beta','benchmark_beta_gemini','v035_core_regression_pilot','v0351_core_regression_pilot','architecture_review_v1','independent_review_package_v1') else '2'
    groups[group].append(rel)
messages={'1':'feat(engine): checkpoint END Engine v0.3.5.2 and offline regressions','2':'docs(engine): preserve implementation reports and offline validation','3':'docs(research): checkpoint historical studies and reproducibility evidence','4':'test(evaluation): preserve rubric drafts and safety boundary research'}
for i,paths in groups.items():
    assert paths
    (OUT/('stage-'+i+'.paths')).write_bytes(('\0'.join(sorted(paths))+'\0').encode('utf-8'))
    # Lists contain explicitly reviewed file paths, not directory-wide git add.
save('STAGING_PLAN.json',{'groups':{i:{'message':messages[i],'files':len(paths),'bytes':sum((ROOT/p).stat().st_size for p in paths),'paths':sorted(paths)} for i,paths in groups.items()},'remaining_dirty_proposal':excluded,'large_files_published':False,'deletions_staged':False})
exclusions=[r for r in rows if r['recommendation']!='INCLUDE']
with (OUT/'EXCLUSIONS.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(exclusions[0]));w.writeheader();w.writerows(exclusions)
sizes=collections.Counter()
for r in exclusions:sizes[r['reason']]+=int(r['size_bytes'])
policy='''# END Engine v0.3.5.2 research checkpoint publication policy

This checkpoint preserves existing uncommitted work on a new branch from local HEAD. No scientific data or Engine behaviour is changed. Original HEAD/main remains6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7. Origin fetch confirmed no divergence or newer branches. Source version0.3.5.2 and fingerprint29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82 are checked, not recreated. See LOCAL_BASELINE/REMOTE_AUDIT/FILE_INVENTORY/STAGING_PLAN and validation/TEST_RESULTS.

## Included source and research evidence

Engine implementation, schemas, regression tests, packaging, README, all implementation/validation reports; benchmark Alpha/Beta/Gemini definitions and compact raw trial/evaluation/call records, frozen pilots, architecture review, independent review evidence; all four evaluator pack source/task/fixture/contract/test/provenance files except explicit local artifacts below. Synthetic fixtures remain synthetic, drafts remain drafts; rubric exp-pack-1.1.0-draft independent approval PENDING. Historical live studies are preserved as prior-version records, not presented as live0.3.5.2 evaluation. No live inference is run for this checkpoint. No Harness changes. Paths are explicit staging lists; no repository-wide add or history rewrite.

## Local research artifacts and exclusions

Python environments/caches/build outputs, existing ignored root trajectories, generated ZIP snapshots and validation/scratch extraction/test directories remain local. Transient live_progress.log is excluded from new staging. Its already tracked initial version stays in Git history; the local modification remains unstaged. No tracked cache or evidence is removed from history.

One unique large scientific replay file (15,443,273 bytes) remains local pending an explicit artifact-storage decision: experimental_task_pack_v1_safety_boundary/validation/HISTORICAL_SINGLE_RESULTS.json; SHA2566708d3490d413c90c4b60363a2d95d9d390ef7268222505c7d153d246f8a0c52. Two identical scratch copies are also excluded. No files exceed25/50/100MiB. Compact OLD_TO_NEW_OUTCOMES.csv, candidate fixtures, active code/tests/contracts, freeze manifest and detailed paired/probe records are included. The complete replay JSON is also in the existing LOCAL ZIP END_Experimental_Safety_Boundary_Review_v1.zip (2,232,598 bytes; SHA256ac523ee358aa07a42479f7177191d5b42865597c10648c4f0c4789a7c1c59c08). This ZIP is preserved locally, not uploaded or called an externally accessible archive.

Proposed separate storage: after explicit approval, place the unchanged review ZIP/large original in owner-controlled durable artifact storage with these hashes, access policy and public immutable download URL recorded. No storage service/LFS is configured here. Committed source can replay fixture evaluation offline, but Git alone does not contain every original generated artifact. Do not claim that all frozen detailed data is remotely archived/accessibly reproduced. FILE_INVENTORY/EXCLUSIONS give every path,size,hash,reason.

Twenty synthetic trajectory paths were already deleted in the working tree at baseline. They are not staged as deletions. Their original contents remain recoverable in the initial commit and are retained in this branch's Git tree. New replacement-UUID trajectory records are committed verbatim with current research records; this task does not infer or alter their provenance. Remaining deletion paths are listed in STAGING_PLAN. No local file is deleted/restored/overwritten for cleanup.

## Ignore changes

- /END_Experimental_*.zip: root review snapshots remain local; receipts preserve hashes.
- /experimental_task_pack_v1*/validation/scratch/: extracted duplicate bundles and temp files only; research source/records are not broadly ignored.
- /checkpoint_20261013/validation/scratch/: new offline temporary files only.
- Exact safety-boundary HISTORICAL_SINGLE_RESULTS.json: large local replay record deferred with hash/provenance, not deleted.
- **/live_progress.log: transient progress logs; tracked files are not removed or silently staged.
- /checkpoint_20261013/SYNC_RECEIPT.json: post-push local receipt carries resulting commit hashes without a self-referential publication commit.
- /checkpoint_20261013/stage-*.paths and staging_review/: operational NUL path lists and per-commit index reviews remain local; the readable STAGING_PLAN.json remains version controlled.

## Security and privacy

Proposed content and all543 reachable historical text blobs were scanned for provider/GitHub/HuggingFace/private-key signatures and credential-bearing assignments. No secret candidates or assignment-review candidates found. A legacy CP1252 validation log is decoded for audit and preserved byte-identically. Local development paths, temp executable paths, loopback Ollama URLs, normative example.invalid references and metadata are provenance/development markers, not account authentication. They are not rewritten inside frozen reports. No private provider config/model weights/licenses/third-party datasets were found in the reviewed source/evidence selection; studies use supplied synthetic task definitions and recorded model outputs. This is a local scan, not a guarantee against every possible secret encoding.

Commit authorship uses the configured GitHub noreply identity. Existing .gitattributes * -text preserves exact source/research bytes despite core.autocrlf. Index blobs must match reviewed working bytes. The original data hash inventory includes ignored/local artifacts so final verification can confirm all original bytes except the authorised .gitignore change.

Initial fetch was not executed because automatic approval review could not refresh the Codex account token. After user sign-in, the approved fetch succeeded. No bypass or alternative publication channel was used. Engine/evaluator tests are network-blocked and redirect temp output to this checkpoint directory, leaving old validation records untouched.

Next scientific action: independent safety-boundary evaluator review. No claim of reasoning superiority, release/tag, main merge or live experiment follows from this checkpoint.
'''
(OUT/'PUBLICATION_POLICY.md').write_text(policy,encoding='utf-8',newline='\n')
print(json.dumps({'groups':{i:{'files':len(paths),'bytes':sum((ROOT/p).stat().st_size for p in paths),'message':messages[i]} for i,paths in groups.items()},'excluded_size_bytes_by_reason':dict(sizes),'deletions_unstaged':sum(e['state']==' D' for e in excluded)}))
