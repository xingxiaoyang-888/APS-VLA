from pathlib import Path
import fcntl,hashlib,json,os
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T1825'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def copy(src,dst,pin=None):
 safe(src);safe(dst);raw=src.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert pin is None or pin==sha;assert len(raw)<90*1024*1024
 assert src.suffix.lower() not in ['.pt','.pth','.safetensors','.ckpt']
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==raw
 else:
  with dst.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return {'source':str(src.relative_to(R)),'path':str(dst.relative_to(R)),'sha256':sha,'bytes':len(raw)}
packages=[('Goal_prefix58_terminal','.local/goal_prefix58_terminal_20261020T1825/delivery_manifest.json','249fb309d591d86dfc8f0e68d6f3045a55059bcdb0e63158a461686ee4f480b8')]
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);state=R/'results/experiment_supervisor/state.json';before=h(state);rows=[]
 for label,rel,pin in packages:
  mp=safe(R/rel);assert h(mp)==pin;v=json.loads(mp.read_bytes());rows.append(copy(mp,E/label/'delivery_manifest_original.json',pin))
  for item in v['files']:
   src=(R/item['source']) if 'source' in item else ((R/item['path']) if item['path'].startswith('.local/') else mp.parent/item['path'])
   sub=src.relative_to(mp.parent) if src.is_relative_to(mp.parent) else Path('_external')/src.relative_to(R)
   rows.append(copy(src,E/label/sub,item['sha256']))
 for p in sorted((R/'.local').glob('*20261020T1825*.py')):rows.append(copy(p,E/'root_helpers'/p.name))
 # Retain the rejected transport typo as an operational failure; runner rejected before opening the entrypoint.
 err=B/'transport_bundle_typo_rejected.json'
 if not err.exists():err.write_text(json.dumps({'schema':'formal_main_v2','status':'rejected_before_entrypoint','entrypoint':'.local/publish_collect_plans_20261020T1825.py','error':'ValueError: bundle SHA missing','cause':'malformed copied bundle SHA argument; rejected by unchanged transport verify_bundle','entrypoint_executed':False,'state_changed':False,'GPU_jobs':0,'repaired_using_exact_registered_bundle_sha256':'3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'},sort_keys=True,indent=2)+'\n')
 assert h(state)==before
 out=B/'sealed_packages_archive_Goal_terminal.json';receipt={'schema':'formal_main_v2','status':'nonweight_packages_archived_exactly','rows':rows,'file_count':len(rows),'bytes':sum(x['bytes'] for x in rows),'state_sha256':before,'state_unchanged':True,'weights_copied':False,'final_values_read':False,'utc':datetime.now(timezone.utc).isoformat()}
 with out.open('x') as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'receipt':str(out.relative_to(R)),'sha256':h(out),'files':len(rows),'bytes':receipt['bytes']}))
