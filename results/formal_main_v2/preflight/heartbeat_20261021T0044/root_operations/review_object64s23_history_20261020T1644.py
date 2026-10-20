from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_terminal1644_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=sha(statepath)
 assert sha(R/'scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py')=='c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'
 puller=mod('scripts/pull_formal_results.py','b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','root_object64_fullpull')
 report,pp=puller.pull(['3028468','3044017','3044844'],timeout=180)
 assert report['status']=='verified_nonweight_snapshot' and {str(j['job_id']) for j in report['selected_jobs']}=={'3028468','3044017','3044844'}
 write(B+'/Object64s23_complete_history_pull.json',{'receipt':ref(pp),'preserved_failed_job':'3028468','resume_boundary_job':'3044017','terminal_job':'3044844','state_unchanged':sha(statepath)==state_sha})
 normal=mod('scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4','root_object64_startup_review')
 jid='3044844';result=normal.review(jid,source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=pp.relative_to(R).as_posix(),verify_server_resume=True,root=R)
 assert result['completed_by_arm']=={'A':5000,'B':5000} and result['pair_allocated_gpu_seconds']==52868 and '3028468' in result['startup_failure_history']
 rp=R/result['output_relative']/'segment_reviews'/(jid+'.json');checks=[];pairroot=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k64/seed23')
 for arm in ['A','B']:
  receipt=json.loads((R/result['output_relative']/arm/'deployment_receipt.json').read_text())
  assert receipt['training_complete'] and receipt['completed_updates']==5000 and [e['update'] for e in receipt['evaluations']]==list(range(0,5001,500))
  target=pairroot/arm/'best.pt';st=target.stat();digest=c.file_sha(target);assert digest==receipt['checkpoint_sha256'] and st==target.stat()
  checks.append(dict(arm=arm,path=str(target),sha256=digest,bytes=st.st_size,selected_update=receipt['metadata']['update'],validation_metric=receipt['metadata']['validation_metric']))
 sr=write(B+'/'+jid+'_selected_server.json',dict(status='verified_actual_server_bytes',job_id=jid,root_review=ref(rp),checks=checks,weights_copied=False,optimizer_rng_deserialized=False))
 rr=write(B+'/'+jid+'_root_terminal.json',dict(root_review=ref(rp),selected_server=sr,pull=ref(pp),completed_by_arm=result['completed_by_arm'],pair_allocated_GPU_seconds=result['pair_allocated_gpu_seconds'],independent_review_integrated=False,original_plain_reviewer_rejection_retained=True,startup_failure_evidence_preserved=True))
 assert sha(statepath)==state_sha
 print(json.dumps(dict(job_id=jid,status=result['status'],pull=ref(pp),root_review=ref(rp),root_terminal=rr,selected=sr,state_unchanged=True)),flush=True)
