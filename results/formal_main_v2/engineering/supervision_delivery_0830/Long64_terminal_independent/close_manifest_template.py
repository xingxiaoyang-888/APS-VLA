from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;J=D/'job3047443'
PRIOR=[('3043709',128,23,'3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325'),('3045322',128,41,'d27e9bbf12e435ba3fd1341757b451e666b77528cd5fede6cb07ab19eb790699'),('3046779',256,17,'968b0e8b09577ce93320a02c1c69f5b37f6bc0256004962aaaa8a62e55789919'),('3046798',256,23,'251788eb33c35f2cd17e613d4bb4842cb1aa6ba6eb14937578fb1675a3d139de'),('3047152',256,41,'07c46b463db75271d7bdc6ecc43b43f9a20e4c88a351a88d16a735daf39ad03b'),('3047156',64,17,'9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190'),('3047163',64,23,'5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc')]
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p,pin=None):
 q=ref(p);assert pin is None or q['sha256']==pin;return json.loads(p.read_bytes()),q
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+b'\n'
 with p.open('xb') as f:f.write(b)
 return ref(p)
mf,mfr=read(J/'manifest.json')
assert mf['status']=='frozen'
for row in mf['files']:assert ref(R/row['path'])==row
ind,ir=read(J/'independent_review.json','__INDEPENDENT_SHA__');assert ir==mf['independent_review']
assert ind['status']=='passed' and ind['scientific_complete'] and ind['job_id']=='3047443' and ind['method_ids']==['A64_seed41','B64_seed41']
assert ind['completed_trials']==ind['expected_trials']==200 and ind['unique_initial_states']==100
assert ind['cost']['current_GPU_seconds']==ind['cost']['all_attempt_GPU_seconds']==3039 and ind['cost']['allocations']==1
assert ind['final_release'] is False and ind['O2A_latency_verified'] is False and ind['legacy_terminal_trials_reused']==0
root,rr=read(R/ind['root_review']['path'],ind['root_review']['sha256']);m=root['reconstructed_summary']['provenance']['manifest'];panel=m['development_panel_sha256'];semantics=root['action_semantics_sha256'];environment=m['environment']
prior=[]
for jid,budget,seed,pin in PRIOR:
 v,q=read(R/('results/formal_main_v2/downstream_reviews/'+jid+'.json'),pin)
 assert v['status']=='passed' and v['scientific_complete'] and v['stage']=='development' and v['suite']=='libero_10'
 assert v['action_semantics_sha256']==semantics and v['raw_invocation_job_ids']==[jid] and v['historical_transition'] is None
 mm=v['reconstructed_summary']['provenance']['manifest'];assert mm['development_panel_sha256']==panel and mm['environment']==environment
 succ={k:x['successes'] for k,x in v['reconstructed_summary']['methods'].items()}
 if budget==128:assert succ=={f'A128_seed{seed}':95,f'B128_seed{seed}':92}
 prior.append({'root_review':q,'budget':budget,'seed':seed,'successes_retained':succ,'B_minus_A_success_rate':(succ[f'B{budget}_seed{seed}']-succ[f'A{budget}_seed{seed}'])/100,'prior_acceptance_inherited_not_repeated':True})
shared=save('shared_development_panel_all_eight_jobs.json',{'status':'passed','current_job':'3047443','prior_matched_runtime_jobs':prior,'current_trials':200,'prior_trials':1400,'unique_initial_states_across_all_eight_jobs':100,'same_development_panel_sha256':panel,'same_environment':environment,'same_action_semantics_sha256':semantics,'not_independent_across_budget_or_seed':True,'old1212_action_trials_merged':False,'combined_budget_effect_estimate':False,'final_release':False})
st,sr=read(D/'Long64_three_seed_statistics.json','__STATISTICS_SHA__');assert st['status']=='passed' and st['seeds']==[17,23,41] and st['budget']==64 and st['total_trials']==600 and st['unique_initial_states']==100
assert st['paired_bootstrap']['configuration']['bootstrap_seed']==20261016 and st['paired_bootstrap']['configuration']['bootstrap_repeats']==10000
for x in st['evidence']+[st['paired_states'],st['bootstrap_draws']]:assert ref(R/x['path'])==x
oldstats,osr=read(R/'.local/independent_long_development_0727/Long256_three_seed_statistics.json','3ad37e5a918b92d7c9e8d5d0ea538584fe548a24bd0c9a03fd97c6ce28f69abb')
assert oldstats['status']=='passed' and oldstats['budget']==256 and oldstats['seeds']==[17,23,41]
assert oldstats['same_development_panel_sha256']==panel and oldstats['same_action_semantics_sha256']==semantics
logs=[];(D/'logs').mkdir(exist_ok=False)
for suffix in ['job3047443_direct','job3047443_terminal','Long64_statistics']:
 origin=R/('results/formal_main_v2/control_transport/independent_long64_development_0830_'+suffix+'.jsonl');raw=origin.read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
 assert rows[0]['event']=='control_start' and rows[-1]['event']=='control_end' and rows[-1]['returncode']==0 and rows[-1]['source173_and_entrypoint_unchanged'] is True
 entry=R/rows[0]['entrypoint'];assert ref(entry)['sha256']==rows[0]['entrypoint_sha256']
 dest=D/'logs'/origin.name
 with dest.open('xb') as f:f.write(raw)
 logs.append({'original':ref(origin),'copy':ref(dest),'returncode':0})
