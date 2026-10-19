# 严格历史前缀消费门（CPU 候选，未启用）

用途：保护 O2A 联合消费和全局冻结元数据检查，防止旧开发 trial 被新报告顶层 `execution_version` 掩盖。不修改已批准 Spatial development 续跑、原 7 文件、原 trial 或原审阅报告。

## API 与部署边界

两个文件可按原字节移到 `scripts/ops/formal_action_consumption_guard_v1/`，同目录放置，不覆盖 `formal_action_deployment_v1`：

- `consumer.require_matching_o2a(evidence, development_refs, full_ref, components_ref, *, suite)`：先调用固定 SHA 的原 v1 完整原始重建消费器，再逐条追溯全部 development 继承链；完整 O2A 身份、样本数、预算和版本检查复用原函数代码对象，只有显式消费依赖增加 ancestry 门。
- `consumer.audit_freeze(evidence, directory, registration)`：先检查四套件全部 development 继承链，再执行原 `audit_freeze` 和真实原 `helper.release_global(release=False)`。没有 release 参数，不能创建全局 release 或 final execution。
- 两 API 返回新的 typed 外层结果，原验证结果放在 `original_verification`；不能把这个外层结果假装为旧报告。调用方需要另行显式、SHA 绑定集成，目前没有生产调用者变更。
- 输入 `evidence` 使用原 v1 reviewer 的 `Evidence`。内部固定原 reviewer/consumer SHA；`consumer` 另外固定同目录新 `reviewer.py` SHA。候选不读取 supervisor state，不提交作业，不写审批或激活文件。

每个祖先的不可变 root、invocation、runtime contract、transition、独立 transition 证明都按 exact path/SHA 读取；检查套件、run root、stage key、manifest、语义 SHA 和原始 prefix 绑定。原消费器负责当前完整 raw 重建及实际 byte prefix；本层不将已增长的输出目录整体当成旧快照重读。递归直到显式 fresh 原点，缺 marker、未知版本、矛盾的 from_version、替换/重播历史、SHA 漂移或任意正向等价/另行处理声明均拒绝。不支持等价例外协议，也不生成等价证明。

## 实测与限制

`pytest_a1`：23/23 通过，32.17 秒。

- 正例字段来自原 v1 writer→reviewer→consumer 的实际 CPU 输出，不是手造成功摘要。该原始科学结果仍为 partial，默认完整消费及 O2A 继续拒绝。该已有 CPU fixture 的基座/GPU/准入 scope 明确为 stand-in；没有运行新的 GPU scope。
- 1／2／3 层 current 祖先、1／2／3 层包含旧叶节点、版本/marker/语义/完成字段/引用/前缀/等价声明等故障均有针对性检查。继承链元数据例明确标为 synthetic。
- 执行真实原 `helper.release_global(release=False)`，检查原完整 88 身份格式、四套件、development 原始记录、checkpoint inventory 元数据及完整哈希。未 mock 该函数。该 fixture 的 72 checkpoint/已验 GPU 身份仍是 synthetic，不读取 checkpoint；其源准入及 root raw 重建属于已有显式 stub。检查通过仅说明新报告形状与原冻结消费结构兼容，不代表生产 72 组完成。
- 原 freeze 正例同时验证没有产生 `root_release.json` 或 `final_execution/`，改动实际冻结证据后原检查照常拒绝。旧祖先在进入全局 helper 前拒绝。
- 原字节复制到预定新生产路径、固定上游 SHA/guard SHA 漂移拒绝已测试。
- 初稿把 `global_freeze.suites` 误设为 list，按原 helper 的真实 dict schema 在测试前修正；原两份草稿保留在 `history_a1/`。本次测试首轮 23 项全过，没有隐藏失败重跑。

`actual_metadata_rejections.json` 是实际不可变元数据的前置拒绝诊断：Long 3019954、Spatial 3022743、Object 3021844 都因旧 execution ancestry 拒绝。它不冒充这些历史 raw 的重新验收，不修改历史结论。Spatial 已登记的新 development 计划保留旧 12 条、追加 588 条的授权不受改变；若该运行完成，旧前缀仍会阻止此候选将其纳入新语义的 O2A／freeze。

实际 R/S 173 冻结文件及现有 7 文件校验通过；未读写 state、未读取封存值或权重、未调用 Slurm/GPU、未发布 P 或 Git。当前没有已完成的全新 runtime 开发数据可供实际 O2A join；`actual_O2A_join_verified=false`，不可将 CPU 正例当生产成功率或 GPU 验收。

## 继续条件

root 与非作者独审先绑定这两份候选源码和测试证据；随后如需采用，另行登记调用方集成和对应原始消费链。现有旧前缀没有已登记的等价/另行处理协议，本候选一律拒绝，不自行挑选、删除、替换或重复初态。需要另行登记且有真实证据支持的处理方案后，才可讨论新的消费版本；此候选不实现或授权该方案。生产 O2A/global freeze/final 均不因本检查而开放。

## 复跑

在服务器运行（全部输出必须在调用者获准的服务器审计目录）：

```text
/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B -m pytest /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/action_mixed_prefix_guard_1111/test_guard.py -q -p no:cacheprovider --basetemp <独立服务器审计目录>/pytest_tmp --junitxml <独立服务器审计目录>/pytest.xml
```

完整作者命令、环境和原日志在 `pytest_a1_command.json`、`pytest_a1.log`、`pytest_a1.xml`。`check_actual_metadata.py` 只读实际 R/S 元数据，但固定把自己的诊断输出写本候选目录；独审只读原诊断或自行在获准目录复做，不覆盖作者证据。

`pytest_a1_tmp/` 是本轮 CPU fixture 原始文件，留服务器，不是生产证据；归档清单不重复收录这批临时合成数据。归档源、测试、命令、XML、日志和诊断即可复现。
