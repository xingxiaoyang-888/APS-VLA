# Goal 原前58条工程诊断登记

2026-10-21：原 Goal256 seed17 作业3049679虽 Slurm 正常结束，但200条开发因配对初始观测不一致未接纳。短探针3050711未复现，原因未定；原200条与新增 Goal 科学开发继续 HOLD。

本次只重走原清单前58条、29个开发初态，使用相同A/B checkpoint、原模型加载顺序、环境seed0、runtime seed17、等待10步、chunk8、最多300控制步。动作重新由策略计算，不强制回放历史动作。被动记录reset、set-init、等待和首次策略查询附近的观测、模拟器/RNG身份，检查原动作与观测是否一致；不能仅凭token相同认定输入相同。

观察器AST钩子完整白名单、首个采样异常处理、落盘后模拟器/RNG复核均已修复并经独立CPU审计；root已在实际R/P路径复核原wrapper、选中checkpoint字节及固定58身份。CPU验证不作为真实GPU通过。冻结173源文件保持原字节。

仅允许1次、1张L40、7CPU、64GiB、30分钟，计入8槽上限；不自动重试。先持共享writer锁登记pending与容量，再held提交，按真实token/作业ID/入口/资源核对并登记后才release。未知ACK保留pending，不重发。原训练72组已完成，不重启CPU训练控制器。

完整Slurm分配、加载、异常和观察器I/O计入成本；观察器有额外开销，不提供正式延迟数据。结果新增科学trial为0，不解除任何Goal或最终评测HOLD。返回58条也不代表已解释原异常；真实产物须另行root和独审。

配置与授权见[工程登记](../results/formal_main_v2/engineering/goal_prefix58_20261020T1825/root_authorization.json)，源码发布见[发布收据](../results/formal_main_v2/preflight/heartbeat_20261021T0225/Goal_prefix58_publication.json)。