lr=save('transport_log_copies.json',{'status':'passed','logs':logs,'same_bytes':True,'closure_transport_log_kept_at_standard_external_path':True})
summary=save('summary.json',{'schema':'formal_main_v2','kind':'independent_Long64_development_0830_summary','status':'passed','utc':datetime.now(timezone.utc).isoformat(),'job_id':'3047443','budget':64,'seed':41,'independent_review':ir,'completed_new_trials':200,'unique_initial_states':100,'successes':ind['successes'],'per_task':ind['per_task'],'paired_outcomes':ind['paired_outcomes'],'B_minus_A_success_rate':ind['B_minus_A_success_rate'],'action_checks':ind['action_checks'],'initial_observation_token_overlap_mean':ind['initial_observation_token_overlap_mean'],'new_actual_GPU_seconds':3039,'new_actual_GPU_hours':3039/3600,'Long64_three_seed_statistics':sr,'Long64_three_seed_mean':st['mean_over_seeds'],'Long64_three_seed_sd_ddof1':st['seed_std_ddof1'],'Long64_CI95_B_minus_A':st['paired_bootstrap']['CI95_B_minus_A'],'Long64_all3_development_GPU_seconds':9102,'shared_panel_check':shared,'prior_Long256_statistics_retained':osr,'prior128_negative_results_retained':True,'different_budgets_pooled':False,'legacy_action_trials_included':0,'final_release':False,'test_opened':False,'O2A_latency_verified':False,'logs':lr})
means=st['mean_over_seeds'];sd=st['seed_std_ddof1'];ci=st['paired_bootstrap']['CI95_B_minus_A']
lines=['# Long64 seed41开发终态及三种子独立统计','', '新增200条真实开发试验；原ledger、原consumer、固定Slurm终态原文及173源镜像一致。未再次查询scheduler/state、未提交新作业。','', '|seed|A成功/100|B成功/100|B−A百分点|初观测token重合率|GPU秒|','|---|---:|---:|---:|---:|---:|']
for seed in [17,23,41]:
 v=st['per_seed'][str(seed)];lines.append(f"|{seed}|{v['A_successes']}|{v['B_successes']}|{100*v['B_minus_A']:+.1f}|{v['token_overlap_initial_observation_mean']:.6f}|{v['development_GPU_seconds']}|")
lines+=['',f"三seed均值A {100*means['A_success_rate']:.3f}%、B {100*means['B_success_rate']:.3f}%；B−A {100*means['B_minus_A_success_rate']:+.3f}pp，种子间SD {100*sd['B_minus_A_success_rate']:.3f}pp。",f"任务内初态簇携完整3seed，bootstrap seed20261016、10000次、95%百分位区间 [{100*ci[0]:+.3f}, {100*ci[1]:+.3f}]pp。600条试验仍100个唯一初态。",'本轮新增3039 GPU秒；Long64三个已完成开发分配合计9102秒，训练与测速另计。','仅开发统计；256与128全部历史结果单独保留，不混预算。未开放最终初态，无完整O2A或成功率—速度结论。','']
p=D/'README.md'
with p.open('x') as f:f.write('\n'.join(lines))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file()]
manifest=save('manifest.json',{'schema':'formal_main_v2','kind':'independent_Long64_development_0830_archive','status':'frozen','root':str(D),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'summary':summary,'child_manifests':[mfr],'no_weights_or_sealed_values':True,'no_raw_trial_duplicate':True,'nested_paths_preserved':True})
print(json.dumps({'summary':summary,'manifest':manifest,'files':len(files),'new_GPU_seconds':3039,'new_trials':200,'unique_initial_states':100,'Long64_statistics':sr}))
