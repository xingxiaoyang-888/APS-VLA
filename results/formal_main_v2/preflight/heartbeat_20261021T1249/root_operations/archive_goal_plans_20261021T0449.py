from pathlib import Path
import json,hashlib,fcntl,os,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_plans_20261021T0449'
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261021T0449/Goal_plans_author'
M=D/'delivery_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def direct(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def write(p,data):
 direct(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert sha(M)=='321e64ca6aa130230c5949bab54b1bcd52f4ef0fec75ad70f2f4161ef1ea683e'
m=json.loads(M.read_bytes());assert m['file_count']==len(m['files'])==81
pending=[];seen=set()
for row in m['files']:
 p=direct(R/row['path']);assert D in p.parents and p.suffix in ['.py','.md','.json','.jsonl']
 assert str(p) not in seen;seen.add(str(p))
 raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 dst=E/p.relative_to(D);assert not dst.exists()
 pending.append((dst,raw,row))
assert not E.exists()
with (R/'results/experiment_supervisor/.writer.lock').open('r+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 for dst,raw,row in pending:write(dst,raw)
 write(E/'delivery_manifest_original.json',M.read_bytes())
 source_map={'kind':'exact_original_author_CPU_package_archive','source_manifest':{'path':str(M.relative_to(R)),'sha256':sha(M)},'files':[{'source':row['path'],'destination':str(dst.relative_to(R)),'sha256':row['sha256'],'bytes':len(raw)} for dst,raw,row in pending],'original_failure_candidates_preserved':True,'new_scientific_trials':0,'actual_P_runtime_verification':False}
 write(E/'source_map.json',enc(source_map))
print(json.dumps({'status':'archived_exact_author_package','files':81,'bytes':sum(len(raw) for _,raw,_ in pending),'manifest':str((E/'delivery_manifest_original.json').relative_to(R)),'manifest_sha256':sha(M)},sort_keys=True))
