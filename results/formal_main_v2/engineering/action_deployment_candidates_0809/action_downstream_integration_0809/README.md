# 新动作执行版本整合候选

本目录仅服务器CPU候选，未解除科学闭环暂停、未提交GPU、未开放final。

- contract.py：保留原v1纯科学plan，生成显式formal-downstream-action-v1外层；只替换运行身份及追加精确依赖。argv、方法、checkpoint、输出、恢复前缀、训练来源和资源均不变。
- wrapper.py/entry.py：新外层独立保存实际执行身份；旧wrapper只用于校验声明的原科学plan，旧科学adapter原函数执行。新动作/单基座/timing scope及恢复事件另存。
- 新原始审核与consumer、runtime scope和gateway来自协作候选，必须整体源码绑定和独立验收后才能签发runtime-readiness。当前没有该准入收据。
- tests只验证明确CPU边界，不能视为完整科学plan验收或实际GPU组合已通过。9项wrapper测试都是拒绝路径，上游科学验证不执行。
- 历史v4的16格仅作动作兼容GPU工程验收，不能代替新入口的实际组合收据或任何成功率/延迟结果。
- API施工修正：事件version/kind使用runtime_version/validator_kind；可信asset identity必须独立重建；全部运行依赖纳入outer support/watch/publish；导入候选模块前验证SHA。
