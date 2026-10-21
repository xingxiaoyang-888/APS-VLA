from pathlib import Path
import json,hashlib,copy
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');rel='.local/goal_bounded_diagnostic_independent_20261020T2358';D=R/rel
H=lambda b:hashlib.sha256(b).hexdigest()
def read(name,pin=None):
 b=(D/name).read_bytes()
 if pin:assert H(b)==pin
 return json.loads(b)
def write(name,x):
 b=(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with (D/name).open('xb') as f:f.write(b)
 return {'path':rel+'/'+name,'bytes':len(b),'sha256':H(b)}
assert not (D/'delivery_manifest.json').exists()
before=read('independent_review_v1.json','935c24b0eb2e5ea19dc3524e045310d3a67a91e0adb2b3e8670f17d0b4331262')
after=read('independent_review.json','8bcbf4e052c5853a9a679f42ff9c0330e23d2669b465d861c215ef511444ed50')
assert len(before['checks'])==1751 and len(after['checks'])==317 and all(c['passed'] is True for c in before['checks']+after['checks'])
combined=[{'phase':'actual_evidence_and_original_contract',**copy.deepcopy(c)} for c in before['checks']]+[{'phase':'revised_contract_and_stability',**copy.deepcopy(c)} for c in after['checks']]
assert len(combined)==2068
final=copy.deepcopy(after);final.update({'kind':'Goal_bounded_CPU_diagnostic_and_prospective_design_final_independent_review','utc':datetime.now(timezone.utc).isoformat(),'check_count':len(combined),'checks':combined,'checks_passed_total':len(combined),'immutable_check_list':True,'count_source':'len(checks), after concatenating immutable original1751 and revision317 arrays; publication does not mutate this array.','prior_contract_revision_review':{'path':rel+'/independent_review.json','sha256':'8bcbf4e052c5853a9a679f42ff9c0330e23d2669b465d861c215ef511444ed50'},'additional_Goal_scientific_development_including_remaining1000_HOLD':True})
final.pop('checks_passed_this_revision',None)
final_ref=write('final_independent_review.json',final)
journals=[]
for src,name,code in [('goal_bounded_independent_20261020T2358_v1.jsonl','transport_v1.jsonl',0),('goal_bounded_independent_20261020T2358_v2_contract.jsonl','transport_v2_metadata_failure.jsonl',1),('goal_bounded_independent_20261020T2358_v3_contract.jsonl','transport_v3_contract.jsonl',0)]:
 b=(R/'results/formal_main_v2/control_transport'/src).read_bytes();rows=[json.loads(x) for x in b.splitlines()]
 assert len(rows)==2 and rows[-1]['event']=='control_end' and rows[-1]['returncode']==code and rows[-1]['source173_and_entrypoint_unchanged'] is True
 with (D/name).open('xb') as f:f.write(b)
 journals.append({'path':rel+'/'+name,'bytes':len(b),'sha256':H(b)})
readme="""Goal 有界 CPU 诊断与未来固定200方案：独审冻结交付
=================================================
最终可引用报告：final_independent_review.json。
status=passed 仅限 audit_scope 明确的真实旧证据 CPU 分析和固定设计契约；
check_count == len(checks) == 2068，数组已经冻结，发布不再追加该数组。
blockers=[] 表示本 CPU 范围无未解决缺陷；
remaining_production_gates 为5项另行必需门槛，production_ready/GPU授权/final_release 全 false。

作者31文件 manifest_v3 25ca8079785f3409d35be85e7a62044ec20e6674b1c36ffbefcc66056a66ed18 已逐SHA核验。
原1235实际检查、14分类用例逐项重现；读取100个精确来源/72个去重blob，重算固定13候选与5个q9归档成员，未重新全扫10741blob。
旧 run_episode 的 hash 是 predict_chunk 返回后采样。旧q9 pre-policy原字节不存在；两58工程 ordinal30 的首次posthash差异q9/step72只给出日志边界，前72条序列化命令相同不证明隐藏状态一致。
原200真正唯一t0 posthash不等是 A57/B58、task2/source42，与ordinal30/task1/source12的工程差异分别记录，不将其混为因果解释。旧原因未查明、未称修复。

未来完整200方案从原100开发初态×原A/B256_seed17顺序生成，原方法/checkpoint/环境不变。上限1次、200条、60000控制步、7600query，旧200全保留HOLD，新增Goal科学（含后续1000）仍HOLD。
原v1设计谓词9项漏检有实际反例保留。作者追加v2契约后，原方案字节仍ed0b59bd…不变；1正30拒重现，独立20拒（包括原9反例、界限/签名/名单/条件）全部通过。纯CPU谓词不是生产入口，未来仍需完整runtime/AST、实际P闭包、存储、原consumer、lock/CAS/8槽/唯一ACK和终态原/独立/root验收。

计数历史保留：作者报告整数1234而实际列表1235；我v1报告整数1750而实际列表1751，均因最后私有发布检查追加。我的v2补审入口以错误整数期待值检查，写入新结果前失败；源/证据/测试未失败。此脚本、失败JSON、transport完整保留；v3按实际数组核验后通过。最终2068=不可变1751+317，各自检查记录均可审，不覆盖原件。

全过程0 GPU、0科学、0Slurm查询/提交、0state/Git/P/canonical写入；仅私有审计产物及已审transport日志。封存后不改本目录。
"""
with (D/'README.md').open('xb') as f:f.write(readme.encode())
files=[]
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink()
 b=p.read_bytes();files.append({'path':p.relative_to(R).as_posix(),'bytes':len(b),'sha256':H(b)})
manifest={'schema':'formal_main_v2','kind':'Goal_bounded_diagnostic_CPU_independent_delivery','status':'passed_CPU_evidence_and_design_only','root':rel,'utc':datetime.now(timezone.utc).isoformat(),'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'files':files,'final_review':final_ref,'check_count':2068,'check_count_rule':'exact len(final_review.checks); list immutable','author_manifest_v3_sha256':'25ca8079785f3409d35be85e7a62044ec20e6674b1c36ffbefcc66056a66ed18','author_classifier_cases':14,'current_contract_author_tests':{'positive':1,'rejections':30},'independent_contract_rejections':20,'original_contract_nine_gaps_and_metadata_failure_preserved':True,'blockers_in_CPU_scope':[],'remaining_production_gate_count':5,'old200_HOLD':True,'new_Goal_science_including_remaining1000_HOLD':True,'prospective_full200_GPU_authorized':False,'cause_identified':False,'production_ready':False,'new_GPU_jobs':0,'new_GPU_seconds':0,'new_scientific_trials':0,'Slurm_queries':0,'no_state_Git_P_canonical_writes':True,'final_release':False,'transport_journals':journals}
ref=write('delivery_manifest.json',manifest)
print(json.dumps({'manifest':ref,'file_count':len(files),'bytes':manifest['total_bytes'],'final_review':final_ref,'check_count':2068,'CPU_scope_status':final['status'],'production_ready':False}))
