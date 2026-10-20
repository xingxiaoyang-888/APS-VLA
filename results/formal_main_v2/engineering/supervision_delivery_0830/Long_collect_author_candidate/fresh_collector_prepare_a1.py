"""Fresh-process CPU call of original frozen collect preparation, no policy load."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/long_collection_prepare_0830'
sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'src'))
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No subprocess/network in fresh CPU preparation')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('No payload read')
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writing and D not in p.parents:raise RuntimeError('private CPU report only')
sys.addaudithook(guard)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,v):
 with (D/name).open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
def load(path,pin,name):
 assert digest(path)==pin
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
try:
 assert not any(n=='cti_vla' or n.startswith('cti_vla.') for n in sys.modules)
 science_path=D/'scientific_plan.json';assert digest(science_path)=='1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0'
 science=json.loads(science_path.read_bytes());inv=science['invocation'];assert inv['stage']=='collect' and inv['method_ids']==['dense'] and not inv['resume']
 wrapper=load(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24','fresh_original_wrapper')
 args=wrapper.verify(inv);args.prepare_only=True
 pin='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd';legacy=load(P/'scripts/ops/formal_evaluation_adapter.py',pin,'fresh_original_adapter')
 result=legacy.run(args,mode='collect',source_root=S,source_inventory=P/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',adapter_sha256=pin,resume=False)
 origins={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='cti_vla' or n.startswith('cti_vla.')) and getattr(m,'__file__',None)}
 assert origins and all(S/'src' in Path(p).parents for p in origins.values())
 assert result['status']=='prepared_only' and result['command']=='collect' and result['methods']==['dense'] and result['observations']==30 and result['gpu_calls']==0 and result['weights_validated'] is False and result['test_opened'] is False
 assert not(R/science['output_relative']).exists() and not(P/science['output_relative']).exists()
 write('fresh_collector_prepare_only.json',dict(schema='formal_main_v2',kind='actual_original_fresh_process_collect_CPU_preparation',status='passed_CPU_prepare_only',result=result,source_modules=origins,scientific_plan=dict(path=science_path.relative_to(R).as_posix(),sha256=digest(science_path)),actual_output_created=False,weights_deserialized=False,production_adapter_changed=False,source_import_guard_preserved=True))
 print(json.dumps(dict(status='passed_fresh_original_collect_prepare_only',path='.local/long_collection_prepare_0830/fresh_collector_prepare_only.json',sha256=digest(D/'fresh_collector_prepare_only.json'),modules=len(origins),observations=30)))
except BaseException as exc:
 write('fresh_collector_prepare_failure_a1.json',dict(error=str(exc),error_type=type(exc).__name__,traceback=traceback.format_exc()));raise
