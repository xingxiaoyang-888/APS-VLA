"""Close only the explicitly authorized completed Long64 round; never submit jobs."""
from pathlib import Path
import datetime, hashlib, json

r=Path('F:/CTI-VLA'); out=r/'results/g1_future_long_k64_v1'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,value): p.write_text(value.rstrip()+'\n',encoding='utf-8',newline='\n')
def dump(p,value): write(p,json.dumps(value,ensure_ascii=False,indent=2))
x=read(out/'analysis/summary.json'); review=read(out/'scientific_review.json')
assert x['status']=='analyzed' and review['status']=='completed_no_automatic_expansion'
assert read(out/'analysis/independent_closed_loop_review.json')['status']=='passed'
assert read(out/'profiling/independent_review.json')['status']=='passed'
state_path=r/'results/experiment_supervisor/state.json'; state=read(state_path)
assert state['pending_submission'] is None and state['automation_status']=='PAUSED'
jobs=[j for j in state['registered_jobs'] if j.get('experiment')=='g1_future_long_k64_v1']
assert len(jobs)==10 and all(j['status'] in ('COMPLETED','FAILED') for j in jobs)
assert sum(j['elapsed_seconds'] for j in jobs)==6296
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
state.update(status='completed',stage='G1_F_Long_k64_and_Long_full_latency_completed',
    last_supervision_utc=now,supervision_status='completed_stopped_after_authorized_round',
    current_work='Completed6 fresh64 training arms,180 paired development trials and2600 full Long O2A calls; all evidence independently audited and retained. No automatic expansion.',
    next_allowed_action='Report this completed bounded round. No new task,seed,training,budget,ablation,C or test without separate explicit user authorization.')
state['current_round_cost'].update(final=True,registered_jobs=10,allocated_gpu_seconds=6296,
    allocated_gpu_hours=6296/3600,training_gpu_seconds=2009,closed_loop_gpu_seconds=3054,
    acceptance_gpu_seconds=314,collection_gpu_seconds=359,profiling_gpu_seconds=560,
    failed_profile_gpu_seconds=55,historical_Long_gpu_seconds_excluded=6557)
progress=state['last_observed_G1_F_Long_k64_progress']
progress.update(closed_loop_trials=180,profile_job='3001817',profile_policy_calls=2600,
    profile_measured_calls=2340,profile_warmup_calls=260,profile_status='completed_independently_audited',
    closed_loop_policy_errors=0,closed_loop_infrastructure_errors=0,
    closed_loop_independent_review='results/g1_future_long_k64_v1/analysis/independent_closed_loop_review.json',
    profiling_independent_review='results/g1_future_long_k64_v1/profiling/independent_review.json',
    scientific_review='results/g1_future_long_k64_v1/scientific_review.json',
    report='docs/G1-F-Long64预算与延迟实验结论.md',scientific_status='same_budget_positive_development_success_but_no_strict_B64_over_A128_tradeoff',
    mean_success_rates={k:v['equal_seed_mean']['mean'] for k,v in x['closed_loop']['methods'].items()},
    new64_successes_by_seed={s:{a:x['closed_loop']['methods'][a+'64']['per_seed'][s]['successes'] for a in ('A','B')} for s in ('17','23','41')},
    latency_seed_equal_weight=x['latency']['seed_equal_weight_summaries'],
    B64_minus_A64={k:x['closed_loop']['contrasts']['B64_minus_A64'][k] for k in ('mean','ci95_percentile','unique_initial_states')},
    B64_minus_A128={k:x['closed_loop']['contrasts']['B64_minus_A128'][k] for k in ('mean','ci95_percentile','unique_initial_states')},
    strict_B64_over_A128=False,test_opened=False,C_run=False)
gate={'stage':'G1-F-Long64-and-full-O2A','status':'completed_no_automatic_expansion',
    'report':'results/g1_future_long_k64_v1/scientific_review.json',
    'reason':'B64 beats A64 by7.78pp on fixed development states, but B64 vs A128 is-2.22pp with only3.28% lower median latency; strict cross-budget improvement not established.',
    'scope':'30 unique development states,3 tasks,all3 training seeds. C remains a proposal only.', 'test_opened':False}
