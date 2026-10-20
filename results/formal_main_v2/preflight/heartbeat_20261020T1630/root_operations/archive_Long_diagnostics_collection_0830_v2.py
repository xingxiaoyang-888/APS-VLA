from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1630';E='results/formal_main_v2/engineering/supervision_delivery_0830'
D='.local/long64_selected_diagnostics_0830';C='.local/long_collection_prepare_0830'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def save(rel,x):
 p=R/rel
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
EXTERNAL={"results/formal_main_v2/control_transport/long_collection_prepare_0830_input_a2.jsonl":"37e8214ee3ffb6b8ddf6bb08faeb7ca4f2b18cece7f2064dd0d28dbc7c2a5023","results/formal_main_v2/control_transport/long_collection_prepare_0830_plan_a1.jsonl":"f3e0ec6f8b9ad603ca4d8ee6b9ff23ec16113685ebdc616d02ace0ccac27f16a","results/formal_main_v2/control_transport/long_collection_prepare_0830_fresh_collect_a1.jsonl":"bfc22d377fc9d37e3f8332a4ec2cdb924b5ea910c51b337c4d0f3a7e35908bc7","results/formal_main_v2/control_transport/long_collection_prepare_0830_plan_a2.jsonl":"a1e5e45d423f2b3dcabcaaaeeef14ad21bb08c43fd711a1e494ba46e72958703"}
def archive(rel,pin,target):
 m=checked(rel,pin);base=Path(rel).parent;rows=[dict(x) for x in m['files']]
 rows.append(dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size));copies=[]
 assert len(rows)==len({x['path'] for x in rows})
 for x in rows:
  p=Path(x['path'])
  assert '..' not in p.parts and not p.is_absolute()
  if p.is_relative_to(base):
   target_rel=p.relative_to(base);allowed_base=R/base
  else:
   assert p.as_posix() in EXTERNAL and EXTERNAL[p.as_posix()]==x['sha256']
   assert json.loads((R/p).read_bytes().splitlines()[-1])['event']=='control_end'
   target_rel=Path('logs')/p.name;allowed_base=R/'results/formal_main_v2/control_transport'
  source=R/p;assert source.is_file() and not source.is_symlink() and source.resolve().is_relative_to(allowed_base.resolve())
  assert h(source)==x['sha256'] and source.stat().st_size==x['bytes']
  assert source.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npy','.npz'] and source.stat().st_size<100*(1<<20)
  dest=R/E/target/target_rel
  if dest.exists():assert target=='Long64_selected_diagnostics' and h(dest)==h(source) and dest.stat().st_size==source.stat().st_size
  copies.append((source,dest,dict(path=p.as_posix(),sha256=x['sha256'],bytes=x['bytes'])))
 for source,dest,x in copies:
  dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():
   with dest.open('xb') as f:f.write(source.read_bytes())
 return [dict(source=x,archive=ref(dest.relative_to(R).as_posix())) for source,dest,x in copies]
diag=checked(D+'/selected_checkpoint_diagnostics.json','6e816d88b82b61c1e27f363a3586f56171b28cbfc6a4283cc22e35ca9ba84274')
assert diag['status']=='pass' and len(diag['rows'])==6 and diag['missing_fields']==[] and diag['same_fixed_validation_panel']['all6_match']
assert diag['GPU_seconds_added']==0 and not diag['checkpoint_bytes_read'] and not diag['fresh_predictions']
for x in diag['input_files']:
 assert h(R/x['path'])==x['sha256'] and (R/x['path']).stat().st_size==x['bytes']
for row in diag['rows']:
 assert row['validation_windows']==165 and row['validation_tasks']==10
 node=min(row['all11_evaluation_nodes'],key=lambda x:(x['validation_metric'],x['update']))
 assert node['update']==row['selected_update']
 assert node['validation_metric']==row['selected_validation_task_macro_hard_teacher_L1']
 v=checked(row['selected_validation_file']['path'],row['selected_validation_file']['sha256'])
 assert v['update']==row['selected_update'] and v['validation_metric']==node['validation_metric']
