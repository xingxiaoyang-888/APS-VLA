from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','spatialpublish2130c')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=json.loads(sp.read_text());assert state['pending_submission'] is None
 pr='results/formal_main_v2/pulls/20261019T213629Z_4f95d3193797/receipt.json';assert h(R/pr)=='046d94aee021b751d49061543d84e935f4f0e674000476a25f2c4e03e69e73fa'
 ir='.local/cuda_recovery_independent_0943/ownership_patch_independent_review.json';assert h(R/ir)=='edff54b1d4ff8ace87251378b882190155f7db5b26bf09bf5e360c0bec34abba'
 ind=json.loads((R/ir).read_text());assert ind['status']=='passed_CPU_review' and ind['tests']['final_passed']==33 and ind['tests']['final_failed']==0
 assert h(R/'.local/cuda_terminal_review_0943/startup_failure_evidence.py')=='c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'
 m=mod('.local/cuda_terminal_review_0943/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4','spatialpublish2130reviewer')
 v=m.review('3043399',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=pr,verify_server_resume=True,root=R)
 assert v['status']=='passed' and v['completed_by_arm']=={'A':1500,'B':1500} and v['pair_allocated_gpu_seconds']==11958
 rr=ref(v['output_relative']+'/segment_reviews/3043399.json')
 out=dict(root_review=rr,source_correction_independent=ref(ir),pull=ref(pr),completed_by_arm=v['completed_by_arm'],original_target_1500_recovered=True,initial_resume_update=1000,initial_sample_cursor=8000,new_sample_cursor=12000,checkpoint_contents_deserialized=False,resume_file_hashes_verified=True,frozen_core_revalidates_optimizer_RNG_cursor_on_next_resume=True,continuous_5000_admitted=False,failed_records_retained=True,failed_GPU_seconds=73,recovery_GPU_seconds=3401,pair_GPU_seconds=11958,new_GPU_jobs=0,independent_actual_terminal_review_pending=True)
 dest=B+'/3043399_root_terminal.json'
 with (R/dest).open('x') as f:json.dump(out,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 assert h(sp)==before
 print(json.dumps(dict(root_review=rr,root_summary=ref(dest),state_unchanged=True)))
