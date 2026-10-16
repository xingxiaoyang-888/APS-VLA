# 正式Goal组件路径兼容修正

2026-10-17 04:28（北京时间）。状态：实现、CPU独立审计、运行登记及服务器原字节校验均已完成；8个GPU槽仍在训练，完整真实GPU复验等待下一空闲槽，Goal正式训练尚未放行。本修正仅解决对应官方权重的加载路径，不改变冻结VLA、DIE、监督目标、h8、λ0.1或正式训练／评测面板。

## 真实失败与定位

Goal的3012296在模型加载前因清单额外说明字段失败15 GPU秒；该问题由既有元数据适配解决。复验3012483已完成原清单25项资产检查和基座加载，但`openvla_oft_loader.py`将动作头及proprio组件文件名固定为150000，Goal官方revision实际使用50000，于是失败186 GPU秒。两次共201 GPU秒及全部原始日志保留。

官方来源为`moojink/openvla-7b-oft-finetuned-libero-goal`，固定revision `c2d0f9fbbd82674683b397ff923168a12f6a307b`；[原清单](../configs/assets/openvla_oft_libero_goal.json)与[服务器只读核验](../results/formal_main_v2/preflight/goal_official_component_probe_20261016.json)一致：

| 官方文件 | 字节数 | SHA256 |
|---|---:|---|
| action_head--50000_checkpoint.pt | 302242654 | b97c2e8939ede32d8a1b29e9565d70f22040ba9e54925665e81989a0cc13ccff |
| proprio_projector--50000_checkpoint.pt | 67275184 | 780595e9cca5292348697686f9ccc83d39d9d3d303e860d62c6d4609952dfff1 |

文件齐全；不重新下载、不在官方目录建立150000别名，也不复用其他套件组件。

## 有界工程方案

保留原173文件及现有六文件元数据运行合同。外置Goal专用wrapper在同进程调用原wrapper，仅在严格作用域内，将该Goal固定模型目录中两个精确150000请求映射到对应官方50000路径；仍由原组件加载函数执行`weights_only`读取、DDP前缀处理和后续严格模型加载。映射前后核文件大小／SHA，退出恢复原函数，其他路径、重复或越界调用拒绝。

新增`component_compatibility`身份与四份文件SHA独立登记，不用原源码SHA掩盖新增运行代码。保存独立identity、逐调用事件及completion，交叉绑定原metadata job receipt和原字节回存证据。root审核必须同时验证两层合同；Object／Long／Spatial不带此Goal合同。训练入口、官方dense参考入口和选模规则均不改。

CPU验证覆盖精确两映射、原函数调用、异常恢复、目标篡改、重复／越界调用、两个wrapper实际组合及严格审核的拒绝分支。服务器Python与本地审核Python版本不同，代码对象一致性在同一生产进程内验证；root绑定原文件SHA和原始证据，不将跨Python字节码不同误判为科学实现不同。

## 登记、验证和下一步

[执行登记](../configs/experiments/formal_main_v2_goal_component_execution_v1.json)绑定原173文件、元数据六文件合同、新增组件四文件合同、root提交器及[修复记录](../results/formal_main_v2/preflight/libero_goal_component_path_repair_v1.json)。[root审核](../results/formal_main_v2/preflight/goal_component_execution_root_review.json)保存全部CPU测试与独立收据：双wrapper组合25项、审核链35项及85项原有回归、提交器50项均通过。最初Windows路径分隔符及测试目录归属失败保留；修正没有放松生产路径边界。

[服务器同步和Python3.11预检查](../results/formal_main_v2/preflight/goal_runtime_sync_20261016T202343Z.json)确认新增四文件原字节、173原文件及原元数据合同一致；该检查未加载模型张量、未调用GPU，不能计作F00验收。[只读复验计划](../results/formal_main_v2/preflight/goal_component_acceptance_retry_plan.json)已生成，尚未提交。下一空闲槽由root使用`formal_goal_asset_supervisor.py`提交原始完整F00、三预算F01和F03，禁止重复使用旧的仅元数据Goal入口。

真实验收通过、回存两层运行证据并经root复核后才训练。Object／Goal开发、最终及测速的[下游显式接入](正式资产清单下游接入待办.md)仍未完成；保持原全局release门槛，最终初态继续封存。
