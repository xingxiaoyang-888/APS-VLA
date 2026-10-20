"""Independent read-only original-chain audit of exactly Spatial/Object fixed30 collect plans."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,os,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent;A=R/'.local/spatial_object_collect_20261020T1825';F='scripts/ops/formal_action_deployment_v1/';INVENTORY='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
READS={};CHECKS=[];NEG=[];REPORTS=[];started=time.process_time();sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'src'))
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):raise RuntimeError('No real process, network or scheduler allowed')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,int):return
  p=Path(os.fsdecode(p)).absolute()
  if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('Weight/sealed payload read prohibited '+str(p))
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
  if writing:assert D in p.parents,'private outputs only '+str(p)
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  for v in args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]:
   p=Path(os.fsdecode(v)).absolute();assert p==D or D in p.parents,'outside private mutation'
sys.addaudithook(guard)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(ok,msg):
 if not ok:raise AssertionError(msg)
 CHECKS.append(msg)
def raw(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;check(p.resolve()==p and not p.is_symlink(),'canonical input '+str(p));b=p.read_bytes();h=hashlib.sha256(b).hexdigest();check(pin is None or pin==h,'SHA '+str(p));check(str(p) not in READS or READS[str(p)]==h,'stable input '+str(p));READS[str(p)]=h;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
def ref(p):return dict(path=Path(p).relative_to(R).as_posix(),sha256=sha(p),bytes=Path(p).stat().st_size)
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
 return ref(p)
def load(rel,pin,base=R):
 p=base/rel;raw(p,pin);name='ind_collect_'+p.stem+'_'+str(len(READS));sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);sys.path.insert(0,str(S/'src'));return m
def reject(name,fn,needle=None):
 try:fn()
 except (ValueError,RuntimeError,AssertionError) as ex:
  check(needle is None or needle in str(ex),'expected rejection '+name);NEG.append(dict(name=name,error_type=type(ex).__name__,message=str(ex),synthetic_in_memory=True));return
 raise AssertionError('unsafe fault accepted '+name)
try:
 author=obj(A/'delivery_manifest.json','bc95cc4708b91e36dd76799f2b6556ca3a7329f9a2547f113b1844bcdeac2a1f');check(author['file_count']==67 and len(author['files'])==67,'67-file sealed author package')
 for x in author['files']:
  p=R/x['path'] if str(x['path']).startswith('.local/') else A/x['path'];raw(p,x['sha256']);check(p.stat().st_size==x['bytes'],'candidate byte length '+x['path'])
 publication=obj('results/formal_main_v2/preflight/heartbeat_20261021T0225/Spatial_Object_collect_plan_publication.json','850bbba409046e2e03914300971c6bd554cd7717a41482840fa3122f50dd8b57')
 inv=obj(INVENTORY,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');check(len(inv['files'])==173,'original173 count')
 for root in (R,S):
  for name,pin in inv['files'].items():raw(root/name,pin)
 import cti_vla
 check(S/'src' in Path(cti_vla.__file__).resolve().parents,'fresh frozen cti_vla package origin')
 wrapper=load('scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',P)
 legacy=load('scripts/ops/formal_evaluation_adapter.py','b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd',P)
 h=load('scripts/formal_execution_manifests.py','614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89')
 planner=load('scripts/ops/formal_downstream_supervisor.py','f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571')
 contract=load(F+'contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19')
 runtime=load(F+'runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53')
 outer=load(F+'wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',P)
 state=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());state_pin=sha(R/'results/experiment_supervisor/state.json');state_before=copy.deepcopy(state)
 check(state['pending_submission'] is None and not state['formal_main_progress']['test_opened'] and not state['formal_main_progress']['global_release_created'],'observed registry pending clear and final sealed')
 from cti_vla.evaluation import formal_profiling as fp
 from cti_vla.data.formal_initial_states import load_formal_development_panel
 registration=obj('configs/experiments/formal_main_v2.json',inv['files']['configs/experiments/formal_main_v2.json'])
 # Independent temporal/proxy test: simulator reuses the same mutable array buffers.
 import numpy as np
 class ReusingEnv:
  def __init__(self):self.n=0;self.ob={k:np.zeros((2,),dtype=np.float32) for k in fp.RAW_KEYS}
  def reset(self):return self.ob
  def set_init_state(self,x):return self.ob
  def step(self,a):
   self.n+=1
   for ar in self.ob.values():ar[:]=self.n
   return self.ob,0.,False,{}
 env=ReusingEnv();cap=fp.CaptureControlObservations(env);cap.reset();cap.set_init_state(None)
 for i in range(27):cap.step(np.zeros(7))
 check(len(cap.captured)==17 and [float(next(iter(x.values()))[0]) for x in cap.captured]==list(map(float,range(10,27))),'proxy copies all17 control pre-action observations after exactly10 wait steps')
 check(fp.selected_control_steps(17)==[0,8,16] and [float(next(iter(cap.captured[i].values()))[0]) for i in fp.selected_control_steps(17)]==[10.,18.,26.],'first/middle/last reference pre-action values without buffer mutation')
 reject('capture_resampling',cap.reset,'one trajectory');reject('wait_changed',lambda:fp.CaptureControlObservations(ReusingEnv(),wait_steps=9),'ten wait');reject('step_before_init',lambda:fp.CaptureControlObservations(ReusingEnv()).step(np.zeros(7)),'state must be set')
 for value in [0,1,2,True,3.0]:reject('short_or_noninteger_control_count_'+repr(value),lambda value=value:fp.selected_control_steps(value),'never pad or substitute')
 for label,suite,limit,indices in [('Spatial','libero_spatial',220,[3,7,5,1,7,3,13,3,1,6]),('Object','libero_object',280,[5,8,0,1,2,11,3,7,1,2])]:
  folder=D/label;folder.mkdir();candidate=A/label/'plan_v1';dest='results/formal_main_v2/execution/'+label.lower()+'_collect_action_v1_20261020T1825';refs={}
  for filename in ['scientific_plan.json','effective_plan.json','execution_contract.json']:
   b=raw(candidate/filename);pin=hashlib.sha256(b).hexdigest();raw(dest+'/'+filename,pin);raw(P/dest/filename,pin);refs[filename]={'path':dest+'/'+filename,'sha256':pin}
  science=obj(dest+'/scientific_plan.json');effective=obj(dest+'/effective_plan.json');execution=obj(dest+'/execution_contract.json');manifest=obj(dest+'/dense_development.json');argsdict=obj(candidate/'plan_arguments.json');selected=obj(A/label/'collection_selection_registration.json');devref=selected['development_panel'];dev=load_formal_development_panel(R/devref['path']);raw(devref['path'],devref['sha256']);raw(P/devref['path'],devref['sha256'])
  fixed=[min((row for row in dev['states'] if row['task_id']==i),key=lambda row:row['source_state_index']) for i in range(10)]
  check(len(dev['states'])==100 and [x['source_state_index'] for x in fixed]==indices and fixed==selected['selected_states']==fp.fixed_profile_states(dev),'independent minimum developmental index and exact task order '+suite)
  check(manifest['suite']==suite and manifest['split']=='development' and fp.validate_profile_manifest(manifest,registration,collect=True)==['dense'],'development dense only '+suite)
  check(manifest['environment']==dict(action_chunk=8,environment_seed=0,max_steps=limit,runtime_seed=17,wait_steps=10),'original suite environment '+suite)
  ev=h.Evidence(R);sources=h.source_contract(ev,INVENTORY);reg=h.registration_contract(ev,h.REGISTRATION);rows=h.suite_rows(ev,reg,suite,sources,['dense']);rebuilt_manifest=h.make_execution(reg,suite,rows);rebuilt_manifest.update(development_panel=devref['path'],development_panel_sha256=ev.watch(devref['path']))
  check(rebuilt_manifest==manifest and rows==[obj('results/formal_main_v2/execution/'+suite+'_development_first_pair_v1.json')['methods'][0]],'original builder and established official Dense identity exactly reconstruct '+suite);ev.unchanged()
  profiles=[j for j in state['registered_jobs'] if j.get('suite')==suite and (j.get('mode') in ('collect','full','components') or j.get('stage') in ('collect','full','components'))];check(not profiles,'unfiltered current registry no prior collect/profile '+suite)
  check(planner.plan(SimpleNamespace(**argsdict),copy.deepcopy(state),project=R,helper=h)==science,'original planner actual current unfiltered registry rebuild '+suite)
  check(contract.validate_effective(science,effective,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution),'original action effective plan reconstruction '+suite)
  invocation=science['invocation'];check(invocation['stage']=='collect' and invocation['method_ids']==['dense'] and invocation['prior_job_ids']==[] and invocation['resume'] is False,'no prior/reuse/resume '+suite)
  for base in (R,P):check(not(base/science['output_relative']).exists() and not(base/science['invocation_relative']).exists(),'no output/invocation duplicate '+suite+' '+str(base))
  args=wrapper.verify(invocation);check(args.mode=='collect' and args.global_freeze is None and args.panel is None,'actual P original wrapper collect-only '+suite)
  args.prepare_only=True;prep=legacy.run(args,mode='collect',source_root=S,source_inventory=P/INVENTORY,adapter_sha256='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd',resume=False)
  check(prep['status']=='prepared_only' and prep['command']=='collect' and prep['methods']==['dense'] and prep['gpu_calls']==0 and prep['weights_validated'] is False and prep['test_opened'] is False and prep['observations']==30 and prep['fixed_state_ids']==[row['trial_id'] for row in fixed],'actual frozen profiler preparation selects same30 from10fixed states '+suite)
  prepref=put(folder/'actual_P_prepare_only.json',dict(result=prep,source_import_guard_preserved=True,weights_deserialized=False,actual_output_created=(P/science['output_relative']).exists(),actual_GPU_collection=False))
  rw={}
  for base in (R,P):
   for path,pin in runtime.validate_contract(execution['runtime_contract'],project_root=base,source_root=S).items():raw(path,pin);rw[path]=pin
   for rel,pin in execution['files'].items():raw(base/rel,pin)
   for rel,pin in effective['publish_files'].items():raw(base/rel,pin)
  for path,pin in effective['invocation']['watched_files'].items():raw(path,pin)
  for rel,pin in effective['invocation']['support_files'].items():raw(P/rel,pin)
  for rel,pin in invocation['root_evidence_sha256'].items():raw(rel,pin)
  components=obj(candidate/'runtime_readiness_draft.json')['component_reviews']
  for role,r in components.items():
   rv=obj(r['path'],r['sha256']);raw(P/r['path'],r['sha256']);check(rv['status']=='passed_CPU_review' and rv['component']==role and rv['review_role']=='independent' and not rv.get('blockers') and rv['production_chain_complete'] is False,'exact inherited component with original limits '+suite+role)
   for p,pin in rv.get('evidence_sha256',{}).items():raw(p,pin)
  reject(suite+'_unsigned_outer',lambda:outer.verify(effective['invocation'],project=P),'Exact path/SHA')
  bad=copy.deepcopy(effective);bad['invocation']['argv'].append('--prepare-only');reject(suite+'_scientific_argv_tamper',lambda:contract.validate_effective(science,bad,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution),'Scientific invocation changed')
  bad=copy.deepcopy(effective);bad['resources']['gres']='gpu:l40:2';reject(suite+'_resources_tamper',lambda:contract.validate_effective(science,bad,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution),'Scientific/resource plan changed')
  bad=copy.deepcopy(manifest);bad['split']='final';reject(suite+'_final_input',lambda:fp.validate_profile_manifest(bad,registration,collect=True),'development observations')
  bad=copy.deepcopy(manifest);bad['methods']=obj('results/formal_main_v2/execution/'+suite+'_development_first_pair_v1.json')['methods'];reject(suite+'_selector_input',lambda:fp.validate_profile_manifest(bad,registration,collect=True),'fixed dense-only')
  for name,delta,fragment in [('full',dict(stage='full'),'complete global freeze'),('components',dict(stage='components'),'complete global freeze'),('panel_substitution',dict(profile_panel=dest+'/panel.json'),'cannot substitute'),('partial',dict(stop_after=1),'Only rollouts'),('resume',dict(resume=True),'No registered prior')]:reject(suite+'_'+name,lambda delta=delta:planner.plan(SimpleNamespace(**{**argsdict,**delta}),copy.deepcopy(state),project=R,helper=h),fragment)
  check(fp.selected_control_steps(limit)==[0,(limit-1)//2,limit-1],'registered temporal selection '+suite)
  consumer=raw(R/F/'consumer.py').decode();reviewer=raw(R/F/'reviewer.py').decode();check('rebuilt = mod.review' in consumer and 'New root review does not exactly rebuild' in consumer and 'clone(old.collect, trajectory=trajectory)' in reviewer and 'runtime.verify_runtime_events' in reviewer,'original consumer/reviewer whole collection and accepted action provenance retained '+suite)
  runtime.unchanged(rw);check(state==state_before,'read-only planning and negative tests preserved registry '+suite)
  report=dict(schema='formal_main_v2',kind='formal_action_runtime_plan_review',status='passed',review_role='independent',reviewed_by='independent',review_agent='/root/devplans_audit_20261020_1418',execution_version='formal-downstream-action-v1',suite=suite,stage='collect',allowed_stages=['collect'],method_ids=['dense'],stage_key=invocation['stage_key'],scientific_plan=refs['scientific_plan.json'],effective_plan=refs['effective_plan.json'],action_execution_contract=refs['execution_contract.json'],plan_sha256=effective['plan_sha256'],runtime_sources=execution['files'],component_reviews=components,production_chain_complete=True,meaning_of_production_chain_complete='Exact canonical scientific/action inputs, unmodified original P wrapper/frozen prepare-only, and inherited producer/reviewer/consumer source closure passed CPU audit. This does not mean actual GPU collect or final runtime readiness has completed.',CPU_only=True,actual_P_original_wrapper_passed=True,actual_P_original_collector_prepare_only_passed=True,actual_GPU_runtime_chain_verified=False,real_GPU_collect=False,actual_collect_GPU_completed=False,scientific_settings_changed=False,final_evaluation_enabled=False,full_components_authorized=False,global_freeze_enabled=False,weights_deserialized=False,final_values_read=False,source173_unchanged=True,state_registry_Git_modified=False,new_scheduler_queries=0,new_GPU_calls=0,new_scientific_success_trials=0,source_development_states=100,selected_development_states=10,expected_observations=30,fixed_source_indices=indices,temporal_rule='Pre-action control observations first, floor((N-1)/2), last; N>=3; no waiting steps, replacement or success filter.',environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_control_steps=limit,prior_job_ids=[],resume=False,fresh_preparation=prepref,publication=ref(R/'results/formal_main_v2/preflight/heartbeat_20261021T0225/Spatial_Object_collect_plan_publication.json'),audit_source=ref(Path(__file__)),limitations=['Root must first bind separate root/independent readiness and pass actual P outer wrapper.verify.','Completed-controller gateway branch and actual live max8 reservation/pending/ACK are separately audited; this report grants no submission authority.','Actual observations require original plus action raw-consumer and independent terminal reconstruction before timing use.','Inherited component/v4 GPU evidence is not a new GPU test. All Goal science and final values remain sealed.'])
  REPORTS.append((folder/'independent_readiness.json',report))
 origins={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='cti_vla' or n.startswith('cti_vla.')) and getattr(m,'__file__',None)};check(origins and all(S/'src' in Path(p).parents for p in origins.values()),'all actual cti_vla code imported from frozen S/src')
 for p,pin in list(READS.items()):check(sha(p)==pin,'all audited evidence unchanged '+p)
 evidence=put(D/'evidence_sha256.json',READS);details=put(D/'CPU_checks.json',dict(checks=CHECKS,negative_cases=NEG,positive_count=len(CHECKS),negative_count=len(NEG),source_modules=origins,all_sources_unchanged=True,current_registry_observation_sha256=state_pin,CPU_seconds=time.process_time()-started,not_live_capacity_authorization=True))
 out=[]
 for path,report in REPORTS:report.update(detailed_CPU_report=details,evidence=evidence);out.append(put(path,report))
 put(D/'independent_index.json',dict(schema='formal_main_v2',status='passed_CPU_plan_review_pending_root_readiness',plans=out,expected_observations_total=60,scientific_success_trials_added=0,actual_GPU_collect_completed=False,source_package=ref(A/'delivery_manifest.json'),detailed_CPU_report=details))
 print(json.dumps(dict(reviews=out,index=ref(D/'independent_index.json'),checks=len(CHECKS),negative_count=len(NEG),CPU_seconds=time.process_time()-started)))
except BaseException as ex:
 put(D/'audit_failure_v1.json',dict(status='failed',error=str(ex),error_type=type(ex).__name__,traceback=traceback.format_exc(),checks_completed=len(CHECKS),negative_cases=NEG));raise
