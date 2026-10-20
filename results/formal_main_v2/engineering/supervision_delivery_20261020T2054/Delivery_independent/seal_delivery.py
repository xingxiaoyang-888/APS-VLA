from pathlib import Path
import datetime,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2054'
assert D.resolve()==D and not (D/'delivery_manifest.json').exists()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(D/'final_review.json')=='4ae69c68faf3ac99b3580fee6e73540c3b3192b1bfa387a8459bc4e17540f3a7'
assert h(R/'results/experiment_supervisor/state.json')=='cf54288d932880c061936f89f94dd3fb9b71c99382226d5276bb694fe6c2f33a'
names=['delivery_static_precheck_2054.jsonl','delivery_all9_archive_2054.jsonl','delivery_CPU_archives_2054.jsonl','delivery_CPU_archives_v2_2054.jsonl','delivery_docs_baseline_2054.jsonl','delivery_final_review_2054.jsonl','delivery_final_review_v3_2054.jsonl']
transport=[]
for name in names:
 p=R/'results/formal_main_v2/control_transport'/name;b=p.read_bytes();events=[json.loads(x) for x in b.splitlines()]
 assert events[0]['event']=='control_start' and events[-1]['event']=='control_end'
 q=D/'transport'/name;q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(b)
 transport.append({'original':str(p.relative_to(R)),'copy':str(q.relative_to(R)),'sha256':h(q),'closed':True})
corr={'kind':'bounded_audit_schema_corrections','scientific_evidence_changed':False,'GPU_seconds':0,'failures_preserved':[
{'source':'check_CPU_archives.py','transport':'delivery_CPU_archives_2054.jsonl','failure':'KeyError real_GPU_or_final_values: independent archive index uses GPU_runs/scientific_trials_added instead of author schema.','correction':'check_CPU_archives_v2.py validates the two exact original schemas separately and verifies every tar member.'},
{'source':'final_delivery_audit_v2.py','transport':'delivery_final_review_2054.jsonl','failure':'Extra audit assumption K64 archived26; normalized archive actually retains26 content files plus original delivery manifest=27.','correction':'final_delivery_audit_v3.py requires exactly27, original26 manifest exact SHA, and all bytes identical.'}]}
(D/'audit_corrections.json').write_text(json.dumps(corr,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
readme="""# 本轮交付独立核验

最终 final_review.json 状态 passed_final_delivery_review，891 项检查通过，blockers=[]；绑定 state SHA cf54288d932880c061936f89f94dd3fb9b71c99382226d5276bb694fe6c2f33a。

核对范围：173 个冻结源码在 R 与原运行快照逐字节一致；新400条来自3053875/3053894真实原始 ledger、精确pair来源桥及原consumer独审，未重复算初态或成本；新state只有预期400条接纳及两个作业终态更新；269项分配合计1984462 GPU秒；5份更新文档保留原文后缀字节；新逐任务/L1/token表所有数字对应独审JSON；6个CPU/诊断包64文件、1061 tar成员及K64原26文件＋原manifest全部原样归档；9大文件39块607951215字节在内存无损重建，既有Git HEAD内容一致。

封存最终仍0，未开放完整O2A；Spatial588兼容/新入口、Object旧记录兼容与Goal生产GPU验收均未通过，不将CPU候选升级为科学准入。所有历史尝试和负结果保留。

本审核未提交GPU、未修改state/Git、未读取封存值。两次额外审核schema假设失败见 audit_corrections.json，原脚本和transport失败均保存，未更改科学证据以通过测试。

角色说明：本agent此前为Spatial588候选作者。这里仅独立审核root交付事务及归档字节；Spatial588候选算法的独立结论来自另一审核agent及已归档独立报告，不将作者自检称为独立算法审核。root仍负责复制此包到E/Delivery_independent，并按确切报告SHA进入Git准入。
"""
(D/'README.md').write_text(readme,encoding='utf-8')
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert not p.is_symlink()
  files.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':h(p)})
out={'schema':'formal_main_v2','kind':'independent_final_delivery_audit_package','root':str(D.relative_to(R)),'status':'passed_final_delivery_review','blockers':[],'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'files':files,'final_review':{'path':str((D/'final_review.json').relative_to(R)),'sha256':h(D/'final_review.json')},'state_sha256':'cf54288d932880c061936f89f94dd3fb9b71c99382226d5276bb694fe6c2f33a','source173_verified':True,'final_sealed':True,'new_GPU_jobs':0,'scientific_trials_added_by_auditor':0,'state_Git_Slurm_mutations':False,'sealed_values_read':False,'transport_copies':transport,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
p=D/'delivery_manifest.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'manifest':str(p.relative_to(R)),'sha256':h(p),'file_count':len(files),'final_review_sha256':h(D/'final_review.json')}))
