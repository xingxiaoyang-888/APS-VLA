# G5 新动作版本 raw reviewer / consumer（候选）

状态：仅作者 CPU 候选。没有新 scientific GPU 执行，没有 readiness、final release 或 Slurm 提交；本作者不声称对整链独立审计。

固定新版本 `formal-downstream-action-v1`。最终拟发布路径：
`scripts/ops/formal_action_deployment_v1/{reviewer,consumer}.py`。实际审核必须从合同绑定的生产路径执行；本目录不是可上线的替代路径。

## 接口

`reviewer.review(project, *, job, invocation_ref, pull_ref, registered_jobs, expected_contract_ref)`

- project 是服务器控制仓库 R；job 必须来自不可变终态正式作业快照。registered_jobs 仅含明确终态 CTI-VLA formal 记录，保留全部相关历史失败分配，不读取 live state。
- 三个 ref 均为精确项目相对 path / SHA256。实际 invocation 必须是新 outer version，且 registered job 逐字段承接 wrapper、entry、runtime_readiness、action_execution_contract、scientific_plan、plan_sha256、source_provenance。
- 先验证真实 effective plan/readiness、当前 source closure 与 SHA pull，再核原 adapter 和新 action identity/events/completion 的同次调用、顺序、恢复及全部成本。
- 不调用运行后的 wrapper.verify；恢复时只有本 run 的 trials.jsonl / closed_loop_report.json 是明确两项可增长输出。原 prior root/pull、精确前缀字节、config/panel、全部旧失败继续绑定。
- 原 validate_invocation、suite_rows、runtime_inputs、adapter、rollout/collect/profile 和 allocation_cost 科学函数保留。私有函数命名空间只替换新 outer shape gate 和幅值检查；不改旧模块的绑定。
- 两处离线变化均精确 AST 校验：analyzer 的 environment_actions 幅值 if；trajectory 的 executed-actions 幅值 conjunct。没有 clip、normalize、截断或数值修改；shape/finite/token/checkpoint/cadence/原样执行等检查保留。
- Object/Goal expected identities 由原 metadata-only verifier 在 P/S 独立生成，全部 watched metadata 显式 P/S→R 同字节校验；不从 raw enter identity 回填 expected，不加载 tensor。
- 失败或不完整 runtime 不能产出此接口的 passed root review，应保留原字节/失败分配并走另行失败审查。成功工程 prefix 的 scientific_complete 仍为 false。
- 当前函数仅返回供 root 决定发布的重建结果；不会写 root 收据、state 或任务。真实 producer 标准 kind 仍为 root_downstream_review，新增 execution_version 分流，绝不将新执行伪装成旧执行。

`consumer.review_downstream_output(evidence, reference, *, expected_stage, suite, run_root=None, require_complete=True)`

- 旧真实记录 → 固定旧 whole-chain consumer 原样调用；未知版本拒绝。
- 新记录 → 从其 immutable registered-job snapshot、原 invocation/pull/contract 重建新 reviewer，除 reviewed_utc 外全字段精确比较，再复核每个 SHA。
- require_complete 默认 true；false 仅用于完整审核成功的工程 prefix，不开放科学门。
- final 在任何 ref/file 访问前拒绝。只有四个精确 development.json 与四个 final_registry.json 索引元数据路径白名单；sealed/value/test/weight/symlink/.. 仍拒绝。

`consumer.require_matching_o2a(evidence, development_refs, full_ref, components_ref, *, suite)`

- 同 checkpoint、完整 88 实例 freeze/四套件已完成 dev 根记录、30共同观测、22实例、14300完整调用、全延迟/独立 components 原协议保持。
- action semantics 由 source/files/contract 定义，只有 stage 字段从比较中移除；suite/model/source/部署实现在比较中。
- 旧动作语义与新语义之间尚无登记等价映射时拒绝，不能仅靠旧 source identity 放行 O2A。components 不替代 full。

## 实际作者 CPU 验证

- a1：48 passed。范围：守卫、实际原两幅值 AST 推导、17种其余科学错误、真实 pull schema/锁排除、旧分发、前缀、O2A identity。
- a2：8 passed / 1 failed。原 helper 的分层整合真实暴露新 Evidence 缺 source_provenance 属性；同时 root 指出缺 require(paths)。原源版本、命令、日志、XML均保留。
- a3：修正两项原 Evidence API，且增加四个精确 final_registry 元数据白名单（root 独立指出）。5 passed。
- a4：最终 62 passed，28.51 秒。新增重哈希后的混合 job/seq/identity/restore/time/return/unknown/code 负例以及 synthetic-runtime 拒绝。原 trial/adapter writer→原科学 parsers→新 root reviewer→新 consumer 的分层整合通过。
- 分层整合的上游完整训练/GPU gate 和实际新 runtime GPU 生命周期是明确 synthetic stand-in；原科学 writer/解析、outer原始证据/成本/重建 dispatch 实际执行。测试不是新的 GPU 通过证明或完整生产链 readiness。
- 原 173 个科学文件及固定旧审核依赖按登记 SHA 复核；没有 source、state、Git、Slurm 或实际产物写入。

所有四轮 source snapshots、command JSON、原 log/XML 保留。tmp_a* 是配方可重建的隔离 synthetic 复制品，不参与正式科学结果，不是需要交付的原始实验数据；未删除。根归档可仅使用 delivery_files.json 列出的文件。

## 保留的阻断

1. 全部7新模块、runtime/gateway/root链尚需交叉独审和 root 精确 readiness；作者 CPU 报告不能代替。
2. 尚无本新入口实际 scientific GPU raw 产物，不能报告新成功率/延迟。
3. 旧→新逐 trial 等价复用映射未登记，O2A 对此 fail-closed。
4. 同版本第二次恢复的 G5 raw prefix 校验已定义，但旧纯 planner 对新 prior receipt 的接入若拒绝，仍需单独明确 dispatcher；不得伪造旧 receipt。
5. 失败 runtime 使用独立失败取证流程；本接口不会将失败改成 passed，也不自动重试。

归档/发布只由 root 执行。权重和封存值始终不在候选读写范围内。
