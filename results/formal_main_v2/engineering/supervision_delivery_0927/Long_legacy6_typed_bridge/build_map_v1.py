"""Minimal author typed-map candidate. No admission or production consumer API.
Current run rechecks all600 raw action records and references prior exact CPU
runtime replay; it does not call the simulator or claim a new execution.
"""
import ast,copy,hashlib,json,math,os,re,struct,sys,time,traceback,types,zipfile
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';H=R.parent
D=R/'.local/legacy6_typed_bridge_0927'
RUN='results/formal_main_v2/libero_10/downstream/development/8c843c1d4ee8383c/attempt01'
PRIOR='results/formal_main_v2/engineering/supervision_delivery_0727/Long_legacy6_CPU_candidate'
HIST='results/formal_main_v2/engineering/supervision_delivery_0830/Long_legacy6_provenance_independent/independent_readiness.json'
TARGET='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed23/execution_contract.json'
ROOT='results/formal_main_v2/downstream_reviews/3019954.json';MAN='results/formal_main_v2/execution/libero_10_development_first_pair_v1.json'
REG='configs/experiments/formal_main_v2_action_execution_compat_v1.json';INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
OLD='formal-downstream-root-v1';NEW='formal-downstream-action-v1'
SEM='4ef98a5beb21bfa790a8a0f484334d6d9020a481a517d8f89534562524025d7d'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
JOBS=['3016981','3017161','3017959','3018505','3019176','3019954']
PINS={REG:'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe',INV:'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',ROOT:'cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba',MAN:'d8c22787050b3223390627d74a804505c62f470b064bab112c2c230c4369051a',HIST:'b786128f4f202c93da6a80f44c7c1fbeeacadef78724b76d9bef294615b7a3d5',TARGET:'ecab6b824d17f52e26b788e47a021d767c79b8606a6ab342388962e1de0d9db6',PRIOR+'/report.json':'22a47a847ed81d7a18360354dd6a53b8e1153c716df78a87264bcbca25c49f18',PRIOR+'/per_trial.jsonl':'2ea56052bf56432858cfb0930707e158054da84c6a68d822b369b4b0cb4e1fbc',PRIOR+'/per_chunk.jsonl':'ccd1d56775752ac9c8d0d1381b2caf932c7327bfd4670bcca1cdc90b14a6dbc0','scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034','scripts/ops/formal_action_consumption_guard_v1/reviewer.py':'843f0336fd4161eb23d512b34935c7fca7d75032aceefe86084a16a7939a642c','scripts/ops/formal_action_consumption_guard_v1/consumer.py':'b3f754557646c8e5fa6172fd8a1bcded7e246bbfb4c490502bdc1e3f73e21b31','scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571','scripts/profile_formal.py':'4b8a7ac0b8be904f8f6b66d9fe7f6c3f7425056e013db903ac6b480191e2ebf6'}
BEGAN=time.perf_counter();CPU=time.process_time();SEEN={};CHECKS=[]
def need(v,msg):
 if not v:raise ValueError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def encode(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def sig(v):return digest(encode(v))
def pairs(xs):
 d={}
 for k,v in xs:need(k not in d,'duplicate JSON key');d[k]=v
 return d
def decode(b):
 def invalid(x):raise ValueError('nonfinite JSON '+x)
 return json.loads(b,object_pairs_hook=pairs,parse_constant=invalid)
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('no process/network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  need(not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) and not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'} and not (p.name=='panel.json' and 'final' in p.parts) and p.name!='init_states_test.json','forbidden values')
  need(not str(p).endswith('/results/experiment_supervisor/state.json'),'mutable state not evidence')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w:need(p.parent==D,'write outside private directory')
def watch(rel,expected=None):
 p=Path(rel);p=p if p.is_absolute() else R/p;need(p.resolve()==p and '..' not in p.parts,'canonical path');h=sha(p)
 key=p.relative_to(R).as_posix() if R in p.parents else str(p)
 need(expected is None or h==expected,'SHA '+key);need(key not in SEEN or SEEN[key]['sha256']==h,'evidence changed')
 SEEN[key]={'sha256':h,'bytes':p.stat().st_size};return {'path':key,'sha256':h}
def read(rel,expected=None):
 watch(rel,expected);p=Path(rel);return (p if p.is_absolute() else R/p).read_bytes()
