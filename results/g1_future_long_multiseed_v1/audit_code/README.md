# 独立审计代码归档

两份脚本与实际审计使用的 `.local/` 原件逐字节一致，SHA见 `manifest.json`。它们不属于运行GPU作业的冻结生产快照，不会加载模型、checkpoint或模拟器。训练脚本由 conditional_method 编写，闭环脚本由 packing_migration 编写；后者不导入生产分析代码。

在项目根目录复查（不覆盖已有审计）：

```powershell
$env:PYTHONPATH = 'F:/CTI-VLA/src'
python results/g1_future_long_multiseed_v1/audit_code/review_long_seed_training.py --root F:/CTI-VLA --check-only
python results/g1_future_long_multiseed_v1/audit_code/review_long_multiseed_closed_loop.py --project-root F:/CTI-VLA
```

脚本在实际运行目录 `.local` 中执行首轮审计，报告引用的脚本SHA与本目录归档对应。闭环首次审计需要全量产物和 `analysis/summary.json`；缺失或不一致返回非零，不预写通过结果。训练审计依赖项目CPU环境；闭环审计只使用标准库和NumPy。

审计覆盖身份、完整性、配对、冻结及成本记录。离线L1只能从原始逐窗口误差重新聚合：本地没有教师/示范完整动作数组，不声称独立重算这些误差本身。
