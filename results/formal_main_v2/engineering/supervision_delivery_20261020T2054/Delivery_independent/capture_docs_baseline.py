from pathlib import Path
import datetime,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2054'
assert not (R/'results/formal_main_v2/preflight/heartbeat_20261021T0454/final_summary.json').exists()
rows=[]
for name in ['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记','正式下游阻塞登记_20261020T1949']:
 p=R/'docs'/(name+'.md');b=p.read_bytes();rows.append({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
out={'kind':'preintegration_docs_readonly_baseline','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,'production_mutations':False}
p=D/'docs_baseline.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':len(rows)}))
