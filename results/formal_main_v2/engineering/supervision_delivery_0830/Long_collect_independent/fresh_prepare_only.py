"""Independent fresh-process original collect preparation; server private evidence only."""
from pathlib import Path
import hashlib, importlib.util, json, os, sys, traceback
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/long_collect_independent_0830'
C='results/formal_main_v2/execution/long_collect_action_v1_0830'
sys.dont_write_bytecode=True
sys.path.insert(0,str(S/'src'))
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('Independent CPU preparation cannot spawn or connect')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('Forbidden payload read')
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writing and D not in p.parents:raise RuntimeError('Only independent private outputs may be written')
sys.addaudithook(guard)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):
 raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with (D/name).open('xb') as f:f.write(raw)
 return dict(path=(D/name).relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(path,pin,name):
 assert digest(path)==pin, str(path)
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
try:
 assert not any(n=='cti_vla' or n.startswith('cti_vla.') for n in sys.modules)
 sp=R/C/'scientific_plan.json';pin='1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0'
 assert digest(sp)==digest(P/C/'scientific_plan.json')==pin
 plan=json.loads(sp.read_bytes());inv=plan['invocation']
 assert inv['stage']=='collect' and inv['method_ids']==['dense'] and inv['resume'] is False
 original=load(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24','independent_actual_original_wrapper')
 args=original.verify(inv);args.prepare_only=True
 adapterpin='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
 adapter=load(P/'scripts/ops/formal_evaluation_adapter.py',adapterpin,'independent_actual_original_adapter')
 result=adapter.run(args,mode='collect',source_root=S,source_inventory=P/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',adapter_sha256=adapterpin,resume=False)
 origins={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='cti_vla' or n.startswith('cti_vla.')) and getattr(m,'__file__',None)}
 assert origins and all(S/'src' in Path(p).parents for p in origins.values())
 assert result['status']=='prepared_only' and result['command']=='collect' and result['methods']==['dense'] and result['observations']==30 and result['gpu_calls']==0 and result['weights_validated'] is False and result['test_opened'] is False
 assert not(R/plan['output_relative']).exists() and not(P/plan['output_relative']).exists()
 out=write('fresh_prepare_only.json',dict(schema='formal_main_v2',kind='independent_actual_original_collect_CPU_preparation',status='passed',review_role='independent',reviewer='/root/object64_pending_0333_audit',utc=datetime.now(timezone.utc).isoformat(),scientific_plan=dict(path=C+'/scientific_plan.json',sha256=pin),original_P_wrapper_verified=True,result=result,source_modules=origins,new_GPU_calls=0,weights_deserialized=False,final_values_read=False,production_code_changed=False,actual_output_created=False))
 print(json.dumps(out))
except BaseException as e:
 write('fresh_prepare_only_failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()));raise
