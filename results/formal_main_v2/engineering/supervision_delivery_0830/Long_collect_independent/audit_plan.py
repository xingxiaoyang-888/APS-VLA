"""Independent per-plan CPU readiness of canonical Long fixed30 collection."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/long_collect_independent_0830'
A=R/'.local/long_collection_prepare_0830/a2'
C='results/formal_main_v2/execution/long_collect_action_v1_0830'
F='scripts/ops/formal_action_deployment_v1/'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PINS={
'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',
F+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
F+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
F+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'}
PLAN_PINS={'scientific_plan.json':'1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0','execution_contract.json':'06ca8c538a323e14ad8197a80e9cc5c39d303976adbd8959630e535b11b1acc0','effective_plan.json':'1ce34d9ecf18e36d2c0043e2fdfd42ca327344d286fb35704fdfe70e8b5ed8ac'}
READS={};CHECKS=[];NEG=[]
sys.dont_write_bytecode=True
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('Independent plan review cannot spawn or connect')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('Forbidden payload read')
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writing and D not in p.parents:raise RuntimeError('Only independent private outputs may be written')
sys.addaudithook(guard)
def check(ok,name):
 if not ok:raise ValueError(name)
 CHECKS.append(name)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p
 check(p.resolve()==p and (R in p.parents or P in p.parents),'canonical evidence '+str(p))
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
 check(pin is None or h==pin,'raw SHA '+str(p))
 check(str(p) not in READS or READS[str(p)]==h,'evidence stable '+str(p));READS[str(p)]=h
 return raw
def obj(p,pin=None):return json.loads(read(p,pin))
def sig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()).hexdigest()
def write(name,value):
 raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 p=D/name
 with p.open('xb') as f:f.write(raw)
 return dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(rel,root=R):
 p=root/rel;read(p,PINS[rel])
 spec=importlib.util.spec_from_file_location('independent_'+p.stem+'_'+str(len(sys.modules)),p)
 m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def reject(name,fn,needle):
 try:fn()
 except (RuntimeError,ValueError) as e:
  check(needle in str(e),'precise rejection '+name+': '+str(e));NEG.append(dict(name=name,error_type=type(e).__name__,error=str(e),in_memory_fault_only=True));return
 raise ValueError('Unsafe accepted negative fixture '+name)
def main():
 inp=obj(D/'input_independent_review.json','fa878235152fe2930653812c6d2ddf7aabdac02f65aa49bdef478d8a06bb6e47')
 check(inp['status']=='passed_inputs_only_plan_not_yet_accepted' and inp['checks_passed']==565,'independent previous 565 input checks')
 fresh=obj(D/'fresh_prepare_only.json','a5089c9ef28878cffc11f159dbb221a71f830a2b5fb340e0ffde67fe55baf410')
 check(fresh['status']=='passed' and fresh['original_P_wrapper_verified'] and fresh['result']['status']=='prepared_only','own independent fresh actual original prepare-only')
 read(D/'fresh_prepare_only.py','1b86462d2a9bf3f8dd05d673ba8235ce4023130c5ef3847c16cc2f95f3e41d50')
 check(fresh['new_GPU_calls']==0 and fresh['actual_output_created'] is False and fresh['weights_deserialized'] is False,'prepare-only no runtime execution')
 for name,h in PLAN_PINS.items():
  read(R/C/name,h);read(P/C/name,h);read(A/name,h)
 science=obj(R/C/'scientific_plan.json');effective=obj(R/C/'effective_plan.json');execution=obj(R/C/'execution_contract.json')
 refs={name:dict(path=C+'/'+name,sha256=h) for name,h in PLAN_PINS.items()}
 for name,plan in [('scientific',science),('effective',effective)]:
  check(plan['plan_sha256']==sig({k:v for k,v in plan.items() if k!='plan_sha256'}),'canonical '+name+' plan signature independently recomputed')
 check(science['plan_sha256']=='33efb5e07b90a9ee54009316182545ec42142d2e0f0e74c6514cdd591f57809c','scientific canonical pin')
 check(effective['plan_sha256']=='97201437512d09f286bd90024510adeccb9746ceba3de16c41587c4371bc6973','effective canonical pin')
 pub=obj('results/formal_main_v2/preflight/heartbeat_20261020T1630/Long_collect_plan_publication.json','0a169d85a8ac70941865ea590e8f52e7454a24d747ccbc72559479abf5801701')
 check(pub['state_unchanged'] and pub['new_GPU_submissions']==0 and len(pub['copied'])==6,'exact static publication scope')
 pm=obj(A/'publication_map.json','391b030df7fdda0030ed3054bd9e7139ef41886bdb1444f1c1a06bf407b4c1cf')
 for row in pm['files']:
  for base in [R,P]:check(len(read(base/row['canonical_path'],row['sha256']))==row['bytes'],'published bytes '+str(base/row['canonical_path']))
 inventory=obj(INV,INV_SHA);check(len(inventory['files'])==173,'exact173 source count')
 for base in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:
  for rel,h in inventory['files'].items():read(base/rel,h)
 inv=science['invocation']
 check(inv['stage']=='collect' and inv['suite']=='libero_10' and inv['method_ids']==['dense'],'Long Dense-only collect')
 check(inv['resume'] is False and inv['stop_after'] is None and not inv['prior_job_ids'] and inv['prior_review'] is None,'fresh complete collection no resume')
 check(inv['scientific_settings_changed'] is False and inv['final_values_read_locally'] is False,'unchanged science sealed final')
 check(inv['source_root']==str(S) and inv['source_inventory_sha256']==INV_SHA,'source binding')
 check(inv['execution_manifest_sha256']=='703980515d5b063c31276b0e610ffd6cdf68adae5e1f43cfb65ecd61d92923f1','exact Dense manifest identity')
 check(science['resources']==dict(job_name='cti-formal-downstream',account='p_p15016',qos='cpu-500_core-l40-8_card-a800-8_card',partition='L40',nodes=1,ntasks=1,cpus_per_task=7,gres='gpu:l40:1',mem='64G',time='04:00:00'),'single GPU original resources')
 for key in ['--sealed-final','--release','--global-freeze','--panel','--stop-after','--resume','--prepare-only']:
  check(key not in inv['argv'],'scientific argv forbidden '+key)
 check(inv['argv'][0]=='collect' and '--uncontended-gpu' in inv['argv'],'collect production argv')
 for mapname in ['support_files','root_evidence_sha256']:
  for rel,h in inv[mapname].items():read(R/rel,h)
 for path,h in effective['invocation']['watched_files'].items():read(Path(path),h)
 for rel,h in effective['invocation']['support_files'].items():read(R/rel,h);read(P/rel,h)
 for rel,h in effective['publish_files'].items():read(R/rel,h);read(P/rel,h)
 contract=load(F+'contract.py',P)
 check(contract.validate_effective(science,effective,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution) is True,'actual P immutable effective-plan validator')
 rebuilt_outer=contract.effective_plan(science,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution)
 check(rebuilt_outer==effective,'entire effective plan independently rebuilt')
 runtime=load(F+'runtime_scope.py',P)
 rw=runtime.validate_contract(execution['runtime_contract'],project_root=P,source_root=S)
 check(rw and execution['runtime_contract']['policy']['action_values']=='unchanged' and execution['runtime_contract']['policy']['final_allowed'] is False,'actual P runtime contract plus inherited actualGPU engineering acceptance')
 for p,h in rw.items():read(Path(p),h)
 wrapper=load('scripts/server/run_formal_downstream.py',P);args=wrapper.verify(inv)
 check(str(args.checkpoint)==execution['runtime_contract']['checkpoint'],'actual P original wrapper matches official Long base')
 helper=load('scripts/formal_execution_manifests.py');planner=load('scripts/ops/formal_downstream_supervisor.py')
 state=obj(A/'state_at_planning.json','88a6744e33ce2382e319a72d778656644d5ec18513dc5508ec1f50f1377b2891')
 argdict=obj(A/'plan_arguments.json','ae21751e8133945ccb57b26e8d2611e10ebfe5fd044a95eae0650a364ad98daa')
 snapshot_sig=sig(state)
 profiles=[j for j in state['registered_jobs'] if j.get('suite')=='libero_10' and (j.get('mode') in ('collect','full','components') or j.get('stage') in ('collect','full','components'))]
 check(not profiles and state.get('pending_submission') is None,'unfiltered saved planning registry has no prior Long collection')
 rebuilt=planner.plan(SimpleNamespace(**argdict),copy.deepcopy(state),project=R,helper=helper)
 check(rebuilt==science,'actual unmodified original scientific planner exactly reconstructs canonical plan')
 check(sig(state)==snapshot_sig,'snapshot unmodified')
 panel=obj('configs/manifests/formal_main_v2/libero_10/initial_states/development.json','46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268')
 fixed=[min([s for s in panel['states'] if s['task_id']==t],key=lambda s:s['source_state_index']) for t in range(10)]
 check(len(panel['states'])==100 and [s['source_state_index'] for s in fixed]==[0,4,7,3,6,2,3,6,8,2],'independent 10task minimum development source indices')
 check(fresh['result']['fixed_state_ids']==[s['trial_id'] for s in fixed],'actual prepare-only selection equals independent minima')
 for name in ['runtime','wrapper','raw_consumer']:
  row=obj(A/'runtime_readiness_draft.json','2f9d55368a95bbc3e742886f3c90bf55164caf18456ade70a8d65c00e518abae')['component_reviews'][name]
  value=obj(row['path'],row['sha256']);read(P/row['path'],row['sha256'])
  check(value['status']=='passed_CPU_review' and value['review_role']=='independent' and value['component']==name and not value['blockers'],'prior exact component independent '+name)
  for path,h in value.get('evidence_sha256',{}).items():read(R/path,h)
  check(value['production_chain_complete'] is False,'component-only limits retained '+name)
 outer=load(F+'wrapper.py',P)
 reject('outer_without_root_readiness',lambda:outer.verify(effective['invocation'],project=P),'Exact path/SHA reference required')
 bad=copy.deepcopy(effective);bad['invocation']['argv'].append('--prepare-only')
 reject('effective_scientific_argv_tamper',lambda:contract.validate_effective(science,bad,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution),'Scientific invocation changed')
 bad=copy.deepcopy(effective);bad['resources']['gres']='gpu:l40:2'
 reject('effective_resource_tamper',lambda:contract.validate_effective(science,bad,scientific_plan_ref=refs['scientific_plan.json'],execution_contract_ref=refs['execution_contract.json'],execution_contract=execution),'Scientific/resource plan changed')
 bad=copy.deepcopy(execution['runtime_contract']);bad['policy']['action_values']='clipped'
 reject('runtime_action_value_tamper',lambda:runtime.validate_contract(bad,project_root=P,source_root=S),'runtime contract fields')
 for name,change,needle in [('full_without_freeze',dict(stage='full'),'complete global freeze'),('components_without_freeze',dict(stage='components'),'complete global freeze'),('collect_substitution',dict(profile_panel=C+'/panel.json'),'cannot substitute'),('collect_resume',dict(resume=True),'No registered prior')]:
  altered={**argdict,**change}
  reject(name,lambda altered=altered:planner.plan(SimpleNamespace(**altered),copy.deepcopy(state),project=R,helper=helper),needle)
 check(sig(state)==snapshot_sig,'all in-memory fault checks preserve original registry snapshot')
 consumer=(R/F/'consumer.py').read_text();reviewer=(R/F/'reviewer.py').read_text()
 check('rebuilt = mod.review' in consumer and 'New root review does not exactly rebuild' in consumer,'consumer retains whole-chain exact rebuild')
 check('clone(old.collect, trajectory=trajectory)' in reviewer and 'runtime.verify_runtime_events' in reviewer,'collect consumer dispatches original collection and actual runtime reconstruction')
 check('helper.release_global(evidence, registration, directory, release=False)' in reviewer,'full components still require original global gate')
 for base in [R,P]:
  check(not(base/science['output_relative']).exists(),'no collect output yet '+str(base))
  check(not(base/science['invocation_relative']).exists(),'not yet submitted '+str(base))
 runtime.unchanged(rw)
 for path,h in list(READS.items()):check(digest(path)==h,'all evidence unchanged '+path)
 evidence=write('plan_evidence_sha256.json',READS)
 tests=write('plan_checks.json',dict(checks=CHECKS,negative_cases=NEG,positive_checks=len(CHECKS),inherited_input_checks=inp['checks_passed'],no_new_GPU_calls=True))
 components=obj(A/'runtime_readiness_draft.json')['component_reviews']
 report=dict(schema='formal_main_v2',kind='formal_action_runtime_plan_review',status='passed',review_role='independent',reviewed_by='/root/object64_pending_0333_audit',execution_version='formal-downstream-action-v1',created_utc=datetime.now(timezone.utc).isoformat(),suite='libero_10',stage='collect',stage_key=inv['stage_key'],method_ids=['dense'],scientific_plan=refs['scientific_plan.json'],effective_plan=refs['effective_plan.json'],action_execution_contract=refs['execution_contract.json'],plan_sha256=effective['plan_sha256'],runtime_sources=execution['files'],component_reviews=components,production_chain_complete=True,meaning_of_production_chain_complete='Exact canonical inputs, unmodified production planner/wrapper/runtime contract and previously independently audited producer/reviewer/consumer closure are ready for this collect plan. This is CPU pre-execution readiness only, not actual GPU collection completion.',CPU_only=True,actual_collect_GPU_completed=False,actual_P_original_wrapper_passed=True,actual_P_original_collector_prepare_only_passed=True,original_planner_rebuilt_exactly=True,raw_and_canonical_SHA_separately_verified=True,scientific_settings_changed=False,final_evaluation_enabled=False,full_components_authorized=False,old600_reuse_or_rerun_authorized=False,source173_unchanged=True,final_values_read=False,weights_deserialized=False,state_registry_Git_modified=False,new_GPU_calls=0,new_scheduler_queries=0,new_scientific_success_trials=0,source_development_states=100,selected_development_states=10,expected_observations=30,fixed_source_indices=[s['source_state_index'] for s in fixed],failed_or_short_trajectory_replacement=False,environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_control_steps=520,temporal_rule='first, floor((N-1)/2), last real pre-action observations; N>=3; no success filtering or replacement',positive_checks=len(CHECKS),negative_checks=len(NEG),input_review=dict(path=(D/'input_independent_review.json').relative_to(R).as_posix(),sha256='fa878235152fe2930653812c6d2ddf7aabdac02f65aa49bdef478d8a06bb6e47'),fresh_preparation=dict(path=(D/'fresh_prepare_only.json').relative_to(R).as_posix(),sha256='a5089c9ef28878cffc11f159dbb221a71f830a2b5fb340e0ffde67fe55baf410'),evidence=evidence,checks=tests,audit_source=dict(path=Path(__file__).relative_to(R).as_posix(),sha256=digest(__file__)),limitations=['Root must sign genuine readiness with separate root and independent receipts, then pass exact P outer wrapper.verify.','Root must check current controller lease, registry, exact exclusive reservation and global eight-GPU capacity; saved planning snapshot is not live capacity evidence.','This receipt does not authorize another stage, final unsealing or any duplicate collection.','Actual collected observations require subsequent original plus action raw consumer reconstruction and independent review before timing use.','Previously accepted component and v4 GPU evidence is inherited by exact hashes, not rerun or counted as new independent GPU tests.'])
 out=write('independent_readiness.json',report)
 rows=[dict(path=p.relative_to(R).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in sorted(D.iterdir()) if p.is_file() and p.name!='manifest.json']
 manifest=write('manifest.json',dict(schema='formal_main_v2',kind='independent_Long_collect_CPU_readiness_manifest',files=rows,only_private_files_written=True))
 print(json.dumps(dict(status='passed',report=out,manifest=manifest,positive_checks=len(CHECKS),negative_checks=len(NEG))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('plan_audit_failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),passed_check_count=len(CHECKS)));raise
