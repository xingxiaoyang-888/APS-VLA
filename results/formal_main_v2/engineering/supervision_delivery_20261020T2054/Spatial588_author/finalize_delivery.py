from pathlib import Path
import datetime,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/spatial588_recovery_20261020T2054'
assert D.resolve()==D and D.is_dir()
assert hashlib.sha256((D/'control.py').read_bytes()).hexdigest()=='e3994a213c54b8824febe95bed2e0ca8f76b2782ddd21b5f7c5a1496f4ac3df8'
assert not (D/'delivery_manifest.json').exists(), 'Do not overwrite an issued delivery manifest'
readme="""# Spatial 12＋588 前置失败历史候选

本包仅为 CPU 控制派生候选，尚未获得生产运行准入。未提交 GPU、未新增科学 trial、未改 state 或 Git，未读取封存值。173 个冻结文件和原科学 wrapper 保持原字节。完整新计划、真实 P 上的新 wrapper --verify、新精确 gateway、完整终态 consumer 以及旧 12 条兼容证明仍未完成。

## 精确历史与边界

- 3022743 为真实执行前缀：COMPLETED 0:0，393 GPU 秒，12 条完成；ledger 592887 字节，SHA256 3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9。
- 3042529 为前置失败：FAILED 1:0，2 GPU 秒，没有 child、adapter 或 ledger invocation。其单次原 ACK、真实 receipt、日志及 Slurm 会计记录全部保留。ACK 后的登记延迟是另一事务问题，不等于 GPU 失败原因。
- 所有 Slurm 历史始终含两作业；实际 ledger 历史只有 3022743。原前缀 root review 仍为 3022743，绝不伪造 3042529 普通 review、pull、adapter 或 invocation。真实历史成本共 395 GPU 秒。
- 仅允许 Spatial、原 6 个方法、固定 600 清单、保留 12、剩余 588、一个后续 attempt03；不授权其他 pair、Goal、collect、profile 或 final。

## 实现和验证

当前入口 control.py，SHA256 e3994a213c54b8824febe95bed2e0ca8f76b2782ddd21b5f7c5a1496f4ac3df8。使用原源码的私有精确派生：原 planner 的 prior_contract 两处区分已执行前缀和全部尝试，原 allocation_cost 三处区分无 child 失败；类型证明先行验证，原源、配置、checkpoint、ledger、恢复、相邻证据和成本门槛继续运行。原文件不修改。planner 只接收自身私有 helper；不能用外部 helper 绕过。

author_CPU_tests_v3.json 的 45 项真实历史及负例检查通过。synthetic_terminal_cost_tests.json 的 16 项为明确标记的合成终态成本单元测试，仅在内存构造未来作业和拟定收据，不是 Slurm 事实、生产授权或新的 ledger invocation。合成 495 秒是 395 秒真实历史加 100 秒 mock，禁止计入真实 GPU 成本。没有执行实际新增作业的完整 terminal consumer。

control_v1.py、control_v2.py、旧 tests/proposal/proof 保留修改历史；不要把旧闭包 proof 当当前入口授权。repair_record_proposal_v3.json 明确无 root 授权，私有路径闭包不能原封不动充当生产证据。

## 旧 12 条的准入限制

即使未来 raw 审计重建全部 600 条，其执行来源也只能写为 12 条旧执行＋588 条新执行。旧 12 逐动作字节不变，以及模型、控制器、初态、随机性和环境身份一致，是独立兼容论证的必要条件，不能由原样保留推出旧新 outcome 等价。证据不足时继续 HOLD，不补造、不删旧尝试、不把 600 条全部称为当前动作执行。

本候选 reviewer 明确写入上述混合来源；consumer 的 require_complete=True 直接拒绝，不能用其发行完整当前动作验收、全局冻结、O2A 或 final release。解除这一限制必须另有具体兼容证据和独立审计后的有界修订。

## 最低后续集成次序

详见 next_integration_steps.json。先补兼容证明，再由 root 集成规范路径、重新形成路径/源码闭包与独立收据、发布真实 root repair，生成新 attempt03 的计划及完整 readiness，审精确 gateway，并完成真实 P 新 invocation 的 wrapper --verify。全部门槛通过后才可由 root 单次提交；不把旧 3042529 修复后的 verify 当新计划验收。

此包交付状态为 CPU candidate，不是可以立即补位的 GPU 作业。
"""
(D/'README.md').write_text(readme,encoding='utf-8')
actions=[
'Independently establish legacy12 compatibility using unchanged per-action bytes and exact model/controller/init-state/randomness/environment identities. Preserve raw prefix and original assumptions. Insufficient evidence means HOLD; no fabricated equivalence.',
'Root integrate only a bounded canonical version, preserving173 frozen files and original scientific wrapper. Recompute canonical path/source closure and independent CPU proof; private descriptors are not production authorization.',
'Root publish typed repair bound to both real prior allocations3022743/3042529, real executed prefix review3022743, raw no-child3042529 receipts/ACK,395GPU seconds and fixed600 manifest. Do not create a nonexistent failure invocation/review/pull.',
'Build exactly one attempt03 scientific/action invocation and transition retaining both prior Slurm IDs and actual3022743 from_version/prefix review. Preserve12 old and588 new identity. Audit full adjacent chain, source/config/checkpoints/prefix and consumer.',
'Audit an exact Spatial588 posttraining gateway preserving owner/lease,shared writer lock/CAS,all-mode8GPU capacity,unknown active/pending/unique ACK/token reconciliation and duplicate submission protection. Do not generalize old collect or k64s23 gateways.',
'Publish exact new readiness and dependencies to P, then run the actual unchanged action wrapper --verify against the NEW invocation with root and independent audit. Previous3042529 dependency-repair verify is insufficient.',
'Only after all gates root may submit one bounded588 GPU job. Independently reconstruct original full terminal review/consumer plus typed all-attempt cost; retain12legacy+588new provenance and all original costs exactly once. No global current-action600 acceptance without step1.']
steps={'schema':'formal_main_v2','kind':'spatial588_candidate_minimum_integration_steps','status':'not_authorized_for_GPU','required_order':[{'step':i+1,'action':a,'complete':False} for i,a in enumerate(actions)],'actual_new_GPU_submissions':0,'actual_new_scientific_trials':0,'actual_P_new_invocation_verify':False,'full_production_chain_complete':False,'sealed_values_read':False,'root_only_submission':True}
(D/'next_integration_steps.json').write_text(json.dumps(steps,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
err={'kind':'transport_argument_preentry_rejection','entrypoint':'.local/spatial588_recovery_20261020T2054/test_candidate_v3.py','failed_invocation':'spatial588_CPU_v3_2054','reason':'Incorrect bundle SHA argument rejected by audited transport verify_bundle with ValueError: bundle SHA missing, before the candidate entry executed.','candidate_executed':False,'new_GPU_seconds':0,'new_GPU_submissions':0,'corrected_unique_invocation':'spatial588_CPU_v3b_2054','corrected_bundle_sha256':'3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149','corrected_result':'passed_author_CPU_tests_not_production_admission','additional_local_transport_construction_error':'First finalize authoring function had a JavaScript parse error before exec_command. No SSH or server write occurred; corrected construction writes this finalizer once.'}
(D/'transport_argument_error.json').write_text(json.dumps(err,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def ref(p):
 b=p.read_bytes(); return {'path':str(p.relative_to(R)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
a=json.loads((D/'author_CPU_tests_v3.json').read_text());s=json.loads((D/'synthetic_terminal_cost_tests.json').read_text())
assert a['state_before']==a['state_after'] and a['check_count']==45 and s['check_count']==16
manifest={'schema':'formal_main_v2','kind':'spatial588_typed_predispatch_CPU_candidate_delivery','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'CPU_candidate_not_production_admitted','root':str(R),'candidate_directory':str(D),'control':ref(D/'control.py'),'policy':ref(D/'policy.json'),'author_real_history_CPU_checks':45,'synthetic_terminal_cost_checks':16,'real_prior_GPU_seconds':395,'synthetic_cost_excluded_from_GPU_ledger':True,'actual_new_GPU_submissions':0,'actual_new_scientific_trials':0,'actual_P_new_invocation_verify':False,'actual_full_terminal_consumer_executed':False,'full_production_chain_complete':False,'legacy12_compatibility_proven':False,'eligible_for_current_action_global_freeze':False,'scientific_settings_changed':False,'sealed_values_read':False,'production_state_written':False,'Git_operations':False,'state_at_real_CPU_test':a['state_after'],'source_bindings':a['history_control_sources'],'files':[ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='delivery_manifest.json']}
(D/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'delivery_manifest':ref(D/'delivery_manifest.json'),'files':len(manifest['files']),'new_GPU_submissions':0,'status':manifest['status']}))
