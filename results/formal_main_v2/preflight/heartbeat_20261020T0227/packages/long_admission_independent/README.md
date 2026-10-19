本次仅审查 8 份 Long 全新开发计划的运行前来源与部署依赖：16 个已完成训练的 A/B 选择器，每方法原固定 100 个开发初态，共待运行 1600 条。原 Long 600 条及成本保留；本次没有产生 GPU 结果。

实际服务器检查全部通过：13 项共同组件/来源检查，125 项发布后依赖检查，245 项逐计划后验检查。执行原函数 NativeIO、validate_authorization 和 P 中实际 wrapper.verify；未替换函数或伪造上游资料。8 份旧科学入口在独审中实际通过，随后 8 份新完整 P wrapper 又独立通过。既有组件 CPU 与 v4 的 16 格 GPU 工程收据仅按原 SHA 继承，不重复计为新实验。

所有计划均为 fresh development，prior_review=None、prior_job_ids=[]、transition=None、resume=False。没有旧动作前缀被顶层新版本包装。root、独审、readiness 对 scientific/effective/action contract、内容 plan SHA 与 method_ids 精确绑定；运行期各 read_ref 依赖均已在 P 原字节发布，包含 effective_plan 和两个嵌套审核收据。prepared_invocation 只在 R，正式 invocation 两端仍不存在，符合事务提交边界。

最终状态见 post_readiness_independent_review.json：production_chain_complete 仅表示这 8 份具体开发计划的运行前控制/来源/发布闭包通过；actual_GPU_runtime_chain_verified=false、scientific_trials_completed_by_new_runtime=0。未调用 Gateway.run、publish、Slurm、模型加载或权重读取；未写 state/P/Git，未读封存值，未开放 O2A、全局冻结或最终评测。

读取时现有 Spatial CUDA 1 槽预约仍为 0aabce41556248f83877ce47a102ebb32817624eac4ad04a431862b098289c9d，8 份 Long 计划均无登记作业。后续 root 必须等待容量并执行 fresh 全登记 Slurm、共享锁/CAS、具体计划预约与一次性授权检查。运行后仍须审核真实 GPU journal、trial 和全部成本。旧结果等价、完整套件开发、O2A 和最终 release 均不由本次 CPU 准入推导。

主证据：
- actual_common_closure.json：共同 7 源及 runtime 依赖/组件继承；215 refs。
- eight_plan_actual_closure.json：24 canonical 文件 R/P 精确、253 个唯一 P/S 输入、8 个实际原入口、无缺件；1280 refs。
- post_readiness_independent_review.json：真实 root 签发后 8 个新 P 完整入口、授权和 metadata 检查；386 refs。
- 三份 check_*.py、三个 command/result/log 组保留实际执行及 audited transport exact entry SHA；不存在新 synthetic 测试矩阵或失败被删。

外层原代码对嵌套 root/ind 的最小校验没有逐项强制 plan refs；本次额外显式核对了全部 5 项绑定，防止复用来源相同但计划不同的旧 Spatial 许可。未来计划仍应执行同样精确检查。
