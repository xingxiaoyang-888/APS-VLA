from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');O=R/'.local/long64_selected_diagnostics_0830'
L=R/'results/formal_main_v2/control_transport/independent_long64_selected_diagnostics_0830_extract_a1.jsonl'
b=L.read_bytes();records=[json.loads(x) for x in b.splitlines()]
assert records[-1]['returncode']==0
assert records[-1]['source173_and_entrypoint_unchanged'] is True
assert hashlib.sha256((R/'.local/independent_long64_development_0830/manifest.json').read_bytes()).hexdigest()=='e14cb0e58f94254a7511b0ec10bec425b83a139ed41ac5222f6762f277d2e471'
(O/'logs').mkdir(exist_ok=False)
with (O/'logs'/L.name).open('xb') as f:f.write(b)
files=[]
for p in sorted(O.rglob('*')):
    if p.is_file():files.append({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
manifest={'schema':1,'kind':'selected_checkpoint_existing_artifact_diagnostics_manifest','status':'pass','root':str(O.relative_to(R)),'files':files,'file_count':len(files),'total_bytes':sum(f['bytes'] for f in files),'nested_paths_preserved':True,'scientific_source173_unchanged':True,'no_weight_reads_or_GPU_reruns':True,'sealed_previous_directory_unchanged':True}
p=O/'manifest.json'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps({'manifest':{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size},'files':files,'status':'pass'}))
