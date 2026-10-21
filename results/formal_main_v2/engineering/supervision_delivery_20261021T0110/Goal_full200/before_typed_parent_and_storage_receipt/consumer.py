"""Typed prospective Goal full200 terminal reconstruction, read-only.
Original runtime_inputs, adapters (one explicit typed-parent read location),
trajectory action-v1 validator and full rollout/summarize are applied intact.
This is a new execution version, never a fabricated old whole-chain review.
"""
from pathlib import Path,PurePosixPath
import ast,copy,hashlib,importlib.util,json,re,sys,types
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
PKG='scripts/ops/formal_goal_full200_gate_v1';STAGE='goal_full200_20261021T0110'
OUT='results/formal_main_v2/engineering/'+STAGE+'/attempt01'
RUN=OUT+'/original_run'
RAW=R/'results/formal_main_v2/raw_runtime'/STAGE/'attempt01'
VERSION='goal-full200-prospective-single-attempt-v1'
PINS={'scripts/review_formal_downstream.py':'753edb55ce21fd43f85499e136a7e52093ecf9feaeafadf0f01cece8fa267202','scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571','scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89','scripts/analyze_formal.py':'7f9573877f8a3662bd06dae9362823fd478283ed14cc86a6c3763f6fb4f682f1','scripts/ops/formal_evaluation_adapter.py':'b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'}
SPEC_SHA='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'
def require(ok,msg):
 if not ok:raise ValueError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(value):
 return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:require(k not in d,'duplicate JSON key');d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def load(path,name,pin):
 b=Path(path).read_bytes();require(digest(b)==pin,'implementation SHA changed')
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def jsonl(path):
 b=Path(path).read_bytes();require(b.endswith(b'\n'),'incomplete JSONL tail')
 rows=[strict(x) for x in b.splitlines()];require(all(type(x) is dict for x in rows),'JSONL objects only');return rows
def validate_job(job,dispatch):
 require(type(job) is dict and job.get('status')=='COMPLETED' and job.get('exit_code')=='0:0' and job.get('gpus')==1,'clean single-GPU terminal required')
 require(type(job.get('elapsed_seconds')) is int and job['elapsed_seconds']>=0,'allocation seconds required once')
 require(job.get('job_id')==dispatch.get('job_id') and re.fullmatch('[1-9][0-9]*',str(job['job_id'])),'exact original ACK required')
 require(job.get('stage_key')==STAGE and job.get('run_root')==str(P/RUN) and job.get('suite')=='libero_goal' and job.get('mode')=='development','exact full200 job scope')
def read_blob(ref,*,observation,output_root,read_refs):
 require(type(ref) is dict and type(ref.get('bytes')) is int and ref['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',str(ref.get('sha256'))),'typed blob reference')
 if observation:
  require(ref.get('storage')=='root_approved_raw_observations','raw observation storage kind')
  path=Path(ref['path']);require(path.parent==RAW and path.name==ref['sha256']+'.bin','only fixed new raw observation root')
 else:
  require(ref.get('storage')=='attempt_local','local blob storage kind')
  p=PurePosixPath(ref['path']);require(len(p.parts)==2 and p.parts[0]=='blobs' and p.name.startswith(ref['sha256']+'.'),'local observer blob reference')
  path=output_root/'observer'/p
 require(path.resolve()==path and not any(p.is_symlink() for p in [path,*path.parents]),'blob canonical path')
 raw=path.read_bytes();require(len(raw)==ref['bytes'] and digest(raw)==ref['sha256'],'raw blob bytes/size changed');read_refs[str(path)]={'sha256':digest(raw),'bytes':len(raw)}
 return raw
