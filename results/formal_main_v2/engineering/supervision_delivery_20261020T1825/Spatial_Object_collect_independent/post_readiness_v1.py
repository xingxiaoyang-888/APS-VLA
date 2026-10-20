"""Read-only post-publication collect readiness audit; no scheduler, GPU, state or production writes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent/'post_readiness';D.mkdir(exist_ok=False)
sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'src'))
READS={};CHECKS=[];OUT=[]
def hook(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):raise RuntimeError('No subprocess/network/scheduler allowed')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,int):return
  p=Path(os.fsdecode(p)).absolute()
  if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in ('.pt','.pth','.pkl','.pickle','.ckpt','.safetensors','.bin','.init','.pruned_init'):raise RuntimeError('Weight or sealed payload prohibited '+str(p))
  write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
  if write:assert D in p.parents,'private-only write'
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  for x in args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]:
   p=Path(os.fsdecode(x)).absolute();assert p==D or D in p.parents,'private-only mutation'
sys.addaudithook(hook)
def check(ok,msg):
 if not ok:raise AssertionError(msg)
 CHECKS.append(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raw(path,pin=None):
 p=Path(path);p=p if p.is_absolute() else R/p
 check(p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)),'exact nonlink path '+str(p));b=p.read_bytes();v=hashlib.sha256(b).hexdigest();check(pin is None or v==pin,'exact SHA '+str(p));check(str(p) not in READS or READS[str(p)]==v,'stable input '+str(p));READS[str(p)]=v;return b
def obj(path,pin=None):return json.loads(raw(path,pin))
def ref(path):p=Path(path);return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def checked_ref(value):
 check(isinstance(value,dict) and set(value)=={'path','sha256'},'reference schema');p=Path(value['path']);check(not p.is_absolute() and '..' not in p.parts and str(p)==value['path'],'reference containment');check(isinstance(value['sha256'],str) and len(value['sha256'])==64 and all(c in '0123456789abcdef' for c in value['sha256']),'reference SHA syntax');return obj(value['path'],value['sha256'])
def put(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
 return ref(path)
def load(path,pin,name):
 raw(path,pin);sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--spatial-root-sha256',required=True);ap.add_argument('--object-root-sha256',required=True);a=ap.parse_args()
try:
 source=ref(Path(__file__));statebytes=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(statebytes);state_before=hashlib.sha256(statebytes).hexdigest()
 check(state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None,'no active submission or reservation observed')
 check(not state['formal_main_progress']['test_opened'] and not state['formal_main_progress']['global_release_created'],'final remains sealed')
 import cti_vla
 check(S/'src' in Path(cti_vla.__file__).resolve().parents,'frozen cti package')
 gp=R/'scripts/ops/formal_action_deployment_posttraining_v1/gateway.py';g=load(gp,'4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83','collect_post_gateway')
 wrapper=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','collect_post_wrapper')
 for label,pin,planpin,indpin in [('Spatial',a.spatial_root_sha256,'0ed890e69b47155eb83dd388e05c68a84b635e79b596b2b0e39cd4f903a2f5b7','8c14a975a6b79cf1f5fdbc497560cafd77455a22af307712465468aecb27cfc3'),('Object',a.object_root_sha256,'7002d950c23e3dcb76862089f428f3305d78a87e6c84ab01389fc32bfd1c6ee5','e278f9ec7db15810e580dffbb886c4853a4838aeac3f287c48c83b569c244330')]:
  prefix='results/formal_main_v2/execution/'+label.lower()+'_collect_action_v1_20261020T1825';suite='libero_'+label.lower();rr='results/formal_main_v2/preflight/heartbeat_20261021T0225/'+label+'_collect_readiness.json';receipt=obj(rr,pin)
  check(receipt['suite']==suite and receipt['status']=='collect_prepared_root_independent_CPU_verified_not_submitted' and receipt['state_unchanged'] is True and receipt['new_GPU_jobs']==0 and receipt['actual_P_action_wrapper_verified_after_publication'] is True and receipt['final_values_read'] is False,'actual root preparation receipt '+suite)
  plan=obj(prefix+'/effective_plan.json',planpin);science=obj(prefix+'/scientific_plan.json');execution=obj(prefix+'/execution_contract.json');auth=checked_ref(receipt['authorization']);ready=checked_ref(auth['runtime_readiness']);prepared=checked_ref(auth['prepared_invocation']);ind=checked_ref(receipt['independent_review']);root=checked_ref(receipt['root_review']);gateway_review=checked_ref(receipt['gateway_review'])
  raw(D.parent/label/'independent_readiness.json',indpin);check(receipt['independent_review']=={'path':prefix+'/independent_plan_review.json','sha256':indpin},'exact prior independent review copied '+suite)
  check(ind['suite']==suite and ind['stage']=='collect' and ind['plan_sha256']==plan['plan_sha256'] and ind['effective_plan']==ref(R/prefix/'effective_plan.json') and ind['scientific_plan']==ref(R/prefix/'scientific_plan.json') and ind['action_execution_contract']==ref(R/prefix/'execution_contract.json'),'per-suite three plans exact binding '+suite)
  check(ind['runtime_sources']==execution['files']==root['runtime_sources'] and ind['production_chain_complete'] is True and root['production_chain_complete'] is True and root['new_GPU_acceptance'] is False and ind['real_GPU_collect'] is False,'CPU source-chain meaning unchanged '+suite)
  check(ready['root_review']==receipt['root_review'] and ready['independent_review']==receipt['independent_review'] and ready['root_review']!=ready['independent_review'] and ready['active'] is True and ready['status']=='passed','separate real readiness roots '+suite)
  check(ready['runtime_sources']==execution['files'] and execution['files']['scripts/ops/formal_action_deployment_v1/gateway.py']=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','scientific action runtime original gateway preserved '+suite)
  check(gateway_review['kind']=='formal_downstream_server_gateway_independent_CPU_review' and gateway_review['status']=='passed_CPU_review' and not gateway_review['blockers'] and gateway_review['files']['scripts/ops/formal_action_deployment_posttraining_v1/gateway.py']==sha(gp),'separately independently reviewed posttraining control gateway '+suite)
  check(auth['gateway_files']==g.source_files(R) and auth['independent_review']==receipt['gateway_review'],'gateway closure and independent review exact '+suite)
  for path,sha256 in auth['gateway_files'].items():raw(path,sha256)
  for value in (auth['runtime_readiness'],ready['root_review'],ready['independent_review']):raw(P/value['path'],value['sha256'])
  for path,sha256 in ready['runtime_publication_files'].items():raw(path,sha256);raw(P/path,sha256)
  for path,sha256 in execution['files'].items():raw(path,sha256);raw(P/path,sha256)
  for path,sha256 in prepared['support_files'].items():raw(path,sha256);raw(P/path,sha256)
  for path,sha256 in prepared['watched_files'].items():raw(path,sha256)
  checked,e,p,sc,prep=g.validate_authorization(R,receipt['authorization'])
  check(checked==auth and p==plan and sc==science and prep==prepared,'actual canonical authorization validator exact result '+suite)
  ctx=wrapper.verify(prepared,project=P)
  check(ctx['original_plan']==science and ctx['effective_plan']==plan,'actual full P action wrapper positive verification '+suite)
  check(prepared['stage']=='collect' and prepared['suite']==suite and prepared['method_ids']==['dense'] and prepared['resume'] is False and prepared['prior_job_ids']==[] and not prepared['final_values_read_locally'],'development dense collect only '+suite)
  reserve=checked_ref(auth['root_reservation']);check(reserve['authorization_intent_sha256']==g.intent_sha(auth),'reservation intent exact '+suite)
  check(not any(j.get('experiment')=='formal_main_v2' and j.get('suite')==suite and j.get('mode') in ('collect','full','components') for j in state['registered_jobs']),'no registered collect/profile duplicate '+suite)
  for base in (R,P):check(not(base/plan['output_relative']).exists() and not(base/plan['invocation_relative']).exists(),'no existing scientific invocation or output '+suite+' '+str(base))
  for method in science['invocation']['method_ids']:check(method=='dense','no selectors in collection '+suite)
  OUT.append({'schema':'formal_main_v2','kind':'formal_collect_post_readiness_independent_review','status':'passed','reviewed_by':'independent','review_agent':'/root/devplans_audit_20261020_1418','suite':suite,'stage':'collect','authorization':receipt['authorization'],'root_readiness_receipt':{'path':rr,'sha256':pin},'runtime_readiness':auth['runtime_readiness'],'prepared_invocation':auth['prepared_invocation'],'root_reservation':auth['root_reservation'],'prior_independent_plan_review':receipt['independent_review'],'independent_gateway_review':receipt['gateway_review'],'scientific_plan':ref(R/prefix/'scientific_plan.json'),'effective_plan':ref(R/prefix/'effective_plan.json'),'action_execution_contract':ref(R/prefix/'execution_contract.json'),'plan_sha256':plan['plan_sha256'],'runtime_sources':execution['files'],'actual_full_P_wrapper_verifications':1,'actual_GPU_runtime_chain_verified':False,'real_GPU_collect':False,'scientific_trial_count_added':0,'planned_observations':30,'final_values_read':False,'production_state_modified':False,'reservation_inactive':True,'registered_duplicate_absent_at_observation':True,'actual_new_scheduler_queries':0,'metadata_preexecution_only':True,'source':source,'blockers':[],'limitations':['Only exact canonical readiness and source closure are proved; runtime and terminal observations are not examined.','Root must recheck live all-mode capacity and pending/duplicate state under the canonical lock at dispatch.','New posttraining control gateway is separately independently audited; its code is not newly audited here.']})
 import torch
 check(not torch.cuda.is_initialized(),'no CUDA initialization')
 for p,sha256 in list(READS.items()):check(sha(p)==sha256,'all audited inputs stable '+p)
 check(hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()==state_before,'canonical state bytes unchanged during independent read-only audit')
 details=put(D/'checks.json',{'checks':CHECKS,'count':len(CHECKS),'evidence_sha256':READS,'state_sha256':state_before,'actual_full_P_wrapper_verifications':2,'new_GPU_calls':0,'new_scheduler_queries':0})
 refs=[]
 for record in OUT:record['detailed_report']=details;refs.append(put(D/(record['suite']+'_independent_review.json'),record))
 index=put(D/'independent_index.json',{'status':'passed','reviews':refs,'detailed_report':details,'actual_full_P_wrapper_verifications':2,'actual_GPU_collect_completed':False,'production_state_modified':False})
 print(json.dumps({'index':index,'reviews':refs,'checks':len(CHECKS)}))
except BaseException as ex:
 put(D/'failure_v1.json',{'status':'failed','error':str(ex),'error_type':type(ex).__name__,'traceback':traceback.format_exc(),'checks_completed':len(CHECKS)});raise
