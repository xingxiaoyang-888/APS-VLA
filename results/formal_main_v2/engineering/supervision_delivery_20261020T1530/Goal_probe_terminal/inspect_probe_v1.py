"""Read-only terminal inspection of one registered engineering GPU probe. No science release."""
from pathlib import Path
import ast,base64,collections,hashlib,json,time,traceback
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/goal_probe_terminal_20261020T1530'
REL='results/formal_main_v2/engineering/goal_t0_probe_20261020T1418';B=P/REL;A=B/'attempt01'
FIELDS=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
ORDER=['A256_seed17','B256_seed17','B256_seed17','A256_seed17']*3
PHASES=['reset','set_init']+[p for n in range(1,11) for p in [f'wait{n:02d}_before',f'wait{n:02d}_after']]+['prequery','postquery']
AUTH='016ddbdc5d638e6271debb124d305dfdd7ccd3ef3d5f9816ac9fe13f4c3a3dda';CONFIG='773594fc7ccaeb51d44b348283634dcb6461945d503893fcdb33ce3b12e118ff';SOURCE='4d0eec76dddf7574521231911c29e0df8dbbeb372910d615c00914451a1cb92c'
CAP='results/formal_main_v2/preflight/heartbeat_20261020T2330/libero_object_k64_seed41_reservation_activation.json';CAPPIN='9b478a4da2e15a645400d0114675ae30010c62d5f7f646652a384e07ecfb4c15'
checks=[];reads={};started=time.perf_counter()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,allow_nan=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def ck(v,label):
 if not v:raise ValueError(label)
 checks.append(label)
def read(p,pin=None):
 p=Path(p);ck(p.is_absolute() and p.resolve()==p,'canonical source '+str(p));s=sha(p)
 if pin:ck(s==pin,'SHA '+str(p))
 reads[str(p)]={'sha256':s,'bytes':p.stat().st_size};return json.loads(p.read_bytes())
def out(name,x):
 p=D/name
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def meta(v):return dict(dtype=str(v.dtype),shape=list(v.shape),sha256=hashlib.sha256(v.tobytes()).hexdigest())
def diff(a,b):
 ans={}
 for k in a:
  av,bv=a[k],b[k];same=av.shape==bv.shape and av.dtype==bv.dtype
  ans[k]=dict(shape_and_dtype_equal=same,byte_equal=same and av.tobytes()==bv.tobytes(),max_abs_difference=float(np.max(np.abs(av.astype(np.float64)-bv.astype(np.float64)))) if same and av.size else None)
 return ans
def aggregate(v):
 h=hashlib.sha256()
 for k in FIELDS:
  a=np.ascontiguousarray(v[k]);h.update(k.encode()+str(a.dtype).encode()+str(a.shape).encode()+a.tobytes())
 return h.hexdigest()
