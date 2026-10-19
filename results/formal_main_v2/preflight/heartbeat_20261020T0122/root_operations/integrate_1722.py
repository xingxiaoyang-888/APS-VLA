
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0122'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
pins={
 'final_capacity_observation.json':'51e662eaf3177092139460772828c9833d9caf00ee6201feb8d80c7c2c1e79b4',
 'canonical_reconstruction_summary.json':'ec6cf8153c0eda0d8b14a02c6d99d0fa038648443a5a2ead9a9ffa51cd66e0ac',
 'Long_selected_identity_root_check.json':'e3b08dff62a583e910aecd04179841017e10f1216f6a19f431036fe056ff5757',
 'Long_manifest_publication.json':'a016d94f02f95c56aed8dcace698995770610e68041ec8f48eaa3d8ffbeb75c3',
 'Long_runtime_science_publication.json':'b0f14c0575db757f5d47541a02b7c83540d768c29acdaed6b3285ce62abf8eb3',
 'package_delivery_first.json':'a3087a61da0f5d693857921e7ccfc5812d0ce75c575cd28c6147ff4f16c242c8',
 'package_delivery_second.json':'c3631b6ba1f70495d076cb8ef74097ff769a75729f255910e2743ab96a14ac2b',
 'packages/long_candidate/long_development_1722/candidate_review.json':'79204acb7c06ff63d5471b9b1d395bb09c11ba3920923f5527a63cba3da59d0e',
 'packages/long_independent/spatial_resume_audit_1722/long16/independent_review.json':'37b8009c1291980b1524e84f26c31ca901309dd30a2346ee6ed0af1c32cd77f8',
 'packages/canonical_source_gate/source_gate_review.json':'7e0fedc18dd4937e2c0a60b1daf3ddc85935f506270cac91aac50033dba018d8'}