def reconstruct_gate(project,rows,*,specification,job_id):
 """Recompute every raw capture, query/chunk/action and all100 paired t0s."""
 import numpy as np
 root=Path(project)/OUT;read_refs={};events=jsonl(root/'observer/events.jsonl');gate=jsonl(root/'observer/gate.jsonl')
 captures=[r for r in events if 'phase' in r]
 require(len(captures)<=21032 and not any(r.get('event')=='observer_abort' for r in events),'observer abort/bound')
 expected={r['trial_id']:r for r in specification['rows']};completed=[r for r in rows if r.get('event')=='result']
 require(len(completed)==200 and all(r['status']=='completed' for r in completed),'whole200 completed records required; policy_error never admitted')
 require([{k:r[k] for k in ('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')} for r in completed]==[{k:r[k] for k in ('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')} for r in specification['rows']],'full200 original identity/order exact')
 require(sum(r['control_steps'] for r in completed)<=60000 and sum(r['policy_calls'] for r in completed)<=7600 and sum(r['wait_steps'] for r in completed)==2000,'control/query/warmup counts distinct')
 capidx={}
 for i,e in enumerate(captures,1):
  require(e['event_index']==i and len(canonical(e))<=16384,'capture sequence/size')
  require(e.get('invariants')=={'object_identity_and_bytes_unchanged':True,'passive_sim_and_environment_rng_unchanged':True,'global_rng_unchanged':True},'passive capture invariant missing')
  aggregate=hashlib.sha256();arrays=e['observation_arrays']
  if arrays:
   require(set(arrays)=={'agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'},'all five raw arrays')
   for key in ('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'):
    a=arrays[key];b=read_blob(a['blob'],observation=True,output_root=root,read_refs=read_refs)
    require(a['bytes']==len(b) and a['sha256']==digest(b) and len(b)==int(np.prod(a['shape']))*np.dtype(a['dtype']).itemsize,'array dtype/shape/byte metadata')
    aggregate.update(key.encode());aggregate.update(a['dtype'].encode());aggregate.update(str(tuple(a['shape'])).encode());aggregate.update(b)
   require(aggregate.hexdigest()==e['observation_sha256'],'five-component aggregate reconstruction')
  require(sum(v['bytes'] for v in e.get('sim_array_blobs',{}).values())<=8192,'sim byte bound')
  for v in e.get('sim_array_blobs',{}).values():read_blob(v,observation=False,output_root=root,read_refs=read_refs)
  rb=read_blob(e['global_rng'],observation=False,output_root=root,read_refs=read_refs);require(len(rb)<=65536,'RNG bound')
  capidx[i]=e
 require(gate[0]['event']=='paired_input_gate_open' and gate[-1]['event']=='paired_input_gate_finished' and not any(x['event']=='paired_input_gate_abort' for x in gate),'complete single gate attempt')
 require(gate[0]['CPU_fixture_enabled'] is False and gate[0]['runtime_context']=='real_environment_engineering','CPU fixture forbidden')
 require(len(gate)<=68032 and all(len(canonical(x))<=16384 for x in gate),'gate storage bound')
 queries=[e for e in gate if e['event']=='query_integrity_passed'];steps=[e for e in gate if e['event']=='policy_step_executed'];pairs=[e for e in gate if e['event']=='t0_pair_gate']
 require(len(pairs)==200 and len(queries)==sum(r['policy_calls'] for r in completed)<=7600 and len(steps)==sum(r['control_steps'] for r in completed)<=60000,'event totals equal original raw ledger')
 bytrial={r['trial_id']:r for r in completed};baselines={};matched=set()
 for e in pairs:
  t=e['trial_identity'];require(t['trial_id'] in expected,'unknown t0 identity')
  cap=capidx[e['capture_event_index']];require(cap['phase']=='t0_query_before' and cap['trial_identity']==t,'pair is before first query')
  sig={'components':{k:{a:cap['observation_arrays'][k][a] for a in ('dtype','shape','bytes','sha256')} for k in cap['observation_arrays']},'instruction_utf8_sha256':e['content']['instruction_utf8_sha256']}
  require(sig==e['content'],'pair content rebuilt from raw bytes')
  state=t['state_trial_id']
  if t['method']=='A256_seed17':require(state not in baselines and e['pairing']=='baseline_recorded_before_first_policy','unique A baseline');baselines[state]=sig
  else:require(t['method']=='B256_seed17' and state in baselines and state not in matched and e['pairing']=='exact_before_policy_pair_passed' and sig==baselines[state],'exact preB five-array and instruction pair');matched.add(state)
 require(len(baselines)==len(matched)==100,'all100 pairs')
 qseen={tid:0 for tid in bytrial};sseen={tid:0 for tid in bytrial}
 for e in queries:
  tid=e['trial_identity']['trial_id'];row=bytrial[tid];qi=qseen[tid];require(e['control_step']==8*qi and qi<len(row['chunks']),'query original cadence')
  after=capidx[e['capture_event_index']];before=capidx[e['capture_event_index']-1]
  require(after['phase'] in ('query_after','t0_query_after') and before['phase'] in ('query_before','t0_query_before') and after['trial_identity']==before['trial_identity']==e['trial_identity'] and after['control_step']==before['control_step']==e['control_step'],'query exact adjacent before/after')
  for key in before['observation_arrays']:require(before['observation_arrays'][key]==after['observation_arrays'][key],'query input byte/identity metadata unchanged')
  c=row['chunks'][qi];require(c['observation_sha256']==after['observation_sha256'],'ledger postpolicy hash')
  for name in ('normalized_actions','environment_actions'):
   meta=e['returned_actions'][name];raw=bytes.fromhex(meta['bytes_hex']);require(digest(raw)==meta['sha256'] and len(raw)==meta['bytes'],'returned actions raw')
   arr=np.frombuffer(raw,dtype=np.dtype(meta['dtype'])).reshape(meta['shape']);require(arr.shape==(8,7) and np.isfinite(arr).all() and np.array_equal(arr,np.asarray(c[name])),'unchanged returned chunk values')
  qseen[tid]+=1
 for e in steps:
  tid=e['trial_identity']['trial_id'];i=sseen[tid];require(e['control_step']==i,'step order')
  a=e['action'];b=bytes.fromhex(a['bytes_hex']);require(digest(b)==a['sha256'] and len(b)==a['bytes'],'step raw bytes');arr=np.frombuffer(b,dtype=np.dtype(a['dtype'])).reshape(a['shape'])
  require(arr.shape==(7,) and np.isfinite(arr).all() and np.array_equal(arr,np.asarray(bytrial[tid]['executed_actions'][i])),'original action unchanged')
  sseen[tid]+=1
 require(all(qseen[k]==v['policy_calls'] and sseen[k]==v['control_steps'] for k,v in bytrial.items()),'pertrial exact queries/actions')
 end=gate[-1];require(end['exact_paired_t0_checks']==100 and end['all_query_checks']==len(queries) and end['executed_policy_steps_recorded']==len(steps) and end['original_prefix_trials']==200,'finish totals exact')
 return {'trials':200,'paired_t0_checks':100,'queries':len(queries),'control_steps':len(steps),'warmup_steps':2000,'raw_blob_refs':read_refs,'old200_HOLD':True,'final_release':False}
