# 正式交付差距盘点（只读）

以 run_a4/gap_review.json 为最终收据。103 项真实元数据/原始日志检查通过，245 个文件引用；23 对训练的既有 root/独审收据、46 份训练报告和部署收据，以及旧开发三份终态收据绑定的完整原始文件均核验。没有重新反序列化 checkpoint，也没有重复训练完整审计。

- 训练已双审 46/72：Long 18、Spatial 16、Object 10、Goal 2；剩余 26。
- 已有开发清单仅覆盖 18/88 个不同部署身份（3 套件各首 6 个），40 个已完成选择器尚无开发清单：Long 16、Spatial 14、Object 8、Goal 2。Goal 的 4 个参考也未列入清单。
- 旧开发记录完整保留：Long 600、Object 600（含 1 条 Dense policy_error）、Spatial 12。它们均为旧动作接口；当前新动作语义下四套件完整开发收据、正式 O2A 收据和最终闭环均为 0。
- Spatial 旧 12 + 新 588 的混合继承链不能通过严格 whole-ancestry O2A/冻结门。修 attempt03 的控制接口并不能消除此交付障碍。Long/Object 旧 600 也没有新旧动作等价证明；顶层标记不能改写祖先语义。已发布 guard 仍须正式消费链集成，不能声称已完成生产放行。

最短下一步：先为 Long 尚未评测的 16 个选择器建立 8 个 A/B pair 的 fresh development 计划，每个固定 100 初态、200 次闭环，保持原 4h 资源请求及选中 checkpoint。它们不与旧首 6 方法重叠；原 Long 600 次累计 10531 GPU 秒，只作实测资源背景，不承诺新 pair 的耗时。root 正在准备原 planner 实际计划，本盘点不替代 per-plan 源、发布闭包、容量或一次性准入。

并行准备 Spatial/Object/Goal 的新增完成方法清单时，须先处理 7 个 pair 的真实源收据路径缺项：Object128s23/256s17，Spatial256s17/23/41、64s17/41。它们已有终态 root/独审整合收据，但缺原 source_provenance 必读的 training/segment_reviews/<最后 job>.json。不能伪造 proof；须依据真实完整原始审计输出作规范化或显式版本化兼容。Long 全部 9 对的该 canonical 路径存在。

旧方法重新评测的最小修正是登记明确的新动作执行身份，保留旧 raw、失败、费用与 checkpoint；开发初态和科学定义不变。原 planner 只按 suite/stage/method-state 重叠判重，未识别动作版本，因此直接新建全 22 方法 fresh run 仍会被拒绝。不能改目录、过滤历史 state 或拼接旧前缀绕过。新身份并非用户要求避免的“身份完全一致”重复；但本审计不签任何迁移、重跑或等价授权。

O2A 可先准备固定 Dense 开发观测采集：10 任务各首/中/末，共 30 观测，源和采样规则固定。现原 planner 的 full/components 阶段需要 complete global freeze 与采集收据；还需新动作链的实际运行证据、独立 raw 审核及消费门集成。最后须全部 72 checkpoint +16 参考身份、四套件完整合格开发收据和最终清单冻结后，由 root release 才能开放 35200 条最终评测。16 格 GPU 工程成功不作性能结果。

审计执行历史全部保留：a1 因 transport 不允许 .local 日志路径而在执行前拒绝；root 允许工具规定的 control_transport 日志后 a2 在已完成 raw 检查后发现审计脚本使用了 jobs 而非 registered_jobs 字段；a3 错把两份已签 typed 独审的 passed_complete_training_only 当成 passed，a4 按确切 kind/status/completed_by_arm 修正后通过。它们是本审计提取器修正，不是实验产物失败或科学门槛放宽。Spatial summary 的 unique_initial_states=100 是登记面板，实际已有终态仅覆盖 2 个初态，两者已分列。

最终入口 audit.py SHA f22671bfe8e2429eb6977eb6557af08c445ffc5c8fde309f2468efb3b84fb3ff。完整命令见 command_a4.json，结果与工具原始日志均归档。只读服务器记录，无 Slurm/GPU 调用，无 state/P/Git 写入，无封存值读取，无 readiness/release 创建。
