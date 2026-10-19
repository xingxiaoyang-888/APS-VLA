# Long16 原科学开发计划候选

这是服务器 CPU 准备结果，不是运行结果、root 审批或提交授权。

## 已完成范围

- 全部 Long 18 个选择器及4参考的身份由原 formal_execution_manifests.py 从真实训练报告、部署收据、原训练根审和同源准入重新构造。
- 仅规划未开发的16选择器：A/B128 seed23/41，A/B256及64 seed17/23/41。分成8个A/B pair，每片同一原100开发初态，共200 trial，合计1600。
- 原 Long600及10531 GPU秒完整保留。本候选不将它们归为新动作身份，不用旧成功率选择方法；原6方法的动作身份迁移单独 HOLD。
- 原173源、科学配置、method IDs、selected checkpoint、Long520/wait10/chunk8/env0/runtime17不变。
- 采用原 pure planner 真正读取 canonical R manifests 和完整259行登记快照。没有 Evidence 映射、state过滤、源码替换或 prior_contract 补丁。
- 8份 manifest 先私有生成，由 root 原字节发布。科学计划输出仍在本目录。

## 入口和验证

prepare.py manifests 调原 source_contract、suite_rows、make_execution；输出manifest_index。root发布后 prepare.py plans 调原plan完整8次并保留full registry观测快照。实际科学来源和冻结文件在前后重哈希。
所有运行经已审 server_control_transport_v1、明确入口SHA；命令原件位于 manifests_a2.command.json、plans_a1.command.json、tests_transport_a1.command.json。审核器可按plan_arguments与完整state_snapshot直接调用原planner比较全部输出；不能把旧state快照当以后提交的实时状态。

31项有界测试检查真实 prior_contract 的全登记状态、旧6重叠、未知/待定占用，以及缺失/重复/错误方法分片和fresh计划边界。8份实际科学计划另在真实完整证据上运行，不由合成测试替代。

第一次 manifests_a1 仅因错误选了私有transport日志目录而被原transport拒绝，未执行prepare.py、0GPU；日志保留。随后依根授权使用固定control_transport目录通过。test_candidate_initial_unrun.py.txt只是未执行的初稿，后来把duplicate fixture明确选为formal作业，未伪造失败测试。

## 依赖与部署边界

science_dependency_closure.json 是完整根审科学证据闭包，不等于GPU运行必需清单。runtime_science_input_projection.json只汇总原plan的watched_files及publish_files；S目标必须173精确SHA，P目标必须同项目原相对路径。checkpoint只列服务器路径/身份与root实际SHA证明，不复制、不加载权重。

新的action runtime有效计划需由既有contract.effective_plan创建，不能执行旧科学计划作为新动作语义。尚缺每片新的action_execution_contract、effective_plan、prepared invocation、runtime_readiness及root/独立精确证明、最终R→P部署与未改wrapper.verify、单次新授权、实时容量/预约/pending门。此目录不生成上述批准或可执行授权，不预留GPU，不修改state/P/Git。

4小时1L40来自原planner固定资源。旧600总10531秒仅作已有成本参考，不是这8片的运行时间保证。若未来单片timeout/错误，应保留实际账本和费用重新审查，不能自动重复提交或删掉记录。

最终0/35200仍封存。完成本候选不满足22方法开发全覆盖、O2A同执行身份或全局release。
