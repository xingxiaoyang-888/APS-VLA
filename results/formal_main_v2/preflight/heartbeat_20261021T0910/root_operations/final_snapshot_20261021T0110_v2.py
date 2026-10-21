from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
B="results/formal_main_v2/preflight/heartbeat_20261021T0910";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0110";PREV="results/formal_main_v2/preflight/heartbeat_20261021T0758/final_summary.json"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x") as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
ap=argparse.ArgumentParser();ap.add_argument("--inputs-sha256",required=True);a=ap.parse_args()
assert h(R/B/"final_snapshot_inputs.json")==a.inputs_sha256;i=rd(B+"/final_snapshot_inputs.json")
assert i["schema"]=="formal_main_v2" and i["kind"]=="root_delivery_inputs"
for item in i["evidence"].values():assert h(R/item["path"])==item["sha256"],item
g=i["Goal_full200"];assert g["old200_adopted"] is False and g["old_cause_explained"] is False and g["new_development_accepted"]==0 and g["remaining1000_scientific_HOLD"] is True
o=rd(i["operation_observation"]["path"]);assert h(R/i["operation_observation"]["path"])==i["operation_observation"]["sha256"]
assert o["kind"]=="root_actual_operation_observation_projection" and o["new_queries"]==0 and o["source_receipt"] in list(i["evidence"].values())
obs=o["observation"];rows=obs["rows"];occupied=o["occupied"]
cp=R/"scripts/ops/formal_autonomous_training_v1/controller.py";assert h(cp)=="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363"
sp=importlib.util.spec_from_file_location("final_snapshot0910",cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 state_path=R/"results/experiment_supervisor/state.json";before=h(state_path);assert before==i["state_before_sha256"]
 s=rd("results/experiment_supervisor/state.json");f=s["formal_main_progress"];ctl=s["autonomous_training_v1"]
 assert s.get("pending_submission") is None and ctl.get("pending_submission") is None and ctl["reserved_GPU_slots"]==0 and ctl.get("root_submission_hold") is None
 assert (f["root_and_independent_completed_arms"],f["root_and_independent_reviewed_arm_updates"],f["current_action_development_trial_count"],f["completed_development_trials"],f["completed_final_trials"])==(72,360000,6388,7600,0)
 assert sum(x["completed_trials"] for x in f["new_action_development_verified_by_job"].values())==6388 and not f["test_opened"] and not f["global_release_created"]
 assert f["current_action_development_unique_initial_states"]==400 and f["complete_development_batches_accepted_trials"]==7000
 priorstate=rd(B+"/Spatial3054201_state_before.json");oldids={str(j["job_id"]) for j in priorstate["registered_jobs"]}
 formal=[j for j in s["registered_jobs"] if j.get("experiment")=="formal_main_v2"];ids=[str(j["job_id"]) for j in formal];assert len(ids)==len(set(ids)) and set(ids)<=set(rows)
 newids=sorted(set(ids)-oldids);assert newids==sorted(i["new_GPU_jobs"]) and "3054409" in newids and 1<=len(newids)<=2
 assert g.get("job_id") is None or g["job_id"] in newids
 cost=sum(rows[j]["elapsed_seconds"]*rows[j]["gpus"] for j in ids);assert cost==o["allocated_GPU_seconds"] and cost>=1992004
 assert rows["3034538"]["status"]=="COMPLETED" and rows["3034538"]["exit_code"]=="0:0" and o["controller_lease_released"]
 assert len(occupied)<=8 and set(occupied)<=set(ids)
 inv=rd("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json");assert len(inv["files"])==173
 for n,w in inv["files"].items():
  for root in [R,P/"snapshots/formal_main_v2_run_564be0995e",R/"snapshots/formal_main_v2_run_564be0995e"]:assert h(root/n)==w,n
 spatial=rd(B+"/Spatial3054201_root_acceptance.json");assert spatial["new_current_trials"]==588 and spatial["retained_legacy_compatible_trials"]==12 and spatial["complete_mixed_panel_trials"]==600
 prev=rd(PREV);summary=copy.deepcopy(prev);now=datetime.now(timezone.utc).isoformat()
 summary.update(utc=now,previous_snapshot=ref(PREV),root_completed_arms=72,root_completed_pairs=36,root_reviewed_arm_updates=360000,compatible_development_trials=7000,current_action_development_trials=6388,compatible_legacy_Long_trials=600,compatible_legacy_Spatial_trials=12,all_historical_accepted_development_trials=7600,unique_development_initial_states=400,new_unique_initial_states=0,new_development_accepted=588,new_GPU_jobs=newids,registered_formal_allocations=len(ids),allocated_GPU_seconds=cost,allocated_GPU_hours=cost/3600,newly_accounted_GPU_seconds=cost-prev["allocated_GPU_seconds"],cost_observed_utc=o["utc"],cost_basis=ref(i["operation_observation"]["path"]),cost_final_for_current_registered_set=not occupied,capacity=dict(occupied=occupied,unknown=[],findings=[]),active_registered_GPU_jobs=occupied,actual_running_allocated_GPUs=sum(rows[j]["gpus"] for j in occupied if rows[j]["status"]=="RUNNING"),engineering_evidence_manifests=i["evidence"],Goal_full200=g)
 summary["Spatial588"]=dict(job_id="3054201",status_at_last_observation=rows["3054201"]["status"],root_and_independent_terminal_accepted=True,completed_new_trials_accepted=588,legacy_compatible_trials=12,complete_mixed_panel_trials=600,origin_breakdown=spatial["origin_breakdown"],cost_GPU_seconds=7030,current_allocation_GPU_seconds=6635,root_acceptance=ref(B+"/Spatial3054201_root_acceptance.json"),independent_review=spatial["independent_review"],profiling_authorized=False,final_release=False)
 summary["Object599"].update(legacy599_root_adopted=True,whole600_production_adopted=False,production_runtime_installed=True,single_failure_GPU_authorized=True,single_failure_job_id="3054409",single_failure_status_at_last_observation=rows["3054409"]["status"],new_trial_accepted=False)
 summary["Object_single_error_linked_attempt"]=i["Object_linked_attempt"];summary["Object_single_error_linked_attempt"].update(status_at_last_observation=rows["3054409"]["status"],elapsed_GPU_seconds_at_last_observation=rows["3054409"]["elapsed_seconds"]*rows["3054409"]["gpus"],scientific_terminal_not_yet_accepted=True)
 summary["Goal_original200_and_new_science_HOLD"]=True;summary["Goal_original200_and_remaining1000_HOLD"]=True
 summary["accepted_count_basis"]="7000 complete development-batch rows =6388 current+600 compatible Long+12 compatible Spatial. Object599 adopted legacy rows remain separate pending the one linked correction and typed whole600 terminal review. Historical7600 is the retained historical acceptance catalog, not the current full-batch denominator."
 summary["next_actions"]=i["next_actions"];summary["O2A_released"]=False;summary["global_release"]=False;summary["final_sealed"]=True
 save(B+"/final_summary.json",summary);last=ref(B+"/final_summary.json");s["last_root_supervision_snapshot"]=last
 s["current_round_cost"]=dict(registered_jobs=len(ids),allocated_gpu_seconds=cost,allocated_gpu_hours=cost/3600,final=not occupied,historical_jobs_excluded=True,scope="All"+str(len(ids))+" unique formal allocations observed "+o["utc"]+"; active allocations are lower bounds, each allocation updated once including all setup/cache/failure/engineering costs.",observation=ref(i["operation_observation"]["path"]))
 ctl["occupied_job_ids"]=occupied
 f["parallel_execution"].update(actual_running_allocated_GPUs=summary["actual_running_allocated_GPUs"],registered_requested_active_GPU_jobs=len(occupied),status="training_complete_downstream_exact_repairs",latest_root_observation=ref(i["operation_observation"]["path"]))
 f["downstream_followups_20261021T0110"]=dict(summary=last,Spatial588_accepted=True,Object3054409=i["Object_linked_attempt"],Goal_full200=g,O2A_released=False,global_release=False)
 s["updated_utc"]=now;s["last_supervision_utc"]=now;s["current_work"]="Training72/72 done;complete accepted development7000/8800,400 unique;Object linked attempt and Goal full200 gates;final sealed."
 s["next_actions"]=i["next_actions"];s["next_allowed_action"]=i["next_actions"][0]
 title="## 2026-10-21 09:10监督交付（实际UTC "+now+"）"
 common=f"""{title}

正式训练72/72组、36pair、360000更新保持完成。Spatial3054201新增588条已通过原类型化consumer和不同代理原始终验；与原3022743的12条兼容历史来源组成600条，分开记录。完整开发批次现6388 current＋Long600兼容＋Spatial12兼容＝7000/8800条，仍为400个唯一初态，没有新增独立样本。历史已验收目录7600条与全部失败原尝试保留，不当作当前完整批次分母。Object599仍单列legacy采用，不预记完整600。

Spatial新作业6635 GPU秒，连同原393秒和前置失败2秒共7030秒。Object3054409只提交一次：原ACK后即时记账延迟和release后的状态传播差异均保留，按唯一原ACK对账，没有重复submit或release；本轮尚不预记新单条结果。{len(ids)}个唯一正式分配在{o["utc"]}累计{cost} GPU秒（{cost/3600:.6f}小时），当时{len(occupied)}个活动GPU；活动作业成本是截面下界，同allocation更新，不重复相加。

{i["Goal_markdown"]}

所有新内容仅服务器保存并按精确非权重清单同步GitHub；173冻结文件、科学配置和选模checkpoint不变。完整O2A/独立分项计时仍等待88身份、四套件完整开发收据及最终清单冻结；最终0/35200封存，未创建global release，不把开发成功率或工程时延当最终有效性或加速结论。

证据：[本轮汇总](../{B}/final_summary.json)；[下游登记](正式下游阻塞登记_20261021T0110.md)。

"""
 changes={}
 for name in ["正式主实验规划","完整实验计划","实验进度","正式主实验阶段结论","正式自动连续训练执行登记","研究方案"]:
  rel="docs/"+name+".md";assert rel not in inv["files"];p=R/rel;raw=p.read_bytes();assert title.encode() not in raw
  p.write_bytes((common+raw.decode().lstrip("\n")).rstrip().encode()+b"\n");changes[rel]=dict(before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=h(p))
 rel="docs/论文方法与实验设置草稿.md";p=R/rel;raw=p.read_bytes()
 note="2026-10-21执行记录：72组训练终验完成，完整开发验收7000/8800；其余开发验收、同checkpoint完整O2A和封存最终结果尚未交付。Spatial588新条目与12兼容历史条目分开；Object原policy_error及Goal旧200差异均不删除或追溯认定修复。详情见[最新下游登记](正式下游阻塞登记_20261021T0110.md)。开发数字不填入最终主表。\n\n"
 p.write_bytes((note+raw.decode().lstrip("\n")).rstrip().encode()+b"\n");changes[rel]=dict(before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=h(p))
 rel="docs/正式下游阻塞登记_20261021T0110.md";assert not (R/rel).exists();(R/rel).write_text(("# 正式下游阻塞登记 20261021T0110\n\n"+common+i["blocker_details_markdown"]).rstrip()+"\n")
 c.atomic_json(state_path,s,expected_sha=before)
 receipt=dict(status="root_delivery_snapshot_updated",state_before=before,state_after=h(state_path),summary=last,document_changes=changes,new_blocker_document=ref(rel),source173_verified=True,new_GPU_jobs=newids,new_development_accepted=588,final_sealed=True)
 save(B+"/state_and_document_update.json",receipt);print(json.dumps(dict(status="ready_for_final_independent_review",summary=last,state_sha256=h(state_path),new_GPU_jobs=newids,dev_complete_batch_rows=7000,GPU_seconds=cost)))
