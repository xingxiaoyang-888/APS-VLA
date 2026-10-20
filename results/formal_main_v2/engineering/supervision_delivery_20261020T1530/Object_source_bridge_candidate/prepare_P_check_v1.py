"""Private CPU only: original P wrapper and runtime metadata validation, no GPU."""
import os,sys,json,hashlib,importlib.util,copy,time,traceback
from pathlib import Path
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).parent;OUT=D/'runtime_check01'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
READS={};TESTS=[]
BRIDGE_SHA='8785b42fe62dd513f796871875547c894de972516ac9762ad60a89d3df9a7c8e'
MANIFEST='results/formal_main_v2/execution/object256seed23_source_bridge_v1_20261020T1530/libero_object_k256_seed23_development.json'
MANIFEST_SHA='5f2bdcac8752c0cd06ad8dcb67114920b642db1415f6a88e1335d6c9f10fb028'
PRE='scripts/ops/formal_action_deployment_v1/'
PINS={'scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',PRE+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',PRE+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',PRE+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',PRE+'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',PRE+'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',PRE+'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',PRE+'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('CPU preparation forbids subprocess/network/Slurm')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   path=Path(os.fsdecode(name));path=path if path.is_absolute() else Path.cwd()/path
   assert not any('sealed' in x.lower() or x.lower() in ['weights','checkpoints'] for x in path.parts),'Forbidden sealed/checkpoint read'
   assert path.suffix.lower() not in ['.pt','.pth','.bin','.safetensors','.pkl','.pickle','.ckpt','.init','.pruned_init'],'Forbidden weight/value suffix'
   writing=isinstance(mode,str) and any(x in mode for x in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing:assert OUT in path.parents,'Private output only: '+str(path)
sys.addaudithook(guard)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path,pin=None):
 path=Path(path);raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest();assert pin is None or h==pin,(str(path),h,pin)
 assert str(path) not in READS or READS[str(path)]==h,'immutable input changed';READS[str(path)]=h;return raw

def write(name,value):
 path=OUT/name;raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
 with path.open('xb') as f:f.write(raw)
 return {'path':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
def load(path,pin):
 raw=read(path,pin);spec=importlib.util.spec_from_file_location('object23_prepare_'+path.stem,path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);return m

def main():
 OUT.mkdir(exist_ok=False);t0=time.perf_counter()
 bridge=load(D/'bridge_v2.py',BRIDGE_SHA)
 policy=bridge.policy();inventory=json.loads(read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'))
 for root in (R,S):
  for rel,h in inventory['files'].items():read(root/rel,h)
 for root in (R,P):
  read(root/MANIFEST,MANIFEST_SHA);read(root/policy['pair']['path'],policy['pair']['sha256'])
 # Atomic read of current state, explicitly an author's snapshot, not a root lock/CAS authorization.
 state_path=R/'results/experiment_supervisor/state.json';raw=state_path.read_bytes();state=json.loads(raw)
 state_ref=write('author_state_snapshot.json',raw);write('author_snapshot_label.json',{'kind':'author_read_only_atomic_file_snapshot','writer_lock_held':False,'root_CAS_authorization':False,'state':state_ref,'root_initial_observation':{'path':'results/formal_main_v2/preflight/heartbeat_20261020T2330/initial_observation.json','sha256':'b2482a34598e5ccf6e33f046000dc26f6385db7fbdb22664b5dcb6f906914bf1'}})
 read(R/'results/formal_main_v2/preflight/heartbeat_20261020T2330/initial_observation.json','b2482a34598e5ccf6e33f046000dc26f6385db7fbdb22664b5dcb6f906914bf1')
 factory_base=bridge.load(SimpleEvidence(R),policy['references']['original_factory'])
 evidence=factory_base.Evidence(R);factory,planner=bridge.control_modules(evidence)
 args=dict(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=MANIFEST,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
 science=planner.plan(SimpleNamespace(**args),copy.deepcopy(state),project=R,helper=factory);write('plan_arguments.json',args);science_ref=write('scientific_plan.json',science);inv=science['invocation']
 assert inv['method_ids']==policy['method_ids'] and inv['prior_job_ids']==[] and not inv['resume']
 for rel in [science['output_relative'],science['invocation_relative']]:assert not (R/rel).exists() and not (P/rel).exists(),'prior output/invocation exists'
 old=load(P/'scripts/server/run_formal_downstream.py',PINS['scripts/server/run_formal_downstream.py']);verified=old.verify(inv);assert verified.mode=='evaluate'
 TESTS.append({'name':'exact_original_P_wrapper_metadata_verify','passed':True,'entrypoint':str(P/'scripts/server/run_formal_downstream.py'),'GPU_runtime_executed':False})
 runtime=load(R/(PRE+'runtime_scope.py'),PINS[PRE+'runtime_scope.py']);contract=runtime.make_contract(project_root=R,source_root=S,suite='libero_object',stage='development')
 assert contract==runtime.make_contract(project_root=P,source_root=S,suite='libero_object',stage='development')
 for root in (R,P):
  for path,pin in runtime.validate_contract(contract,project_root=root,source_root=S).items():read(path,pin)
 assets=runtime.expected_asset_identities(project_root=P,source_root=S,contract=contract,asset_contract=inv['downstream_asset_compatibility']);write('runtime_metadata_identities.json',assets);write('runtime_contract.json',contract)
 TESTS.append({'name':'actual_P_runtime_scope_metadata','passed':True,'model_or_environment_loaded':False})
 c=load(R/(PRE+'contract.py'),PINS[PRE+'contract.py']);files={rel:PINS[rel] for rel in c.EXPECTED_NEW_FILES};files[c.ACTION_ADAPTER]=c.ACTION_SHA
 action=dict(schema=c.SCHEMA,kind='formal_action_execution_contract',version=c.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,final_evaluation_enabled=False,files=files,runtime_contract=contract,GPU_acceptance=c.GPU_REFS,source_inventory={'path':c.INVENTORY,'sha256':c.INVENTORY_SHA},transition=None)
 action_ref=write('execution_contract.json',action);effective=c.effective_plan(science,scientific_plan_ref=science_ref,execution_contract_ref=action_ref,execution_contract=action);write('effective_plan_private_preview.json',effective)
 wrapper=load(P/(PRE+'wrapper.py'),PINS[PRE+'wrapper.py'])
 try:wrapper.verify(effective['invocation'],project=P)
 except (ValueError,RuntimeError) as e:
  assert 'Exact path/SHA reference required' in str(e),str(e)
  TESTS.append({'name':'missing_actual_root_readiness_fails_closed','passed':True,'error':str(e)})
 else:raise ValueError('new P action wrapper incorrectly admitted missing readiness')
 # Every original science argument, method panel, checkpoint and preprocessing remains frozen.
 assert planner.plan(SimpleNamespace(**args),copy.deepcopy(state),project=R,helper=factory)==science
 TESTS.append({'name':'versioned_planner_rebuild_same_snapshot_identical','passed':True})
 for path,pin in inv['root_evidence_sha256'].items():read(R/path,pin)
 for path,pin in READS.items():assert sha(path)==pin,'input changed'
 write('read_evidence_sha256.json',READS)
 report={'schema':'formal_main_v2','status':'CPU_P_metadata_passed_not_GPU_or_root_admitted','checks':TESTS,'source173_R_and_S_unchanged':True,'methods':policy['method_ids'],'planned_development_trials':200,'unique_initial_states':100,'state_snapshot':state_ref,'old_P_wrapper_verify':True,'new_P_action_wrapper_root_readiness':False,'actual_GPU_runtime':False,'root_release':False,'Slurm_submissions':0,'state_Git_writes':False,'weights_or_sealed_states_read':False,'GPU_seconds_added':0,'CPU_wall_seconds':time.perf_counter()-t0,'remaining':['Independent source bridge and control binding review','Canonical root bridge admission/publication','Versioned gateway exact re-plan and terminal consumer same explicit bridge','Actual final checkpoint byte identities checked by original runtime','True per-plan root/independent readiness and locked fresh duplicate/capacity checks'],'scientific_plan':science_ref}
 write('P_check_only.json',report);print(json.dumps({k:report[k] for k in ['status','old_P_wrapper_verify','new_P_action_wrapper_root_readiness','actual_GPU_runtime','Slurm_submissions']}))
class SimpleEvidence:
 def __init__(self,root):self.root=self.project=root
 def path(self,p):p=Path(p);return p if p.is_absolute() else self.root/p
 def watch(self,p):return hashlib.sha256(read(self.path(p))).hexdigest()
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if OUT.exists():write('failure.json',{'status':'failed','error':str(e),'traceback':traceback.format_exc(),'GPU_runs':0,'Slurm_submissions':0})
  raise