assert not any(g['stage']==gate['stage'] for g in state['verified_gates'])
state['verified_gates'].append(gate)
state['long_k64_source_snapshot']={k:v for k,v in read(out/'source_g1_future_long_k64_v1.json').items() if k!='files'}
dump(state_path,state)
plan=r/'docs/完整实验计划.md'; text=plan.read_text(encoding='utf-8')
start=text.index('## 当前执行补充：Long 64-token与完整延迟（2026-10-15）')
end=text.index('## 当前执行补充：Long seed23/41（2026-10-15）')
section='''## 当前执行补充：Long 64-token与完整延迟（2026-10-15）

用户另行授权[本轮登记](G1-F-Long64预算与延迟执行登记.md)：Long原划分、90/60窗口、100更新、batch8、h8、λ0.1不变，seed17/23/41从头训练总64-token的A/B六组；先通过新预算工程验收，再完成原30开发初态180条闭环，身份匹配后复用dense与128结果。新增9个共同Long原始观测、13实例完整O2A计时；C仅登记不运行，test封存。

**执行结果：第一、二部分全部完成，停止新增作业。** 六组各100更新、全部选update100，64预算F01、训练、180闭环与2600测速调用均通过独立审计。A64/B64逐seed成功数25/26、21/24、24/27（各30）；均值77.78%/85.56%，差+7.78个百分点，30初态整簇条件区间[+1.11,+15.56]。完整O2A median/p95：dense122.839/124.875ms，A12884.452/87.720，B12884.307/91.662，A6481.679/83.959，B6481.683/84.421。B64相对A128成功率低2.22个百分点、median仅降低3.28%，未达到预登记跨预算占优条件；不把跨零视为等价。

新增6296 L40 GPU秒＝1.7489小时，含首次测速CUDA初始化失败55秒及唯一同协议重试505秒；没有结果择优重跑。全部非权重产物回存，权重留服务器；C只提出[具体候选与继续条件](G1-F-Long当前摘要对照候选登记.md)，本轮未运行，不自动扩大。见[完整结论](G1-F-Long64预算与延迟实验结论.md)及[全部数值表](../results/g1_future_long_k64_v1/analysis/tables.md)。此前各轮停止记录保留为当时事实。

'''
write(plan,text[:start]+section+text[end:])
progress_path=r/'docs/实验进度.md'; text=progress_path.read_text(encoding='utf-8')
lines=text.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| G1-F Long 64-token与完整延迟 |'):
        lines[i]='| G1-F Long 64-token与完整延迟 | **完成，本轮停止** | 六组各100更新、180/180闭环、2600完整O2A调用及独立审计完成。A64/B64均值77.78%/85.56%，+7.78个百分点；B64对A128−2.22个百分点、median仅快3.28%，未证跨预算占优。新增6296秒＝1.7489 L40小时，含失败55秒；C未运行、test封存。见[结论](G1-F-Long64预算与延迟实验结论.md)。 |'
text='\n'.join(lines)
text=text.replace('旧128补充已完成；新64与Long延迟另获本轮授权，正在按新登记推进。','旧128补充及本轮64与Long延迟均已完成。新轮6296秒，Long累计12853秒＝3.5703小时；已停止新增实验。')
text=text.replace('尚无 CTI-VLA 正式闭环成功率或加速结果。开发验收数字只用于确认链路正确，不能用作论文主结果。','当前结果均为有界开发集实验，尚无封存test的正式泛化结果；不能将这些开发数字直接当作论文盲测主结果。')
write(progress_path,text)
c=r/'docs/G1-F-Long当前摘要对照候选登记.md'
text=c.read_text(encoding='utf-8')
assert '## 当前轮完成后的状态' not in text
write(c,text+'''

## 当前轮完成后的状态（2026-10-15）

64预算B−A为+7.78个百分点，条件95%区间[+1.11,+15.56]；B的实测median/p95分别比A多0.004/0.463ms。128预算也有正向开发成功率证据，但B的p95较A高3.941ms。B64相对A128成功率−2.22个百分点、median仅快3.28%，严格跨预算占优条件未通过。延迟接近未证明等价，机制尚未区分。

本轮仅把C保留为可讨论的机制对照，不据此发起作业。以上预先固定的设置与继续判据不变；若后续考虑执行，先由用户结合真实成功率与median/p95决定是否另行授权，不能自动扩大或事后搜索阈值。C已执行次数为0，test仍封存。
''')
report=r/'docs/G1-F-Long64预算与延迟实验结论.md'
text=report.read_text(encoding='utf-8')
text=text.replace('## 全部seed和任务','[成功率—延迟图](../results/g1_future_long_k64_v1/analysis/success_latency_tradeoff.png)同时展示median与p95。\n\n## 全部seed和任务')
write(report,text)
audit=out/'audit_code'
for name in ('record_long64_readback_fix.py','write_long64_results.py','finish_long64_round.py'):
    target=audit/name
    assert not target.exists()
    target.write_bytes((r/'.local'/name).read_bytes())
old=read(audit/'manifest.json')
for name,digest in old['files'].items():
    assert hashlib.sha256((audit/name).read_bytes()).hexdigest()==digest, name
old['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(audit.glob('*.py'))}
old['final_source_note']='review_long_k64_closed_loop_final.py uses the immutable supervisor_state_at_review.json; earlier helper versions retained. Post-measurement readback fix is CPU-only and production snapshot remains immutable.'
dump(audit/'manifest.json',old)
print(json.dumps({'status':state['status'],'stage':state['stage'],'all_jobs_terminal':True,'GPU_seconds':6296,'automatic_expansion':False,'audit_sources':len(old['files'])}))
