"""Render the completed, independently audited Long64/128 evidence; no jobs."""
from pathlib import Path
from collections import defaultdict
from statistics import mean
import hashlib, json, os

r=Path('F:/CTI-VLA'); out=r/'results/g1_future_long_k64_v1'; seeds=('17','23','41')
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def write(path,text): path.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
def pct(value): return f'{100*value:.2f}%'
def pp(value): return f'{100*value:+.2f}'
def table(headers,rows):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+
        ['|'+'|'.join(map(str,row))+'|' for row in rows])
x=read(out/'analysis/summary.json'); assert x['status']=='analyzed'
cr=read(out/'analysis/independent_closed_loop_review.json'); assert cr['status']=='passed'
pr=read(out/'profiling/independent_review.json'); assert pr['status']=='passed'
closed=x['closed_loop']; latency=x['latency']; methods=closed['methods']
families={row['method_family']:row for row in latency['seed_equal_weight_summaries']}
dense_time=next(row for row in latency['primary'] if row['method']=='dense')
measurement=read(out/'profiling/measurements.json')
jobs=read(out/'slurm_accounting.json')['jobs']
assert len(jobs)==10 and all(row['state'] in ('COMPLETED','FAILED') for row in jobs)
gpu_seconds=sum(row['elapsed_seconds']*row['allocated_gpus'] for row in jobs)
assert gpu_seconds==6296
metrics={}
for budget in ('128','64'):
    for arm in ('A','B'):
        metrics[arm+budget]={key:mean(x['offline_all_budgets'][budget][s]['arms'][arm]['best']['overall'][key]['mean'] for s in seeds)
            for key in ('teacher_l1','demonstration_l1')}
overlap={b:mean(x['offline_all_budgets'][b][s]['best_hard_selection_comparison']['overall']['intersection_over_'+b]['mean'] for s in seeds) for b in ('128','64')}
primary_rows=[['dense',pct(closed['dense']['success_rate']),f"{dense_time['median']:.3f}",f"{dense_time['p95']:.3f}"]]
for name in ('A128','B128','A64','B64'):
    primary_rows.append([name,pct(methods[name]['equal_seed_mean']['mean']),
        f"{families[name]['mean_of_seed_medians_ms']:.3f}",f"{families[name]['mean_of_seed_p95_ms']:.3f}"])
primary_table=table(['方法','开发成功率','完整O2A median / ms','完整O2A p95 / ms'],primary_rows)
seed_table=table(['方法','seed17','seed23','seed41','三seed均值'],[
    [name,*[f"{methods[name]['per_seed'][s]['successes']}/30" for s in seeds],pct(methods[name]['equal_seed_mean']['mean'])]
    for name in ('A128','B128','A64','B64')])
task_rows=[]
for task in ('0','3','5'):
    for s in seeds:
        task_rows.append([task,s,*[f"{methods[name]['per_seed'][s]['by_task'][task]['successes']}/10" for name in ('A128','B128','A64','B64')]])
task_table=table(['任务','seed','A128','B128','A64','B64'],task_rows)
contrast_rows=[]
for name,c in closed['contrasts'].items():
    contrast_rows.append([name,*[pp(c['per_seed'][s]['left_minus_right']) for s in seeds],pp(c['mean']),
        f"[{pp(c['ci95_percentile'][0])}, {pp(c['ci95_percentile'][1])}]"])
contrast_table=table(['对比','seed17 Δpp','seed23 Δpp','seed41 Δpp','均值 Δpp','条件95%区间 / pp'],contrast_rows)
paired_rows=[]
for name,c in closed['contrasts'].items():
    for s in seeds:
        for task in ('all','0','3','5'):
            row=c['per_seed'][s] if task=='all' else c['per_seed'][s]['by_task'][task]
            cells=row['paired_counts']
            paired_rows.append([name,s,task,pp(row['left_minus_right']),cells['left_only'],cells['right_only'],cells['both'],cells['neither']])
paired_table=table(['左−右','seed','任务','差值 / pp','仅左成功','仅右成功','均成功','均失败'],paired_rows)
offline_rows=[]
for budget in ('128','64'):
    for s in seeds:
        t=x['offline_all_budgets'][budget][s]
        a,b=(t['arms'][arm]['best']['overall'] for arm in ('A','B'))
        ov=t['best_hard_selection_comparison']['overall']
        offline_rows.append([budget,s,f"{a['teacher_l1']['mean']:.7f}",f"{b['teacher_l1']['mean']:.7f}",
            f"{a['demonstration_l1']['mean']:.7f}",f"{b['demonstration_l1']['mean']:.7f}",
            pct(ov['intersection_over_'+budget]['mean']),pct(ov['jaccard']['mean'])])
