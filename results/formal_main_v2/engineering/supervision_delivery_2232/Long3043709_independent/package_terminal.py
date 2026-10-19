"""Package independent actual terminal review; never writes canonical results or state."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).resolve().parent
B='results/formal_main_v2/preflight/heartbeat_20261020T0632/'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def readref(rel,pin):
 r=ref(R/rel);assert r['sha256']==pin,rel;return json.loads((R/rel).read_bytes()),{'path':rel,'sha256':pin}
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return ref(p)
direct,dref=readref('.local/Long3043709_independent_2232/direct_raw_audit_a1.json','57fc312b0c00e0369a6f6cbd7345cc738edf5f85c7fd7d0623531da1883b7256')
closed,cref=readref('.local/Long3043709_independent_2232/exact_consumer_verification_a1.json','cc2fa7dd4e7d91333e7a02ca02ea800021fa3800ffbb202a99751a1f037620b8')
root,rootref=readref('results/formal_main_v2/downstream_reviews/3043709.json','3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325')
terminal,tref=readref(B+'3043709_root_terminal.json','22199d9e332346942dbd6aefe0b59bca3870f3bceee63e994b92b32153a0e03e')
mirror,mref=readref(B+'3043709_source_snapshot_mirror.json','fc781199e14d1e38557289a86a26e32099aed311e06cd8af545c35e09de7d5fb')
failure,fref=readref(B+'3043709_root_review_failure.json','8a4a3709ef3e26537065200917ca8f12f4bc96aeebc1c53d06bf32393f7c0970')
pull,pref=readref('results/formal_main_v2/pulls/20261019T223821Z_c4b67281fa45/receipt.json','ed05968d82ceb14d333990099496d32aa0fdaf40f7217525636d10ec113f132e')
snapshot,sref=readref(B+'3043709_terminal_jobs_snapshot.json','509955f1a0d3650bcc42cf317b81f83dd88a8e7cd08a52f3029785cb36f14f6b')
inventory,iref=readref('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
assert mirror['status']=='verified' and len(mirror['files'])==173 and mirror['weights_copied'] is False and mirror['sealed_values_read'] is False
assert {x['canonical_source'] for x in mirror['files']}==set(inventory['files'])
total=0;checks=[]
for x in mirror['files']:
 rel=x['canonical_source'];h=inventory['files'][rel];dest='snapshots/formal_main_v2_run_564be0995e/'+rel
 assert x['sha256']==h and x['destination']==dest and x['source']==str(S/rel) and x['raw_bytes_changed'] is False
 bs=[(R/rel).read_bytes(),(R/dest).read_bytes(),(S/rel).read_bytes()]
 assert all(sha(b)==h and len(b)==x['bytes'] for b in bs) and bs[0]==bs[1]==bs[2]
 total+=x['bytes'];checks.append({'source':str(S/rel),'canonical':rel,'mirror':dest,'sha256':h,'bytes':x['bytes']})
assert total==1664859
mirrorcheck=save('mirror_confirmation.json',{'schema':'formal_main_v2','kind':'independent_exact_snapshot_mirror_verification','status':'passed',
 'root_mirror':mref,'original_failure_retained':fref,'files':checks,'files_count':173,'total_bytes':total,'scientific_source_or_reviewer_changed':False,'independent_wrote_mirror':False})
assert closed['status']=='passed_actual_terminal_development_only' and closed['root_review']==rootref
assert terminal['root_review']==rootref and terminal['pull']==pref and terminal['scientific_complete'] is True and terminal['new_jobs']==0
assert root['pull_ref']==pref and root['registered_jobs_at_review']==snapshot['registered_jobs']
assert root['scientific_complete'] is True and root['historical_transition'] is None and root['raw_invocation_job_ids']==['3043709']
job=next(j for j in snapshot['registered_jobs'] if j['job_id']=='3043709')
assert job['status']=='COMPLETED' and job['exit_code']=='0:0' and job['gpus']==1 and job['elapsed_seconds']==3083
assert all(pull[k] is False for k in ['weights_copied','sealed_initial_states_copied'])
assert root['reconstructed_summary']['test_opened'] is False and root['final_release'] is False and root['final_state_values_read'] is False and root['weights_read'] is False
# File pins are independently rechecked after the root consumer returned.
for rel,h in root['audit_source_sha256'].items():assert sha((R/rel).read_bytes())==h,rel
evidence=dict(closed['evidence_sha256'])
for v in [dref,cref,rootref,tref,mref,fref,pref,sref,iref,{'path':mirrorcheck['path'],'sha256':mirrorcheck['sha256']}]:
 assert v['path'] not in evidence or evidence[v['path']]==v['sha256'];evidence[v['path']]=v['sha256']
for p in D.iterdir():
 if p.is_file():r=ref(p);evidence[r['path']]=r['sha256']
for name in ['Long3043709_independent_direct_2232_a1.jsonl','Long3043709_independent_consumer_2232_a1.jsonl']:
 p=R/'results/formal_main_v2/control_transport'/name;r=ref(p);evidence[r['path']]=r['sha256']
receipt={'schema':'formal_main_v2','kind':'formal_action_downstream_independent_review','status':'passed','review_role':'independent',
 'reviewed_utc':datetime.now(timezone.utc).isoformat(),'reviewed_by':'independent_subagent_server_v3_audit','version':'Long3043709-independent-2232-v1',
 'execution_version':'formal-downstream-action-v1','job_id':'3043709','stage':'development','suite':'libero_10','method_ids':['A128_seed23','B128_seed23'],
 'root_review':rootref,'pull':pref,'terminal_snapshot':sref,'direct_raw_audit':dref,'exact_consumer_verification':cref,
 'source_snapshot_mirror_confirmation':{'path':mirrorcheck['path'],'sha256':mirrorcheck['sha256']},'original_transport_boundary_failure':fref,
 'blockers':[],'scientific_complete':True,'completed_trials':200,'expected_trials':200,'unique_initial_states':100,
 'fresh_action_ancestry':True,'legacy_terminal_trials_reused':0,'raw_invocation_job_ids':['3043709'],
 'actual_runtime_chain_verified':True,'synthetic_evidence_used_for_scientific_acceptance':False,
 'successes':direct['successes'],'per_task':direct['per_task'],'paired_outcomes':direct['paired_outcomes'],'B_minus_A_success_rate':-0.03,
 'selected_checkpoint_SHA':{x['identity']['method_id']:x['identity']['checkpoint_sha256'] for x in root['reconstructed_summary']['provenance']['manifest']['methods']},
 'action_checks':{k:direct[k] for k in ['raw_policy_calls','executed_control_steps','finite_environment_action_max_abs','chunks_with_environment_abs_above_1','executed_actions_exactly_match_chunk_prefixes','future_head_calls']},
 'runtime_structure':direct['deployment_runtime_structure'],'action_semantics_sha256':root['action_semantics_sha256'],
 'cost':{'current_GPU_seconds':3083,'all_attempt_GPU_seconds':3083,'GPU_hours':3083/3600,'allocations':1,'nested_runtime_wall_seconds':direct['nested_execution_wall_seconds'],'nested_phases_added':False},
 'initial_observation_token_overlap_mean':direct['initial_observation_token_overlap_mean'],
 'token_overlap_scope':direct['token_overlap_scope'],'O2A_latency_verified':False,'whole_suite_22_methods_complete':False,
 'final_release':False,'final_state_values_read':False,'weights_read_by_independent':False,'state_changed':False,'P_written':False,'Slurm_submitted':False,
 'conclusions':['Exact published consumer rebuilt the genuine root result from all raw evidence; no validator or scientific source was changed.',
 'The sole initial root-review failure was a missing control-side mirror of173 frozen source files. All actual S, original R and new R snapshot bytes agree; failure is retained.',
 '200 fixed development trials cover two selectors over100 shared initial states. B−A is−3percentage points for this seed/budget; this is not a suite aggregate, final success rate, significance/equivalence claim or latency benefit.',
 'No legacy prefix is present. This proof covers only this genuine fresh action-version job and does not certify old execution semantics.'],
 'evidence_sha256':evidence,'evidence_count':len(evidence)}
rref=save('independent_review.json',receipt)
readme="""# Long 3043709 独立终态验收

