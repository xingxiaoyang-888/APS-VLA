"""All-five conservative two-root capacity; one own attempt claim, no deletion."""
from pathlib import Path
import os,hashlib,json
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
KEYS=('libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41')
MAX_CAPTURE_EVENTS=21032
MAX_OBSERVATION_BYTES=393288
MAX_RNG_BLOB_BYTES=65536
MAX_SIM_BYTES_PER_CAPTURE=8192
MAX_CAPTURE_EVENT_BYTES=16384
MAX_GATE_EVENTS=68032
MAX_GATE_EVENT_BYTES=16384
MAX_RESULT_ROW_BYTES=4194304
MAX_CLEANUP_ROW_BYTES=65536
MAX_START_ROW_BYTES=4096
MAX_RUNTIME_LOG_BYTES=2147483648
BOOTSTRAP_LOG_BUDGET_BYTES=4294967296
P_UPPER_BYTES=200*(MAX_RESULT_ROW_BYTES+MAX_CLEANUP_ROW_BYTES+MAX_START_ROW_BYTES)+2*16777216+16777216+16777216+1024*65536+16777216
P_MARGIN_BYTES=134217728
R_UPPER_BYTES=MAX_CAPTURE_EVENTS*(MAX_OBSERVATION_BYTES+MAX_RNG_BLOB_BYTES+MAX_SIM_BYTES_PER_CAPTURE+MAX_CAPTURE_EVENT_BYTES)+MAX_GATE_EVENTS*MAX_GATE_EVENT_BYTES+2*MAX_RUNTIME_LOG_BYTES+BOOTSTRAP_LOG_BUDGET_BYTES
R_MARGIN_BYTES=1073741824
P_REQUIRED_BYTES=P_UPPER_BYTES+P_MARGIN_BYTES
R_REQUIRED_BYTES=R_UPPER_BYTES+R_MARGIN_BYTES
assert (P_UPPER_BYTES,P_REQUIRED_BYTES,R_UPPER_BYTES,R_REQUIRED_BYTES)==(1003782144,1137999872,19871439680,20945181504)
OBS_SCHEMA={'agentview_image':('uint8',[256,256,3],196608),'robot0_eye_in_hand_image':('uint8',[256,256,3],196608),'robot0_eef_pos':('float64',[3],24),'robot0_eef_quat':('float64',[4],32),'robot0_gripper_qpos':('float64',[2],16)}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def paths(key):
 require(key in KEYS,'exact five capacity scope')
 return R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01',P/'results/formal_main_v2/execution/goal_remaining5_v1'/key/'attempt01'
def ancestor(path):
 path=Path(path);require(path.is_absolute() and path.resolve()==path,'exact absolute storage path required')
 for node in [path,*path.parents]:require(not node.is_symlink(),'storage symlink forbidden')
 q=path
 while not q.exists():q=q.parent
 require(q.is_dir() and q.stat().st_uid==os.getuid() and os.access(q,os.W_OK|os.X_OK),'storage ancestor ownership/write permissions differ')
 return q
def inspect(path,required):
 q=ancestor(path);s=os.statvfs(q);return {'path':str(path),'existing_ancestor':str(q),'owner_uid':q.stat().st_uid,'free_bytes':s.f_bavail*s.f_frsize,'required_bytes':required,'st_dev':q.stat().st_dev,'symlink':False,'writable':True}
def verify_storage(ctx,*,must_be_fresh=True,aggregate_pair_keys=KEYS):
 require(type(must_be_fresh) is bool and tuple(aggregate_pair_keys)==KEYS,'whole five budget cannot be narrowed')
 require(ctx.pair_key in KEYS and (ctx.RAW,ctx.OUTPUT)==paths(ctx.pair_key),'exact context paths required')
 if must_be_fresh:require(not ctx.RAW.exists() and not ctx.OUTPUT.exists(),'own once-only claim already exists')
 probes=[];bydev={}
 for key in KEYS:
  raw,out=paths(key)
  for p,n in ((raw,R_REQUIRED_BYTES),(out,P_REQUIRED_BYTES)):
   row=inspect(p,n);probes.append(row);bydev.setdefault(row['st_dev'],[]).append(row)
 checks=[]
 for dev,rows in sorted(bydev.items()):
  need=sum(v['required_bytes'] for v in rows);free=min(v['free_bytes'] for v in rows)
  require(free>=need,'whole-five conservative filesystem capacity insufficient')
  checks.append({'st_dev':dev,'required_bytes':need,'free_bytes':free})
 own={v['path']:v for v in probes}
 return {'version':'goal-remaining5-dual-root-budget-v1','aggregate_pair_keys':list(KEYS),'raw':own[str(ctx.RAW)],'local':own[str(ctx.OUTPUT)],'all_paths':probes,'filesystem_checks':checks,'raw_upper_bytes':R_UPPER_BYTES,'local_upper_bytes':P_UPPER_BYTES,'R_required_per_pair':R_REQUIRED_BYTES,'P_required_per_pair':P_REQUIRED_BYTES,'R_aggregate_required':5*R_REQUIRED_BYTES,'P_aggregate_required':5*P_REQUIRED_BYTES,'no_dedup_credit':True,'no_expected_release_credit':True,'quota_not_proven':True,'filesystem_space_can_change_after_check':True,'exclusive_claim_required_at_execution':True,'new_storage_paths_created':False}
def claim_raw(ctx):
 verify_storage(ctx)
 ctx.RAW.parent.mkdir(parents=True,exist_ok=True);ancestor(ctx.RAW.parent);ctx.RAW.mkdir(exist_ok=False)
 require(ctx.RAW.stat().st_uid==os.getuid() and ctx.RAW.resolve()==ctx.RAW,'exclusive raw claim')
 proof={'version':'goal-remaining5-raw-exclusive-claim-v1','pair_key':ctx.pair_key,'path':str(ctx.RAW),'pid':os.getpid(),'job_id':os.environ['SLURM_JOB_ID'],'purpose':'five raw development observations, passive simulator/RNG payload, observer/gate journals and own runtime logs for this attempt only','old200_HOLD':True,'new_scientific_trials_accepted':0}
 with (ctx.RAW/'claim.json').open('x') as f:json.dump(proof,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return proof
