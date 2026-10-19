# 七对训练 canonical root 路径检查

结论：0/7 可直接按原字节 alias；7/7 原 root 重建请求已准备，未执行。187 项只读检查通过，94 文件引用，28 次实际原消费者 same 合同拒绝均符合预期。

request_index.json 给出每对末次 job、canonical 目标、原 machine/root/独审来源和 SHA，以及原 scripts/review_formal_segment.review 的精确参数。现有 root_completed_pairs_terminal_integration 与各 pair 独审是真实的5000终态验收，但不是原消费者所需的单个 root_segment_review/status=passed 文件。机器外层明确 root_signature_claimed=false；其 original_review.status=local_passed_remote_required；此前 root 单段收据对应较早 job/1000或1500或2000。均不得改 status 或抽取机器内容冒充 root。

最小修复不需要新 consumer：由 root 在共享 writer 锁下重新核当前 pending、末次 pair job 和源身份，经已审 transport 用原 reviewer 调用 verify_server_resume=True，重建完整 raw 并校验两份服务器 resume SHA。只有原函数真实成功后才发布 canonical。随后原 suite_rows/source_provenance 再做正式消费验证。本任务没有执行该有写入动作的分支。

已核七份原始 live pull receipt 确实存在、SHA 与 immutable machine raw_input_evidence 一致，requested/selected 覆盖对应全部 pair 历史；before/after Slurm 计费与当前登记相同，末次 job COMPLETED/0:0/target5000；对应 inventory_before/after SHA 相同，原 required files 均有同 SHA 映射。当前 summary、A/B report 和 deployment receipt 原字节重核。该检查不等同重新验证全部大日志或当前 checkpoint 字节，完整重建及新 SHA 检查仍由原 root 调用完成。

代码 audit_requests.py SHA9aefc892480167aaad73f8754f3c263d4fc765ec93604028583f79f8f49d90b9；入口经原 transport 精确 SHA 运行，命令/日志完整保留。本目录未写 state、P、canonical、Git；无 Slurm/GPU、模型、checkpoint 或封存值读取。旧 gap 审计目录未改。
