# 20261020T2253 最终交付独审

前置归档核查 733 项，最终快照核查 3835 项均通过。36 pair / 72 arms / 360000 更新及原 root+独立训练终验链逐项复核；173 冻结文件在 R、P 冻结快照及 R 镜像保持原字节。开发仍为5800当前动作+600明确兼容Long=6400/8800，历史7012，最终0/35200封存。

从冻结 raw sacct 与 squeue 独立重建271唯一正式分配，累计1986011 GPU秒。Goal3054127完整分配840秒，其前轮已计217秒，本轮净增623；Spatial3054201唯一原ACK，冻结观察709秒。本轮合计净增1332秒。均非未来成本估计。

Goal工程与完整blob归档的已通过独审绑定原SHA，本轮不重复10741 blob全扫。Goal原200和新增科学HOLD。Spatial12 legacy与588 current分别绑定，保留393+2历史GPU秒；精确ACK补登记没有新submit，尚不接受完整600批。Object599兼容证明和18文件单失败CPU候选分别归档；候选仅作者测试，未独立生产准入，原policy_error和6713秒不删。

单次ACK补登记31文件及34项终核证据已绑定。此次最终审查不读取运行中的P ledger/report，也不查询Slurm，不改state、Git、P或作业。

Git入口只审最后v4，SHA3fac309a6515f8ab7f7c124a4bec944c8f61b3881c337f3b20a30d85011bc63b。v4从固定Goal归档manifest及每个包manifest提取exact allowlist，显式force-add被.gitignore隐藏的15卷与12份metadata/log和包内原件；没有宽泛加入被忽略目录。实际运行仍须执行同state、writer lock、索引范围与173字节检查。本独审不执行commit/push。

未执行的auditor v1/v2保留，v3仅增加最终ACK包、v4 Git门槛及精确旧文档前置换行识别；文档历史尾部SHA仍必须完全一致。本次实际前置与最终检查均一次通过，运输日志原字节保留。
