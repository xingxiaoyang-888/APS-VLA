"""Exact existing Object collect production plan, unapproved drafts, CPU-only evidence."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e';INPUT=R/'.local/spatial_object_collect_20261020T1825/Object';D=INPUT/'science_only'
DEST='results/formal_main_v2/execution/object_collect_action_v1_20261020T1825';PREF='scripts/ops/formal_action_deployment_v1/'
MANIFEST=DEST+'/dense_development.json';MANIFEST_SHA='45197f0dc711ebc09a685e25a8edc251c25b881eb1ad477ef8dbbe89a9aed13d'
INVENTORY='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
PIN={
'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',
'scripts/ops/formal_evaluation_adapter.py':'b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd',
'scripts/profile_formal.py':'4b8a7ac0b8be904f8f6b66d9fe7f6c3f7425056e013db903ac6b480191e2ebf6',
'src/cti_vla/evaluation/formal_profiling.py':'56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80',
PREF+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
PREF+'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',
PREF+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',
PREF+'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
PREF+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
PREF+'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
PREF+'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
READS={};WRITTEN={};TESTS=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No process/network/Slurm in candidate preparation')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('No sealed/weight payload access: '+str(p))
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
   if writing and D not in p.parents:raise RuntimeError('No writes outside unique private directory: '+str(p))
sys.addaudithook(guard)
def require(v,m):
 if not v:raise ValueError(m)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(value,pin=None):
 p=Path(value);p=p if p.is_absolute() else R/p
 require(p.resolve()==p and (R in p.parents or P in p.parents),'canonical R/P file required')
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();require(pin is None or pin==h,'pin changed: '+str(p))
 require(str(p) not in READS or READS[str(p)]==h,'evidence drift');READS[str(p)]=h;return raw
def js(value,pin=None):return json.loads(read(value,pin))
def write(name,value):
 p=D/name;require(D in p.parents,'private output only');raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 row=dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));WRITTEN[name]=row;return row
def cref(name):return dict(path=DEST+'/'+name,sha256=WRITTEN[name]['sha256'])
def load(rel):
 raw=read(rel,PIN[rel]);p=R/rel;name='collect1825_object_'+p.stem
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(raw,str(p),'exec'),m.__dict__);return m
def reject(name,fn,fragment):
 try:fn()
 except (ValueError,RuntimeError) as exc:
  require(fragment in str(exc),'wrong negative-test rejection '+name+': '+str(exc));TESTS.append(dict(name=name,status='rejected_as_required',error_type=type(exc).__name__,error=str(exc),synthetic_fault_input=True,actual_receipt_created=False));return
 raise ValueError('Unsafe accepted candidate fault: '+name)
def check_sources():
 inventory=js(INVENTORY,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 require(len(inventory['files'])==173,'frozen inventory count')
 for root in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):
  for rel,h in inventory['files'].items():read(root/rel,h)
 for rel,h in PIN.items():
  read(rel,h)
  if rel.startswith(PREF):read(P/rel,h)
 return inventory

def main():
 started=datetime.now(timezone.utc).isoformat();inventory=check_sources()
 input_evidence=js(INPUT/'dense_input_evidence.json');read(MANIFEST,MANIFEST_SHA);read(P/MANIFEST,MANIFEST_SHA)
 publication=dict(kind='actual_published_input_R_P_exact_byte_verification',path=MANIFEST,sha256=MANIFEST_SHA)
 h=load('scripts/formal_execution_manifests.py');planner=load('scripts/ops/formal_downstream_supervisor.py')
 c=load(PREF+'contract.py');runtime=load(PREF+'runtime_scope.py');gw=load(PREF+'gateway.py')
 original_wrapper=load('scripts/server/run_formal_downstream.py');outer_wrapper=load(PREF+'wrapper.py');legacy=load('scripts/ops/formal_evaluation_adapter.py')
 state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw);write('state_at_planning.json',state_raw)
 state_before=copy.deepcopy(state)
 require(state.get('pending_submission') is None,'pending submission must resolve before plan')
 registered=[j for j in state['registered_jobs'] if j.get('suite')=='libero_object' and (j.get('mode') in ('collect','full','components') or j.get('stage') in ('collect','full','components'))]
 require(not registered,'registered formal collect/profile already exists; no duplicate')
 arguments=dict(stage='collect',source_inventory=INVENTORY,execution_manifest=MANIFEST,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
 write('plan_arguments.json',arguments)
 science=planner.plan(SimpleNamespace(**arguments),copy.deepcopy(state),project=R,helper=h)
 require(state==state_before,'read-only actual registry mutated')
 inv=science['invocation'];require(inv['stage']=='collect' and inv['method_ids']==['dense'] and inv['resume'] is False and inv['prior_job_ids']==[],'unexpected scope/history')
 require(science['resources']==gw.RESOURCES,'original one-L40 allocation changed')
 require(not(R/science['output_relative']).exists() and not(P/science['output_relative']).exists(),'existing collect output')
 require(not(R/science['invocation_relative']).exists() and not(P/science['invocation_relative']).exists(),'existing invocation')
 require('--global-freeze' not in inv['argv'] and '--sealed-final' not in inv['argv'] and '--uncontended-gpu' in inv['argv'],'collect/final/timing flags differ')
 write('scientific_plan.json',science);science_ref=cref('scientific_plan.json')
 args=original_wrapper.verify(inv);require(args.mode=='collect' and args.global_freeze is None and args.panel is None,'actual original P wrapper collect paths')
 write('science_only_review.json',dict(schema='formal_main_v2',kind='original_scientific_collect_plan_and_actual_P_wrapper_CPU_verification',status='passed_science_only_pending_fresh_original_prepare_only',manifest_publication=publication,scientific_plan=cref('scientific_plan.json'),source_state_sha256=hashlib.sha256(state_raw).hexdigest(),original_P_wrapper_verified=True,submission_authorized=False,new_GPU_seconds=0))
 print(json.dumps(dict(status='passed_science_only',scientific_plan=WRITTEN['scientific_plan.json'],run_root=inv['run_root']),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  write('science_preparation_failure_v1.json',dict(error=str(exc),error_type=type(exc).__name__,traceback=traceback.format_exc(),partial_outputs=WRITTEN));raise
