"""Independent read-only canonical k64 seed23 source bridge audit. No submission."""
from pathlib import Path
from types import SimpleNamespace
import sys,os,json,hashlib,copy,ast,importlib.util,contextlib,io,traceback,time,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/k64_seed23_bridges_independent_20261020T1949/post_readiness';A=R/'.local/k64_seed23_bridges_20261020T1949'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PUBLICATION='results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_candidate_publication.json';PUB_SHA='1656f5c931545c0b0b2ae987202dbf1ae3281ccf2c71b900a30bf2f8a55f3949'
MAP_SHA='ec56fca197dcbb6de668761081852be973aba6ab61673edf4c961d29390973aa'
EXPECT={'spatial':{'control':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3','bridge':'678b6c57fbf6e188eced6d42bfa158862c1f185bced034027e535a4316804c87','total':42480,'failed':73,'selected':{'A':2500,'B':3500},'jobs':['3024716','3025205','3028522','3043399','3044479']},'object':{'control':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767','bridge':'04c596f8b86569d7476f504fcf5519c205b0fc7eb2e0bd6de953fa47f5bc6735','total':52868,'failed':69,'selected':{'A':2500,'B':4500},'jobs':['3028468','3044017','3044844']}}
READS={};CHECKS=[];NEG=[];REPORTS=[]
SELECTED_ALLOWED={Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2')/suite/'k64'/'seed23'/arm/'best.pt' for suite in ('libero_spatial','libero_object') for arm in ('A','B')}
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork'):raise RuntimeError('audit forbids process/network/Slurm')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2] or 0
  if p not in SELECTED_ALLOWED and (p.suffix.lower() in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init','.npz','.h5','.hdf5'} or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts)):raise RuntimeError('no non-selected weights/data/sealed access '+str(p))
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


ROOT_PINS={'Spatial':'9a85ad40763f3d31a5b7bf6fa3c2c23abf82ff27f3499e3663db9dd88d6c3f1e','Object':'24e7511cba602382662a900ed4b673ab5c5ae729186078c582c24e64890340ea'}
B='results/formal_main_v2/preflight/heartbeat_20261021T0349'
def hash_selected(path,pin):
 p=Path(path);check(p in SELECTED_ALLOWED and p.resolve()==p.absolute() and not p.is_symlink(),'only exact independently registered selected best bytes')
 before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 after=p.stat();check((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'checkpoint stable while hashing');check(h.hexdigest()==pin,'selected checkpoint exact byte SHA '+str(p))
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':after.st_size,'deserialized':False,'copied':False}
def main():
 g=load('scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py','873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb');wrapper=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33');out=[]
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH)
  try:
   state_raw=(R/g.STATE).read_bytes();state=json.loads(state_raw);state_sha=sha(state_raw)
   check(state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None,'no active reservation or pending state during readonly post review')
   for title,pin in ROOT_PINS.items():
    suite='libero_'+title.lower();rootref={'path':B+'/'+title+'64s23_runtime_readiness_root.json','sha256':pin};receipt=rd(rootref['path'],pin)
    check(receipt['status']=='passed_exact_pre_execution_checks_pending_live_capacity' and receipt['suite']==suite and receipt['actual_full_P_wrapper_verifications']==1 and receipt['new_GPU_submissions']==[] and receipt['new_trials']==0 and receipt['actual_GPU_runtime_chain_verified'] is False and receipt['state_unchanged'] is True,'actual root metadata receipt scope '+suite)
    rootcheck=rd(receipt['root_check']['path'],receipt['root_check']['sha256']);check(rootcheck['full_P_wrapper_verify'] is True and rootcheck['state_unchanged'] is True and rootcheck['reservation_not_activated'] is True,'root positive original wrapper result bound '+suite)
    auth,e,plan,science,prepared=g.validate_authorization(R,receipt['authorization']);allowed=g.SCOPED_DEVELOPMENT_PLANS[suite];control=load(allowed['control']['path'],allowed['control']['sha256']);descriptor=control.descriptor()
    check(auth['plan']=={k:allowed[k] for k in ('path','sha256')} and auth['explicit_source_control']==descriptor==receipt['source_control'],'exact actual authorization/source closure '+suite)
    ready=e.ref(auth['runtime_readiness']);check(ready['active'] is False and ready['allowed_stages']==['development'] and ready['final_evaluation_enabled'] is False,'inactive metadata readiness only '+suite)
    check(ready['root_review']!=ready['independent_review'],'root and independent distinct '+suite)
    for ref in [auth['runtime_readiness'],ready['root_review'],ready['independent_review'],auth['scientific_plan'],auth['plan'],plan['invocation']['action_execution_contract']]:read(P/ref['path'],ref['sha256'])
    check(receipt['readiness']==auth['runtime_readiness'] and receipt['prepared_invocation']==auth['prepared_invocation'] and receipt['reservation']==auth['root_reservation'],'root receipt exact current refs '+suite)
    check(not any(j.get('experiment')==g.ROUND and j.get('suite')==suite and j.get('mode')=='development' and set(j.get('method_ids',[]))&set(control.METHODS) for j in state['registered_jobs']),'no prior overlapping attempt '+suite)
    for n in [plan['invocation_relative'],plan['output_relative']]:check(not (R/n).exists() and not (P/n).exists(),'no existing invocation/output '+n)
    bundle=g.FrozenPlan(R,auth,e,plan,science,prepared).prepare(state);bundle['readiness_files']={**ready['runtime_publication_files'],auth['runtime_readiness']['path']:auth['runtime_readiness']['sha256']};actual=g.NativeIO(R)._inputs(bundle,False);check(actual['missing_publications']==[] and actual['output_exists'] is False,'all real P metadata exact and output absent '+suite)
    verified=wrapper.verify(prepared,project=P);check(verified['effective_plan']==plan and verified['original_plan']==science and verified['execution_contract']==e.ref(plan['invocation']['action_execution_contract']),'independent actual full P action wrapper positive '+suite)
    policy=control.bridge(Evidence()).policy();selected={arm:hash_selected(row['path'],row['sha256']) for arm,row in policy['selected_checkpoints'].items()};check(set(selected)=={'A','B'},'both exact selected checkpoints verified '+suite);e.unchanged()
    ev=write(title+'/actual_metadata_evidence.json',{'schema':'formal_main_v2','kind':'independent_actual_metadata_and_selected_bytes','root_readiness_receipt':rootref,'root_pre_execution':receipt['root_check'],'root_evidence_sha256':e.hashes,'runtime_files':actual['checked_files'],'selected_checkpoint_bytes':selected,'full_P_wrapper_verifications':1,'model_deserialized':False,'GPU_runs':0,'state_sha256':state_sha})
    result={'schema':'formal_main_v2','kind':'exact_k64s23_post_readiness_independent_review','status':'passed','reviewed_by':'independent','suite':suite,'authorization':receipt['authorization'],'root_pre_execution':receipt['root_check'],'root_readiness_receipt':rootref,'effective_plan':auth['plan'],'scientific_plan':auth['scientific_plan'],'prepared_invocation':auth['prepared_invocation'],'runtime_readiness':auth['runtime_readiness'],'reservation':auth['root_reservation'],'explicit_source_control':descriptor,'actual_full_P_wrapper_verifications':1,'actual_GPU_runtime_chain_verified':False,'selected_checkpoint_bytes_verified':True,'original_selected_updates':{arm:row['update'] for arm,row in policy['selected_checkpoints'].items()},'model_deserialized':False,'official_base_identity_inherited_not_rehashed':True,'reservation_not_activated':True,'no_existing_duplicate':True,'scientific_trials_added':0,'new_GPU_runs':0,'state_unchanged':True,'state_sha256':state_sha,'final_enabled':False,'Goal_HOLD_unchanged':True,'metadata_evidence':ev,'blockers':[],'dispatch_requirement':'Root must freshly reconcile all registered Slurm jobs and capacity; this proof does not itself submit or reserve a GPU.'}
    out.append(write(title+'/post_readiness_independent.json',result))
   check((R/g.STATE).read_bytes()==state_raw,'shared-lock post review left state exact bytes unchanged')
  finally:fcntl.flock(lock,fcntl.LOCK_UN)
 inventory=rd(INV,INV_SHA)
 for root in (R,S):
  for rel,pin in inventory['files'].items():check(sha((root/rel).read_bytes())==pin,'173 frozen preserved '+str(root/rel))
 ref=write('post_readiness_index.json',{'schema':'formal_main_v2','status':'passed','pair_reviews':out,'checks':len(CHECKS),'actual_full_P_wrapper_verifications':2,'selected_checkpoint_files_hashed':4,'new_GPU_runs':0,'state_writes':False,'final_enabled':False,'blockers':[],'check_log':write('checks.json',CHECKS),'input_sha256':write('read_inputs.json',READS)});print(json.dumps({'index':ref,'pair_reviews':out},sort_keys=True))
try:main()
except BaseException as e:write('failure.json',{'error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'checks':CHECKS});raise
