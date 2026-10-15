from pathlib import Path
import hashlib, json
r=Path('F:/CTI-VLA')
for old,new in [('prepare_long_seed_snapshot.py','prepare_long_k64_snapshot.py'),('install_long_seed_snapshot.py','install_long_k64_snapshot.py')]:
    text=(r/'.local'/old).read_text(encoding='utf-8').replace('g1_future_long_multiseed_v1','g1_future_long_k64_v1')
    (r/'.local'/new).write_text(text,encoding='utf-8',newline='\n')
text=(r/'.local/check_long_seed_jobs.py').read_text(encoding='utf-8').replace('g1_future_long_multiseed_v1','g1_future_long_k64_v1').replace("old['training_seed']","old.get('training_seed')")
(r/'.local/check_long_k64_jobs.py').write_text(text,encoding='utf-8',newline='\n')
text=(r/'.local/pull_long_seed_results.py').read_text(encoding='utf-8')
text=text.replace("p.add_argument('seed', type=int, choices=[23, 41])", "p.add_argument('stage', choices=['all','17','23','41'])")
text=text.replace("relative = f'results/g1_future_long_multiseed_v1/seed{a.seed}'", "relative = 'results/g1_future_long_k64_v1' + ('' if a.stage == 'all' else '/seed'+a.stage)")
text=text.replace("('.json','.jsonl','.txt','.md')", "('.json','.jsonl','.txt','.md','.npz','.out','.err')")
text=text.replace("'seed':a.seed", "'scope':a.stage")
(r/'.local/pull_long_k64_results.py').write_text(text,encoding='utf-8',newline='\n')
p=r/'configs/experiments/g1_future_long_k64_v1.json'
j=json.loads(p.read_text(encoding='utf-8'))
j['analysis']['primary_latency_aggregation']='equal-weight arithmetic mean of the3 per-seed medians and of the3 per-seed p95s; pooled distributions are secondary, no posthoc choice'
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
p=r/'results/g1_future_long_k64_v1/registration_receipt.json'
j=json.loads(p.read_text(encoding='utf-8'))
j['sha256']=hashlib.sha256((r/'configs/experiments/g1_future_long_k64_v1.json').read_bytes()).hexdigest()
j['latency_aggregation_clarified_before_any_GPU_results']=True
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
p=r/'docs/G1-F-Long64预算与延迟执行登记.md'
t=p.read_text(encoding='utf-8').replace('同时给三seed均值和合并分布。','主比较固定为三个seed各自median的等权均值、各自p95的等权均值；合并分布另作次要描述，不事后替换。')
p.write_text(t,encoding='utf-8',newline='\n')
print('Prepared root helpers and preregistered primary aggregation')
