# 历史开发动作范围审计候选

仅供下一轮 root/独立审计。没有实现新适配层，没有证明新旧执行等价，也没有授权复用或重跑。所有写入均在本目录；未改 results、源码、state 或 Git。

实际读取三份已登记 development 账本，先绑定已交付 root review 和 verified pull SHA，再流式检查原行、调用覆盖和动作。未读取任何最终初态或权重。

| 套件 | 终态 | 已记录 chunk | policy 调用 | 已执行动作 | 未记录 chunk |
|---|---:|---:|---:|---:|---:|
| Long | 600 | 23179 | 23179 | 183676 | 0 |
| Object | 600 | 11727 | 11728 | 92001 | 1 |
| Spatial | 12 | 122 | 122 | 917 | 0 |
| 合计 | 1212 | 35028 | 35029 | 276594 | 1 |

全部已记录 normalized/environment chunk 为有限 `[8,7]`。仅 environment 动作适用原阈值 `abs <= 1.00001`；normalized 预测超界不作错误。全部 executed 动作按 IEEE754 float64 小端字节与 chunk 队列前缀精确比较，包括有符号零，无容差或截断。每个 trial 保存原 start/result 行的字节 offset、长度和 SHA（包含换行），以及旧 run/source/adapter/execution-manifest 身份。

1211 条正常终态完整覆盖所有 policy 调用。Object 原第1073行 policy_error 原样保留：7个已有 chunk、56个已执行动作；第8个 chunk 数值未记录，不能从本审计恢复，也不能判断新适配层执行结果。`retained_policy_error.json` 单列该证据。结果不生成替换成功率表。

真实审计第一次执行即通过，用时约7.69秒。10项小型合成合同测试通过，覆盖 normalized 超界与环境阈值区别、阈值边界、非有限值/形状、精确队列前缀、早停、缺失调用、原错误保留和 final/未登记路径提前拒绝。

首次合成测试后、真实审计运行前，检查实际 pull writer 的状态是 `verified_nonweight_snapshot`，将草稿中预想的 `completed` 对齐到该精确状态；没有放宽验收、没有失败的真实审计或GPU调用。`synthetic_tests_v1.log` 保留该对齐前的合成运行，`synthetic_tests_v2.log` 对应最终源码。实际日志为 `actual_audit_v1.log`。

从项目根复算（新目录名，避免覆盖本轮产物）：

```powershell
python -B -m unittest discover -s .local/action_execution_compat_legacy_audit_0452 -p test_audit_legacy.py -v
python -B .local/action_execution_compat_legacy_audit_0452/audit_legacy.py --output-name run_independent
```

`run_v1/report.json`、逐trial结果和单列错误均为候选证据。下一步仍需独立复算、实现/CPU/有界GPU验收及逐trial执行身份等价证明；本候选不解除任何门槛，final 继续封存。
