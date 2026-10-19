from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,importlib.util,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin,(rel,sha(p))
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':rel,'sha256':sha(p)}
def ref(rel):return {'path':rel,'sha256':sha(R/rel)}
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_terminal_controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=sha(statepath);s=json.loads(statepath.read_text());a=s['autonomous_training_v1'];p=s['formal_main_progress']
 owner=json.loads((R/'results/formal_main_v2/autonomous_training/run_v1/owner.json').read_text())
 assert owner['owner_id']==a['owner_id'] and owner['coordinator_job_id']=='3034538'
 with (R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock').open('a+b') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:lease=True
  else:fcntl.flock(f,fcntl.LOCK_UN);lease=False
 assert lease,'Controller lease not held'
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,owner['coordinator_job_id'])
 assert not cap['unknown'] and not cap['findings'],cap
 assert obs['rows'][owner['coordinator_job_id']]['status']=='RUNNING'
 formal_ids={str(j['job_id']) for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'}
 cost=sum(r['gpus']*r['elapsed_seconds'] for jid,r in obs['rows'].items() if jid in formal_ids)
 overview={'utc':datetime.now(timezone.utc).isoformat(),'controller_owner':owner,'lease_held':lease,'capacity':cap,'formal_allocated_GPU_seconds':cost,'formal_allocated_GPU_hours':cost/3600,'trained_arms_machine_and_prior':p['trained_arms'],'root_independent_completed_arms':2*len(p['completed_training_pairs']),'root_independent_updates':p['root_and_independent_reviewed_arm_updates'],'machine_prior_updates':p['machine_and_prior_verified_arm_updates'],'state_sha256':before,'slurm':obs,'pending_submission':s.get('pending_submission'),'autonomous_pending_submission':a.get('pending_submission'),'last_tick_utc':a.get('last_tick_utc'),'root_submission_hold':a.get('root_submission_hold'),'reserved_GPU_slots':a.get('reserved_GPU_slots',0)}
 obref=write(B+'/initial_observation.json',overview)
 print(json.dumps({'observation':obref,'GPU_jobs':len(cap['occupied']),'formal_GPU_hours':cost/3600,'trained_machine':p['trained_arms'],'root_independent_arms':2*len(p['completed_training_pairs'])}),flush=True)
 pull=mod('scripts/pull_formal_results.py','b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','root_terminal_puller')
 report,path=pull.pull(['3028460','3039258'],timeout=300)
 assert report['status']=='verified_nonweight_snapshot'
 pullref=ref(path.relative_to(R).as_posix());write(B+'/cuda_recovery_pull.json',{'pull':pullref,'files':len(report['files']),'job_ids':['3028460','3039258'],'weights_copied':False})
 print(json.dumps({'CUDA_pull':pullref,'files':len(report['files'])}),flush=True)
 assert sha(R/'.local/cuda_startup_recovery_0840/startup_failure_evidence.py')=='c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'
 reviewer=mod('.local/cuda_startup_recovery_0840/review_formal_segment_startup.py','a06069b9139d24e9ac35944559fa0918afce62a4c58d57adee63ace2c3776f4a','root_cuda_terminal_reviewer')
 inv='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
 result=reviewer.review('3039258',source_inventory=inv,pull_receipt=pullref['path'],verify_server_resume=True,root=R)
 rp=result['output_relative']+'/segment_reviews/3039258.json'
 assert result['completed_by_arm']=={'A':500,'B':500}
 write(B+'/cuda_root_terminal.json',{'root_review':ref(rp),'pull':pullref,'completed_by_arm':result['completed_by_arm'],'pair_allocated_GPU_seconds':result['pair_allocated_gpu_seconds'],'original_target_recovered':True,'continuous_5000_admitted':False,'history_retained':True,'optimizer_rng_content_deserialized':False})
 print(json.dumps({'CUDA_root_review':ref(rp),'completed':result['completed_by_arm'],'pair_GPU_seconds':result['pair_allocated_gpu_seconds']}),flush=True)
 complete=a['completed_pairs']['libero_object_k256_seed41']
 out=json.loads((R/complete['machine_output']['path']).read_text());assert sha(R/complete['machine_output']['path'])==complete['machine_output']['sha256']
 candidates=[]
 for x in out['evidence_refs']:
  if x['path'].startswith('results/formal_main_v2/pulls/') and x['path'].endswith('/receipt.json'):
   v=json.loads((R/x['path']).read_text())
   if '3034570' in {str(j['job_id']) for j in v['selected_jobs']}:
    assert sha(R/x['path'])==x['sha256'];candidates.append(x)
 assert len(candidates)==1
 normal=mod('scripts/review_formal_segment.py','566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790','root_normal_terminal_reviewer')
 result=normal.review('3034570',source_inventory=inv,pull_receipt=candidates[0]['path'],verify_server_resume=True,root=R)
 assert result['completed_by_arm']=={'A':5000,'B':5000}
 rp=result['output_relative']+'/segment_reviews/3034570.json'
 checks=[]
 pairroot=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k256/seed41')
 for arm in ['A','B']:
  receipt=json.loads((R/result['output_relative']/arm/'deployment_receipt.json').read_text())
  assert receipt['training_complete'] and receipt['completed_updates']==5000
  assert [e['update'] for e in receipt['evaluations']]==list(range(0,5001,500))
  target=pairroot/arm/'best.pt';st=target.stat();digest=c.file_sha(target)
  assert digest==receipt['checkpoint_sha256'] and st==target.stat()
  checks.append({'arm':arm,'path':str(target),'sha256':digest,'bytes':st.st_size,'selected_update':receipt.get('selected_update'),'validation_metric':receipt.get('validation_metric')})
 sr=write(B+'/3034570_selected_server.json',{'status':'verified_actual_server_bytes','job_id':'3034570','root_review':ref(rp),'checks':checks,'weights_copied':False,'optimizer_rng_deserialized':False})
 write(B+'/3034570_root_terminal.json',{'root_review':ref(rp),'selected_server':sr,'machine_original_outcome':complete['machine_output'],'pull':candidates[0],'completed_by_arm':result['completed_by_arm'],'pair_allocated_GPU_seconds':result['pair_allocated_gpu_seconds'],'independent_review_pending':True})
 assert sha(statepath)==before,'Registry changed while root holds writer lock'
 print(json.dumps({'normal_root_review':ref(rp),'completed':result['completed_by_arm'],'selected':sr,'state_unchanged':True}),flush=True)
