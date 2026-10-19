# Spatial attempt03 准备候选（精确 3042529）

本目录只验证服务器原件并生成不可提交的规划数据，不是已通过的独立审计、root 授权或生产规划器。没有 Slurm、GPU、state、P目录、Git 写入。 `prepare.py --write-candidate` 仅新增本目录文件，已存在文件拒绝覆盖；再次实物检查可不加该参数。

固定历史：3022743 COMPLETED0:0 /393 GPU秒；3042529 FAILED1:0 /2 GPU秒。两次分配均保留，总395秒；实际账本只有3022743贡献的12 terminal、25行、2初态。原600清单剩588，环境220/10/8/seed0及六部署实例不变，不复写已有trial。

根在 heartbeat_20261019T2318 已把3022743 prior_review 原字节补至P；旧说明“7canonical尚未发布P”已过时。本工具重新核R/P整个既有运行依赖闭包及173 R/S，并真正调用未经修改 wrapper.verify(P)。不以诊断中的内存路径替代当作真实修复。

## 当前交付

- prepare.py：精确SHA入口、失败事实、完整当前两job投影、原始prefix、冻结源码、既有依赖重核。
- actual_evidence_check.json / actual_facts.json：真实只读CPU结果，包含全部实际输入SHA；全局可变state仅记录所用job投影。
- attempt03_candidate.json：非可执行数据，不是formal_downstream_plan或prepared invocation。
- publication_closure.json：既有R→P逐字节闭包，以及尚未产生的新attempt依赖角色。
- actual_check_a*.log/command.json、failure_*.json及prepare_a1.py.txt保留作者失败；a1误把R缺失的snapshot镜像当控制源码，a2只按精确173 inventory把R原相对源映射S，逐SHA和bytes仍核。
- test_candidate.py、原JUnit/log：仅CPU定向检查。独立审查另由其他代理进行。

## 仍阻断，不能提交

1. 3042529没有child adapter/runtime artifact，不可造旧root_downstream_review passed。
2. 原prior_contract把分配集合与ledger贡献者强制相同；原gateway FrozenPlan又固定调用该planner。因此本工具不会过滤registry、替换prior或伪装旧identity以绕过。
3. 原allocation_cost也要求每个分配有原始invocation行；新终态消费者必须精确支持已证明的before-child分配，保留2秒。不能补造账本。
4. 新的精确版本规划适配与费用消费者需被root及独立审计绑定；新typed before-child失败审核、repair、transition、effective plan、runtime readiness和一次性授权都未生成。

## root 后续最少步骤

先独审本目录真实证据和反例；为唯一3042529发布新的typed失败/repair收据。实现并独审最小版本planning/cost dispatcher，保持旧7文件和173原字节；显式记录allocation_history=[3022743,3042529]、ledger_contributors=[3022743]。绑定新的控制身份，不能宣称旧消费者已经覆盖。

随后重建真正attempt03 plan/transition及所有P运行时递归读取的依赖，特别是prior_review原件，不仅watched_files。发布只能按明确目标和SHA；未生成的future roles没有虚构SHA。本目录230项既有闭包可作为重建起点，不能当未来新plan完整闭包。

只有新root+independent readiness及全新单次授权齐全后，才在共享writer锁/CAS下复查全registry、UNKNOWN/PENDING、controller owner/lease、同stage唯一、全部已有reservation与8GPU上限，再注册自有预约和pending-before-submit。旧55f6授权已消耗，不能重用。当前8健康GPU无需取消或持续等待；本候选不预约槽。

成功后的终态核验必须同时覆盖原12字节前缀、新588上限、完整分配历史和新实际调用身份；自动恢复/科学全局release没有放开。
