# v4 一次性控制层候选（最终代码已冻结，独审待完成）

本目录只派生已审的 v3 控制层；作者未预留 GPU、未写正式 state、未发布 invocation、未查询或提交 Slurm。root 已分别签署 v4 配置并在其独立事务中预留未来空槽，来源见 final_binding.json。

6 个新 v4 源文件已由 root 原字节发布；action_adapter 和 constructor CPU 收据继续原 v3 路径。所有旧 v3 文件及 R/S 173 科学源不变。templates 中的外层封装始终是未签模板，不是生产配置。

最终入口：.local/action_v4_autonomous_dispatch_1940/entry.py
SHA：e259572effecf20f8769db47edfd1ac46799e8f50517fe3c98d6dfee919fef56
facade SHA：dd662101cf4e0546784d071925d86d1fd8d3b7a6dafc55fb6dbd74e58b55129e

默认只检查：--entry-sha256 <上述SHA> --check-only
正式提交额外需要：--submit --root-reviewed-submit，且必须经已审 server_control_transport_v1，使用唯一 --audit-relative。最后一次 root 实时 check-only 必须确认新 reservation、controller、全部已登记 Slurm、GPU 空槽、无 invocation 和无旧尝试。8 卡满时不提交，不取消健康作业。

34 项 CPU 事务回归使用候选目录内隔离 synthetic 项目和明确标记的 CPU 假登记，不能充当真实科学门槛。另有 3 项 CLI 拒绝门验证。真实生产只读 check_contract 验证 290 文件部署闭包和 R/S 双根 173 文件；不读取权重或封存状态。原 submit.py 与 gate 不改，shared writer/CAS、全部 Slurm 查询（CPU仍须真实证实0卡）、unknown/pending fail closed、one-shot、node exclusion 及成功后消费自身 reservation 保持原逻辑。

root review 不反向绑定最终 facade/entry，避免 GPU config→reservation→facade 的哈希环。独审收据在上游配置之后签署；同一 entry 精确 SHA 完成独审并经 root check-only 后才可考虑单次提交。

v3 仍失败 4/16，303 GPU 秒及所有历史结果保留。此候选不授权科学闭环、不开放封存最终初态。v4 必须另有真实完整 16 格 GPU 验收。
