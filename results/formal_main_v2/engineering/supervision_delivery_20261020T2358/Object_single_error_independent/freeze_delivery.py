from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
rel='.local/object_single_error_independent_20261020T2358';O=R/rel
def h(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 with (O/name).open('xb') as f:f.write(b)
 return dict(path=rel+'/'+name,sha256=h(b),bytes=len(b))
def pack(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (O/'delivery_manifest.json').exists()
pins={'audit_v1.py':'4bdc049b869b0cdd8811321cd1639a00811b90059cb240f0f20d2758c92f53dc','independent_review.json':'7aefd070fe5e437c7e8c0636db7301efeb9bd5cb0484665921b70aad5d6c6481','canonical599_audit_v1.py':'3f7224341c8c9e51948cbbd407f3c39cde1f1721d02ce475fcc1581fc4c853ba','canonical599_adoption_addendum.json':'d9d6de64311c45639a40a028e75a2697ac5cb605b892e881c50e81ab4b4e5ecf'}
for n,v in pins.items():assert h((O/n).read_bytes())==v
journals=[]
for source,name in [('object_single_error_independent_20261020T2358_v1.jsonl','transport_cpu_candidate.jsonl'),('object_single_error_canonical599_independent_20261020T2358_v1.jsonl','transport_canonical599.jsonl')]:
 b=(R/'results/formal_main_v2/control_transport'/source).read_bytes();items=[json.loads(x) for x in b.splitlines()]
 assert len(items)==2 and items[-1]['event']=='control_end' and items[-1]['returncode']==0 and items[-1]['source173_and_entrypoint_unchanged'] is True
 journals.append(put(name,b))
readme="""Object 单 policy_error CPU 候选独审（冻结交付）
================================================
候选 manifest fd5af505956b76add76fbd2e2ad3d8fff4f5910ae6e8cdf9e95d662d20b2dec7。
独审作者 goal_cpu_gate_2054，与候选作者不同。全部运行在服务器私有目录，经固定 SHA transport；无 GPU、Slurm 查询/提交、state、Git、canonical、P 写入。

CPU 审计：原 24 个正例、74 个拒绝例在内存重放并与作者结果逐项相等；另 16 个边界案例。5472 项核验通过。单节点 AST 白名单独立重建，完整 100 状态和 6 方法原校验、真实原 600 条身份/字节、唯一失败与原 6713 GPU 秒保持。单试验是新的全 reset linked attempt，不能称旧第 8 chunk 精确重放或普通 resume；derived loop 必须与 frozen loop 身份分开。

CPU 边界实际测得：终态同 CELL 缺 link/output/token、实际 Slurm comment/name 冲突、opaque policy 与 live run_episode 替换、带布尔假收据的空动作 success，只被结构层处理而无生产效力。所有 CPU 输出 production=false。生产 native gateway/source/model/实际 P/typed consumer 必须另做完整绑定与拒绝测试；本包不宣称生产可用，不给 GPU 授权。

随后独立审 root canonical599 adoption，31,550 项核验通过：599 条 start/result 原字节，11,720 chunks / 91,945 动作，controller clip 与执行队列字节，520 成功 / 79 负结果，3 个原分配共 6713 秒仅保留一次，author17/ind39 归档与 173 文件三根。旧失败（7 chunks、56 actions、第 8 输出未知）仍在原 600 条；whole600/新增科学/新增成本/最终 release 均未准入。源版本/历史环境证据沿用对应旧独审，不冒称实际旧控制器实例捕获或重新运行全部 599 环境。

independent_review.json 固定记录 CPU 候选审计时的缺口，不追改历史。canonical599_adoption_addendum.json 明确 B5 的 root599-only adoption 已完成核验；单次生产链和终态审计仍待完成。交付后不改本目录。
"""
put('README.md',readme.encode())
files=[]
for p in sorted(O.iterdir()):
 assert p.is_file() and not p.is_symlink()
 b=p.read_bytes();files.append({'path':p.relative_to(R).as_posix(),'bytes':len(b),'sha256':h(b)})
manifest={'schema':'formal_main_v2','kind':'Object_single_error_CPU_candidate_independent_delivery','status':'passed_CPU_candidate_only_with_production_blockers','root':rel,'utc':datetime.now(timezone.utc).isoformat(),'reviewed_by':'independent_goal_cpu_gate_2054','candidate_manifest_sha256':'fd5af505956b76add76fbd2e2ad3d8fff4f5910ae6e8cdf9e95d662d20b2dec7','review_sha256':pins['independent_review.json'],'canonical599_adoption_addendum_sha256':pins['canonical599_adoption_addendum.json'],'file_count':len(files),'total_bytes':sum(v['bytes'] for v in files),'files':files,'CPU_candidate_checks':5472,'canonical599_adoption_checks':31550,'author_positives_replayed':24,'author_negatives_replayed':74,'additional_boundary_cases':16,'old599_root_adoption_independently_verified':True,'legacy599_counts':{'trials':599,'chunks':11720,'actions':91945},'old600_raw_and_one_policy_error_retained':True,'old6713_GPU_seconds_retained_once':True,'production_admitted':False,'whole600_admitted':False,'new_GPU_submissions':0,'new_GPU_seconds':0,'new_scientific_trials':0,'Slurm_queries':0,'no_state_Git_P_canonical_writes':True,'final_release':False,'remaining_production_gates':['native all-mode capacity and identity/duplicate/CAS/pending/ACK transaction','complete entry/wrapper/gateway/reviewer/consumer/model/checkpoint source closure and actual-P verification','distinct original-versus-derived runtime provenance','true original/action consumers with raw result reconstruction, canonical role-specific review references','single linked full-reset root authorization and terminal original+independent review'],'transport_journals':journals}
out=put('delivery_manifest.json',pack(manifest));print(json.dumps({'manifest':out,'file_count':len(files),'total_bytes':manifest['total_bytes'],'production_admitted':False}))
