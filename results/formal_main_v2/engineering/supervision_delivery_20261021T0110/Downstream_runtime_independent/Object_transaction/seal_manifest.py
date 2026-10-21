from pathlib import Path
import json,hashlib
D=Path(__file__).parent
r=json.loads((D/'independent_review.json').read_bytes());assert r['status']=='passed_original_ACK_single_release_transaction' and r['check_count']==961 and r['blockers']==[]
rows=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='Object_transaction_manifest.json':
  assert not p.is_symlink();rows.append({'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
m={'schema':'formal_main_v2','kind':'Object_actual_transaction_independent_delivery','file_count':len(rows),'files':rows,'state_sha256':r['state_sha256'],'job_id':'3054409','review_sha256':hashlib.sha256((D/'independent_review.json').read_bytes()).hexdigest(),'Slurm_queries':0,'new_GPU_submissions':0,'scientific_results_accepted':0,'cost_metadata_note_retained':True}
p=D/'Object_transaction_manifest.json'
with p.open('x') as f:json.dump(m,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'file_count':len(rows),'manifest_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
