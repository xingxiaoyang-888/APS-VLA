# 正式动作部署运行时候选

仅服务器候选；未提交 Slurm、未运行 GPU、未修改生产文件、173 冻结文件、state 或 Git。完整部署/新原始审核链与 root activation 由 root 另行集成。本模块不会签发科学完成或 root 放行。

## 文件与接口

实现是 `runtime.py`，可按原字节发布为 `scripts/ops/formal_action_deployment_v1/runtime_scope.py`。`contract_example.json` 为 Long/development 样例，`contract_schema.json` 固定字段；其他套件/阶段通过 `make_contract` 生成。合同仅允许 development、collect、full、components，不允许 final。

- `make_contract(*, project_root, source_root, suite, stage)` / `validate_contract(contract, *, project_root, source_root)`：绑定当前实现 SHA、冻结173、套件基座、原动作配置及适配器、v4 probe、原资产适配器，以及固定 root/ind GPU 收据。validate 返回实际只读 SHA 清单。
- `run_with_asset_contexts(runner, *, project_root, source_root, contract, asset_contract, emit)`：runner 为调用原 `legacy.run` 的零参闭包。内部按 metadata（Object/Goal）→ Goal组件（Goal）→ runtime → 原 runner 组合；不运行旧 stage wrapper。Long/Spatial 的 asset_contract 必须为 None。
- `runtime_scope(*, project_root, source_root, contract, emit)`：供 root 已正确安装资产外层时使用；不可同时重复安装两套上下文。`emit(event, **fields)` 必须由调用方持久保存，字段使用 runtime_version、validator_kind，避免覆盖外层 version/kind。
- `expected_asset_identities(*, project_root, source_root, contract, asset_contract)`：调用原 metadata/Goal 元数据验证器生成可信身份，不读取模型张量。生产身份必须基于 P/S 原路径，不能把 raw 自报身份当 expected，也不能归一化旧身份路径。
- `verify_runtime_events(events, contract, *, expected_asset_identities=None)`：无 IO 的结构校验。Object/Goal 必须提供上述可信身份；缺失/重复/乱序、动作源或构造器漂移、双别名恢复失败、单次加载/poison、资产身份与恢复异常均抛错。返回 `complete_runtime_structure_only`，明确不推断科学完成、GPU 验收或 root activation，并保留 synthetic_input 标志；真实消费者须拒绝 synthetic 输入。
- `derive_validator(module, kind='analyzer_chunk')` 返回原函数、派生函数与精确 AST 证明；`validator_scope(...,kind='analyzer_chunk',emit=...)` 只绑定旧 analyze_formal.validate_chunk 的一个幅值分支。其余 reviewer.trajectory / read_final_run 的新版本消费由 root 负责，本模块不替代完整审核器，也不放行最终评测。

CLI 仅 inspect（只读 stdout），没有 run/submit/final：

    python -B runtime.py inspect --project-root /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo --source-root /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e --suite libero_10 --stage development

## 有界行为

动作 scope 直接加载 b8a1632e… 的原 v3 字节，candidate_only/deployment_authorized 原字段不伪改；新的外部 activation 另行登记。所有方法作用相同，不剪裁、不缩放、不改动作数组。

full/components 的 `_validate_chunk` 仅删除幅值 disjunct，同时绑定 profiling 与 formal_profiling 的两个既有别名，保留 NumPy输入语义、8×7、finite、None返回。正式 CPU NumPy endpoint、元数据/单前向/无未来头检查仍在原 `_validate_timed_chunk`；验证发生在原测量端点之后，不增加逐 policy 调用监控。

单次基座生命周期从已验收 v4 类精确派生四个计数常量4→1；可信 globals、constants、helper、cumsum、模块身份/spec/path及失败停止检查未改。原四次加载错误字符串保留，但 proof/合同明确期望1次。外层包装只在模型加载阶段执行；调用原 loader 期间恢复原绑定，使原 Goal intact 检查仍看到相同函数/字节；结束前恢复包装、退出恢复原始绑定。每候选进程只准一次 runtime attempt，失败不得在同进程继续。

## 已完成验证与限制

`pytest_a4.log/.xml`：90项通过（25.20秒）。使用实际冻结 S 的 validator、Prismatic installer 和原 Goal 兼容上下文；模型加载成功例是明确 synthetic，未加载权重。实际原 loader 的 CPU设备拒绝路径已触达，验证动作/双timing别名/loader全部恢复、后续同进程拒绝。

包含：四套件/四阶段合同；封存/final参数前置拒绝；有限超界动作原字节保留；NaN/Inf/形状、CPU endpoint与未来头检查；漂移、异常及恢复；单次/重复/错误基座/错误flag/失败加载；原Goal两组件映射期间原loader身份；完整事件结构及资产自洽伪造反例。

a1 为53过1测试导入名错误；a2为85过1测试异常类型错误；两份原始失败完整保留；a3为86过，补入资产可信身份反例后a4为90过。不得将CPU成功标为新增GPU验收。

`original_asset_metadata_readiness.json` 保留实际 P/S 原 Object/Goal 元数据验证结果。P侧尚缺本轮v4 root/ind两个新收据；外层发布时须按已登记 SHA 原字节复制，不能降低 validate 的缺件拒绝。

其他 P侧依赖：source_inventory位于P根，其173文件位于S；dependencies所列原字节；engineering_acceptance两收据；Object/Goal原 asset_contract.files 完整集合（严格manifest/metadata/Goal映射等）。原模型目录仅原loader使用，权重始终服务器。所有完整科学plan、checkpoint/面板、作业锁/CAS/容量、原raw报告重建、最终release门槛仍由外层承担。

待完成：独立CPU审核、root外层/消费者闭包与单独activation登记、实际首个新科学入口的接口核验。16格工程验收不计正式成功率或延迟。
