from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
D='results/formal_main_v2/engineering/goal_t0_probe_20261020T1418'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,b):
 assert p.is_relative_to(R) or p.is_relative_to(P)
 for x in (p,*p.parents):assert not x.is_symlink()
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
 return dict(path=str(p),sha256=h(p))
def dump(x):return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('prepg1530c',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
hand=R/'.local/goal_t0_probe_candidate_20261020T1418/handoff.json';assert h(hand)=='774051f9132e194296d9d84978e69f9622a229ef912f990ce96bf7def7f3d984'
ind=R/'.local/goal_t0_probe_independent_20261020T1530/independent_review_v2.json';assert h(ind)=='70a819ba7f5e715a6042b675399599fe28cd0f56d6e43be6318e57360535dcbc'
iv=read(ind);assert iv['status']=='passed' and iv['config_sha256']=='773594fc7ccaeb51d44b348283634dcb6461945d503893fcdb33ce3b12e118ff' and iv['entrypoint_sha256']=='4d0eec76dddf7574521231911c29e0df8dbbeb372910d615c00914451a1cb92c'
pub=R/'.local/object256s23_consumer_candidate_20261020T1530/minimum_P_publication.json';assert h(pub)=='78132fb11a6b37fb7900d225e584d9bd03a4928357267d7362d87aa8495f808e'
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);rows=[]
 for item in read(hand)['proposed_publication']:
  src=Path(item['source']['path']);dest=Path(item['destination']);assert src.is_relative_to(R/'.local/goal_t0_probe_candidate_20261020T1418') and dest.is_relative_to(P/D/'source') and h(src)==item['source']['sha256']
  rows.append(put(dest,src.read_bytes()));rows.append(put(R/dest.relative_to(P),src.read_bytes()))
 for base in (R,P):rows.append(put(base/D/'independent_review.json',ind.read_bytes()))
 root=dict(schema='formal_main_v2',kind='root_bounded_engineering_probe_review',status='passed',reviewed_by='root',utc=datetime.now(timezone.utc).isoformat(),config_sha256=iv['config_sha256'],entrypoint_sha256=iv['entrypoint_sha256'],independent_review_sha256=h(ind),maximum_GPU_jobs=1,Slurm_hard_wall_seconds=1800,application_soft_seconds=1680,soft_timeout_is_best_effort=True,LIBERO_reset_finally_continue_swallows_exceptions=True,internal_reset_retries_not_counted_by_external_12_query_limit=True,original_200_trial_model_renderer_CUDA_history_not_replayed=True,ABBA_repeats=3,maximum_external_queries=12,maximum_dummy_steps=120,policy_actions_executed=0,automatic_retry=False,scientific_release=False,original_goal200_remain_HOLD=True,interrupted_NPZ_is_failed_evidence_only=True,scope='Only pre-registered Goal development task2/source42 and exact original A256/B256 seed17 checkpoint metadata. No new scientific results or final values.',checks=['Exact four source bytes and original-prefix AST/invocation preserved','Training method,loss,horizon,panel and original failed records unchanged','Future inputs absent from policy deployment; 0 policy actions applied','Candidate root-only authorization plus independent source/config binding','Maximum hard compute allocation 1GPU30min counted against8; no requeue; gpu4020 excluded by dispatcher'])
 rootb=dump(root)
 for base in (R,P):rows.append(put(base/D/'root_review.json',rootb))
 auth=dict(schema='formal_main_v2',kind='root_bounded_engineering_probe_authorization',status='approved',reviewed_by='root',config_sha256=iv['config_sha256'],entrypoint_sha256=iv['entrypoint_sha256'],root_review=dict(path=str(P/D/'root_review.json'),sha256=h(P/D/'root_review.json')),independent_review=dict(path=str(P/D/'independent_review.json'),sha256=h(ind)),maximum_gpu_jobs=1,maximum_wall_seconds=1800,counts_against_8_GPU_slots=True,scientific_release=False,original_goal_failure_retained=True,automatic_retry=False,best_effort_application_timeout_not_hard_bound=True,does_not_replay_original_200_trial_history=True,controller_job_id='3034538',maximum_external_queries=12,maximum_dummy_steps=120,policy_actions_executed=0,source_index=42,task_id=2,failed_scientific_job_id='3049679',excluded_nodes=['gpu4020'])
 for base in (R,P):rows.append(put(base/D/'root_authorization.json',dump(auth)))
 # Actual P metadata validation only, never --run-gpu.
 pre=subprocess.run([sys.executable,'-B',str(P/D/'source/probe.py'),'--config',str(P/D/'source/config.json'),'--config-sha256',iv['config_sha256']],capture_output=True,text=True,timeout=90)
 rows.append(put(R/B/'Goal_t0_actual_P_prepare.json',dump(dict(returncode=pre.returncode,stdout=pre.stdout,stderr=pre.stderr))))
 assert pre.returncode==0 and json.loads(pre.stdout)['status']=='cpu_prepared_not_GPU_run'
 manifest=R/'.local/object256s23_consumer_candidate_20261020T1530/attempt01/development.json';assert h(manifest)=='5f2bdcac8752c0cd06ad8dcb67114920b642db1415f6a88e1335d6c9f10fb028'
 rel='results/formal_main_v2/execution/object256seed23_source_bridge_v1_20261020T1530/libero_object_k256_seed23_development.json'
 for base in (R,P):rows.append(put(base/rel,manifest.read_bytes()))
 conf='configs/experiments/formal_main_v2/libero_object_k256_seed23.json';assert h(R/conf)=='1ca418462bc31685a5fcca7a346054f983e3f97157dfc6ff19fdb998efc13cb9';rows.append(put(P/conf,(R/conf).read_bytes()))
 assert h(state)==before
 out=dict(schema='formal_main_v2',kind='exact_root_publication_for_bounded_probe_and_metadata_only',utc=datetime.now(timezone.utc).isoformat(),status='published_exact_bytes',files=rows,probe_authorization=dict(path=D+'/root_authorization.json',sha256=h(R/D/'root_authorization.json')),probe_no_GPU_submitted=True,Object_manifest_CPU_only_no_runtime_bridge_or_submission=True,state_unchanged=True,state_sha256=before)
 put(R/B/'Goal_probe_and_Object_metadata_publication.json',dump(out))
 print(json.dumps(dict(status=out['status'],files=len(rows),authorization=out['probe_authorization'],receipt=B+'/Goal_probe_and_Object_metadata_publication.json',sha256=h(R/B/'Goal_probe_and_Object_metadata_publication.json'))))
