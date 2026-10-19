from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,xml.etree.ElementTree as ET
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
C=R/'.local/spatial_continuous_admission_2130'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def save(name,value):
 p=D/name;b=json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return ref(p)
pins={'admission.py':'0e5d2bbdca27640c4784393b3ea6a17969a7c6235bdeeb10b61c4a8ab7546b74','gateway.py':'71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6','test_continuation.py':'a684c5c449246e66511537ae684fff5cdf5b12e4c5303bb88bab2bc3864a3d7b','candidate_review.json':'83a3961f25020d0f1cce9d1287323fc23d882f27102ba25fa8bba93f4198ec30','archive_manifest.json':'053c9e1f74f5e75d09aa3a938fc291fba3150529590700ca5778713b1f55fa72','README.md':'52797708c013b5468a986ef1725a5d3148322f842fd7d0bb3bd69bffff262f8a'}
for n,h in pins.items():assert ref(C/n)['sha256']==h,n
rawref=ref(D/'actual_readonly_bridge_a1.json');assert rawref['sha256']=='05f940811023427e314ffb08cabb484b59cc44dd14be9d61eee0959d6d21bd1a'
actual=json.loads((D/'actual_readonly_bridge_a1.json').read_bytes());assert actual['status']=='passed_actual_metadata_and_original_raw_reconstruction'
assert actual['state_sha256_before']==actual['state_sha256_after'] and actual['state_changed'] is False
suite=next(ET.parse(D/'independent_tests_a1.xml').iter('testsuite'))
assert {k:int(suite.get(k)) for k in ['tests','failures','errors','skipped']}==dict(tests=14,failures=0,errors=0,skipped=0)
aSuite=next(ET.parse(C/'author_tests_a1.xml').iter('testsuite'))
assert {k:int(aSuite.get(k)) for k in ['tests','failures','errors','skipped']}==dict(tests=45,failures=0,errors=0,skipped=0)
evidence=dict(actual['evidence_sha256'])
for p in [*(C/n for n in pins),C/'author_tests_a1.xml',C/'author_tests_a1.log',C/'actual_prepare_a1.log',C/'actual_prepare_a2.json',C/'authorization_a2_draft.json',
 D/'test_independent.py',D/'run_independent.py',D/'run_independent_a2.py',D/'independent_tests_a1.xml',D/'independent_tests_a1.log',D/'independent_tests_a1_command.json',D/'independent_tests_a1_result.json',D/'actual_readonly_bridge_a1.json',D/'actual_readonly_bridge_a1.log',
 R/'scripts/ops/formal_autonomous_training_v1/controller.py',R/'scripts/ops/formal_action_deployment_v1/gateway.py',
 R/'results/formal_main_v2/control_transport/spatial_continuous_independent_2130_a1.jsonl',R/'results/formal_main_v2/control_transport/spatial_continuous_independent_2130_a2.jsonl']:
 r=ref(p);assert r['path'] not in evidence or evidence[r['path']]==r['sha256'];evidence[r['path']]=r['sha256']