def metadata(rel,expected=None):return decode(read(rel,expected))
def write(name,v,jsonl=False):
 b=b''.join(encode(x)+b'\n' for x in v) if jsonl else json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2).encode()+b'\n'
 with (D/name).open('xb') as f:f.write(b)
 return {'path':(D/name).relative_to(R).as_posix(),'bytes':len(b),'sha256':digest(b)}
def f64(a):
 out=[];need(type(a) is list,'matrix list')
 for row in a:
  need(type(row) is list and len(row)==7,'seven columns')
  for x in row:need(type(x) in (int,float) and math.isfinite(x),'finite numeric action');out.append(float(x))
 return struct.pack('<'+'d'*len(out),*out)
def line_ref(n,o,b):return {'line':n,'byte_offset':o,'bytes':len(b),'sha256':digest(b)}

# This is the complete draft schema validator, not a production-adoption function.
TOP={'schema','kind','version','status','suite','split','registration','legacy','target','method_identities','environment','trial_records','coverage','controller_identity','RNG_scope','cost','adoption','evidence'}
TRIAL={'schema','kind','version','status','suite','split','trial_id','state_trial_id','initial_state_sha256','task_id','task_name','source_state_index','method_id','method_identity_sha256','source','target_action_semantics_sha256','outcome','action_evidence','controller_identity_status','old_invocation_ran_new_wrapper','new_GPU_trial','reuse_authorized'}
def validate_candidate(m,rs):
 need(type(m) is dict and set(m)==TOP,'map fields')
 need(m['schema']=='formal_main_v2' and m['kind']=='legacy_development_equivalence_map_candidate' and m['version']=='long-legacy6-typed-equivalence-v1' and m['status']=='candidate_not_admitted','draft type')
 need(m['suite']=='libero_10' and m['split']=='development','Long development only')
 need(m['registration']=={'path':REG,'sha256':PINS[REG]},'original registration')
 need(m['legacy']['execution_version']==OLD and m['legacy']['old_invocation_ran_new_wrapper'] is False,'no retrospective wrapper or execution version')
 need(m['legacy']['root_review']=={'path':ROOT,'sha256':PINS[ROOT]},'old review binding')
 need(m['target']['execution_version']==NEW and m['target']['action_semantics_sha256']==SEM and m['target']['contract']=={'path':TARGET,'sha256':PINS[TARGET]},'target semantics')
 need(m['adoption']=={'root':None,'independent':None,'production_reuse_authorized':False,'production_consumer_changed':False,'final_release':False,'GPU_submission_authorized':False,'old_latency_reused':False},'no draft approval')
 need(m['controller_identity']['status']=='historical_source_chain_available_adoption_pending' and m['controller_identity']['old_instance_hash_recorded'] is False,'no historical instance claim')
 need(m['RNG_scope']['old_dump_recorded'] is False and m['RNG_scope']['old_dump_required_by_registration'] is False,'no retrospective/new RNG dump requirement')
 need(set(m['method_identities'])==set(METHODS) and len(rs)==600,'all6 methods and600 required')
 need(m['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':520},'unchanged env')
 trials=set();states={};counts=Counter();methods=Counter()
 for r in rs:
  need(type(r) is dict and set(r)==TRIAL,'trial fields')
  need(r['schema']=='formal_main_v2' and r['kind']=='legacy_trial_equivalence_candidate' and r['version']==m['version'] and r['status']=='conditional_evidence_not_admitted','trial draft')
  need(r['suite']=='libero_10' and r['split']=='development' and r['method_id'] in METHODS,'trial scope')
  need(r['trial_id'] not in trials,'duplicate trial');trials.add(r['trial_id']);methods[r['method_id']]+=1
  need(r['method_identity_sha256']==sig(m['method_identities'][r['method_id']]),'method changed')
  need(r['source']['execution_version']==OLD and r['source']['job_id'] in JOBS and r['source']['root_review']==m['legacy']['root_review'] and r['source']['raw_ledger']==m['legacy']['raw_ledger'],'actual source identity')
  need(r['target_action_semantics_sha256']==SEM and r['old_invocation_ran_new_wrapper'] is False and r['new_GPU_trial'] is False and r['reuse_authorized'] is False,'execution overclaim')
  need(r['controller_identity_status']=='pending_root_independent_source_chain_adoption','controller condition')
  a=r['action_evidence'];need(a['full_chunks_finite_and_old_threshold'] and a['recorded_queue_prefix_exact'] and a['prior_CPU_replay_exact'],'action requirements')
  need(a['recorded_executed_f64le_sha256']==a['old_CPU_replay_executed_sha256']==a['new_CPU_replay_executed_sha256'],'changed actions')
  need(a['clip_changed_all7']==a['clip_changed_arm6']==0,'clip inactive')
  need(type(r['outcome']['success']) is bool and r['outcome']['status']=='completed','preserve outcome')
  k=r['state_trial_id'];x=states.setdefault(k,{'hash':r['initial_state_sha256'],'methods':set()})
  need(x['hash']==r['initial_state_sha256'] and r['method_id'] not in x['methods'],'state mismatch');x['methods'].add(r['method_id'])
  counts.update(chunks=a['full_chunks'],actions=a['executed_actions'])
 need(methods==Counter({x:100 for x in METHODS}) and len(states)==100 and all(x['methods']==set(METHODS) for x in states.values()),'complete Cartesian coverage')
 need(counts==Counter(chunks=23179,actions=183676),'complete action counts')
 need(m['coverage']=={'trials':600,'unique_initial_states':100,'tasks':10,'methods':6,'full_chunks':23179,'executed_actions':183676,'new_scientific_trials':0,'outcome_filtering':False},'coverage claims')
 need(m['cost']['historical_GPU_seconds']==10531 and m['cost']['new_GPU_seconds']==0 and m['cost']['original_jobs_counted_once']==JOBS,'cost')
 return {'status':'typed_draft_structure_passed','production_reuse_authorized':False,'trials':600}

