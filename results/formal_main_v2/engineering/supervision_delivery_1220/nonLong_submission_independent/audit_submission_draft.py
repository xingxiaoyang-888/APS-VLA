"""One read-only submission identity/capacity observation; no scientific result audit."""
import copy,fcntl,hashlib,importlib.util,json,os,re,subprocess,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/nonLong_submission_independent_1220';B='results/formal_main_v2/preflight/heartbeat_20261020T2020/';PR='scripts/ops/formal_action_deployment_v1/'
READS={};CHECKS=[];sys.dont_write_bytecode=True;os.chdir(R)
def need(v,msg):
 if not v:raise ValueError(msg)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(name,pin=None):
 p=Path(name);p=p if p.is_absolute() else R/p
 need(p.resolve()==p and (R in p.parents or P in p.parents),'canonical server evidence required')
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();need(pin is None or h==pin,'SHA mismatch '+str(p));need(str(p) not in READS or READS[str(p)]==h,'evidence drift');READS[str(p)]=h;return b
def js(name,pin=None):return json.loads(read(name,pin))
def getref(r):return js(r['path'],r['sha256'])
def ref(p):p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size}
def write(name,value):
 p=D/name;b=value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return ref(p)
def load(name,pin):
 p=R/name;b=read(p,pin);spec=importlib.util.spec_from_file_location('submit_audit_'+p.stem,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
def guard(event,args):
 if event in ('os.system','socket.connect'):raise RuntimeError('No shell/network')
 if event=='subprocess.Popen':
  executable,argv,cwd,env=args;need(isinstance(argv,list) and argv[0] in ('sacct','squeue','scontrol'),'Only registered read-only Slurm calls')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
   need(not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) and p.suffix.lower() not in ('.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init'),'no weight/final reads')
   writing=isinstance(mode,str) and any(c in mode for c in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing:need(D in p.parents,'private outputs only')
sys.addaudithook(guard)
def fields(answer):
 need(answer['returncode']==0,'scontrol failed');out={}
 for key in ('JobId','JobName','JobState','Comment','NodeList','WorkDir','Requeue','Restarts','Account','Partition'):
  found=re.findall(r'(?:^|\s)'+key+r'=([^\s]+)',answer['stdout']);need(len(found)==1,'scontrol identity '+key);out[key]=found[0]
 return out

ORIGINAL_AUDIT={'path':'.local/nonLong_submission_independent_1032/audit_submission_v1.py','sha256':'a9d4612a65cad1b044730120067204b4daf30919510d33ecc3f59f3bd3880f86'}
EXPECTED_GROUPS=[{'suite':'libero_spatial','seed':41,'methods':['A128_seed41','B128_seed41'],'expected_trials':200},{'suite':'libero_object','seed':41,'methods':['A128_seed41','B128_seed41'],'expected_trials':200},{'suite':'libero_goal','seed':23,'methods':['A128_seed23','B128_seed23'],'expected_trials':200}]
# Placeholder only: root supplies immutable actual submissions/post-dispatch evidence.
# No old job IDs, outcomes, runtime approvals, or Slurm queries may be inferred.
ROOT_INPUTS=None
REQUIRED_EVIDENCE=['all_three_actual_job_ids','original_ACK_and_exact_request_token','original_preflight_and_prepared_invocation','genuine_distinct_plan_independent_and_post_readiness','root_post_dispatch_state_snapshot','root_registered_raw_sacct_squeue_and_exact_scontrol','normal_commit_or_pending_reconciliation_per_actual_outcome']
def main():
 need(ROOT_INPUTS is not None,'Draft only: actual job IDs and immutable root post-dispatch evidence not yet supplied')
 raise ValueError('Draft locked: exact input adaptation and fresh entrypoint SHA required before any audit execution')
if __name__=='__main__':main()
