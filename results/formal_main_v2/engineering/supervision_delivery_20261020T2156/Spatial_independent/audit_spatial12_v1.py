"""Independent immutable Spatial12 audit; no production adoption or new rollout."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,math,os,random,struct,subprocess,sys,time,zipfile
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['CUDA_VISIBLE_DEVICES']=''
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent;AUTHOR=R/'.local/spatial588_integration_20261020T2156';SP=R.parent/'venv/lib/python3.11/site-packages';checks=[];evidence={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dig(b):return hashlib.sha256(b).hexdigest()
def enc(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def write(name,x):
 with (D/name).open('x',encoding='utf8') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def watch(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;h=sha(p)
 ck('pin:'+str(p),pin is None or h==pin);evidence[str(p)]={'sha256':h,'bytes':p.stat().st_size};return p

def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key')
  d[k]=v
 return d
def dec(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def read(p,pin=None):return dec(watch(p,pin).read_bytes())
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def matrix(values):
 a=np.asarray(values,dtype='<f8')
 if a.ndim!=2 or a.shape[1]!=7 or not np.isfinite(a).all():raise ValueError('finite Nx7 matrix required')
 return a

def inspect_trial(row,identity,state):
 if row['status']!='completed' or row['suite']!='libero_spatial' or row['split']!='development':raise ValueError('noncompleted/nonSpatial trial')
 if row['method']!=identity['method_id'] or any(row[k]!=state[k] for k in ('task_id','task_name','source_state_index','initial_state_sha256')):raise ValueError('state/method identity differs')
 if (row['environment_seed'],row['runtime_seed'],row['wait_steps'],row['configured_wait_steps'],row['action_chunk'])!=(0,17,10,10,8):raise ValueError('environment settings differ')
 acts=matrix(row['executed_actions']);chunks=row['chunks'];q=[];metadata=[]
 if len(acts)!=row['control_steps'] or row['control_steps']>220 or len(chunks)!=row['policy_calls'] or len(chunks)!=math.ceil(len(acts)/8):raise ValueError('control/chunk count differs')
 for index,c in enumerate(chunks):
  a,n=matrix(c['environment_actions']),matrix(c['normalized_actions']);md=c['metadata']
  if a.shape!=(8,7) or n.shape!=(8,7) or c['control_step']!=8*index or bool((np.abs(a)>1.00001).any()):raise ValueError('full chunks/former range differs')
  if a[:,:6].tobytes()!=np.clip(a[:,:6],-1.,1.).tobytes() or a.tobytes()!=np.clip(a,-1.,1.).tobytes():raise ValueError('controller clipping changes bytes')
  if md['suite']!='libero_spatial' or md['method']!=identity['method'] or md['visual_tokens']!=identity['visual_tokens'] or md['per_camera_budgets']!=[identity['visual_tokens']//2]*2:raise ValueError('metadata/budget differs')
  if (md['vision_calls'],md['packing_calls'],md['policy_calls'],md['future_head_calls'],md['scorer_calls'])!=(1,1,1,0,int(identity['method'] in ('A','B'))):raise ValueError('deployment calls differ')
  inds=md['retained_indices'];budget=identity['visual_tokens']//2
  if len(inds)!=2*budget or len(set(inds))!=len(inds) or inds!=sorted(inds) or sum(i<256 for i in inds)!=budget or any(i<0 or i>=512 for i in inds):raise ValueError('token indices invalid')
  if identity['method'] in ('A','B') and (md['selector_checkpoint_sha256']!=identity['checkpoint_sha256'] or md['training_seed']!=17):raise ValueError('selected checkpoint differs')
  q.append(a);metadata.append({'chunk':index,'environment_f64le_sha256':dig(a.tobytes()),'normalized_f64le_sha256':dig(n.tobytes()),'metadata_sha256':dig(enc(md)),'observation_sha256':c['observation_sha256']})
 full=np.concatenate(q)
 if full[:len(acts)].tobytes()!=acts.tobytes():raise ValueError('executed queue differs')
 return full,acts,metadata

def rejection(n,fn):
 try:fn()
 except (ValueError,AssertionError):ck(n,True)
 else:ck(n,False)

def main():
 manifest=read(AUTHOR/'phase1_manifest.json','20d8ee977e9735592660025acd4769c74935963f419d582f5c32fe74000ae5d3');ck('all15_author_files',manifest['file_count']==len(manifest['files'])==15)
 for x in manifest['files']:p=watch(x['path'],x['sha256']);ck('author_size:'+x['path'],p.stat().st_size==x['bytes'])
 # First reproduce the author's original guarded checks without modifying its files.
 command=[sys.executable,'-B',str(AUTHOR/'verify_saved.py')]
 proc=subprocess.run(command,cwd=R,env=dict(os.environ),capture_output=True,text=True,timeout=90)
 write('author_readonly_reconstruction.json',{'command':command,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'private_readonly_verifier_sha256':'11fb6fc4c61fb1765f3117f63492905931d24ec436e21041fbe70cd9ec7869aa','outputs_overwritten':False})
 ck('full_author_guarded_reconstruction',proc.returncode==0,proc.stderr[-1000:] if proc.returncode else None)
 proof=read(AUTHOR/'compatibility_proof.json','c2b46372be33cfe35c53643211b602102652d3662fb74a58553142a6e6a944f2');root=read(proof['original_prefix']['root_review']['path'],proof['original_prefix']['root_review']['sha256'])
 ck('original_root_partial_gate_not600',root['status']=='passed' and root['scientific_complete'] is False and root['completed_trials']==12 and root['expected_trials']==600 and root['raw_invocation_job_ids']==['3022743'])
 for p,h in root['files'].items():watch(p,h)
 config=read(proof['original_config']['path'],proof['original_config']['sha256']);man=read(proof['manifest']['path'],proof['manifest']['sha256']);panel=read(proof['panel']['path'],proof['panel']['sha256'])
 ck('config_manifest_run_signature',config['manifest']==man and dig(enc(config))==root['run_signature']==proof['original_prefix']['run_signature'])
 ck('fixed_development_panel100_taskbalance',len(panel['states'])==100 and Counter(x['task_id'] for x in panel['states'])=={i:10 for i in range(10)} and dig(enc(panel))==config['panel_signature'])
 identities={x['identity']['method_id']:x['identity'] for x in man['methods']};methods=list(identities)
 ck('six_exact_methods_order',methods==['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'])
 ck('original_root_model_method_binding',all(root['source_provenance']['method_bindings'][k]['identity']==v for k,v in identities.items()))
 ck('base_revision_and_selected_checkpoint_identity',all(v['model_revision']=='6d0231af0e48c5985f1ff86908f4674b84bc049b' and v['frozen_model_sha256']=='6a34ed9b4790fa889eb36406a1182d3d89ee539f7a65cb2f72d67e8326d557e7' and not v['future_head_deployed'] for v in identities.values()) and identities['A128_seed17']['checkpoint_sha256']=='68953d2b4f0325b54df698b3ed7aadb19ac1d53b2b53bb9e0b8ff7abb0c84a40' and identities['B128_seed17']['checkpoint_sha256']=='ea56dea4fd9f67c99c2b149b123a2112ae7e5971249fe86f697128000d7d1b7e')
 inv=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 for rel,h in inv['files'].items():
  for base in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):watch(base/rel,h)
 ck('frozen173_all_original_aliases',len(inv['files'])==173)
 target=read(proof['target']['contract']['path'],proof['target']['contract']['sha256'])
 for rel,h in {**target['files'],**target['GPU_acceptance'],**target['runtime_contract']['dependencies']}.items():watch(rel,h)
 ck('target_settings_not_changed',target['scientific_settings_changed'] is False and target['final_evaluation_enabled'] is False and target['runtime_contract']['suite']=='libero_spatial')
 sys.path.insert(0,str(S/'src'));from cti_vla.evaluation import libero_runtime as runtime
 reviewer=load(watch('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'),'sp12_ind_actual_semantic_reviewer')
 ck('exact_target_action_semantic_hash',reviewer.semantic_identity(target)==proof['target']['action_semantics_sha256'])
 # Reconstruct the only removed AST statement independently, rather than trusting
 # a verdict for another suite or selecting outcomes.
 source=(S/'src/cti_vla/evaluation/libero_runtime.py').read_bytes();tree=ast.parse(source);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run_episode')
 needle='if bool((np.abs(chunk.environment_actions) > 1.00001).any()):\n    raise ValueError("environment action outside normalized controller [-1, 1] range")';needle_node=ast.parse(needle).body[0]
 found=[x for x in ast.walk(fn) if isinstance(x,ast.If) and ast.dump(x,include_attributes=False)==ast.dump(needle_node,include_attributes=False)]
 ck('exact_single_pure_range_branch',len(found)==1 and not any(isinstance(n,ast.Call) and ('random' in ast.unparse(n.func) or 'seed' in ast.unparse(n.func)) for n in ast.walk(found[0])))
 sys.path.insert(0,str(S/'src'));from cti_vla.evaluation import libero_runtime as runtime
 adapter=load(watch('results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185'),'sp12_ind_exact_action_adapter')
 old,new,astproof=adapter.derive_function(runtime,source)
 ck('accepted_action_adapter_only_branch_and_no_binding_mutation',astproof['removed_if_count']==1 and astproof['other_AST_nodes_unchanged'] and runtime.run_episode is old)
 states={x['trial_id']:x for x in panel['states']};expected=[x['trial_id']+':'+m for x in panel['states'] for m in methods];ledger_path=watch(proof['original_prefix']['path'],proof['original_prefix']['sha256'])
 raw=ledger_path.read_bytes();rows=[dec(x) for x in raw.splitlines()];ck('exact_one_invocation_24trial_events',len(rows)==25 and rows[0]['event']=='invocation' and rows[0]['slurm_job_id']=='3022743')
 pertrial_author=[dec(x) for x in (AUTHOR/'per_trial_compatibility.jsonl').read_bytes().splitlines()];chunk_author=[dec(x) for x in (AUTHOR/'per_chunk_compatibility.jsonl').read_bytes().splitlines()];independent=[];chunk_out=[];group=defaultdict(set);sample=None
 for i,(start,row) in enumerate(zip(rows[1::2],rows[2::2])):
  ck('start_result_pair_'+str(i),start['event']=='start' and row['event']=='result' and row['trial_id']==start['trial_id']==expected[i] and all(row[k]==v for k,v in start.items() if k not in ('created_utc','event')))
  st=states[row['state_trial_id']];ident=identities[row['method']];full,acts,metadata=inspect_trial(row,ident,st)
  q=[dict(trial_id=row['trial_id'],**md) for md in metadata];chunk_out.extend(q);group[row['state_trial_id']].add(row['chunks'][0]['observation_sha256'])
  derived={'trial_id':row['trial_id'],'full_emitted_f64le_sha256':dig(full.tobytes()),'executed_f64le_sha256':dig(acts.tobytes()),'full_emitted_chunks':len(metadata),'executed_actions':len(acts),'old_range_branch_taken':False,'controller_clip_changes_bytes':False,'metadata_sequence_sha256':dig(enc([x['metadata_sha256'] for x in metadata])),'identity_sha256':dig(enc(ident)),'raw_initial_state_sha256':st['initial_state_sha256']}
  author=pertrial_author[i];ck('independent_pertrial_matches_'+str(i),all(author[k]==derived[k] for k in ('trial_id','full_emitted_f64le_sha256','executed_f64le_sha256','full_emitted_chunks','executed_actions','metadata_sequence_sha256')) and author['method_identity_sha256']==derived['identity_sha256'])
  # Recompute accepted queue pass-through using the actual function on a fake
  # env/policy. This consumes recorded policy arrays; it is not another rollout.
  def run(fn):
   ob={'agentview_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eye_in_hand_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eef_pos':np.zeros(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
   class E:
    def __init__(self):self.sent=[]
    def reset(self):return ob
    def set_init_state(self,x):return ob
    def step(self,a):self.sent.append(a);return ob,0.,len(self.sent)==10+len(acts) if row['success'] else False,{}
   class Q:
    def __init__(self):self.i=0
    def __call__(self,o,l):
     c=row['chunks'][self.i];self.i+=1;return runtime.PolicyChunk(np.array(c['normalized_actions'],dtype=np.float32),np.array(c['environment_actions'],dtype=np.float64),c['metadata'])
   e=E();before=(random.getstate(),enc([np.random.get_state()[0],np.random.get_state()[1].tolist(),*np.random.get_state()[2:]]));v=fn(e,Q(),'CPU recorded trace',np.array(st['initial_state']),wait_steps=10,max_steps=220);after=(random.getstate(),enc([np.random.get_state()[0],np.random.get_state()[1].tolist(),*np.random.get_state()[2:]]))
   ck('RNG_pass_through_'+str(i),before==after)
   ck('loop_queue_pass_through_'+str(i),matrix(e.sent[10:]).tobytes()==acts.tobytes() and matrix(e.sent[:10]).tobytes()==matrix([list(runtime.DUMMY_ACTION)]*10).tobytes() and v['status']==row['status'] and v['success']==row['success'] and v['control_steps']==len(acts))
   return dig(matrix(e.sent).tobytes())
  oldhash,newhash=run(old),run(new);ck('both_loop_action_paths_byte_identical_'+str(i),oldhash==newhash==author['old_runtime']['all_wait_and_control_f64le_sha256']==author['target_runtime']['all_wait_and_control_f64le_sha256'])
  derived['old_and_current_full_action_trace_sha256']=oldhash;independent.append(derived)
  if sample is None:sample=(copy.deepcopy(row),ident,st)
 ck('all122_chunk_receipts_independently_reconstructed',chunk_out==chunk_author and len(chunk_out)==122)
 ck('12trials917controls_two_initial_states',len(independent)==12 and sum(x['executed_actions'] for x in independent)==917 and len(group)==2)
 ck('all_six_method_recorded_t0_hashes_equal_per_state',all(len(x)==1 for x in group.values()))
 ck('exact_remaining588_identity_order',proof['legacy_trial_ids']==expected[:12] and len(expected[12:])==588 and dig(enc(expected[12:]))==proof['remaining_trial_ids_sha256'])
 # Negative tests target our independently implemented raw-trace checker.
 row,identity,state=sample
 for kind in ('nan','over_range','queue','metadata_budget','checkpoint','state'):
  bad=copy.deepcopy(row);idcopy=copy.deepcopy(identity);stcopy=copy.deepcopy(state)
  if kind=='nan':bad['chunks'][0]['environment_actions'][0][0]=float('nan')
  elif kind=='over_range':bad['chunks'][0]['environment_actions'][0][0]=1.000001
  elif kind=='queue':bad['executed_actions'][0][0]+=0.01
  elif kind=='metadata_budget':bad['chunks'][0]['metadata']['visual_tokens']=31
  elif kind=='checkpoint':idcopy['method_id']='A128_seed17'
  else:stcopy['initial_state_sha256']='0'*64
  rejection('reject_mutated_'+kind,lambda bad=bad,idcopy=idcopy,stcopy=stcopy:inspect_trial(bad,idcopy,stcopy))
 # Independent installed wheel byte/stat continuity evidence; explicitly source
 # inference, never a retrospectively captured old controller instance.
 history=read(AUTHOR/'historical_identity.json','9980917fedc08fc39bb2b5eed1b2d522ef956eadf8e4e8ee8c55297332a4c9aa');members=read(AUTHOR/'installed_package_members.json','a0512c95f29f406c211a2222ffdc2d7eb564d93f8ffbab75a6746d54ef560a39');byname={x['member']:x for x in members};cutoff=datetime(2026,10,17,tzinfo=timezone.utc).timestamp();seen=[]
 for pkg,prefix in zip(history['packages'],('robosuite/','mujoco/')):
  wheel=watch(pkg['wheel'],pkg['sha256'])
  with zipfile.ZipFile(wheel) as z:
   for item in z.infolist():
    if not item.filename.startswith(prefix) or item.is_dir():continue
    p=SP/item.filename;st0=p.stat();b=p.read_bytes();st1=p.stat();a=byname[item.filename]
    ck('wheel_member:'+item.filename,p.resolve()==p and not p.is_symlink() and dig(b)==dig(z.read(item))==a['sha256'] and len(b)==a['bytes'] and st0==st1 and st0.st_ctime<cutoff and st0.st_mtime<cutoff)
    seen.append(item.filename)
 ck('1058_exact_installed_members',len(seen)==len(set(seen))==1058 and set(seen)==set(byname))
 ck('no_private_macros',not (SP/'robosuite/macros_private.py').exists())
 limits=read(SP/'robosuite/controllers/config/osc_pose.json');ck('source_controller_delta_limits',limits['control_delta'] is True and limits['input_min']==-1 and limits['input_max']==1 and limits==history['limits'])
 base=(SP/'robosuite/controllers/base_controller.py').read_text();osc=(SP/'robosuite/controllers/osc.py').read_text();ck('controller_source_existing_clip_and_delta',base.count('action = np.clip(action, self.input_min, self.input_max)')==1 and 'self.use_delta = control_delta' in osc and 'scaled_delta = self.scale_action(delta)' in osc)
 oldlog=watch(history['old_import_log']['path'],history['old_import_log']['sha256']).read_text();ck('actual_old_venv_import_and_missing_macros',str(SP/'robosuite/scripts/setup_macros.py') in oldlog and 'No private macro file found!' in oldlog)
 install=watch(history['installation_success']['path'],history['installation_success']['sha256']).read_text();ck('historic_install_success',all(t in install for t in ('Verified transferred runtime packages: 11','Successfully installed','runtime_imports_passed')))
 wrapper=watch(history['LIBERO_env_wrapper']['path'],history['LIBERO_env_wrapper']['sha256']);ck('old_LIBERO_OSC_factory',wrapper.stat().st_ctime<cutoff and 'controller="OSC_POSE"' in wrapper.read_text() and 'suite.load_controller_config(default_controller=controller)' in wrapper.read_text())
 v4=watch('results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl','54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c');controllers=[dec(x) for x in v4.read_bytes().splitlines() if dec(x).get('event')=='actual_controller_verified' and dec(x).get('suite')=='libero_spatial']
 ck('actual_target_four_Spatial_controllers',len(controllers)==4)
 for c in controllers:
  cc=c['controller'];ck('target_controller:'+c['method_id'],cc['actual_use_delta'] is True and cc['controller_type']=='robosuite.controllers.osc.OperationalSpaceController' and cc['limits']==dict(input_min=[-1.]*6,input_max=[1.]*6,output_min=limits['output_min'],output_max=limits['output_max']))
  for item in cc['methods'].values():watch(item['path'],item['sha256'])
 source=(S/'scripts/eval_formal_selector_libero.py').read_text();ex=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='execute');reseed=next(x for x in ex.body if isinstance(x,ast.FunctionDef) and x.name=='reseed');factory=next(x for x in ex.body if isinstance(x,ast.FunctionDef) and x.name=='factory')
 ck('same_frozen_per_trial_RNG_rule',ast.unparse(reseed)=='def reseed():\n    random.seed(17)\n    np.random.seed(17)\n    torch.manual_seed(17)' and 'env.seed(0)' in ast.unparse(factory))
 ck('historical_limits_candid',history['actual_historical_controller_instance_capture'] is False and history['RNG']['old_full_snapshot_recorded'] is False)
 failed=read('results/formal_main_v2/job_receipts/3042529.json','86676fe6e84440069e61f4609008c4e5a9a7c88e883444519479d45767bd011e');ck('failed3042529_not_ledger_origin',failed['status']=='failed' and failed['original_scientific_wrapper_executed'] is False and not failed['adapter_artifacts'] and not failed['adapter_receipts'] and not failed['action_execution_artifacts'] and all(str(x.get('slurm_job_id',''))!='3042529' for x in rows))
 ck('existing393sec_allocation_kept_once',root['cost']['current_gpu_seconds']==root['cost']['all_attempt_gpu_seconds']==393 and root['cost']['allocations'][0]['job_id']=='3022743')
 for p,x in evidence.items():ck('final_evidence_unchanged:'+p,sha(p)==x['sha256'])
 write('independent_trials.json',independent);write('independent_chunks.json',chunk_out);write('source_evidence.json',evidence)
 return {'schema':'formal_main_v2','kind':'Spatial12_legacy_compatibility_independent_review','status':'passed','reviewed_by':'independent','review_agent':'/root/goal_cpu_gate_2054','proof_sha256':proof['original_prefix'].get('proof_sha256',sha(AUTHOR/'compatibility_proof.json')),'manifest_sha256':sha(AUTHOR/'phase1_manifest.json'),'phase1_manifest_sha256':sha(AUTHOR/'phase1_manifest.json'),'scope':proof['scope'],'blockers':[],'check_count':len(checks),'checks':checks,'counts':{'trials':12,'chunks':122,'executed_actions':917,'unique_initial_states':2},'full_original_author_reconstruction_passed':True,'independent_byte_and_queue_reconstruction_passed':True,'all_six_methods_recorded_t0_equal_for_two_states':True,'all_source173_and_current_action_AST_verified':True,'historical_controller_identity_basis':'Independent old install/import/archive evidence and exact1058 installed wheel bytes/stat continuity; source-derived inference, not captured historical controller instance. Current Spatial real controller events agree.','historical_instance_capture_available':False,'historical_full_RNG_dump_available':False,'RNG_basis':'Frozen per-trial reseed/factory; only pure range predicate deleted, false on all122 emitted chunks; CPU recorded action paths consume no Python/NumPy RNG.','no_other_suite_equivalence_borrowed':True,'legacy_origin_preserved':'3022743 original formal-downstream-root-v1, never rewritten as current action wrapper origin','actual_supplemental_environment_rollouts':0,'remaining588_registration_or_submission_authorized':False,'production_admission':False,'requires_separate_root_explicit_adoption':True,'original393GPU_seconds_already_accounted_once':True,'3042529_pre_adapter_failure_kept_distinct':True,'new_GPU_seconds':0,'new_scientific_trials':0,'weights_read':False,'sealed_values_read':False,'state_Git_P_mutations':False}
try:report=main()
except BaseException as e:
 import traceback
 report={'status':'failed','checks':checks,'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()};write('failed_review.json',report);print(json.dumps({k:report[k] for k in ('status','error_type','error')}));raise
write('independent_review.json',report);print(json.dumps({k:report[k] for k in ('status','check_count','counts','new_GPU_seconds','production_admission')}))