for rel,pin in pins.items():assert h(R/B/rel)==pin,(rel,h(R/B/rel))
for name in ['package_delivery_first.json','package_delivery_second.json']:
 for package in json.loads((R/B/name).read_text())['packages']:
  for row in package['files']:
   p=R/row['path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
author=json.loads((R/B/'packages/long_candidate/long_development_1722/candidate_review.json').read_text())
ind=json.loads((R/B/'packages/long_independent/spatial_resume_audit_1722/long16/independent_review.json').read_text())
assert author['methods']==16 and author['engineering_shards']==8 and author['planned_trials_total']==1600
assert author['author_tests']==dict(tests=31,failures=0,errors=0,skipped=0) and author['all_registry_rows']==259
assert ind['status']=='passed_independent_scientific_plan_review' and ind['production_status']=='HOLD_PRODUCTION' and ind['independent_checks']==18 and ind['independent_checks_passed']==18
canonical=json.loads((R/B/'canonical_reconstruction_summary.json').read_text());assert canonical['status']=='passed' and len(canonical['results'])==7
for row in canonical['results']:
 for key in ['canonical_review','existing_independent_review']:
  rr=row[key];assert h(R/rr['path'])==rr['sha256']
assert json.loads((R/B/'packages/canonical_source_gate/source_gate_review.json').read_text())['status']=='passed_actual_original_suite_rows'
ob=json.loads((R/B/'final_capacity_observation.json').read_text())
assert ob['root_independent_complete']==46 and len(ob['active_jobs'])==8 and ob['allocated_GPU_seconds']==1417806
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('integrate1722ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_text());old=copy.deepcopy(s)
 assert s['pending_submission'] is None and s['formal_main_progress']['root_and_independent_completed_arms']==46
 assert s['autonomous_training_v1']['reserved_GPU_slots']==1 and s['autonomous_training_v1']['reservation_root_record']['sha256']=='0aabce41556248f83877ce47a102ebb32817624eac4ad04a431862b098289c9d'
 assert s['formal_main_progress']['completed_final_trials']==0 and not s['formal_main_progress']['global_release_created']
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for rel,pin in inventory['files'].items():assert h(R/rel)==pin
 now=datetime.now(timezone.utc).isoformat()
 prep=save(B+'/Long_development_root_preparation.json',dict(schema='formal_main_v2',kind='root_scientific_development_preparation_review',utc=now,status='accepted_scientific_preparation_only',production_status='HOLD_PRODUCTION',author=ref(B+'/packages/long_candidate/long_development_1722/candidate_review.json'),independent=ref(B+'/packages/long_independent/spatial_resume_audit_1722/long16/independent_review.json'),selected_checkpoint_bytes=ref(B+'/Long_selected_identity_root_check.json'),manifest_publication=ref(B+'/Long_manifest_publication.json'),runtime_scientific_inputs=ref(B+'/Long_runtime_science_publication.json'),methods=16,engineering_shards=8,trials_per_shard=200,total_planned_trials=1600,unique_development_initial_states_per_method=100,author_CPU_tests=31,independent_checks=18,full_unfiltered_registered_jobs=259,new_action_contract_or_readiness_created=False,submission_authorized=False,new_trials=0,new_GPU_submissions=[],old_Long_trials_retained=600,old_Long_GPU_seconds_retained=10531,old_six_identity_migration_not_solved=True,required_before_any_submission=ind['required_before_any_submission']))
 canonreview=save(B+'/canonical_source_gate_root_acceptance.json',dict(schema='formal_main_v2',status='accepted_original_root_reconstruction_and_independent_source_gate',utc=now,reconstruction=ref(B+'/canonical_reconstruction_summary.json'),independent_source_gate=ref(B+'/packages/canonical_source_gate/source_gate_review.json'),reconstructed_pairs=7,downstream_source_gate_methods=14,new_full_training_independent_audit_claimed=False,original_independent_training_evidence_preserved=True,new_completed_training_groups=0,canonical_reviews=[x['canonical_review'] for x in canonical['results']]))
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_source_review_and_development_preparation',utc=now,observation_utc=ob['utc'],scheduler=ref(B+'/final_capacity_observation.json'),root_independent_complete=46,machine_and_prior_complete=ob['machine_and_prior_complete'],root_independent_updates=239000,root_training_complete_by_suite=dict(Long=18,Spatial=16,Object=10,Goal=2),allocated_GPU_seconds=ob['allocated_GPU_seconds'],allocated_GPU_hours=ob['allocated_GPU_hours'],cost_is_final=False,active_GPU_jobs=8,reserved_next_GPU_slots=1,reservation_is_not_additional_allocated_GPU=True,canonical_source_gate=canonreview,Long_development_preparation=prep,new_completed_training_groups=0,new_GPU_submissions=[],new_development_trials=0,completed_final_trials=0,final_release=False,normal_training_left_to_controller=True,server_only=True,frozen_files_unchanged=173,previous_verified_Git_commit='29292573896f1d9619c83f540a7a4be3a898e438',old_development_trials_retained=1212))
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now
 s['current_work']='46/72 root+independent completed;8 healthy GPUs observed. Rebuilt7 original terminal root reviews and independently verified14 downstream source gates. Long16 development science plans pass original planner and independent audit;8x200 planned trials remain HOLD_PRODUCTION pending exact new-action outer contracts/readiness. Next free slot remains reserved for exact Spatial64 seed23 CUDA recovery.'
 s['next_actions']=[
 'Normal controller continues auto5000 with at most8 GPUs; no healthy cancellation and no manual normal500 boundary.',
 'At the next actual free slot, root uses exact3028522 recovery fresh preflight and single authorization to1500; after genuine resume evidence, separately admit continuous5000.',
 'Create and independently review exact new-action outer contract/effective plan/readiness for each of the8 prepared Long A/B development shards before root one-use capacity-gated submission; original inner plans alone are not executable new-action authorization.',
 'Keep old Long6 execution identities and old1212 development results/costs. Prior Spatial mixed12+588 preparation remains historical HOLD_PRODUCTION; it does not satisfy whole-ancestry O2A/global freeze. Handle old6 identity migration explicitly without registry filtering, method renaming, or fabricated ledgers.',
 'Use reconstructed canonical reviews for remaining completed-selector development preparation. Keep O2A/final global release closed until all72 checkpoints,16 references,full4suite development receipts and exact runtime identities satisfy original gates.'
 ]
 s['next_allowed_action']=s['next_actions'][1]+' '+s['next_actions'][2]
 s['formal_main_progress']['latest_canonical_terminal_review_reconstruction']=canonreview
 s['formal_main_progress']['Long_remaining16_development_preparation']=prep
 s['formal_main_progress']['downstream_action_range_issue']['latest_execution_preparation']=prep
 assert s['registered_jobs']==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(sp,s,before)
 newdoc='docs/正式Long其余16选择器开发登记.md'
 content="""# 正式Long其余16选择器开发登记

2026-10-20 CST。范围仅为正式矩阵中尚无开发闭环的16个Long选择器，科学计划已通过作者31项CPU检查、独立18项检查和root复核；原规划器使用完整259条登记记录，无过滤。当前为 **HOLD_PRODUCTION**，没有新GPU提交、开发trial或成功率结论。

| 总token | 训练seed | 方法 | 开发trial |
| --- | --- | --- | --- |
| 128 | 23 | A、B | 200 |
| 128 | 41 | A、B | 200 |
| 256 | 17 | A、B | 200 |
| 256 | 23 | A、B | 200 |
| 256 | 41 | A、B | 200 |
| 64 | 17 | A、B | 200 |
| 64 | 23 | A、B | 200 |
| 64 | 41 | A、B | 200 |

各选择器沿用已训练5000步、按原11次validation选择的checkpoint。root核对了Long全部18个selected checkpoint的实际服务器字节；本轮没有重新训练、重新选模或修改方法ID。每方法使用同一固定10任务×10开发初态；16方法共1600条，不能当成1600个独立初态。面板路径为 configs/manifests/formal_main_v2/libero_10/initial_states/development.json，SHA256为46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268。模拟器seed0、runtime seed17、等待10步、chunk8、最大控制步520不变，最终40初态/任务仍封存。

8个A/B pair分片用于适配固定4小时Slurm资源。旧Long600条开发闭环合计10531 GPU秒，仅作实测资源参考，不保证新分片耗时。原600条、原身份与成本全部保留，原dense、3个uniform、A128seed17、B128seed17的新版动作身份迁移另行处理。当前16个方法没有原开发结果，属于原矩阵的缺项补齐；不重命名已有方法或改变账本来绕过重复运行检查。

8份科学manifest已发布至 results/formal_main_v2/execution/long_remaining16_action_v1_1722/。原规划器实际校验和独立重建全部通过；222个科学运行输入在P中逐SHA匹配，其中本轮按原字节补齐16个。下一步仍需每分片的新版动作外层contract、effective plan、readiness、准备调用及root一次性授权；本登记和旧版inner plan均不授权直接执行。运行前重新核实真实空槽、重复提交、已有产物与checkpoint身份；8卡上限包含工程作业，Spatial64seed23恢复的既有下一槽预约优先。

Spatial旧12条＋新588条混合续跑准备保留为历史且仍HOLD_PRODUCTION，不能据此通过整条执行历史的O2A/最终冻结门槛；不继续用该方案代替统一身份验收。全部旧1212条开发结果、失败及成本保留。本轮7对原始终态审计重建只恢复缺少的canonical收据，另经原下游接口独审14个方法；不增加已完成训练组数，也不冒称新增完整训练独审。

"""
 content+='[root准备验收](../'+B+'/Long_development_root_preparation.json)；[本轮总收据](../'+B+'/summary.json)；[终态来源验收](../'+B+'/canonical_source_gate_root_acceptance.json)。\n'
 assert not (R/newdoc).exists();(R/newdoc).write_text(content)
 changed=[dict(path=newdoc,before_sha256=None,after_sha256=h(R/newdoc))]
 note='2026-10-20 01:51 CST 快照：训练仍 **46/72组**（Long18、Spatial16、Object10、Goal2），**8卡运行，累计393.835 GPU小时**，含失败及运行中分配，非最终成本。本轮重建7对原终态root审计，原独审身份保留，14个方法通过实际下游来源门槛；没有新增训练完成量。Long其余16选择器已登记8×200条开发计划，通过作者31项和独立18项CPU检查，222个科学输入已核齐；新版动作外层及readiness仍待完成，尚未提交或产生新闭环。Spatial旧混合续跑准备保留，不作为完整身份验收。下一真实空槽继续优先已批准的Spatial64seed23 CUDA恢复；正常训练交控制器。最终0/35200封存。\n\n[Long开发登记](正式Long其余16选择器开发登记.md)；[本轮收据](../'+B+'/summary.json)。\n\n'
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式动作执行入口接入记录']:
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;prior=p.read_text();assert '2026-10-20 01:51 CST 快照' not in prior;first,tail=prior.split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+note+tail.lstrip('\n'));changed.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 ops=R/B/'root_operations';ops.mkdir(exist_ok=True)
 for name in ['observe_formal_1722.py','prepare_long_root_identities_1722.py','publish_Long_manifests_1722.py','publish_Long_manifests_1722_a2.py','reconstruct_canonical_reviews_1722.py','publish_Long_science_inputs_1722.py','archive_packages_1722.py','capacity_before_approved_recovery_1722.py','archive_packages_1722_second.py','integrate_1722.py']:
  with (ops/name).open('xb') as f:f.write((R/'.local'/name).read_bytes())
 with (R/B/'previous_Git_push_verified.json').open('xb') as f:f.write((R/'.local/github_push_1621_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(schema='formal_main_v2',state_before=before,state_after=h(sp),summary=summary,documentation=changed,source_and_science_unchanged=True,CPU_failures_retained=True,no_new_GPU_job=True,controller_and_registered_jobs_unchanged=True,cost_field_not_overwritten=True,engineering_notes=['Initial manifest publisher guard confused canonical JSON receipt signature with raw bytes; stopped before any manifest write; corrected exact original json_signature formula without scientific change.','Private audit transport path rejection and parser/finalizer failed attempts preserved in package mappings.','Independent finalizer saw initial16 missing P inputs already published by root; retained failure and distinguished prior snapshot from fresh exact222-input check; science tests not rerun or altered.']))
 print(json.dumps(dict(summary=summary,root_complete=46,observed_GPU=8,GPU_hours=ob['allocated_GPU_hours'],reserved_next_GPU=1,Long_development='HOLD_PRODUCTION',documents=len(changed))))