def run():
 auth=read(B/'root_authorization.json',AUTH);savedauth=read(A/'root_authorization.json');c=read(B/'source/config.json',CONFIG);savedconfig=read(A/'registered_config.json');runtime=read(A/'runtime_identity.json');selected=read(A/'selected_development_state.json');completion=read(A/'completion.json','6cc57138c901684f20284f221ec3c76a468bbb47fb68f7f94c1b198e2558a853');capacity=read(R/CAP,CAPPIN)
 ck(auth==savedauth and c==savedconfig,'authorization and semantic config copies match exact registered originals')
 ck(auth['status']=='approved' and auth['entrypoint_sha256']==SOURCE and auth['config_sha256']==CONFIG and auth['policy_actions_executed']==0 and auth['maximum_external_queries']==12 and auth['maximum_dummy_steps']==120 and not auth['scientific_release'],'registered engineering scope')
 ck(c['order']==ORDER and c['resets']==12 and c['wait_steps']==10 and c['source_state_index']==42 and c['task_id']==2 and c['suite']=='libero_goal' and c['split']=='development','fixed development-only sequence')
 ck(c['maximum_wall_seconds']==1800 and not c['scientific_acceptance_enabled'] and not c['final_evaluation_enabled'],'bounded no release')
 for key in ['root_review','independent_review']:read(auth[key]['path'],auth[key]['sha256'])
 for name,pin in c['bundle_sources'].items():
  p=B/'source'/name;ck(sha(p)==pin,'exact executed source '+name);reads[str(p)]={'sha256':pin,'bytes':p.stat().st_size}
 ck(c['bundle_sources']['probe.py']==SOURCE,'source tied authorization')
 for ref in c['pinned_inputs'].values():
  p=Path(ref['path']);ck('sealed' not in p.name.lower() and p.resolve()==p,'nonsealed canonical input');ck(sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes'],'registered input '+str(p));reads[str(p)]={'sha256':ref['sha256'],'bytes':ref['bytes']}
 panel=read(c['pinned_inputs']['development_panel']['path'],c['pinned_inputs']['development_panel']['sha256']);matches=[x for x in panel['states'] if x['task_id']==2 and x['source_state_index']==42]
 ck(panel['split']=='development' and len(matches)==1 and matches[0]==selected,'actual selected current development state only')
 ck(selected['initial_state_sha256']==c['initial_state_sha256']==runtime['initial_state_sha256'],'initial state identity preserved')
 ck(runtime['source_state_index']==42 and runtime['task']['task_id']==2 and runtime['task']['task_name']==c['task_name'] and runtime['methods']==c['methods'],'runtime original methods and task')
 ck(runtime['runtime']['slurm_job_id']=='3050711' and runtime['node']=='gpu4023' and runtime['runtime']['gpu']=='NVIDIA L40','actual GPU/runtime identity')
 for key,pin in [('bddl',c['bddl_sha256']),('environment_wrapper',c['environment_wrapper_sha256'])]:
  x=runtime[key];ck(x['sha256']==pin and sha(x['path'])==pin,'original '+key)
 ck(completion['status']=='engineering_probe_completed_science_HOLD' and completion['exit_code']==0 and completion['job_id']=='3050711' and completion['real_GPU_probe_completed'],'completion actual engineering')
 ck(not completion['sealed_values_read'] and not completion['original_200_trials_replaced'] and not completion['retry_authorized'] and completion['scientific_trials_accepted']==0,'no original trial replacement or release')
 row=capacity['scheduler']['rows']['3050711'];ck(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['gpus']==1 and row['elapsed_seconds']==354 and row['node']=='gpu4023','immutable root Slurm terminal allocation')
 ck(completion['wall_seconds']<354<1800,'wall limit actual completion')
 eventpath=A/'events.jsonl';ck(sha(eventpath)==completion['events_sha256'],'completion binds all raw events');reads[str(eventpath)]={'sha256':sha(eventpath),'bytes':eventpath.stat().st_size}
 events=[json.loads(x) for x in eventpath.read_text().splitlines()];ck([x['seq'] for x in events]==list(range(len(events))),'event sequence contiguous');ck(all(x['monotonic_seconds']<=y['monotonic_seconds'] for x,y in zip(events,events[1:])),'event time monotonic')
 counts=collections.Counter(x['event'] for x in events);ck(counts['observation']==288 and counts['query_record']==12 and counts['environment_created']==counts['environment_closed']==12 and counts['rng_state']==94,'exact observations/queries/environments/RNG counts')
 ck(not any('exception' in x['event'] for x in events),'no recorded exception (reset internals not observable)')
 ck(events[0]['config_sha256']==CONFIG and events[0]['entrypoint_sha256']==SOURCE and events[-1]['event']=='probe_end' and events[-1]['exit_code']==0,'executed config source final event')
 for e in [x for x in events if x['event']=='rng_state']:
  v=e['state'];w={k:x for k,x in v.items() if k!='state_sha256'};ck(hashlib.sha256(dump(w).encode()).hexdigest()==v['state_sha256'],'RNG state digest '+str(e['seq']))
  t=v['torch']
  if t['imported']:
   ck(hashlib.sha256(base64.b64decode(t['cpu_base64'])).hexdigest()==t['cpu_sha256'],'torch CPU RNG digest '+str(e['seq']))
   for i,a in enumerate(t['cuda']):ck(hashlib.sha256(base64.b64decode(a['base64'])).hexdigest()==a['sha256'],'torch CUDA RNG digest '+str(e['seq'])+'/'+str(i))
 npzmanifest=[];observations={};queries=[];querysummary=[];phasehashes={};environmentstable=[]
 for n,mid in enumerate(ORDER,1):
  label=f'q{n:02d}_{mid}';obs=[x for x in events if x['event']=='observation' and x['label']==label];ck([x['phase'] for x in obs]==PHASES,'all24 observation stages '+label)
  rng=[x for x in events if x['event']=='rng_state' and x.get('label')==label];ck([x['phase'] for x in rng]==['before_reseed','after_reseed_before_factory','before_reset','after_reset','after_set_init','prequery','postquery'],'all7 RNG stages '+label)
  creates=[x for x in events if x['event']=='environment_created' and x['label']==label];closed=[x for x in events if x['event']=='environment_closed' and x['label']==label];ck(len(creates)==len(closed)==1,'environment lifetime '+label);ce=creates[0]
  ck(ce['method_id']==mid and ce['round']==(n-1)//4+1 and ce['order']==('AB' if (n-1)%4<2 else 'BA') and ce['position']==(n-1)%2+1,'balanced order '+label)
  identity=ce['identity'];ck(identity['environment_seed']==0 and identity['runtime_seed']==17 and identity['control_freq']==20 and identity['camera_names']==['agentview','robot0_eye_in_hand'] and identity['camera_heights']==identity['camera_widths']==[256,256],'fixed environment settings '+label)
  stable=json.loads(json.dumps(identity))
  for controller in stable['controllers']:controller['config']['sim'].pop('representation',None)
  environmentstable.append(stable)
  previous=None;observations[label]={}
  for e in obs:
   phase=e['phase'];rr=e['raw_archive'];p=Path(rr['path']);ck(p==A/'arrays'/f'{label}_{phase}.npz' and p.resolve()==p,'exact current dev array path '+label+'/'+phase)
   ck(sha(p)==rr['sha256'] and p.stat().st_size==rr['bytes'],'NPZ archive hash '+label+'/'+phase)
   with np.load(p,allow_pickle=False) as archive:
    ck(set(archive.files)==set(FIELDS)|{'sim_qpos','sim_qvel','sim_flattened'},'five observations plus sim state '+label+'/'+phase)
    values={k:np.ascontiguousarray(archive[k]) for k in FIELDS};sim={k:np.ascontiguousarray(archive['sim_'+k]) for k in ['qpos','qvel','flattened']}
   ck(all(np.isfinite(v).all() for v in [*values.values(),*sim.values()]),'finite arrays '+label+'/'+phase)
   ck({k:meta(v) for k,v in values.items()}==e['arrays'],'five per-array byte hashes '+label+'/'+phase)
   ck({k:meta(v) for k,v in sim.items()}==e['simulation'],'simulation array hashes '+label+'/'+phase)
   ck(aggregate(values)==e['aggregate_sha256'],'aggregate original hash formula '+label+'/'+phase)
   ck(e['difference_from_previous']==(diff(previous,values) if previous is not None else None),'actual preceding-stage array difference '+label+'/'+phase)
   observations[label][phase]=values;phasehashes.setdefault(phase,set()).add(e['aggregate_sha256']);npzmanifest.append({'source':str(p),'sha256':rr['sha256'],'bytes':rr['bytes'],'query_label':label,'phase':phase,'array_payload_verified':True,'copy_to_control_repo':False,'remain_on_server':True})
   previous=values
  query=[x for x in events if x['event']=='query_record' and x['label']==label];ck(len(query)==1,'one query record '+label);q=query[0];pre=observations[label]['prequery'];post=observations[label]['postquery']
  ck(q['method_id']==mid and q['wait_actions_executed']==10 and q['policy_actions_executed']==0 and q['input_unchanged'],'10 dummy and0 executed policy actions '+label)
  ck(q['prequery_sha256']==aggregate(pre) and q['postquery_sha256']==aggregate(post) and q['per_array_difference']==diff(pre,post),'query input alignment '+label)
  md=q['policy_metadata'];expected=next(x['identity'] for x in c['methods'] if x['identity']['method_id']==mid)
  ck(md['selector_checkpoint_sha256']==expected['checkpoint_sha256'] and md['pair_id']==expected['pair_id'] and md['suite']=='libero_goal' and md['training_seed']==17,'original selected checkpoint metadata '+label)
  indices=np.array(md['retained_indices']);ck(indices.shape==(256,) and len(np.unique(indices))==256 and (indices>=0).all() and (indices<512).all() and sum(indices<256)==sum(indices>=256)==128,'hard Top-k equal per-camera counts '+label)
  ck(md['future_head_calls']==0 and all(md[k]==1 for k in ['policy_calls','vision_calls','scorer_calls','packing_calls']),'one forward and no future head '+label)
  actions=np.asarray(q['environment_actions']);norm=np.asarray(q['normalized_actions']);ck(actions.shape==norm.shape==(8,7) and np.isfinite(actions).all() and np.isfinite(norm).all(),'finite8-action chunk only queried '+label)
  ck(hashlib.sha256(actions.tobytes()).hexdigest()==q['environment_action_sha256'],'query action payload hash '+label)
  ck(obs[-1]['seq']<q['seq']<closed[0]['seq'],'post-query capture before close '+label)
  queries.append({k:v for k,v in q.items() if k not in ['event','seq','utc','monotonic_seconds']})
  querysummary.append({k:q[k] for k in ['label','method_id','prequery_sha256','postquery_sha256','input_unchanged','query_seconds','wait_actions_executed','policy_actions_executed','environment_action_sha256']})
 ck(all(x==environmentstable[0] for x in environmentstable),'all12 environment/controller settings equal excluding memory-address repr')
 ck(len(list((A/'arrays').glob('*.npz')))==len(npzmanifest)==completion['arrays_written']==288,'exact NPZ manifest no extra or missing files')
 diag=completion['diagnostics'];ck(queries==diag['query_records'],'completion query records reconstruct exactly')
 pairs=[]
 for n in range(0,12,2):
  left,right=queries[n:n+2];a=observations[left['label']];b=observations[right['label']]
  pairs.append(dict(round=n//4+1,order='AB' if n%4==0 else 'BA',left=left['label'],right=right['label'],prequery_equal=left['prequery_sha256']==right['prequery_sha256'],postquery_equal=left['postquery_sha256']==right['postquery_sha256'],prequery_array_difference=diff(a['prequery'],b['prequery']),postquery_array_difference=diff(a['postquery'],b['postquery'])))
 ck(pairs==diag['pair_diagnostics'] and diag['all_current_probe_pairs_equal'] and all(x['prequery_equal'] and x['postquery_equal'] for x in pairs),'all6 paired t0 comparisons recomputed from actual NPZ')
 ck(diag['scientific_gate']=='HOLD' and diag['scientific_trials_accepted']==0 and not diag['retry_authorized'],'probe explicitly retains scientific hold')
 ck(completion['runtime_restoration']['all_source_and_binding_contexts_restored'] and not completion['runtime_restoration']['scientific_completion_inferred'],'runtime contexts restored no science inferred')
 # Source-only proof of the sole environment action site, no execution/import of probe runtime.
 tree=ast.parse((B/'source/probe.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='env' and n.func.attr=='step']
 ck(len(calls)==1 and ast.unparse(calls[0])=='env.step(list(DUMMY))','executed exact source only env.step is registered dummy action')
 diagnosis=read(c['pinned_inputs']['diagnosis']['path'],c['pinned_inputs']['diagnosis']['sha256']);original=diagnosis['mismatching_states'][0]
 current=sorted({q['prequery_sha256'] for q in queries});ck(current==[original['B_t0_observation_sha256']] and current[0]!=original['A_t0_observation_sha256'],'all current probe inputs match original B; original A mismatch not reproduced')
 ck(all(len(v)==1 for v in phasehashes.values()),'all recorded phases identical across fresh resets in this bounded probe')
 copyfiles=[]
 for p in sorted(A.iterdir()):
  if p.is_file():copyfiles.append({'source':str(p),'destination':str(R/p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size,'kind':'nonweight_engineering_record','copy_by_root_only':True})
 for ext in ['out','err']:
  p=P/f'results/slurm/cti-goal-t0-probe_3050711.{ext}';ck(p.is_file(),'registered Slurm log '+ext);copyfiles.append({'source':str(p),'destination':str(R/p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size,'kind':'original_Slurm_log','copy_by_root_only':True})
 out('npz_manifest.json',dict(job_id='3050711',count=288,total_bytes=sum(x['bytes'] for x in npzmanifest),files=npzmanifest,all_npz_remain_server=True,no_local_copy=True))
 out('nonweight_copy_plan.json',dict(status='exact_source_byte_plan_only_not_copied',files=copyfiles,files_count=len(copyfiles),total_bytes=sum(x['bytes'] for x in copyfiles),npz_excluded=True))
 out('checks.json',dict(status='passed',checks=checks,count=len(checks),inputs=reads,new_GPU_jobs=0,source_and_runtime_read_only=True))
 summary=dict(schema='formal_main_v2',kind='bounded_Goal_probe_terminal_read_only_check',status='passed_engineering_record_integrity_science_HOLD',job_id='3050711',reviewed_utc=datetime.now(timezone.utc).isoformat(),root_sacct_evidence={'path':CAP,'sha256':CAPPIN},allocation=row,allocated_GPU_seconds=354,allocated_GPU_hours=354/3600,cost_already_in_global_allocation_total=True,new_GPU_jobs=0,new_scientific_trials=0,external_queries=12,dummy_control_actions=120,policy_control_actions=0,recorded_NPZ=288,NPZ_array_payloads_verified=True,raw_NPZ_copied=False,event_count=len(events),RNG_events=94,event_counts=dict(counts),current_common_pre_and_post_hash=current[0],all6_AB_BA_pairs_equal=True,all_query_inputs_unmodified=True,all_phase_hashes_identical_across12_fresh_resets=True,original_mismatch_reproduced=False,original_A_hash=original['A_t0_observation_sha256'],original_B_hash=original['B_t0_observation_sha256'],original200_trial_history_replayed=False,original200_HOLD_unchanged=True,cause='Undetermined. Fresh reset/query probe did not reproduce the original history-dependent observation difference; it cannot identify or clear the original fault.',limitations=['Original200 rollout/reset/model-use history was not replayed.','LIBERO reset internal retry/exception swallowing is inherited and not instrumented; no recorded exception is not proof of no internal retry.','One model-loading order A then B; balanced AB/BA refers external query/reset order, not independent loading orders.','Application alarm is best effort; actual Slurm1800-second hard bound used, completed354 seconds.','No policy actions executed; no successful scientific rollout or release inferred.'],checkpoint_or_weight_bytes_read_by_terminal_review=False,only_fixed_development_state_values_read=True,sealed_values_read=False,state_registry_docs_Git_Slurm_mutations=False,checks_passed=len(checks),query_records=querysummary,CPU_wall_seconds=time.perf_counter()-started)
 out('terminal_summary.json',summary)
 readme='工程探针3050711记录完整性已通过只读复核：12查询、120等待动作、0策略执行；288个NPZ和五观测/模拟状态逐字节hash验证。354GPU秒已在全项目Slurm账内，不重复加账。12次t0均与原B相同，原A不一致未复现；原200试验仍HOLD，原因未确定。该探针不重放原完整200历史，不授权科学重试或部署修复。NPZ原件仅P服务器保存；nonweight_copy_plan.json供root精确回存，作者未复制生产结果、未改state/docs/Git、未提交GPU。\n'
 with (D/'README.md').open('xb') as f:f.write(readme.encode())
 files=[{'path':str(p.relative_to(R)),'relative_path':str(p.relative_to(D)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(D.rglob('*')) if p.is_file()]
 out('manifest.json',dict(status='sealed_read_only_terminal_check',files=files,file_count=len(files),total_bytes=sum(x['bytes'] for x in files),new_GPU_jobs=0,scientific_release=False))
 print(dump(dict(status=summary['status'],checks=len(checks),manifest={'path':str((D/'manifest.json').relative_to(R)),'sha256':sha(D/'manifest.json')},summary={'path':str((D/'terminal_summary.json').relative_to(R)),'sha256':sha(D/'terminal_summary.json')},copy_plan={'path':str((D/'nonweight_copy_plan.json').relative_to(R)),'sha256':sha(D/'nonweight_copy_plan.json')},files_to_copy=len(copyfiles),NPZ_left_on_server=288)))
try:run()
except BaseException as exc:
 out('failure.json',dict(status='terminal_check_failed_science_HOLD',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),checks_completed=checks,new_GPU_jobs=0,canonical_mutations=False));raise
