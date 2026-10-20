# 正式Long固定测速观测采集登记

2026-10-20 17:50 CST验收：3047982通过root及独审，**10条开发采集轨迹、30观测全部验收**，固定来源与首中末规则不变。成本472GPU秒；不计入成功率分母或推理延迟。O2A及分项计时未运行。[验收记录](正式Long测速观测验收.md)。

2026-10-20 17:13 CST执行登记：单次作业 **3047982** 已提交并独审通过，原ACK会计延迟已精确对账，无重提交。计划30观测、当前验收0；后续定时监督待真实产物双审，完整O2A/分项测速及最终评测未运行。[提交证据](../results/formal_main_v2/preflight/heartbeat_20261020T1630/Long3047982_pending_reconciliation.json)。

2026-10-20，formal_main_v2。已在任何采集结果前固定输入并完成root及独立CPU链路检查，仅准入一次Dense采集；尚未把计划观测计为已采集。

来源为原Long开发面板的全部10任务，每任务选择source_state_index最小的一条初态，依任务0—9为 **0、4、7、3、6、2、3、6、8、2**。只用对应官方Dense512基座生成轨迹；环境seed0、runtime seed17、等待10步、chunk8、最大520控制步。每个实际动作前记录原始观测，首、中floor((N−1)/2)、末三个时刻，N须至少3；异常或不足跨度即失败，不按成功与否换轨迹、补帧或替换观测。计划10轨迹/30观测，已有100开发初态范围不变。

此次只采集统一测速输入，不重评旧600，不增加成功率分母，也不报告推理延迟。使用已GPU验收的动作语义与同一Dense身份，完整输入和173科学文件不变。未来头/教师缓存不参与部署。真实采集完成后须用原始轨迹、面板、动作收据及全部Slurm成本通过双审。

完整O2A及独立分项计时保留原规则：同checkpoint、同L40与运行环境；原始观测/指令就绪至CPU动作chunk就绪，含预处理、视觉编码、DIE、packing、VLA与后处理，排除模型加载、磁盘读取和模拟器步进。每部署实例预热50次、共同30观测重复20轮、固定随机平衡方法顺序，全部尖峰保留；仍需88身份和四套件开发冻结。此次采集不开放full/components或最终封存初态。

[唯一授权](../results/formal_main_v2/execution/long_collect_action_v1_0830/submission_authorization.json)、[容量及双审收据](../results/formal_main_v2/preflight/heartbeat_20261020T1630/Long_collect_slot_activation.json)、[固定选择规则](../results/formal_main_v2/engineering/supervision_delivery_0830/Long_collect_author_candidate/collection_selection_registration.json)。权重留服务器，非权重结果在服务器控制库回存并同步GitHub。
