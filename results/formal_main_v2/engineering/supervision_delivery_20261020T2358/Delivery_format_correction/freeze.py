from pathlib import Path
import hashlib,json,datetime,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_format_correction_20261020T2358';B='results/formal_main_v2/preflight/heartbeat_20261021T0758'
H=lambda b:hashlib.sha256(b).hexdigest()
def guard(e,a):
 if e in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No production operations in private freeze')
 if e=='open':
  p,m,f=a
  if isinstance(p,(str,bytes)) and ((m and any(c in m for c in 'wax+')) or (isinstance(f,int) and f&(1|2|64|512|1024))):assert Path(p).resolve().is_relative_to(D)
sys.addaudithook(guard)
def write(n,b):
 with (D/n).open('xb') as f:f.write(b)
r=(D/'final_independent_review.json').read_bytes();assert H(r)=='a5fcf802fc83c945778030ef3f1291c2987aa6a531464d2662c560b2a6da2c07';review=json.loads(r)
assert review['status']=='passed_final_delivery_review' and len(review['checks'])==review['check_count']==575 and not review['blockers']
assert H((R/'results/experiment_supervisor/state.json').read_bytes())==review['state_sha256']
copies=[
('.local/repair_git_format_20261020T2358_v1.py','root_repair_source.py','4100c380d0284009b17c29dda7a1d86a782575064aa34d743d638a20a2884fa2'),
('.local/deliver_20261020T2358_v6.py','root_delivery_v6_source.py','0d308a50847b86786d62ca71f0842749ef913877ad0ec86eac572bfcb60361a3'),
('.local/archive_packages_20261020T2358_v2.py','root_archive_v2_source.py','6d4fe8bc192856d71ac4ab50752beb82dda9a840e7f333918398de2e3ce85b6a'),
(B+'/git_format_repair.json','root_actual_format_repair.json','42c4803ed973c6ccfe47fd884e7379305c48dc7798656e96f0c65090afb616e5'),
(B+'/git_v5_precommit_failure.json','root_preserved_git_v5_failure.json','a0d9a437c72247e066a6f578ed9770f698da1dc72edcbe377f16f180082c85b9'),
(B+'/git_required_files.json','root_failed_v5_required_files.json','e52831510cbbc626612880054e4f151dd4d6c568eeebfe90a55e4e91979987ea'),
(B+'/git_index_guard.json','root_failed_v5_index_guard.json','5129c715ea72a2a49125fb2660f52b059860438e670f9af9888272b60ed57fe7'),
(B+'/commit_transport_argument_correction.json','root_pre_entry_argument_correction.json','2147a340c8236f21c64052b7b3ea0b617c85dc90958fda7de44311e04d3777f2')]
copied=[]
for n,out,w in copies:
 b=(R/n).read_bytes();assert H(b)==w;write(out,b);copied.append({'source':n,'archive':str((D/out).relative_to(R)),'sha256':w,'bytes':len(b)})
journals=[]
for name in ['delivery_format_independent_static_20261020T2358','delivery_format_independent_actual_20261020T2358','repair_git_format_20261020T2358_v1']:
 n='results/formal_main_v2/control_transport/'+name+'.jsonl';b=(R/n).read_bytes();ev=[json.loads(l) for l in b.splitlines()];assert [x['event'] for x in ev]==['control_start','control_end'];assert ev[-1]['returncode']==0 and ev[-1]['source173_and_entrypoint_unchanged'];write(name+'.jsonl',b);journals.append({'source':n,'archive':str((D/(name+'.jsonl')).relative_to(R)),'sha256':H(b),'bytes':len(b)})
readme='''# 限定格式修正交付独审

范围仅原 224 个暂存文件的精确绑定、一份文档末尾删除 1 LF、索引精确恢复以及原审计继承。原完整 3896 项实际审计与 21 文件封包保持原字节，未重跑科研审核。该补包有 35 项静审和 575 项实际限定检查；计数分开，不宣称本轮重新完成原 3896 项。

实际文件为 docs/正式下游阻塞登记_20261020T2358.md，6300 字节变为 6299 字节；语义正文完全一致，其余 223 个文件和 state/summary/inputs 不变。保留失败前的 224 行精确文件清单与原文、根修正入口、已关闭 transport。根入口在共享 writer lock 下核验全部 index/worktree 字节后只 unstage 原清单，验证 index 为空，再删除该文档最后 1 LF。子代理不运行 Git；实际 index 动作的证据为精确审过的根源码及其成功执行日志，非新增 Git 查询。

最终 review status 为 passed_final_delivery_review，source173_verified/final_sealed 为真；沿用原科学范围、成本和 HOLD。0 新 GPU、0 科学试验、0 新 Slurm 查询、0 state/P/canonical 写入。Git v6 的 commit 和 push 仍待根执行，本包不声称远端已同步。

旧完整独审：.local/delivery_independent_20261020T2358/final_independent_review.json
SHA 419c180e8d5bcaa89ba5c5620f7e09dab5302d522d8e4f53e85ff377166af1a5
旧 manifest SHA fa35971d52afc4ce76013aaa734b680dc1cec345dff3c02f787611a8ae5ffc92
'''
write('README.md',readme.encode())
rows=[]
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink() and p.resolve()==p
 b=p.read_bytes();rows.append({'path':str(p.relative_to(R)),'sha256':H(b),'bytes':len(b)})
assert not (D/'delivery_manifest.json').exists()
manifest={'schema':'formal_main_v2','kind':'root_final_delivery_format_correction_independent_manifest','status':'passed_final_delivery_review','reviewed_by':'independent','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(D.relative_to(R)),'files':rows,'file_count':len(rows),'total_bytes':sum(x['bytes'] for x in rows),'blockers':[],'final_review':{'path':str((D/'final_independent_review.json').relative_to(R)),'sha256':H(r)},'state_sha256':review['state_sha256'],'source173_verified':True,'final_sealed':True,'final_release':False,'check_count':575,'static_check_count':35,'original_checks_inherited_not_reexecuted':3896,'original_review':review['original_review'],'original_manifest':review['original_manifest'],'closed_transport_journals':journals,'copied_exact_evidence':copied,'open_transport_journals_excluded':['results/formal_main_v2/control_transport/delivery_format_independent_freeze_20261020T2358.jsonl'],'new_GPU_submissions':0,'new_scientific_trials':0,'additional_Slurm_queries':0,'no_state_Git_P_canonical_writes':True,'Git_commit_and_push_pending':True}
b=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();write('delivery_manifest.json',b)
print(json.dumps({'path':str((D/'delivery_manifest.json').relative_to(R)),'sha256':H(b),'file_count':len(rows),'bytes':len(b),'total_bytes':manifest['total_bytes'],'review_sha256':H(r)}))
