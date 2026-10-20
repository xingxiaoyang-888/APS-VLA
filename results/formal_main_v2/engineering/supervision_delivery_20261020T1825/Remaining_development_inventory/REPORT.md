# 非Goal开发覆盖只读盘点

状态口径：72/72训练已双审；当前动作语义5200条＋明确兼容Long600条＝5800条，400唯一初态。下列按盘点时已登记接纳状态，3052166虽然root终审通过仍等待独审，不擅自增加分母。

|套件|已接纳实例/22|已接纳开发条数|尚未准入|
|---|---:|---:|---|
|libero_10|22/22|2200|无；不得重跑|
|libero_spatial|14/22|1400|dense, uniform256, uniform128, uniform64, A128_seed17, B128_seed17, A64_seed23, B64_seed23|
|libero_object|12/22|1200|dense, uniform256, uniform128, uniform64, A256_seed23, B256_seed23, A128_seed17, B128_seed17, A64_seed23, B64_seed23|

未准入非Goal总1800条：Object256s23已有唯一作业200；Spatial旧12需经失败修复和原续跑588，再接纳完整600；Object旧600需逐chunk/环境等价审查，其中1条Dense policy_error必须单列；两套件64s23各200需独立startup来源桥。未准入不等于全都需要新跑。

原factory对Spatial/Object旧6方法均通过并重建完全相同manifest，但原planner禁止重叠子集和完整组重复提交。实际64s23原消费失败分别是Spatial失败3028522的pull ownership、Object失败3028468没有普通runtime metadata，原因不同。现Object256s23桥只认3028460→3039258→3042627的确切链，不能泛化。

完整O2A及组件计时必须有全部88实例、四套件开发收据的global_freeze；它们验证freeze但不要求先签final root_release。dense-only观测collect可提前；Long已双审30观测，其余套件只有固定100开发初态与确定性抽取规则，尚无实际collect产物。Goal科学HOLD继续；无完整延迟结果。

精确路径、SHA、每一实例的checkpoint和源链见instance_inventory.json；原入口与最小下一步见minimum_next_actions.json。所有权重均未读取/复制；无Slurm调用、无GPU、无state/Git/canonical写入，唯执行transport按既有规定新增不可覆盖审计日志。
