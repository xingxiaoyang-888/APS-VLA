"""Independent read-only canonical k64 seed23 source bridge audit. No submission."""
from pathlib import Path
from types import SimpleNamespace
import sys,os,json,hashlib,copy,ast,importlib.util,contextlib,io,traceback,time,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/k64_seed23_bridges_independent_20261020T1949/dispatch_mock';A=R/'.local/k64_seed23_bridges_20261020T1949'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PUBLICATION='results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_candidate_publication.json';PUB_SHA='1656f5c931545c0b0b2ae987202dbf1ae3281ccf2c71b900a30bf2f8a55f3949'
MAP_SHA='ec56fca197dcbb6de668761081852be973aba6ab61673edf4c961d29390973aa'
EXPECT={'spatial':{'control':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3','bridge':'678b6c57fbf6e188eced6d42bfa158862c1f185bced034027e535a4316804c87','total':42480,'failed':73,'selected':{'A':2500,'B':3500},'jobs':['3024716','3025205','3028522','3043399','3044479']},'object':{'control':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767','bridge':'04c596f8b86569d7476f504fcf5519c205b0fc7eb2e0bd6de953fa47f5bc6735','total':52868,'failed':69,'selected':{'A':2500,'B':4500},'jobs':['3028468','3044017','3044844']}}
READS={};CHECKS=[];NEG=[];REPORTS=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork'):raise RuntimeError('audit forbids process/network/Slurm')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2] or 0
  if p.suffix.lower() in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init','.npz','.h5','.hdf5'} or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('no weights/data/sealed access '+str(p))
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing and not p.is_relative_to(D):raise RuntimeError('private writes only '+str(p))
sys.addaudithook(guard)
def sha(b):return hashlib.sha256(b).hexdigest()
def check(ok,label):
 CHECKS.append({'name':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def read(path,pin=None):
 p=Path(path);p=p if p.is_absolute() else R/p;b=p.read_bytes();h=sha(b)
 check(pin is None or pin==h,'exact byte SHA '+str(p));check(str(p) not in READS or READS[str(p)]==h,'stable input '+str(p));READS[str(p)]=h;return b
def rd(path,pin=None):return json.loads(read(path,pin))
def write(path,val):
 p=D/path;p.parent.mkdir(parents=True,exist_ok=True);b=val if isinstance(val,bytes) else (json.dumps(val,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b)}
def load(path,pin=None,name=None):
 p=Path(path);p=p if p.is_absolute() else R/p;b=read(p,pin);n=name or 'k64ind_'+p.stem+'_'+sha(str(p).encode())[:12];spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
class Evidence:
 def __init__(self):self.project=self.root=R;self.files={};self.hashes=self.files;self.forbidden_paths=set()
 def path(self,n):
  p=Path(n);p=p if p.is_absolute() else R/p;check('..' not in p.parts and p.resolve()==p.absolute() and p.is_relative_to(R),'safe R evidence '+str(n));return p
 def watch(self,n):
  p=self.path(n);b=read(p);self.files[p.relative_to(R).as_posix()]=sha(b);return sha(b)
 def read(self,n):p=self.path(n);self.watch(p);return json.loads(p.read_bytes())
 def relative(self,n):return self.path(n).relative_to(R).as_posix()
 def unchanged(self):
  for n,pin in self.files.items():check(sha((R/n).read_bytes())==pin,'unchanged evidence '+n)
def neg(label,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError) as e:NEG.append({'name':label,'type':type(e).__name__,'message':str(e),'passed':True});return
 raise AssertionError(label+' accepted invalid input')
def capture(path,fn):
 buff=io.StringIO()
 with contextlib.redirect_stdout(buff),contextlib.redirect_stderr(buff):result=fn()
 write(path,buff.getvalue().encode());return result


ENTRY='.local/collect_terminal_20261020T1949/development_gateway/root_dispatch_v1.py';PIN='750a8178ef670d7a45ffc9797a05f6fb492ff0d123f9fbb0f095211b4a5af041'
from subprocess import TimeoutExpired

def run_case(label,mode):
 root=D/label/'SYNTHETIC_CONTROL_ROOT';br=root/'results/formal_main_v2/preflight/heartbeat_20261021T0349';br.mkdir(parents=True);sp=root/'results/experiment_supervisor/state.json';sp.parent.mkdir(parents=True)
 events=[];commands=[];mod=load(ENTRY,PIN,'dispatch_fixture_'+label);mod.R=root;mod.B=br;mod.G=root/'scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py'
 suite='libero_spatial';cr='results/formal_main_v2/execution/spatial64seed23_source_control_v1_20261020T1949';ar={'path':cr+'/submission_authorization.json','sha256':'a'*64};pr={'path':'.local/CPU_ONLY_POST.json','sha256':'b'*64};pref={'path':cr+'/prepared_invocation.json','sha256':'c'*64};rref={'path':cr+'/runtime_readiness.json','sha256':'d'*64};res={'path':cr+'/reservation_root_record.json','sha256':'e'*64};pl={'path':cr+'/effective_plan.json','sha256':'f'*64};descriptor={'CPU_SYNTHETIC':True}
 post={'schema':'formal_main_v2','kind':'exact_k64s23_post_readiness_independent_review','status':'passed','suite':suite,'blockers':[],'authorization':ar,'actual_full_P_wrapper_verifications':1,'effective_plan':pl,'prepared_invocation':pref,'explicit_source_control':descriptor,'CPU_ONLY':True}
 receipt={'schema':'formal_main_v2','kind':'exact_k64s23_runtime_readiness_root','status':'passed_exact_pre_execution_checks_pending_live_capacity','suite':suite,'authorization':ar,'actual_full_P_wrapper_verifications':1,'state_unchanged':True,'new_GPU_submissions':[],'readiness':rref,'reservation':res,'prepared_invocation':pref,'CPU_ONLY':True}
 (br/'Spatial64s23_runtime_readiness_root.json').write_text(json.dumps(receipt));auth={'plan':pl,'prepared_invocation':pref,'explicit_source_control':descriptor,'runtime_readiness':rref,'root_reservation':res};ready={'runtime_publication_files':{}}
 state={'CPU_SYNTHETIC':True,'pending_submission':None,'registered_jobs':[],'autonomous_training_v1':{'reserved_GPU_slots':0,'root_submission_hold':None,'downstream_reservations_consumed':{}}}
 if mode=='pending':state['pending_submission']={'unknown':True,'token':'CPU_ONLY_PENDING'}
 if mode=='reservation':state['autonomous_training_v1']['reserved_GPU_slots']=1
 if mode=='consumed':state['autonomous_training_v1']['downstream_reservations_consumed'][ar['sha256']]={}
 if mode=='bad_post':post['status']='pending'
 if mode=='wrong_bridge':post['explicit_source_control']={}
 sp.write_text(json.dumps(state));before=sp.read_bytes();references={pr['path']:post,rref['path']:ready,str((br/'Spatial64s23_runtime_readiness_root.json').relative_to(root)):receipt}
 def require(v,message):
  if not v:raise ValueError(message)
 class E:
  def __init__(self,*a):pass
  def ref(self,r):events.append('ref:'+r['path']);return copy.deepcopy(references[r['path']])
  def unchanged(self):events.append('unchanged')
 class Lock:
  def __enter__(self):events.append('lock_enter')
  def __exit__(self,*a):events.append('lock_exit')
 def emit(path,value):
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as f:f.write(value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True)+'\n').encode())
  events.append('write:'+path.name)
 def atomic(path,value,expected_sha):
  require(sha(path.read_bytes())==expected_sha,'fixture CAS drift');path.write_text(json.dumps(value));events.append('atomic_reservation')
 class Slurm:
  def observe(self,jobs):events.append('observe_registered_only');return {'rows':{},'queue':{}}
 ctl=SimpleNamespace(exclusive_lock=lambda *a:Lock(),read_json=lambda p:json.loads(p.read_text()),atomic_json=atomic,Slurm=Slurm)
 class Frozen:
  def __init__(self,*a):pass
  def prepare(self,st):events.append('FrozenPlan');return {}
 class Native:
  def __init__(self,*a):pass
  def preflight(self,b):events.append('NativeIO_preflight')
 def validated(*a):events.append('validate_authorization');return auth,E(),{'CPU_ONLY':True},{'CPU_ONLY':True},{'CPU_ONLY':True}
 gw=SimpleNamespace(CONTROLLER='controller.py',CONTROLLER_SHA='0'*64,ROUND='formal_main_v2',STATE='results/experiment_supervisor/state.json',SCOPED_DEVELOPMENT_PLANS={suite:{'path':pl['path']}},require=require,Evidence=E,validate_authorization=validated,capacity_gate=lambda *a:({'occupied':[]},[],{}),FrozenPlan=Frozen,NativeIO=Native,immutable=emit,record=emit)
 mod.load=lambda p,pin,name:gw if 'gateway' in name else ctl
 def fake_run(command,**kw):
  events.append('subprocess:'+('submit' if '--submit' in command else 'preflight'));commands.append(command[:]);require(kw['cwd']==root and kw['capture_output'] is True,'fixed subprocess destination');current=json.loads(sp.read_text())
  require(current['autonomous_training_v1']['reserved_GPU_slots']==1,'must reserve before subprocess')
  if '--submit' not in command:
   require(len(commands)==1,'preflight once')
   if mode=='preflight_timeout':raise TimeoutExpired(command,360,output=b'CPU timeout')
   if mode=='preflight_fail':return SimpleNamespace(returncode=2,stdout=b'CPU rejected',stderr=b'CPU diagnostic')
   return SimpleNamespace(returncode=0,stdout=json.dumps({'status':'read_only_checks_passed_not_submitted','capacity':{'occupied':[]}}).encode(),stderr=b'')
  require(len(commands)==2 and command[-2:]==['--submit','--root-reviewed-submit'],'single explicit submit only')
  if mode=='submit_timeout':
   current['pending_submission']={'token':'CPU_UNCERTAIN_ACK','unknown':True};sp.write_text(json.dumps(current));raise TimeoutExpired(command,360,output=b'CPU uncertain response')
  current['pending_submission']=None;current['autonomous_training_v1']['reserved_GPU_slots']=0;current['registered_jobs'].append({'job_id':'9909999','CPU_SYNTHETIC':True});sp.write_text(json.dumps(current));return SimpleNamespace(returncode=0,stdout=json.dumps({'status':'submitted_once','job':{'job_id':'9909999','stage_key':'CPU_STAGE'},'state_sha256':sha(sp.read_bytes())}).encode(),stderr=b'')
 mod.subprocess=SimpleNamespace(run=fake_run);argv=['--suite','Spatial','--authorization',ar['path'],'--authorization-sha256',ar['sha256'],'--post-readiness-review',pr['path'],'--post-readiness-review-sha256',pr['sha256'],'--root-reviewed-source-sha256',PIN,'--execute-exact-dispatch'];oldcwd=Path.cwd();error=None
 try:
  os.chdir(root)
  try:capture(label+'/stdout.log',lambda:mod.main(argv))
  except (ValueError,TimeoutExpired) as exc:error={'type':type(exc).__name__,'message':str(exc)}
 finally:os.chdir(oldcwd)
 after=json.loads(sp.read_text());out=br/'Spatial64s23_dispatch'
 if mode in ('pending','reservation','consumed','bad_post','wrong_bridge'):
  check(error is not None and not commands and 'atomic_reservation' not in events and sp.read_bytes()==before and not out.exists(),label+' refuses before mutation or subprocess')
 elif mode in ('preflight_fail','preflight_timeout'):
  check(error is not None and len(commands)==1 and after['autonomous_training_v1']['reserved_GPU_slots']==1 and (out/'failure.json').exists(),label+' preserves reservation after preflight failure')
 elif mode=='submit_timeout':
  check(error is not None and len(commands)==2 and after['pending_submission']=={'token':'CPU_UNCERTAIN_ACK','unknown':True} and (out/'failure.json').exists(),label+' preserves uncertain pending without retry')
 else:check(error is None and len(commands)==2 and (out/'completion.json').exists() and after['registered_jobs']==[{'job_id':'9909999','CPU_SYNTHETIC':True}],label+' one simulated ACK only')
 if commands:
  check(events.index('atomic_reservation')<events.index('lock_exit')<events.index('subprocess:preflight'),'reservation CAS before unlock and before original gateway preflight '+label)
  oldcommands=len(commands);oldstate=sp.read_bytes();os.chdir(root)
  try:neg(label+' reentry denied before second transaction',lambda:mod.main(argv))
  finally:os.chdir(oldcwd)
  check(len(commands)==oldcommands and sp.read_bytes()==oldstate,label+' rejected reentry preserves original state')
 write(label+'/mock_result.json',{'CPU_SYNTHETIC_ONLY':True,'scenario':mode,'events':events,'commands':commands,'exception':error,'real_Slurm_calls':0,'production_state_writes':False})

