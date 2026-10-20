"""Independent genuine terminal closure. Only server-local audit outputs are written."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, sys, subprocess, traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).resolve().parent
B='results/formal_main_v2/preflight/heartbeat_20261020T1330'
ROOT='results/formal_main_v2/downstream_reviews/3045322.json'
PREVIOUS='results/formal_main_v2/downstream_reviews/3043709.json'
PREVIOUS_SHA='3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325'
def sha(b): return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def readref(rel,pin=None):
 p=R/rel;b=p.read_bytes();assert pin is None or sha(b)==pin,rel
 return json.loads(b),ref(p)
def save(name,value):
 p=D/name;b=json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return ref(p)
def module(name,path,pin):
 assert sha(path.read_bytes())==pin
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 # Exact checker keeps the published versioned consumer and pinned scientific closure intact.
 check=module('independent_Long3045322_exact',D/'exact_consumer_check.py','04d762f75e8ed5e97a0541cd5d9aa99182fa0dc0a777fa4cc5fe1615e350b775')
 check.main()
 direct,dref=readref(str((D/'direct_raw_audit_a1.json').relative_to(R)),'77824c0e2d946698d4fca4e7ac91733023493edb8bf5c16b05d7b9421229178b')
 exact,eref=readref(str((D/'exact_consumer_verification_a1.json').relative_to(R)))
 rootpin=exact['root_review']['sha256'];root,rref=readref(ROOT,rootpin)
 pull,pref=readref(root['pull_ref']['path'],root['pull_ref']['sha256'])
 assert exact['status']=='passed_actual_terminal_development_only' and root['scientific_complete'] is True
 assert root['raw_invocation_job_ids']==['3045322'] and root['historical_transition'] is None
 assert root['final_release'] is False and root['final_state_values_read'] is False and root['weights_read'] is False
 assert all(pull[k] is False for k in ['weights_copied','sealed_initial_states_copied'])
 job=next(x for x in root['registered_jobs_at_review'] if x['job_id']=='3045322')
 assert (job['status'],job['exit_code'],job['elapsed_seconds'],job['gpus'])==('COMPLETED','0:0',3466,1)
 # A single exact-ID accounting read independently corroborates the terminal allocation.
 c=module('independent_Long3045322_scheduler',R/'scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
 live=c.Slurm(timeout=30).observe([job]);assert set(live['rows'])=={'3045322'} and live['queue']=={}
 row=live['rows']['3045322'];assert (row['status'],row['exit_code'],row['elapsed_seconds'],row['gpus'])==('COMPLETED','0:0',3466,1)
 assert row['scheduler_name']==job['name'] and row['scheduler_comment']==job['downstream_gateway']['request_token']
 first,fref=readref(B+'/initial_observation.json','96b6affc5b4fd95c65d6d049a85993a9f6b0c7c610bee314fdf8f7161fc47ba9')
 assert first['observation']['rows']['3045322']==row
 sref=save('actual_Slurm_terminal.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':'verified','observation':live,'initial_root_observation':fref,'queried_only_registered_job':'3045322','submitted_jobs':0})
 # Source mirrors are independently verified, not merely inherited by narrative.
 inv,iref=readref('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 assert len(inv['files'])==173
 mirrors=[]
 for rel,h in inv['files'].items():
  paths=[R/rel,S/rel,R/'snapshots/formal_main_v2_run_564be0995e'/rel]
  bs=[p.read_bytes() for p in paths]
  assert bs[0]==bs[1]==bs[2] and sha(bs[0])==h
  mirrors.append({'canonical':rel,'original_snapshot':str(paths[1]),'control_mirror':str(paths[2].relative_to(R)),'sha256':h,'bytes':len(bs[0])})
 mref=save('source_mirror_verification.json',{'status':'passed','files_count':173,'files':mirrors,'total_bytes':sum(x['bytes'] for x in mirrors),'source_inventory':iref,'independent_wrote_mirror':False})
 # Compare only the exact existing development panel, never the sealed init values.
 prev,prref=readref(PREVIOUS,PREVIOUS_SHA)
 oldmanifest=prev['reconstructed_summary']['provenance']['manifest'];manifest=root['reconstructed_summary']['provenance']['manifest']
 assert oldmanifest['development_panel']==manifest['development_panel'] and oldmanifest['development_panel_sha256']==manifest['development_panel_sha256']
 panel,paref=readref(manifest['development_panel'],manifest['development_panel_sha256'])
 assert panel['split']=='development' and len(panel['states'])==100
 assert prev['action_semantics_sha256']==root['action_semantics_sha256']
 prior_succ={k:v['successes'] for k,v in prev['reconstructed_summary']['methods'].items()}
 assert prior_succ=={'A128_seed23':95,'B128_seed23':92}
 panel_check={'same_exact_development_panel':paref,'unique_initial_states_across_seed23_and41':100,'trial_count_across_two_seeds':400,'independent_initial_states_not_doubled':True,'old_seed23_review':prref,'old_seed23_successes_retained':prior_succ,'old_seed23_B_minus_A':-0.03,'seed17_included':False,'legacy_action_trials_included':0,'aggregate_or_significance_claim':False}
 pcref=save('cross_seed_panel_identity.json',panel_check)
 evidence=dict(exact['evidence_sha256'])
 for x in [dref,eref,rref,pref,sref,fref,iref,mref,prref,paref,pcref]:
  assert x['path'] not in evidence or evidence[x['path']]==x['sha256'];evidence[x['path']]=x['sha256']
 for rel,h in evidence.items():assert sha((R/rel).read_bytes())==h,rel
 taskdiff={t:(direct['per_task']['B128_seed41'][t]['successes']-direct['per_task']['A128_seed41'][t]['successes'])/10 for t in map(str,range(10))}
 receipt={'schema':'formal_main_v2','kind':'formal_action_downstream_independent_review','status':'passed','review_role':'independent','reviewed_by':'independent_subagent_long128s41_terminal_0530','reviewed_utc':datetime.now(timezone.utc).isoformat(),'version':'Long3045322-independent-0530-v1',
  'execution_version':'formal-downstream-action-v1','job_id':'3045322','stage':'development','suite':'libero_10','method_ids':['A128_seed41','B128_seed41'],
  'root_review':rref,'pull':pref,'direct_raw_audit':dref,'exact_consumer_verification':eref,'actual_terminal_accounting':sref,'source_mirror_verification':mref,'cross_seed_panel_identity':pcref,
  'blockers':[],'scientific_complete':True,'completed_trials':200,'expected_trials':200,'unique_initial_states':100,'fresh_action_ancestry':True,'legacy_terminal_trials_reused':0,'raw_invocation_job_ids':['3045322'],
  'actual_runtime_chain_verified':True,'synthetic_evidence_used_for_scientific_acceptance':False,'successes':direct['successes'],'per_task':direct['per_task'],'paired_outcomes':direct['paired_outcomes'],'B_minus_A_success_rate':direct['B_minus_A_success_rate'],'per_task_B_minus_A_success_rate':taskdiff,
  'selected_checkpoint_SHA':{x['identity']['method_id']:x['identity']['checkpoint_sha256'] for x in manifest['methods']},
  'action_checks':{k:direct[k] for k in ['raw_policy_calls','executed_control_steps','finite_environment_action_max_abs','chunks_with_environment_abs_above_1','executed_actions_exactly_match_chunk_prefixes','future_head_calls']},
  'runtime_structure':direct['deployment_runtime_structure'],'action_semantics_sha256':root['action_semantics_sha256'],
  'cost':{'current_GPU_seconds':3466,'all_attempt_GPU_seconds':3466,'GPU_hours':3466/3600,'allocations':1,'nested_runtime_wall_seconds':direct['nested_execution_wall_seconds'],'nested_phases_added':False},
  'initial_observation_token_overlap_mean':direct['initial_observation_token_overlap_mean'],'token_overlap_scope':direct['token_overlap_scope'],
  'O2A_latency_verified':False,'whole_suite_22_methods_complete':False,'final_release':False,'final_state_values_read':False,'weights_read_by_independent':False,'state_changed':False,'P_written':False,'Slurm_submitted':False,
  'conclusions':['The exact published consumer reconstructed the genuine root review without changing any scientific source or validator.',
  'This job contains200 complete fresh development trials over100 shared initial states. Seed41 A95/B92 gives B minus A minus3percentage points; no significance, equivalence or latency claim follows.',
  'The same100 development initial states are shared with seed23; those two seeds are not200 independent states. Seed23 negative results are retained; seed17 is not silently included.',
  'The1212 historical trials under old action execution semantics are not merged into this matching-runtime comparison. No final-state values were read or released.'],
  'evidence_sha256':evidence,'evidence_count':len(evidence)}
 reviewref=save('independent_review.json',receipt)
 lines=['# Long128 seed41 开发评测独立验收','', '通过原始试验逐条复算和原发布 consumer 重建。仅开发评测，不是最终成功率或测速结论。','',
 'A=95/100，B=92/100，B−A=−3个百分点。双方成功91、仅A4、仅B1、均失败4。','',
 '|任务|A成功/10|B成功/10|B−A百分点|','|---|---:|---:|---:|']
 for t in map(str,range(10)):lines.append('|'+t+'|'+str(direct['per_task']['A128_seed41'][t]['successes'])+'|'+str(direct['per_task']['B128_seed41'][t]['successes'])+'|'+str(round(taskdiff[t]*100))+'|')
 lines+=['','6835次8×7 chunk，54014控制步；执行动作逐值等于返回chunk前缀。未来头调用0。初始观测token集合重合率0.881796875，仅覆盖100个相同初观测。',
 '单次实际Slurm分配3466 GPU秒（约0.9628 GPU小时），嵌套运行耗时不重复累加。',
 'seed23与41使用同100个固定开发初态，不能视为200独立初态。保留seed23的A95/B92负结果；未纳入seed17，也未混入旧动作语义的1212条历史结果。',
 '全部代码、收据与本目录审计产物仅保存服务器；未改state/Git或提交Slurm，未复制权重、读取封存值。','']
 with (D/'README.md').open('x') as f:f.write(chr(10).join(lines))
 files=[ref(p) for p in sorted(D.iterdir()) if p.is_file()]
 mf=save('manifest.json',{'schema':'formal_main_v2','kind':'independent_terminal_archive','status':'frozen','root':str(D),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'independent_review':reviewref,'external_references':[rref,pref,fref,prref],'no_raw_trial_duplicate':True,'no_checkpoints_or_sealed_values':True})
 print(json.dumps({'independent_review':reviewref,'manifest':mf,'successes':direct['successes'],'completed_trials':200,'unique_initial_states':100,'GPU_seconds':3466}))
if __name__=='__main__':
 try:main()
 except Exception as e:
  save('closure_failure_a2.json',{'status':'failed_no_source_modified','type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()});raise
