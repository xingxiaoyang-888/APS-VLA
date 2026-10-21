from pathlib import Path
import hashlib,json,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
assert D==R/'.local/goal_terminal_independent_20261021T0334'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
report=read(D/'independent_terminal_review.json')
assert report['status']=='passed_new200_terminal_independent_review' and report['blockers']==[]
assert report['complete_original_scientific_consumer'] and report['old200_HOLD'] and report['other1000_HOLD'] and report['final_sealed']
assert report['new_Slurm_queries_by_auditor']==report['new_GPU_submissions_by_auditor']==report['scientific_trials_accepted_by_auditor']==0
for name in ['goal_terminal_independent_raw_20261021T0334.jsonl','goal_terminal_independent_consume_20261021T0334.jsonl']:
 src=R/'results/formal_main_v2/control_transport'/name
 data=src.read_bytes();rows=[json.loads(x) for x in data.splitlines() if x]
 assert rows and rows[-1]['event']=='control_end' and rows[-1]['returncode']==0 and rows[-1]['source173_and_entrypoint_unchanged']
 dest=D/name
 with dest.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
files=[]
for p in sorted(D.rglob('*')):
 assert not p.is_symlink()
 if p.is_file():
  assert p.name!='delivery_manifest.json'
  files.append({'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)})
m={'schema':'formal_main_v2','kind':'Goal3054717_terminal_independent_delivery_manifest','status':'passed_new200_terminal_independent_review','source_root':str(D),'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'files':files,'independent_report':{'path':'independent_terminal_review.json','sha256':h(D/'independent_terminal_review.json')},'raw_reconstruction':{'path':'raw_reconstruction.json','sha256':h(D/'raw_reconstruction.json')},'raw_blobs_not_copied_by_auditor':True,'source173_verified_by_complete_exact_transport':True,'old200_HOLD':True,'other1000_HOLD':True,'scientific_admission':False,'final_sealed':True}
p=D/'delivery_manifest.json'
with p.open('x') as f:json.dump(m,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'report_sha256':h(D/'independent_terminal_review.json'),'delivery_manifest_sha256':h(p),'file_count':len(files),'bytes':m['total_bytes']}))
