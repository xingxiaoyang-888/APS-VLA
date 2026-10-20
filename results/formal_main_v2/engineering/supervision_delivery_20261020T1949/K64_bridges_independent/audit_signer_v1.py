"""Independent read-only canonical k64 seed23 source bridge audit. No submission."""
from pathlib import Path
from types import SimpleNamespace
import sys,os,json,hashlib,copy,ast,importlib.util,contextlib,io,traceback,time,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/k64_seed23_bridges_independent_20261020T1949/helper_audit';A=R/'.local/k64_seed23_bridges_20261020T1949'
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


SIGNER='.local/collect_terminal_20261020T1949/development_gateway/root_sign_readiness_v1.py';SIGNER_SHA='773bc105bd77ddab8a9927e981f87c2050ff1baecb34cfdb4009916099e81338'
def main():
 source=read(SIGNER,SIGNER_SHA).decode();tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 selected=[]
 for node in main.body:
  names={n.id for n in ast.walk(node) if isinstance(n,ast.Name)}
  if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='require' and ('cpu' in names or 'ind' in names):selected.append(copy.deepcopy(node))
  if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple) and [n.id for n in node.target.elts]==['key','value']:selected.append(copy.deepcopy(node))
 check(len(selected)==4,'exact four original signer independent-interface validation AST statements')
 args=['ind','cpu','gateway_files','pair','action_ref','action','effective','descriptor','suite','g','require'];fn=ast.FunctionDef(name='verify_exact_independent_interfaces',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n) for n in args],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=selected,decorator_list=[]);m=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));ns={};exec(compile(m,SIGNER+'::<exact_validation_AST_only>','exec'),ns)
 validate=ns['verify_exact_independent_interfaces'];gateway=load('scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py','873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb');base='.local/k64_seed23_bridges_independent_20261020T1949/control_runtime_attempt01/'
 cpu=rd(base+'independent_gateway_CPU_review.json','45a86335a1c3224c47e76e162e90958f2437fd0152fe8ee1edbf710bfb10284a');mapping=rd(A/'static_plan_publication_candidate.json','d447aebff71f88bea0f568def97a5106936a7c107062062e7386758f8d6a30ca')
 for pair in mapping['pairs']:
  suite=pair['suite'];short=suite.removeprefix('libero_');ind=rd(base+short+'/independent_plan_review.json');eff=rd(pair['effective_plan']['path'],pair['effective_plan']['sha256']);ar=eff['invocation']['action_execution_contract'];action=rd(ar['path'],ar['sha256']);descriptor=pair['source_control'];closure=gateway.source_files(R)
  params=dict(ind=ind,cpu=cpu,gateway_files=closure,pair=pair,action_ref=ar,action=action,effective=eff,descriptor=descriptor,suite=suite,g=gateway,require=gateway.require)
  # METHODS is the original pinned module constant used by the unmodified AST.
  ns['METHODS']=['A64_seed23','B64_seed23'];validate(**params);check(True,'actual signer consumes actual typed receipts '+suite)
  for field,value in [('status','pending'),('execution_version','legacy'),('production_chain_complete',False),('actual_GPU_runtime_chain_verified',True),('suite','libero_goal'),('plan_sha256','0'*64),('method_ids',['dense']),('allowed_stages',['final']),('resume',True),('prior_job_ids',['1']),('runtime_sources',{}),('explicit_source_control',{}),('scientific_plan',{}),('action_execution_contract',{})]:
   ix=copy.deepcopy(ind);ix[field]=value;neg(suite+' signer independent '+field,lambda ix=ix:validate(**{**params,'ind':ix}))
  for field,value in [('status','pending'),('kind','other'),('files',{}),('blockers',['blocked'])]:
   cx=copy.deepcopy(cpu);cx[field]=value;neg(suite+' signer CPU '+field,lambda cx=cx:validate(**{**params,'cpu':cx}))
 signer=load(SIGNER,SIGNER_SHA)
 invalid=['--suite','Spatial','--plan-independent-review','unused','--plan-independent-review-sha256','0'*64,'--gateway-cpu-review','unused','--gateway-cpu-review-sha256','0'*64,'--root-reviewed-source-sha256','0'*64,'--execute-root-readiness']
 neg('signer refuses wrong exact source before any metadata write',lambda:signer.main(invalid))
 calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)];check(not any(isinstance(n.func,ast.Attribute) and n.func.attr in ('atomic_json','observe','sbatch') for n in calls),'signer has no state mutation/scheduler submission/observation API')
 check(not any(isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' for n in calls),'signer has no subprocess path')
 report={'schema':'formal_main_v2','kind':'k64_root_signer_independent_interface_review','status':'passed','entrypoint':{'path':SIGNER,'sha256':SIGNER_SHA},'reviewed_by':'independent','original_validation_AST_executed':True,'actual_typed_receipts_consumed_for_both_pairs':True,'checks':len(CHECKS),'negative_cases':len(NEG),'root_only_actual_execution_required':True,'full_source_review':True,'shared_writer_lock_and_state_unchanged_assertion_preserved':True,'one_shot_immutable_outputs_and_no_existing_invocation_guard':True,'actual_P_wrapper_positive_required_before_root_receipt':True,'actual_readiness_created_by_this_audit':False,'state_Git_Slurm_writes':False,'new_GPU_runs':0,'evidence':{'checks':write('signer_checks.json',CHECKS),'negative_cases':write('signer_expected_rejections.json',NEG),'input_sha256':write('signer_inputs.json',READS)},'blockers':[]}
 print(json.dumps(write('signer_independent_review.json',report),sort_keys=True))
try:main()
except BaseException as e:write('signer_failure.json',{'error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'checks':CHECKS,'expected_rejections':NEG});raise
