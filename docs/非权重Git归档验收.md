# 非权重Git归档验收

2026-10-18：Long首批600条开发账本为110,234,480字节，超过GitHub单文件上限。完整原件仍留在本地；Git改存7个无损gzip块、完整映射及来源收据。两个相同原件共用一个内容对象，压缩块合计26,095,303字节。历史提交和历史原始记录全部保留。

仅下面两个路径新增精确ignore，未增加通配忽略规则：

- `results/formal_main_v2/libero_10/downstream/development/8c843c1d4ee8383c/attempt01/trials.jsonl`
- `results/formal_main_v2/preflight/long_sixth_development_raw_v1/17_trials.jsonl`

这两个原件的SHA256均为`0f8b8d265fce7d77728e5c8923420ad40eb780a26289fd8094837ea2a851c136`。从新克隆恢复时，在项目根目录运行：

```powershell
python -B scripts/ops/nonweight_archive.py restore --project-root . --snapshot results/formal_main_v2/nonweight_archives/v1/snapshots/long_dev600_20261018.json --snapshot-sha256 ac7e4dce68abeddb147dd412f83afffbc5041715868547d6f60811e5fca137f0
```

恢复先验证全部块、映射、来源和目标；已存在且字节相同则跳过，不同则拒绝覆盖。无需服务器、checkpoint或旧大文件。权重不在归档内，最终初态未读。

归档codec最终69项中66通过、3项因Windows真实symlink权限缺失而显式跳过；另26项独立检查全部通过，包含4个真实junction案例。暂存区核验工具最终38项和独立19项全部通过；历史失败与有界修正均保留。

root已在实际Git暂存区执行完整提取、验证和恢复：两份110,234,480字节原件逐字节一致，173个冻结源文件在工作区和暂存区的SHA均符合原清单。只有明确登记的原始账本索引项被移除，文件系统原件未删。

后续不要强制重新加入上述原件。新增大日志须单独登记精确路径、SHA和字节数，先存齐块与来源，再用`scripts/ops/check_nonweight_archive_stage.py`检查真实暂存区；原有通用stage检查器不适用于已登记的原件索引迁移。缺块、SHA变化、未登记删除、权重及封存状态输入必须拒绝。

[本次映射](../results/formal_main_v2/nonweight_archives/v1/snapshots/long_dev600_20261018.json)、[迁移登记](../results/formal_main_v2/preflight/long_dev600_archive_v1/migration_registration.json)、[精确ignore登记](../results/formal_main_v2/preflight/long_dev600_archive_v1/exact_ignore_registration.json)、[独立工程审核](../results/formal_main_v2/preflight/nonweight_archive_stage_independent_20261018.json)。旧codec审核中的`.gitattributes`和`.gitignore`历史SHA分别对应各修正目录中保存的原件，不修改历史审核收据。

2250批次保留了一次暂存准备失败：旧回存收据中的3份Spatial进度文件已经合法推进，不能用旧SHA核验当前文件。已从对应历史Git提交恢复旧字节副本；当前8份回存的全部664条文件记录仍逐项核验。历史收据与修正前后脚本均保留，无GPU重跑。

Object新增12份实际开发产物全部进入本批精确交付。另一个依赖是此前已提交且未改的Object开发初态面板：仅固定`configs/manifests/formal_main_v2/libero_object/initial_states/development.json`及SHA `6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a`，单独检查HEAD、index和工作区原字节一致，并要求无任何暂存或未暂存变化。通用守卫的状态路径禁令保持原样；此既有文件不重新暂存，所有新改文件仍完整受守卫检查。检查前后还要求全Git索引不变；任一身份不符即停止交付，不自动修复或放宽路径。

[旧进度原字节与有界修正](../results/formal_main_v2/preflight/parallel_review_batch_20261017T2250_staging_repair/root_review.json)、[既有开发面板身份](../results/formal_main_v2/preflight/object_existing_development_panel_index_20261018.json)、[本批实际交付核验](../results/formal_main_v2/preflight/parallel_review_batch_20261017T2250_git_delivery.json)。