offline_table=table(['预算','seed','A 教师L1','B 教师L1','A 示范L1','B 示范L1','交集÷预算','Jaccard'],offline_rows)
timing_rows=[]
for row in latency['primary']:
    values=[v['elapsed_ms'] for v in measurement['rows'] if v['method']==row['method']]
    timing_rows.append([row['method'],row['count'],f"{row['median']:.4f}",f"{row['p95']:.4f}",f'{max(values):.4f}'])
timing_table=table(['部署实例','实测次数','median / ms','p95 / ms','最大值 / ms'],timing_rows)
cost_table=table(['作业','阶段','seed','状态','L40 GPU秒'],[
    [j['job_id'],j['scope'],j.get('training_seed') or '—',j['state'],j['elapsed_seconds']*j['allocated_gpus']] for j in jobs])
write(out/'analysis/tables.md','\n\n'.join([
    '# Long64/128 全部开发结果',
    '30个唯一初态；三个seed重复不视为90独立初态。dense原29/30只复用一次，任务0/3/5分别10/9/10。以下所有结果保留。',
    '## 成功率与完整推理延迟',primary_table,
    '剪枝方法的median/p95为三个seed各自统计量的等权均值；dense为一个参考部署实例。',
    '## 逐seed成功率',seed_table,'## 逐任务成功率',task_table,
    '## 配对差值与条件区间',contrast_table,
    '按任务分层、完整三seed初态向量整簇bootstrap2000次（seed1517）；条件于三个任务和三个训练seed。',
    '## 完整配对四格计数',paired_table,
    '## 相同60个validation窗口的硬剪枝动作与token诊断',offline_table,
    '每任务/阶段、窗口级诊断及全部初态向量另见summary.json；该validation也用于选模，不作为独立test。',
    '## 全部13个真实部署实例',timing_table,
    '9个共同预定原始观测，每实例20次预热和20轮×9实测。全部尖峰保留，无组件计时、未来头、教师或输入缓存。',
    '## 全部新增GPU分配',cost_table,
    f'新增合计{gpu_seconds}秒＝{gpu_seconds/3600:.4f} L40 GPU小时。旧128两轮6557秒单列，Long累计{gpu_seconds+6557}秒＝{(gpu_seconds+6557)/3600:.4f}小时。内嵌计时不重复加到账单。']))
