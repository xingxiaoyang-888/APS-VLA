from pathlib import Path
from datetime import datetime,timezone
import os,json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('goal_io_decision_0110_ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');assert before=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'
 target=R/'results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01';assert not target.exists() and target.resolve()==target and not any(v.is_symlink() for v in [target,*target.parents])
 disks={str(p):{'available_bytes':os.statvfs(p).f_bavail*os.statvfs(p).f_frsize,'filesystem_block_bytes':os.statvfs(p).f_frsize,'known_local_write_permissions':os.access(p,os.W_OK)} for p in [R,P]}
 out={'schema':'formal_main_v2','kind':'root_fixed_Goal_raw_observation_storage_choice','status':'engineering_mapping_adopted_runtime_and_GPU_HOLD','utc':datetime.now(timezone.utc).isoformat(),'base_design':{'path':'results/formal_main_v2/preflight/heartbeat_20261021T0758/Goal_prospective_root_decision.json','sha256':'06911f2ba90ffa9e7df233e0793c0989e0d15edf260b18a2fa2fb963ef0912d7'},'root_observation_blob_directory':str(target),'metadata_runtime_root':str(P/'results/formal_main_v2/engineering/goal_full200_20261021T0110/attempt01'),'mapped_content':'Only five current observation components as content-addressed development blobs; sim/RNG/control/ledger metadata retain P exact attempt root','unchanged_science':True,'unchanged_raw_content_and_capture_timing':True,'no_legacy_deletion_or_move':True,'symlinks_allowed':False,'reuse_existing_output_allowed':False,'capacity_observation':disks,'capacity_scope':'statvfs availability only; node permissions/quota/write failure remain runtime fail-closed checks, not an asserted unlimited quota','requirements':['Separate conservative upper bounds for P metadata and R observation blobs','Actual P static verification plus compute-node pre-execution realpath owner writable capacity and exclusive fresh output checks','Any capacity or write exception terminates attempt and preserves raw prefix/cost; no silent record drop or automatic retry','Only exact allowlisted nonweight volumes published to Git; no loose bin glob add'],'target_created':False,'GPU_submission_authorized':False,'new_GPU_jobs':[],'scientific_trials_added':0,'state_unchanged':True,'final_release':False}
 assert h(R/out['base_design']['path'])==out['base_design']['sha256']
 p=R/B/'Goal_blob_storage_root_decision.json'
 with p.open('x') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps({'status':out['status'],'receipt':str(p.relative_to(R)),'sha256':h(p),'capacity':disks}))
