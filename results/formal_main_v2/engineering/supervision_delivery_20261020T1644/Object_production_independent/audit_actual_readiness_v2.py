from pathlib import Path
from types import ModuleType
from datetime import datetime,timezone
import sys,os,json,hashlib,copy,time,traceback,collections
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).parent;OUT=D/'post';C='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644';B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
ROOTREF={'path':B+'/Object_runtime_readiness_root.json','sha256':'4a9ae0aa406884ba7ee3d2f29799ff26186b19e42c4b1359de498df3cb400233'}
CONTROL='scripts/ops/formal_object256s23_source_bridge_v1/control.py';CONTROL_SHA='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f'
METHODS=['A256_seed23','B256_seed23'];CHECKS=[];WATCH={};WEIGHT_ALLOWED=set();WEIGHT_READS=set();BLOCKED=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def audit_guard(event,args):
 if event in ('subprocess.Popen','socket.connect','os.system'):
  BLOCKED.append(event);raise RuntimeError('Independent audit forbids external processes/network/Slurm')
 if event=='open':
  n,m,flags=args
  if isinstance(n,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(n));p=p if p.is_absolute() else Path.cwd()/p
   writing=isinstance(m,str) and any(x in m for x in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
   if writing and OUT not in p.parents:
    BLOCKED.append(str(p));raise RuntimeError('Only private audit output writes allowed')
   if any('sealed' in x.lower() or x.lower() in ('test',) for x in p.parts) or p.suffix in ('.pkl','.init','.pruned_init'):
    BLOCKED.append(str(p));raise RuntimeError('No final or initial-state payload reads')
   if any(x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix in ('.pt','.pth','.bin','.ckpt','.safetensors'):
    if p not in WEIGHT_ALLOWED or writing:
     BLOCKED.append(str(p));raise RuntimeError('Only exact declared checkpoint bytes may be streamed readonly')
    WEIGHT_READS.add(str(p))
 if event in ('os.remove','os.rename','os.rmdir','os.symlink','os.link'):
  BLOCKED.append(event);raise RuntimeError('No mutation outside immutable private outputs')
 if event=='os.mkdir':
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if p!=OUT and OUT not in p.parents:raise RuntimeError('Only private audit directories')
sys.addaudithook(audit_guard)
def check(name,ok):
 CHECKS.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def fingerprint(p):
 s=p.stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'inode':s.st_ino,'device':s.st_dev}
def hash_stable(p,git_blob=False):
 p=Path(p);check('canonical path '+str(p),p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)))
 before=fingerprint(p);hh=hashlib.sha256();gh=hashlib.sha1() if git_blob else None
 if gh:gh.update(('blob '+str(before['bytes'])+'\0').encode())
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):
   hh.update(block)
   if gh:gh.update(block)
 check('stable streamed bytes '+str(p),fingerprint(p)==before)
 return {'path':str(p),'sha256':hh.hexdigest(),'git_blob_sha1':gh.hexdigest() if gh else None,**before}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def refread(rr):
 check('exact reference fields',type(rr) is dict and set(rr)=={'path','sha256'})
 rel=rr['path'];check('safe relative reference '+rel,type(rel) is str and not Path(rel).is_absolute() and '..' not in Path(rel).parts and Path(rel).as_posix()==rel)
 q=R/rel;check('reference SHA '+rel,h(q)==rr['sha256']);WATCH[rel]=rr['sha256'];return json.loads(q.read_bytes())
def pinnedread(rel,pin):return refread({'path':rel,'sha256':pin})
def load(p,pin):
 check('exact executable source '+str(p),h(p)==pin);m=ModuleType('object_post_'+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def write(name,obj):
 p=OUT/name
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':h(p)}
def stable_state():
 p=R/'results/experiment_supervisor/state.json';before=fingerprint(p);data=p.read_bytes();after=fingerprint(p);check('stable read live state',before==after);return json.loads(data),hashlib.sha256(data).hexdigest()
def assert_not_admitted(state,label):
 check(label+' pending empty',state.get('pending_submission') is None)
 auto=state['autonomous_training_v1'];check(label+' no active reservation',auto.get('reserved_GPU_slots')==0 and auto.get('root_submission_hold') is None)
 overlap=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('suite')=='libero_object' and j.get('mode')=='development' and set(j.get('method_ids',[]))&set(METHODS)]
 check(label+' no registered duplicate',not overlap)
 return {'pending_submission':None,'reserved_GPU_slots':0,'root_submission_hold':None,'overlap_job_ids':[],'controller_job_id':auto['controller_job_id']}
