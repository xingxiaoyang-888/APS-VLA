"""Readonly actual P publication check; does not test or grant readiness/capacity."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/action_actual_plan_0943'
readmap={}
def h(raw):return hashlib.sha256(raw).hexdigest()
def read(path,pin=None):
 p=Path(path);raw=p.read_bytes();got=h(raw);assert pin is None or got==pin,(str(p),got,pin)
 assert str(p) not in readmap or readmap[str(p)]==got;readmap[str(p)]=got;return raw
def js(path,pin=None):return json.loads(read(path,pin))
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No scheduler/process/network')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(p));p=p if p.is_absolute() else Path.cwd()/p
   assert not any('sealed' in x.lower() for x in p.parts)
   assert not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.pruned_init','.init'}
   write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if write:assert D in p.parents,str(p)
sys.addaudithook(guard);read(__file__)
sources={}
for name,pin in [('gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'),('runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53'),('contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19')]:
 path=R/'scripts/ops/formal_action_deployment_v1'/name;raw=read(path,pin)
 spec=importlib.util.spec_from_file_location('postpub_'+name[:-3],path);mod=importlib.util.module_from_spec(spec);exec(compile(raw,str(path),'exec'),mod.__dict__);sources[name]=mod
publication_ref={'path':'results/formal_main_v2/execution/action_spatial_resume_0943/runtime_publication.json','sha256':'f86add8e6dc7fbbc2c2c8458ba97a70b42f71701c95009d4be324eee7badc8b0'}
publication=js(R/publication_ref['path'],publication_ref['sha256'])
before=js(D/'runtime_publication_readonly_inventory.json','e7945da1b874690b49b3abec48733d639a9cd5ed16b65da06baeb45f8a3cb472')
current=[]
for row in before['files']:
 read(R/row['path'],row['sha256']);raw=read(P/row['path'],row['sha256'])
 current.append({'path':row['path'],'sha256':row['sha256'],'bytes':len(raw),'P_status':'already_exact'})
plan=js(D/'effective_plan.json','a56ff9e12b6ddad13e3e6ee4b78f5181ffa3ead3f8df8c620370e00c95d2eb3b')
inner=js(D/'scientific_plan.json','43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94')
action=js(D/'execution_contract.json','b63689d9f3fb3dece0c2fee8c219ad94cd8e1e694962afdb2cd66a40bf551bc0')
ready=js(D/'runtime_readiness_draft.json','3dbf2a4eac17d1f33766a2d8cbc5b89280bf223de8ec52293214e44afd805738')
rt_watch=sources['runtime_scope.py'].validate_contract(action['runtime_contract'],project_root=P,source_root=S)
for n,pin in rt_watch.items():read(n,pin)
prefix=sources['contract.py'].resume_prefix_inputs(inner['invocation'])
bundle={'plan':plan,'invocation':plan['invocation'],'prefix':prefix,'readiness_files':ready['runtime_publication_files']}
preflight=sources['gateway.py'].NativeIO(R).preflight(bundle)
for path,row in preflight['checked_files'].items():read(path,row['sha256'])
for path,pin in list(readmap.items()):assert h(Path(path).read_bytes())==pin
result=dict(schema='formal_main_v2',kind='actual_runtime_post_publication_readonly_check',status='passed_input_IO_only_not_readiness_or_capacity',created_utc=datetime.now(timezone.utc).isoformat(),publication=publication_ref,current_runtime_files=current,native_input_preflight=preflight,runtime_contract_P_validation=True,root_readiness_issued=False,capacity_checked=False,submission_called=False,production_state_modified=False,files_published_by_this_check=0,scientific_inputs_synthetic=False,read_evidence_sha256=readmap)
raw=(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
with (D/'runtime_post_publication_readonly_check.json').open('xb') as f:f.write(raw)
print(json.dumps({'sha256':h(raw),'runtime_files':len(current),'checked_runtime_inputs':len(preflight['checked_files']),'missing_exact_planned_publications':preflight['missing_publications'],'read_evidence_count':len(readmap)},ensure_ascii=False))
