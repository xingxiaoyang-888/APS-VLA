"""Exact full200 two-filesystem storage contract; no path discovery or cleanup."""
from pathlib import Path
import os,hashlib,json
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
STAGE='goal_full200_20261021T0110'
RAW_ROOT=R/'results/formal_main_v2/raw_runtime'/STAGE/'attempt01'
OUTPUT=P/'results/formal_main_v2/engineering'/STAGE/'attempt01'
MAX_CAPTURE_EVENTS=21032
MAX_OBSERVATION_BYTES=393288
MAX_RNG_BLOB_BYTES=65536
MAX_SIM_BYTES_PER_CAPTURE=8192
MAX_CAPTURE_EVENT_BYTES=16384
MAX_GATE_EVENT_BYTES=16384
MAX_GATE_EVENTS=68032
# No deduplication saving assumed. Blobs are raw; arrays are never altered.
RAW_UPPER_BYTES=MAX_CAPTURE_EVENTS*MAX_OBSERVATION_BYTES
LOCAL_UPPER_BYTES=MAX_CAPTURE_EVENTS*(MAX_RNG_BLOB_BYTES+MAX_SIM_BYTES_PER_CAPTURE+MAX_CAPTURE_EVENT_BYTES)+MAX_GATE_EVENTS*MAX_GATE_EVENT_BYTES+1073741824
MARGIN_BYTES=1073741824
RAW_REQUIRED_BYTES=RAW_UPPER_BYTES+MARGIN_BYTES
LOCAL_REQUIRED_BYTES=LOCAL_UPPER_BYTES+MARGIN_BYTES
OBS_SCHEMA={'agentview_image':('uint8',[256,256,3],196608),'robot0_eye_in_hand_image':('uint8',[256,256,3],196608),'robot0_eef_pos':('float64',[3],24),'robot0_eef_quat':('float64',[4],32),'robot0_gripper_qpos':('float64',[2],16)}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def ancestor(path):
 path=Path(path);require(path.is_absolute() and path.resolve()==path,'exact absolute storage path required')
 for node in [path,*path.parents]:require(not node.is_symlink(),'storage symlink forbidden')
 q=path
 while not q.exists():q=q.parent
 require(q.is_dir() and q.stat().st_uid==os.getuid() and os.access(q,os.W_OK|os.X_OK),'storage ancestor ownership/write permissions differ')
 return q
def check_free(path,required):
 q=ancestor(path);s=os.statvfs(q);free=s.f_bavail*s.f_frsize
 require(free>=required,'insufficient exclusive-attempt capacity: '+str(path))
 return {'path':str(path),'existing_ancestor':str(q),'owner_uid':q.stat().st_uid,'free_bytes':free,'required_bytes':required,'st_dev':q.stat().st_dev,'symlink':False,'writable':True}
def verify_storage(*,must_be_fresh=True):
 require(type(must_be_fresh) is bool,'explicit freshness required')
 if must_be_fresh:require(not RAW_ROOT.exists() and not OUTPUT.exists(),'one-shot output/raw claim already exists')
 a=check_free(RAW_ROOT,RAW_REQUIRED_BYTES);b=check_free(OUTPUT,LOCAL_REQUIRED_BYTES)
 if a['st_dev']==b['st_dev']:
  require(min(a['free_bytes'],b['free_bytes'])>=RAW_REQUIRED_BYTES+LOCAL_REQUIRED_BYTES,'same filesystem needs combined reservation')
 return {'version':'goal-full200-two-root-storage-v1','raw':a,'local':b,'raw_upper_bytes':RAW_UPPER_BYTES,'local_upper_bytes':LOCAL_UPPER_BYTES,'no_dedup_credit':True,'filesystem_space_can_change_after_check':True,'exclusive_claim_required_at_execution':True,'new_storage_paths_created':False}
def claim_raw():
 # Called exactly once by authorized entry, after Slurm/ACK/locks; never preflight.
 verify_storage()
 RAW_ROOT.parent.mkdir(parents=True,exist_ok=True)
 ancestor(RAW_ROOT.parent)
 RAW_ROOT.mkdir(exist_ok=False)
 require(RAW_ROOT.stat().st_uid==os.getuid() and RAW_ROOT.resolve()==RAW_ROOT,'raw exclusive claim identity')
 proof={'version':'goal-full200-raw-exclusive-claim-v1','path':str(RAW_ROOT),'pid':os.getpid(),'job_id':os.environ['SLURM_JOB_ID'],'purpose':'only raw five-component development observations for this new attempt','old200_HOLD':True,'new_scientific_trials_accepted':0}
 with (RAW_ROOT/'claim.json').open('x') as f:json.dump(proof,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return proof
