from pathlib import Path
import json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/git_stage_precheck_20261021T0449'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,b):
 with (D/name).open('xb') as f:f.write(b)
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
p=D/'independent_precheck.json';assert sha(p.read_bytes())=='10f50efa57479dedab60af4ae08937c40f42107e8eb53d3e9054658f5db52d5f'
j=json.loads(p.read_bytes());assert j['status']=='passed_current_archive_precheck_pending_final_required' and j['blockers']==[] and j['check_count']==len(j['checks'])==2352
text="""# 当前 Git 归档范围静态预检

本包只核 Git 交付范围：当前 B/E 的原字节、manifest/source_map、CPU tar 全成员和既有文件名 guard。不是作者对本人 Goal runtime 的独立科学审核；不重跑科学 CPU/GPU 测试。运行时科学独审仍由另一代理报告承担。

实际执行 precheck_v2.py，2352 项全部通过。捕获 389 文件、7 个包 manifest，19 个 CPU tar 的 7770 成员逐 SHA/bytes 比对，包含与服务器私有原成员的相等检查，未解包。tar 内 .bin 仅已标记 CPU fixture 的不超过 36 字节小观测/模拟器数组，不作为松散 Git 文件；其他压缩成员及原失败/候选也全部保留。173 冻结源在 R、原 S、R 快照三个根均核原 SHA。当前路径均过原 lexical 守卫，全部单文件不超过 100MiB，无 Markdown 尾空白或额外 EOF 空行。

precheck_v1.py 未执行，静态发现根作者 gateway manifest 是 root 新生成而非私有原 manifest 后保留 v1，并写 v2 显式区分该生成来源；未放宽任何复制成员的 SHA/bytes 核验。

captured_inventory.json 是当前捕获清单，不是最终 required 文件。manifest_mapping_review.json 中未被作者 manifest 覆盖的操作收据需要 root 的最终精确 allowlist。后续新增 Goal30、提交、最终 state/docs 及其他文件不自动继承本次通过。

原 guard 的 lexical 谓词本身允许 raw_runtime/.../events.jsonl 和 observer/blobs/*.rng.json。最终 stage 必须另行排除整个 loose raw_runtime 与 observer/blobs 路径，不能只排除 .bin。不得加入权重、checkpoint、封存/test 初态；不能修改 guard 或173源以让清单通过。CPU 原始小 blob 只通过本包所核精确 tar+members 清单回存。

最终 required 需全部路径唯一（含大小写别名）、无自指、每项准确 path/SHA/bytes，并保留原失败与候选。root stage 后还须原 nonweight index/archive restore/frozen173 验证。本次未读取或修改 Git index、未提交、未推送；未修改 state、canonical、P，无 Slurm 调用。

执行 trace：results/formal_main_v2/control_transport/git_stage_precheck_20261021T0449_v2.jsonl。
"""
write('README.md',text.encode())
files=[]
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink()
 if p.name=='delivery_manifest.json':raise AssertionError('manifest already exists')
 b=p.read_bytes();files.append({'path':p.name,'sha256':sha(b),'bytes':len(b)})
assert len(files)==8
m={'schema':'formal_main_v2','kind':'bounded_Git_archive_static_precheck_delivery','source_root':str(D),'status':'frozen_current_archive_precheck_final_required_pending','file_count':len(files),'files':files,'report_sha256':sha((D/'independent_precheck.json').read_bytes()),'independent_scientific_runtime_audit':False,'Git_index_writes':0,'state_writes':0,'new_GPU_submissions':0,'final_required_checked':False,'final_release':False}
write('delivery_manifest.json',enc(m))
print(json.dumps({'manifest':str((D/'delivery_manifest.json').relative_to(R)),'sha256':sha((D/'delivery_manifest.json').read_bytes()),'file_count':len(files),'report_sha256':m['report_sha256']},sort_keys=True))
