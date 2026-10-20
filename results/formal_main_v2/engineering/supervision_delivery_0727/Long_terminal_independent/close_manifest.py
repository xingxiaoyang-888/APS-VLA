from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
JOBS={'3047152':(256,41,3130),'3047156':(64,17,3025),'3047163':(64,23,3038)}
PRIOR=[('3043709',128,23,'3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325'),('3045322',128,41,'d27e9bbf12e435ba3fd1341757b451e666b77528cd5fede6cb07ab19eb790699'),('3046779',256,17,'968b0e8b09577ce93320a02c1c69f5b37f6bc0256004962aaaa8a62e55789919'),('3046798',256,23,'251788eb33c35f2cd17e613d4bb4842cb1aa6ba6eb14937578fb1675a3d139de')]
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+b'\n'
 with p.open('xb') as f:f.write(b)
 return ref(p)
reports={};children=[];panels=set();semantics=set();environments=[]
for jid,(budget,seed,seconds) in JOBS.items():
 child=D/('job'+jid);mf=json.loads((child/'manifest.json').read_bytes());assert mf['status']=='frozen'
 for row in mf['files']:assert ref(R/row['path'])==row
 p=child/'independent_review.json';v=json.loads(p.read_bytes());assert ref(p)==mf['independent_review']
 assert v['status']=='passed' and v['scientific_complete'] and v['job_id']==jid and v['stage']=='development'
 assert v['method_ids']==[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'] and v['completed_trials']==v['expected_trials']==200 and v['unique_initial_states']==100
 assert v['cost']['current_GPU_seconds']==v['cost']['all_attempt_GPU_seconds']==seconds and v['cost']['allocations']==1
 assert v['final_release'] is False and v['O2A_latency_verified'] is False and v['legacy_terminal_trials_reused']==0
 cp=json.loads((R/v['cross_seed_panel_identity']['path']).read_bytes());panels.add(cp['same_exact_development_panel']['sha256']);semantics.add(v['action_semantics_sha256'])
 rp=R/v['root_review']['path'];assert ref(rp)['sha256']==v['root_review']['sha256'];root=json.loads(rp.read_bytes());environments.append(root['reconstructed_summary']['provenance']['manifest']['environment'])
 reports[jid]={'review':ref(p),'budget':budget,'seed':seed,'successes':v['successes'],'per_task':v['per_task'],'per_task_B_minus_A_success_rate':v['per_task_B_minus_A_success_rate'],'paired_outcomes':v['paired_outcomes'],'B_minus_A_success_rate':v['B_minus_A_success_rate'],'GPU_seconds':seconds,'action_checks':v['action_checks'],'initial_observation_token_overlap_mean':v['initial_observation_token_overlap_mean']}
 children.append(ref(child/'manifest.json'))
assert len(panels)==len(semantics)==1 and all(x==environments[0] for x in environments)
prior=[]
for jid,budget,seed,pin in PRIOR:
 p=R/('results/formal_main_v2/downstream_reviews/'+jid+'.json');q=ref(p);assert q['sha256']==pin
 v=json.loads(p.read_bytes());assert v['status']=='passed' and v['scientific_complete'] and v['stage']=='development'
 assert v['action_semantics_sha256'] in semantics and v['raw_invocation_job_ids']==[jid] and v['historical_transition'] is None
 m=v['reconstructed_summary']['provenance']['manifest'];assert m['development_panel_sha256'] in panels and m['environment']==environments[0]
 succ={k:x['successes'] for k,x in v['reconstructed_summary']['methods'].items()}
 if budget==128:assert succ=={f'A128_seed{seed}':95,f'B128_seed{seed}':92}
 prior.append({'root_review':q,'budget':budget,'seed':seed,'successes_retained':succ,'B_minus_A_success_rate':(succ[f'B{budget}_seed{seed}']-succ[f'A{budget}_seed{seed}'])/100,'prior_acceptance_inherited_not_repeated':True})
comparison=save('shared_development_panel_all_seven_jobs.json',{'status':'passed','current_jobs':list(JOBS),'prior_matched_runtime_jobs':prior,'current_trials':600,'prior_trials':800,'unique_initial_states_across_all_seven_jobs':100,'same_development_panel_sha256':next(iter(panels)),'same_environment':environments[0],'same_action_semantics_sha256':next(iter(semantics)),'not_independent_across_budget_or_seed':True,'old1212_action_trials_merged':False,'combined_budget_effect_estimate':False,'final_release':False})
sp=D/'Long256_three_seed_statistics.json';sr=ref(sp);assert sr['sha256']=='3ad37e5a918b92d7c9e8d5d0ea538584fe548a24bd0c9a03fd97c6ce28f69abb'
st=json.loads(sp.read_bytes());assert st['status']=='passed' and st['seeds']==[17,23,41] and st['total_trials']==600 and st['unique_initial_states']==100
assert st['paired_bootstrap']['configuration']['bootstrap_seed']==20261016 and st['paired_bootstrap']['configuration']['bootstrap_repeats']==10000
for x in st['evidence']+[st['paired_states'],st['bootstrap_draws']]:assert ref(R/x['path'])==x
summary=save('summary.json',{'schema':'formal_main_v2','kind':'independent_Long_three_development_jobs_summary','status':'passed','utc':datetime.now(timezone.utc).isoformat(),'jobs':reports,'completed_trials':600,'unique_initial_states':100,'same_initial_states_across_budget_and_seeds':True,'sum_actual_current_GPU_seconds':9193,'sum_actual_current_GPU_hours':9193/3600,'shared_development_panel_check':comparison,'Long256_three_seed_statistics':sr,'Long256_statistics_scope':{'includes_prior_completed_jobs':['3046779','3046798'],'includes_current_job':'3047152','mean':st['mean_over_seeds'],'seed_std_ddof1':st['seed_std_ddof1'],'CI95_B_minus_A':st['paired_bootstrap']['CI95_B_minus_A'],'descriptive_development_only':True},'Long64_complete_seeds':[17,23],'Long64_seed41_included':False,'Long64_three_seed_statistic_computed':False,'prior_allocations_added_to_this_round_cost':False,'legacy_action_trials_included':0,'final_release':False,'O2A_latency_verified':False,'scientific_equivalence_or_significance_claim':False,'failure_policy':'all attempt sources and audit logs preserved; no new scientific or GPU work'})
lines=['# Long 开发终态独立审计0727','', '3个真实终态的原始ledger、原consumer重建、Slurm分配与173源镜像均通过。新增600条试验，共用100个唯一开发初态。','', '|预算|seed|A成功/100|B成功/100|B−A百分点|初观测token重合率|GPU秒|','|---|---|---:|---:|---:|---:|---:|']
for jid,v in reports.items():
 b=v['budget'];s=v['seed'];lines.append(f"|{b}|{s}|{v['successes'][f'A{b}_seed{s}']}|{v['successes'][f'B{b}_seed{s}']}|{100*v['B_minus_A_success_rate']:+.1f}|{v['initial_observation_token_overlap_mean']:.6f}|{v['GPU_seconds']}|")
lines+=['','本轮新增成本9193 GPU秒（2.553611小时），只计3次实际Slurm分配；不重复累加嵌套耗时。','', 'Long256三seed开发均值：A92.667%、B95.000%，B−A+2.333pp，95%配对bootstrap区间[-1.000,+6.000]pp。区间按任务内初态簇携完整三seed、seed20261016、10000次生成；不能据此断言稳定收益或等效。','Long64仅17/23已齐，未生成三seed统计；Long128 seed23/41的95/92负结果继续保留。','未开放最终初态；不混入旧动作语义1212条，不作完整O2A或成功率—速度结论。','']
p=D/'README.md'
with p.open('x') as f:f.write('\n'.join(lines))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file()]
manifest=save('manifest.json',{'schema':'formal_main_v2','kind':'independent_Long_development_0727_archive','status':'frozen','root':str(D),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'summary':summary,'child_manifests':children,'no_weights_or_sealed_values':True,'no_raw_trial_duplicate':True})
print(json.dumps({'summary':summary,'manifest':manifest,'files':len(files),'GPU_seconds':9193,'trials':600,'unique_initial_states':100,'Long256_statistics':sr}))
