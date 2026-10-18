# 动作执行兼容候选：尚未部署

依据 `configs/experiments/formal_main_v2_action_execution_compat_v1.json`，从冻结的 `libero_runtime.run_episode` 原 AST 生成候选函数，仅删除 `abs(environment_actions) > 1.00001` 对应的完整 `if/raise`。不增加 clipping、缩放、重新归一化或方法特例。

入口为 `adapter.install_action_execution_compat(...)` 上下文，显式传入项目目录、冻结源码目录、已经加载的 `libero_runtime` 与 `formal_trials` 模块、候选 SHA 和事件回调。它同时绑定两模块的 `run_episode`，并在正常或异常退出时恢复原绑定；拒绝重复活动安装、嵌套安装、未知来源和作用域篡改。没有 CLI、GPU 或提交入口。

保留原 `PolicyChunk` 形状及有限值检查、watchdog、reset/wait、chunk、任务时域、成功条件、动作后处理、动作日志和错误分类。有限动作不作任何新数值变换，由原循环原样传给环境。身份返回值明确 `candidate_only=true`、`deployment_authorized=false`，不能作为实际闭环或最终集放行证明。

CPU 测试使用冻结函数、`PolicyChunk` 和观测哈希的原始 AST；仅环境、策略输出与时钟是合成的。没有加载模型、官方环境、控制器、开发或封存初态。测试验证范围内结果逐字段与逐动作相同、诊断值 `1.010742197890625` 原样传递、NaN/Inf/形状与 watchdog 错误、无新增 RNG、导入别名与异常恢复、来源及代码篡改拒绝。准确用例数和状态以同目录原始 XML、日志与候选收据为准。

仍需根对话后续完成：独立 CPU 审计；各套件实际 controller 配置/源码验收；全部方法统一新执行身份；已有原始开发结果的逐条等价/不可复用映射；调用方、收据和总账接入；预登记有界 GPU 工程验收及其独审。当前候选不修改或替代旧 1212 条记录，不自动重跑失败试次，不改变训练或选模，不开放最终集。
