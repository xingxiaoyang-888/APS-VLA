from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/integration_candidate_20261020T1530'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,b):
 with p.open('xb') as f:f.write(b)
def raw(x):return (json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
entry=D/'integrate_1530_v2.py';assert digest(entry)=='c05d049e4d56d82708a64e05802ca9281f91f191d3e510ccbbc54550a8d25219'
checks=json.loads((D/'cpu_selfcheck_v1.json').read_bytes());assert checks['status']=='passed' and checks['count']==62
preview=D/'preview_95f917f55464';r=json.loads((preview/'receipt.json').read_bytes());assert r['canonical_state_unchanged'] and r['canonical_docs_unchanged']
logs=[]
for name in ['integration1530_preview_v2.jsonl','integration1530_cpu_selfcheck_v1.jsonl']:
 p=R/'results/formal_main_v2/control_transport'/name;rows=[json.loads(s) for s in p.read_text().splitlines()]
 assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==0 and rows[-1]['source173_and_entrypoint_unchanged']
 out=D/'transport';out.mkdir(exist_ok=True);dst=out/name;write(dst,p.read_bytes());logs.append({'source':str(p.relative_to(R)),'copy':str(dst.relative_to(R)),'sha256':digest(p)})
readme="""# 完成结果接纳候选 20261020T1530

状态：私有候选。作者未 apply；未提交任何 GPU 作业、未修改 canonical state/docs/Git。实际服务器 CPU private preview 通过，62 项正反 CPU 检查通过。必须先独审，再由 root 明确执行 --apply。

本事务仅接纳 Goal64 seed17（3043762）A/B 的原 root 与独立训练终验（+2组/+10000更新），及三批已完成开发3050192、3050205、3050224（+600条）。目标66/72、331000 reviewed updates；current4400/raw5612/compatible5000，唯一初态仍400。Spatial256三seed完整保留负种子23，Object256仅17/41并明确缺23。没有完整O2A或等效结论。

不依赖新派发：controller、owner、lease、registry、pending、reservation、hold、machine completion68/330000及后续dispatch字段逐值保留。目标训练pair原machine proof原样保留，另增加root/ind证明；其他pair不变。Goal原200HOLD及Object兼容桥未科学准入保持不变。Goal工程探针由root另行登记，此候选不接纳其任何科学trial。

顶层current_work/next_actions/last_root_*原叙述也按root要求保留。root将在本轮后续dispatch/Git最终汇总事务更新这些叙述；本事务在 formal_main_progress.integration_20261020T1530_accepted 加精确新summary引用。

安全边界：重新验证所有输入exact SHA、原R/P ledger、173冻结源、真实Slurm终态及全项目累计allocation一次；共享writer.lock内新读state，构建候选、保存原始before bytes、intent排他写入、文档CAS、state CAS。发现已有intent/output/completion就拒绝重入，需要root原证据对账。新工作不写权重、未读封存最终值、不改任何科学设置。每次运行重新观测Slurm，不能沿用preview成本替代后续实际成本。

当前执行文件：integrate_1530_v2.py SHA c05d049e4d56d82708a64e05802ca9281f91f191d3e510ccbbc54550a8d25219。默认只写私有preview；root在明确独审通过后通过已审server_control_transport_v1运行同一入口，参数分隔符 -- 后传 --apply。原v1因作者生成换行转义错误无法编译，原字节及author_compile_failure_v1.json保留；没有执行/生产影响。封存helper作者内存引号错误亦记录。v2是唯一当前候选。

输入：results/formal_main_v2/engineering/supervision_delivery_20261020T1530/{training_independent,terminal_independent}，canonical Goal64s17原双审、B2330真实selected_server和Spatial256重算收据，源内PINS精确绑定。root的bootstrap重算复用审计方算法并确实重新执行，不声称算法由root另行独创。

本私有目录保留源码、失败、CPU测试/原结果、真实preview（含raw state_before和candidate）、闭合transport日志。封存执行自身的外部transport日志因避免递归hash不在此manifest；root可另行精确归档。
"""
write(D/'README.md',readme.encode())
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert not p.is_symlink();files.append({'path':str(p.relative_to(R)),'relative_path':str(p.relative_to(D)),'sha256':digest(p),'bytes':p.stat().st_size})
m={'schema':'formal_main_v2','kind':'private_completed_evidence_integration_candidate_delivery','created_utc':datetime.now(timezone.utc).isoformat(),'status':'sealed_candidate_not_applied_not_independently_approved_yet','source_root':str(D),'entrypoint':{'path':str(entry.relative_to(R)),'sha256':digest(entry)},'CPU_checks':62,'new_GPU_jobs':0,'canonical_mutations':False,'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'closed_transport_copies':logs,'root_next_step':'Independent source/numeric/transaction review, then exact pinned root --apply; update top-level narrative separately with subsequent dispatch summary.'}
write(D/'manifest.json',raw(m));print(json.dumps({'manifest':str((D/'manifest.json').relative_to(R)),'sha256':digest(D/'manifest.json'),'files':len(files),'bytes':m['total_bytes'],'entrypoint':m['entrypoint']},ensure_ascii=False))