def review_terminal(project,terminal_ref):
 """Typed root terminal manifest contains exact pulled artifacts + unique ACK."""
 project=Path(project).resolve();require(project==R,'terminal only in control R after exact pull')
 own=project/PKG/'consumer.py';require(Path(__file__).resolve()==own,'exact canonical typed consumer required')
 reviewer_path=project/'scripts/ops/formal_action_deployment_v1/reviewer.py'
 # Original reviewer pin is bound by the genuine old execution contract below.
 original=project/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json'
 require(digest(original.read_bytes())=='c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803','original science lineage')
 inv=strict(original.read_bytes());contract=strict((project/inv['action_execution_contract']['path']).read_bytes())
 require(digest((project/inv['action_execution_contract']['path']).read_bytes())==inv['action_execution_contract']['sha256'],'original runtime contract identity')
 rv=load(reviewer_path,'goal200_original_reviewer',contract['files']['scripts/ops/formal_action_deployment_v1/reviewer.py']);ev=rv.Evidence(project)
 terminal=ev.read_ref(terminal_ref)
 require(terminal.get('kind')=='goal_full200_typed_terminal_manifest' and terminal.get('execution_version')==VERSION and terminal.get('status')=='complete_nonweight_pull' and terminal.get('weights_copied') is False and terminal.get('sealed_values_read') is False,'new typed terminal envelope only')
 package=ev.read(PKG+'/package_manifest.json');require(ev.watch(PKG+'/package_manifest.json')==terminal['package_manifest_sha256'],'terminal package identity')
 for name,h in package['files'].items():require(ev.watch(name)==h,'new package changed')
 entry=rv.load(ev,PKG+'/entry.py',package['files'][PKG+'/entry.py'])
 config=ev.read(PKG+'/config.json');entry.validate_config(config)
 auth=ev.read_ref(terminal['authorization']);entry.validate_authorization(auth,ev.watch(PKG+'/config.json'),terminal['package_manifest_sha256'],ev.watch(PKG+'/entry.py'))
 dispatch=ev.read_ref(terminal['dispatch']);reservation=ev.read_ref(terminal['reservation'])
 job=terminal['job'];validate_job(job,dispatch)
 entry.validate_dispatch(dispatch,reservation,auth,terminal['authorization']['sha256'],job['job_id'],terminal['reservation']['sha256'])
 for role in ('root','independent'):
  ref=auth[role+'_review'];rel=Path(ref['path']).relative_to(P).as_posix();value=ev.read_ref({'path':rel,'sha256':ref['sha256']});entry.check_review(value,role,terminal['package_manifest_sha256'],ev.watch(PKG+'/config.json'))
 inventory=terminal['artifacts'];require(type(inventory) is list and len({x['path'] for x in inventory})==len(inventory),'complete unique pull artifacts')
 files={}
 for row in inventory:
  require(row['path'].startswith(OUT+'/'),'foreign terminal artifact')
  require(ev.watch(row['path'])==row['sha256'] and ev.path(row['path']).stat().st_size==row['bytes'],'pulled bytes changed');files[row['path']]=row['sha256']
 for name in ['outer/completion.json','outer/events.jsonl','outer/typed_parent.json','observer/events.jsonl','observer/gate.jsonl','original_run/config.json','original_run/panel.json','original_run/trials.jsonl','original_run/closed_loop_report.json']:require(OUT+'/'+name in files,'missing actual full200 raw artifact:'+name)
 complete=ev.read(OUT+'/outer/completion.json');outer=rv.lines(ev,OUT+'/outer/events.jsonl');parent=ev.read(OUT+'/outer/typed_parent.json')
 require(complete.get('status')=='returned_200_prospective_pending_terminal_review' and complete.get('exit_code')==0 and complete.get('errors')==[] and complete.get('original_runtime_restored') is True and complete.get('observer_failed') is False,'failed or partial cannot be terminal passed')
 require(complete['job_id']==job['job_id'] and complete['authorization_sha256']==terminal['authorization']['sha256'] and complete['package_manifest_sha256']==terminal['package_manifest_sha256'] and complete['raw_observation_root']==str(RAW),'outer exact job/source/raw binding')
 require(complete['raw_event_sha256']==files[OUT+'/outer/events.jsonl'] and parent['kind']=='goal_full200_typed_parent_receipt' and parent['execution_version']==VERSION and parent['source_completion_sha256']==files[OUT+'/outer/completion.json'],'typed parent exact new outer binding')
 require(all(e['seq']==i and e['job_id']==job['job_id'] for i,e in enumerate(outer)) and outer[0]['event']=='engineering_start' and outer[-1]['event']=='engineering_prefix_returned','one complete outer lifecycle')
 starts=[e for e in outer if e['event']=='prefix_observer_scope_enter'];ends=[e for e in outer if e['event']=='prefix_observer_scope_exit'];require(len(starts)==len(ends)==1 and ends[0]['bindings_intact'] and ends[0]['bindings_restored'],'exact observer AST lifecycle')
 astmod=rv.load(ev,PKG+'/ast_gate_v2.py',package['files'][PKG+'/ast_gate_v2.py'])
 raw=ev.path('src/cti_vla/evaluation/libero_runtime.py').read_bytes();traw=ev.path('src/cti_vla/evaluation/formal_trials.py').read_bytes();_,_,rp=astmod.derive_run(raw);_,_,tp=astmod.base.derive_trials(traw)
 require(starts[0]['proof']['run_episode']==rp and starts[0]['proof']['trial_loop']==tp,'actual AST proof exact source derivation')
 for n,h in PINS.items():require(ev.watch(n)==h,'original scientific consumer source')
 for n,h in inv['support_files'].items():require(ev.watch(n)==h,'original support changed')
 for n,h in inv['watched_files'].items():require(ev.watch(Path(n).relative_to(P).as_posix())==h,'original immutable input changed')
 for n,h in inv['root_evidence_sha256'].items():require(ev.watch(n)==h,'root original input evidence changed')
 old=rv.load(ev,'scripts/review_formal_downstream.py',PINS['scripts/review_formal_downstream.py']);scheduler=rv.load(ev,'scripts/ops/formal_downstream_supervisor.py',PINS['scripts/ops/formal_downstream_supervisor.py'])
 runtime=rv.load(ev,'scripts/ops/formal_action_deployment_v1/runtime_scope.py',contract['files']['scripts/ops/formal_action_deployment_v1/runtime_scope.py'])
 runtime.validate_contract(contract['runtime_contract'],project_root=project,source_root=Path(inv['source_root']))
 assets,_=rv.checked_asset_identities(ev,runtime,contract,inv);runtimeproof=runtime.verify_runtime_events(outer,contract['runtime_contract'],expected_asset_identities=assets)
 require(runtimeproof['all_source_and_binding_contexts_restored'] and runtimeproof['original_base_loads']==1 and runtimeproof['synthetic_input'] is False,'complete actual source/runtime chain')
 # Construct an explicit new-output science view. Never serialize it as an old invocation.
 opt=old.options(inv);registration=ev.read('configs/experiments/formal_main_v2.json');manifest=ev.read(Path(inv['execution_manifest']).relative_to(P).as_posix());panel=ev.read(Path(inv['run_root']).relative_to(P).as_posix()+'/panel.json')
 source_inventory=ev.read(Path(inv['source_inventory']).relative_to(P).as_posix())
 sys.path.insert(0,str(project/'src'))
 from cti_vla.training.formal_future import formal_source_hashes
 scientific_config=ev.read(RUN+'/config.json')
 projection={**inv,'resume':False,'run_root':str(P/RUN),'wrapper_sha256':ev.watch(PKG+'/entry.py')}
 value={'invocation':projection,'opt':opt,'registration':registration,'suite':'libero_goal','manifest':manifest,'inventory':source_inventory,'sources':formal_source_hashes(project),'development':panel,'methods':['A256_seed17','B256_seed17'],'output':RUN}
 value['checkpoint']=old.runtime_inputs(ev,scheduler,value,scientific_config)
 # Only literal parent-read location changes. All original adapter checks stay.
 rawold=ev.path('scripts/review_formal_downstream.py').read_text();tree=ast.parse(rawold);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='adapters');derived=copy.deepcopy(node)
 target=next(n for n in derived.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='wrapper')
 original_expr=copy.deepcopy(target.value);target.value=ast.parse("evidence.read("+repr(OUT+'/outer/typed_parent.json')+")",mode='eval').body;ast.fix_missing_locations(derived)
 ns=dict(old.__dict__);exec(compile(ast.Module(body=[derived],type_ignores=[]),str(old.__file__)+'::<explicit-Goal-typed-parent>','exec'),ns)
 adapter=ns['adapters'](ev,scheduler,value,job,scientific_config,files)
 require(adapter['frozen_trial_loop_code_sha256']==starts[0]['proof']['observer_trial_code_sha256'],'original adapter records exact derived trial code')
 require(adapter['status']=='returned' and adapter['before_ledger_raw']=={'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()},'new fresh ledger; no fake old completion prefix')
 analyzer=rv.load(ev,'scripts/analyze_formal.py',PINS['scripts/analyze_formal.py']);trajectory,trajectory_proof=rv.trajectory_validator(old,analyzer,runtime)
 result=rv.clone(old.rollout,trajectory=trajectory)(ev,scheduler,value,job,scientific_config,adapter)
 require(result['scientific_complete'] and result['completed_trials']==200 and result['expected_trials']==200 and result['raw_invocation_job_ids']==[job['job_id']] and result['unfinished_attempts_unknown_cost']==0,'complete exactly one fresh200 original consumer')
 spec=ev.read(PKG+'/specification.json');require(ev.watch(PKG+'/specification.json')==SPEC_SHA,'fixed200 specification')
 rawproof=reconstruct_gate(project,rv.lines(ev,RUN+'/trials.jsonl'),specification=spec,job_id=job['job_id'])
 require(parent['wall_seconds']<=job['elapsed_seconds']+1 and complete['wall_seconds']<=job['elapsed_seconds']+1,'whole wall within actual allocation')
 ev.unchanged()
 return {'schema':'formal_main_v2','kind':'goal_full200_typed_terminal_review','status':'passed_pending_root_and_independent_acceptance','execution_version':VERSION,'terminal_ref':terminal_ref,'job_id':job['job_id'],'full_original_scientific_consumer_reconstruction':result,'explicit_adapter_parent_path_derivation':{'original_source_sha256':PINS['scripts/review_formal_downstream.py'],'original_AST_sha256':digest(ast.dump(node,include_attributes=False).encode()),'derived_AST_sha256':digest(ast.dump(derived,include_attributes=False).encode()),'only_parent_read_relocated_to_actual_typed_receipt':True},'raw_gate':rawproof,'runtime':runtimeproof,'trajectory_validator':trajectory_proof,'allocation_gpu_seconds':job['elapsed_seconds'],'allocation_count':1,'all_prior_allocations_retained_not_added_again':True,'original200_HOLD':True,'old_cause_identified':False,'scientific_trials_accepted_by_this_function':0,'final_release':False,'evidence_sha256':ev.files}
def consume(project,reference):
 p=Path(project)/reference['path'];require(p.resolve()==p and p.is_file() and digest(p.read_bytes())==reference['sha256'],'typed saved review pin')
 saved=strict(p.read_bytes());require(saved.get('kind')=='goal_full200_typed_terminal_review','no legacy/CPU review substitute')
 rebuilt=review_terminal(project,saved['terminal_ref']);require(saved==rebuilt,'typed terminal review does not rebuild exactly');return rebuilt
