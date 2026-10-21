"""Exact immutable inputs for one Object development correction. No execution authority."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
BASE='scripts/ops/formal_object_single_error_v1'
PRIVATE='.local/object_single_error_candidate_20261020T2253'
EX='results/formal_main_v2/execution/object_single_error_v1'
OUT='results/formal_main_v2/libero_object/downstream/linked_policy_error_correction/task08_state0049_dense/attempt01'
RUN='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01'
OLD_PROOF='results/formal_main_v2/engineering/supervision_delivery_20261020T2253/Object599_independent'
PROOF_ARCHIVE='results/formal_main_v2/engineering/supervision_delivery_20261020T2253/Object599_independent/independent_review.json'
SCOPE_SHA='2d63670412abc28d3217242151ebf82f309ea93c1bb0e90478d817cf58d4a7b4'
METHODS=('dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17')
CELL='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
PAIR='c39b5da58df0b9e0e0e3e5de896906460bc4db2ec7d02b89f9254f04f1a2fb1a'
ACTION='9a5f5935100bb04bf8fb91f6405b94efc93de236b3a75896d0f08cdb2aa1ee02'
LOOP='src/cti_vla/evaluation/formal_trials.py'
LOOP_SHA='93a0971dbc8bbf4cb462490b0b00a337d92f015af83b798bb635163a9cb864f6'
RUNTIME='src/cti_vla/evaluation/libero_runtime.py'
RUNTIME_SHA='2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781'
MANIFEST='results/formal_main_v2/execution/libero_object_development_first_pair_v1.json'
INVENTORY='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INVENTORY_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
JOBS=('3021394','3021603','3021844')
ELAPSED=(386,1401,4926)
START={'byte_offset':50238056,'bytes':738,'line':1072,'sha256':'6533a08978eb006c39304bcf97829e3cfd0eef2145be3418c8d8bb02adf49c51'}
RESULT={'byte_offset':50238794,'bytes':44183,'line':1073,'sha256':'d7f134683c6e01c8667731c6ca6807290d91d7816d28197f48232de9bc271eb0'}
PINS={
 PROOF_ARCHIVE:'62c0a39784953b14f061ae7d161813f5e4bbfa5c8db39297e7047327b28463f7',
 RUN+'/trials.jsonl':'d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1',
 RUN+'/config.json':'ccbb680ade2c6cab783568ea34f2fd3d3ae9abb69a62e7088f53d7150dad27a5',
 RUN+'/panel.json':'6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a',
 MANIFEST:'34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a',
 'results/formal_main_v2/downstream_reviews/3021844.json':'004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37',
 OLD_PROOF+'/independent_review.json':'62c0a39784953b14f061ae7d161813f5e4bbfa5c8db39297e7047327b28463f7',
 OLD_PROOF+'/per_trial_independent_599.jsonl':'ddba2cf9b392fd49e445d8a264605bc0832de5196c0c39d3a7c950160d186155',
 OLD_PROOF+'/failed_trial_independent.json':'4fdfbc8b6acd4dae54d49e8af4f8ed06224424c3a66dd7b75845da1af2ed1b80',
 OLD_PROOF+'/single_error_correction_design.json':'0d5e6432f258cfb869a289bdfd6adb9b004e8d9beff88719d7a29b4f01847d19',
 OLD_PROOF+'/single_error_scope_guard_addendum.json':'b3dc7454b046393d4542e560cbb5d3a223c6e4113713108990c251ffb6002ea0',
 'configs/experiments/formal_main_v2_action_execution_compat_v1.json':'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe',
 LOOP:LOOP_SHA, RUNTIME:RUNTIME_SHA, INVENTORY:INVENTORY_SHA,
}
ENV={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':280}


def require(ok,message):
 if not ok:raise ValueError(message)


def sig(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def check_scope(scope):
 require(type(scope) is dict and sig(scope)==SCOPE_SHA,'exact independently reproducible scope required')
 return scope


def safe(root,relative):
 q=Path(relative)
 require(not q.is_absolute() and '..' not in q.parts and not any('sealed' in p.lower() for p in q.parts),'relative nonsealed metadata only')
 p=Path(root)/q
 require(p.resolve()==p and Path(root) in p.parents,'direct immutable input path required')
 return p


def read(root,relative,checksum):
 p=safe(root,relative);before=p.stat();raw=p.read_bytes();after=p.stat()
 require((before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),'input still changing')
 require(sha(raw)==checksum,'pinned input differs: '+relative)
 return raw


def validate_panel_manifest(panel,manifest,config,formal):
 require(sig(panel)==sig(json.loads(read(R,RUN+'/panel.json',PINS[RUN+'/panel.json']))),'full original100-state panel differs')
 require(sig(manifest)==sig(json.loads(read(R,MANIFEST,PINS[MANIFEST]))),'full original6-method scientific manifest differs')
 require(config['manifest']==manifest and config['panel_signature']==sig(panel),'original manifest/config mismatch')
 require(panel['suite']==manifest['suite']=='libero_object' and panel['split']==manifest['split']=='development','Object development only')
 require(manifest['environment']==ENV and tuple(r['identity']['method_id'] for r in manifest['methods'])==METHODS,'environment/method identities differ')
 # Both original full-manifest and full-panel guards run unchanged, before filtering.
 require(tuple(formal.validate_execution_manifest(manifest,registration_sha256=config['registration_sha256']))==METHODS,'original full manifest guard differs')
 formal.validate_trial_identities(panel,METHODS,SimpleNamespace(events=[]))
 ids=[formal._identity(panel,state,mid) for state in panel['states'] for mid in METHODS]
 require(len(ids)==600 and len({x['trial_id'] for x in ids})==600,'full600 logical identities required')
 target=[x for x in ids if x['trial_id']==CELL]
 require(len(target)==1 and target[0]['task_id']==8 and target[0]['source_state_index']==49 and target[0]['initial_state_sha256']=='85fbef5e8e439507095dea71a26e5af94291e1a451e2e698c1baded3cfebc062','wrong failed cell identity')
 return target[0]


def load_inputs(formal,root=R):
 require(Path(root)==R,'CPU metadata root is exact server R')
 data={p:read(root,p,h) for p,h in PINS.items()}
 panel=json.loads(data[RUN+'/panel.json']);config=json.loads(data[RUN+'/config.json']);manifest=json.loads(data[MANIFEST])
 identity=validate_panel_manifest(panel,manifest,config,formal)
 inventory=json.loads(data[INVENTORY])
 require(len(inventory['files'])==173,'frozen173 inventory missing')
 for p,h in inventory['files'].items():
  for base in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):read(base,p,h)
 raw=data[RUN+'/trials.jsonl'];require(raw.endswith(b'\n'),'old ledger incomplete tail')
 lines=raw.splitlines(keepends=True);events=[json.loads(x) for x in lines]
 for ref in (START,RESULT):
  require(raw[ref['byte_offset']:ref['byte_offset']+ref['bytes']]==lines[ref['line']-1] and sha(lines[ref['line']-1])==ref['sha256'],'failed raw byte/line identity differs')
 results={};starts={};seenjobs=[]
 for row in events:
  if row['event']=='invocation':
   require(row['slurm_job_id'] not in seenjobs,'duplicate old invocation');seenjobs.append(row['slurm_job_id'])
  elif row['event']=='start':
   require(row['trial_id'] not in starts,'repeated original start');starts[row['trial_id']]=row
  elif row['event']=='result':
   require(row['trial_id'] in starts and row['trial_id'] not in results,'invalid old result history');results[row['trial_id']]=row
 formal.validate_trial_identities(panel,METHODS,SimpleNamespace(events=events))
 require(tuple(seenjobs)==JOBS and len(starts)==len(results)==600,'old full600/3 jobs required')
 failed=results[CELL]
 require(failed['status']=='policy_error' and failed['success'] is False and failed['policy_calls']==8
  and len(failed['chunks'])==7 and len(failed['executed_actions'])==56,'exact retained failed outcome differs')
 normal={k:v for k,v in results.items() if v['status']=='completed'}
 require(len(normal)==599 and set(results)-set(normal)=={CELL},'only exact original one error allowed')
 pertrial=[json.loads(x) for x in data[OLD_PROOF+'/per_trial_independent_599.jsonl'].splitlines()]
 require(len(pertrial)==599 and {x['trial_id'] for x in pertrial}==set(normal),'599 proof coverage differs')
 for row in pertrial:
  ref=row['result'];require(sha(raw[ref['byte_offset']:ref['byte_offset']+ref['bytes']])==ref['sha256'],'599 raw proof byte differs')
 review=json.loads(data[OLD_PROOF+'/independent_review.json'])
 require(review['kind']=='Object599_legacy_compatibility_independent_review' and review['status']=='passed' and review['blockers']==[]
  and review['counts']=={'actions':91945,'chunks':11720,'trials':599} and review['all_original_GPU_seconds']==6713
  and review['production_reuse_authorized'] is False and review['whole600_compatibility_admitted'] is False,'599 independent CPU scope differs')
 old=json.loads(data['results/formal_main_v2/downstream_reviews/3021844.json'])
 require(old['scientific_complete'] is True and old['completed_trials']==600 and old['cost']['all_attempt_gpu_seconds']==6713,'original terminal/cost differs')
 alloc=old['cost']['allocations']
 require(tuple(x['job_id'] for x in alloc)==JOBS and tuple(x['elapsed_seconds'] for x in alloc)==ELAPSED
  and all(x['gpus']==1 and x['status']=='COMPLETED' and x['exit_code']=='0:0' for x in alloc),'exact original allocations required')
 scope=dict(schema='formal_main_v2',kind='Object_single_error_scientific_scope',suite='libero_object',stage='development',
  allowlist=[CELL],original_full_trial_count=600,original_methods=list(METHODS),original_states=100,
  identity=identity,scientific_environment=ENV,action_semantics_sha256=ACTION,
  original_manifest={'path':MANIFEST,'sha256':PINS[MANIFEST]},original_panel={'path':RUN+'/panel.json','sha256':PINS[RUN+'/panel.json']},
  original_config={'path':RUN+'/config.json','sha256':PINS[RUN+'/config.json']},legacy_raw={'path':RUN+'/trials.jsonl','sha256':PINS[RUN+'/trials.jsonl']},
  failed_start=START,failed_result=RESULT,legacy_allocations=alloc,legacy_gpu_seconds=6713,legacy_compatible_count=599,
  ordinary_resume=False,fresh_reset=True,rejected_query8_unknown=True,original_science_unchanged=True,
  original_sources=inventory['files'],loop_source_sha256=LOOP_SHA,run_episode_source_sha256=RUNTIME_SHA)
 return dict(scope=scope,panel=panel,manifest=manifest,config=config,raw=raw,results=results,normal=normal,proof=review,per_trial=pertrial)
