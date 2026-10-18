# gpu4020 排除适配候选（未部署）

仅给未来明确的本项目 `sbatch` 命令添加 `--exclude=gpu4020`。已有作业不取消、不迁移；三个启动失败不代表该节点上所有作业都失败。此处不提供失败作业恢复授权，也不修改训练、动作、评测、GPU可见性或冻结源。

`adapter.py` 不执行任何子进程。它在短作用域内替换一个指定的 `formal_supervisor` 模块的 `SSH` 属性，实际现有提交仍由原 `subprocess.run` 执行。限定支持正式训练的原始、Object、Goal三个固定wrapper，以及动作工程验收v2 wrapper。其他提交语法拒绝；不宣称已接入E04控制器。普通既有查询返回原argv。

适配核对root登记及SHA、固定supervisor与wrapper、明确的suite/budget/seed/500步目标与resume标志、已准备invocation原字节和pending身份、原export顺序与值、`cd`目录及完整单命令。只有完整匹配后插入节点排除。既有exclude（包括同值）、其他shell命令、其他项目、额外export和wrapper均拒绝。一次作用域最多一个sbatch；记录写入并fsync成功后才返回实际argv。查询、scp、Slurm回复和原pending处置不修改，不吞错误，不自动重试。

`registration_draft.json` 是未批准草案，适配器会拒绝其当前状态。root审核后需另存正式登记，绑定适配SHA、不可变失败证据、登记中的固定wrapper清单；将状态改为 `reviewed_for_future_explicit_requests` 并自行核对科学门槛与8槽容量。不要把此CPU收据替代train64负责的失败恢复证据门槛。

## 接入已审训练入口

root在同一进程加载当前已审helper引用的同一个 `formal_supervisor` 模块，并保留原锁/刷新/容量/恢复检查。以下只是接入示意，不在本任务运行：

```python
request = dict(kind="training", suite="libero_spatial", budget=64,
               seed=17, segment_end=2000, resume=True)
with adapter.exclude_future_sbatch(
    f, request=request,
    registration_ref={"path": "<root另存的正式登记.json>", "sha256": "<实际SHA>"},
    audit_relative="results/formal_main_v2/preflight/<唯一命令变更收据>.json",
):
    # 原已审入口：由它持管理锁、核8槽、原失败修复/恢复门槛。
    original_submit(args, state, jobs)
```

如果整体通过 `runpy.run_path` 调用既有fill helper，须先按其原模块名 `formal_supervisor` 导入并包装该同一对象，再运行helper；不能另载一个不同的f然后假称覆盖。新训练请求应明确一对，禁止批量自动调度。

## 接入v2 execute_submit

root按现有三SHA参数验证v2 contract，显式加载传给 `execute_submit` 的同一个f：

```python
with adapter.exclude_future_sbatch(
    f, request={"kind": "action_execution_gpu_v2"},
    registration_ref=actual_root_registration_ref,
    audit_relative=unique_transport_evidence_path,
):
    result = original_v2_submit.execute_submit(project, checked, refs, f)
```

不直接包装v2 `main()` 外的另一个f：main会加载自己的模块实例。原v2单attempt/marker、完整部署SHA、8槽和未知pending门槛仍全部执行；此适配不会允许已失败v2重新使用原stage，也不会为它创建新namespace。新的工程恢复版本必须由root另行登记和审核。

## 证据与测试边界

返回给原subprocess的确切原argv/修改argv记入唯一JSON，状态仅 `argv_prepared_not_submission_result`；不是已提交或已运行证明。root须将该收据、实际提交命令结果和job登记共同归档。可变state本身不进入不可变evidence map，只保留变换时pending投影和原invocationSHA。

`synthetic_command_examples.json` 来自实际CPU测试执行的四种变换，但其中invocation/pending/失败证据均为合成，未向SSH发送。原32例首次共有27例被 `.local/test/` 夹具路径提前拒绝、5例路径守卫通过；仅把合成输出改至 `.local/fixture/`，未改适配主体，最终32例通过。原源码、JUnit、日志完整保留。测试不替代真实Linux/Slurm验收。

无全局SSH/环境变更，无GPU调用、SSH、Slurm提交、真实state或Git写入。173冻结源与原dispatcher/wrapper均保持不变。此目录全部是待root集成的候选。