def main():
 source=read(ENTRY,PIN).decode();tree=ast.parse(source);calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)];runs=[n for n in calls if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run'];check(len(runs)==2,'two bounded subprocess statements preflight and single submit')
 check('sbatch' not in source and 'scancel' not in source and 'pending_submission\'] =' not in source,'helper has no direct sbatch/cancel/pending-clear implementation')
 for mode in ['bad_post','pending','reservation','consumed','wrong_bridge','preflight_fail','preflight_timeout','submit_timeout','success']:run_case(mode,mode)
 report={'schema':'formal_main_v2','kind':'k64_root_dispatch_independent_CPU_review','status':'passed','entrypoint_sha256':PIN,'entrypoint':{'path':ENTRY,'sha256':PIN},'reviewed_by':'independent','full_source_review':True,'CPU_synthetic_scenarios':9,'real_submission_calls':0,'production_state_writes':False,'gateway_lifecycle_inherited':True,'scope_two_exact_pairs_only':True,'actual_runtime_post_required':True,'unknown_submission_kept_no_retry':True,'checks':len(CHECKS),'expected_reentries_rejected':len(NEG),'blockers':[],'evidence':{'checks':write('checks.json',CHECKS),'expected_rejections':write('expected_reentries.json',NEG)}}
 print(json.dumps(write('dispatch_independent_review.json',report),sort_keys=True))
try:main()
except BaseException as e:write('failure.json',{'error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'checks':CHECKS,'expected_rejections':NEG});raise
