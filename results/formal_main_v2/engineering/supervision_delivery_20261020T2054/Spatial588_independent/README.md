# Spatial 588 精确恢复候选独审

仅服务器 CPU 与源码审查，未提交 GPU、未修改 state 或生产证据。

- 真实基线 378 项通过：173源R/S不变；3022743原12条；3042529真实前置失败、无child/adapter/ledger invocation；395 GPU秒中包含失败2秒。
- 最终候选 control SHA e3994a213c54b8824febe95bed2e0ca8f76b2782ddd21b5f7c5a1496f4ac3df8：27项正检查、46项拒绝用例通过。独立AST证明只修改原planner的2谓词和成本3处，原科学轨迹、contract与wrapper不变。
- 成本单测的当前100秒作业纯CPU模拟：395+100=495不计实际GPU账。没有向真实ledger写入模拟invocation。
- 原12是legacy动作历史；新588是当前动作执行。最终候选明确分开记录；完整current-action consumer拒绝未证明兼容的legacy12，不能凭raw600完成解锁freeze/O2A。
- 缺少canonical集成、真实root repair/独审绑定、新transition/effective/readiness、实际P完整wrapper --verify和精确posttraining gateway，因此本包不构成生产续跑许可。真实600终态尚未发生。

v1 bounded CPU结果保留；其complete consumer混合历史边界经root指出后，由最终候选fail-closed修正。所有历史检查保留。

另含对root已有64seed23终审helper的static-only审查，不是两作业GPU终审。
