from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2253'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
 p=D/name
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
assert sha(D/'independent_delivery_review.json')=='2394fafcf03768f1ce694a2a064fd298cc77dc9852943dc221b6f571f6d1bef2'
assert sha(R/'results/experiment_supervisor/state.json')=='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10'
assert sha(R/'results/formal_main_v2/preflight/heartbeat_20261021T0653/final_summary.json')=='f4d17e968396671b9e8072de1503133652b437e1dd9eee040f74c5d37a56b12d'
journals=[]
for name in ['delivery_independent_2253_precheck.jsonl','delivery_independent_2253_final_v3.jsonl']:
 src=R/'results/formal_main_v2/control_transport'/name;dst=D/('transport_'+name);data=src.read_bytes();rows=[json.loads(x) for x in data.splitlines()];assert rows[0]['event']=='control_start' and rows[-1]['event']=='control_end';dst.open('xb').write(data);journals.append({'source':str(src.relative_to(R)),'copy':dst.name,'sha256':sha(src),'bytes':len(data)})
save('transport_provenance.json',{'completed_journals':journals,'finalizer_journal':'results/formal_main_v2/control_transport/delivery_independent_2253_freeze.jsonl','finalizer_journal_archived_separately_by_root':True})
notes="""# 20261020T2253 最终交付独审

前置归档核查 733 项，最终快照核查 3835 项均通过。36 pair / 72 arms / 360000 更新及原 root+独立训练终验链逐项复核；173 冻结文件在 R、P 冻结快照及 R 镜像保持原字节。开发仍为5800当前动作+600明确兼容Long=6400/8800，历史7012，最终0/35200封存。

从冻结 raw sacct 与 squeue 独立重建271唯一正式分配，累计1986011 GPU秒。Goal3054127完整分配840秒，其前轮已计217秒，本轮净增623；Spatial3054201唯一原ACK，冻结观察709秒。本轮合计净增1332秒。均非未来成本估计。

Goal工程与完整blob归档的已通过独审绑定原SHA，本轮不重复10741 blob全扫。Goal原200和新增科学HOLD。Spatial12 legacy与588 current分别绑定，保留393+2历史GPU秒；精确ACK补登记没有新submit，尚不接受完整600批。Object599兼容证明和18文件单失败CPU候选分别归档；候选仅作者测试，未独立生产准入，原policy_error和6713秒不删。

单次ACK补登记31文件及34项终核证据已绑定。此次最终审查不读取运行中的P ledger/report，也不查询Slurm，不改state、Git、P或作业。

Git入口只审最后v4，SHA3fac309a6515f8ab7f7c124a4bec944c8f61b3881c337f3b20a30d85011bc63b。v4从固定Goal归档manifest及每个包manifest提取exact allowlist，显式force-add被.gitignore隐藏的15卷与12份metadata/log和包内原件；没有宽泛加入被忽略目录。实际运行仍须执行同state、writer lock、索引范围与173字节检查。本独审不执行commit/push。

未执行的auditor v1/v2保留，v3仅增加最终ACK包、v4 Git门槛及精确旧文档前置换行识别；文档历史尾部SHA仍必须完全一致。本次实际前置与最终检查均一次通过，运输日志原字节保留。
"""
(D/'README.md').open('x',encoding='utf-8').write(notes)
files={}
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink()
 if p.name=='delivery_manifest.json':continue
 files[p.name]={'sha256':sha(p),'bytes':p.stat().st_size}
save('delivery_manifest.json',{'schema':'formal_main_v2','kind':'final_delivery_independent_audit_manifest','status':'frozen','root':str(D),'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files.values()),'files':files,'review':{'path':'independent_delivery_review.json','sha256':sha(D/'independent_delivery_review.json')},'source173_verified':True,'final_sealed':True,'state_sha256':'a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10','scientific_results_added':0,'new_GPU_seconds':0,'no_state_Git_P_Slurm_mutations':True})
print(json.dumps({'manifest_path':str((D/'delivery_manifest.json').relative_to(R)),'manifest_sha256':sha(D/'delivery_manifest.json'),'file_count':len(files),'review_sha256':sha(D/'independent_delivery_review.json')}))
