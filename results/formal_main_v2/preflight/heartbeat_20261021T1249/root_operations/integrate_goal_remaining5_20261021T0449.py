from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,json,hashlib,importlib.util,sys,os,copy
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");B="results/formal_main_v2/preflight/heartbeat_20261021T1249";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
ST="58e4ff5cd74c07c667a942119d2ed2de80059efb294ad8f21d192cdbe14bdac7";STATE="results/experiment_supervisor/state.json"
OLD="results/formal_main_v2/preflight/heartbeat_20261021T1134/final_summary.json"
OBS=B+"/post_dispatch_observation.json";OSHA="2bfccdc44ce0fd488be0d50bc76092aa071c07517d8ae9dccee2160e5bb6fcd2"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
def rd(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_bytes())
def put(n,b):
 p=R/n;assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(n,v):put(n,(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode());return ref(n)
def package(src,pin,dst):
 mb=(R/src/"delivery_manifest.json").read_bytes();assert hashlib.sha256(mb).hexdigest()==pin
 seen=set();rows=[]
 for r in json.loads(mb)["files"]:
  n=r["path"];n=n[len(src)+1:] if n.startswith(src+"/") else n
  p=PurePosixPath(n);assert not p.is_absolute() and ".." not in p.parts and n not in seen;seen.add(n)
  b=(R/src/n).read_bytes();assert len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]
  rows.append((n,b))
 assert not (R/dst).exists()
 for n,b in rows:put(dst+"/"+n,b)
 put(dst+"/delivery_manifest_original.json",mb)
 save(dst+"/source_map.json",dict(source_root=src,manifest_sha256=pin,files=[dict(source=src+"/"+n,**ref(dst+"/"+n)) for n,b in rows]))
def module(n,pin,name):
 p=R/n;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument("--ack-manifest-sha256",required=True);ap.add_argument("--ack-report-sha256",required=True);a=ap.parse_args()
