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

2026-10-18 08:38：第二段已登记并提交`3021603`，同原账本显式resume，新增120、累计目标132/600，首12条不重跑。方法、任务、初态、环境与权重身份不变；下一分段须待实际终态双审。

[v2登记](../results/formal_main_v2/preflight/object_first_pair_development_registration_v2.json)；[root重建及提交](../results/formal_main_v2/preflight/object_first_pair_development_submission_root_v2.json)。

2026-10-18 10:24：第二段`3021603`已通过root与独立复核，新增120、累计132/600条，覆盖22个唯一开发初态。16条达到280步时限而未成功，0运行错误、0重放；2502次策略/视觉/packing调用及19601控制动作，未来头调用0。总分配1787 GPU秒含两段加载及失败任务。该固定前缀不作全套件成功率或未来监督收益结论。

[实际GPU复核](../results/formal_main_v2/downstream_reviews/3021603.json)；[独立审计](../results/formal_main_v2/preflight/object_second_development_real_independent_20261018.json)；[20份完整非权重回存](../results/formal_main_v2/preflight/object_second_development_raw_v2/receipt.json)。

原600条清单的剩余468条已登记并提交`3021844`，同账本显式恢复、原132条不重跑。已观测132条最大单trial尝试耗时19.433788秒，1.5倍余量乘468再加整段首次分配386秒，估计14028.519秒；这是工程估计，不是后续任务耗时上界。保留4小时时限，若未完成则保存前缀并审核后续跑。方法、初态、环境及checkpoint身份不变，不开放最终集。

[v3登记](../results/formal_main_v2/preflight/object_first_pair_development_registration_v3.json)；[root重建及提交](../results/formal_main_v2/preflight/object_first_pair_development_submission_root_v3.json)。

2026-10-18 12:11：作业`3021844`实际产物经root与独立审计通过，新增468、累计600/600条，100个唯一开发初态；79条时限内未成功、1运行错误。累计6713 GPU秒已含全局账单。该六方法面板不代表本套件所有22部署实例完成，更不开放最终评测。

[原始回存与复核](../results/formal_main_v2/preflight/object_third_development_root_integration_0318.json)。

该600条包含1条Dense在task8/source49的policy_error（第8次调用、控制步56），保留在失败分母；其余599条正常结束，另有79条horizon失败。逐方法成功数/100：Dense98、均匀256为93、均匀128为86、均匀64为49、A128 seed17为98、B128 seed17为96。这里只覆盖6/22实例，不作未来监督有效或等效结论。root收据的scientific_complete仅表示登记终态覆盖完整；当前运行接口问题尚未解决，不作为全局release资格。

[动作范围诊断](../results/formal_main_v2/preflight/object_action_range_diagnosis_0318.json)；[有界诊断登记](正式动作范围诊断登记.md)。
