"""CPU-only complete Long legacy600 action-compatibility candidate.
No runtime/simulator/model invocation, no state/Git/Slurm writes, no sealed values.
Historical trace replay uses a deterministic fake environment and recorded chunks:
it is not a new LIBERO run or proof of unrecorded historical controller attributes.
"""
from __future__ import annotations
import ast, copy, hashlib, importlib, json, math, random, re, struct, sys, time, types
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/long_legacy6_followup_0727'
RUN='results/formal_main_v2/libero_10/downstream/development/8c843c1d4ee8383c/attempt01'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
IDS=['action_chunk','configured_wait_steps','environment_seed','initial_state_sha256','method','run_signature','runtime_seed','source_state_index','split','state_trial_id','suite','task_id','task_name','trial_id']
PINS={
'configs/experiments/formal_main_v2_action_execution_compat_v1.json':'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe',
'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json':'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',
'results/formal_main_v2/downstream_reviews/3019954.json':'cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba',
'results/formal_main_v2/preflight/long_sixth_development_real_independent_20261018.json':'f920678a126c575abdc3ae21d24bf6d6e97e73f6b1a69c897681c07c2d41b126',
'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py':'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',
'results/formal_main_v2/preflight/heartbeat_20261019T1347/v4_GPU_root_acceptance.json':'3ee503429d703bb9d8da5970a9e183d371defbaf86884b24ae164d6cbc7bc1e9',
'results/formal_main_v2/engineering/action_v4_actual_independent_0547/terminal_review.json':'613489f84224eaafac36523244ac98e3b81d50624d9da7102b3d5cd1062edbbe',
'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/source/candidate_manifest.json':'25d6e0e831d7e7770150bd2008e49991ec10bddbd815a3400f7a60b539404d26',
'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl':'54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c',
'scripts/ops/formal_action_deployment_v1/runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
'scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034',
'scripts/ops/formal_action_consumption_guard_v1/consumer.py':'b3f754557646c8e5fa6172fd8a1bcded7e246bbfb4c490502bdc1e3f73e21b31',
'scripts/ops/formal_action_consumption_guard_v1/reviewer.py':'843f0336fd4161eb23d512b34935c7fca7d75032aceefe86084a16a7939a642c',
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/profile_formal.py':'4b8a7ac0b8be904f8f6b66d9fe7f6c3f7425056e013db903ac6b480191e2ebf6',
'src/cti_vla/evaluation/formal_profiling.py':'56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80',
}
seen={}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def reject_pairs(pairs):
 d={}
 for k,v in pairs:need(k not in d,'duplicate JSON key '+k);d[k]=v
 return d
def decode(b):
 def bad(x):raise ValueError('nonfinite JSON '+x)
 return json.loads(b,object_pairs_hook=reject_pairs,parse_constant=bad)
def encode(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def sig(x):return digest(encode(x))
def read(rel,expected=None):
 p=R/rel;need(not Path(rel).is_absolute() and '..' not in Path(rel).parts and p.resolve()==p,'path')
 need(not any('sealed' in q.lower() or q.lower()=='test' for q in p.parts),'forbidden sealed/test')
 b=p.read_bytes();h=digest(b);need(expected is None or h==expected,'SHA '+rel);seen[rel]=h;return b
def metadata(rel,expected=None):return decode(read(rel,expected))
def f64(matrix):
 need(isinstance(matrix,list),'matrix list');flat=[]
 for row in matrix:
  need(isinstance(row,list) and len(row)==7,'seven action columns')
  for x in row:need(type(x) in (int,float) and math.isfinite(x),'finite numeric action');flat.append(float(x))
 return struct.pack('<'+'d'*len(flat),*flat)
def rng():
 n=np.random.get_state()
 return sig({'python':random.getstate(),'numpy':[n[0],n[1].tolist(),n[2],n[3],n[4]]})
def refline(n,off,b):return dict(line=n,byte_offset=off,bytes=len(b),sha256=digest(b))
def load(path,name):
 m=types.ModuleType(name);m.__file__=str(path);m.__package__='';sys.modules[name]=m
 exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),m.__dict__);return m

