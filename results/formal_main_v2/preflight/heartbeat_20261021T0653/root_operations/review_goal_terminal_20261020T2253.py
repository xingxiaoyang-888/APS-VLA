from pathlib import Path
from collections import Counter,defaultdict
import hashlib,importlib.util,json,sys,re,numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0653';BASE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';Q=P/BASE/'attempt01'
def h(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):z.update(b)
 return z.hexdigest()
def rd(p):return json.loads(p.read_bytes())
def jl(p):return [json.loads(x) for x in p.read_bytes().splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
def sig(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())
def load(p,pin,name):
 assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
checks=0
def need(x,msg):
 global checks
 if not x:raise AssertionError(msg)
 checks+=1
obs=rd(R/B/'live_observation.json');need(h(R/B/'live_observation.json')=='b16ee5b23e3ab2e4a7edea7734bbf2871e0b936b51b6800e41c20fdfc4a8feac','frozenSlurm');row=obs['observation']['rows']['3054127'];need(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['elapsed_seconds']==840 and row['gpus']==1,'terminal840')
entry=load(R/'scripts/ops/formal_goal_paired_input_gate_v1/entry.py','1e8caecfda12f1f0a1d55a5652e9c300d25dff5fb0cf071cf4555a68b8605977','goal2253rootentry');inv,wrapper,ctx,legacy=entry.prepare_original()
pkg=rd(P/'scripts/ops/formal_goal_paired_input_gate_v1/package_manifest.json');need(h(P/'scripts/ops/formal_goal_paired_input_gate_v1/package_manifest.json')=='7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec','manifest')
for path,pin in pkg['files'].items():need(h(R/path)==h(P/path)==pin,'sameR_P_package:'+path)
complete=rd(Q/'outer/completion.json');need(complete['status']=='returned_58_engineering_only' and complete['exit_code']==0 and complete['errors']==[] and complete['original_runtime_restored'] is True and complete['scientific_trials_added']==0,'completion')
outer=jl(Q/'outer/events.jsonl');need(h(Q/'outer/events.jsonl')==complete['raw_event_sha256'],'outerhash');need(all(x['seq']==i and x['job_id']=='3054127' and x['scientific_trials_added']==0 for i,x in enumerate(outer)),'outerseq')
with legacy.source_imports(entry.S):
 runtime=ctx['runtime'];contract=ctx['execution_contract'];orig=ctx['original_plan'];assets=runtime.expected_asset_identities(project_root=P,source_root=entry.S,contract=contract['runtime_contract'],asset_contract=orig['invocation'].get('downstream_asset_compatibility'));proof=runtime.verify_runtime_events(outer,contract['runtime_contract'],expected_asset_identities=assets)
need(proof==outer[-1]['runtime_proof'] and proof['all_source_and_binding_contexts_restored'],'runtimeindependentreconstruction')
prefix=rd(P/'scripts/ops/formal_goal_paired_input_gate_v1/prefix58.json')['rows'];entry.validate_prefix(inv,legacy,prefix)
trials=jl(Q/'original_run/trials.jsonl');need(Counter(x['event'] for x in trials)=={'invocation':1,'start':58,'result':58},'trialevents');results=[x for x in trials if x['event']=='result'];starts=[x for x in trials if x['event']=='start'];need(trials[0]['slurm_job_id']=='3054127','onlyjobinvocation')
identity_keys=['trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method','environment_seed','runtime_seed'];need([{k:x[k] for k in identity_keys} for x in starts]==[{k:x[k] for k in identity_keys} for x in prefix],'startprefix');need([{k:x[k] for k in identity_keys} for x in results]==[{k:x[k] for k in identity_keys} for x in prefix],'resultprefix')
events=jl(Q/'observer/events.jsonl');captures=[x for x in events if 'event_index' in x];need(len(captures)==3513 and [x['event_index'] for x in captures]==list(range(1,3514)),'capturesequence');ce={x['event_index']:x for x in captures}
for x in captures:need(x['scientific_trials_added']==0 and x['invariants']=={'global_rng_unchanged':True,'object_identity_and_bytes_unchanged':True,'passive_sim_and_environment_rng_unchanged':True},'passiveinvariant')
blobs={}
def gather(x):
 if isinstance(x,dict):
  if isinstance(x.get('path'),str) and x['path'].startswith('blobs/'):
   need(set(x)=={'path','sha256','bytes'},'blobrefshape');need(re.fullmatch(r'blobs/[0-9a-f]{64}\.(bin|rng\.json)',x['path']) is not None,'bloballowlist');need(Path(x['path']).name.startswith(x['sha256']+'.'),'blobname')
   need(x['path'] not in blobs or blobs[x['path']]==x,'duplicateblobref');blobs[x['path']]=x
  for v in x.values():gather(v)
 elif isinstance(x,list):
  for v in x:gather(v)
for x in captures:gather(x)
actual={p.relative_to(Q/'observer').as_posix() for p in (Q/'observer/blobs').iterdir()};need(actual==set(blobs),'allblobsreferenced_exact_noextras')
for name,v in blobs.items():
 p=Q/'observer'/name;need(p.is_file() and p.resolve()==p and not p.is_symlink(),'blobregular');need(p.stat().st_size==v['bytes'] and h(p)==v['sha256'],'blobexact')
gate=jl(Q/'observer/gate.jsonl');counts=Counter(x['event'] for x in gate);need(counts=={'paired_input_gate_open':1,'t0_pair_gate':58,'query_integrity_passed':940,'policy_step_executed':7302,'paired_input_gate_finished':1},'gateeventcounts');need(gate[0]['CPU_fixture_enabled'] is False and gate[0]['runtime_context']=='real_environment_engineering','realGPUcontext')
pairs={};queries=defaultdict(list);steps=defaultdict(list);before={(x['trial_identity']['trial_id'],x['control_step']):x for x in captures if x['phase'] in ('t0_query_before','query_before')}
for x in gate:
 need(x.get('scientific_trials_added')==0,'gate_sciencezero')
 if x['event']=='t0_pair_gate':
  cap=ce[x['capture_event_index']];need(cap['phase']=='t0_query_before' and cap['trial_identity']==x['trial_identity'],'pairprequery');key=x['trial_identity']['state_trial_id'];content=x['content'];need(set(content['components'])=={'agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'},'fivecomponents')
  for k,v in content['components'].items():need(v=={f:cap['observation_arrays'][k][f] for f in ['dtype','shape','bytes','sha256']},'paircomponent')
  if x['trial_identity']['method']=='A256_seed17':need(key not in pairs and x['pairing']=='baseline_recorded_before_first_policy','Abaseline');pairs[key]=content
  else:need(content==pairs[key] and x['pairing']=='exact_before_policy_pair_passed','Bprepairequal')
 if x['event']=='query_integrity_passed':
  tid=x['trial_identity']['trial_id'];queries[tid].append(x);pre=before[(tid,x['control_step'])];post=ce[x['capture_event_index']];need(post['phase'] in ('t0_query_after','query_after') and post['control_step']==pre['control_step'],'postpair')
  need(pre['observation_arrays']==post['observation_arrays'],'allquerystatebytesandmetadataequal')
  for k,v in x['content']['components'].items():need(v=={f:post['observation_arrays'][k][f] for f in ['dtype','shape','bytes','sha256']},'querycomponent')
 if x['event']=='policy_step_executed':steps[x['trial_identity']['trial_id']].append(x)
pertrial=[]
for idx,r in enumerate(results):
 tid=r['trial_id'];qq=queries[tid];ss=steps[tid];need(r['status']=='completed' and r['wait_steps']==r['configured_wait_steps']==10 and r['action_chunk']==8 and r['runtime_seed']==17 and r['environment_seed']==0,'resultconvention');need(len(qq)==r['policy_calls']==len(r['chunks']) and len(ss)==r['control_steps']==len(r['executed_actions']),'query_step_count');need(r['control_steps']<=300,'Goalbound');queue=[]
 for n,(record,chunk) in enumerate(zip(qq,r['chunks'])):
  need(record['control_step']==chunk['control_step']==n*8,'chunkorder')
  for name,meta in record['returned_actions'].items():
   raw=bytes.fromhex(meta['bytes_hex']);arr=np.asarray(chunk[name],dtype=np.dtype(meta['dtype']));need(arr.shape==tuple(meta['shape'])==(8,7) and np.isfinite(arr).all() and raw==arr.tobytes(order='C') and len(raw)==meta['bytes'] and sha(raw)==meta['sha256'],'returned_chunk_'+name)
  md=chunk['metadata'];need(md['future_head_calls']==0 and md['language_cache']=='disabled' and md['per_camera_budgets']==[128,128] and md['vision_calls']==md['scorer_calls']==md['packing_calls']==md['policy_calls']==1,'harddeployment');need(md['method']==r['method'][0] and md['suite']=='libero_goal' and md['training_seed']==17,'methodmetadata');need(md['selector_checkpoint_sha256']=={'A':'756e7033ed467d50c748ff2a6290a3c9f84928c4a5a30c3304669c9e5f28d928','B':'48cadc7b53914b87f4a7e8ef232bdcfe87bf94a1e28d8758e2db44d31e4ab2c3'}[r['method'][0]],'selectedcheckpoint')
  indices=md['retained_indices'];need(len(indices)==len(set(indices))==256 and indices==sorted(indices) and sum(x<256 for x in indices)==128 and all(0<=x<512 for x in indices),'hardTopkpacking')
  queue.extend(chunk['environment_actions'])
 for n,(rec,action) in enumerate(zip(ss,r['executed_actions'])):
  meta=rec['action'];raw=bytes.fromhex(meta['bytes_hex']);arr=np.asarray(action,dtype=np.dtype(meta['dtype']));need(rec['control_step']==n and arr.shape==(7,) and arr.tobytes()==raw and sha(raw)==meta['sha256'],'executed_stepbytes')
 need(np.array_equal(np.asarray(queue[:r['control_steps']],dtype=np.float64),np.asarray(r['executed_actions'],dtype=np.float64)),'exactemittedqueue')
 pertrial.append(dict(ordinal=idx+1,trial_id=tid,queries=len(qq),steps=len(ss),same_raw_actions=True,scientific_trials_added=0))
need(len(pairs)==29 and sum(len(x) for x in queries.values())==940 and sum(len(x) for x in steps.values())==7302,'totalrealcounts')
# Registration is engineering only. It is not an exact replay of the held old200.
need(gate[-1]['old_cause_identified'] is False and gate[-1]['old_failure_repaired'] is False and gate[-1]['original200_HOLD'] is True and gate[-1]['new_Goal_science_HOLD'] is True,'limits')
files=['outer/completion.json','outer/events.jsonl','original_run/panel.json','original_run/config.json','original_run/trials.jsonl','original_run/closed_loop_report.json','observer/events.jsonl','observer/gate.jsonl']
allow=[dict(source=str(Q/rel),relative='attempt01/'+rel,sha256=h(Q/rel),bytes=(Q/rel).stat().st_size) for rel in files]
for p in [P/'results/slurm/cti-goal-paired-input_3054127.out',P/'results/slurm/cti-goal-paired-input_3054127.err',*sorted((P/'results/formal_main_v2/adapter_invocations').glob('3054127_*'))]:
 need(p.is_file() and p.suffix in ('.out','.err','.json','.jsonl'),'onlyexactengineeringlogs');allow.append(dict(source=str(p),relative='original_logs/'+p.name,sha256=h(p),bytes=p.stat().st_size))
need(len(allow)==12,'eightmetadata_fourlogs')
ctl=load(R/'scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','goal2253rootctl')
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statep=R/'results/experiment_supervisor/state.json';state_sha=h(statep);need(state_sha=='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f','stateunchanged')
 out=dict(schema='formal_main_v2',status='root_engineering_terminal_verified_pending_independent',job_id='3054127',Slurm_status='COMPLETED',Slurm_exit_code='0:0',GPU_seconds=840,check_count=checks,real_environment_engineering=True,prefix_trials=58,paired_inputs=29,accepted_queries=940,executed_steps=7302,all_runtime_sources_reconstructed=True,all_passive_capture_invariants=True,per_trial=pertrial,metadata_allowlist=allow,blob_allowlist=[blobs[k] for k in sorted(blobs)],blob_count=len(blobs),blob_bytes=sum(v['bytes'] for v in blobs.values()),old200_adopted=False,new_Goal_science_HOLD=True,old_cause_identified=False,old_failure_repaired=False,new_scientific_trials=0,new_GPU_submissions=0,final_release=False,slurm_observation=dict(path=B+'/live_observation.json',sha256=h(R/B/'live_observation.json')),state_sha256_unchanged=state_sha)
 p=R/B/'Goal_terminal_root_review.json';p.open('x').write(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n');need(h(statep)==state_sha,'statepost');print(json.dumps({k:out[k] for k in ['status','job_id','GPU_seconds','check_count','prefix_trials','paired_inputs','accepted_queries','executed_steps','blob_count','blob_bytes']}));print(json.dumps({'root_review':str(p.relative_to(R)),'sha256':h(p)}))
