# 动作执行 GPU 工程验收：传输 v2 候选

本目录仅保存 CPU 修正候选，未发布、未连接服务器、未提交 GPU、未写真实监督状态。v1 已发布源码、登记、根收据、提交失败及原始日志均保持原字节；此候选不能凭旧 root receipt 直接执行。

## 真实失败与最小修正

原提交于 2026-10-18 07:54Z，在 `remote_attempt_absent` 后的首个 `remote_hashes` 调用触发 Windows `CreateProcess WinError 206`。293 个路径与散列脚本被放入 SSH 命令参数，超过命令行长度限制。失败发生在文件 publication、pending 和 sbatch 之前；没有新增 GPU 作业或 GPU 成本。此前已执行的根查询及失败仍保留，不称其从未运行。

原根失败收据 `results/formal_main_v2/preflight/action_execution_gpu_submission_0626.json` 的 SHA 为 `9e18b0149bed9eb2b95ef194b4f25a323c2691a0e8dcc4f5e13c4d858003a2e2`；本目录 `observed_submission_failure_v1.json` 是逐字节副本。

`submit.py` 唯一函数变化是 `remote_hashes`：同一段远端 Python 散列源码，经 `subprocess.check_output(..., input=script, text=True, encoding='utf-8')` 送入短命令 `python -B -` 的 stdin。原路径/符号链接检查、逐键 SHA 校验、缺失返回 `None`、非零退出上抛完全保留。其他函数 AST 不变，包括容量、单次 stage、原子发布、pending 和不明提交禁止重投。

## 完整新命名空间

root 已授权新 v2 命名空间，避免覆盖 v1 或跨版本共用输出：

| 对象 | v2 候选值 |
| --- | --- |
| stage / probe GPU_VERSION | `formal_main_v2_action_execution_compat_gpu_v2` |
| output root | `P/results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v2` |
| source | 上述 output root 下 `source/` |
| registration | `configs/experiments/formal_main_v2_action_execution_compat_gpu_v2.json` |
| invocation | `results/formal_main_v2/invocations/formal_main_v2_action_execution_compat_gpu_v2_attempt01.json` |
| stage lock | `results/formal_main_v2/stage_locks/formal_main_v2_action_execution_compat_gpu_v2.lock` |
| one-shot marker | 新 output root 下 `attempt01.launcher_started.json` |
| output attempt | 新 output root 下唯一 Slurm job id 目录 |
| dispatcher version | `root-action-execution-engineering-dispatch-v2-stdin` |

`P` 仍是原服务器 CTI-VLA 路径。冻结 source snapshot S、173 文件、模型和 checkpoint 身份不变。

精确源码变化见 `v1_to_v2.diff`：

- `submit.py`：上述 stdin 传输变化，其他函数不变。
- `launcher.py`：仅 `STAGE` 和 `DISPATCH_VERSION` 两个工程常量；ENTRY/LAUNCHER/WRAPPER/SUBMITTER/OUT/INVOCATION 从新 STAGE 自动派生。
- `probe.slurm`：仅内嵌启动器的 stage 字符串。1 L40、3600 秒、`--no-requeue` 不变。
- `probe.py`：仅 `GPU_VERSION` 一行；候选科学协议 `VERSION`、动作代码、16 cell 计数、每格原固定目标、校验及输出结构不变。
- `candidate_manifest.json`：与 v1 原字节完全相同，SHA `12b359cd6dfb261a5c5cb5c3876b06a556d18f23cece5e803cebe840751c8b04`，包括所有 selected checkpoint 与任务/初态身份。
- `gpu_registration.template.json`：只供新登记参考，仍 pending 且 `gpu_submission_authorized=false`，不是已通过或可执行的 root 登记。

## root 后续绑定要求

1. 独立审阅本次实际 Windows 回归及精确 diff。旧 53/32/22 CPU 测试可作为 unchanged code 的历史证据，不能称在新 SHA 上重跑。
2. 为新 probe SHA 和新发布路径生成新的 typed candidate independent / root CPU receipts；三键 `candidate_identity`、`candidate_files`、`evidence_sha256` 必须绑定新 probe，不复用 v1 的通过身份。动作适配器本身未变，其既有独立收据可按原精确 SHA 继续使用。
3. 新 root receipt 绑定 `launcher.DISPATCH`、新的 registration 路径、移除 `cpu_reviews.root_acceptance` 后的完整登记 intent SHA，以及完整 P/S deployment 列表。root receipt 不包含自身或最终 registration SHA，继续避免哈希环。
4. 最终 registration 对新 root receipt 全 SHA；提交 CLI 独立给出最终 root、manifest、registration 三份 SHA。新的 invocation 再绑定全部 watched files。不得改 v1 收据让它宣称覆盖 v2。
5. root 先 CPU `--check-only`，再在锁内刷新全部已登记请求、确认不足 8 槽及无 pending/本 stage 历史，方可提交新的唯一尝试。失败后的人工 v2 修正不是自动 GPU 重试；v1 无 GPU 作业事实须附原失败链。未知提交结果仍保留 pending，不能再投。

## CPU 回归边界

`test_transport.py` 使用真实 Windows 子进程：本地 Python shim 仅替代 SSH 入口，执行生产 `remote_hashes` 的原样 Python 脚本。293 条合成 metadata 路径包含空格、引号和 Unicode；原 v1 argv 必须实际触发 WinError 206，新 v2 通过 stdin 返回全部精确 SHA/缺失值。此测试不是模拟 Windows 长度判断。

其他测试独立核对 invalid JSON/错键/坏 SHA/非零退出的原拒绝行为、v1→v2精确源码差异和 manifest 原字节、原失败收据、所有未改事务函数。另用已登记 293 条真实 metadata 路径**仅构造** single-path preflight/commit/scp/sbatch 命令并测 Windows 字符数，不执行传输。没有读取权重、cache tensor、最终初态；没有 SSH、SCP、Slurm 或 GPU 调用。

真正 Linux stdin/SSH 传输、远端发布和 GPU 16 格仍待独立复核及 root 的新登记后验收。本次没有修改科学门槛、重跑 Object 旧失败 trial、开放 final 或新增统计结果。
