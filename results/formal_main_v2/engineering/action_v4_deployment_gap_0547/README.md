# 动作 v4 正式入口接入缺口（只读）

3039197 已由 root 与独审验收：16 格、4 个开发初态、814 GPU 秒。它是工程证据，新增正式试验数为 0；封存评测未开放。本次未运行测试、GPU 或提交，也未改生产源码/状态。

建议只做一个有版本的操作入口，保留冻结173文件及原科学 runner。需要同步四处闭包：

1. **执行 scope**：原 `formal_evaluation_adapter.run` 尚未安装已验收 v3 `action_adapter.py`（b8a1632e…）。在其外层组合动作 scope 与现有 Object/Goal 资产 scope，保留 enter/exit、失败及恢复原绑定的原始收据。wrapper 必须明确新入口及支持文件 SHA。
2. **测速和审核残留幅值限制**：`profiling.py:325`、`review_formal_downstream.py:433`、`analyze_formal.py:505/581` 仍要求执行动作绝对值≤1。v3 只改 run_episode，未覆盖这些位置。新合同下只修这一语义；8×7、有限值、原始动作逐步相等、后处理和计时边界全部保留，不剪裁。`formal_profiling` 的 from-import 别名也须校验。旧证据按旧版本保留。
3. **自动控制器共存**：旧 downstream CLI 会 legacy refresh，且把 CPU 控制器计入8卡。不可直接调用。窄 facade 必须完整查询登记作业，验证 CPU0，采用共享锁/CAS、GPU8上限及新预留槽，保留 pending/未知提交结果及 autonomous 状态。
4. **证据消费者**：新合同要贯通 plan、invocation、wrapper、raw reviewer、root receipt 重建；仅挂一个未登记外层不可验收。历史 prefix 与 policy_error 不重写；旧输出续跑须有明确兼容迁移收据。

生命周期不需照搬四次加载：当前正式评测和测速每进程仅加载一个套件基座一次。v4 probe 的 guard 强制四个 checkpoint，直接移植反而不匹配。保留单进程单套件单次加载，引用 v4 来源验收；若抽出单次 guard，只需针对首次/重复/异常及 Goal 组合做有界 CPU 验证，不人为加载四套件。

`gap_review.json` 列出35个实读文件/测试入口的确切 SHA，以及每处行号和继续条件。已有 CPU 回归集中在 `test_formal_evaluation_adapter`、`test_formal_downstream_supervisor`、资产集成、锁、raw reviewer 和 `test_formal_profiling`；本轮仅登记入口，未声称已执行。

下一步：完成上述操作候选并独立 CPU 审核，root 核对准确源/配置/所选 checkpoint/开发面板后，在空槽提交首个登记开发入口；O2A 仍需原88身份冻结与固定观测面板。最终初态必须等待原全局 release，不因工程通过提前打开。
