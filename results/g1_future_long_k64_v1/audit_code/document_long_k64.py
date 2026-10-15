from pathlib import Path
import datetime, hashlib, json

r=Path('F:/CTI-VLA')
p=r/'configs/experiments/g1_future_long_k64_v1.json'
j=json.loads(p.read_text(encoding='utf-8'))
v=j['profiling']
v.update(version='long-o2a-13-deployments-v1', warmup_calls=20, repeats=20,
         component_repeats=0, task_control_steps={str(x['task_id']):x['capture_steps'] for x in v['states']},
         source_dense_trials_sha256=j['frozen_evidence_sha256']['results/g1_future_long_v1/closed_loop/trials.jsonl'],
         method_names=[x['id'] for x in v['deployment_instances']],max_pipeline_calls=2600)
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
receipt=r/'results/g1_future_long_k64_v1/registration_receipt.json'
q=json.loads(receipt.read_text(encoding='utf-8'))
q.update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
         finalized_before_jobs_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         implementation_aliases_added_before_any_new_results=True)
receipt.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
doc='''# LIBERO-Long 64-token与完整延迟执行登记

2026-10-15。用户授权本轮第一、二部分；本登记在看过128-token三seed结果后制定，在任何64-token训练、闭环及Long专门测速之前固定。研究问题是未来监督能否改善视觉剪枝的成功率—完整推理延迟折中。test封存，C不运行。

## 固定训练

机器可读协议：[总登记](../configs/experiments/g1_future_long_k64_v1.json)。Long基座仍为libero-10@95220f9，原episode划分、90/60窗口、100次更新、有效batch8；seed17/23/41各从头训练A/B，共6组。只把每视角预算从64降为32（总64），不得复用128选择器冒充新训练。

A=0.5完整教师动作L1+0.5示范动作L1；B=A+0.1未来摘要MSE。未来跨度8个实际执行动作、表征投影seed917、568→256→512训练头不变。同seed A/B的DIE初始化、数据顺序、AdamW设置、cosine门控退火及选模相同。选模只看update0/25/50/75/100的硬剪枝validation教师L1，同值取最早。

VLA冻结，梯度经过VLA到DIE；当前特征、教师动作和未来目标detach。实际动作仅给训练头；部署只读当前图像、语言和归一化proprio，移除未来头，一次硬Top-k、统一packing、一次VLA前向。

## 工程闸门与闭环

复核原F00及150窗口缓存的真实SHA与生产者身份；不重建或改名旧证据。先以新64预算完成真实VLA梯度、零参数更新、输入隔离、硬32/view数量/位置/动作切片及部署一致性验收。原128 F01不能替代此验收；新64工程证据可在相同代码、基座及配置身份下显式共享给三个seed。

验收后训练，再在原固定任务0/3/5各10初态上新增180条A/B闭环。环境seed0、运行seed17、wait10、chunk8、max520不变。原dense与128结果需通过基座、依赖、源文件、输入输出和首观测身份核验才复用；训练seed不改变环境seed。保留所有失败与异常尝试，不择优重跑。

## Long完整推理计时

从每个固定任务中原开发source index最小的状态，复现原dense轨迹并采集9个原始观测：任务0/state0在0/184/336步，任务3/state3在0/104/192步，任务5/state2在0/72/128步。位置由旧dense轨迹长度的0/50%/90%向下取8动作边界决定，未按新方法选择。首观测SHA与原dense一致。缺失帧照实登记，不复制末帧；若未覆盖三个任务则停止计时并报告。

同一张无其他进程竞争的L40，单一base，13个部署实例：dense及A128/B128/A64/B64各seed17/23/41。每实例20次预热；20轮，每轮在全部共同观测上测量，实例顺序由seed1017预先排列并循环平衡，方法共享每轮观测顺序。最多2600次pipeline调用，无额外组件测量、无自动重复测速。

计时边界是原始模拟器数组与指令就绪，到CPU可执行8×7动作chunk就绪；CUDA计时前后同步。包含图像预处理、视觉编码、DIE、packing、VLA和动作后处理。环境步进/磁盘读取/模型启动不计入单次延迟，但其GPU分配时间计入总成本。部署禁用未来头、教师和特征/语言/选择缓存。128实例使用原冻结部署代码并核对共享模型算子，不能放宽旧receipt验证。

报告全部原始调用、每实例/seed/观测及方法的median/p95、尖峰、失败；同时给三seed均值和合并分布。少token不是加速证据，闭环墙钟不替代完整O2A计时，不套用Spatial数字。

## 汇总与继续条件

汇总dense、A128、B128、A64、B64的全部seed/任务成功率、A/B配对四格计数、动作误差、同观测token交集比例与Jaccard。统计以30个唯一初态为簇，按任务分层，携带全部seed/预算完整向量bootstrap2000次（seed1517）；结果是固定面板/seed条件下描述区间，不能把90次seed×初态当独立状态或把不显著视为等价。

主要比较B64−A64、B128−A128及B64−A128。相同预算的正向支持要求配对均值>0、条件95%区间下界>0，并结合实测延迟判断；严格B64相对A128折中占优要求上述成功率条件成立，且B64实测median和p95均更低。边界或不确定结果保留，不自动扩大，也不把条件区间解释为任务总体结论。

所有新GPU分配（含验收、缓存核验、训练/选模、采集、闭环、测速及失败）按Slurm墙钟×GPU数计一次；旧128轮6557秒单独列出。权重/checkpoint只在服务器，非权重产物和校验收据回存。root统一登记、提交、回收，只管理监督清单内本项目作业。

完成本轮后汇报停止。C只有[候选登记](G1-F-Long当前摘要对照候选登记.md)，是否值得继续由真实折中结果判断；执行仍需用户另行授权。
'''
(r/'docs/G1-F-Long64预算与延迟执行登记.md').write_text(doc,encoding='utf-8',newline='\n')
candidate='''# Long 当前摘要辅助监督：候选登记（未授权运行）

2026-10-15，在64-token结果前固定候选。当前状态：仅提案，不提交作业。研究问题仍是剪枝控制信息，非图像生成或独立未来预测。

若第一、二部分支持剪枝成功率—实测延迟折中改善，可向用户提出固定64-token的C对照：同Long基座、原episode和90/60窗口、seed17/23/41、100更新、batch8、每视角32、λ=0.1。C继承B的DIE、训练期568→256→512预测头、读出和真实执行动作输入、门控退火、优化器、数据顺序及硬validation教师L1选模；唯一改变是目标由t+8未来摘要换为t时刻完整当前观测的冻结摘要。当前目标仍detach，使用相同冻结编码器、空间摘要投影seed917及归一化；不得用门控后特征作为自回归目标。

若另获授权，从与对应B完全相同的新初始化训练C；不按已看成功率选种子或更新，不复用B训练出的DIE。训练期仍输入原8步实际执行动作以严格匹配B（该输入在C任务中可能冗余，须如实说明）；无额外损失或预测头，未来信息仍不得进入选择器/部署。部署移除训练头，统一64预算硬剪枝与完整计时。

只在原30开发初态对C与已完成A/B配对，不改任务/测试集或搜索超参。报告全部seed、动作误差、集合差异和全部成本；同初态跨seed整簇分析。若C与B相近或区间跨零，只能说明机制尚未区分，不能宣布未来无效或二者等价；若B相对C改善且成功率—延迟结果支持，才构成未来目标比一般视觉辅助更有价值的开发证据。

提交提案的继续条件：当前轮至少一个预算有配对成功率正向支持，且结合实测median/p95支持改善折中；严格跨预算占优按主登记判断。若当前轮不支持折中改善，记录限制并停止，不运行C、不堆模块、不调参。无论是否满足条件，本轮均不自动运行C。
'''
(r/'docs/G1-F-Long当前摘要对照候选登记.md').write_text(candidate,encoding='utf-8',newline='\n')
p=r/'docs/完整实验计划.md'; t=p.read_text(encoding='utf-8')
section='''## 当前执行补充：Long 64-token与完整延迟（2026-10-15）

用户另行授权[本轮登记](G1-F-Long64预算与延迟执行登记.md)：保持Long原划分、90/60窗口、100更新、batch8、h8、λ0.1，seed17/23/41从头训练总64-token的A/B六组。先做新预算工程验收，再做原30开发初态180条A/B闭环；身份不变时复用dense与128结果。新增9个预定Long原始开发观测、13实例完整O2A计时，所有seed/失败/成本保留。当前仅已登记，尚无新GPU结果。C只提交候选方案与继续条件，不运行；第一、二部分完成即汇报停止，test封存。此前各轮停止记录保留为当时事实。

'''
assert '## 当前执行补充：Long 64-token与完整延迟' not in t
t=t.replace('# CTI-VLA 完整实验计划\n\n','# CTI-VLA 完整实验计划\n\n'+section,1);p.write_text(t,encoding='utf-8',newline='\n')
p=r/'docs/实验进度.md';t=p.read_text(encoding='utf-8')
row='| G1-F Long 64-token与完整延迟 | 已登记，工程接入中 | 6组新训练、180条开发闭环、Long 13部署实例完整计时；先新64预算验收，尚无新GPU作业或结果。C仅候选登记，test封存。见[执行登记](G1-F-Long64预算与延迟执行登记.md) |\n'
t=t.replace('| 旧 G2/G3 标注与训练 |',row+'| 旧 G2/G3 标注与训练 |',1)
t=t.replace('本轮补充已完成并停止，不自动扩大；test继续封存，自动化仍PAUSED。','旧128补充已完成；新64与Long延迟另获本轮授权，正在按新登记推进。test继续封存，自动化仍PAUSED。')
p.write_text(t,encoding='utf-8',newline='\n')
print('Registration and documents finalized before new GPU jobs')
