# 16-cell 工程验收提交候选

此目录仅供 CPU 审阅。它没有提交、连接服务器或修改真实监督状态；root 集成、复核并显式执行 `--submit` 后才可产生唯一作业。验收结果是 16 个 engineering cells，不是科学闭环 trial，也不会重跑 Object 的旧失败 trial 或开放 final。

固定范围：四套件，每套件 Dense、uniform128、A128 seed17、B128 seed17 各一次 chunk；1 L40、3600 秒、单次尝试、`--no-requeue`、不自动重试。probe 的完整科学输入、模型与实际 controller 验证仍由已验收 probe 执行，dispatcher 不改其行为。

## root 额外字段

probe 已定义的 root typed CPU receipt 不变。额外需要：

- `dispatch_contract` 精确等于 `launcher.DISPATCH`。
- `gpu_registration_path`：最终 GPU 登记的项目相对路径。
- `gpu_registration_intent_sha256`：用 `launcher.registration_intent(reg)` 计算。仅移除 `cpu_reviews.root_acceptance`，其余登记内容全部进入 canonical SHA。
- `deployment_files`：精确列表，每项 `{path, server, sha256, bytes}`。`server` 不重复；同一 `path` 可分别映射 P 与冻结 S，但 S 只接受 173 inventory 的原 SHA。
- `evidence_sha256` 必须包含发布后的 `source/launcher.py`、`source/probe.slurm`、`source/submit.py`，并保留 probe typed receipt 原要求。

root receipt 的映射及 evidence 不含自身或最终 GPU registration，避免哈希环。提交 CLI 单独核对二者全 SHA，验证 registration 中的 root 引用，再将二者补进 invocation 的完整 watched 映射。只有 typed status/kind 精确匹配才通过；普通 `passed` 无效。

闭包是：173 文件到 S，manifest 原始证据、所有本地 metadata refs、四个精确 development 面板、compatibility 文件、CPU 收据、root evidence、发布的四份执行源码及 frozen supervisor 到 P。实际安装的两个 robosuite controller 文件由 probe 在服务器核验，不复制、修改或下载；权重同理不进入传输清单。缺项、多余目标、任意 alias、已存在但 SHA 不同的远端文件均拒绝。

## 调用

root 发布这三份文件及已冻结 probe 后，可纯 CPU 检查：

```text
python -B <published-source>/submit.py --project-root F:/CTI-VLA --check-only \
  --root-review <relative-root-review.json> --root-review-sha256 <sha> \
  --manifest <relative-candidate-manifest.json> --manifest-sha256 <sha> \
  --gpu-registration <relative-registration.json> --gpu-registration-sha256 <sha>
```

正式提交将 `--check-only` 换为 `--submit`；只能由 root 执行。它取得原 supervisor 锁、刷新本项目已登记作业，所有未知/过渡/PENDING/SUBMITTED 状态及 CPU 请求均占槽。8 槽满直接返回；任何相同 stage 历史或 pending 都拒绝。元数据先按 SHA 完整检查及仅缺失文件原子发布，然后在 invocation 发布及 sbatch 前持久化 pending。提交结果不明或后续失败保留 pending，不自动重投。

wrapper 先校验自身、invocation、launcher SHA，再启动 launcher。launcher 使用独占锁及不可覆盖的一次性启动标记，执行前后核完整 watched 映射，给 probe 传所有登记 SHA、job id 和固定 output root。child 最多使用扣除校验时间后的 3540 秒，余量留给失败收据；Slurm 硬限制 3600 秒。root 以实际 Slurm 分配计全成本，不能用 child 耗时代替账单。

## CPU 验证范围

`test_dispatch.py` 的正向闭包使用真实 173 源文件及 inventory bytes，但其工程 manifest/typed receipts、开发面板和 probe 是隔离合成数据。真实 probe 已由另一项 CPU 验收，不在这里重复运行。测试会运行真实 check-only CLI、检查无文件改变，并验证缺失/重复/alias/SHA/typed status/边界拒绝、路径在文件系统访问前拒绝、容量和不明提交的 pending。

提交测试仅用隔离 fake supervisor 和 transport/sbatch stand-in；没有真实锁、SSH、SCP、Slurm、GPU、模型或最终初态。shell wrapper 仅做固定指令与内嵌 Python AST 检查，本地 Windows 不执行 Bash。真实服务器路径、远端文件系统发布与 GPU 验收尚需 root 单次登记后验证。
