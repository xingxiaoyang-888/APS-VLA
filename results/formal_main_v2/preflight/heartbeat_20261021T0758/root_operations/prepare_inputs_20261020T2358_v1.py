from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0758';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2358'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return {'path':n,'sha256':h(R/n)}
def pinned(n,w):assert n.startswith(E+'/') and '..' not in Path(n).parts and h(R/n)==w;return rd(n)
a=argparse.ArgumentParser()
for n in ['production-manifest','production-audit-manifest','production-review']:
 a.add_argument('--'+n,required=True);a.add_argument('--'+n+'-sha256',required=True)
a=a.parse_args()
objprod=pinned(a.production_manifest,a.production_manifest_sha256);objindman=pinned(a.production_audit_manifest,a.production_audit_manifest_sha256);objind=pinned(a.production_review,a.production_review_sha256)
assert isinstance(objind['status'],str) and not objind.get('production_ready',False) and not objind.get('production_admitted',False)
reports={
 'Object_CPU_review':(E+'/Object_single_error_independent/independent_review.json','7aefd070fe5e437c7e8c0636db7301efeb9bd5cb0484665921b70aad5d6c6481'),
 'Object599_addendum':(E+'/Object_single_error_independent/canonical599_adoption_addendum.json','d9d6de64311c45639a40a028e75a2697ac5cb605b892e881c50e81ab4b4e5ecf'),
 'Goal_CPU_final_review':(E+'/Goal_bounded_diagnostic_independent/final_independent_review.json','1f33da03cb3a1680ead9d090d12889dc334534008cac67f0ed169a10596da901'),
 'Goal_specification':(E+'/Goal_bounded_diagnostic/prospective_full200_specification.json','ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'),
 'Goal_author_manifest':(E+'/Goal_bounded_diagnostic/delivery_manifest_v3_original.json','25ca8079785f3409d35be85e7a62044ec20e6674b1c36ffbefcc66056a66ed18'),
 'Goal_independent_manifest':(E+'/Goal_bounded_diagnostic_independent/delivery_manifest_original.json','52991b019aacd2534fb13081db0d85e13fefe19d9655177eec07679e5135d7a3'),
 'Object_CPU_manifest':(E+'/Object_single_error_independent/delivery_manifest_original.json','78303859a448333984ce888f8b2f192c273dc8aff41cc8b0ae003a983e79e134'),
 'Object_production_author_manifest':(a.production_manifest,a.production_manifest_sha256),
 'Object_production_independent_manifest':(a.production_audit_manifest,a.production_audit_manifest_sha256),
 'Object_production_independent_review':(a.production_review,a.production_review_sha256)}