assert os.environ.get("CTI_SERVER_CONTROL_ROOT")==str(R)
private=".local/goal_remaining5_ACK_independent_20261021T0449"
ar=rd(private+"/independent_review.json",a.ack_report_sha256)
assert str(ar["status"]).startswith("passed") and ar.get("blockers")==[]
c=module("scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","integrate_r5_ctl")
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 before=(R/STATE).read_bytes();assert hashlib.sha256(before).hexdigest()==ST
 s=json.loads(before);p=s["formal_main_progress"];obs=rd(OBS,OSHA);assert obs["state_sha256"]==ST
 assert s["pending_submission"] is None and s["autonomous_training_v1"]["reserved_GPU_slots"]==0
 package(private,a.ack_manifest_sha256,E+"/Goal_ACK_independent")
 assert p["root_and_independent_completed_arms"]==72 and p["complete_development_batches_accepted_trials"]==7800 and p["completed_final_trials"]==0
 keys={"libero_goal_k256_seed23":"3057505","libero_goal_k256_seed41":"3057510","libero_goal_k64_seed17":"3057515","libero_goal_k64_seed23":"3057526","libero_goal_k64_seed41":"3057533"}
 assert {j["pair_key"]:j["job_id"] for j in obs["new_jobs"]}==keys
 assert set(obs["capacity"]["occupied"])==set(keys.values()) and obs["formal_GPU_seconds"]==1995402 and obs["formal_unique_allocations"]==278
 assert all(j["row"]["status"]=="RUNNING" and j["row"]["gpus"]==1 for j in obs["new_jobs"])
 registrations=[]
 for key,jid in keys.items():
  x="results/formal_main_v2/execution/goal_remaining5_v1/"+key
  ack=rd(x+"/dispatch_attempt01/sbatch_result.json");commit=rd(x+"/dispatch_attempt01/committed.json");release=rd(x+"/dispatch_attempt01/release_result.json")
  assert ack["stdout"]==jid+"\n" and ack["returncode"]==release["returncode"]==0 and commit["job_id"]==jid
  j=next(j for j in s["registered_jobs"] if j["job_id"]==jid);row=obs["observation"]["rows"][jid]
  for name in ("status","exit_code","elapsed_seconds","allocation","node"):j[name]=row[name]
  registrations.append(dict(pair_key=key,pair_id=j["pair_id"],job_id=jid,method_ids=j["method_ids"],training_seed=j["training_seed"],tokens=j["visual_tokens"],observed_status=row["status"],planned_trials=200,completed_trials_accepted=0,unique_development_states=100,scientific_terminal_acceptance_pending=True,maximum_attempts=1,automatic_retry=False,authorization=ref(x+"/root_authorization.json"),admission=ref(x+"/dispatch_admission.json"),original_ACK=ref(x+"/dispatch_attempt01/sbatch_result.json"),original_accounting_delay=ref(x+"/dispatch_attempt01/failed_transaction.json"),held_dispatch=ref(x+"/held_dispatch_record.json"),committed=ref(x+"/dispatch_attempt01/committed.json"),independent_submission_review=ref(E+"/Goal_ACK_independent/independent_review.json"),raw_root=str(R/"results/formal_main_v2/raw_runtime/goal_remaining5_v1"/key/"attempt01"),attempt_root=j["attempt_root"]))
 save(B+"/Goal_remaining5_submissions_root_receipt.json",dict(schema="formal_main_v2",status="five_single_attempts_registered_released_running_at_saved_observation",jobs=registrations,observation=ref(OBS),independent_submission_review=ref(E+"/Goal_ACK_independent/independent_review.json"),new_scientific_trials_accepted=0,duplicate_submissions=0,release_count_per_job=1,all_first_sacct_delays_retained=True))
 oldcost=copy.deepcopy(s["current_round_cost"])
 s["current_round_cost"].update(registered_jobs=278,allocated_gpu_seconds=1995402,allocated_gpu_hours=1995402/3600,final=False,observation=ref(OBS),scope="All278 unique formal allocations once each at saved UTC "+obs["utc"]+"; five RUNNING single-GPU allocations included as elapsed lower bounds, not final cost or parallel wall-clock estimate.")
 p["parallel_execution"].update(status="training_complete_remaining5_Goal_development_running",registered_requested_active_GPU_jobs=5,actual_running_allocated_GPUs=5,active_registered_GPU_jobs=list(keys.values()),latest_registered_job_observation=ref(OBS))
 s["autonomous_training_v1"]["occupied_job_ids"]=list(keys.values())
 p["Goal_remaining5_development_registration_20261021T0449"]=registrations
 p["downstream_followups_20261021T0449"]={"Goal_remaining1000":"five_exact_jobs_running_pending_terminal_review_no_resubmit","Goal_fixed30":"CPU_design_only_not_collected","Goal_old200":"HOLD_cause_unresolved_not_retroactively_accepted","runtime_independent":ref(E+"/Goal_runtime_independent/independent_review.json"),"dispatch_independent":ref(E+"/Goal_gateway_independent/independent_review.json"),"Goal30_design":ref(E+"/Goal_fixed30_design/Goal_fixed30_design.json"),"source_manifest":ref("scripts/ops/formal_goal_remaining5_gate_v1/package_manifest.json"),"submission_receipt":ref(B+"/Goal_remaining5_submissions_root_receipt.json"),"new_trials_accepted":0,"O2A_released":False,"final_release":False}
 summary=rd(OLD,"35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02")
 summary.update(utc=datetime.now(timezone.utc).isoformat(),previous_snapshot=ref(OLD),source_state_before_sha256=ST,Goal_remaining1000_HOLD=False,Goal_remaining1000_acceptance_pending=True,Goal_remaining5_submissions=ref(B+"/Goal_remaining5_submissions_root_receipt.json"),Goal_fixed30_design=ref(E+"/Goal_fixed30_design/Goal_fixed30_design.json"),active_registered_GPU_jobs=list(keys.values()),actual_running_allocated_GPUs=5,registered_formal_allocations=278,allocated_GPU_seconds=1995402,allocated_GPU_hours=1995402/3600,capacity=obs["capacity"],cost_basis=ref(OBS),cost_observed_utc=obs["utc"],cost_final_for_current_registered_set=False,new_GPU_jobs=list(keys.values()),new_complete_batch_rows_accepted=0,new_current_development_trials_accepted=0,new_legacy_rows_entering_complete_batch_view=0,new_unique_initial_states=0,newly_accounted_GPU_seconds=1995402-1994468)
 summary["next_actions"]=["按原5个ACK核终态，逐pair由新typed consumer完整复建200条、双根原始输入/动作与原consumer，再独立终审和精确非权重归档；不重复提交或自动重跑。","完成Goal自身固定30开发观测的新精确采集计划/入口/独审/actualP/单次提交门槛；原90观测不重采。","全部72checkpoint、16参考身份、四套件完整开发收据及最终清单冻结后再做同checkpoint完整O2A与分项计时；root全局release前35200最终试验保持封存。"]
 save(B+"/final_summary.json",summary);put(B+"/dispatch_supervisor_snapshot_before.json",before)
 s["last_root_supervision_snapshot"]=ref(B+"/final_summary.json");c.atomic_json(R/STATE,s,ST)
 text=("## 2026-10-21 14:11 CST：Goal剩余五配对已单次放行\n\n"
 "训练72/72组、36pair、360000更新的原root+独立终验保持完成。开发已验收仍7800/8800（6589 current + Long600、Spatial12、Object599兼容历史），400唯一初态；本轮新增验收0。\n\n"
 "Goal 256 seed23/41与64 seed17/23/41各固定100开发初态×A/B200条，单次提交3057505、3057510、3057515、3057526、3057533。UTC "+obs["utc"]+"保存观察均RUNNING：5请求槽/5实分GPU、无pending/reserve/hold。首次Slurm即时记账缺行均按唯一原ACK补登记，submit/release各一次，保留失败收据。278唯一正式分配累计1995402 GPU秒=554.278333小时，为在运下界，不是终值或并行墙钟。\n\n"
 "新五pair入口通过原计划/选模/来源复建、1365作者CPU检查、1970项不同代理独审、5次actual P来源/身份/容量检查及原子提交独审。这些是工程准入，科学终验仍待原始记录；旧专用入口未泛化，173冻结源不改。被动观测及RNG/环境payload写R独立raw目录，P保留原科学ledger与有界metadata，完整五pair容量计账，运行中raw不入Git。\n\n"
 "Goal固定30观测仅完成CPU设计：原登记最低source索引[7,2,3,4,4,1,10,1,4,9]，Dense512轨迹首中末，尚未采集。另三套件原90观测不重采。Goal旧200继续HOLD且旧原因未明。O2A/global release未开放，final仍0/35200。\n\n"
 "证据：[本轮快照](../"+B+"/final_summary.json)、[单ACK登记](../"+B+"/Goal_remaining5_submissions_root_receipt.json)、[下游门槛](正式下游阻塞登记_20261021T0449.md)。正常作业留后续监督，不持续轮询。\n\n")
 docs={}
 for n in ["docs/正式主实验规划.md","docs/完整实验计划.md","docs/实验进度.md","docs/正式主实验阶段结论.md"]:
  old=(R/n).read_bytes();assert text.encode() not in old;docs[n]={"before_sha256":hashlib.sha256(old).hexdigest()}
  (R/n).write_bytes(text.encode()+old);docs[n]["after_sha256"]=h(R/n)
 blocking="# 正式下游阻塞登记：2026-10-21 04:49 UTC轮次\n\n"+text+"""## 后续终态交付

仅检查五个已登记job的真实终态。新 consumer.py 的 review_terminal/consume 需要完整typed terminal、原ledger/adapter/raw、R双根payload集合及原consumer复建；运行期布尔收据不代替终验。每pair输出为P/results/formal_main_v2/execution/goal_remaining5_v1/<pair_key>/attempt01，原始payload为R/results/formal_main_v2/raw_runtime/goal_remaining5_v1/<pair_key>/attempt01。终态按精确allowlist回存归档，保留正常任务失败、policy_error及全部成本。新失败只作有界诊断，不按结果自动再试。

runtime manifest 200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f；gateway 45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b；scope f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b。各pair执行目录保存root授权/admission、ACK/held/登记/release/committed，不得再submit。

CPU旧候选和反例完整保留：已有ACK对账不能套新五pair容量门槛；大小上界按实际编码；scope导入前固定SHA；gateway v2缺pair_key；fresh panel不能依赖不存在的旧输出。均在GPU前有界修正。计划报告550项与报告后5次合约SHA核对单列，不称新增科学证据。

Goal30设计包为工程交付中的Goal_fixed30_design，仅作者CPU122项/10拒绝。仍需独立审计、新精确计划/一次性gateway/actualP/原始采集终验；原collect gateway不泛化。
"""
 put("docs/正式下游阻塞登记_20261021T0449.md",blocking.encode())
 for directory,title in [("formal_goal_remaining5_gate_v1","Goal五配对被动门控入口"),("formal_goal_remaining5_dispatch_v1","Goal五配对原子单次提交")]:
  put("scripts/ops/"+directory+"/README.md",("# "+title+"\n\n仅绑定256 seed23/41与64 seed17/23/41的既定5×200开发试验。已登记3057505/3057510/3057515/3057526/3057533，禁止重复提交或自动重试。原科学循环、模型选择与173冻结源不变。\n\n来源/CPU/实际P验证不等于GPU或科学终验。每pair必须由新typed consumer从原始证据重建，并独立终审后root接纳。原始payload终态精确归档，运行中不入Git。\n\n共享writer锁/CAS、全模式8槽、每pair独立ACK/token及一次release；不确定提交仅原ACK对账。操作证据与后续门槛见[本轮下游登记](../../../docs/正式下游阻塞登记_20261021T0449.md)。\n").encode())
 save(B+"/transport_argument_preflight_correction.json",dict(kind="root_observed_command_argument_error",source="root tool traceback; not a fabricated server audit",failed_action="observe_goal_dispatch with malformed bundle SHA",error="ValueError: bundle SHA missing",failed_before_entrypoint_execution=True,failed_before_transport_audit_creation=True,corrected_action="same entrypoint SHA with exact stored approved transport prefix",successful_audit="results/formal_main_v2/control_transport/observe_goal_dispatch_20261021T0449_v2.jsonl",state_unchanged_at_successful_observation=ST,new_submissions_from_observer=0))
 receipt=save(B+"/root_integration_receipt.json",dict(schema="formal_main_v2",status="five_once_development_jobs_integrated_no_scientific_results_accepted",state_before=ref(B+"/dispatch_supervisor_snapshot_before.json"),state_after=ref(STATE),summary=ref(B+"/final_summary.json"),observation=ref(OBS),submission_receipt=ref(B+"/Goal_remaining5_submissions_root_receipt.json"),prior_cost_display_metadata=oldcost,cost_metadata_corrected_from_stale_final_to_running_lower_bound=True,documentation_changes=docs,new_scientific_trials_accepted=0,source173_unchanged=True,training_controller_restarted=False,final_opened=False))
 print(json.dumps(dict(status="root_integrated",receipt=receipt,state_sha256=h(R/STATE),summary_sha256=h(R/B/"final_summary.json"),accepted_development=7800,new_GPU_jobs=list(keys.values()),GPU_seconds=1995402)))