def replay(row,fn,runtime):
 # The same old serialized PolicyChunks feed each runtime. No policy inference,
 # image reconstruction, simulator, hidden-state replay or RNG restore occurs.
 obs={'agentview_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eye_in_hand_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eef_pos':np.zeros(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
 class FakeEnv:
  def __init__(self):self.actions=[]
  def reset(self):return obs
  def set_init_state(self,x):return obs
  def step(self,action):
   self.actions.append(action)
   return obs,0.,bool(row['success'] and len(self.actions)==10+row['control_steps']),{}
 class RecordedPolicy:
  def __init__(self):self.i=0
  def reset(self):self.i=0
  def __call__(self,ob,text):
   c=row['chunks'][self.i];self.i+=1
   return runtime.PolicyChunk(np.asarray(c['normalized_actions'],dtype=np.float32),np.asarray(c['environment_actions'],dtype=np.float64),c['metadata'])
 env=FakeEnv();before=rng();out=fn(env,RecordedPolicy(),'recorded trace CPU check',np.zeros(1),wait_steps=10,max_steps=520,policy_watchdog_seconds=60.)
 need(rng()==before,'CPU replay consumed Python/NumPy RNG')
 for k in ['status','success','termination','control_steps','wait_steps','policy_calls']:need(out[k]==row[k],'replay differs: '+k)
 need(len(out['chunks'])==len(row['chunks']),'replay chunks')
 for a,b in zip(out['chunks'],row['chunks']):
  need(f64(a['normalized_actions'])==f64(b['normalized_actions']) and f64(a['environment_actions'])==f64(b['environment_actions']) and a['metadata']==b['metadata'],'replay emitted chunk changed')
 need(f64(out['executed_actions'])==f64(row['executed_actions']),'replay executed bytes changed')
 need(f64(env.actions[:10])==f64([list(runtime.DUMMY_ACTION)]*10),'wait action changed')
 need(f64(env.actions[10:])==f64(row['executed_actions']),'env boundary differs')
 return {'executed_f64le_sha256':digest(f64(env.actions[10:])), 'all_wait_and_control_actions_f64le_sha256':digest(f64(env.actions)), 'python_numpy_RNG_unchanged':True,'new_GPU_or_simulator_execution':False}

def main():
 began=time.perf_counter();need(Path(__file__).parent==D,'unique private directory')
 for rel,h in PINS.items():read(rel,h)
 inv=metadata('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')
 need(len(inv['files'])==173,'173 inventory')
 for rel,h in inv['files'].items():
  for base in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:
   p=base/rel;need(p.resolve()==p and sha(p)==h,'173 source byte mismatch '+str(p))
 root=metadata('results/formal_main_v2/downstream_reviews/3019954.json');ind=metadata('results/formal_main_v2/preflight/long_sixth_development_real_independent_20261018.json')
 need(root['status']==ind['status']=='passed' and root['completed_trials']==ind['completed_trials']==600,'prior exact600 root/ind')
 need(root['scientific_complete'] and root['stage']=='development' and root['final_state_values_read'] is False,'prior scope')
 for rel,h in root['files'].items():read(rel,h)
 config=metadata(RUN+'/config.json');report=metadata(RUN+'/closed_loop_report.json')
 manifest=metadata('results/formal_main_v2/execution/libero_10_development_first_pair_v1.json',root['execution_manifest_sha256'])
 need(config['manifest']==manifest and report['provenance']['manifest']==manifest,'manifest crossbinding');need(sig(config)==root['run_signature']==report['provenance']['run_signature'],'canonical config signature')
 need([r['identity']['method_id'] for r in manifest['methods']]==METHODS,'six methods')
 identities={r['identity']['method_id']:r['identity'] for r in manifest['methods']}
 jobs=root['raw_invocation_job_ids'];need(len(jobs)==6 and root['cost']['all_attempt_gpu_seconds']==10531,'six costs')
 historical=[]
 for job in jobs:
  journals=sorted((R/RUN/'adapter_invocations').glob(job+'_*.jsonl'));need(len(journals)==1,'one historical journal')
  events=[decode(b) for b in read(journals[0].relative_to(R).as_posix(),root['files'][journals[0].relative_to(R).as_posix()]).splitlines()]
  official=[e for e in events if e['event']=='official_source_verified'];need(len(official)==2,'two official sources')
  end=[e for e in events if e['event']=='adapter_end'];need(len(end)==1 and end[0]['status']=='returned' and end[0]['runner_status']==('completed' if job=='3019954' else 'incomplete'),'adapter returned correct partial/final state')
  historical.append({'job_id':job,'journal':journals[0].relative_to(R).as_posix(),'journal_sha256':sha(journals[0]),'official_source_events':official,'controller_instance_capture':False,'runtime_RNG_state_capture':False})
 # All read-only imports use the original frozen S bytes. derive_function returns
 # an unbound replacement; no production module binding or function is patched.
 sys.path.insert(0,str(S/'src'))
 runtime=importlib.import_module('cti_vla.evaluation.libero_runtime');need(Path(runtime.__file__)==S/'src/cti_vla/evaluation/libero_runtime.py','frozen runtime import')
 adapter=load(R/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','_long600_approved_adapter')
 before_rng=rng();original,replacement,proof=adapter.derive_function(runtime,(S/'src/cti_vla/evaluation/libero_runtime.py').read_bytes());need(before_rng==rng(),'derivation RNG')
 need(proof['removed_if_count']==1 and proof['other_AST_nodes_unchanged'],'single branch AST')
 # Current actual-engineering records are bounded4 Long cells, never600 rollouts.
 v4rel='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl'
 v4rows=[decode(b) for b in read(v4rel,PINS[v4rel]).splitlines()];v4={}
 for e in v4rows:
  if e.get('suite')=='libero_10' and e.get('method_id') in METHODS:
   v4.setdefault(e['method_id'],{}).setdefault(e['event'],[]).append(e)
 v4manifest=metadata('results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/source/candidate_manifest.json')
 controller_files=[]
 for c in v4manifest['actual_controller_evidence']['installed_source_reference_from_root_diagnosis'].values():
  need(sha(c['path'])==c['sha256'],'current pinned controller code');controller_files.append(c)
 # Complete ledger, not sampled. Every result retains explicit raw-line refs.
 ledger=R/RUN/'trials.jsonl';need(sha(ledger)==root['files'][RUN+'/trials.jsonl'],'ledger identity')
 active=None;job=None;offset=0;pertrial=[];perchunk=[];counts=Counter();methods=Counter();states={};comparison=[];findings=[]
 for number,b in enumerate(ledger.open('rb'),1):
  need(b.endswith(b'\n'),'unterminated ledger');lr=refline(number,offset,b);offset+=len(b);row=decode(b)
  need(row['run_signature']==root['run_signature'],'run signature')
  if row['event']=='invocation':need(active is None,'unfinished invocation');job=row['slurm_job_id'];need(job in jobs,'unknown job');continue
  if row['event']=='start':need(active is None,'overlap');active=(row,lr);continue
  need(row['event']=='result' and active is not None,'result without start');start,sr=active;active=None
  need(all(row[k]==start[k] for k in IDS),'start/result identity')
  need(row['suite']=='libero_10' and row['split']=='development' and row['method']==METHODS[len(pertrial)%6],'ordered development6')
  need(row['environment_seed']==0 and row['runtime_seed']==17 and row['wait_steps']==row['configured_wait_steps']==10 and row['action_chunk']==8,'environment flags')
  need(row['status']=='completed' and row['policy_calls']==len(row['chunks'])==math.ceil(row['control_steps']/8),'no missing chunks or hidden failed calls')
  key=row['state_trial_id'];st=states.setdefault(key,{'hash':row['initial_state_sha256'],'methods':[]});need(st['hash']==row['initial_state_sha256'],'state changed');st['methods'].append(row['method'])
  identity=identities[row['method']];queue=[];max_env=0.;max_normal=0.;metadata_hashes=[]
  for i,c in enumerate(row['chunks']):
   need(c['control_step']==8*i and len(c['environment_actions'])==len(c['normalized_actions'])==8,'complete chunk8')
   eb=f64(c['environment_actions']);nb=f64(c['normalized_actions']);a=np.asarray(c['environment_actions'],dtype=np.float64)
   need(bool((np.abs(a)<=1.00001).all()),'old amplitude guard taken')
   need(np.asarray(c['normalized_actions'],dtype=np.float32).astype(np.float64).tobytes()==np.asarray(c['normalized_actions'],dtype=np.float64).tobytes(),'normalized f32 serialization')
   md=c['metadata'];need(md['suite']=='libero_10' and md['method']==identity['method'] and md['visual_tokens']==identity['visual_tokens'],'chunk method identity')
   need(md['per_camera_budgets']==[identity['visual_tokens']//2]*2,'per-camera budget')
   need(all(md[x]==1 for x in ['policy_calls','vision_calls','packing_calls']) and md['future_head_calls']==0 and md['scorer_calls']==int(identity['method'] in ('A','B')) and md['language_cache']=='disabled','deployment calls/cache')
   if identity['method'] in ('A','B'):need(md['selector_checkpoint_sha256']==identity['checkpoint_sha256'] and md['training_seed']==17,'selector checkpoint')
   need(re.fullmatch('[0-9a-f]{64}',c['observation_sha256']) is not None,'observation identity')
   queue.extend(c['environment_actions']);metadata_hashes.append(sig(md));max_env=max(max_env,float(np.max(np.abs(a))));max_normal=max(max_normal,float(np.max(np.abs(c['normalized_actions']))))
   perchunk.append({'trial_id':row['trial_id'],'chunk_index':i,'control_step':i*8,'environment_f64le_sha256':digest(eb),'normalized_f64le_sha256':digest(nb),'environment_shape_finite_old_range':True,'metadata_sha256':sig(md),'observation_sha256':c['observation_sha256']})
  actual=f64(row['executed_actions']);need(len(row['executed_actions'])==row['control_steps'] and actual==f64(queue[:row['control_steps']]),'actual serialized queue prefix')
  a=replay(row,original,runtime);bnew=replay(row,replacement,runtime);need(a==bnew,'old/new CPU trace differs')
  item={k:row[k] for k in IDS};item.update(status=row['status'],success=row['success'],termination=row['termination'],job_id=job,start_line=sr,result_line=lr,policy_calls=row['policy_calls'],control_steps=row['control_steps'],full_chunks=len(row['chunks']),queue_actions=len(queue),all_chunks_recorded=True,environment_max_abs=max_env,normalized_max_abs=max_normal,all_chunks_old_threshold_pass=True,executed_f64le_sha256=digest(actual),all_emitted_f64le_sha256=digest(f64(queue)),chunk_metadata_sequence_sha256=sig(metadata_hashes),selector_checkpoint_sha256=identity.get('checkpoint_sha256'),old_runtime_replay=a,new_runtime_replay=bnew,new_actions_basis='derived from original recorded chunks with deterministic CPU fake environment; no actual new LIBERO trajectory',action_function_conditional_equivalence=True,historical_controller_instance_identity='not recorded in old ledger/config/journal',historical_Python_NumPy_torch_RNG_state_identity='not recorded; fixed seeds and reseed source only',new_GPU_trial=False,reuse_authorized=False)
  pertrial.append(item);counts.update(chunks=len(row['chunks']),actions=row['control_steps'],trials=1);methods[row['method']]+=1
  if row['method'] in v4:
   cell=v4[row['method']];starts=cell.get('cell_start',[])
   if len(starts)==1 and starts[0]['state_identity']['trial_id']==key:
    chunk=cell.get('policy_chunk',[]);need(len(chunk)==1,'one actual v4 chunk')
    comparison.append({'method':row['method'],'trial_id':row['trial_id'],'engineering_job_id':'3039197','state_identity_matches':starts[0]['state_identity']['initial_state_sha256']==row['initial_state_sha256'],'selected_identity_matches':starts[0]['identity']==identity,'actual_v4_first_chunk_matches_old':f64(chunk[0]['environment_actions'])==f64(row['chunks'][0]['environment_actions']),'old_full_trajectory_actions':row['control_steps'],'v4_actual_control_actions':8,'v4_old_rng_state_comparison':'unavailable_old_state_not_captured'})
 need(active is None and len(pertrial)==600 and len(states)==100 and counts['chunks']==23179 and counts['actions']==183676,'complete600 coverage')
 need(all(x['methods']==METHODS for x in states.values()) and all(methods[m]==100 for m in METHODS),'all methods all100states')
 need(len(comparison)==4,'only four accepted boundedLong engineering cells')
 need(runtime.run_episode is original,'production function binding untouched')
 envproof={'old_registered_environment':manifest['environment'],'old_runtime':config['runtime'],'old_source_verification':config['source_verification'],'historical_invocation_evidence':historical,'new_v4_actual_controller_cells':[{k:v for k,v in es['actual_controller_verified'][0]['controller'].items() if k not in ['constructor_source','methods']} for es in v4.values() if es.get('actual_controller_verified')],'current_controller_source_sha256':controller_files,'same_frozen_reseed_environment_factory_source':inv['files']['scripts/eval_formal_selector_libero.py'],'old_controller_instance_or_robosuite_code_SHA_in_config':False,'historical_controller_equivalence_proven':False,'full_historical_runtime_RNG_state_captured':False,'action_AST_introduces_rng_operation':False,'old_new_CPU_trace_RNG_unchanged':True,'actual_v4_first_chunk_comparisons':comparison,'limitation':'Pinned LIBERO source/reseed/factory and current controller SHA provide provenance. Old600 did not capture robosuite source/runtime controller attributes or pre-trial RNG hashes; current v4 captures cannot retrospectively create those records. Recorded action equivalence is conditional on same controller/environment.'}
 # A one-ULP and signed-zero mutation must fail exact prefix comparison; bounds
 # must check all8 emitted actions, including unexecuted suffix after success.
 negative=[]
 for name,values in [('one_ulp',[[math.nextafter(0.5,1.)]+[0.]*6]),('signed_zero',[[-0.]+[0.]*6])]:
  baseline=[[0.5]+[0.]*6] if name=='one_ulp' else [[0.]*7]
  need(f64(values)!=f64(baseline),'negative exact bytes failed');negative.append({'case':name,'rejected':True})
 for value in [True,float('nan'),float('inf')]:
  try:f64([[value]+[0.]*6])
  except ValueError:negative.append({'case':repr(value),'rejected':True})
  else:raise AssertionError('nonfinite/type negative')
 late=[[0.]*7 for _ in range(8)];late[-1][0]=1.00002
 need(bool((np.abs(np.asarray(late))>1.00001).any()),'late suffix negative');negative.append({'case':'unused_last_action_above_old_bound','rejected':True})
 for rel,h in seen.items():need(sha(R/rel)==h,'read source changed '+rel)
 for rel,h in inv['files'].items():need(sha(S/rel)==h and sha(R/rel)==h,'source changed')
 seen[Path(__file__).relative_to(R).as_posix()]=sha(__file__)
 result={'schema':'formal_main_v2','kind':'Long_legacy600_action_equivalence_CPU_candidate','version':'long-legacy6-action-equivalence-candidate-v1','created_utc':datetime.now(timezone.utc).isoformat(),'status':'action_trace_checks_passed_full_reuse_unresolved_controller_provenance','completed_trials_checked':600,'unique_development_initial_states':100,'all_methods_checked':dict(methods),'counts':dict(counts),'conditional_action_equivalence_trials':600,'unconditional_reuse_receipts':0,'new_scientific_trials':0,'new_GPU_seconds':0,'historical_GPU_seconds_retained':10531,'root_review_ref':{'path':'results/formal_main_v2/downstream_reviews/3019954.json','sha256':PINS['results/formal_main_v2/downstream_reviews/3019954.json']},'old_execution_manifest_sha256':root['execution_manifest_sha256'],'target_action_semantics_sha256':'4ef98a5beb21bfa790a8a0f484334d6d9020a481a517d8f89534562524025d7d','single_removed_branch_AST_proof':proof,'environment_rng_evidence':envproof,'findings':[{'severity':'unresolved','scope':'all600','condition':'same historical/current controller runtime identity','detail':'Old600 receipts bind full LIBERO archive and basic runtime versions, but lack robosuite controller source/instance capture. Newv4/current code identity is not retrospective evidence of those old attributes.'}],'focused_negative_checks':negative,'read_evidence_sha256':dict(sorted(seen.items())),'source173_R_S_and_mirror_rehashed':True,'frozen_source_changed':False,'weights_deserialized':False,'sealed_values_read':False,'supervisor_state_modified':False,'Git_modified':False,'scientific_reuse_authorized':False,'production_consumer_modified':False,'elapsed_CPU_audit_seconds':time.perf_counter()-began,'limitations':['This is an author CPU candidate, pending independent/root review; it does not activate legacy reuse.','All600 traces and all23179 full8x7 chunks are inspected, including unexecuted suffix actions. No result-based filtering.','Old/new runtime replay is deterministic CPU control-flow replay using recorded actions and fake observations/env; it is not simulator/RNG/model regeneration.','Four existing v4 engineering first-chunk comparisons are bounded evidence only; no new scientific success/latency or whole600 measured equivalence is claimed.']}
 outputs={'report.json':json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n','per_trial.jsonl':b''.join(encode(x)+b'\n' for x in pertrial),'per_chunk.jsonl':b''.join(encode(x)+b'\n' for x in perchunk),'environment_rng.json':json.dumps(envproof,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n'}
 for name,b in outputs.items():
  with (D/name).open('xb') as f:f.write(b)
 manifest_out={'schema':'formal_main_v2','kind':'candidate_delivery_manifest','files':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.iterdir()) if p.is_file()]}
 with (D/'delivery_files.json').open('xb') as f:f.write(json.dumps(manifest_out,sort_keys=True,indent=2).encode()+b'\n')
 print(json.dumps({'status':result['status'],'counts':dict(counts),'comparisons':comparison,'report_sha256':sha(D/'report.json'),'delivery_sha256':sha(D/'delivery_files.json'),'seconds':result['elapsed_CPU_audit_seconds']}),flush=True)
if __name__=='__main__':main()
