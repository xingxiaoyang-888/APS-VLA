from pathlib import Path
import argparse, hashlib, json, time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_terminal_archive_20261021T0334'
def h(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
def write_json(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
def main(manifest_sha):
    vp=D/'verify_archives.py';vraw=vp.read_bytes()
    require(h(vraw)=='e466661b2899ce289947867c2b44eeb280fd34a2ee15f48c7bb20721a3fea2d3','verifier identity')
    V={'__name__':'goal_archive_final_verifier','__file__':str(vp)};exec(compile(vraw,str(vp),'exec'),V)
    verified=V['verify'](D,manifest_sha)
    write_json(D/'read_only_reverification.json',verified)
    inv=json.loads((D/'inventory.json').read_bytes());manifest=json.loads((D/'archive_manifest.json').read_bytes())
    require(inv['scientific_admission'] is False and manifest['scientific_admission'] is False,'scope')
    provenance=D/'provenance';provenance.mkdir(exist_ok=False)
    sources=[
      (R/'.local/archive_goal_terminal_20261020T2253.py','previous_58_trial_archive_source.py','885c65d1443a8579df6ad0b4b29aa96fbe7aa6bb6206d1deb353980615e06447'),
      (P/'scripts/ops/formal_goal_full200_gate_v1/consumer.py','original_goal_full200_consumer.py','c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b'),
      (P/'scripts/ops/formal_goal_full200_gate_v1/observer_v3.py','original_goal_full200_observer.py','bd60cb3b97db443f0953d53cd0a7e0719f437807716bda0ef462610495572f23'),
      (P/'scripts/ops/formal_goal_full200_gate_v1/package_manifest.json','original_runtime_package_manifest.json','2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec'),
      (R/'results/formal_main_v2/preflight/heartbeat_20261021T1134/initial_observation.json','saved_initial_observation.json','0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41')]
    provenance_refs=[]
    for p,name,pin in sources:
        raw=p.read_bytes();require(h(raw)==pin,'provenance SHA '+name)
        out=provenance/name
        with out.open('xb') as f:f.write(raw)
        provenance_refs.append({'original_path':str(p),'path':out.relative_to(D).as_posix(),'bytes':len(raw),'sha256':pin})
    for name in ('inventory','extract','archive','verifier_tests'):
        p=R/('results/formal_main_v2/control_transport/goal_terminal_archive_20261021T0334_'+name+'.jsonl')
        raw=p.read_bytes();require(raw.endswith(b'\n'),'incomplete transport journal')
        records=[json.loads(line) for line in raw.splitlines()]
        require(records,'empty transport journal')
        out=provenance/('transport_'+name+'.jsonl')
        with out.open('xb') as f:f.write(raw)
        provenance_refs.append({'original_path':str(p),'path':out.relative_to(D).as_posix(),'bytes':len(raw),'sha256':h(raw)})
    write_json(D/'provenance_manifest.json',{'schema':'formal_main_v2','kind':'Goal3054717_nonweight_archive_provenance','files':provenance_refs,'note':'Saved scheduler observation reused, no new Slurm query. Original consumer only read_blob/strict_json CPU reads, no scientific consumer verdict.'})
    tests=json.loads((D/'verifier_CPU_tests.json').read_bytes())
    require(tests['status']=='passed' and tests['positive_count']==1 and tests['negative_count']==22,'container CPU tests')
    summary={'schema':'formal_main_v2','kind':'Goal3054717_nonweight_archive_preparation_delivery','status':'passed_exact_archival_scope','job_id':'3054717','inventory_sha256':h((D/'inventory.json').read_bytes()),'P_pull_allowlist_sha256':h((D/'P_terminal_pull_allowlist.json').read_bytes()),'archive_manifest_sha256':manifest_sha,'restoration_verification_sha256':h((D/'restoration_verification.json').read_bytes()),'read_only_reverification_sha256':h((D/'read_only_reverification.json').read_bytes()),'namespace_counts':inv['counts'],'member_count':35076,'raw_bytes':1680131983,'volume_count':manifest['volume_count'],'compressed_bytes':manifest['compressed_bytes'],'largest_compressed_volume_bytes':max(p['bytes'] for p in manifest['parts']),'container_integrity_positive_tests':1,'container_integrity_rejection_tests':22,'source_files_unchanged':True,'P_observer_blobs_exact_event_allowlist':True,'R_observation_blobs_already_in_R':True,'unknown_or_unreferenced_files':[],'source_symlinks':[],'scientific_admission':False,'new_trials':0,'new_GPU_jobs':0,'weights_or_sealed_final_values':False,'root_publication_required':True,'remaining_scope':'Root may copy/publish exact archive set and bind separate scientific terminal review. This package makes no success-rate or scientific admission decision.'}
    write_json(D/'author_report.json',summary)
    readme=f"""# Goal3054717 非权重终态精确归档

仅准备和验证归档；不做科学终验、成功率统计或新试验。复用 root 已保存的 COMPLETED 0:0 / 2205 GPU 秒证据，不另查 Slurm，不写 state/Git/P 或冻结源。

- inventory.json 是不可变事件引用清单，SHA {summary['inventory_sha256']}。逐唯一 blob 实际调用原 consumer.read_blob，核文件名内容地址、bytes、SHA、无 symlink；事件所有引用与两个源目录精确相等。
- R 五组件开发观测：19,540 blob / 1,544,833,664 B；R claim.json：360 B。它们本来已在 R，不需 P→R 再复制。
- P 被动模拟器/RNG：15,522 blob / 4,014,813 B；P 原始元数据：13 项 / 131,283,146 B（含两零字节锁）。P_terminal_pull_allowlist.json 给出每项 P-relative / attempt-relative / bytes / SHA。root 拉取可显式排除两锁；归档保留用于完整还原。
- 全部 35,076 项 / 1,680,131,983 原始字节。volumes/ 共 {summary['volume_count']} 卷，压缩总 {summary['compressed_bytes']} B，最大 {summary['largest_compressed_volume_bytes']} B；每卷严格小于 90 MiB。
- archive_manifest.json SHA {manifest_sha}。各卷成员索引精确引用 inventory，不通过 glob 把未知 .bin 加入 Git。R observations、P passive、P metadata 和 R metadata 分开归档。
- 归档采用 gzip + tar PAX（mtime=0，uid/gid=0，mode=0600）。创建后逐卷流式解压检验全部成员顺序/type/bytes/SHA，再由独立只读入口完整复核一次，均通过。原始文件未修改。
- CPU 容器测试 1 正例 / 22 拒绝，用两份已记录真实被动 blob 仅构造 tar 容器，拒绝损坏、错 SHA/size、重复/漏/额外成员、乱序、symlink、路径穿越。不是模拟器重跑或新科学结果。

## 精确恢复和审核

inventory.members[*].restore_root 只能是 R 或 P，restore_relative 是原文件相对根路径；archive_path 是卷内名字。恢复时先跑只读完整验证，再由 root 决定唯一目标；不得覆盖不同内容或从 tar 自行接受额外路径。本任务只流式验证，未向原路径解压。

可在原私有包或 root 发布后的完整目录运行只读检查（正常项目执行仍通过已审 transport，固定脚本 SHA e466661b2899ce289947867c2b44eeb280fd34a2ee15f48c7bb20721a3fea2d3）：

    python -B verify_archives.py --directory <完整归档包目录> --manifest-sha256 {manifest_sha}

所有成员、卷、清单、脚本和恢复报告按 delivery_manifest.json 逐项 SHA 发布；不要把未压缩原始 .bin 直接加入 Git。provenance/ 保留原 58 条归档实现、当前 frozen consumer/observer/package、原保存 Slurm 观察及本次 transport 原日志。

本包不采纳 200 条科学结果，不改原失败/尝试历史，不开放 sealed final，不重复计 GPU 成本。科学终验由 root 和独立审核另行完成。
"""
    with (D/'README.md').open('x',encoding='utf-8') as f:f.write(readme)
    files=[]
    for p in sorted(D.rglob('*')):
        require(not p.is_symlink(),'delivery symlink')
        if not p.is_file() or p.name=='delivery_manifest.json':continue
        raw=p.read_bytes();require(len(raw)<100*1024*1024,'single deliverable exceeds100MiB')
        files.append({'path':p.relative_to(R).as_posix(),'bytes':len(raw),'sha256':h(raw)})
    delivery={'schema':'formal_main_v2','kind':'Goal3054717_nonweight_archive_delivery_manifest','root':D.relative_to(R).as_posix(),'file_count':len(files),'files':files,'author_report':{'path':(D/'author_report.json').relative_to(R).as_posix(),'sha256':h((D/'author_report.json').read_bytes())},'archive_manifest':{'path':(D/'archive_manifest.json').relative_to(R).as_posix(),'sha256':manifest_sha},'scientific_admission':False,'new_trials':0,'new_GPU_jobs':0}
    write_json(D/'delivery_manifest.json',delivery)
    print(json.dumps({'status':summary['status'],'path':(D/'delivery_manifest.json').relative_to(R).as_posix(),'sha256':h((D/'delivery_manifest.json').read_bytes()),'file_count':len(files),'volume_count':manifest['volume_count'],'compressed_bytes':manifest['compressed_bytes'],'largest_volume_bytes':summary['largest_compressed_volume_bytes'],'report_sha256':h((D/'author_report.json').read_bytes())}),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--manifest-sha256',required=True);args=a.parse_args()
    try:main(args.manifest_sha256)
    except BaseException as e:
        write_json(D/('finalization_failure_%s.json'%time.time_ns()),{'status':'failed','exception_type':type(e).__name__,'message':str(e)})
        raise
