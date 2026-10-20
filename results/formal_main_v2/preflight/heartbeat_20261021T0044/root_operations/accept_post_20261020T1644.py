from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode()
def put(p,b):
 assert p.is_relative_to(R) and not any(v.is_symlink() for v in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
def checked(rr):assert h(R/rr['path'])==rr['sha256'];return json.loads((R/rr['path']).read_bytes())
ap=argparse.ArgumentParser();ap.add_argument('--post-review',required=True);ap.add_argument('--post-review-sha256',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args()
pr=dict(path=a.post_review,sha256=a.post_review_sha256);review=checked(pr);mr=dict(path=a.manifest,sha256=a.manifest_sha256);manifest=checked(mr)
assert review['status']=='passed' and review['canonical_state_docs_Git_Slurm_mutated'] is False and review['all173_R_S_unchanged']
assert review['result']['completed_arms']==68 and review['result']['reviewed_updates']==341000 and review['result']['dev_current']==4400 and review['result']['final_trials']==0
private=R/Path(a.manifest).parent;rows=manifest['files'];assert isinstance(rows,list);source_paths=set()
for row in rows:
 p=R/row['path'];assert p.is_relative_to(private) and h(p)==row['sha256'] and p.stat().st_size==row['bytes'];source_paths.add(p)
assert {p for p in private.rglob('*') if p.is_file()}==source_paths|{R/a.manifest}
forensic_ref=dict(path=E+'/Goal_t0_forensic/report.json',sha256='44f959a0d6cf18db62435371eecbfd5ae184d3489305a62f000d2a2856b04a3f')
forensic=checked(forensic_ref);assert forensic['cause']=='undetermined' and forensic['original200_HOLD_unchanged'] and forensic['new_GPU_jobs']==0 and forensic['checks_passed']==836
object_ref=dict(path=E+'/Object_source_bridge_independent/attempt02/independent_review.json',sha256='5af9969323f0b2af76bc4f396be740bfa89d8211f792d91d2e457bd805559347')
ob=checked(object_ref);assert ob['status']=='passed_CPU_source_bridge_pending_explicit_root_integration' and not ob['production_gateway_ready'] and not ob['production_terminal_consumer_ready'] and ob['all_pair_GPU_seconds']==58917
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('finalCrosscheck1644',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before_sha=h(state);s=json.loads(state.read_bytes());old=copy.deepcopy(s);f=s['formal_main_progress'];key='supervision_integrity_review_20261020T1644'
 assert f[key]['status']=='pending_post_integration_crosscheck' and f['root_and_independent_completed_arms']==68 and f['root_and_independent_reviewed_arm_updates']==341000
 assert f['current_action_development_trial_count']==4400 and f['completed_development_trials']==5612 and not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0
 assert s['pending_submission'] is None and s['autonomous_training_v1']['root_submission_hold'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 summary=dict(path=B+'/summary.json',sha256='c2db3e60218e486bae15faa5f7480527379f9525deea893ac2fc13038bbf11f6');checked(summary);assert s['last_root_supervision_snapshot']==summary and review['actual_summary']==summary
 copies=[]
 for p in sorted(source_paths|{R/a.manifest}):
  assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5');dst=R/E/'Goal64s41_integration_independent'/p.relative_to(private);put(dst,p.read_bytes());copies.append(dict(source=ref(p),archive=ref(dst)))
 ar=dict(path=(R/E/'Goal64s41_integration_independent'/(R/a.post_review).relative_to(private)).relative_to(R).as_posix(),sha256=a.post_review_sha256)
 followups=dict(schema='formal_main_v2',status='bounded_CPU_findings_no_new_GPU_submission',training_complete_root_independent=68,Goal_forensic=forensic_ref,Goal_new_scientific_development='HOLD_until_cause_and_bounded_engineering_accepted',Goal_original_trials_on_HOLD=200,Goal_cause='undetermined',Goal_prefix58_diagnostic_draft=dict(path=E+'/Goal_t0_forensic/proposed_single_attempt_registration.json',sha256='5bff6f45968d03978f2928e2c230a20a4503fa78be1b67cf59034d2ebdddf112'),Goal_prefix58_executed=False,Object_source_candidate_independent=object_ref,Object_production_binding='private_candidate_in_progress_not_admitted',new_GPU_jobs=0,new_development_accepted=0,final_sealed=True,final_release=False)
 out=R/B/'downstream_followups.json';put(out,enc(followups))
 doc='''# 正式下游工程与开发登记

本轮训练验收增至68/72组：Goal64 seed41 A/B各5000步、11次完整验证；A选择3500步、B选择3000步。59575 GPU秒已在总账，不重复计费。初次核对的6个GPU作业及548.415 GPU小时仅代表该时点，健康作业由自动控制器继续运行；本轮未新增开发结果或GPU提交。

当前动作语义已验收4400条，另有明确兼容的Long600条，合计5000条、400个唯一开发初态。此前4个Spatial/Object64作业计划800条仍待真实终态及独立审计，不算已验收。最终0/35200继续封存，不能形成最终成功率或完整加速结论。

## Goal原200条保持HOLD

取证明确异常在原第57/58条开发试验，之前已有56条试验、916次策略查询、7124个策略动作。原执行和短探针均逐trial重设seed并新建环境；原t0哈希在predict_chunk返回后记录。短探针仅12次查询、120个等待动作，未覆盖前序策略执行历史。

短探针B首动作与原B一致；A的token集合及元数据相同，但最大动作差为环境动作0.0035470、归一化动作0.00390625。以上只能描述观测到的差异，不能证明原记录正确、模型修改输入或历史依赖是原因。此前“history-dependent”的推断予以收窄：异常出现在更长执行历史中，依赖性未证实。原200条保留且不计分；整个Goal新增科学开发继续暂停。

下一候选只登记为工程草案：保持原前58条身份/顺序、原checkpoint及闭环语义，捕获reset/等待/query前后输入与RNG。最多1GPU、30分钟、单次，计入8槽，未运行。它不是强制回放原动作；若不复现仍HOLD。观察器实现、语义差分、root与独立验收完成前不提交，也不自动重跑科学试验。

## Object256 seed23来源兼容

来源桥CPU独审通过，保留3028460失败84 GPU秒及全pair58917 GPU秒，科学manifest逐字节相同。该结果只准许继续显式控制层集成：正式gateway重建、source闭包、terminal consumer、实际checkpoint及双审readiness仍须全部绑定。当前生产接入为私有候选，尚未准入或提交。禁止伪造成功metadata或绕过原失败记录。

[本轮训练收据](../'''+B+'''/summary.json) · [边界与候选登记](../'''+B+'''/downstream_followups.json) · [完整非权重证据](../'''+B+'''/evidence_delivery_initial.json)
'''
 put(R/'docs/正式下游阻塞登记_20261020T1644.md',doc.encode())
 receipt=dict(schema='formal_main_v2',status='passed',summary=summary,independent_review=ar,private_independent_review=pr,root_completed_arms=68,reviewed_arm_updates=341000,current_action_development_trials=4400,compatible_development_trials=5000,Goal_original_trials_on_HOLD=200,Goal_new_development_on_HOLD=True,Object_production_bridge_admitted=False,observation_cost_not_readded=True,controller_and_registry_preserved=True,new_GPU_jobs=0,new_development_accepted=0,final_sealed=True,followups=ref(out),copies=copies,utc=datetime.now(timezone.utc).isoformat())
 rp=R/B/'root_post_integration_acceptance.json';put(rp,enc(receipt))
 f[key]=dict(status='passed',summary=summary,independent_review=ar,root_acceptance=dict(path=rp.relative_to(R).as_posix(),sha256=h(rp)),scientific_gate_changed=False)
 f['downstream_followups_20261020T1644']=dict(path=out.relative_to(R).as_posix(),sha256=h(out))
 s['updated_utc']=receipt['utc']
 for k in old:
  if k not in ('formal_main_progress','updated_utc'):assert old[k]==s[k],k
 for k in old['formal_main_progress']:
  if k!=key:assert old['formal_main_progress'][k]==f[k],k
 c.atomic_json(state,s,before_sha)
 print(json.dumps(dict(status='passed_68_of72_post_crosscheck',receipt=ref(rp),post_independent=ar,followups=ref(out))),flush=True)