def main():
 need(Path(__file__).parent==D,'unique private source');sys.dont_write_bytecode=True;sys.addaudithook(guard)
 for rel,h in PINS.items():watch(rel,h)
 inv=metadata(INV);need(len(inv['files'])==173,'173 source count')
 for rel,h in inv['files'].items():
  for base in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:watch(base/rel,h)
 CHECKS.append('173 R/S/mirror exact files')
 recheck=metadata(D/'legacy_root_recheck.json');need(recheck['status']=='passed_original_whole_chain' and recheck['completed_trials']==600 and recheck['actual_execution_version']==OLD,'original consumer recheck')
 for rel,h in recheck['evidence_sha256'].items():watch(rel,h)
 root=metadata(ROOT);man=metadata(MAN);prior=metadata(PRIOR+'/report.json');hist=metadata(HIST);target=metadata(TARGET)
 need(root['status']=='passed' and root['scientific_complete'] and root['completed_trials']==600 and root['raw_invocation_job_ids']==JOBS,'old whole600')
 need(root.get('execution_version',OLD)==OLD,'actual old version')
 need([x['identity']['method_id'] for x in man['methods']]==METHODS,'exact6 order');identities={x['identity']['method_id']:x['identity'] for x in man['methods']}
 for rel,h in root['files'].items():watch(rel,h)
 for rel,h in {**target['files'],**target['GPU_acceptance'],**target['runtime_contract']['dependencies']}.items():watch(rel,h)
 scope=target['runtime_contract'];need(sig({'execution_version':NEW,'files':target['files'],'runtime_contract_without_stage':{k:v for k,v in scope.items() if k!='stage'},'GPU_acceptance':target['GPU_acceptance'],'source_inventory':target['source_inventory']})==SEM,'exact reviewer semantic function')
 need(scope['checkpoint']==str(H/'models/openvla-7b-oft-finetuned-libero-10-95220f9'),'same official Long base')
 need(len({x['frozen_model_sha256'] for x in identities.values()})==1 and all(x['model_revision']=='95220f9a3421a7ff12d4218e73d09ade830fa9a3' and x['future_head_deployed'] is False for x in identities.values()),'method/base identities')
 CHECKS.append('unchanged old consumer/root plus exact new semantic target')
 # Recheck the recovered historical source chain; inherit its historical Git
 # anchoring as independent evidence, without running Git or claiming old capture.
 need(hist['status']=='historical_installation_and_factory_evidence_recovered_runtime_identity_adoption_unresolved','historical qualification')
 for rel,desc in hist['evidence'].items():
  if not rel.startswith('.local/'):watch(rel,desc['sha256'])
 hi=hist['historical_installation_evidence'];fc=hist['factory_chain']
 need(hi['installation_attempt4_exit_zero_and_import_success'] and len(fc['old_attempts'])==6,'history/factory coverage')
 with zipfile.ZipFile(P/'external/wheels-libero/robosuite-1.4.1-py3-none-any.whl') as z:
  for name,e in hi['wheel_members_compared'].items():need(digest(z.read(name))==e['wheel_member_sha256']==e['current_file_sha256'],'installed distribution member')
 CHECKS.append('historical install/factory evidence and five wheel source members; no old instance claim')
 invocations={}
 for j in root['registered_jobs_at_review']:
  if j['job_id'] in JOBS:
   v=metadata(j['invocation'],j['invocation_sha256']);need(v['version']==OLD and v['suite']=='libero_10' and v['stage']=='development','actual old invocation')
   oldjob=next(x for x in fc['old_attempts'] if x['job_id']==j['job_id']);need(j['job_id'] not in invocations,'one invocation perjob')
   invocations[j['job_id']]={'invocation':{'path':j['invocation'],'sha256':j['invocation_sha256']},'journal':{'path':oldjob['journal'],'sha256':oldjob['journal_sha256']}}
 need(list(invocations)==JOBS,'six invocations')
 previous={x['trial_id']:x for x in [decode(b) for b in read(PRIOR+'/per_trial.jsonl').splitlines()]};pc=iter(decode(b) for b in read(PRIOR+'/per_chunk.jsonl').splitlines())
 ledger_ref=watch(RUN+'/trials.jsonl');offset=0;active=None;job=None;records=[];stats={x:Counter() for x in METHODS};chunks=0

 for n,b in enumerate((R/RUN/'trials.jsonl').open('rb'),1):
  need(b.endswith(b'\n'),'complete line');lr=line_ref(n,offset,b);offset+=len(b);r=decode(b);need(r['run_signature']==root['run_signature'],'run signature')
  if r['event']=='invocation':need(active is None,'unfinished trial');job=r['slurm_job_id'];need(job in JOBS,'known job');continue
  if r['event']=='start':need(active is None,'overlap');active=(r,lr);continue
  need(r['event']=='result' and active is not None,'start/result pair');start,sr=active;active=None;old=previous[r['trial_id']]
  need(old['start_line']==sr and old['result_line']==lr and old['job_id']==job,'prior raw position binding')
  fields=['action_chunk','configured_wait_steps','environment_seed','initial_state_sha256','method','run_signature','runtime_seed','source_state_index','split','state_trial_id','suite','task_id','task_name','trial_id']
  need(all(r[k]==start[k] for k in fields),'start identity')
  need(r['method']==METHODS[len(records)%6] and r['status']=='completed' and r['suite']=='libero_10' and r['split']=='development' and r['environment_seed']==0 and r['runtime_seed']==17 and r['wait_steps']==10 and r['action_chunk']==8,'original scope')
  identity=identities[r['method']];queue=[];clip7=clip6=0;maxenv=0.;mds=[]
  for i,c in enumerate(r['chunks']):
   need(c['control_step']==i*8 and len(c['environment_actions'])==len(c['normalized_actions'])==8,'full8 chunk')
   eb=f64(c['environment_actions']);nb=f64(c['normalized_actions']);a=np.asarray(c['environment_actions'],dtype=np.float64)
   need(bool((np.abs(a)<=1.00001).all()),'old threshold violated')
   clip7+=int(np.count_nonzero(a.view(np.uint64)!=np.clip(a,-1.,1.).view(np.uint64)))
   arm=a[:,:6].copy();clip6+=int(np.count_nonzero(arm.view(np.uint64)!=np.clip(arm,-1.,1.).view(np.uint64)))
   md=c['metadata'];need(md['method']==identity['method'] and md['visual_tokens']==identity['visual_tokens'] and md['future_head_calls']==0,'policy identity')
   if identity['method'] in ('A','B'):need(md['selector_checkpoint_sha256']==identity['checkpoint_sha256'],'checkpoint metadata')
   expected={'trial_id':r['trial_id'],'chunk_index':i,'control_step':i*8,'environment_f64le_sha256':digest(eb),'normalized_f64le_sha256':digest(nb),'environment_shape_finite_old_range':True,'metadata_sha256':sig(md),'observation_sha256':c['observation_sha256']}
   need(next(pc)==expected,'prior perchunk differs');chunks+=1;queue.extend(c['environment_actions']);maxenv=max(maxenv,float(np.max(np.abs(a))));mds.append(sig(md))
  actual=f64(r['executed_actions']);need(len(r['executed_actions'])==r['control_steps'] and actual==f64(queue[:r['control_steps']]),'exact recorded prefix')
  need(len(r['chunks'])==r['policy_calls']==math.ceil(r['control_steps']/8),'chunk count')
  need(clip6==clip7==0,'clip active on recorded actions')
  need(digest(actual)==old['executed_f64le_sha256'] and digest(f64(queue))==old['all_emitted_f64le_sha256'] and sig(mds)==old['chunk_metadata_sequence_sha256'],'old CPU proof binds actual bytes')
  need(old['old_runtime_replay']==old['new_runtime_replay'] and old['old_runtime_replay']['python_numpy_RNG_unchanged'] is True and old['old_runtime_replay']['executed_f64le_sha256']==digest(actual),'inherited old/new CPU replay proof')
  record={'schema':'formal_main_v2','kind':'legacy_trial_equivalence_candidate','version':'long-legacy6-typed-equivalence-v1','status':'conditional_evidence_not_admitted','suite':'libero_10','split':'development','trial_id':r['trial_id'],'state_trial_id':r['state_trial_id'],'initial_state_sha256':r['initial_state_sha256'],'task_id':r['task_id'],'task_name':r['task_name'],'source_state_index':r['source_state_index'],'method_id':r['method'],'method_identity_sha256':sig(identity),'source':{'execution_version':OLD,'job_id':job,'root_review':watch(ROOT),'raw_ledger':ledger_ref,'start_line':sr,'result_line':lr,'run_signature':root['run_signature'],**invocations[job]},'target_action_semantics_sha256':SEM,'outcome':{k:r[k] for k in ['status','success','termination','control_steps']},'action_evidence':{'full_chunks_finite_and_old_threshold':True,'full_chunks':len(r['chunks']),'executed_actions':r['control_steps'],'maximum_absolute_environment_action':maxenv,'old_threshold':1.00001,'recorded_queue_prefix_exact':True,'recorded_executed_f64le_sha256':digest(actual),'all_emitted_f64le_sha256':digest(f64(queue)),'clip_changed_all7':clip7,'clip_changed_arm6':clip6,'prior_CPU_replay_exact':True,'prior_CPU_replay_record':watch(PRIOR+'/per_trial.jsonl'),'old_CPU_replay_executed_sha256':old['old_runtime_replay']['executed_f64le_sha256'],'new_CPU_replay_executed_sha256':old['new_runtime_replay']['executed_f64le_sha256'],'new_actions_basis':'prior deterministic fake-env CPU replay of recorded chunks, not actual new model/simulator execution'},'controller_identity_status':'pending_root_independent_source_chain_adoption','old_invocation_ran_new_wrapper':False,'new_GPU_trial':False,'reuse_authorized':False}
  records.append(record);stats[r['method']].update(trials=1,successes=int(r['success']),full_chunks=len(r['chunks']),executed_actions=r['control_steps'])
 need(active is None and len(records)==600 and chunks==23179,'complete600')
 try:next(pc)
 except StopIteration:pass
 else:raise ValueError('extra prior chunks')
 CHECKS.extend(['All600 genuine terminal records and23179 full8x7 chunks rechecked including unused suffix','Executed actions equal recorded full-chunk queue prefix by float64 little-endian bytes','Original controller np.clip arm6 and diagnostic all7 each change zero component bytes','Prior exact old/new runtime CPU replay bound to rechecked raw action bytes; not a new simulator replay'])
 allocs=root['cost']['allocations'];need([x['job_id'] for x in allocs]==JOBS and sum(x['elapsed_seconds']*x['gpus'] for x in allocs)==10531,'all six allocation costs')
 # This output is candidate evidence only; original version, jobs and outcomes stay intact.
 trialref=write('per_trial_equivalence_candidates.jsonl',records,True)
 evidenceref=write('evidence.json',dict(sorted(SEEN.items())))
 mapping={'schema':'formal_main_v2','kind':'legacy_development_equivalence_map_candidate','version':'long-legacy6-typed-equivalence-v1','status':'candidate_not_admitted','suite':'libero_10','split':'development','registration':watch(REG),'legacy':{'execution_version':OLD,'root_review':watch(ROOT),'execution_manifest':watch(MAN),'raw_ledger':ledger_ref,'run_signature':root['run_signature'],'old_invocation_ran_new_wrapper':False},'target':{'execution_version':NEW,'contract':watch(TARGET),'action_semantics_sha256':SEM,'GPU_acceptance':target['GPU_acceptance'],'scope':'compatibility target only, not retrospective execution'},'method_identities':identities,'environment':man['environment'],'trial_records':trialref,'coverage':{'trials':600,'unique_initial_states':100,'tasks':10,'methods':6,'full_chunks':23179,'executed_actions':183676,'new_scientific_trials':0,'outcome_filtering':False},'controller_identity':{'status':'historical_source_chain_available_adoption_pending','old_instance_hash_recorded':False,'independent_provenance':watch(HIST),'original_required_condition':'controller and environment were identical','available_evidence':'historical installation/distribution and same frozen factory, corroborated by accepted realGPU v4 captures; not old controller instance capture','pending':'Explicit root and independent judgment whether this exact source chain establishes the original identity condition; no additional historical snapshot prerequisite invented.','clip_scope':'Original run_episode forwards actions unchanged. Existing simulator Controller.scale_action np.clip applies to arm6. All full emitted arm6 and diagnostic all7 clip comparisons are byte-equal; diagnostic clipping is never inserted into deployment.'},'RNG_scope':{'old_dump_recorded':False,'old_dump_required_by_registration':False,'adapter_new_draws':False,'AST_proof_inherited_from_exact_prior_candidate':prior['single_removed_branch_AST_proof'],'CPU_replay_scope':'Existing author600 recorded-chunk fake-env replay checks Python/NumPy invariance; current run rebinds its proof to all raw actions. No old simulator RNG regeneration or independent approval claimed.'},'cost':{'historical_GPU_seconds':10531,'original_jobs_counted_once':JOBS,'original_allocations':allocs,'new_GPU_seconds':0,'new_scientific_trials':0},'adoption':{'root':None,'independent':None,'production_reuse_authorized':False,'production_consumer_changed':False,'final_release':False,'GPU_submission_authorized':False,'old_latency_reused':False},'evidence':evidenceref}
 validation=validate_candidate(mapping,records);neg=[]
 for case in ['legacy_relabel','subset','changed_action','approval','fake_instance','invented_RNG_gate']:
  m=copy.deepcopy(mapping);rs=copy.deepcopy(records)
  if case=='legacy_relabel':m['legacy']['execution_version']=NEW
  elif case=='subset':rs.pop()
  elif case=='changed_action':rs[0]['action_evidence']['new_CPU_replay_executed_sha256']='0'*64
  elif case=='approval':m['adoption']['production_reuse_authorized']=True
  elif case=='fake_instance':m['controller_identity']['old_instance_hash_recorded']=True
  elif case=='invented_RNG_gate':m['RNG_scope']['old_dump_required_by_registration']=True
  try:validate_candidate(m,rs)
  except ValueError as e:neg.append({'case':case,'rejected':True,'reason':str(e)})
  else:raise ValueError('negative case passed '+case)
 CHECKS.append('six focused typed-map rejection tests passed')
 for rel,x in SEEN.items():need(sha(Path(rel) if Path(rel).is_absolute() else R/rel)==x['sha256'],'evidence changed')
 mapref=write('equivalence_map_candidate.json',mapping)
 plan={'schema':'formal_main_v2','kind':'minimal_legacy600_bridge_integration_proposal','status':'not_implemented_or_activated','candidate':mapref,'original_condition_pending':'Root and independent must explicitly accept or reject whether the pinned historical distribution/installation/factory chain establishes same controller/environment. No rule requires full historical RNG dumps; lack of an instance capture must not be rewritten into a captured hash.','proposed_interface':'consume_explicit_legacy_equivalence(evidence, old_root_ref, map_ref, root_adoption_ref, independent_adoption_ref, *, suite, stage, target_action_semantics_sha256)','returned_type':'separate compatibility envelope containing genuine old root unchanged, old execution_version, adopted target semantics and all600 receipts; never a fabricated new root_downstream_review','required_gates':['Unchanged original whole-chain consumer passes before the bridge.','Exact immutable per-trial map/root/evidence/target hashes, all600 coverage and original method/checkpoint/state identities.','Genuine root and independent bridge adoption receipts bind exact map SHA and explicit controller/environment identity assessment; missing or negative assessment rejects.','Original costs10531GPU seconds counted once; no added independent states, relabelled invocations, overwritten outcomes or old latency.','Full72selector/16reference/four-suite development and global root release remain unchanged.'],'integration_points':[{'path':'scripts/ops/formal_action_deployment_v1/consumer.py','sha256':PINS['scripts/ops/formal_action_deployment_v1/consumer.py'],'function':'require_matching_o2a','minimum_change':'Separate new version consumes legacy compatibility envelope explicitly, plus genuine current receipts. Compare target action semantics without changing old execution_version; full/components stay current,30observations/22methods/14300forwards and same checkpoint identities.'},{'path':'scripts/ops/formal_action_consumption_guard_v1/reviewer.py','sha256':PINS['scripts/ops/formal_action_consumption_guard_v1/reviewer.py'],'function':'_require_current_ancestry / _no_exception_claims','minimum_change':'Existing current-only guard remains intact. New explicit dispatcher handles a whole approved legacy root through the map API; no positive equivalence field injected into original roots or concealed mixed prefix.'},{'path':'scripts/ops/formal_action_consumption_guard_v1/consumer.py','sha256':PINS['scripts/ops/formal_action_consumption_guard_v1/consumer.py'],'function':'audit_freeze / guarded_consumer','minimum_change':'New assembly unions600legacy and1600current by trial/method/state identity and rejects overlap/conflicts. Preserve100unique states and22methods, all4suite/global freeze.'},{'path':'scripts/ops/formal_downstream_supervisor.py','sha256':PINS['scripts/ops/formal_downstream_supervisor.py'],'minimum_change':'No old600 resubmission or dedup bypass. Proof API is only for future freeze/O2A consumption.'},{'path':'scripts/profile_formal.py','sha256':PINS['scripts/profile_formal.py'],'minimum_change':'Existing collected30 panel and original50warmup/20repeat/full+components protocol remain; this map grants no latency or final-state reuse.'}],'no_production_code_changed':True,'no_new_GPU_or_scientific_trial':True,'next':'Root independent review of candidate and original identity condition, then separately version exact minimal consumer extension. If identity condition remains unresolved, retain stop without automatic600 rerun.'}
 planref=write('minimum_integration_plan.json',plan)
 report={'schema':'formal_main_v2','kind':'author_legacy600_typed_bridge_review','status':'author_CPU_candidate_checks_passed_not_admitted','review_role':'author','created_utc':datetime.now(timezone.utc).isoformat(),'map':mapref,'plan':planref,'original_consumer_recheck':watch(D/'legacy_root_recheck.json'),'candidate_validation':validation,'checks':CHECKS,'negative_checks':neg,'coverage':mapping['coverage'],'per_method':{k:dict(v) for k,v in stats.items()},'pending_original_condition':mapping['controller_identity'],'new_GPU_seconds':0,'historical_GPU_seconds':10531,'new_scientific_trials':0,'production_consumer_state_Git_changed':False,'weights_or_final_values_read':False,'reuse_authorized':False,'CPU_wall_seconds':time.perf_counter()-BEGAN,'CPU_process_seconds':time.process_time()-CPU,'prior_replay_was_recomputed_in_this_run':False,'prior_replay_exact_source_and_raw_bindings_rechecked':True,'implementation':watch(Path(__file__)),'bounded_transport_failure_retained':'transport_preparation_failure.json'}
 reportref=write('report.json',report)
 print(json.dumps({'status':report['status'],'report':reportref,'map':mapref,'plan':planref,'CPU_wall_seconds':report['CPU_wall_seconds'],'CPU_process_seconds':report['CPU_process_seconds']}))

if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('build_map_failure_v1.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'CPU_wall_seconds':time.perf_counter()-BEGAN,'CPU_process_seconds':time.process_time()-CPU,'new_GPU_seconds':0,'reuse_authorized':False})
  raise
