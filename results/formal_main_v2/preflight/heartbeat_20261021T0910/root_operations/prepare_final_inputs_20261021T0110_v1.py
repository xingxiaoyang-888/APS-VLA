from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T0910';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110';OX='results/formal_main_v2/execution/object_single_error_v1';GX='results/formal_main_v2/engineering/goal_full200_20261021T0110'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def save(n,v):
 p=R/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--source-sha256',required=True);ap.add_argument('--goal-job',required=True);ap.add_argument('--expected-state-sha256',required=True);a=ap.parse_args()
assert a.goal_job.isdigit() and a.source in (GX+'/dispatch_attempt01/post_release_observation.json',GX+'/dispatch_attempt01/reconciled_release.json') and h(R/a.source)==a.source_sha256
raw=rd(a.source);o=raw['observation'] if a.source.endswith('reconciled_release.json') else raw
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('prepare_final0910',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 st=R/'results/experiment_supervisor/state.json';assert h(st)==a.expected_state_sha256;s=rd('results/experiment_supervisor/state.json')
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 allids={str(j['job_id']) for j in s['registered_jobs']};fids={str(j['job_id']) for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'}
 assert c.parse_sacct(o['observation']['raw_sacct'],allids)==o['observation']['rows']
 assert set(o['observation']['rows'])==allids and len(fids)==273
 cap=c.capacity(s['registered_jobs'],o['observation'],'3034538');assert cap['unknown']==[] and cap['findings']==[] and cap['occupied']==o['derived']['occupied']
 cost=sum(o['observation']['rows'][j]['elapsed_seconds']*o['observation']['rows'][j]['gpus'] for j in fids);assert cost==o['derived']['allocated_formal_GPU_seconds']
 assert o['lease']['lease_available_measured'] is True
 save(B+'/latest_actual_operation_observation.json',dict(kind='root_actual_operation_observation_projection',new_queries=0,source_receipt=ref(a.source),utc=o['utc'],observation=o['observation'],occupied=cap['occupied'],allocated_GPU_seconds=cost,controller_lease_released=True,lease=o['lease'],registered_formal_allocations=len(fids),raw_sacct_reparsed_equal=True))
 before=B+'/final_state_before.json';assert not (R/before).exists();(R/before).write_bytes(st.read_bytes());assert h(R/before)==a.expected_state_sha256
 files=[a.source,before,B+'/Spatial3054201_root_acceptance.json',B+'/Spatial3054201_acceptance_transaction.json',B+'/Goal_source_publication.json',B+'/Goal_actual_P_capture.json',B+'/Goal_root_authorization_receipt.json',B+'/Goal_dispatch_admission_receipt.json',OX+'/root_legacy_adoption.json',OX+'/legacy599_adoption_rows.jsonl',OX+'/actual_P_verification.json',OX+'/runtime_readiness.json',OX+'/submission_authorization.json',OX+'/prepared_invocation.json',OX+'/gateway_attempt01/sbatch_result.json',OX+'/gateway_attempt01/release_attempt.json',OX+'/gateway_attempt01/release_result.json',OX+'/gateway_attempt01/reconciled_release.json',OX+'/gateway_attempt01/committed.json',GX+'/root_authorization.json',GX+'/root_readiness.json',GX+'/independent_readiness.json',GX+'/dispatch_admission.json',GX+'/held_dispatch.json',GX+'/slot_reservation.json']
 # Exact transaction filenames are checked against installed scope; no fresh Slurm observation.
 for n in ['sbatch_result.json','release_attempt.json','release_result.json','committed.json']:
  files.append(GX+'/dispatch_attempt01/'+n)
 for n in list(files):
  if not (R/n).exists() and n.endswith(('/held_dispatch.json','/slot_reservation.json')):files.remove(n)
 # Production authorization supplies exact actual dispatch/reservation paths.
 auth=rd(GX+'/root_authorization.json')
 P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
 for key in ['dispatch_record_path','reservation_path']:
  files.append(Path(auth[key]).relative_to(P).as_posix())
 for p in sorted((R/B).glob('*_archive.json')):
  v=rd(p.relative_to(R).as_posix())
  if v.get('status')=='immutable_nonweight_package_archived':
   files.extend([p.relative_to(R).as_posix(),v['destination']+'/'+Path(v['manifest']['path']).stem+'_original.json'])
 evidence={str(i):ref(n) for i,n in enumerate(dict.fromkeys(files))}
 obj=dict(job_id='3054409',authorization=ref(OX+'/submission_authorization.json'),invocation=ref('results/formal_main_v2/invocations/object_single_error_task08_state0049_dense_attempt01.json'),original_ACK=ref(OX+'/gateway_attempt01/sbatch_result.json'),original_release=ref(OX+'/gateway_attempt01/release_result.json'),original_ACK_reconciliation=ref(OX+'/gateway_attempt01/reconciled_release.json'),old599_legacy_adopted=True,old_policy_error_retained=True,original_three_allocation_GPU_seconds=6713,new_trial_accepted=False,automatic_retry=False)
 goal=dict(job_id=a.goal_job,status='one_prospective_fixed200_attempt_registered',old200_adopted=False,old_cause_explained=False,new_development_accepted=0,remaining1000_scientific_HOLD=True,package_manifest_sha256='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec',runtime_entrypoint_sha256='1b640f36962c1278b4a40af634ac4cb0793e7baf00840dd40e5fbeaf4c1ade15',dispatch_entrypoint_sha256='8d3e282946c300f072a13c1b4a658f92b3e25cfb3130a0ad63ab186fe6386b3c',authorization=ref(GX+'/root_authorization.json'),dispatch_admission=ref(GX+'/dispatch_admission.json'),original_ACK=ref(GX+'/dispatch_attempt01/sbatch_result.json'),original_release=ref(GX+'/dispatch_attempt01/release_result.json'),root_runtime_verification=ref(B+'/Goal_actual_P_capture.json'),maximum_trials=200,unique_original_development_states=100,maximum_control_steps=60000,maximum_policy_queries=7600,maximum_attempts=1,automatic_retry=False,final_states_opened=False,raw_observation_root='/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01',original_control_loop_preserved=True,new_attempt_acceptance_requires_raw_terminal_review=True)
 text='Goal新固定200方案完成运行包与提交器不同代理CPU独审、R/P精确发布及actual P元数据/来源/存储门槛；仅授权并提交一次'+a.goal_job+'，仍须真实原始输入/动作/consumer终验。原100开发初态×A/B256seed17顺序、checkpoint、科学设置及原控制循环不变；单次上限200条/60000控制步/7600查询。CPU独审发现并修正非t0查询缺五组件原始数组未被拒绝的验收漏洞，和提交器mode/run_root与真实consumer不一致的接口问题；旧候选与反例完整保留。两处修正均不是科学方法变更。新运行尚未计入开发验收，不解释旧Goal差异、不接纳旧200，另1000 Goal科学开发仍HOLD；工程58的803/840秒均保留。正常运行不在本轮连续轮询。'
 actions=['按原ACK检查Object3054409和Goal'+a.goal_job+'后续终态，不重复提交；正常运行交下次监督。','Object新单条须原始记录+原类型consumer与独立终审，再与legacy599构成完整600来源视图；原policy_error保留。','Goal固定200须完整原始输入/动作与原consumer及独立终验，按精确allowlist归档开发blob；旧200和另1000仍HOLD。','全部88身份、四套件完整开发收据及最终清单冻结后再开放完整O2A；最终35200仍等待root全局release。']
 details='Spatial已接纳588current与12legacy，400全局唯一开发初态不增加。Object599独立采用及旧失败均保留，新单条不能按结果自动重试或伪造599新ledger。Goal v1/v2和dispatcher v1/v2完整保留，CPU结果不是GPU科学终验；调用前输入证据通过不解释旧原因。所有活动GPU成本按保存的唯一allocation截面更新，不能把运行下界当终值。Git提交和GitHub推送必须分别验证。\n'
 result=dict(schema='formal_main_v2',kind='root_delivery_inputs',state_before_sha256=a.expected_state_sha256,state_before=ref(before),evidence=evidence,operation_observation=ref(B+'/latest_actual_operation_observation.json'),new_GPU_jobs=['3054409',a.goal_job],Object_linked_attempt=obj,Goal_full200=goal,Goal_markdown=text,next_actions=actions,blocker_details_markdown=details)
 save(B+'/final_snapshot_inputs.json',result);assert h(st)==a.expected_state_sha256
 print(json.dumps(dict(status='exact_final_inputs_ready',input_sha256=h(R/B/'final_snapshot_inputs.json'),state_before=a.expected_state_sha256,cost=cost,active=cap['occupied'])))
