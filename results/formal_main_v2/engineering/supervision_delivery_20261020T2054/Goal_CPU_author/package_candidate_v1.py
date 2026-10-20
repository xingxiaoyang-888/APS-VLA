from pathlib import Path
import json,hashlib,tarfile,time
D=Path(__file__).parent;R=D.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
files=[]
for p in sorted((D/'CPU_attempt01').rglob('*')):
 if p.is_file():
  assert not p.is_symlink();files.append({'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
archive=D/'CPU_evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for row in files:tar.add(D/row['path'],arcname=row['path'],recursive=False)
with tarfile.open(archive,'r:gz') as tar:
 members=tar.getmembers();assert len(members)==len(files)
 for member,row in zip(members,files):
  assert member.isfile() and member.name==row['path'] and member.size==row['bytes']
  assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==row['sha256']
write(D/'CPU_evidence_archive_index.json',{'kind':'lossless_synthetic_CPU_evidence_archive','archive':{'path':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive)},'raw_files_preserved_on_server':True,'raw_bytes':sum(r['bytes'] for r in files),'members':files,'real_GPU_or_final_values':False})
(D/'transport').mkdir()
for n in ['goal_cpu_gate_AST_sourcefreeze_20261020T2054.jsonl','goal_cpu_gate_author_CPU_v1_20261020T2054.jsonl']:
 src=R/'results/formal_main_v2/control_transport'/n;target=D/'transport'/n
 with target.open('xb') as f:f.write(src.read_bytes())
selected=[p for p in D.iterdir() if p.is_file() and p.name!='delivery_manifest.json']+list((D/'transport').iterdir())
items=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(selected)]
manifest={'kind':'Goal_CPU_paired_input_gate_candidate_delivery','root':str(D.relative_to(R)),'files':items,'file_count':len(items),'bytes':sum(x['bytes'] for x in items),'status':'CPU_candidate_only_awaiting_independent_audit','production_entrypoint_integrated':False,'P_runtime_source_closure_verified':False,'real_environment_validation_completed':False,'single_attempt_GPU_authorization_granted':False,'old_history_exactly_replayed':False,'old200_accepted':False,'new_Goal_science_HOLD':True,'GPU_runs':0,'scientific_trials_added':0,'final_release':False,'CPU_original_paths_in_archive_index':str((D/'CPU_evidence_archive_index.json').relative_to(R))}
write(D/'delivery_manifest.json',manifest)
print(json.dumps({'manifest':str((D/'delivery_manifest.json').relative_to(R)),'sha256':sha(D/'delivery_manifest.json'),'file_count':len(items),'bytes':manifest['bytes'],'raw_CPU_files':len(files)}))
