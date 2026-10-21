from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=D/'final_independent_review.json'
assert h(review)=='28ecacb7850f711ecd8b11e38e1a33f15eace9034c278862801ec447c6465ce4'
value=json.loads(review.read_bytes())
assert value['status']=='passed' and value['blockers']==[] and value['GPU_execution_authorized'] is False and value['production_admitted'] is False
td=D/'transport';td.mkdir()
n='goal_dispatch_v2_independent_20261021T0110.jsonl'
src=R/'results/formal_main_v2/control_transport'/n
lines=[json.loads(x) for x in src.read_text().splitlines() if x]
assert lines[-1].get('returncode',lines[-1].get('exit_code'))==0,lines[-1]
with (td/n).open('xb') as f:f.write(src.read_bytes())
assert h(td/n)==h(src)
files=[]
for p in sorted(D.rglob('*')):
 assert not p.is_symlink()
 if p.is_file():files.append(dict(path=p.relative_to(D).as_posix(),bytes=p.stat().st_size,sha256=h(p)))
manifest=dict(schema='formal_main_v2',kind='Goal_full200_dispatch_independent_delivery_manifest',source_root=D.relative_to(R).as_posix(),file_count=len(files),files=files,review=dict(path='final_independent_review.json',sha256=h(review)),GPU_execution_authorized=False,production_admitted=False)
p=D/'Goal_dispatch_manifest.json'
with p.open('x') as f:json.dump(manifest,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(manifest=str(p.relative_to(R)),sha256=h(p),file_count=len(files),review_sha256=h(review))))