stat=checked(E+'/Long64_terminal_independent/Long64_three_seed_statistics.json','510cfc9c907b0d721df0ce39b6d528adddaf7b04575e848ec21e5622ba6f98d4')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive0830',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 dc=archive(D+'/manifest.json','36d38ef5bcb9e520b3b3b068270608ecd906e895ba3416a2944535237f638feb','Long64_selected_diagnostics')
 cc=archive(C+'/delivery_files.json','19cf2d76142d357dd2da76ad5d90822f204d96afd43d8bb4e51de1bc525726ef','Long_collect_author_candidate')
 dr=save(B+'/Long64_selected_diagnostics_delivery.json',dict(copies=dc,source_manifest=ref(D+'/manifest.json'),root_checked_all_selected_nodes=True,no_weights_read=True,new_GPU_cost=0))
 cr=save(B+'/Long_collect_author_candidate_delivery.json',dict(copies=cc,source_manifest=ref(C+'/delivery_files.json'),CPU_author_candidate_only=True,independent_or_root_or_GPU_acceptance_not_inferred=True,failed_CPU_attempts_retained=True))
 report='# 正式Long64三种子开发结论\n\n2026-10-20；formal_main_v2开发阶段。固定训练、选模和部署设置未改，最终初态未开放。\n\n'
 report+='| seed | A成功/100 | B成功/100 | B−A百分点 | 初观测token重合率 | 开发GPU秒 |\n|---:|---:|---:|---:|---:|---:|\n'
 for seed in [17,23,41]:
  q=stat['per_seed'][str(seed)];report+=f'|{seed}|{q["A_successes"]}|{q["B_successes"]}|{q["B_minus_A"]*100:+.3f}|{q["token_overlap_initial_observation_mean"]*100:.5f}%|{q["development_GPU_seconds"]}|\n'
 report+='\n三seed均值：A **87.333%**（种子间SD2.517个百分点），B **90.333%**（SD3.215）；B−A **+3.000个百分点**（SD1.732）。原登记10000次配对bootstrap、seed20261016、每任务内重采样初态，每簇携全部3seed及A/B，95%区间 **[-0.333,+6.333]个百分点**。root另从600条原始结果以整数簇独立重算全部30000个draw值通过。\n\n'
 report+='600条仅对应100个唯一初态。区间包含零，尚不能确认稳定改善；差异不显著也不代表等效。完整O2A尚未完成，不作成功率—延迟折中结论，未评价相对Dense不下降2个百分点的目标。\n\n'
 report+='| 任务ID | s17 A/B（各/10） | s23 A/B | s41 A/B | 三seed平均B−A百分点 |\n|---:|---:|---:|---:|---:|\n'
 for t in range(10):
  cells=[]
  for seed in [17,23,41]:
   v=stat['per_seed'][str(seed)]['per_task'];cells.append(str(v[f'A64_seed{seed}'][str(t)]['successes'])+'/'+str(v[f'B64_seed{seed}'][str(t)]['successes']))
  report+='|'+str(t)+'|'+'|'.join(cells)+f'|{stat["per_task"][str(t)]["B_minus_A_mean"]*100:+.3f}|\n'
 report+='\n负差任务0、2、9与所有种子完整保留，不择优。Long256已有三seed均值B−A+2.333个百分点、95%区间[-1,+6]；Long128 seed23与41仍各为A95/B92（−3个百分点），不因64/256较好的点估计而删除。旧128 seed17及Dense/均匀参考的执行语义复用还需完成单独核验，尚不混入当前语义统计。\n\n'
 report+='硬剪枝动作误差来自固定165个validation窗口、10任务等权的已选checkpoint；不以5000步末次误差替代选模结果。checkpoint完整SHA、11节点记录及来源哈希见附录JSON。\n\n| seed | 方法 | 选中update | teacher L1 | 示范L1 |\n|---:|:---:|---:|---:|---:|\n'
 for q in diag['rows']:report+=f'|{q["seed"]}|{q["arm"]}|{q["selected_update"]}|{q["selected_validation_task_macro_hard_teacher_L1"]:.9f}|{q["selected_validation_task_macro_hard_demonstration_L1"]:.9f}|\n'
 report+='\ntoken重合率来自100个共同开发初始观测，与验证窗口不同；后续轨迹已经分叉，未把后续各自观测当共同输入。新seed41共7215完整动作chunk、57079实际控制步核对通过，训练期未来头部署调用为0。\n\n'
 report+='本轮新增200条开发分配3039GPU秒（0.844小时）；64三seed开发累计9102秒（2.528小时），已包含前两seed成本，两者不可重复相加。诊断只读取非权重记录，未新增GPU计算。全正式轮包括训练、失败、加载和其他工程分配，以监督Slurm总账为准。\n\n'
 report+=f'[统计与全部draw](../{E}/Long64_terminal_independent/Long64_three_seed_statistics.json)，[root独立重算](../{B}/Long64_root_statistics_verification.json)，[已选checkpoint诊断](../{E}/Long64_selected_diagnostics/selected_checkpoint_diagnostics.json)，[200条验收](../{B}/Long_development_acceptance.json)。\n'
 p=R/'docs/正式Long64三种子开发结论.md'
 with p.open('x') as f:f.write(report)
 assert h(R/'results/experiment_supervisor/state.json')==before
 proof=save(B+'/Long64_diagnostics_root_verification.json',dict(status='passed_selected_checkpoint_nonweight_reconstruction',diagnostics=ref(E+'/Long64_selected_diagnostics/selected_checkpoint_diagnostics.json'),six_selected_nodes_verified=True,fixed_validation_windows=165,tasks=10,development_unique_states=100,doc=ref('docs/正式Long64三种子开发结论.md'),diagnostics_delivery=dr,collection_author_delivery=cr,state_unchanged=True,new_GPU_calls=0))
 save(B+'/archive_attempt01_correction.json',dict(status='bounded_archive_path_correction',failed_source_sha256=h(R/'.local/archive_Long_diagnostics_collection_0830.py'),replacement_source_sha256=h(Path(__file__)),reason='Author manifest deliberately includes four exact closed transport logs outside its private directory. Archive those exact pinned logs under logs/ instead of prefixing private path.',allowed_external_logs=EXTERNAL,no_source_rewrite=True,no_state_write=True,no_GPU_cost=True))
 print(json.dumps(dict(status='diagnostics_and_collection_candidate_archived',receipt=proof,diagnostic_files=len(dc),collection_files=len(cc))))