def main():
 OUT.mkdir(exist_ok=False);started=time.monotonic();root=refread(ROOTREF);check('root positive metadata status',root['status']=='passed_exact_Object256s23_pre_execution_checks_pending_live_capacity')
 check('root did not imply GPU or trial completion',root['actual_full_P_wrapper_verifications']==1 and root['actual_GPU_runtime_chain_verified'] is False and root['new_GPU_submissions']==[] and root['new_trials']==0 and root['final_release'] is False and root['state_unchanged'] is True)
 rc=refread(root['root_check']);check('exact root preexecution identity',root['root_check']['sha256']=='4dff5677a601cb71f4d41a1c5f64008d54d466e5853987b95625d5960b326523')
 check('root full positive check',rc['status']=='passed_actual_unchanged_P_wrapper_verify_and_NativeIO' and rc['full_P_wrapper_verify'] is True and rc['real_full_registry_scientific_reconstruction'] is True)
 check('root readonly inactive reservation',rc['state_sha256']==root['state_sha256'] and rc['state_unchanged'] is True and rc['reservation_not_activated'] is True and rc['live_capacity_not_queried'] is True and rc['actual_GPU_runtime_chain_verified'] is False and rc['model_not_loaded'] is True)
 c=load(R/CONTROL,CONTROL_SHA);descriptor=c.descriptor();check('root exact source control',root['source_control']==rc['explicit_source_control']==descriptor)
 auth=refread(root['authorization']);ready=refread(root['readiness']);prepared=refread(root['prepared_invocation']);reservation=refread(root['reservation'])
 check('exact authorization identity',root['authorization']['sha256']=='e6a6a2165c46187e42338764f16417d90e8d42dd1892d8d06f61bce6d32c5047')
 check('authorization one bounded attempt',auth['maximum_attempts']==1 and auth['automatic_retry'] is False and auth['final_release_authorized_by_gateway'] is False and auth['excluded_nodes']==['gpu4020'])
 check('authorization descriptor and full closure',auth['explicit_source_control']==descriptor and auth['gateway_files']==c.closure())
 check('matching refs through root auth and actual check',auth['runtime_readiness']==root['readiness']==rc['readiness'] and auth['prepared_invocation']==root['prepared_invocation']==rc['prepared_invocation'] and auth['root_reservation']==root['reservation']==rc['reservation'])
 check('inactive readiness only development',ready['active'] is False and ready['allowed_stages']==['development'] and ready['forbidden_stages']==['collect','full','components','global_freeze','final'] and ready['allowed_suite']=='libero_object' and ready['expected_trials']==200 and ready['unique_development_initial_states']==100)
 check('readiness cannot claim GPU/final/O2A',ready['actual_GPU_runtime_chain_verified'] is False and ready['scientific_trials_completed_by_new_runtime']==0 and ready['final_evaluation_enabled'] is False and ready['O2A_enabled'] is False and ready['global_freeze_enabled'] is False)
 check('same prior CPU/root/independent evidence',ready['independent_review']==root['independent_review']==rc['independent_review'] and ready['root_review']==rc['root_review'] and ready['independent_review']!=ready['root_review'])
 ind=refread(ready['independent_review']);rr=refread(ready['root_review']);cpu=refread(root['gateway_CPU_review'])
 check('separate exact reviewers source-bound',ind['status']==rr['status']=='passed' and ind['explicit_source_control']==rr['explicit_source_control']==descriptor and ind['actual_GPU_runtime_chain_verified'] is rr['actual_GPU_runtime_chain_verified'] is False)
 check('typed gateway CPU exact closure',cpu['kind']=='formal_downstream_server_gateway_independent_CPU_review' and cpu['status']=='passed_CPU_review' and cpu['blockers']==[] and cpu['files']==c.closure() and cpu['explicit_source_control']==descriptor)
 g=c.gateway_module();check('reservation exact inactive intent',reservation['status']=='approved_for_exact_downstream_request' and reservation['reserved_slots']==1 and reservation['capacity_limit_all_GPU_modes']==8 and reservation['automatic_retry'] is False and reservation['authorization_intent_sha256']==g.intent_sha(auth) and reservation['authorization_path']==root['authorization']['path'])
 before,before_sha=stable_state();before_gate=assert_not_admitted(before,'before');check('same controller',before_gate['controller_job_id']==auth['controller_job_id']=='3034538')
 aa,ee,effective,science,inv=g.validate_authorization(R,root['authorization']);check('actual validator returned exact prepared',aa==auth and inv==prepared)
 action=refread(inv['action_execution_contract']);check('exact plan/internal hash',effective['plan_sha256']==ready['plan_sha256']==ind['plan_sha256']=='2c28c6def19c9f4abc98dbe10f3435ec712791786a2e54b48c7f4feec28070f0')
 check('exact four published plan references',aa['plan']==ready['effective_plan']==rc['effective_plan'] and aa['scientific_plan']==ready['scientific_plan']==rc['scientific_plan'] and inv['action_execution_contract']==ready['action_execution_contract']==rc['action_execution_contract'])
 c.scope_invocation(inv);check('unrun first complete development pair',inv['method_ids']==METHODS and inv['prior_job_ids']==[] and inv['resume'] is False and inv['prior_review'] is None and inv['stop_after'] is None)
 statecopy=copy.deepcopy(before);bundle=g.FrozenPlan(R,aa,ee,effective,science,inv).prepare(before);check('actual original scientific rebuild and no in-memory state mutation',before==statecopy and bundle['plan']==effective and bundle['invocation']==inv)
 bundle['readiness_files']={**ready['runtime_publication_files'],root['readiness']['path']:root['readiness']['sha256']}
 io=g.NativeIO(R);pre=io.preflight(bundle);actual=io._inputs(bundle,False);check('actual P metadata all present',pre['missing_publications']==actual['missing_publications']==[] and actual['output_exists'] is False and len(actual['checked_files'])==rc['runtime_files_checked'])
 _,pubs=io._watch(bundle)
 for rel,pin in pubs.items():check('exact R P publication '+rel,h(R/rel)==h(P/rel)==pin)
 for base in (R,P):check('no published invocation '+str(base),not (base/effective['invocation_relative']).exists());check('no output '+str(base),not (base/effective['output_relative']).exists())
 w=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33');verified=w.verify(inv,project=P)
 check('actual P original wrapper full positive',verified['effective_plan']==effective and verified['original_plan']==science and verified['execution_contract']==action and verified['readiness']==ready)
 check('runtime exact checkpoint path',str(verified['args'].checkpoint)==action['runtime_contract']['checkpoint']=='/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-object-4c89574')
 manifest=pinnedread('results/formal_main_v2/execution/object256seed23_source_bridge_v1_20261020T1530/libero_object_k256_seed23_development.json','5f2bdcac8752c0cd06ad8dcb67114920b642db1415f6a88e1335d6c9f10fb028')
 check('manifest no method substitution',[x['identity']['method_id'] for x in manifest['methods']]==METHODS and manifest['suite']=='libero_object' and manifest['split']=='development')
 selector_rows=[]
 for row in manifest['methods']:
  ident=row['identity'];arm=ident['method'];q=Path(row['checkpoint']);expected=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k256/seed23')/arm/'best.pt'
  check('selected checkpoint exact bounded path '+arm,q==expected);WEIGHT_ALLOWED.add(q);got=hash_stable(q);check('selected checkpoint actual bytes '+arm,got['sha256']==ident['checkpoint_sha256'])
  receipt=pinnedread(row['receipt'],ident['deployment_receipt_sha256']);check('frozen accepted selection metadata '+arm,receipt['checkpoint_sha256']==got['sha256'] and receipt['completed_updates']==receipt['planned_updates']==5000 and receipt['training_complete'] is True and receipt['metadata']['update']==5000 and ident['future_head_deployed'] is False and receipt['metadata']['per_camera_budgets']==[128,128])
  check('selection identity consistent '+arm,receipt['metadata']['frozen_model_sha256']==ident['frozen_model_sha256']=='33285a7643de7073e41bd2062cbbc80b4df8fddff915c0a86a13d0bbae48edce' and receipt['metadata']['suite']=='libero_object' and receipt['metadata']['seed']==23)
  selector_rows.append({'method_id':ident['method_id'],'selected_update':5000,'expected_sha256':ident['checkpoint_sha256'],'actual':got})
 base=Path(verified['args'].checkpoint);official=pinnedread('configs/assets/openvla_oft_libero_object.json','3c3e3b614fa0bf4134825d95d22b69173d79bfb4a594f9c113c832156d0f6a24');strict=pinnedread('configs/assets/formal_main_v2_strict/libero_object.json','d8f1f9a5c1c8c040aa499fd9df35ebe4a039fd6c756b565cf6055046be0cf8b3')
 check('official immutable model manifest unchanged',all(strict[k]==official[k] for k in ('schema_version','repository','revision','total_bytes','files')) and strict['revision']=='4c89574e1c538b6c102f43f0526d60a9d3650148' and len(strict['files'])==25)
 for row in strict['files']:
  rel=Path(row['path']);check('bounded official file path '+row['path'],not rel.is_absolute() and '..' not in rel.parts);WEIGHT_ALLOWED.add(base/rel)
 base_rows=[]
 for row in strict['files']:
  got=hash_stable(base/row['path'],git_blob='git_blob_sha1' in row);check('official file size '+row['path'],got['bytes']==row['size']);check('official content identity '+row['path'],got.get('sha256' if 'sha256' in row else 'git_blob_sha1')==row.get('sha256',row.get('git_blob_sha1')));base_rows.append({'relative_path':row['path'],'registered':row,'actual':got})
 check('all base bytes verified',sum(x['actual']['bytes'] for x in base_rows)==strict['total_bytes']==15939159270)
 inventory=pinnedread('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');check('173 exact inventory',len(inventory['files'])==173)
 for rel,pin in inventory['files'].items():check('frozen 173 R S '+rel,h(R/rel)==h(S/rel)==pin)
 for rel,pin in c.closure().items():check('exact canonical source closure '+rel,h(R/rel)==pin)
 for rel,pin in WATCH.items():check('pinned evidence still unchanged '+rel,h(R/rel)==pin)
 for row in [x['actual'] for x in selector_rows]+[x['actual'] for x in base_rows]:check('model file stat unchanged at end '+row['path'],fingerprint(Path(row['path']))=={k:row[k] for k in ('bytes','mtime_ns','inode','device')})
 ee.unchanged();after,after_sha=stable_state();after_gate=assert_not_admitted(after,'after');check('unchanged relevant root admission state',before_gate==after_gate)
 check('no forbidden audit actions attempted',BLOCKED==[])
 evidence=write('checked_metadata.json',{'gateway_evidence':ee.hashes,'own_pinned_refs':WATCH,'actual_P_inputs':actual,'publications':pubs,'state_before_sha256':before_sha,'state_after_sha256':after_sha,'before_gate':before_gate,'after_gate':after_gate})
 weights=write('checkpoint_byte_verification.json',{'status':'passed','server_only_streamed_bytes':True,'model_deserialized':False,'model_loaded':False,'selectors':selector_rows,'official_base':{'root':str(base),'repository':strict['repository'],'revision':strict['revision'],'total_bytes':strict['total_bytes'],'files':base_rows},'weight_paths_read':sorted(WEIGHT_READS),'retained_server_only':True})
 report={'schema':'formal_main_v2','kind':'object256s23_source_control_post_actual_readiness_independent_review','status':'passed','blockers':[],'utc':datetime.now(timezone.utc).isoformat(),'entrypoint_sha256':h(Path(__file__)),'authorization':root['authorization'],'root_pre_execution':root['root_check'],'root_readiness_receipt':ROOTREF,'readiness':root['readiness'],'prepared_invocation':root['prepared_invocation'],'reservation':root['reservation'],'explicit_source_control':descriptor,'scientific_plan':aa['scientific_plan'],'effective_plan':aa['plan'],'action_execution_contract':inv['action_execution_contract'],'plan_sha256':effective['plan_sha256'],'method_ids':METHODS,'suite':'libero_object','allowed_stages':['development'],'expected_trials':200,'unique_development_initial_states':100,'actual_full_P_wrapper_verifications':1,'actual_NativeIO_preflight_passed':True,'selected_checkpoint_bytes_verified':True,'official_base_all_25_files_bytes_verified':True,'checkpoint_byte_verification':weights,'actual_GPU_runtime_chain_verified':False,'new_GPU_submissions':[],'new_trials':0,'production_metadata_source_chain_verified':True,'reservation_inactive_at_audit':True,'no_registered_duplicate':True,'no_existing_invocation_or_output':True,'state_not_modified_by_audit':True,'live_state_bytes_unchanged_during_audit':before_sha==after_sha,'root_reported_state_sha256':root['state_sha256'],'state_before_sha256':before_sha,'state_after_sha256':after_sha,'controller_live_capacity_not_queried':True,'model_loaded':False,'model_deserialized':False,'final_state_values_read':False,'final_release':False,'all173_frozen_files_unchanged':True,'all_pair_GPU_seconds':58917,'retained_failed_GPU_seconds':84,'checks':CHECKS,'evidence':evidence,'limitations':['Metadata/source and server byte verification only; no newly executed Object23 GPU runtime chain or trial result.','Root must still verify live lease/capacity/pending and activate exact inactive reservation under lock/CAS before the one allowed submission.','No automatic retry or final release; any uncertain submit or runtime failure remains fail-closed.'],'elapsed_seconds':time.monotonic()-started}
 rr=write('independent_review.json',report);print(json.dumps({'status':'passed','report':rr,'checks':len(CHECKS),'actual_full_P_wrapper_verifications':1,'selected_checkpoint_bytes_verified':True,'official_base_bytes':strict['total_bytes'],'actual_GPU_runtime_chain_verified':False}),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  if OUT.exists():write('failure.json',{'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'checks':CHECKS,'blocked':BLOCKED})
  raise
