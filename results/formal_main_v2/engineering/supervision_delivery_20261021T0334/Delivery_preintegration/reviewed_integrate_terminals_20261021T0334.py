from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,importlib.util,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
B='results/formal_main_v2/preflight/heartbeat_20261021T1134';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
STATE='results/experiment_supervisor/state.json';BEFORE='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def rd(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_text())
def write(n,b):
 p=R/n;assert not p.exists(),n;p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(b);return ref(n)
def save(n,v):return write(n,(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def cp(src,dst):
 p=R/src;assert p.resolve()==p and not p.is_symlink();return write(dst,p.read_bytes())
def package(private,pin,dest):
 mp=private+'/delivery_manifest.json';m=rd(mp,pin);seen=set();mapping=[]
 for row in m['files']:
  n=row['path'];sub=Path(n).relative_to(private).as_posix() if n.startswith(private+'/') else n
  src=private+'/'+sub;assert '..' not in Path(sub).parts and not Path(sub).is_absolute() and sub not in seen;seen.add(sub)
  assert h(R/src)==row['sha256'] and (R/src).stat().st_size==row['bytes']<100*(1<<20)
  mapping.append(dict(source=src,**cp(src,dest+'/'+sub)))
 cp(mp,dest+'/delivery_manifest_original.json')
 save(dest+'/root_publication_mapping.json',dict(original_manifest=ref(mp),files=mapping))
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
ap=argparse.ArgumentParser();ap.add_argument('--goal-manifest-sha256',required=True);ap.add_argument('--goal-review-sha256',required=True);a=ap.parse_args()
op='.local/object_terminal_independent_20261021T0334';gp='.local/goal_terminal_independent_20261021T0334'
oi=rd(op+'/independent_review.json','2e3b0c6c5253e0c4c612daa3d6d27860a315af585b462407896786737f847faf')
gi=rd(gp+'/independent_terminal_review.json',a.goal_review_sha256)
assert oi['status']=='passed' and not oi['blockers'] and oi['full_original_consumer_reconstructed'] and oi['raw_P_R_all13_equal']
assert gi['status']=='passed_new200_terminal_independent_review' and not gi['blockers'] and gi['complete_original_scientific_consumer'] and gi['trials']==200 and gi['allocation_gpu_seconds']==2205
o=rd(B+'/Object_terminal_review.json','07b9c955b5e625dd4cd48fdf0ab8224b0e8d0e8d035190d4cd9d250ae25543d1')
g=rd(B+'/Goal_terminal_review.json','96de85c4c3954d8176461950f53bb6fb6dc6dd441454401a3d8fe5364bb9e18b')
assert o['original_review']['logical_reference_view_complete'] and o['original_review']['unique_total_GPU_seconds']==7039
assert g['status']=='passed_pending_root_and_independent_acceptance' and g['raw_gate']['trials']==200
arc=rd(B+'/Goal_archive_root_verification.json','c2af89ef9fccc868adc380876546f6e4044b8632cf14e267ea1e3116bd515630')
assert arc['status']=='passed' and arc['exact_scientific_blob_set_equal'] and arc['verified_members']==35076
obs=rd(B+'/initial_observation.json','0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41')
assert obs['formal_unique_allocations']==273 and obs['formal_GPU_seconds']==1994468 and not any(obs['projection']['derived'].values())
table='results/formal_main_v2/execution/object_single_error_v1/legacy599_adoption_rows.jsonl'
assert h(R/table)=='ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e'
old=[json.loads(x) for x in (R/table).read_bytes().splitlines()];assert len(old)==599
raw='results/formal_main_v2/libero_object/downstream/linked_policy_error_correction/task08_state0049_dense/attempt01/trials.jsonl'
lines=(R/raw).read_bytes().splitlines(keepends=True);new=[json.loads(x) for x in lines];assert len(new)==3 and new[-1]['status']=='completed'
logical=[dict(trial_id=x['trial_id'],method=x['method'],success=x['success'],status=x['status'],origin='legacy_equivalent',source_job_id=x['source_job_id'],adoption_table=table,adoption_row=i+1,original_result=x['result']) for i,x in enumerate(old)]
logical.append(dict(trial_id=new[-1]['trial_id'],method=new[-1]['method'],success=new[-1]['success'],status=new[-1]['status'],origin='current_linked_attempt',source_job_id='3054409',raw_ledger=raw,result_line=3,result_raw_line_sha256=hashlib.sha256(lines[-1]).hexdigest()))
assert len({x['trial_id'] for x in logical})==600 and sum(x['success'] for x in logical)==521
per={}
for x in logical:
 v=per.setdefault(x['method'],dict(trials=0,successes=0));v['trials']+=1;v['successes']+=int(x['success'])
assert len(per)==6 and all(v['trials']==100 for v in per.values())
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('integration0334_ctl',p);ctl=importlib.util.module_from_spec(sp);sys.modules[sp.name]=ctl;sp.loader.exec_module(ctl)
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=(R/STATE).read_bytes();assert hashlib.sha256(before).hexdigest()==BEFORE;s=json.loads(before)
 frozen=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')['files'];assert len(frozen)==173
 for n,pin in frozen.items():assert h(R/n)==h(S/n)==pin
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 package(op,'dd2266f5c9024e81d785583f1c4931f4086ae0d68f8c710f6659eb8261dcab63',E+'/Object_independent')
 package(gp,a.goal_manifest_sha256,E+'/Goal_independent')
 bridge='.local/object_terminal_pull_bridge_20261021T0334/bridge.py';assert h(R/bridge)=='191745c8b7bcd82a165849ce8680a990da4f5de53d3204f9cdbb51f598cc7e49'
 cp(bridge,'scripts/ops/formal_object_terminal_pull_bridge_v1/bridge.py')
 origin=write(B+'/Object_logical600_origin_view.jsonl',b''.join((json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode() for x in logical))
 oa=save(B+'/Object3054409_root_acceptance.json',dict(schema='formal_main_v2',kind='root_Object_linked_single_error_and_logical600_acceptance',status='accepted',job_id='3054409',reviewed_by='root',root_review=ref(B+'/Object_terminal_review.json'),independent_review=ref(E+'/Object_independent/independent_review.json'),typed_bridge=ref('scripts/ops/formal_object_terminal_pull_bridge_v1/bridge.py'),original_runtime_reviewer_unchanged=True,logical_origin_view=origin,legacy_equivalent_trials=599,current_trials=1,logical_complete_trials=600,unique_development_initial_states=100,successes=521,normal_task_failures=79,per_method=per,all_original600_attempts_retained=True,total_linked_attempts=601,original_policy_error_retained=True,original_refused_chunk_unknown=True,new_allocation_GPU_seconds=326,original_three_allocation_GPU_seconds=6713,total_unique_GPU_seconds=7039,raw_new_ledger_stays_partial1_of600=True,no_fake_legacy_ledger=True,no_automatic_retry=True,final_release=False))
 gs=g['full_original_scientific_consumer_reconstruction']['reconstructed_summary']
 assert gs['methods']['A256_seed17']['successes']==97 and gs['methods']['B256_seed17']['successes']==96
 ga=save(B+'/Goal3054717_root_acceptance.json',dict(schema='formal_main_v2',kind='root_Goal_prospective_full200_acceptance',status='accepted_new200_only',job_id='3054717',reviewed_by='root',root_review=ref(B+'/Goal_terminal_review.json'),independent_review=ref(E+'/Goal_independent/independent_terminal_review.json'),terminal_manifest=ref(B+'/Goal_terminal_manifest.json'),archive_root_verification=ref(B+'/Goal_archive_root_verification.json'),archive_manifest=ref(E+'/Goal_archive/archive_manifest.json'),current_trials=200,unique_development_initial_states=100,policy_queries=3027,executed_policy_steps=23508,paired_pre_policy_inputs=100,methods=gs['methods'],allocation_GPU_seconds=2205,attempts=1,no_automatic_retry=True,old200_retained_HOLD=True,old_failure_cause_identified=False,remaining1000_scientific_HOLD=True,final_release=False,O2A_result=False))
 now=datetime.now(timezone.utc).isoformat()
 nxt=['为Goal剩余五pair（256 seed23/41；64 seed17/23/41）补齐独立原计划/来源/输入门控与单次提交门槛；不泛化已完成3054717的专用入口。','Goal固定30开发观测仍须自身采集准入；Long/Spatial/Object90条不重采。','全部88身份、四套件开发收据及最终清单冻结后再做同checkpoint完整O2A；root全局release前35200最终试验封存。']
 summary=dict(schema='formal_main_v2',kind='root_supervision_delivery',utc=now,previous_snapshot=s['last_root_supervision_snapshot'],source_state_before_sha256=BEFORE,root_completed_arms=72,root_completed_pairs=36,root_reviewed_arm_updates=360000,training_finished=True,controller_completed_normally=True,controller_lease_released=True,controller_restarted=False,current_action_development_trials=6589,compatible_legacy_Long_trials=600,compatible_legacy_Spatial_trials=12,compatible_legacy_Object_trials=599,compatible_development_trials=7800,planned_development_trials=8800,new_current_development_trials_accepted=201,new_legacy_rows_entering_complete_batch_view=599,new_complete_batch_rows_accepted=800,new_unique_initial_states=0,unique_development_initial_states=400,all_historical_catalog_development_rows=7801,historical_catalog_basis='6388 prior current +201 new current +1212 retained historical rows; includes original Object policy_error. Not current complete-panel denominator. Old Goal200 and engineering attempts separately retained.',accepted_count_basis='7800 full-batch rows =6589 current +600 compatible Long +12 compatible Spatial +599 compatible Object. Original Object policy_error retained outside logical denominator; linked new attempt counted once.',per_suite=dict(libero_10=dict(current=1600,legacy=600,complete=2200),libero_spatial=dict(current=2188,legacy=12,complete=2200),libero_object=dict(current=1601,legacy=599,complete=2200),libero_goal=dict(current=1200,legacy=0,complete=1200)),Object_linked_single_error_and600=oa,Goal_prospective200=ga,Goal_old200_HOLD=True,Goal_remaining1000_HOLD=True,remaining_scientific_pairs=[dict(suite='libero_goal',budget=b,seed=seed,trials=200) for b,seed in [(256,23),(256,41),(64,17),(64,23),(64,41)]],registered_formal_allocations=273,allocated_GPU_seconds=1994468,allocated_GPU_hours=1994468/3600,cost_final_for_current_registered_set=True,cost_observed_utc=obs['root_utc'],cost_basis=ref(B+'/initial_observation.json'),newly_accounted_GPU_seconds=2205,active_registered_GPU_jobs=[],actual_running_allocated_GPUs=0,capacity=obs['projection']['derived'],new_GPU_jobs=[],accepted_fixed_observations_including_Long=90,Goal_fixed30_observations_complete=False,frozen_source_files_unchanged=173,all_project_writes_server_only=True,final_trials=0,final_total=35200,final_sealed=True,global_release=False,O2A_released=False,next_actions=nxt)
 sr=save(B+'/final_summary.json',summary);write(B+'/supervisor_snapshot_before.json',before)
 projection=rd(B+'/terminal_analysis_supervisor_projection.json','28972a53a01b3bf21e7c2194fe8b7fd31106fd49ed47290beb1a4f871d363513')
 for jid in ['3054409','3054717']:
  job=next(j for j in s['registered_jobs'] if str(j['job_id'])==jid);exact=next(j for j in projection['registered_jobs'] if str(j['job_id'])==jid)
  for k in ['status','raw_status','exit_code','elapsed_seconds','gpus','node','allocation']:job[k]=exact[k]
  job['terminal_root_acceptance']=oa if jid=='3054409' else ga
 fp=s['formal_main_progress'];assert fp['current_action_development_trial_count']==6388 and fp['completed_development_trials']==7600
 fp.update(current_action_development_trial_count=6589,completed_development_trials=7801,complete_development_batches_accepted_trials=7800,complete_development_batches_compatible_legacy_trials=1211,completed_development_trials_catalog_semantics=summary['historical_catalog_basis'])
 fp['Object3054409_terminal_acceptance_20261021T0334']=oa;fp['Goal3054717_terminal_acceptance_20261021T0334']=ga
 fp['new_action_development_verified_by_job']['3054409']=dict(completed_trials=1,current_trials=1,compatible_legacy_trials=599,complete_panel_trials=600,root_acceptance=oa)
 fp['new_action_development_verified_by_job']['3054717']=dict(completed_trials=200,current_trials=200,root_acceptance=ga)
 fp['downstream_followups_20261021T0334']=dict(summary=sr,Object600_accepted=True,Goal_new200_accepted=True,Goal_old200_HOLD=True,Goal_remaining1000_HOLD=True,O2A_released=False,global_release=False)
 fp['first_object_development'].update(status='complete600_typed_mixed_origin_accepted_original_error_retained',active_job_id=None,active_job_status=None,latest_linked_correction_root_acceptance=oa)
 s['current_round_cost'].update(allocated_gpu_seconds=1994468,allocated_gpu_hours=1994468/3600,final=True,observation=ref(B+'/initial_observation.json'),registered_jobs=273)
 s.update(updated_utc=now,updated_date=now[:10],last_supervision_utc=now,last_root_health_check=ref(B+'/initial_observation.json'),last_root_supervision_snapshot=sr,current_work='Training72/72 done; complete development7800/8800,400 unique; Object mixed600 and prospective Goal200 accepted; remaining Goal5 pairs require exact operational admission; final sealed.',next_actions=nxt,next_allowed_action=nxt[0])
 assert (R/STATE).read_bytes()==before
 tmp=R/'results/experiment_supervisor/.state.integration0334.tmp';assert not tmp.exists();tmp.write_text(json.dumps(s,ensure_ascii=False,indent=2,allow_nan=False)+'\n');os.replace(tmp,R/STATE)
 section=('\n## 2026-10-21 本轮终态验收（'+now+'）\n\n训练72/72组、36pair、360000更新保持完成。Object3054409的新1条与599条兼容历史来源通过原科学consumer、限定四日志补充及不同代理终审，形成完整600条视图；原policy_error与全部601次尝试保留，未伪造599条新ledger。Goal3054717的新固定200条通过完整输入/动作及原consumer独审，仅接纳本次新数据；旧200与旧原因仍HOLD，另1000条待精确工程准入。\n\n完整开发验收7800/8800＝6589 current＋Long600、Spatial12、Object599兼容来源，仍400唯一初态。本轮实际新增验收201条，另599历史条进入完整批次；不是新增800个试验或初态。历史目录7801条含原Object错误，不能作当前分母。Object逻辑600为521成功/79正常失败；Goal256 seed17 A97/100、B96/100，仅开发单seed描述，非最终有效性、等效或加速结论。\n\n273唯一正式分配累计1994468 GPU秒（554.018889小时），0请求槽、0实际活动GPU，当前登记集合成本已终态。Object旧6713＋新326＝7039秒，Goal新2205秒均在总账各计一次。新Goal开发证据35076成员归档24卷并恢复核验，原文件及失败均保留。173冻结文件不变，本轮无新GPU提交。\n\n下一步为Goal剩余五pair（256的23/41；64的17/23/41）补齐独立计划、来源与单次提交准入，并处理Goal固定30观测；已完成作业不重跑。88身份与四套件完整收据/最终清单未全冻结，O2A未开放，最终0/35200仍封存。\n\n证据：[本轮汇总](../'+B+'/final_summary.json)；[下游登记](正式下游阻塞登记_20261021T0334.md)。\n')
 changes=[]
 for n in ['docs/正式主实验规划.md','docs/完整实验计划.md','docs/实验进度.md','docs/正式主实验阶段结论.md','docs/正式非Long开发结果.md','docs/正式Goal主预算开发结果.md']:
  p=R/n;oldb=p.read_bytes();first,sep,rest=oldb.decode().partition('\n');assert sep
  p.write_text(first+'\n'+section+'\n'+rest);changes.append(dict(path=n,before_sha256=hashlib.sha256(oldb).hexdigest(),after_sha256=h(p)))
 write('docs/正式下游阻塞登记_20261021T0334.md',('# 正式下游阻塞登记 20261021T0334\n'+section+'\nObject终审接线的原失败与修正独审全部保留：真实S源码路径影响marshal字节码身份；原pull guard验证9件后，新只读bridge仅核4份精确journal，未改变原生产或科学guard。新Goal200通过不追认旧200，也不解释缺失历史数组。\n').encode())
 for n,pin in frozen.items():assert h(R/n)==h(S/n)==pin
 receipt=save(B+'/root_integration_receipt.json',dict(status='accepted_exact_terminal_evidence_and_updated_shared_state',state_before_sha256=BEFORE,state_after=ref(STATE),summary=sr,object_root_acceptance=oa,goal_root_acceptance=ga,document_changes=changes,new_GPU_submissions=0,pending_submission_unchanged=True,controller_state_unchanged=s['autonomous_training_v1']==json.loads(before)['autonomous_training_v1'],frozen173_unchanged=True))
 print(json.dumps(dict(summary=sr,integration=receipt,state_sha256=h(R/STATE),accepted=7800)))
