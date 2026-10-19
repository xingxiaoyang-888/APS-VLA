from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':rel,'sha256':sha(p)}
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','cuda_publish_controller')
irel='.local/cuda_recovery_independent_0943/ownership_patch_independent_review.json'
assert sha(R/irel)=='edff54b1d4ff8ace87251378b882190155f7db5b26bf09bf5e360c0bec34abba'
ind=json.loads((R/irel).read_text());assert ind['kind']=='startup_pull_ownership_independent_CPU_review' and ind['status']=='passed_CPU_review' and ind['tests']['final_passed']==33 and ind['tests']['final_failed']==0
reviewer=mod(ind['candidate']['path'],ind['candidate']['sha256'],'cuda_published_terminal_reviewer')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=sha(R/'results/experiment_supervisor/state.json')
 pr='results/formal_main_v2/pulls/20261019T095542Z_e5d54e39d3ae/receipt.json';assert sha(R/pr)=='8cf02df4314a103db61824fbf64a238994a1572757bc443682ab6d5d319be0e8'
 result=reviewer.review('3039258',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=pr,verify_server_resume=True,root=R)
 assert result['status']=='passed' and result['completed_by_arm']=={'A':500,'B':500} and result['pair_allocated_gpu_seconds']==6596
 rel=result['output_relative']+'/segment_reviews/3039258.json'
 rr=write(B+'/cuda_root_terminal.json',{'root_review':{'path':rel,'sha256':sha(R/rel)},'source_correction_independent':{'path':irel,'sha256':sha(R/irel)},'pull':{'path':pr,'sha256':sha(R/pr)},'completed_by_arm':result['completed_by_arm'],'original_target_500_recovered':True,'actual_prior_optimizer_RNG_loaded':False,'startup_before_training_failure_restarted_from_authorized_fresh_zero':True,'checkpoint_contents_deserialized':False,'resume_file_hashes_verified':True,'frozen_core_revalidates_optimizer_RNG_cursor_on_next_resume':True,'continuous_5000_admitted':False,'failed_records_retained':True,'failed_GPU_seconds':84,'recovery_GPU_seconds':6512,'pair_GPU_seconds':6596,'new_GPU_jobs':0})
 assert sha(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps({'root_review':{'path':rel,'sha256':sha(R/rel)},'root_summary':rr,'state_unchanged':True}),flush=True)
