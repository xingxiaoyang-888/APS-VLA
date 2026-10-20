"""Independent terminal reconstruction of Goal job3054127. No scheduler/GPU/state writes."""
from pathlib import Path
from collections import Counter,defaultdict
from functools import lru_cache
from datetime import datetime,timezone
import ast,hashlib,importlib.util,json,os,sys,time,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/goal_terminal_independent_20261020T2253';STAGE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';O=P/STAGE/'attempt01';PKG='scripts/ops/formal_goal_paired_input_gate_v1';Q=P/PKG
MSHA='7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec';ASHA='9188b62f799d15bdb12eba29fc6c982f196661cd74e6632b210c3fa730f06180'
LIVE='results/formal_main_v2/preflight/heartbeat_20261021T0653/live_observation.json';LSHA='b16ee5b23e3ab2e4a7edea7734bbf2871e0b936b51b6800e41c20fdfc4a8feac'
KEYS=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')
OBS=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
counts=Counter();seen={};sections={};blobrefs=set();started=time.perf_counter()
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):
 d=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
 return d.hexdigest()
def ck(n,ok):
 counts[n]+=1
 if not bool(ok):raise AssertionError(n)
def watch(p,pin=None):
 p=Path(p);before=p.stat();v=h(p);ck('stable_file:'+p.suffix,before==p.stat());ck('regular_resolved_file',p.is_file() and p.resolve()==p and not p.is_symlink())
 if pin is not None:ck('expected_source_or_evidence_sha',v==pin)
 seen[str(p)]={'sha256':v,'bytes':before.st_size};return v

def read(p,pin=None):watch(p,pin);return json.loads(Path(p).read_bytes())
def lines(p):watch(p);raw=Path(p).read_bytes();ck('jsonl_final_newline',raw.endswith(b'\n'));return [json.loads(x) for x in raw.splitlines()]
def write(name,value):
 p=D/name
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':h(p)}
def load(p,name,pin):
 watch(p,pin);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('No process/network/GPU scheduling in terminal independent review')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in x.lower() for x in p.parts) or (p.name=='panel.json' and 'final' in p.parts) or p.name=='init_states_test.json':raise RuntimeError('No sealed final values')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('Write outside private terminal audit')
@lru_cache(maxsize=128)
def blobraw(rel):return (O/'observer'/rel).read_bytes()
def validate_blob(v):
 ck('blob_exact_schema',set(v)=={'bytes','path','sha256'});rel=v['path'];p=Path(rel)
 ck('blob_content_addressed_path',p.parts[0]=='blobs' and len(p.parts)==2 and p.name in (v['sha256']+'.bin',v['sha256']+'.rng.json'))
 ck('blob_manifest_link',blobmanifest['observer/'+rel]=={'bytes':v['bytes'],'sha256':v['sha256']});blobrefs.add('observer/'+rel);return blobraw(rel)
def validate_array(meta,raw):
 dtype=np.dtype(meta['dtype']);shape=tuple(meta['shape']);ck('nonobject_array',not dtype.hasobject)
 ck('array_bytes_hash_shape',len(raw)==meta['bytes']==int(np.prod(shape))*dtype.itemsize and sha(raw)==meta['sha256'])
 value=np.frombuffer(raw,dtype=dtype).reshape(shape);ck('numeric_array_finite',np.isfinite(value).all());return value

def capture_content(e,instruction_hash):
 return {'components':{k:{a:e['observation_arrays'][k][a] for a in ('dtype','shape','bytes','sha256')} for k in OBS},'instruction_utf8_sha256':instruction_hash}
def ident(x):return {k:x[k] for k in KEYS}
def expect_reject(name,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError):counts['negative_rejected:'+name]+=1
 else:raise AssertionError('negative not rejected:'+name)

