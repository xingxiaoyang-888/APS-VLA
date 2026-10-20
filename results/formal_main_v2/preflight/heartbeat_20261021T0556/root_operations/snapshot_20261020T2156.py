from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,fcntl,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0556';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2156'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def save(n,x):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def load(n,pin,name):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--statistics-review',required=True);ap.add_argument('--statistics-review-sha256',required=True);a=ap.parse_args()
 assert h(R/a.statistics_review)==a.statistics_review_sha256
 st=rd(a.statistics_review);assert st['status']=='passed' and not st.get('blockers') and st['root_statistics_sha256']=='d327e603eb76790d1dd30f4f6cdd9b5364121343eb01cd65298cf31c1959926d'
 c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','snap2156c')
 g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','snap2156g')
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');f=s['formal_main_progress'];ctl=s['autonomous_training_v1'];oldscience=copy.deepcopy(f)
  sciencekeys=['root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','current_action_development_trial_count','completed_development_trials','completed_final_trials','test_opened','global_release_created']
  assert tuple(f[k] for k in sciencekeys)==(72,360000,5800,7012,0,False,False)
  assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
  obs=c.Slurm(timeout=60).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
  assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8
  for job in s['registered_jobs']:g.check_observed_identity(job,obs['rows'][str(job['job_id'])],obs['queue'].get(str(job['job_id'])),c.TERMINAL)
  assert obs['rows']['3034538']['status']=='COMPLETED' and obs['rows']['3034538']['exit_code']=='0:0' and obs['rows']['3034538']['gpus']==0
  with (R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock').open('rb') as z:fcntl.flock(z,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(z,fcntl.LOCK_UN)
  formal=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];assert len({str(j['job_id']) for j in formal})==len(formal)
  secs=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in formal)
  for n,pin in [(E+'/Goal_author/author_report.json','91c9e3db7269883c1e2f81687c091e50a7b1d27a8e64a319701960cb12d7a773'),(E+'/Spatial_independent/independent_review.json','3cb7efa91ebbdb42c8ae91afef2f34ade5b237ee169a369a721353b0840bbf50'),(B+'/Spatial_Object64_three_seed_development_statistics.json','d327e603eb76790d1dd30f4f6cdd9b5364121343eb01cd65298cf31c1959926d')]:assert h(R/n)==pin
  receipt=B+'/Goal_paired_dispatch/receipt.json';go=rd(receipt);assert go['status']=='registered_and_release_verified' and go['scientific_release'] is False
  jid=go['job_id'];job=next(j for j in formal if str(j['job_id'])==jid);actual=obs['rows'][jid];assert job['stage_key']=='goal_paired_input_gate_20261020T2156' and job['mode']=='engineering' and actual['gpus']==1
  job['status']=actual['status'];ctl['occupied_job_ids']=cap['occupied'];utc=datetime.now(timezone.utc).isoformat()
  evidence=dict(Goal=ref(E+'/Goal_author/author_report.json'),Spatial=ref(E+'/Spatial_independent/independent_review.json'),Object=ref(E+'/Object_author/stage1_delivery_manifest_original.json'))
  nxt=['Review the single Goal paired-input engineering terminal evidence; old Goal200/new science stay HOLD.','Finish exact Spatial588 source control, root adoption/repair, new gateway and actual-P readiness.','Independently audit Object599 compatibility and a separately linked single failed-trial repair.','Complete four-suite development and global identity freeze before O2A/components/final release.']
  summary=dict(schema='formal_main_v2',status='posttraining_engineering_and_CPU_compatibility_progress',utc=utc,state_before_sha256=before,training_arms=72,training_pairs=36,reviewed_arm_updates=360000,current_action_development_trials=5800,compatible_legacy_Long_trials=600,compatible_development_trials=6400,planned_development_trials=8800,all_historical_accepted_development_trials=7012,new_development_accepted=0,new_unique_initial_states=0,unique_development_initial_states=400,accepted_fixed_observations_including_Long=90,final_trials=0,final_total=35200,final_sealed=True,global_release=False,O2A_released=False,controller_completed_normally=True,controller_lease_released=True,controller_restarted=False,registered_formal_allocations=len(formal),allocated_GPU_seconds=secs,allocated_GPU_hours=secs/3600,newly_accounted_GPU_seconds=secs-1984462,cost_final_for_current_registered_set=not cap['occupied'],new_GPU_jobs=[jid],active_registered_GPU_jobs=cap['occupied'],capacity=cap,observation=obs,Goal_paired_input_engineering=dict(job_id=jid,status=actual['status'],elapsed_GPU_seconds=actual['elapsed_seconds'],maximum_trials=58,scientific_trials_added=0,terminal_evidence_reviewed=False,dispatch=ref(receipt)),Goal_original200_and_new_science_HOLD=True,Spatial_legacy12_compatibility_evidence_independently_passed=True,Spatial_legacy12_production_adopted=False,Spatial588_new_GPU_submission=False,Object599_author_compatibility_passed=True,Object599_compatibility_adopted=False,Object_original_policy_error_retained=True,engineering_CPU_evidence=evidence,development_k64_statistics=ref(B+'/Spatial_Object64_three_seed_development_statistics.json'),development_k64_statistics_independent=ref(a.statistics_review),scientific_effect_conclusion='Development-only k64 three-seed means: Spatial B-A=0pp; Object=-0.666667pp. No final effectiveness/equivalence/speedup conclusion.',frozen_source_files_unchanged=173,all_project_writes_server_only=True,unaccepted_original_attempts_retained=True,next_actions=nxt)
  save(B+'/final_summary.json',summary);sr=ref(B+'/final_summary.json')
  f['Goal_paired_input_engineering_registration']=dict(status='awaiting_terminal_evidence_review' if actual['status'] in c.TERMINAL else 'registered_single_engineering_attempt_running_or_pending',job_id=jid,source_registration=ref(receipt),maximum_attempts=1,maximum_trials=58,automatic_retry=False,old200_and_new_science_HOLD=True,scientific_trials_added=0)
  f['latest_posttraining_CPU_evidence']=evidence;f['latest_k64_development_diagnostic']=dict(statistics=summary['development_k64_statistics'],independent_review=summary['development_k64_statistics_independent'],unique_initial_states_per_suite=100,final_result=False)
  s['current_round_cost']=dict(allocated_gpu_hours=secs/3600,allocated_gpu_seconds=secs,final=not cap['occupied'],historical_jobs_excluded=True,registered_jobs=len(formal),scope='All registered formal_main_v2 allocations once, including loading/cache/engineering/failures; active allocation elapsed usage only.')
  s.update(last_root_supervision_snapshot=sr,last_supervision_utc=utc,updated_utc=utc,current_work='Posttraining development and bounded engineering; training72 complete, final sealed.',next_actions=nxt,next_allowed_action='Review existing Goal terminal evidence and complete exact Spatial/Object recovery gates; no duplicate submission.')
  assert all(f[k]==oldscience[k] for k in sciencekeys);c.atomic_json(sp,s,before)
  ptext='\n## 2026-10-21 05:56监督交付（实际UTC '+utc+'）\n\n正式训练72/72、360000更新完成；当前动作5800＋明确兼容Long600＝6400/8800开发条目，400唯一开发初态。最终0/35200继续封存。\n\n本轮单次Goal成对输入工程作业 '+jid+' 已登记，快照状态 '+actual['status']+'；最多58条原开发前缀，旧Goal200与新增Goal科学结果仍HOLD。Spatial旧12兼容证据通过独审，588恢复入口仍待精确集成；Object599作者证明完成，原1条policy_error保留，兼容接纳与显式修复尝试待审。\n\n64-token三seed开发均值经独审：Spatial A/B均96.33%，B−A=0pp（配对簇bootstrap95%区间−1.33至1.00pp）；Object A97.00%、B96.33%，差−0.67pp（−2.00至0.67pp）。每套件仍仅100个唯一开发初态；不是最终效果、等效或加速证据。\n\n当前登记'+str(len(formal))+'个分配，累计'+str(secs)+' GPU秒（'+format(secs/3600,'.6f')+'小时），活动GPU作业'+str(len(cap['occupied']))+'。完整O2A/分项计时未放行。证据只写服务器，原始失败与CPU工程记录完整保留。\n\n证据：'+B+'/final_summary.json；细则见 docs/正式下游阻塞登记_20261020T2156.md。\n'
  docs=['docs/'+n+'.md' for n in ['正式主实验规划','完整实验计划','实验进度','正式主实验阶段结论','正式自动连续训练执行登记']]
  for n in docs:
   p=R/n;old=p.read_text();assert '2026-10-21 05:56监督交付' not in old;p.write_text(ptext+'\n'+old)
  block='# 正式下游阻塞登记 20261020T2156\n'+ptext+'\n- Goal：新增调用前配对和每query前后输入完整性检查，单次工程验收；不是旧历史精确重放。增加跨模式Goal活动作业拒绝门槛及完整原始记录磁盘余量门槛。policy_error、输入差异或观察器异常保留后终止，不自动重跑。\n- Spatial：3022743执行12条393GPU秒；3042529前置失败2秒无adapter/ledger，395秒分开记。12 legacy与未来588 current分别标来源，CPU证明不代替新生产链验收。\n- Object：599正常完成和1原policy_error均保留；被拒chunk未知，不推断。修复须绑定原失败，不能普通resume静默跳过terminal错误。\n- 四套件完整开发收据与72 checkpoint/16参考身份/最终清单冻结后才测速，root全局release后才开启35200 final。当前均未放行。\n'
  n='docs/正式下游阻塞登记_20261020T2156.md';assert not (R/n).exists();(R/n).write_text(block)
  save(B+'/state_and_document_update.json',dict(status='updated_under_writer_lock_and_CAS',state_before_sha256=before,state_after_sha256=h(sp),summary=sr,documents=[ref(n) for n in docs+[n]],new_GPU_jobs=[jid],new_scientific_trials=0))
  print(json.dumps({k:summary[k] for k in ['training_arms','compatible_development_trials','new_GPU_jobs','active_registered_GPU_jobs','allocated_GPU_hours','final_sealed','utc']}))
if __name__=='__main__':main()
