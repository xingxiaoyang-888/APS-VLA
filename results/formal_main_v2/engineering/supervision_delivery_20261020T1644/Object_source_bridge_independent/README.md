# Object256 seed23 来源兼容桥独立审计

结论：候选桥通过 CPU 来源审计，可进入明确版本化的 root 控制层集成；尚不可直接提交开发 GPU。

- 主审：7405 项逐证据检查、49 个拒绝负例。原始失败 raw verifier 重建；仅 `_root_pull` 和 `_pair_source` AST 有四处登记差异。原 suite/F00/F01/F03、科学身份、全部11次验证、checkpoint、动作及未来定义仍由原函数校验。
- 三个原分配为3028460、3039258、3042627，总58917 GPU秒，失败84秒完整保留。科学manifest与已登记5f2bdcac…字节一致；100个开发初态（10任务×10）×A/B=200，封存状态未读。
- 所有权补审：11150 项逐证据检查、13 个拒绝负例。原consumer在真实终验pull上仍严格绑定失败job receipt及两份Slurm日志为3028460。合成内存负例只测试原语义校验，不能作为真实日志或授权。
- 真实P原wrapper.verify及runtime metadata通过；新action wrapper正确拒绝缺少root readiness。没有加载模型/环境、读取权重、运行GPU或提交Slurm。
- 当前生产gateway仍用原planner，会拒绝这个特殊历史。factory/planner/gateway与终态source consumer须显式绑定同一版本桥，保留原全部检查。桥位置进入proof，移动到生产路径后必须重建canonical计划与proof，不能直接复用此私有预览。
- 根集成后仍需独审控制层、原运行入口checkpoint字节核对、真实root/independent readiness及当时writer-lock/CAS/容量/重复提交核验。源兼容改动不要求另加方法实验；既定200开发运行本身的原始适配器/试验消费者和独审通过前不得计数。

原第一轮测试在action contract引用中多给bytes字段，被原严格引用校验拒绝。failure.json、v1源及diff保留；v2仅修测试引用、改私有输出目录并补面板数量断言，未改候选或生产代码。全部预期拒绝、日志和闭合transport保留。训练完成证据继承原root及独审，不冒称重新审计全部5000步。
