# 新动作执行身份：独立设计静读

仅完成设计审查，未运行施工候选、测试或GPU。科学评测暂停保持。

最小链：新版本计划/调用登记 → 新wrapper → 显式动作/单次加载/兼容scope → 原字节科学adapter → 新raw审核 → 按版本分发的root消费者。冻结173及训练来源证明不变。

不能将新invocation改写成旧v1获得旧审核通过。旧adapter可真实作为内层执行；新外层必须同时绑定同job、invocation、manifest及原始receipt/journal。新动作规则另存execution contract SHA，同checkpoint不能单独证明完整O2A或最终评测语义一致。

旧root收据精确重建还包含审核源码SHA；旧版本须走原字节完整消费链。跨版本resume另需锁定旧prefix、失败、费用与新合同的转换证明，不改历史1212条或自动重跑policy_error。

可以先发布candidate。runtime、gateway、wrapper与消费者整链CPU证据、root登记和实际预约未齐时，提交应拒绝。最终开放仍遵守72+16及四套件开发门槛；不重复16格GPU工程验收。

完整检查位置和建议反例见design_review.json。
