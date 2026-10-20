# Goal 查询前配对门槛独立 CPU 审计

候选 manifest ab07dec9d6fcf8334c52b9bb836ce3b79402a3b77268d0c85c63ad3cdb42b4e4 的 CPU 范围通过。审计没有提交 GPU、查询 Slurm 或改生产状态。

核验了全部 14 项候选文件、原证据归档 491 个唯一成员及 SHA/大小；直接重算合成原始 ledger 的去时间字段等价性、58 条/29 配对、174 查询、986 动作，并核对 348 个查询边界的原始数组 blob。复核固定原 prefix 与候选草案身份，173 个冻结文件在 R/S 前后均保持原字节。

独立执行原作者 66 条断言，仅将 OUT 重定向到本审计目录，D/R、源码、样本、断言不变，变更证明保存在 author_reexecution_derivation.json。另写独立拒绝检查，确认缺失观测在策略前停止、环境错误保留 infrastructure_error、cleanup_error 与原 result 保留、非有限 PolicyChunk 保留原 policy_error；均不得启动下一试验。错误初态 hash、方法身份、无前置的 post query、漏查询、t0 标记、控制步类型和非 fixture sink 均拒绝。共 2784 项检查含逐文件/逐 blob 校验；这个数字不是独立科学样本数。

静态确认插桩 AST 反向投影保持原循环与 timer 语句，动作兼容上下文依旧为已验收的一处分支删除；新 step_after 仅作动作字节记录。捕获与比对不进入原 policy timer，但必然扰动墙钟/I/O，不能用于正式 O2A 测速。状态与操作符在失败/成功退出后恢复。现有保护对 invalid chunk 的过早 gate 错误会 fail-stop 并保留侧证；真实接口还须新 P 包验证，不能只依此 CPU 包推断。

未通过或未审范围：新生产包/入口、完整 P 来源闭包、root runtime readiness、独立 runtime readiness、真实 MuJoCo/GPU 被动读取、Slurm 注册/容量预留/ACK、真实终态收据及消费者。下一次最多 58 条工程运行仍须 root 单独集成与登记。它既不能精确重放缺失的历史 before-query 字节，也不能证明旧第57条 t0 原因已查明或修复。旧 200 与新增 Goal 科学开发继续 HOLD；final release 为 false。

原作者证据原包保留；本包 CPU_evidence.tar.gz 无损归档本审计新生成的合成数组/ledger，逐文件索引可验证。所有原始文件仍留服务器，无权重、封存值和新科学结果。
