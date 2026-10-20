"""Object original whole-chain CPU recheck. Reused control pattern only; no Long evidence or conclusion. Old 600 includes one policy_error; not compatibility admission."""
import hashlib,json,time,sys,types,os,traceback
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object_legacy_integration_20261020T2156'
BEGAN=time.perf_counter();CPU=time.process_time()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('no process/network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or set(p.suffixes)&{'.pt','.pth','.bin','.pkl','.pickle','.ckpt','.safetensors','.init','.pruned_init'} or p.name=='init_states_test.json' or (p.name=='panel.json' and 'final' in p.parts):raise RuntimeError('forbidden value path')
  mode,flags=args[1:3]
  write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if write and p.parent!=D:raise RuntimeError('write outside private directory')
def load(rel,h,name):
 p=R/rel;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==h
 m=types.ModuleType(name);m.__file__=str(p);m.__package__='';sys.modules[name]=m;exec(compile(b,str(p),'exec',dont_inherit=True),m.__dict__);return m
sys.dont_write_bytecode=True;sys.addaudithook(guard)
try:
 h=load('scripts/formal_execution_manifests.py','614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89','_object600_oldhelper')
 c=load('scripts/ops/formal_action_deployment_v1/consumer.py','16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034','_object600_consumer')
 ev=h.Evidence(R);ref={'path':'results/formal_main_v2/downstream_reviews/3021844.json','sha256':'004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37'}
 v=c.review_downstream_output(ev,ref,expected_stage='development',suite='libero_object');ev.unchanged()
 result={'kind':'author_original_legacy_consumer_recheck','status':'passed_original_whole_chain','root':ref,'actual_execution_version':v.get('execution_version','formal-downstream-root-v1'),'completed_trials':v['completed_trials'],'cost':v['cost'],'evidence_sha256':ev.files,'new_GPU_seconds':0,'reuse_authorized':False,'old_invocation_ran_new_wrapper':False,'wall_seconds':time.perf_counter()-BEGAN,'CPU_seconds':time.process_time()-CPU}
 with (D/'legacy_root_recheck.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ('evidence_sha256','cost')}))
except BaseException as exc:
 with (D/'legacy_root_recheck_failure.json').open('x') as f:json.dump({'error':str(exc),'traceback':traceback.format_exc(),'wall_seconds':time.perf_counter()-BEGAN,'CPU_seconds':time.process_time()-CPU,'GPU_seconds':0},f,indent=2)
 raise