gain64=closed['contrasts']['B64_minus_A64']
cross=closed['contrasts']['B64_minus_A128']
median_reduction=1-families['B64']['mean_of_seed_medians_ms']/families['A128']['mean_of_seed_medians_ms']
p95_reduction=1-families['B64']['mean_of_seed_p95_ms']/families['A128']['mean_of_seed_p95_ms']
report=f'''# LIBERO-Long 64-token与完整推理延迟实验结论

2026-10-15。**本轮第一、二部分完成，停止新增作业；C只保留候选登记，test封存。**

未来监督在同预算下提高了这组Long开发闭环成功率：64-token的A/B三seed均值为77.78%/85.56%，B−A为+7.78个百分点，条件95%区间[+1.11,+15.56]。但B64相对A128成功率低2.22个百分点，而实测median仅降低{100*median_reduction:.2f}%；**未达到预登记的跨预算占优条件**，不能声称等效成功率下可进一步加速。

## 共同设置与实际验收

按[执行前登记](G1-F-Long64预算与延迟执行登记.md)：Long基座libero-10@95220f9、原episode划分、90/60窗口、100更新、有效batch8、seed17/23/41、h8、λ0.1。六组64-token DIE从头训练，每视角32；同seed A/B初始化、800次样本使用顺序、AdamW和门控退火相同，均按硬validation教师L1选中update100。没有搜索超参数或用128选择器直接改Top-k。

A=0.5完整教师动作L1+0.5示范动作L1；B只加0.1未来视觉摘要MSE。VLA冻结，允许梯度经过VLA进入DIE。未来头568→256→512只用于训练，使用真实8步执行动作；部署只读当前观测/指令/归一化proprio，一次硬Top-k、统一packing、一次VLA前向。

新64真实验收中，动作与未来分支到DIE的梯度范数分别0.012529和0.002905，未来头梯度0.841734；dense/硬packing动作差均0，VLA参数未变。六组训练和全部部署已通过独立审计。原150窗口缓存及时间对齐身份保持不变；h8末端位移均值约3.17cm，不能据此声称跨越语义子任务。旧128 F01未冒充新64验收。

GPU执行源码基底commit为a980996，清单SHA为192daa57…，冻结副本未修改。执行前247项CPU整合检查通过；完成后的离线JSON读取顺序修正另有18项回归通过，无新增GPU调用。

## 成功率—完整延迟

{primary_table}

剪枝行是三个seed成功率、各自median和各自p95的等权均值。dense只复用原29/30成功率参考；本轮另对同一dense部署测速，不增加成功率样本。

同预算B64较A64成功率提高7.78个百分点，median增加0.004ms、p95增加0.463ms；B128较A128成功率提高4.44个百分点，median降低0.144ms、p95增加3.941ms。支持这组开发面板上未来辅助监督的闭环增益，但不能把延迟数值接近说成已证明等价，也不构成严格Pareto支配。

B64相对A128的median/p95分别降低{100*median_reduction:.2f}%/{100*p95_reduction:.2f}%，成功率差−2.22个百分点，条件95%区间[−11.11,+6.67]。更强压缩恢复了部分成功率，但目前不足以支持“B64优于A128的整体折中”。相比dense，B64的median实测加速比为{dense_time['median']/families['B64']['mean_of_seed_medians_ms']:.3f}×，同时成功率低11.11个百分点；不能省略这项代价。

## 全部seed和任务

{seed_table}

{task_table}

任务0为汤罐与番茄酱放入篮子；任务3为碗放入底层抽屉并关上；任务5为书放入收纳架后隔间。dense对应10/10、9/10、10/10。64预算的B增益主要来自任务3（+1/+1/+3次），另有seed23任务0增加2次；不是每个初态都改善，seed17存在2个仅A成功的初态。

统计以原30个唯一初态为簇、任务分层、保持三seed完整向量bootstrap2000次（seed1517），不把90个seed×初态单元当作独立初态。B64−A64逐seed为+3.33/+10/+10个百分点。区间仅条件于固定三个任务与三个seed，不是任务总体或训练seed总体结论。B64−A128区间跨零不等于两者等效，也不能证明此前Spatial负结果由任务难度造成。完整配对四格计数、其他跨预算差值及逐任务均值见[全部数值表](../results/g1_future_long_k64_v1/analysis/tables.md)。

## 动作误差与token诊断

{offline_table}

64预算的平均教师L1为A {metrics['A64']['teacher_l1']:.7f}、B {metrics['B64']['teacher_l1']:.7f}，平均示范L1为A {metrics['A64']['demonstration_l1']:.7f}、B {metrics['B64']['demonstration_l1']:.7f}；B在seed17/23较差、seed41略好，整体未改善。64-token A/B集合交集平均{pct(overlap['64'])}，128预算为{pct(overlap['128'])}；均在同一60个validation观测比较，不混用不同闭环轨迹的观测。

未来MSE约0.371–0.373，视觉读出置零后约0.972–0.978，实际动作倒序影响很小。这仅是训练头诊断：不能当作新的未来预测成果，也未隔离未来目标与一般视觉辅助训练的作用。动作误差来自记录的归一化8×7动作L1；本地审计核对记录与选模一致性，未独立重算服务器未回存的原始动作张量。

## 测速与成本范围

原开发任务0/state0采0/184/336步，任务3/state3采0/104/192步，任务5/state2采0/72/128步。三个复现dense轨迹共95个策略查询的原始观测SHA与动作均和历史记录一致，9/9预定观测完整；这3条采集回放不加入成功率分母。

全部13实例在同一张无其他计算进程竞争的L40上完成：每实例20次预热、20轮×9观测，260次预热+2340次实测。顺序按seed1017预定并循环平衡。边界为原始模拟器数组和指令就绪，到CPU可执行8×7动作就绪，包含预处理、视觉编码、DIE、packing、VLA和后处理；模型加载、磁盘、环境步进、日志及遥测不计入单次延迟，仍计入总GPU分配成本。未来头、教师、语言/视觉缓存均未参与部署。

全部尖峰保留；例如B128_seed17的p95为101.964ms、最大365.076ms，未截尾或择优重跑。13实例、每观测分布与原始调用均已回存，见[完整计时](../results/g1_future_long_k64_v1/profiling/summary.json)。

| 新增阶段 | L40 GPU秒 |
|---|---:|
| 新64工程验收 | 314 |
| 9观测采集回放 | 359 |
| 六组训练与选模 | 2009 |
| 180条闭环 | 3054 |
| 完整测速成功运行 | 505 |
| 测速首次CUDA初始化失败 | 55 |
| **新增合计** | **6296＝1.7489小时** |

六组训练与选模为0.5581小时；旧128两轮6557秒单列，Long累计12853秒＝3.5703小时。按Slurm分配墙钟×GPU数计一次，包含加载、校验、I/O及失败，不叠加程序内部计时。

首次测速3001742在CUDA首次初始化失败，0策略调用，55秒与日志保留；仅按事先追加的基础设施登记换节点重试3001817，相同源码/权重/观测/顺序，2600调用全部完成。离线读取因JSON键排序造成列表/浮点归约顺序差异，经显式observation_ids恢复后与原summary全字段精确一致；原始4个测速产物未改，见[修复记录](../results/g1_future_long_k64_v1/profile_readback_fix.json)。

## 结论与停止

同预算未来辅助监督有正向开发闭环证据，64-token下增益点估计较大；更强压缩的总体折中优势仍未成立。当前结果既不支持继续扩规模或搜索，也不足以解释辅助监督的机制。

C保持[结果前候选登记](G1-F-Long当前摘要对照候选登记.md)：同64预算、三seed、90/60窗口、100更新、batch8、相同568→256→512训练头与实际8步动作输入、λ0.1，仅把detach目标从t+8未来摘要改为当前完整观测摘要。继续讨论需同预算正向配对闭环证据并结合median/p95判断；严格B64对A128占优条件本轮未通过。不新增事后阈值；本轮不运行C，无论结果均须另获明确执行授权。

180条新闭环、旧180条A/B与30条dense参考、全部12选择器身份、30初态整簇统计和完整GPU账单均通过[独立闭环审计](../results/g1_future_long_k64_v1/analysis/independent_closed_loop_review.json)；2600次测速通过[独立测速审计](../results/g1_future_long_k64_v1/profiling/independent_review.json)。权重/checkpoint只在服务器`/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_long_k64_v1/seed{{17,23,41}}/{{A,B}}/best.pt`，非权重结果回存本项目。保留全部旧实验和失败记录，test继续封存，自动化保持PAUSED。本轮到此停止。
'''
write(r/'docs/G1-F-Long64预算与延迟实验结论.md',report)
scientific={
    'status':'completed_no_automatic_expansion','stage':'G1-F_Long64_and_full_O2A',
    'report':'docs/G1-F-Long64预算与延迟实验结论.md',
    'same_budget_development_success_evidence':'positive_conditional_for64_and128',
    'strict_B64_over_A128_tradeoff':False,'B64_minus_A64':gain64,'B64_minus_A128':cross,
    'new_gpu_seconds':gpu_seconds,'new_gpu_hours':gpu_seconds/3600,'historical_Long_gpu_seconds':6557,
    'C_execution_authorized':False,'C_executed':False,'test_opened':False,
    'raw_data_modified':False,'weights_local':False,
    'limits':['30 unique fixed development states,3 tasks,3 training seeds; no seed/task population claim',
       'No equivalence claim from nonsignificance or near latency; no Spatial difficulty causal claim',
       'Auxiliary target mechanism remains unidentified; no automatic C,scale,seed,task,budget or hyperparameter expansion'],
    'evidence_sha256':{str(p.relative_to(r)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in
       (out/'analysis/summary.json',out/'analysis/independent_closed_loop_review.json',out/'profiling/independent_review.json',out/'slurm_accounting.json')}
}
write(out/'scientific_review.json',json.dumps(scientific,ensure_ascii=False,indent=2))
os.environ['MPLCONFIGDIR']=str(r/'.local/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10.8,4.5),sharey=True)
style={'dense':('#333333','o'),'A128':('#bc5b21','s'),'B128':('#1b778c','s'),'A64':('#bc5b21','^'),'B64':('#1b778c','^')}
for ax,metric in zip(axes,('median','p95')):
    for name in ('dense','A128','B128','A64','B64'):
        xx=dense_time[metric] if name=='dense' else families[name]['mean_of_seed_'+('medians_ms' if metric=='median' else 'p95_ms')]
        yy=100*(closed['dense']['success_rate'] if name=='dense' else methods[name]['equal_seed_mean']['mean'])
        color,marker=style[name]
        ax.scatter([xx],[yy],s=76,color=color,marker=marker,zorder=3)
        ax.annotate(name,(xx,yy),xytext=(-7,-15) if name=='dense' else (6,4),textcoords='offset points',fontsize=10,
            ha='right' if name=='dense' else 'left')
    ax.set_xlabel(f'Full O2A {metric} (ms / action chunk8)')
    ax.set_xlim(78,132);ax.set_ylim(74,101);ax.grid(alpha=.2)
axes[0].set_ylabel('Development success rate (%)')
fig.suptitle('LIBERO-Long: measured success–latency tradeoff',fontsize=13)
fig.text(.5,.015,'30 unique development states; all3 training seeds averaged. Dense: one reused success reference. No equivalence claim.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.05,1,.95))
for suffix in ('png','pdf','svg'):
    fig.savefig(out/'analysis'/('success_latency_tradeoff.'+suffix),dpi=180)
plt.close(fig)
print(json.dumps({'report_written':True,'all_tables_written':True,'scientific_status':scientific['status'],'GPU_seconds':gpu_seconds}))
