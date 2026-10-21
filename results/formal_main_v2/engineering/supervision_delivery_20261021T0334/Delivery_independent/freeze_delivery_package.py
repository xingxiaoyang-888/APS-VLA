from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261021T0334/final'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,data):
 p=D/name;assert not p.exists();p.open('xb').write(data)
state='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d';index='febbc0259aa99fcc2421d108f515de191e9a167a991172af586b0c141989f469'
report=json.loads((D/'final_independent_review.json').read_bytes())
assert report['status']=='passed_actual_delivery' and report['blockers']==[] and report['state_sha256']==state and report['index_sha256']==index
assert h(R/'results/experiment_supervisor/state.json')==state and h(R/'.git/index')==index
journals=[
('actual_integration_independent_20261021T0334_v2.jsonl','53129416ab44e7a25490ffa8368d35a7e8b0bce1d212f5485f65c14d19b3d57d'),
('delivery_finish_push_source_independent_20261021T0334.jsonl','0bf5fafc3df585cb64e5c3ea6531e22a40a59417b4f8fb0303d38559e8078ffa'),
('actual_delivery_index_independent_20261021T0334.jsonl','d039511377797fed4e057d3ae4eec6ce1bc24a2819f6c28b048dc40854e4a03b')]
for name,pin in journals:
 p=R/'results/formal_main_v2/control_transport'/name;raw=p.read_bytes();events=[json.loads(x) for x in raw.splitlines()]
 assert len(events)==2 and events[-1]['event']=='control_end' and events[-1]['returncode']==0 and events[-1]['source173_and_entrypoint_unchanged']
 assert pin in raw.decode()
 put('transport_'+name,raw)
put('README.md',('本包为本轮实际根整合、state/docs/成本及Git暂存交付的独立复核。\n\n'
'原科学终态收据按精确SHA继承；Goal运行入口由本代理编写，其科学终审来自另一代理，未在本包冒称自己重跑独审。\n'
'Git暂存237项与234项required清单逐字节核验，173冻结源码、26回存元数据、24真实归档及9CPU归档范围通过；原归档还原门槛继承已完成原guard。\n'
'finish/push入口仅源码审计，不表示已commit或push。最终封存初态未开放，旧Goal200与剩余1000均HOLD。\n'
'v1审计器在执行前发现读取Python源时误用JSON读器，保留原件并执行v2精确SHA/bytes读器；生产及科学证据不变。\n').encode())
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert not p.is_symlink() and p.name!='delivery_manifest.json'
  files.append(dict(path=p.relative_to(D).as_posix(),sha256=h(p),bytes=p.stat().st_size))
manifest=dict(schema='formal_main_v2',kind='actual_delivery_independent_frozen_package',status='frozen',source_root=str(D),file_count=len(files),files=files,final_review=dict(path='final_independent_review.json',sha256=h(D/'final_independent_review.json'),bytes=(D/'final_independent_review.json').stat().st_size),state_sha256=state,index_sha256=index,source173_verified=True,final_sealed=True,scope='Actual integration and stage bytes; exact scientific terminal audits inherited. No commit/push/Slurm/state/GPU writes by this independent audit.',utc=datetime.now(timezone.utc).isoformat())
put('delivery_manifest.json',(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(dict(status='frozen',file_count=len(files),manifest_sha256=h(D/'delivery_manifest.json'),report_sha256=h(D/'final_independent_review.json'))))
