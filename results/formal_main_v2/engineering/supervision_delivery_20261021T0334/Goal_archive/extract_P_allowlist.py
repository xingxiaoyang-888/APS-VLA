from pathlib import Path
import json, hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_terminal_archive_20261021T0334'
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
A=P/'results/formal_main_v2/engineering/goal_full200_20261021T0110/attempt01'
p=D/'inventory.json'; raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='db4d8a05cd7f21af5aac0687d2190297cd571eb1a6ffc83eb74d235d53eb7ac1'
inv=json.loads(raw)
assert inv['status']=='exact_event_allowlist_and_original_read_blob_verified'
items=[]
for m in inv['members']:
    if m['restore_root']!='P': continue
    assert m['namespace'] in ('P_passive','P_attempt_metadata')
    q=Path(m['source'])
    assert q.is_relative_to(A)
    items.append({'path':m['restore_relative'],'relative':q.relative_to(A).as_posix(),'bytes':m['bytes'],'sha256':m['sha256'],'kind':m['namespace'],'source':str(q)})
assert len(items)==15535
v={'schema':'formal_main_v2','kind':'Goal3054717_exact_P_terminal_pull_allowlist','status':'verified_original_event_references_and_bytes','job_id':'3054717','source_root':str(P),'attempt_root':str(A),'inventory':{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()},'file_count':len(items),'total_bytes':sum(m['bytes'] for m in items),'blob_count':15522,'metadata_count':13,'R_observation_blobs_already_in_R':True,'scientific_admission':False,'new_trials':0,'new_GPU_jobs':0,'members':items}
out=D/'P_terminal_pull_allowlist.json'
with out.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
print(json.dumps({'path':out.relative_to(R).as_posix(),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'file_count':len(items),'total_bytes':v['total_bytes']}))