通过：原发布consumer从正式pull完整重建root结果，且独立逐条复算200个开发trial。此次没有改validator或科学源。

- 仅 Long128 seed23 的A/B两组；100个固定开发初态、200次评测，全部完成。
- A=95/100，B=92/100；配对双方成功91、仅A4、仅B1、均失败4，B−A=−3个百分点。
- 6906次8×7策略chunk、54560个实际控制动作均有限且执行值与chunk前缀完全相同；每视角64token、未来头调用0、单基座加载及上下文恢复通过。
- 单次Slurm分配3083 GPU秒（约0.8564 GPU小时），嵌套加载/运行时间不重复相加。
- 首轮root失败为缺少R/snapshots源镜像。173份原R/S/新镜像逐字节一致（1664859字节），失败原件保留。
- 新运行没有旧前缀。结论只适用于本job；完整套件、测速及最终封存评测尚未据此放行。
- 初态token集合重合率0.866328125只基于100个相同初始观测；不同方法后续轨迹不混作同状态。

本目录仅保存独审代码、摘要与引用，不复制31MB原始trial或权重。正式原件仍在root记录路径，全部写入仅服务器。
"""
with (D/'README.md').open('x') as f:f.write(readme)
rows=[ref(p) for p in sorted(D.iterdir()) if p.is_file()]
manifest=save('archive_closure.json',{'schema':'formal_main_v2','kind':'Long3043709_independent_archive','status':'frozen','root':str(D),'files':rows,
 'file_count':len(rows),'total_bytes':sum(x['bytes'] for x in rows),'independent_review':rref,
 'external_references':[rootref,pref,sref,mref,fref,tref],'no_raw_trial_duplicate':True,'no_checkpoints_or_sealed_values':True})
print(json.dumps({'independent_review':rref,'archive_closure':manifest,'files':len(rows),'evidence_count':len(evidence)}))
