# 服务器工作区与 GitHub 同步

2026-10-19 用户新要求覆盖旧的本地保存规则：本机不再新增项目文件；代码、文档、配置、日志整理、审计、Git 提交和非权重归档均在服务器完成，并同步到 https://github.com/xingxiaoyang-888/DIWA.git 。

- 唯一控制工作区：/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo。通过现有 SSH 别名 tongji-cvpr 操作；Windows 端只在内存中传递命令与必要认证，不写临时脚本、结果或 Git 索引。
- 原运行目录：/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA。已有作业、快照、模型、checkpoint、数据与缓存保持原身份。模型权重和 checkpoint 只在服务器，不提交 Git。
- 非权重结果从运行目录整理到服务器控制工作区，再提交 GitHub。超过单文件限制的原始记录继续使用已审计的分块压缩归档，保留完整原文 SHA 与可恢复清单。临时测试副本、依赖安装包、官方原始数据和可重建缓存不直接加入 Git；有用的未集成代码及审计原件按哈希归档。
- AGENTS.md 是173个冻结源文件之一，保留原字节以维持科学身份。其旧 F 盘保存条款已被本次用户要求及本登记覆盖；其余方法、实验与门槛继续有效。
- 882个待集成与操作证据路径已按原字节恢复，两个旧大文件从既有归档恢复。见 results/formal_main_v2/preflight/server_storage_migration_20261019/restore_receipt.json。CPU synthetic 文件只能作工程证据，不能作为真实配置、root release 或 GPU通过记录。
- 服务器控制传输入口已通过20项CPU检查、12项独立检查和一次真实登记作业状态查询；旧 frozen ssh/scp tongji-cvpr 的含义仅在该子进程内转为同服务器操作，不改冻结源码或科学门槛。旧 v3 integration 的 ROOT == F:/CTI-VLA 断言仍需单独有界迁移审查，当前不可直接执行。
- GitHub 认证经 stdin 进入 scripts/ops/server_github_sync.py，仅临时用于指定仓库的 HTTPS 请求，不保存凭据。必须非强制推送并核对远端 main 与本次提交 SHA。
- 继续每90分钟的既有监督；正常运行时不持续轮询。每次只处理登记的 CTI-VLA 作业，先核对现有产物和活动作业再补位，最多8卡；最终初态仍须原全局 release。
- 已有本地副本尚未删除：自动审批策略拒绝了已核验临时副本的删除请求，仅返回 blocked by policy。当前工具无法完成本地清空，不应声称已删除；本机副本已停用，不再作为监督状态来源。

## 已验收控制入口

完整适配目录为 scripts/ops/server_control_transport_v1；bundle_manifest.json SHA为3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149。保留bin目录结构和执行位。只对已经过审的原控制脚本及其确切SHA使用该包装器；它不授权新实验、不替代pair/root release门槛。下面命令在服务器执行，后续调用必须改用全新的audit文件名，不能覆写本次记录。

    /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B \\
      /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/scripts/ops/server_control_transport_v1/run_server_control.py \\
      --bundle-manifest-sha256 3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149 \\
      --entrypoint .local/read_parallel_live.py \\
      --entrypoint-sha256 85592adfa7e52d70bad4930f0d6d5d99d0b2a625860ac107c206a17fe119cff2 \\
      --audit-relative results/formal_main_v2/control_transport/migration_status_20261019.jsonl

本次返回0，实时观察时刻为2026-10-18T16:27:38Z；198个正式作业累计723108 GPU秒，无活动作业。终态只是Slurm事实，需原回存和双审后才能推进下一500步。下一次定时监督负责这些已结束分段的复核与补位。

服务器直连GitHub曾发生空响应和连接超时，均在推送前的远端查询阶段中止，已保留两次失败收据。网络不通时可只读核实本机既有Git HTTP代理，并通过一次性SSH反向转发供服务器Git使用；仓库、Git对象与提交始终留在服务器。代理端口仅绑定服务器loopback，作用于该次Git进程，退出后关闭SSH转发；不改全局代理，不把项目内容落到Windows。若提交结果不明确，先核对远端SHA再重试，禁止强推。