assert evidence['scripts/ops/formal_autonomous_training_v1/controller.py']=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
assert evidence['scripts/ops/formal_action_deployment_v1/gateway.py']=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
files={'scripts/ops/formal_spatial_cuda_continuous_admission_v1/'+n:pins[n] for n in ('admission.py','gateway.py')}
value={'schema':'formal_main_v2','kind':'spatial_cuda_continuous_admission_independent_CPU_review','status':'passed_CPU_review',
 'reviewed_utc':datetime.now(timezone.utc).isoformat(),'reviewed_by':'independent_subagent_server_v3_audit','version':'spatial-cuda-continuous-admission-v1',
 'pair_key':'libero_spatial_k64_seed23','files':files,'candidate_sources':{str((C/n).relative_to(R)):pins[n] for n in ('admission.py','gateway.py')},
 'same_byte_canonical_publication_permitted':True,'blockers':[],
 'scope':'Independent review of exact one-time Spatial64 seed23 1500-to5000 execution admission; not root authorization or a completed continuation.',
 'tests':{'independent':{'count':14,'failures':0,'errors':0,'skipped':0,'seconds':float(suite.get('time')),'xml':ref(D/'independent_tests_a1.xml'),'log':ref(D/'independent_tests_a1.log'),'command':ref(D/'independent_tests_a1_command.json')},
 'author_inherited':{'count':45,'failures':0,'errors':0,'skipped':0,'xml':ref(C/'author_tests_a1.xml'),'test_source':ref(C/'test_continuation.py')},
 'boundary':'Transaction Science/IO/Slurm positive and negative cases are isolated synthetic fixtures; real original raw reviewer and byte checks were executed separately without injection.'},
 'actual_readonly_bridge':rawref,
 'findings':[
  'Scientific source173 and original Spatial formal_main.slurm remain exact; only registered timestamp, segment end and two execution argv values change, plus typed continuation metadata.',
  'Actual original startup-aware reviewer reconstruction equals genuine root recovery review; finalization additions are two exact SHA/bytes paths proved by archived failure evidence and unique signed pull ownership, not a directory exemption.',
  'Four history allocations and FAILED3028522 remain: 3281+5203+73+3401=11958 GPU seconds; A/B1500, cursor12000, existing validation0/500/1000/1500 with189windows match.',
  'Live NativeIO rehashed213 source/raw inputs and both exact resume files. It did not deserialize tensors or restore optimizer/RNG.',
  'Shared writer lock/CAS, all registered scheduler identities including CPU0, existing lease, unknown-state refusal and unreserved capacity gate are retained. Positive isolated transaction preserves entire autonomous controller dictionary and existing reservations/blocked entry.',
  'Post-ACK accounting lag preserves known job pending and refuses another attempt; no automatic retry or pending clearing is introduced.',
  'Unsigned actual draft is rejected by real typed gate; no production root authorization is manufactured by this audit.'
 ],
 'source173_R_and_S_match':True,'server_inputs_checked':213,'actual_resume_checks':actual['server_metadata']['server_resume_checks'],
 'historical_GPU_seconds':11958,'retained_failure_GPU_seconds':73,'current_boundary':{'A':1500,'B':1500},'current_cursor':{'A':12000,'B':12000},
 'real_1500_to5000_continuation_run':False,'root_authorized':False,'GPU_submitted':False,'scientific_results_created':False,
 'optimizer_RNG_restore_verified_by_this_CPU_audit':False,'state_changed':False,'P_written':False,'sealed_values_read':False,
 'remaining_root_steps':['Publish exact two files at canonical paths and sign exact-once typed authorization referencing this receipt.','At a genuinely free unreserved slot, run unchanged locked all-registry/owner/lease/capacity/evidence/resume checks immediately before explicit one-time submit.','Keep pending on uncertain submit; reconcile the known job rather than resubmit. Terminal continuation needs genuine raw/root/independent review and remains outside this CPU pass.'],
 'retained_harness_failure':{'source':ref(D/'run_independent.py'),'transport':ref(R/'results/formal_main_v2/control_transport/spatial_continuous_independent_2130_a1.jsonl'),'reason':'Independent runner JSON newline quoting SyntaxError before any candidate or test execution; preserved, corrected only runner in a2.'},
 'evidence_sha256':evidence,'evidence_count':len(evidence)}
receipt=save('independent_review.json',value)
readme="""# Spatial64 seed23 连续入口独审

结论：最终两份候选通过有限 CPU 独审，可由 root 原字节发布后签署一次性准入。尚未提交或执行1500→5000。

- 14项独立定向 CPU 检查通过；作者45项仅作为继承证据。正交易使用隔离 synthetic fixture，不能当作真实作业。
- 实际调用原 Science/reviewer 和 NativeIO：487项来源、213项P/S输入、两个resume实际SHA通过。未反序列化checkpoint，未恢复optimizer/RNG。
- 四次分配11958 GPU秒完整保留（含失败73秒）；A/B均1500、cursor12000。5000调度、每500验证和每50恢复点不变，使用原Spatial Slurm wrapper。
- 两个早期finalization仅以精确路径/SHA/bytes、原failure archive和唯一pull ownership补入严格清单；未扩大目录豁免。
- 实际unsigned draft仍拒绝。现存controller、blocked记录和其他预约保留；未来提交需root新签授权及空闲非预约槽的完整实时复核。
- accounting传播延迟会保留known pending并拒绝再次提交，需对账原作业，不能重发。
- 一次独审runner引号语法失败原件保留，未运行候选；只修runner后14项和实际桥接通过。
- 本目录不含state/P/Slurm修改、封存值或权重副本。所有pytest隔离副本不进入交付包；仅归档顶层代码、原日志、XML、收据。
"""
with (D/'README.md').open('x') as f:f.write(readme)
rows=[ref(p) for p in sorted(D.iterdir()) if p.is_file()]
manifest=save('archive_closure.json',{'schema':'formal_main_v2','kind':'spatial_continuous_independent_archive','status':'frozen','root':str(D),
 'files':rows,'file_count':len(rows),'total_bytes':sum(x['bytes'] for x in rows),'independent_review':receipt,
 'external_transport':[ref(R/'results/formal_main_v2/control_transport/spatial_continuous_independent_2130_a1.jsonl'),ref(R/'results/formal_main_v2/control_transport/spatial_continuous_independent_2130_a2.jsonl')],
 'excluded':'pytest_independent_a1 contains isolated synthetic fixtures; no temporary duplicate evidence is part of this package.'})
print(json.dumps({'independent_review':receipt,'archive_closure':manifest,'evidence_count':len(evidence)}))
