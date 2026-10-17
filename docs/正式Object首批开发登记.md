# Object首批正式开发登记

2026-10-18，北京时间。Object128 seed17的A/B已完成5000步及终态双重审计，实际选中服务器权重已核验。以下为运行前登记，不是闭环结果；最终初态保持封存。

- 六方法：Object对应官方Dense、固定均匀256／128／64、A128 seed17、B128 seed17。A使用2500步、B使用4500步选中权重，不采用段末权重替代选模。
- 沿用预先冻结的100个Object开发初态（全部10任务×10），共600条。环境seed0、runtime seed17、等待10步、chunk8、最多280控制步。
- 首段固定12条，即原状态优先／方法次序的前2个初态×6方法，用于实际接口和耗时验收。之后须审查真实Object兼容日志、原始ledger及成本，再沿同一600条清单显式续跑；已完成试次不重做。
- 使用已通过CPU验收的Object metadata兼容入口。原173文件、科学设置、DIE部署和选中checkpoint不变；不复用其他套件或pilot参考结果。
- 每作业1张L40、7 CPU、64GiB、4小时，本项目所有活动请求合计最多8个。后续分段大小仅按实测耗时确定，不依据成败调整任务或方法。

本批只覆盖Object的6/22个部署实例，不代表全套件开发完成或全局最终开放，也不是完整O2A测速。闭环、完整测速和未来监督结论须由真实结果支持。

提交前发现项目规范路径缺少`libero_object_k128_seed17.json`，已从冻结快照按原SHA原子补齐，未改配置。第一次预检保留；第二次预检确认203个现存输入（含两个best）匹配，其余两份精确计划文件由正式提交器发布。全部工程准备无GPU作业重跑。

证据：[执行清单](../results/formal_main_v2/execution/libero_object_development_first_pair_v1.json)、[候选登记](../results/formal_main_v2/preflight/object_first_pair_development_registration_v1.json)、[首12条计划](../results/formal_main_v2/preflight/object_first_pair_development_plan_v1.json)、[root独立重建](../results/formal_main_v2/preflight/object_first_pair_development_root_review_v1.json)、[配置补齐](../results/formal_main_v2/preflight/object_first_pair_development_config_sync_v1.json)、[服务器复核](../results/formal_main_v2/preflight/object_first_pair_development_server_inputs_v2.json)。逻辑计划SHA：`524f52b19055b6e636322289e2d54bcb628adc12a197fb687501129b5b737501`。

已提交作业3021394，首段12条。当前尚无已验收Object开发试次；实际GPU产物须另行回存和复核。

后续实际验收：3021394以0:0结束，12条/2初态通过root及独立审计；269次策略、视觉和packing，2103控制动作，0未来头。3条horizon失败和0运行错误全部保留，实际分配386 GPU秒。原始12份证据另存不可变副本，后续沿同一600条清单续跑，不重复前12条；此小面板不支持套件成功率或未来监督收益结论。

证据：[root](../results/formal_main_v2/downstream_reviews/3021394.json)、[独立审计](../results/formal_main_v2/preflight/object_first_development_real_independent_20261018.json)、[原始字节归档](../results/formal_main_v2/preflight/object_first_development_raw_v1/receipt.json)。
