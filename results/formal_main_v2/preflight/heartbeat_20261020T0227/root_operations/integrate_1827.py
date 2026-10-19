
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0227'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
pins={'final_capacity_observation.json':'778134f7599c9984440d3461ca67c128853ca3bd19d0ee151b1ad10fc83b61f1','Long_runtime_readiness_root_index.json':'aa3319a5d3f2cf5f1c34d0ed272feae84cbaf7cfda4a6cb7d3cc88cb97c34c53','author_archive_publication.json':'e90e423885a5d5558ff8cf4cd1434dbbfb4e5d5b29671a31a94f36123091e00c','independent_archive_publication.json':'bc41fa4a6d2893b2890c563ecb646b8c104ed11716c51fc4f54b03b04c578b91','admission_archive_publication.json':'dab48b1c9d820f8be91c2ccbb0850fc3cd30112659e987603deb36028f1f0757','packages/long_admission_independent/post_readiness_independent_review.json':'c0d14e1e1a4b249c44ec9fde1b7d2a386396e868cec4c8d5034266a3812fd939'}
for rel,pin in pins.items():assert h(R/B/rel)==pin
for rel in ['author_archive_publication.json','independent_archive_publication.json','admission_archive_publication.json']:
 for row in json.loads((R/B/rel).read_text())['files']:
  p=R/row['path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
postrel=B+'/packages/long_admission_independent/post_readiness_independent_review.json';post=json.loads((R/postrel).read_text())
assert post['status']=='passed_exact_pre_execution_control_and_source_closure_only' and post['actual_new_P_wrapper_verifications']==post['actual_full_NativeIO_checks']==post['actual_validate_authorization_checks']==8
assert len(post['checks'])==245 and all(x['passed'] for x in post['checks']) and not post['actual_GPU_runtime_chain_verified']
ix=json.loads((R/B/'Long_runtime_readiness_root_index.json').read_text());assert len(ix['shards'])==8 and ix['actual_full_P_wrapper_verifications']==8
for sh in ix['shards']:
 for k in ['authorization','readiness','reservation','prepared_invocation','root_check','independent_review']:
  rr=sh[k];assert h(R/rr['path'])==rr['sha256']
ob=json.loads((R/B/'final_capacity_observation.json').read_text());assert ob['root_independent_complete']==46 and len(ob['active_jobs'])==8 and ob['allocated_GPU_seconds']==1443838
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('integrate1827ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_text());old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==46
 assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']['sha256']=='0aabce41556248f83877ce47a102ebb32817624eac4ad04a431862b098289c9d'
 assert f['completed_final_trials']==0 and not f['global_release_created']
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for rel,pin in inventory['files'].items():assert h(R/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.fromisoformat(ob['utc']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 accepted=save(B+'/Long_development_runtime_root_acceptance.json',dict(schema='formal_main_v2',kind='root_exact_Long16_development_pre_execution_acceptance',utc=now,status='passed_exact_pre_execution_not_reserved_or_submitted',runtime_readiness_index=ref(B+'/Long_runtime_readiness_root_index.json'),independent_plan_review=ref(B+'/packages/long_outer_independent/independent_review.json'),post_readiness_independent_review=ref(postrel),author=ref(B+'/packages/long_outer_author/candidate_review.json'),author_CPU_tests=42,independent_plan_checks=39,actual_P_wrapper_checks_root=8,actual_P_wrapper_checks_independent=8,methods=16,shards=8,planned_trials=1600,unique_initial_states_per_method=100,all_plan_and_method_bindings_explicit=True,typed_approval_fields_alone_not_treated_as_full_plan_binding=True,old_Long600_and_10531_GPU_seconds_preserved=True,old_execution_equivalence_not_claimed=True,new_GPU_submissions=[],new_trials=0,actual_GPU_runtime_chain_verified=False,reservations_created_but_not_activated=True,existing_Spatial_CUDA_reservation_unchanged=True,final_release=False))
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_exact_Long_development_admission',utc=now,observation_utc=ob['utc'],scheduler=ref(B+'/final_capacity_observation.json'),root_independent_complete=46,machine_and_prior_complete=ob['machine_and_prior_complete'],root_independent_updates=239000,root_training_complete_by_suite=dict(Long=18,Spatial=16,Object=10,Goal=2),allocated_GPU_seconds=ob['allocated_GPU_seconds'],allocated_GPU_hours=ob['allocated_GPU_hours'],cost_is_final=False,active_GPU_jobs=8,reserved_next_GPU_slots=1,reservation_is_not_additional_allocated_GPU=True,Long_runtime_acceptance=accepted,new_completed_training_groups=0,new_GPU_submissions=[],new_development_trials=0,old_development_trials_preserved=1212,completed_final_trials=0,final_release=False,normal_training_left_to_controller=True,no_continuous_in_turn_monitoring=True,server_only=True,frozen_files_unchanged=173,previous_verified_Git_commit='1ab222e5b26453bc648b7fff810cba801ea7cd2f'))
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now
 s['current_work']='46/72 root+independent training groups complete;8 healthy GPU jobs in bounded snapshot. Long16 development:8 exact fresh A/B shards have root and independent pre-execution acceptance,real P wrapper checks,readiness and unconsumed one-use authorizations;not registered/submitted. Existing next-slot reservation remains exact Spatial64 seed23 CUDA recovery.'
 s['next_actions']=[
 'Normal controller continues auto5000 with max8 GPUs;leave healthy jobs running and no manual normal500 boundaries.',
 'At the next actual free slot use exact3028522 recovery gateway and existing one-use authorization to1500;after genuine evidence review separately admit continuous5000. Do not reuse its reservation for development.',
 'After the CUDA reservation is properly consumed/released,root may activate exactly one prepared Long shard reservation in shared writer lock/CAS,query all actual registered jobs,pending,owner/lease and artifacts,then use its exact one-use authorization/gateway. Start k128_seed23 followed by registered index order when real capacity allows;do not regenerate plans or issue duplicate stages.',
 'Use the new runtime journal/whole allocation/actual trial artifacts for terminal review;pre-execution CPU acceptance and inherited3039197 engineering are not new GPU scientific results. Retain old1212 trials and10531 Long GPU seconds;old6 Long identity migration remains separate.',
 'Complete remaining trained-selector development preparation using canonical source reviews. Keep O2A/global freeze/final closed until all72 checkpoints,16 references and four full suite development receipts satisfy the original global gates.'
 ]
 s['next_allowed_action']=s['next_actions'][1]+' '+s['next_actions'][2]
 f['Long_remaining16_development_runtime_readiness']=accepted
 f['downstream_action_range_issue']['latest_execution_preparation']=accepted
 f['downstream_action_range_issue']['Long16_pre_execution_qualified_scope']=dict(stage='development',methods=16,planned_trials=1600,acceptance=accepted,actual_GPU_verified=False,slot_reservation_activated=False)
 assert s['registered_jobs']==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(sp,s,before)
 detail=f'{stamp} 监督快照：正式训练仍 **46/72组**（Long18、Spatial16、Object10、Goal2），**8卡运行，累计401.066111 GPU小时**，含失败和运行中分配，非最终成本。本轮完成Long其余16选择器的8份开发运行入口验收：作者42项、独立39项检查，root和另一独审各执行8次真实P端完整wrapper校验。科学方法、原checkpoint、100个共同开发初态及173冻结文件不变；没有新增训练完成量或闭环结果。\n\n8份readiness与一次性提交授权已登记，专属预约均未激活；下一实际空槽仍优先Spatial64seed23的已批准CUDA恢复。恢复预约正确消费后，root按本批顺序、实时容量和唯一请求保护启用开发评测。现有1212条结果及费用保留，最终0/35200封存；正常训练交控制器和下次定时监督。\n\n[Long开发登记](正式Long其余16选择器开发登记.md)；[本轮收据](../'+B+'/summary.json)。\n\n'
 short=f'{stamp} 更新：Long其余16选择器的8份开发运行入口通过root/独审及实际P端完整校验，8份readiness与单次授权已登记但未激活预约、未提交。训练仍46/72组、8卡运行，累计401.066111 GPU小时（非最终）；下一空槽优先已登记Spatial CUDA恢复，最终0/35200封存。[验收与执行顺序](正式Long其余16选择器开发登记.md)；[本轮收据](../'+B+'/summary.json)。\n\n'
 changed=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式动作执行入口接入记录','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;prior=p.read_text();assert stamp+' 监督快照' not in prior and stamp+' 更新' not in prior
  first,tail=prior.split('\n',1);oldsha=h(p);note=detail if name=='实验进度' else short
  if name=='正式Long其余16选择器开发登记':
   note=detail.replace('[Long开发登记](正式Long其余16选择器开发登记.md)；','')
   note+='本次canonical目录：results/formal_main_v2/execution/long_remaining16_action_v1_1827/。每pair包含scientific/effective plan、execution contract、root/independent review、readiness、prepared invocation、单次authorization/reservation和实际P入口check。prepared invocation不等于已登记调用；正式invocation仅在真实提交事务发布。每个reservation只属于其本身计划，不能消费Spatial CUDA预约。旧方案HOLD状态保留如下作为历史，本批新readiness仅适用这16方法的fresh development；旧Long6方法的身份处理、完整O2A和最终release另行验收。\n\n'
  p.write_text(first+'\n\n'+note+tail.lstrip('\n'));changed.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 p=R/'scripts/ops/formal_action_deployment_v1/README.md';prior=p.read_text();first,tail=prior.split('\n',1);oldsha=h(p)
 p.write_text(first+'\n\nCurrent status, 2026-10-20 CST: eight fresh Long A/B development shards (16 already selected checkpoints,1600 planned trials) have exact per-plan root/independent readiness and one-use authorizations. Root and independent checks each ran the unchanged full P wrapper for all8; no new GPU execution or trial is claimed. Their reservations are not activated. The next reserved slot still belongs to the approved Spatial64 seed23 CUDA recovery. See results/formal_main_v2/preflight/heartbeat_20261020T0227/Long_development_runtime_root_acceptance.json.\n\nThe following records earlier component/Spatial preparation and remains historical evidence.\n\n'+tail.lstrip('\n'))
 changed.append(dict(path=p.relative_to(R).as_posix(),before_sha256=oldsha,after_sha256=h(p)))
 ops=R/B/'root_operations';ops.mkdir(exist_ok=True)
 for name in ['observe_formal_1827.py','publish_Long_outer_1827.py','archive_Long_outer_author_1827.py','archive_Long_outer_independent_1827.py','archive_Long_admission_1827.py','archive_Long_admission_1827_v2.py','sign_Long_readiness_1827.py','capacity_before_approved_recovery_1827.py','integrate_1827.py']:
  with (ops/name).open('xb') as f:f.write((R/'.local'/name).read_bytes())
 with (R/B/'previous_Git_push_verified.json').open('xb') as f:f.write((R/'.local/github_push_1722_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(schema='formal_main_v2',state_before=before,state_after=h(sp),summary=summary,documentation=changed,controller_jobs_reservations_and_cost_field_unchanged=True,scientific_files_unchanged=173,new_GPU_submissions=[],archive_schema_adjustment_before_execution='Admission archive uses paths relative to its own base; v2 normalizes those paths. Unexecuted v1 retained; no failed invocation or source overwrite.',new_GPU_results_claimed=False))
 print(json.dumps(dict(summary=summary,Long_pre_execution=accepted,root_complete=46,observed_GPU=8,GPU_hours=ob['allocated_GPU_hours'],next_slot='Spatial64_seed23_CUDA_recovery',new_trials=0,documents=len(changed))))
