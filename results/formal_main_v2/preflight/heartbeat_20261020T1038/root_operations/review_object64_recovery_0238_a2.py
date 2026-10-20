from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','rootobject0238v2ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_bytes());assert s['pending_submission'] is None
 jobs={str(j['job_id']):j for j in s['registered_jobs']}
 assert jobs['3028468']['status']=='FAILED' and jobs['3028468']['elapsed_seconds']==69 and jobs['3044017']['status']=='COMPLETED' and jobs['3044017']['exit_code']=='0:0' and jobs['3044017']['elapsed_seconds']==5141
 pr=dict(path='results/formal_main_v2/pulls/20261020T024610Z_89cee566247b/receipt.json',sha256='aa509e9edbe2bb52ae1832501b7a4785c43fa579215e67a17f47d80e284ec53b');assert h(R/pr['path'])==pr['sha256']
 reviewer=load('scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4','rootobject0238v2reviewer')
 result=reviewer.review('3044017',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=pr['path'],verify_server_resume=True,root=R)
 assert result['status']=='passed' and result['completed_by_arm']=={'A':500,'B':500} and result['pair_allocated_gpu_seconds']==5210
 rr=ref(result['output_relative']+'/segment_reviews/3044017.json')
 summary=save(B+'/3044017_root_terminal.json',dict(root_review=rr,pull=pr,utc=datetime.now(timezone.utc).isoformat(),completed_by_arm=result['completed_by_arm'],original_target_500_recovered=True,initial_resume_update=0,initial_sample_cursor=0,new_sample_cursor=4000,prior_failure_before_training=True,fresh_initialization_expected=True,old_optimizer_rng_restored_this_job=False,next_continuation_must_restore_optimizer_RNG_cursor=True,checkpoint_contents_deserialized=False,resume_file_hashes_verified=True,continuous_5000_admitted=False,failed_records_retained=True,failed_GPU_seconds=69,recovery_GPU_seconds=5141,pair_GPU_seconds=5210,new_reviewed_arm_updates=1000,new_complete_training_groups=0,new_GPU_jobs=0,independent_actual_terminal_review_pending=True,prior_review_blocked_by_global_pending_transport=ref('results/formal_main_v2/control_transport/heartbeat_0238_object_root_terminal.jsonl')))
 assert h(sp)==before
 print(json.dumps(dict(status='passed_original500_only',root_review=rr,summary=summary,pair_GPU_seconds=5210,state_unchanged=True)))
