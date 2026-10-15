from pathlib import Path
import hashlib,json
r=Path('F:/CTI-VLA');p=r/'configs/experiments/g1_future_long_k64_v1.json'
j=json.loads(p.read_text(encoding='utf-8'))
for path in ('results/g1_future_long_multiseed_v1/source_g1_future_long_multiseed_v1.json',
             'results/g1_future_long_v1/acceptance/f01_acceptance.json'):
    j['frozen_evidence_sha256'][path]=hashlib.sha256((r/path).read_bytes()).hexdigest()
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
q=r/'results/g1_future_long_k64_v1/registration_receipt.json';v=json.loads(q.read_text(encoding='utf-8'))
v['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();v['original128_source_and_F01_pins_completed_before_any_GPU_results']=True
q.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print({k:j['frozen_evidence_sha256'][k] for k in list(j['frozen_evidence_sha256'])[-2:]})
