# Goal 剩余五配对：原下游计划 CPU 作者交付

本包只生成可复核的计划、来源和固定试验清单；未发布 R/P 生产内容、未写监督 state 或 Git、未查询/提交 Slurm、未运行新试验。全部源码和结果仅在服务器私有目录。实际 P 验证、真实新运行时和原子网关准入均仍 HOLD。

## 已生成范围
严格为 Goal256 seed23/41、Goal64 seed17/23/41，各原100开发初态×A/B=200，共1000条待执行。environment_seed=0、runtime_seed=17、wait10、chunk8、max300；训练seed只控制对应选模身份，未冒充runtime seed。保留已冻结10个选中checkpoint与完整原train/11节点、5000更新科学设置。没有模型加载或新推理，没有复制权重，没有读取封存最终值。

原 formal_execution_manifests.py 的 source_contract、registration_contract、suite_rows、make_execution 逐pair实际通过；suite_rows完整运行F00/F01/F03、训练终验、原选模和本pair全部来源历史。原 formal_downstream_supervisor.plan 完整重建scientific_plan，原action contract生成effective_plan。五pair均使用自己的原provenance直接通过，无需新来源桥，更没有套用别pair结论。原173源码和原builders保持原字节。

每pair在结果路径 results/formal_main_v2/execution/goal_remaining5_v1/<pair_key> 下生成 execution_manifest.json、scientific_plan.json、source_provenance.json、execution_contract.json、effective_plan.json、invocation_template.json、specification.json，实际原件位于 v2/publication/<上述相对路径>。candidate_index.json给全部路径/SHA、40项精确发布映射、10checkpoint前轮真实SHA验证来源和当前stat核对。此前已精确复算的10个checkpoint本轮未重复大文件hash，实际新runtime仍须复核服务器字节。

原planner要求内层科学输出为 libero_goal/downstream/development/<methods-tag>/attempt01。本包未改其守卫或把X输出冒充原输出。新五pair运行时拟输出 X/attempt01/original_run，必须作为显式derived行为单独审查。原action support闭包中的旧gateway只作不可变源依赖，不授权调用旧gateway；新提交仍由root新精确gateway负责。

## 原guard失败与有界登记修复
初次原planner正确拒绝：真实3054717登记 mode=development/suite=Goal但缺method_ids，空集合被保守视为潜在重叠。原54ee...输入、返回1的transport记录、部分manifest及源码均保留。root依据已终验3054717原证据只补 method_ids=[A256_seed17,B256_seed17]；原stage/output/成本和历史不变。作者没有删行、改state或修改重叠守卫。v2基于真实d795...完整state重建通过，每pair仍测试缺method_ids的拒绝行为。

## 可重跑入口
固定源码：v2/build_plans.py；验证调用为 --verify <v2/candidate_index.json绝对路径> --index-sha256 <index SHA>。默认仅用精确一个未发布manifest的只读路径投影，原helper函数/全局科学实现均未替换；source/provenance全部直接读取R真实证据。root精确发布后可增加 --canonical 使用原helper、不带投影，重建字节必须一致。该CLI重放保存的完整state；未来prepare步骤另读当时真实state重新过原guard。

最终CPU入口 v2/test_plans_v3.py，参数 --index <绝对路径> --index-sha256 <SHA> --output <作者私有新输出路径>。独审可按精确源码加载后调用run(index_path,index_sha)得到返回值并在自己的私有目录保存；run只读，不写作者目录。最终36正例、340拒绝，五pair原planner全量重建；每pair均覆盖错源/基座/receipt/config/checkpoint/F01/方法/种子/环境、sealed/非法路径、重排或缺失清单、active/UNKNOWN/已完成重复、空method历史、pending及伪根收据。200行校验仅是原_identity/validate_trial_identities的元数据测试，不冒称GPU闭环。

先前CPU_report_v2的source_files键把prepare_after_reviews_v2.py误标为无v2的文件名；SHA对应实际v2源码。最终test_plans_v3更正标签并增加30个禁止审查证据路径反例，重新执行全流程。旧测试/记录仍保留。

## 真实根/独审收据后再准备 invocation
本包没有伪造passed readiness、root review、independent review或registered invocation。invocation_template只是effective['invocation']；标准planned_invocation_path尚无文件，不能直接运行。

1. root按candidate_index publication_map精确复制到R/P（新35 metadata和5个P配置，已有不同字节则拒绝），并重新无投影运行原planner。
2. root和不同agent分别完成新五pair原科学/来源/旧consumer前置闭包审查，形成X/plan_root_review.json、X/plan_independent_review.json。精确schema由 v2/prepare_after_reviews_v2.py 的 expected_review(item,index,role) 给出；必须另含完整action runtime_sources、blockers=[]和实际归档review_evidence路径/SHA。其production_chain_complete明示只指原metadata/source/consumer前置闭包，不指新GPU或新typed runtime准入。新运行时/网关/容量独审及实际P收据另行提供。
3. root用 v2/prepare_after_reviews_v2.py --index <index> --index-sha256 <SHA> --pair-key <精确key> --root-review-sha256 <实际SHA> --independent-review-sha256 <实际SHA> --prepared-utc <带时区UTC>。该入口先读canonical R文件、实际当前state和双pending，原planner无投影再重建，校验真实根/独审证据，再仅写本私有v2/prepared/<key>下readiness和prepared_invocation及精确发布映射，不触碰canonical/P/state。
4. root精确发布生成readiness及标准唯一invocation。新runtime config固定scientific/effective/manifest等原SHA；其actual-P --verify和实际authorization必须绑定此prepared invocation的实际SHA，不能仅相信路径。若标准invocation已存在，prepare拒绝重写；未知ACK不能清pending再发。
5. 此后才由root/独审完成新typed runtime/consumer/source闭包、actual-P、并行worst-case R/P容量、全模式8卡及同pair排他、双pending/lease和held→持久原ACK→同锁CAS登记→唯一release。新登记必须包括本pair完整method_ids，不能再次丢字段。任何异常停该尝试并保留成本；不自动重跑。

本包未承担新五pair运行时/observer/consumer实现和网关实现，这两项分别由其他作者/root负责。每pair全200真实raw终验、五组件及被动sim/RNG内容地址归档、独立终审均属于未来GPU结束后的验收。当前通过不开放O2A、最终0/35200或任何新方法。