def main():
 global blobmanifest
 sys.dont_write_bytecode=True;os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['CUDA_VISIBLE_DEVICES']='';sys.addaudithook(guard)
 live=read(R/LIVE,LSHA);row=live['observation']['rows']['3054127'];ck('clean_Slurm_terminal',row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['gpus']==1 and row['elapsed_seconds']==840 and row['node']=='gpu4015')
 absence=live['observation']['terminal_queue_absence_evidence'];ck('exact_bounded_queue_absence',absence['requested_ids']==['3054127'] and absence['original_returncode']==1 and absence['original_stderr'].strip()=='slurm_load_jobs error: Invalid job id specified' and not absence['original_stdout'].strip() and absence['user_queue_returncode']==0 and absence['user_queue_matched_rows']==[])
 ck('capacity_clear',live['capacity']=={'active_pairs':{},'findings':[],'occupied':[],'unknown':[]});ck('all_cost_unique_snapshot',live['formal_allocations']==270 and live['allocated_GPU_seconds']==1985302)
 rawline=[x.split('|') for x in absence['second_terminal_sacct'].splitlines() if x.strip()];ck('second_raw_sacct_exact_terminal',len(rawline)==1 and rawline[0][:4]==['3054127','COMPLETED','0:0','840'])
 firstline=[x for x in live['observation']['raw_sacct'].splitlines() if x.startswith('3054127|')];ck('full_raw_sacct_stable',firstline==absence['second_terminal_sacct'].splitlines())
 sections['Slurm']={'snapshot':{'path':LIVE,'sha256':LSHA},'job':row,'allocated_GPU_seconds':840,'all_270_allocation_GPU_seconds':1985302,'queue_error_not_job_failure':True}
 manifest=read(Q/'package_manifest.json',MSHA);ck('package_8',len(manifest['files'])==8)
 for rel,pin in manifest['files'].items():watch(P/rel,pin);watch(R/rel,pin)
 watch(R/PKG/'package_manifest.json',MSHA)
 entry=load(Q/'entry.py','_terminal2253_entry','1e8caecfda12f1f0a1d55a5652e9c300d25dff5fb0cf071cf4555a68b8605977')
 config=read(Q/'config.json');entry.validate_config(config)
 auth=read(P/STAGE/'root_authorization.json',ASHA);entry.validate_authorization(auth,h(Q/'config.json'),MSHA,h(Q/'entry.py'))
 for role in ('root','independent'):
  ref=auth[role+'_review'];entry.check_review(read(ref['path'],ref['sha256']),role,MSHA,h(Q/'config.json'))
 dispatch=read(P/STAGE/'held_dispatch_record.json');reservation=read(P/STAGE/'reservation.json');entry.validate_dispatch(dispatch,reservation,auth,ASHA,'3054127',h(P/STAGE/'reservation.json'))
 ck('unique_registered_dispatch',dispatch['new_submissions']==1 and dispatch['job_id']=='3054127' and dispatch['occupied_job_ids']==['3054127'])
 inv,wrapper,ctx,legacy=entry.prepare_original();prefix=read(Q/'prefix58.json',entry.PREFIX_SHA)['rows'];prefix_proof=entry.validate_prefix(inv,legacy,prefix)
 for path,pin in inv['watched_files'].items():watch(path,pin)
 for p,pin in [(entry.ORIGINAL,entry.ISHA),(entry.WRAPPER,entry.WSHA),(entry.LEGACY,entry.LSHA)]:watch(p,pin)
 inventory=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck('source173',len(inventory['files'])==173)
 for root in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):
  for rel,pin in inventory['files'].items():watch(root/rel,pin)
 # Complete raw subtree allowlist: all raw files, including empty locks, retained.
 blobmanifest={};artifactfiles={};stat_before={}
 for p in sorted(O.rglob('*')):
  ck('raw_path_resolved',p.resolve()==p and not p.is_symlink())
  if p.is_file():
   rel=p.relative_to(O).as_posix();v=watch(p);artifactfiles[rel]={'bytes':p.stat().st_size,'sha256':v};stat_before[rel]=p.stat()
   if rel.startswith('observer/blobs/'):blobmanifest[rel]=artifactfiles[rel]
 nonblob=set(artifactfiles)-set(blobmanifest)
 ck('exact_nonblob_rawfiles',nonblob=={'.original_run.adapter.lock','original_run/.evaluation.lock','outer/completion.json','outer/events.jsonl','observer/events.jsonl','observer/gate.jsonl','original_run/config.json','original_run/panel.json','original_run/trials.jsonl','original_run/closed_loop_report.json'})
 ck('complete_blob_inventory',len(blobmanifest)==10741 and sum(x['bytes'] for x in blobmanifest.values())==474068525)
 completion=read(O/'outer/completion.json','ebd1813f5dc506ccb7a286a5aa750e6e6fbb775f935bb54598df2314bc345d38');outer=lines(O/'outer/events.jsonl');events=lines(O/'observer/events.jsonl');gate=lines(O/'observer/gate.jsonl');ledger=lines(O/'original_run/trials.jsonl');report=read(O/'original_run/closed_loop_report.json');actualconfig=read(O/'original_run/config.json');panel=read(O/'original_run/panel.json','ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9')
 ck('outer_complete_only_engineering',completion['status']=='returned_58_engineering_only' and completion['exit_code']==0 and completion['errors']==[] and completion['job_id']=='3054127' and completion['authorization_sha256']==ASHA and completion['package_manifest_sha256']==MSHA and completion['observer_failed'] is False and completion['original_runtime_restored'] is True and completion['last_observer_abort'] is None and completion['last_paired_input_abort'] is None)
 for obj in (completion,gate[0],gate[-1]):ck('science_HOLD_zero_no_retry',obj['scientific_trials_added']==0 and obj.get('new_Goal_science_HOLD') is True)
 ck('completion_retains_fixed_scope',completion['observer_begun']==completion['observer_finished']==58 and completion['accepted_queries_retained']==940 and completion['executed_policy_steps_retained']==7302 and completion['paired_t0_checks_retained']==29 and completion['maximum_attempts']==1 and completion['automatic_retry'] is False and completion['final_release'] is False and completion['original_goal200_HOLD'] is True)
 ck('outer_rawhash',completion['raw_event_sha256']==h(O/'outer/events.jsonl'));ck('gate_rawhash',gate[-1]['event_sha256']==h(O/'observer/events.jsonl'))
 ck('production_not_CPU_fixture',gate[0]['CPU_fixture_enabled'] is False and gate[0]['runtime_context']=='real_environment_engineering' and gate[-1]['runtime_context']=='real_environment_engineering' and completion['runtime_context']=='real_environment_engineering')
 ck('observer_runtime_true_GPU',actualconfig['runtime']['gpu']=='NVIDIA L40' and actualconfig['runtime']['cuda']=='12.1' and actualconfig['runtime']['torch']=='2.2.0+cu121')
 ck('outer_order_ids',len(outer)==23 and [x['seq'] for x in outer]==list(range(23)) and all(x['job_id']=='3054127' and x['scientific_trials_added']==0 for x in outer))
 ck('fixed_arg_changes',outer[0]['original_argument_changes']=={'output':str(O/'original_run'),'stop_after':58} and outer[0]['original_actions_forced'] is False)
 ck('actual_compute_environment',all(outer[0]['environment'][k]==v for k,v in entry.THREADS.items()) and outer[0]['environment']['SLURMD_NODENAME']=='gpu4015' and outer[0]['environment']['SLURM_JOB_ID']=='3054127' and outer[0]['environment']['CUDA_VISIBLE_DEVICES']=='0')
 runtime=ctx['runtime'];contract=ctx['execution_contract']['runtime_contract'];expected=runtime.expected_asset_identities(project_root=P,source_root=S,contract=contract,asset_contract=ctx['original_plan']['invocation'].get('downstream_asset_compatibility'))
 runtime_proof=runtime.verify_runtime_events(outer,contract,expected_asset_identities=expected);ck('original_runtime_reverified',runtime_proof==outer[-1]['runtime_proof'] and runtime_proof['all_source_and_binding_contexts_restored'])
 astgate=load(Q/'ast_gate_v2.py','_terminal2253_ast',manifest['files'][PKG+'/ast_gate_v2.py']);_,_,rp=astgate.derive_run((S/'src/cti_vla/evaluation/libero_runtime.py').read_bytes());_,_,tp=astgate.base.derive_trials((S/'src/cti_vla/evaluation/formal_trials.py').read_bytes())
 astproof=next(x['proof'] for x in outer if x['event']=='prefix_observer_scope_enter');ck('recorded_AST_exact_CPU_rederived',astproof['run_episode']==rp and astproof['trial_loop']==tp)
 exitobs=next(x for x in outer if x['event']=='prefix_observer_scope_exit');ck('observer_scope_restored',exitobs['bindings_intact'] and exitobs['bindings_restored'] and exitobs['runner_raised'] is False)
 for e in outer:
  for path,pin in e.get('identity',{}).get('watched_files',{}).items():watch(path,pin)
 for path,pin in actualconfig['watched_files'].items():watch(path,pin)
 for rel,pin in actualconfig['source_files'].items():watch(S/rel,pin)
 ck('actual_manifest_original',actualconfig['manifest']==read(inv['execution_manifest'],inv['execution_manifest_sha256']))
 # Adapter and the original ledger agree without treating stop58 as full200.
 adapterpaths=list((P/'results/formal_main_v2/adapter_invocations').glob('3054127_*.json'));ck('one_adapter_attempt',len(adapterpaths)==1);adapter=read(adapterpaths[0]);adapterevents=lines(adapter['events_path']);ck('adapter_eventsha',adapter['events_sha256']==h(adapter['events_path']))
 ck('adapter_returns_partial_original200',adapter['status']=='returned' and adapter['runner_status']=='incomplete' and adapter['resume'] is False and adapter['output']==str(O/'original_run') and adapter['job_id']=='3054127' and adapter['frozen_source_unchanged'] and adapter['verified_frozen_file_count']==173 and adapter['old_ledger_prefix_unchanged'])
 ck('adapter_exact_ledger',adapter['before_ledger']['bytes']==0 and adapter['after_ledger']['sha256']==h(O/'original_run/trials.jsonl') and adapter['after_ledger']['events']==117 and adapter['after_ledger']['invocation_job_ids']==['3054127'] and adapter['after_ledger']['active_trial_ids']==[])
 starts=[x for x in ledger if x['event']=='start'];trials=[x for x in ledger if x['event']=='result'];ck('one_ledger_invocation',Counter(x['event'] for x in ledger)=={'invocation':1,'start':58,'result':58} and ledger[0]['slurm_job_id']=='3054127')
 ck('ledger_alternation',all(ledger[2*i+1]==starts[i] and ledger[2*i+2]==trials[i] for i in range(58)))
 ck('prefix_order_all58', [ident(x) for x in starts]==[ident(x) for x in trials]==[ident(x) for x in prefix])
 ck('original_report58of200',report['completed_trials']==58 and report['expected_trials']==200 and report['status']=='incomplete')
 ck('58_original_outcomes_unchosen',all(x['status']=='completed' and x['termination'] in ('environment_success','task_horizon') for x in trials))
 ck('report_counts_sums',sum(x['policy_calls'] for x in trials)==940 and sum(x['control_steps'] for x in trials)==7302 and sum(len(x['executed_actions']) for x in trials)==7302)
 # Independently parse every real blob, not merely trust recorder hashes.
 captures=[x for x in events if 'event_index' in x];ends=[x for x in events if x.get('event')=='trial_end'];ck('event_counts',len(events)==3571 and len(captures)==3513 and len(ends)==58)
 ck('capture_indices', [x['event_index'] for x in captures]==list(range(1,3514)));ck('capture_monotonic',all(a['elapsed_ns_before_capture']<=b['elapsed_ns_before_capture'] for a,b in zip(captures,captures[1:])))
 for e in captures:
  ck('capture_production_identity',e['version']=='goal-before-policy-all-query-recorder-candidate-v1' and e['scientific_trials_added']==0 and e['timing_boundary']=='observer outside original policy perf_counter interval')
  ck('three_runtime_passivity_guards',e['invariants']=={'global_rng_unchanged':True,'object_identity_and_bytes_unchanged':True,'passive_sim_and_environment_rng_unchanged':True})
  rng=json.loads(validate_blob(e['global_rng']));ck('RNG_has_real_generators',set(rng)>={'python','numpy','torch_cpu','torch_cuda'})
  if isinstance(rng['torch_cuda'],list):ck('CUDA_generator_readout',len(rng['torch_cuda'])==1 and rng['torch_cuda'][0]['dtype']=='uint8')
  if e['observation_arrays']:
   ck('five_arrays',set(e['observation_arrays'])==set(OBS));aggregate=hashlib.sha256()
   for key in OBS:
    m=e['observation_arrays'][key];raw=validate_blob(m['blob']);v=validate_array(m,raw);aggregate.update(key.encode());aggregate.update(m['dtype'].encode());aggregate.update(str(tuple(m['shape'])).encode());aggregate.update(raw)
    expectedshape=(256,256,3) if key.endswith('image') else {'robot0_eef_pos':(3,),'robot0_eef_quat':(4,),'robot0_gripper_qpos':(2,)}[key];ck('required_input_dimensions',v.shape==expectedshape)
   ck('aggregate_observation_sha',aggregate.hexdigest()==e['observation_sha256'])
  else:ck('missing_observation_explicit','observation_missing' in e)
  if e['sim_array_blobs']:
   ck('real_native_mujoco',e['sim']['native_type']=='mujoco._structs.MjData')
   for key,b in e['sim_array_blobs'].items():validate_array(e['sim']['fields'][key.removeprefix('sim.')],validate_blob(b))
  else:ck('missing_sim_explicit','missing' in e['sim'])
 ck('no_unreferenced_or_missing_blobs',blobrefs==set(blobmanifest))
 capbyindex={x['event_index']:x for x in captures};group=defaultdict(list)
 for e in captures:
  if e['ordinal'] is not None:group[e['ordinal']].append(e)
 gate_group=defaultdict(list)
 for e in gate:
  ck('gate_zero_science',e['scientific_trials_added']==0)
  if 'ordinal' in e:gate_group[e['ordinal']].append(e)
 ck('full_gate_schema_counts',Counter(x['event'] for x in gate)=={'paired_input_gate_open':1,'t0_pair_gate':58,'query_integrity_passed':940,'policy_step_executed':7302,'paired_input_gate_finished':1})
 baselines={};trialdetails=[];allnorm=[];allenv=[]
 M=Path(next(x['checkpoint'] for x in outer if x['event']=='deployment_base_load_start'));stats=read(M/'dataset_statistics.json')['libero_goal_no_noops']['action'];modelraw=(M/'modeling_prismatic.py').read_bytes();watch(M/'modeling_prismatic.py');low=np.array(stats['q01']);high=np.array(stats['q99']);mask=np.asarray(stats.get('mask',np.ones_like(low,dtype=bool)))
 ck('official_q99_source_formula',b'0.5 * (normalized_actions + 1) * (action_high - action_low + 1e-8) + action_low' in modelraw)
 for ordinal,(start,t) in enumerate(zip(starts,trials),1):
  ck('trial_fixed_settings',all(t[k]==start[k]==v for k,v in {'action_chunk':8,'configured_wait_steps':10,'environment_seed':0,'runtime_seed':17,'split':'development','suite':'libero_goal'}.items()) and t['wait_steps']==10 and 0<t['control_steps']<=300)
  caps=group[ordinal];nq=t['policy_calls'];ck('query_count_ceiling',nq==(t['control_steps']+7)//8==len(t['chunks']))
  phases=['trial_begin_before_reseed','reseed_after','factory_before','factory_after','reset_before','reset_after','set_init_before','set_init_after']+['wait_before','wait_after']*10+['t0_query_before','t0_query_after']+['query_before','query_after']*(nq-1)
  ck('complete_phase_order', [e['phase'] for e in caps]==phases);ck('phase_identity',all(e['trial_identity']==ident(t) for e in caps))
  waits=[e for e in caps if e['phase'].startswith('wait_')];ck('dummy_wait_sequence',[e['wait_steps'] for e in waits]==[n for i in range(10) for n in (i,i+1)])
  gg=gate_group[ordinal];ck('all_gate_identity',all(e['trial_identity']==ident(t) for e in gg));pairs=[e for e in gg if e['event']=='t0_pair_gate'];queries=[e for e in gg if e['event']=='query_integrity_passed'];steps=[e for e in gg if e['event']=='policy_step_executed'];ck('exact_pertrial_gate_counts',len(pairs)==1 and len(queries)==nq and len(steps)==t['control_steps'])
  ck('step_order', [e['control_step'] for e in steps]==list(range(t['control_steps'])))
  instruction_hash=sha(t['task_name'].replace('_',' ').encode());t0=caps[28];ck('first_query_t0',t0['phase']=='t0_query_before' and t0['control_step']==0)
  content=capture_content(t0,instruction_hash);ck('pair_content_rebuilt',pairs[0]['content']==content and pairs[0]['capture_event_index']==t0['event_index'])
  key=t['state_trial_id']
  if t['method']=='A256_seed17':ck('new_A_baseline',key not in baselines and pairs[0]['pairing']=='baseline_recorded_before_first_policy');baselines[key]=content
  else:ck('before_policy_exact_pair',content==baselines[key] and pairs[0]['pairing']=='exact_before_policy_pair_passed')
  chunks=[];qseq=[]
  for j,(q,chunk) in enumerate(zip(queries,t['chunks'])):
   pre,post=caps[28+2*j:30+2*j];ck('query_capture_binding',q['capture_event_index']==post['event_index'] and q['control_step']==chunk['control_step']==pre['control_step']==post['control_step']==8*j)
   ck('query_input_bytes_dtype_shape',pre['observation_arrays']==post['observation_arrays'] and pre['observation_sha256']==post['observation_sha256']==chunk['observation_sha256'])
   ck('query_sim_passive',pre['sim']==post['sim']);ck('query_content_signature',q['content']==capture_content(pre,instruction_hash)==capture_content(post,instruction_hash))
   arrays={}
   for name in ('normalized_actions','environment_actions'):
    m=q['returned_actions'][name];v=validate_array(m,bytes.fromhex(m['bytes_hex']));ck('chunk_shape',v.shape==(8,7));ck('original_chunk_identical',np.array_equal(np.asarray(chunk[name],dtype=v.dtype),v));arrays[name]=v
   normal=arrays['normalized_actions'];env=arrays['environment_actions'];physical=np.where(mask,0.5*(normal+1)*(high-low+1e-8)+low,normal);physical[:,-1]=-np.sign(2.0*physical[:,-1]-1.0);ck('exact_official_action_conversion',physical.dtype==env.dtype and physical.tobytes()==env.tobytes())
   meta=chunk['metadata'];ck('one_pass_checkpoint_metadata',meta['selector_checkpoint_sha256']==actualconfig['manifest']['methods'][0 if t['method'].startswith('A') else 1]['identity']['checkpoint_sha256'] and meta['visual_tokens']==256 and meta['per_camera_budgets']==[128,128] and meta['training_seed']==17 and meta['suite']=='libero_goal' and meta['method']==t['method'][0] and meta['future_head_calls']==0 and all(meta[k]==1 for k in ('policy_calls','vision_calls','scorer_calls','packing_calls')) and meta['language_cache']=='disabled')
   ind=meta['retained_indices'];ck('hard_topk_packing_counts',len(ind)==len(set(ind))==256 and ind==sorted(ind) and sum(0<=v<256 for v in ind)==128 and sum(256<=v<512 for v in ind)==128)
   ck('fixed_runtime_versions',meta['action_version']=='libero-oft-boundsq99-gripper-sign-invert-chunk8-v1' and meta['inputs_version']=='libero-oft-eval-rotate180-jpeg-lanczos3-crop09-boundsq99-v1' and meta['packing_version']=='oft-original-positions-v1')
   chunks.extend(env);allnorm.append(normal);allenv.append(env);qseq.append({'ordinal':ordinal,'query':j,'step':8*j,'pre_event':pre['event_index'],'post_event':post['event_index'],'observation_sha256':pre['observation_sha256'],'normalized_sha256':q['returned_actions']['normalized_actions']['sha256'],'environment_sha256':q['returned_actions']['environment_actions']['sha256']})
  executed=np.asarray(t['executed_actions'],dtype=np.float64);ck('chunks_to_original_execution',np.array_equal(executed,np.asarray(chunks)[:t['control_steps']]))
  for k,e in enumerate(steps):v=validate_array(e['action'],bytes.fromhex(e['action']['bytes_hex']));ck('every_executed_action_raw',v.shape==(7,) and v.tobytes()==executed[k].tobytes())
  # Gate interleaving is exact: query acknowledgement precedes its steps.
  expectedgate=['t0_pair_gate']
  for j in range(nq):expectedgate+=['query_integrity_passed']+['policy_step_executed']*min(8,t['control_steps']-j*8)
  ck('query_before_actual_steps', [e['event'] for e in gg]==expectedgate)
  end=ends[ordinal-1];ck('terminal_observer_matches_ledger',end['ordinal']==ordinal and end['trial_identity']==ident(t) and end['control_steps']==t['control_steps'] and end['policy_calls']==nq and end['wait_steps']==10 and end['status']==t['status'] and end['t0_hashes']=={'t0_query_before':t0['observation_sha256'],'t0_query_after':t0['observation_sha256']} and end['success_not_used_for_admission'])
  trialdetails.append({'ordinal':ordinal,'identity':ident(t),'policy_calls':nq,'executed_steps':t['control_steps'],'status':t['status'],'termination':t['termination'],'success_preserved_but_not_used_for_admission':t['success'],'t0_observation_sha256':t0['observation_sha256'],'queries':qseq})
 ck('29_unique_complete_pairs',len(baselines)==29)
 # Independent comparisons retain every old outcome. No source conclusion is borrowed.
 diagnostics={}
 oldpaths={'historical200':Path(inv['run_root'])/'trials.jsonl','engineering3053440':P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01/original_run/trials.jsonl'}
 for label,path in oldpaths.items():
  oldrows=[x for x in lines(path) if x.get('event')=='result'];byid={x['trial_id']:x for x in oldrows};ck('old_prefix_ids_present',all(t['trial_id'] in byid for t in trials));differences=[]
  for ordinal,t in enumerate(trials,1):
   prior=byid[t['trial_id']];same_actions=t['executed_actions']==prior['executed_actions'];same_chunks=[{k:c[k] for k in ('control_step','observation_sha256','normalized_actions','environment_actions','metadata')} for c in t['chunks']]==[{k:c[k] for k in ('control_step','observation_sha256','normalized_actions','environment_actions','metadata')} for c in prior['chunks']]
   changed={k:prior.get(k)!=t.get(k) for k in ('status','success','termination','control_steps','policy_calls')};t0same=t['chunks'][0]['observation_sha256']==prior['chunks'][0]['observation_sha256']
   if not same_actions or not same_chunks or any(changed.values()):
    priorchunks=prior['chunks'];first=None
    for j in range(min(len(t['chunks']),len(priorchunks))):
     l,r=priorchunks[j],t['chunks'][j]
     diff=[k for k in ('observation_sha256','normalized_actions','environment_actions','metadata') if l[k]!=r[k]]
     if diff:first={'query_index':j,'control_step':j*8,'fields':diff};break
    if first is None and len(priorchunks)!=len(t['chunks']):first={'query_index':min(len(priorchunks),len(t['chunks'])),'reason':'different_query_count'}
    differences.append({'ordinal':ordinal,'identity':ident(t),'t0_same':t0same,'executed_actions_same':same_actions,'chunks_same':same_chunks,'terminal_field_differences':changed,'first_chunk_divergence':first})
  diagnostics[label]={'path':str(path),'sha256':h(path),'total_original_results':len(oldrows),'compared_fixed_prefix':58,'differences':differences,'exact_replay':not differences,'old_history_never_overwritten':True}
 # Negative checks exercise the independent raw validators, not scientific code.
 sample=next(x for x in captures if x['observation_arrays'])['observation_arrays'][OBS[0]];raw=validate_blob(sample['blob']);bad=dict(sample,sha256='0'*64);expect_reject('tampered_blob_array',lambda:validate_array(bad,raw));badref=dict(sample['blob'],path='../unexpected.bin');expect_reject('path_escape',lambda:validate_blob(badref))
 badref=dict(sample['blob'],bytes=sample['blob']['bytes']+1);expect_reject('byte_length',lambda:validate_blob(badref))
 # Snapshot files are immutable for this audit; record source-after checks.
 for rel,st in stat_before.items():ck('raw_artifact_not_modified', (O/rel).stat()==st)
 for rel,pin in inventory['files'].items():ck('frozen_source_after',h(S/rel)==pin and h(R/rel)==pin)
 for rel,pin in manifest['files'].items():ck('package_after',h(P/rel)==pin and h(R/rel)==pin)
 ck('live_snapshot_after',h(R/LIVE)==LSHA)
 allnorm=np.concatenate(allnorm);allenv=np.concatenate(allenv);exc=np.abs(allenv)>1
 sections['raw_reconstruction']={'raw_file_count':len(artifactfiles),'raw_total_bytes':sum(x['bytes'] for x in artifactfiles.values()),'blob_count':len(blobmanifest),'blob_bytes':sum(x['bytes'] for x in blobmanifest.values()),'captures':len(captures),'trial_end_records':len(ends),'all_queries':940,'executed_steps':7302,'exact_paired_t0':29,'all_blobs_referenced':True,'all_input_bytes_recomputed':True,'all_actions_roundtrip_exact':True,'native_MjData_readouts_verified':True,'CPU_fixture_enabled':False,'normalized_extrema':[float(allnorm.min()),float(allnorm.max())],'environment_extrema':[float(allenv.min()),float(allenv.max())],'returned_environment_elements_abs_gt1':int(exc.sum()),'original_model_preprocessing_packing_action_versions_retained':True}
 sections['runtime']={'original_verify_runtime_events_recomputed':runtime_proof,'AST_projection_recomputed':True,'source173_verified':True,'all_future_heads_absent_in_deployment':True,'two_selected_checkpoint_bytes_verified':True,'scientific_results_added':0}
 sections['limitations']=['No evidence identifies or repairs the historical Goal200 mismatch. Fresh58 diagnostic is not assumed to be exact historical replay.','All old200 and all new Goal science remain HOLD. No global release, timing admission, checkpoint reselection, or GPU retry is authorized.','Raw observation bytes and action roundtrips are independently reconstructed; pointer-identity invariance is guaranteed by reviewed runtime checks and their durable PASS events, not independently recoverable pointer values.','Observer changes wall-clock I/O overhead; this job is engineering cost only and never full O2A timing.','Wall timestamps across scheduler and compute node are not assumed synchronized; cost uses frozen Slurm allocation elapsed840 seconds.']
 af=write('raw_artifact_allowlist.json',{'source_root':str(O),'classification':'nonweight_development_engineering_raw','all_files_retained':True,'file_count':len(artifactfiles),'files':artifactfiles,'blob_count':len(blobmanifest),'blob_bytes':sum(x['bytes'] for x in blobmanifest.values()),'scientific_trials_added':0,'final_values':False})
 tf=write('per_trial_independent_reconstruction.json',{'trials':trialdetails,'engineering_only':True});df=write('historical_comparison.json',diagnostics);sf=write('source_and_provenance_inventory.json',{'files':seen,'file_count':len(seen),'source173_verified':True})
 review={'schema':'formal_main_v2','kind':'independent_Goal_paired_input58_terminal_review','status':'passed_engineering_terminal_only','reviewed_by':'independent','review_agent':'/root/spatial588_recovery_audit_2054','job_id':'3054127','blockers':[],'root_Slurm_snapshot_sha256':LSHA,'package_manifest_sha256':MSHA,'authorization_sha256':ASHA,'source173_verified':True,'real_environment_engineering_verified':True,'old_cause_identified':False,'old_failure_repaired':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False,'scientific_trials_added':0,'automatic_retry':False,'allocated_GPU_seconds':840,'independent_check_count':sum(counts.values()),'checks_by_category':dict(counts),'sections':sections,'raw_allowlist':af,'per_trial_reconstruction':tf,'historical_comparison':df,'source_inventory':sf,'wall_seconds':time.perf_counter()-started,'utc':datetime.now(timezone.utc).isoformat()}
 rr=write('terminal_review.json',review)
 readiness={'schema':'formal_main_v2','kind':'independent_Goal_engineering_evidence_readiness','status':'passed_engineering_evidence_only','job_id':'3054127','blockers':[],'terminal_review':rr,'raw_allowlist':af,'engineering_gate_verified':True,'ready_for_root_engineering_admission_only':True,'scientific_release':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'old_cause_identified':False,'old_failure_repaired':False,'automatic_retry':False,'further_engineering_requires_separate_exact_design_and_root_review':True}
 write('readiness.json',readiness)
 print(json.dumps({'review':rr,'checks':sum(counts.values()),'raw':sections['raw_reconstruction'],'historical_changed_ordinals':{k:[x['ordinal'] for x in v['differences']] for k,v in diagnostics.items()}},ensure_ascii=False))
try:main()
except BaseException as exc:
 write('failure_'+str(time.time_ns())+'.json',{'status':'failed_independent_audit','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'checks_by_category':dict(counts),'scientific_release':False});raise