docs={key:pinned(*v) for key,v in reports.items()};evidence={key:ref(v[0]) for key,v in reports.items()}
goal=docs['Goal_CPU_final_review'];assert goal['status']=='passed' and goal['check_count']==goal['checks_passed_total']==len(goal['checks'])==2068 and goal['blockers']==[] and not goal['production_ready'] and not goal['prospective_full200_GPU_authorized'] and goal['old200_HOLD'] and goal['new_Goal_science_HOLD']
legacy=docs['Object599_addendum'];assert legacy['status']=='passed_legacy599_only' and legacy['audit_checks_passed']==31550 and legacy['negative_outcomes']==79 and legacy['successes']==520 and legacy['original_GPU_seconds_once']==6713 and not legacy['whole600_admitted']
meta={'kind':'root_CPU_delivery_inputs','new_GPU_jobs':[],'runtime_installed':False,'new_scientific_trials':0,'evidence':evidence}
meta['Object_single_error_CPU_review']={'independent_review':evidence['Object_CPU_review'],'independent_status':docs['Object_CPU_review']['status'],'production_ready':False,'independent_checks':5472,'author_positive_checks':24,'author_negative_checks':74,'supplementary_boundary_tests':16,'canonical599_adoption_independent_review':evidence['Object599_addendum'],'legacy_adoption_checks':31550,'legacy_adoption_negative_outcomes_retained':79,'legacy599_not_new_runtime_trials':True}
meta['Object_single_error_production_candidate']={'independent_review':evidence['Object_production_independent_review'],'independent_status':objind['status'],'production_ready':False,'author_manifest':evidence['Object_production_author_manifest'],'independent_manifest':evidence['Object_production_independent_manifest'],'runtime_installed':False,'actual_P_verified':False,'native_submit_implemented':False,'new_GPU_jobs':[],'original_frozen_loop_preserved_required':True,'derived_loop_provenance_distinct_required':True,'raw_consumer_required':True,'CPU_report_scope':objind.get('audit_scope',objind.get('scope',objind.get('kind'))),'remaining_production_gates':objind.get('remaining_production_gates',objind.get('production_blockers',objind.get('blockers',[])))}
meta['Goal_bounded_CPU_diagnostic']={'independent_review':evidence['Goal_CPU_final_review'],'independent_status':goal['status'],'production_ready':False,'author_manifest':evidence['Goal_author_manifest'],'independent_manifest':evidence['Goal_independent_manifest'],'checks':2068,'original_author_evidence_checks':1235,'classifier_cases':14,'design_positive':1,'design_negative':30,'independent_design_negative':20,'cause_identified':False,'old200_HOLD':True,'additional1000_HOLD':True,'new_GPU_jobs':[],'prospective_specification':evidence['Goal_specification'],'query_index':9,'query_index_zero_based':True,'policy_call_ordinal':10,'step':72,'mismatch_pair_in_original200':{'ordinals':[57,58],'task_id':2,'source_state_index':42},'two_engineering_trace_difference':{'ordinal':30,'task_id':1,'source_state_index':12},'old200_mismatch_distinct_from_engineering_trace_divergence':True,'maximum_attempts':1,'maximum_trials':200,'maximum_control_steps':60000,'maximum_policy_queries':7600,'metadata_errata_and_old_validator_gaps_retained':True}
meta['blocker_details_markdown']='''## Object：历史采用与新尝试分开

root以逐条原始字节引用建立599条兼容采用表，另一个代理按原始start/result、动作队列与控制器clip重建复核31550项；520成功、79普通任务失败全部保留。原3分配6713 GPU秒已计账，不在此重复相加。原唯一policy_error仍保留，拒绝的chunk字节未知，不能推断其值或新的结果。完整600的typed视图未生成，599旧条目不写成新ledger，也未计入current增量。

原24正74拒CPU包独审5472项及16边界例；本轮进一步形成新typed入口、原始记录reviewer/consumer和只读gateway guard候选。生产候选实际审核范围以本轮汇总所链接的独立报告为准，不能用CPU布尔收据冒充真实终验。原冻结循环和单cell派生循环必须分别标识；仍没有canonical/P安装、新真实repair/plan/invocation、actual P --verify和原子Slurm submit。下一轮补齐这些精确门槛后，才允许原失败同初态同方法的一次完整新尝试；从初态起，不从第8查询恢复，不普通resume跳过terminal失败，不按结果自动重试。保留六方法/100初态完整验证，不缩为单cell来放宽guard。

## Goal：旧采样时序与新数据验收

真实源明确：旧ledger五分量哈希采于predict_chunk返回后。query index8/step64与index9/step72界定的是post-policy日志区间；index9是零基索引，即第10次策略调用。旧非零query的pre/post原始数组与中间sim/controller/RNG信息不足，前72环境指令相同不证明中间隐藏状态相同。固定13候选不匹配只排除这13项，不能归因图像、proprio、RNG、模拟器或policy mutation。

旧200的t0不一致是ordinal57/58、task2/source42；两次58工程中的唯一轨迹差异是ordinal30、task1/source12，两件事不能混为因果。新的全query输入门控工程通过不证明旧200可采用或旧原因已修复。

作者实际检查数组1235项与原整数1234的差异、独审原1751数组与1750整数差异、旧设计validator的9项漏检均保留。修正版31文件不改实际200身份表，作者1正30拒、不同代理额外20拒通过；最终独审不可变检查数组2068项、14分类例通过，仅CPU/设计。

root选择固定一次完整200的新数据验收方案，原100开发初态×原A/B256seed17原顺序，保持所有checkpoint/预算/seed/控制循环，200条/60000控制步/7600query上限。普通任务失败全部计入，旧200整批保留且不接纳，不挑旧成功或失败重跑。此处只有设计选择；生产全200被动门控、AST/异常fail-closed、实际P身份/储存容量、原consumer、同锁CAS单ACK门槛须先实现并独审，再另行root授权唯一输出及一次GPU尝试。当前没有新输出、token、job、实际P通过或科学结果。未来新200通过只证明这份新数据满足协议，不能据此查明旧原因或开放final；另1000 Goal开发仍HOLD。

## Spatial、计时与最终结果

3054201仅在UTC2026-10-21T00:03:34观测一次，原报告204/600、RUNNING；原12 legacy和其后588 current尚未组成终验批次。正常运行不本轮轮询、不重复submit。等待后续监督按原类型reviewer/consumer、独立终审及非权重回存后计数；原3022743的393秒和3042529前置失败2秒保留，后者没有执行invocation不补造。

训练72/72组已完成，不重训、不重新选checkpoint。完整开发批次仍6400/8800，400唯一初态；本轮0新增科学试验、0新GPU提交。271唯一分配1987496 GPU秒为上述时刻下界，之后按同一分配更新，不把CPU或旧工程成本重复累加。Long/Spatial/Object固定观测仍90，不重复采集；正式O2A/分项计时及35200封存最终评测均等待原全局身份与开发收据门槛。全部当前工程证据不是论文主表结果。
'''
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('input2358ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert h(R/'results/experiment_supervisor/state.json')=='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10'
 p=R/B/'final_snapshot_inputs.json'
 with p.open('x') as f:json.dump(meta,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':h(p),'status':'inputs_prepared_no_state_change','new_GPU_jobs':[]}))