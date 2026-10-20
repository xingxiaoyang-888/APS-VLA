from pathlib import Path
import hashlib,json,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_terminal_independent_20261020T2253'
assert D.resolve().parent == (R/'.local').resolve()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,obj):
    p=D/name
    assert p.parent == D and not p.exists(), str(p)
    p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
required={
 'terminal_review.json':'e48e5f5a0855c81280ea9cd4eb014aefe45c3b18d324836930b5a5ef1e1d4d61',
 'archive_review.json':'3b7166d6422cbf4551fcd54a0f7d15a08e30d6b0f2de8d2d644f5578f6dd8fd5',
 'bounded_diagnostic.json':'c1b9de88b2781ade315b3db5bb3000473ca74d36f994adfc00ac11e297dfa354',
 'readiness.json':'e969d8fc21ea0e88429d14e5289ff600c2141506e20d3669a8c670a4c92d8db2'}
for name,digest in required.items(): assert sha(D/name)==digest, name
journals=['goal_terminal_independent_2253_v1.jsonl','goal_terminal_independent_2253_v2.jsonl','goal_terminal_independent_2253_diagnostic.jsonl','goal_terminal_independent_2253_archive.jsonl']
provenance=[]
for name in journals:
    src=R/'results/formal_main_v2/control_transport'/name
    dst=D/('transport_'+name)
    assert src.is_file() and not dst.exists(), str(src)
    data=src.read_bytes()
    dst.write_bytes(data)
    provenance.append({'source':str(src.relative_to(R)),'destination':dst.name,'sha256':sha(src),'bytes':len(data)})
put('transport_provenance.json',{'journals':provenance,'finalizer_own_transport_journal':'results/formal_main_v2/control_transport/goal_terminal_independent_2253_finalize.jsonl','own_journal_archived_separately_by_root':True})
put('finalizer_creator_failure.json',{'kind':'in_memory_remote_creator_syntax_failure','error':'SyntaxError caused by nested same triple-quote delimiters in creator script','remote_finalizer_file_created':False,'scientific_or_production_files_modified':False,'correction':'Use distinct triple quote delimiters; preserve review artifacts unchanged.'})
notes="""# Goal 3054127 独立终验交付

本包仅验收开发工程证据。58 条固定前缀、29 个配对初态、940 次 query、7302 个环境动作均重建通过，Slurm 分配为 840 GPU 秒。173 个冻结源码文件、实际 P 入口、原授权、模型和选择器 checkpoint 身份均核对；不增加科学成功率分母。

15 个归档分卷的 10741 个 blob 成员逐一核对路径、类型、SHA 与字节数，合计 474068525 个原始字节；12 个元数据/日志按 P 原件核对。两个零字节运行锁仍保留在 P，已显式记入原始清单，未混入归档数据。失败或负结果未删除。

第一次终审脚本将 runner_raised=False 错当 None，检查失败后有界更正为源代码真实布尔契约；原脚本、失败记录与更正记录全部保留。归档全部验证均通过。finalizer 创建中的引号语法错误发生于内存代码解析，未写出文件，另有明确记录。

与旧 200 条记录相比，第 27、33、34、46、57、58 条存在观测或动作差异，其中 34 的已执行动作相同。与上一工程 3053440 相比仅第 30 条不同：t0 的观测、仿真与 RNG 相同，前 72 个已执行动作一致，到 query 9 / step 72 才首次出现输入 hash 差异，随后动作分歧。旧工程未保留该处非 t0 原始输入，不能据此判明渲染、仿真或其他未记录状态的原因。

旧 Goal 200 条和新增科学开发继续 HOLD；本包不宣称原因查明或旧失败修复，不授权重跑、最终 release 或完整 O2A。后续完整固定清单的被动门控和显式替代尝试链仍须另行精确登记与独立准入，不用普通 resume 的终态跳过冒称修复。
"""
assert not (D/'README.md').exists()
(D/'README.md').write_text(notes,encoding='utf-8')
review={
 'schema':'formal_main_v2_independent_delivery_review_v1',
 'status':'passed_engineering_terminal_and_archive_only','reviewed_by':'independent_subagent',
 'job_id':'3054127','blockers':[], 'source173_verified':True,
 'actual_P_runtime_closure_verified':True, 'scientific_trials_added':0,
 'Goal_original_200_hold':True,'Goal_new_scientific_development_hold':True,
 'old_cause_identified':False,'old_failure_repaired':False,
 'final_release':False,'automatic_retry_authorized':False,
 'allocated_gpu_seconds':840,'engineering_trials':58,'paired_initial_states':29,'queries':940,'executed_steps':7302,
 'all_raw_blob_members_verified':10741,'raw_blob_bytes':474068525,'archive_parts_verified':15,'metadata_and_logs_verified':12,
 'reviews':required,'state_modified':False,'Git_modified':False,'P_modified':False,'Slurm_modified':False,
 'note':'Pass is engineering evidence retention and provenance only; scientific holds remain.'}
put('delivery_review.json',review)
files={}
for p in sorted(D.iterdir()):
    assert p.is_file() and not p.is_symlink(), str(p)
    if p.name=='delivery_manifest.json': continue
    files[p.name]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest={'schema':'formal_main_v2_independent_audit_delivery_manifest_v1','kind':'independent_audit_delivery_manifest','status':'frozen','root':str(D),'file_count':len(files),'total_bytes':sum(v['bytes'] for v in files.values()),'files':files,'delivery_review':{'path':'delivery_review.json','sha256':sha(D/'delivery_review.json')},'weights_or_sealed_final_values':False,'scientific_release':False}
put('delivery_manifest.json',manifest)
print(json.dumps({'delivery_manifest':str((D/'delivery_manifest.json').relative_to(R)),'manifest_sha256':sha(D/'delivery_manifest.json'),'file_count':len(files),'delivery_review_sha256':sha(D/'delivery_review.json')},ensure_ascii=False))
