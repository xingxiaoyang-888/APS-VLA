"""Independent Object256 seed23 terminal byte/CPU audit including startup failure.
Raw training/update/validation reconstruction adapted from audited independent
Goal terminal FSM; Object identity, pool and failure chain independently bound.
Only private audit outputs. No tensor deserialization, scheduler or state writes.
"""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,importlib.util,json,math,random,sys,subprocess
from datetime import datetime,timezone
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/independent_object3042627_0626"
helper=R/"results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258.py"
assert hashlib.sha256(helper.read_bytes()).hexdigest()=="fd566045bc20e76a10dc05b7ed56377d9817231bb5538eb828c087eb7dd5ef1a"
sp=importlib.util.spec_from_file_location("independent_io_0943",helper)
io=importlib.util.module_from_spec(sp);sp.loader.exec_module(io)
need,read,raw,jrows,close,sig,shafile=io.need,io.read,io.raw,io.jrows,io.close,io.sig,io.shafile
P,H,S=io.P,io.H,io.S
REL="results/formal_main_v2/libero_object/k256/seed23/training"
JOBS=["3039258","3042627"]
ALLJOBS=["3028460",*JOBS]
ENDS=[500,5000];STARTS=[0,500];COSTS=[84,6512,52321]
def refread(ref):return read(ref["path"],ref["sha256"])
def main():
 need(len(sys.argv)==2,"one exact bindings SHA required")
 bindings=read(".local/independent_object3042627_0626/bindings.json",sys.argv[1])
 raw(helper.relative_to(R).as_posix())
 raw(".local/independent_goal3039988_0530/audit_3039988.py","c5cf0c3c937da2abd107d341ca45a4f0a913979b99974daab362cb493ccfaf1a")
 raw("SERVER_WORKSPACE.md","fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62")
 raw("docs/服务器工作区与GitHub同步.md","d7f0455ef4febb536df199653fd323a1cef98ad66732e5b2ea8edfdf06b75343")
 raw("scripts/review_formal_segment.py","566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790")
 raw("scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py","ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4")
 raw("scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py","c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480")
 root=refread(bindings["root"]);selected=refread(bindings["selected"])
 PULL=bindings["pull"]["path"];PULLSHA=bindings["pull"]["sha256"]
 need(bindings["root"]["path"]==REL+"/segment_reviews/3042627.json","canonical terminal scope")
 need(root["kind"]=="root_segment_review" and root["status"]=="passed" and root["job_id"]=="3042627" and root["suite"]=="libero_object" and root["visual_tokens"]==256 and root["seed"]==23,"root identity")
 need(root["completed_by_arm"]=={"A":5000,"B":5000} and root["allowed_next_segment_end"] is None and root["resume_required"] is False,"terminal only, no5500")
 need(selected["status"]=="verified_actual_server_bytes" and selected["job_id"]=="3042627" and selected["root_review"]==bindings["root"] and selected["weights_copied"] is False and selected["optimizer_rng_deserialized"] is False,"selected exact byte proof")
 inventory=read("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
 need(len(inventory["files"])==173 and root["source_sha256"]==inventory["source_sha256"],"source173")
 for rel,h in inventory["files"].items():
  raw(rel,h);need(shafile(S/rel)["sha256"]==h,"runtime snapshot byte identity")
  raw("snapshots/formal_main_v2_run_564be0995e/"+rel,h)
 configrel="configs/experiments/formal_main_v2/libero_object_k256_seed23.json"
 config=read(configrel,inventory["files"][configrel]);need(read(REL+"/registered_config.json")==config,"same run config")
 need(config["seed"]==23 and config["tokens_per_camera"]==128 and config["training"]["updates"]==5000 and config["training"]["effective_batch"]==8,"full unchanged config")
 need(config["selection"]["updates"]==list(range(0,5001,500)),"11 validation nodes")
 jobs={str(j["job_id"]):j for j in root["registered_pair_jobs_at_review"]}
 need(set(jobs)==set(ALLJOBS) and len(root["registered_pair_jobs_at_review"])==3,"exact failed and two successful allocations")
 for jid,cost,end in zip(ALLJOBS,COSTS,[500,500,5000]):
  j=jobs[jid];status,exitcode=("FAILED","1:0") if jid=="3028460" else ("COMPLETED","0:0")
  need((j["status"],j["exit_code"],j["elapsed_seconds"],j["gpus"],j["segment_end"])==(status,exitcode,cost,1,end),"terminal unique bill "+jid)
 need(sum(j["elapsed_seconds"]*j["gpus"] for j in jobs.values())==root["pair_allocated_gpu_seconds"]==58917,"unique all-pair cost incl failure")
 failedinv=read(jobs["3028460"]["invocation"],jobs["3028460"]["invocation_sha256"])
 oldinv=read(jobs["3039258"]["invocation"],jobs["3039258"]["invocation_sha256"])
 newinv=read(jobs["3042627"]["invocation"],jobs["3042627"]["invocation_sha256"])
 auth=read("configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json","5f86034d43017d3f89b0d3a73cd90dd8bd22b0b8a54461d0b0a51e5f8df6220e")
 contract=newinv["continuous_admission"];registered_contract=jobs["3042627"]["continuous_admission"]
 need({k:v for k,v in registered_contract.items() if k not in ["actual_sbatch_argv","request_token"]}==contract,"exact registered execution contract")
 need(contract["authorization"]=={"path":"configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json","sha256":io.readmap["configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json"]},"exact authorization")
 for obj in [auth,contract]:
  need(obj["scientific_settings_changed"] is False and obj["single_new_attempt"] is True and obj["automatic_retry"] is False and obj["controller_admission_changed"] is False,"bounded admission")
  need(obj["target_updates_per_arm"]==5000 and obj["soft_wall_seconds"]==169200 and obj["allocation_time"]=="48:00:00" and obj["completed_before"]=={"A":500,"B":500} and obj["historical_GPU_seconds"]==6596,"actual admitted boundary")
 for key in ["canonical_failure_review","root_recovery_review","independent_recovery_review","terminal_pull","controller_activation","normal_execution_authorization","node_exclusion","root_review","independent_review"]:refread(auth[key])
 for rel,h in {**auth["gateway_files"],**auth["reviewer_publication"]}.items():raw(rel,h)
 need(contract["sample_cursor_before"]=={"A":4000,"B":4000} and contract["prior_job_ids"]==["3028460","3039258"],"correct inherited cursor/history")
 need(contract["validation_updates"]==list(range(0,5001,500)) and contract["checkpoint_every_updates"]==50,"fixed validation/checkpoint cadence")
 need(oldinv["argv"]==failedinv["argv"]+["--resume"],"bounded recovery originally explicit resume with no prior checkpoint")
 base=json.loads(json.dumps(newinv));base.pop("continuous_admission");base["segment_end"]=500;base["registered_utc"]=oldinv["registered_utc"]
 for key,value in [("--stop-after-updates","500"),("--max-wall-seconds","12600")]:
  need(base["argv"].count(key)==1,"unique execution option");base["argv"][base["argv"].index(key)+1]=value
 need(base==oldinv and newinv["argv"].count("--resume")==1,"only admitted target/wall/registration changes; same science and retained repair")
 need(newinv["runtime_compatibility"]==oldinv["runtime_compatibility"]==failedinv["runtime_compatibility"],"same metadata adapter for all allocations")
 need("component_compatibility" not in newinv and "autonomous_execution" not in newinv,"Object original metadata only; no Goal component mapping")
 for rel,h in newinv["runtime_compatibility"]["files"].items():raw(rel,h);need(shafile(P/rel)["sha256"]==h,"same runtime metadata bytes")
 sb=registered_contract["actual_sbatch_argv"]
 need(jobs["3042627"]["startup_recovery"]["actual_sbatch_argv"]==sb and jobs["3042627"]["startup_recovery"]["authorization"]==contract["authorization"],"startup consumer exact scheduler metadata")
 for x in ["--no-requeue","--time=48:00:00","--exclude=gpu4020","--chdir="+str(P),"--comment="+registered_contract["request_token"]]:need(x in sb,"actual submitted option "+x)
 need(sb[-1]==str(P/"scripts/server/formal_asset_main.slurm"),"frozen original Slurm wrapper")
 failuremod=io.load("scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py")
 failure=failuremod.require_saved(io.Evidence(),job=jobs["3028460"])
 need(root["startup_failure_history"]=={"3028460":failure},"all failed original evidence retained")
 need(failure["completed_by_arm"]=={"A":0,"B":0} and failure["next_sample_cursor"]=={"A":0,"B":0} and failure["current_allocation_arm_initializations"]==failure["current_allocation_new_updates"]==0,"failure did not initialize/train either arm")
 need(all(x["exists"] is False for x in failure["server_resume_checks"]),"no fabricated failed checkpoint")
 prior=refread(contract["root_recovery_review"]);pri_ind=refread(contract["independent_recovery_review"])
 need(prior["status"]=="passed" and prior["kind"]=="root_segment_review" and prior["completed_by_arm"]=={"A":500,"B":500} and prior["job_id"]=="3039258","historical root500")
 need(pri_ind["kind"]=="CUDA_original_target_recovery_independent_review" and pri_ind["status"]=="passed_original_target_recovery_only" and pri_ind["job_id"]=="3039258" and pri_ind["root_review"]==contract["root_recovery_review"],"historical real independent500")
 need(pri_ind["weights_copied_or_deserialized"] is False and pri_ind["state_or_Git_writes"] is False,"historical scope retained")
 need(prior["server_resume_checks"]==pri_ind["actual_server_resume_checks"]==contract["resume_checks_before"],"exact500 actual checkpoint chain")
 for arm in "AB":need(pri_ind["arms"][arm]["completed_updates"]==500 and pri_ind["arms"][arm]["cursor"]==4000,"historical independent real cursor")
 prior_checks=[prior["server_resume_checks"]]
 prior_receipts=[{"job_id":"3039258","completed_by_arm":{"A":500,"B":500},"root":contract["root_recovery_review"],"independent":contract["independent_recovery_review"]}]
 gate=read("results/formal_main_v2/libero_object/acceptance/root_review.json","2fd415c47d8852678b4d83296ffcff4709d97765debe7f4e41a17a7ae02daaa2")
 need(gate["status"]=="passed" and gate["suite"]=="libero_object" and gate["job_id"]=="3012482" and gate["source_sha256"]==root["source_sha256"] and gate["runtime_compatibility"]==newinv["runtime_compatibility"],"own GPU acceptance")
 registration=read("configs/experiments/formal_main_v2.json",inventory["files"]["configs/experiments/formal_main_v2.json"])
 suite=registration["suites"]["libero_object"];pairs=[p for p in registration["pairs"] if p["suite"]=="libero_object" and p["visual_tokens"]==256 and p["seed"]==23];need(len(pairs)==1,"exact registered pair");pair=pairs[0]
 expected=["--config",str(S/pair["path"]),"--protocol",str(P/suite["protocol"]),"--windows",str(P/suite["windows"]),"--checkpoint",suite["model_root_server"],"--asset-manifest",str(S/suite["model_manifest"]),"--data-directory",suite["data_root_server"],"--cache-directory",str(P/".local/formal-hf-libero_object"),"--feature-cache",suite["cache_root_server"],"--training-checkpoints",pair["checkpoint_root_server"],"--input-acceptance-report",str(P/gate["output_relative"]/"input_acceptance.json"),"--acceptance-report",str(P/gate["output_relative"]/"f01_k256.json"),"--output",str(P/REL),"--arm","both","--stop-after-updates","5000","--max-wall-seconds","169200","--resume"]
 need(newinv["argv"]==expected,"full unchanged Object scientific argv")
 model=read(suite["model_manifest"],inventory["files"][suite["model_manifest"]])
 need(model["repository"]=="moojink/openvla-7b-oft-finetuned-libero-object" and model["revision"]==config["model_revision"],"official immutable Object model")
 official_components=[]
 for name in ["action_head--150000_checkpoint.pt","proprio_projector--150000_checkpoint.pt"]:
  spec=next(v for v in model["files"] if v["path"]==name);actual=shafile(Path(suite["model_root_server"])/name)
  need(actual["sha256"]==spec["sha256"] and actual["bytes"]==spec["size"],"official actual Object component");official_components.append(actual)
 for name,h in gate["files"].items():raw(gate["output_relative"]+"/"+name,h)
 f00=read(gate["output_relative"]+"/input_acceptance.json")
 for rel,h in gate["source_files"].items():raw(rel,h)
 protocol=read(config["data"]["protocol"]);manifest=read(config["data"]["windows"])
 sys.path.insert(0,str(R/"src"))
 from cti_vla.data.formal_windows import load_formal_protocol,load_formal_windows
 checked=load_formal_protocol(R/config["data"]["protocol"],project_root=R)
 need(load_formal_windows(R/config["data"]["windows"],checked)==manifest,"full legal window manifest")
 train=manifest["train_window_ids"];val=manifest["validation_window_ids"];lookup={r["window_id"]:r for r in manifest["windows"]}
 need(len(train)==44068 and len(set(train))==44068 and len(val)==len(set(val))==204,"full train/validation pools")
 need(not set(train)&set(val) and not {lookup[x]["episode_id"] for x in train}&{lookup[x]["episode_id"] for x in val},"episode isolation")
 rng=random.Random(23);order=[]
 while len(order)<40000:
  epoch=list(train);rng.shuffle(epoch);order.extend(epoch)
 order=order[:40000]
 need(len(set(order))==40000 and len(order)-len(set(order))==0,"40000 unique uses of full44068 pool; no repeat")
 constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(raw("src/cti_vla/training/formal_future.py").decode()).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith("FORMAL_")}
 trainer=raw("src/cti_vla/training/formal_future.py").decode()
 need('optimizer.load_state_dict(saved["optimizer"])' in trainer and 'restore_rng(saved["rng"])' in trainer,"frozen restoration path")
 reports={};summaries={};initial={};actualchecks=[]
 for arm in ["A","B"]:
  base=REL+"/"+arm;report=read(base+"/training_report.json");reports[arm]=report
  for key,value in {"schema":"formal_main_v2","arm":arm,"status":"completed","training_updates_completed":5000,"committed_samples":40000,"next_sample_cursor":40000,"unique_committed_windows":len(set(order)),"attempted_forward_backward_samples_completed":40000,"train_pool_windows":44068,"validation_pool_windows":204,"vla_parameters_unchanged":True,"attempts":2,"resumed_from_update":500,"job_ids":JOBS}.items():
   need(report.get(key)==value,"report "+arm+" "+key)
  ident=report["identity"]
  need(ident["training_source_files"]==gate["source_files"] and ident["pair_config_sha256"]==sig(config) and ident["training_config_sha256"]==sig({**config,"arm":arm}),"arm source/config")
  need(ident["training_version"]==constants["FORMAL_TRAINING_VERSION"] and ident["training_numerics"]==constants["FORMAL_NUMERICS"],"numerics unchanged")
  for key,rel in [("window_manifest_sha256",config["data"]["windows"]),("data_protocol_sha256",config["data"]["protocol"]),("input_acceptance_sha256",gate["output_relative"]+"/input_acceptance.json"),("f01_report_sha256",gate["output_relative"]+"/f01_k256.json"),("resume_acceptance_sha256",gate["output_relative"]+"/resume_acceptance.json"),("resume_journal_sha256",gate["output_relative"]+"/f03_calls.jsonl")]:need(ident[key]==io.readmap[rel],"gate identity "+key)
  need(ident["frozen_model_sha256"]==report["frozen_model_sha256"]==f00["frozen_model_sha256"],"base frozen identity")
  savedorder=read(base+"/training_order.json")
  need(savedorder["samples"]==order and savedorder["order_sha256"]==report["sample_order_sha256"]==sig(order),"full40000 seeded order")
  need(savedorder["initial_scorer_sha256"]==report["initial_scorer_sha256"] and savedorder["train_pool_sha256"]==sig(train),"matched start")
  bytask=defaultdict(list)
  for wid in order:bytask[str(lookup[wid]["task_id"])].append(wid)
  sampling={t:{"samples":len(ids),"unique_windows":len(set(ids)),"unique_episodes":len({lookup[i]["episode_id"] for i in ids}),"phase_sample_counts":dict(Counter(lookup[i]["phase"] for i in ids))} for t,ids in bytask.items()}
  need(sampling==report["committed_sampling_by_task"]==report["attempted_completed_sampling_by_task"],"actual unique sampling")
  paths=sorted((R/base/"attempts").glob("*/cost_events.jsonl"));need(len(paths)==2,"two exact attempts")
  cur=0;sampleids=[];allcommits=[];vals={};grad=[];byattempt=[]
  for index,path in enumerate(paths):
   attempt=path.parent.name;rows=jrows(path.relative_to(R).as_posix());first=rows[0];jid=JOBS[index];end=ENDS[index]
   need(first["event"]=="attempt_start" and first["job_id"]==jid and first["attempt_id"]==attempt and first["completed_update"]==cur and first["next_sample_cursor"]==cur*8 and first["resumed"] is bool(index) and first["identity"]==ident,"resume/start identity")
   if index:
    before=next(x for x in prior_checks[index-1] if x["arm"]==arm)
    need(before["sha256"]==allcommits[-1]["resume_sha256"] and before["exists"] is True,"observed prelaunch exact prior commit")
   need(all(r["job_id"]==jid and r["attempt_id"]==attempt for r in rows),"entire attempt identity")
   need(all(a["attempt_elapsed_seconds"]<=b["attempt_elapsed_seconds"] for a,b in zip(rows,rows[1:])),"monotonic time")
   active=None;micro=0;sample=False;validating=None;ended=False;commits=[];u_count=0;v_count=0
   for r in rows[1:]:
    e=r["event"];need(not ended,"events after terminal")
    if e=="update_start":
     need(active is None and validating is None and r["update"]==cur+1,"continuous updates")
     if cur%50==0:need(allcommits and allcommits[-1]["completed_update"]==cur,"durable prior50")
     active=cur+1;micro=0;need(r["window_ids"]==order[(active-1)*8:active*8],"actual batch order")
    elif e in ["sample_start","sample_end"]:
     need(active is not None and micro<8 and r["update"]==active and r["micro_batch_index"]==micro and r["window_id"]==order[(active-1)*8+micro],"actual sample order")
     need((e=="sample_start")!=sample,"paired sample");sample=e=="sample_start"
     if not sample:micro+=1;sampleids.append(r["window_id"])
    elif e=="update_end":
     need(active==r["update"] and micro==8 and not sample and r["forward_backward_samples"]==8,"8 gradients")
     close(r["alpha"],.1+.95*(1+math.cos(math.pi*(active-1)/4999)),"original5000 annealing")
     for k in ["grad_norm","loss","action_loss","teacher_l1","demonstration_l1","seconds"]:need(math.isfinite(r[k]) and r[k]>=0,"finite optimization")
     close(r["action_loss"],.5*(r["teacher_l1"]+r["demonstration_l1"]),"action objective")
     close(r["loss"],r["action_loss"]+(0 if arm=="A" else .1*r["future_mse"]),"only B auxiliary")
     grad.append(r["grad_norm"]);cur=active;active=None;u_count+=1
    elif e=="validation_start":
     need(active is None and validating is None and r["update"]==cur and cur in range(0,5001,500) and cur not in vals and r["windows"]==204,"exact node once");validating=cur
    elif e=="validation_end":
     need(validating==r["update"] and r["window_forwards"]==204,"full validation")
     vr=base+"/attempts/"+attempt+"/validation_"+str(validating).zfill(5)+".json";v=read(vr,r["artifact_sha256"])
     need(v["arm"]==arm and v["update"]==validating and v["job_id"]==jid and v["attempt_id"]==attempt and v["windows"]==204 and v["tasks"]==10 and v["metric"]=="task_macro_hard_validation_teacher_l1","validation identity")
     need([x["window_id"] for x in v["observations"]]==val,"full ordered204")
     task=defaultdict(list)
     for x in v["observations"]:
      ref=lookup[x["window_id"]];need(x["episode_id"]==ref["episode_id"] and x["task_id"]==ref["task_id"],"val source")
      ids=x["retained_indices"];need(len(ids)==256 and ids==sorted(set(ids)) and all(type(i)==int and 0<=i<512 for i in ids) and sum(i<256 for i in ids)==128,"hard256 original packing")
      a=x["normalized_actions"];need(len(a)==8 and all(len(y)==7 for y in a) and all(math.isfinite(z) for y in a for z in y),"finite8x7")
      need(x["teacher_l1"]>=0 and x["demonstration_l1"]>=0,"finite metric");task[str(x["task_id"])].append(x)
     need(len(task)==10,"10 tasks")
     metric=sum(sum(x["teacher_l1"] for x in xs)/len(xs) for xs in task.values())/10
     expert=sum(sum(x["demonstration_l1"] for x in xs)/len(xs) for xs in task.values())/10
     close(metric,v["validation_metric"]);close(metric,r["validation_metric"]);close(expert,v["demonstration_l1"])
     for t,xs in task.items():
      need(v["per_task"][t]["windows"]==len(xs),"task count")
      for k in ["teacher_l1","demonstration_l1"]:close(v["per_task"][t][k],sum(x[k] for x in xs)/len(xs))
     close(v["window_weighted_teacher_l1_diagnostic"],sum(x["teacher_l1"] for x in v["observations"])/204)
     vals[validating]={"update":validating,"teacher_l1":metric,"expert_l1":expert,"path":vr,"sha256":io.readmap[vr]}
     if validating==0:initial[arm]=[{k:x[k] for k in ["window_id","episode_id","task_id","teacher_l1","demonstration_l1","retained_indices","normalized_actions"]} for x in v["observations"]]
     validating=None;v_count+=1
    elif e=="checkpoint_commit":
     need(active is None and validating is None and r["completed_update"]==cur,"atomic committed update")
     commits.append(r);allcommits.append(r)
    elif e=="attempt_end":
     need(active is None and validating is None and cur==end and r["completed_update"]==end and r["status"]==("checkpointed" if index<1 else "completed"),"clean committed attempt")
     need(commits[-1]["completed_update"]==end,"last checkpoint");ended=True
    else:raise ValueError("unknown event "+e)
   need(ended and u_count==[500,4500][index] and v_count==[2,9][index],"full attempt work")
   byattempt.append({"job_id":jid,"attempt_id":attempt,"start_update":STARTS[index],"end_update":end,"updates":u_count,"validation_nodes":v_count,"journal_rows":len(rows),"last_resume_sha256":commits[-1]["resume_sha256"]})
  need(cur==5000 and sampleids==order and len(sampleids)==40000 and len(set(sampleids))==len(set(order)),"no missing/replayed samples")
  need(set(x["completed_update"] for x in allcommits)==set(range(0,5001,50)) and len(grad)==5000 and max(grad)>0,"all checkpoint/gradient evidence")
  need(sorted(vals)==list(range(0,5001,500)) and [v["update"] for v in report["evaluations"]]==sorted(vals),"11 selection nodes")
  for v in report["evaluations"]:
   obs=vals[v["update"]];need(v["artifact_sha256"]==obs["sha256"] and v["artifact_path"]==str(P/obs["path"]),"raw selection binding");close(v["validation_metric"],obs["teacher_l1"])
  best=min(vals.values(),key=lambda v:(v["teacher_l1"],v["update"]))
  need(report["best_update"]==best["update"],"earliest min selection");close(report["best_validation_metric"],best["teacher_l1"])
  dep=read(base+"/deployment_receipt.json")
  need(dep["training_complete"] is True and dep["base_frozen"] is True and dep["checkpoint_unchanged"] is True and dep["completed_updates"]==dep["planned_updates"]==5000,"completed deployment")
  need(dep["checkpoint_sha256"]==report["best_checkpoint_sha256"] and dep["metadata_sha256"]==sig(dep["metadata"]),"deployment SHA")
  md=dep["metadata"];need(md["arm"]==arm and md["suite"]=="libero_object" and md["seed"]==23 and md["visual_tokens"]==256 and md["per_camera_budgets"]==[128,128] and md["update"]==best["update"],"deployment identity")
  close(md["validation_metric"],best["teacher_l1"])
  need(dep["evaluations"]==report["evaluations"] and dep["pair_config"]==config and dep["training_config"]=={**config,"arm":arm},"deployment original config and selection")
  resume=shafile(H/"checkpoints/formal_main_v2/libero_object/k256/seed23"/arm/"resume.pt");resume["arm"]=arm
  need(resume["sha256"]==allcommits[-1]["resume_sha256"] and resume==next(x for x in root["server_resume_checks"] if x["arm"]==arm),"actual final resume")
  checkpoint=shafile(H/"checkpoints/formal_main_v2/libero_object/k256/seed23"/arm/"best.pt")
  proof=next(x for x in selected["checks"] if x["arm"]==arm)
  need(checkpoint["path"]==report["best_checkpoint"]==proof["path"] and checkpoint["sha256"]==dep["checkpoint_sha256"]==proof["sha256"] and checkpoint["bytes"]==proof["bytes"],"actual selected best")
  actualchecks.append(dict(arm=arm,resume=resume,best=checkpoint,selected_update=best["update"],validation_metric=best["teacher_l1"]))
  summaries[arm]=dict(completed_updates=5000,sample_uses=40000,unique_windows=len(set(sampleids)),cursor=40000,attempts=byattempt,validation=[vals[u] for u in sorted(vals)],earliest_selected_update=best["update"],selected_teacher_l1=best["teacher_l1"],selected_expert_l1=best["expert_l1"],best_sha256=checkpoint["sha256"],gradient_range=[min(grad),max(grad)],replayed_or_uncommitted_samples=0)
 need(initial["A"]==initial["B"] and reports["A"]["initial_scorer_sha256"]==reports["B"]["initial_scorer_sha256"],"matched AB")
 summary=read(REL+"/training_summary.json")
 need(summary["arms"]==reports and summary["status"]=="completed" and summary["pair_complete"] is True and summary["job_id"]=="3042627" and summary["test_opened"] is False and summary["checkpoint_unchanged"] is True,"pair complete")
 final=read(REL+"/finalizations/3042627_7500f0544661.json")
 need(final["status"]=="verified" and final["kind"]=="training" and final["result_sha256"]==io.readmap[REL+"/training_summary.json"] and final["checkpoint_unchanged"] is True,"final source/base provenance")
 need(final["source_files"]==gate["source_files"]==summary["source_files"],"all producer sources")
 cache=Counter();paths=sorted((R/REL/"cache_events").glob("*.jsonl"));need(len(paths)==2,"two actual cache logs")
 cache_identity=reports["A"]["identity"]["cache_identity"];need(cache_identity==reports["B"]["identity"]["cache_identity"],"common cache namespace")
 cv=ast.parse(raw("src/cti_vla/training/formal_records.py").decode())
 cversion=next(ast.literal_eval(n.value) for n in cv.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="FORMAL_CACHE_VERSION")
 namespace=sig({"cache_version":cversion,**cache_identity})
 for p in paths:
  for row in jrows(p.relative_to(R).as_posix()):
   need(row["job_id"] in JOBS and row["cache_identity_sha256"]==namespace,"cache owner/identity");cache[row["event"]]+=1
 need(dict(cache)==root["cache_event_counts"],"raw cache totals")
 pull=read(PULL,PULLSHA)
 need(pull["status"]=="verified_nonweight_snapshot" and pull["final_evidence"] is True and pull["weights_copied"] is False and pull["sealed_initial_states_copied"] is False and not pull["missing"] and not pull["skipped"],"complete final pull")
 before=read(str(Path(PULL).parent/"inventory_before.json"),pull["inventory_sha256"]);after=read(str(Path(PULL).parent/"inventory_after.json"))
 need(before==after,"stable double inventory");pulledrows={r["relative"]:r for r in before["files"]};need(len(pulledrows)==len(before["files"]),"unique inventory")
 for when in ["accounting_before","accounting_after"]:
  for jid,j in jobs.items():
   bill=pull[when]["jobs"][jid];need(all(bill[k]==j[k] for k in ["status","exit_code","elapsed_seconds"]),"actual unique bill "+jid)
   need(dict(x.split("=",1) for x in bill["allocation"].split(",") if "=" in x).get("gres/gpu")=="1","GPU allocated")
 failed_only={"results/formal_main_v2/job_receipts/3028460.json","results/slurm/cti-formal_3028460.out","results/slurm/cti-formal_3028460.err"}
 for r in pull["files"]:
  rel=r["relative"];data=raw(rel,r["sha256"]);need(len(data)==r["bytes"],"pull byte count")
  need(all(r[k]==pulledrows[rel][k] for k in ["path","sha256","bytes","job_ids"]),"stable original inventory binding")
  need(r["path"]==str(P/rel) and r["action"] in ["same_sha_skipped","downloaded_verified"],"exact P raw origin")
  if rel in failed_only:need("3028460" in r["job_ids"] and r["sha256"]==failure["evidence_bundle"][rel]["sha256"],"preserved failed original ownership")
  else:need("3042627" in r["job_ids"],"current/shared run ownership")
  need(shafile(P/rel)["sha256"]==r["sha256"],"live terminal P unchanged")
 for rel,h in root["files"].items():raw(rel,h)
 for rel,h in root.get("evidence_sha256",{}).items():
  if rel!="results/experiment_supervisor/state.json":raw(rel,h)
 shared=io.load("scripts/review_formal_acceptance.py");asset_reviews={}
 for jid in JOBS:
  j=jobs[jid];receipt=read(f"results/formal_main_v2/job_receipts/{jid}.json")
  need(receipt["exit_code"]==receipt["runner_exit_code"]==0 and receipt["errors"]==[] and receipt["loader_restored"] is True and receipt["source_inputs_unchanged"] is True,"successful restored Object metadata scope")
  need(receipt["invocation_sha256"]==j["invocation_sha256"] and receipt["runtime_compatibility"]==j["runtime_compatibility"],"same actual metadata execution")
  events=jrows(REL+f"/compatibility/{jid}/compatibility_events.jsonl")
  need([e["event"] for e in events]==["stage_start","asset_metadata_compat_enter","stage_runner_start","asset_metadata_compat_load_start","asset_metadata_compat_load_complete","stage_runner_return","asset_metadata_compat_exit","stage_end"] and [e["seq"] for e in events]==list(range(8)),"eight actual metadata events")
  me=shared.Evidence(R);actualinv=read(j["invocation"],j["invocation_sha256"])
  rebuilt=shared.review_runtime_compatibility(me,job=j,invocation=actualinv,receipt=receipt,inventory=inventory,pull_receipt=PULL)
  component=shared.review_component_compatibility(me,job=j,invocation=actualinv,receipt=receipt,inventory=inventory,metadata_review=rebuilt,pull_receipt=PULL)
  need(rebuilt["event_count"]==8 and component is None,"Object needs no Goal component alias")
  need(root["runtime_compatibility_history"][jid]==rebuilt,"original root same metadata reconstruction")
  me.unchanged()
  for rel,h in me.hashes.items():raw(rel,h)
  asset_reviews[jid]={"metadata":rebuilt,"component":component,"elapsed_seconds":j["elapsed_seconds"],"nested_phase_times_added":False}
 gatejob=gate["job_at_review"];gateinv=read(gatejob["invocation"],gatejob["invocation_sha256"]);gatereceipt=read(f"results/formal_main_v2/job_receipts/{gatejob['job_id']}.json")
 gatepull=gate["runtime_compatibility_review"]["pull_receipt"];refread(gatepull)
 ge=shared.Evidence(R)
 gm=shared.review_runtime_compatibility(ge,job=gatejob,invocation=gateinv,receipt=gatereceipt,inventory=inventory,pull_receipt=gatepull["path"])
 need(gm==gate["runtime_compatibility_review"],"own accepted Object metadata reverified")
 ge.unchanged()
 for rel,h in ge.hashes.items():raw(rel,h)
 asset_reviews[str(gatejob["job_id"])]={"metadata":gm,"elapsed_seconds":gatejob["elapsed_seconds"],"shared_prerequisite_not_added_to_pair_bill":True}
 need(root["server_resume_checks"]==[x["resume"] for x in actualchecks],"fresh independently hashed final resume proofs")
 need(len(selected["checks"])==2 and {x["arm"] for x in selected["checks"]}=={"A","B"},"two selected byte probes")
 archive_inputs=refread(bindings["archive_inputs"]);snapshot=bindings["archive_snapshot"]["path"];snapshot_sha=bindings["archive_snapshot"]["sha256"]
 raw("scripts/ops/nonweight_archive.py","f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2")
 codec=io.load("scripts/ops/nonweight_archive.py");value,evidence,objects,chunks=codec.verified_plan(R,snapshot,snapshot_sha)
 all_raw_paths={p.relative_to(R).as_posix() for p in list((R/REL).glob("*/attempts/*/cost_events.jsonl"))+list((R/REL/"cache_events").glob("*.jsonl"))}
 need(len(all_raw_paths)==6 and len(value["files"])==3 and sum(x["bytes"] for x in value["files"])==213072852,"six actual journals, three new large archived logs")
 archived_paths={x["path"] for x in value["files"]};need(archived_paths<=all_raw_paths,"archive scope")
 for rel in archived_paths:need(json.loads(raw(rel).splitlines()[0])["job_id"]=="3042627","new log owner")
 old_paths=sorted(all_raw_paths-archived_paths);need(len(old_paths)==3,"three historical raw journals")
 head=subprocess.run(["git","-C",str(R),"rev-parse","HEAD"],capture_output=True,check=True,text=True).stdout.strip();need(len(head)==40,"HEAD commit")
 historical_raw=[]
 for rel in old_paths:
  live=raw(rel);need(json.loads(live.splitlines()[0])["job_id"]=="3039258","original successful recovery raw owner")
  tracked=subprocess.run(["git","-C",str(R),"show",head+":"+rel],capture_output=True,check=True).stdout
  need(tracked==live and hashlib.sha256(tracked).hexdigest()==io.readmap[rel],"historical raw original Git bytes")
  historical_raw.append({"path":rel,"bytes":len(live),"sha256":io.readmap[rel],"git_commit":head,"verified_byte_equal_to_tracked_blob":True})
 need(sum(x["bytes"] for x in historical_raw)==14865531,"historical original raw byte total")
 need(subprocess.run(["git","-C",str(R),"rev-parse","HEAD"],capture_output=True,check=True,text=True).stdout.strip()==head,"HEAD stable while checking")
 need([{k:x[k] for k in ["path","sha256","bytes"]} for x in value["files"]]==archive_inputs["raw"],"exact archive input original map")
 for ref,role in evidence.values():need(len(raw(ref["path"],ref["sha256"]))==ref["bytes"],"archive evidence bytes")
 class CompareSink:
  def __init__(self,stream):self.stream=stream;self.h=hashlib.sha256();self.n=0
  def write(self,data):
   need(self.stream.read(len(data))==data,"archive restored chunk unequal to retained original");self.h.update(data);self.n+=len(data);return len(data)
 recovered=[]
 for row in value["files"]:
  need(io.readmap[row["path"]]==row["sha256"],"archive bound to independently parsed raw")
  with (R/row["path"]).open("rb") as stream:
   sink=CompareSink(stream);codec.verify_object(R,row["manifest"],row["sha256"],row["bytes"],sink=sink)
   need(stream.read(1)==b"" and sink.n==row["bytes"] and sink.h.hexdigest()==row["sha256"],"lossless fullfile reconstruction")
  recovered.append({"path":row["path"],"sha256":sink.h.hexdigest(),"bytes":sink.n,"byte_equal_to_retained_original":True})
 archive_review={"snapshot":bindings["archive_snapshot"],"input_registration":bindings["archive_inputs"],"files":recovered,"filesystem_restoration_performed":False,"summary":codec.summary(snapshot,snapshot_sha,value,objects,chunks,"verified")}
 raw(Path(__file__).relative_to(R).as_posix())
 for rel,h in io.readmap.items():need(hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,"input drift "+rel)
 out=dict(schema="formal_main_v2",kind="independent_completed_training_review",status="passed_complete_training_only",job_id="3042627",suite="libero_object",visual_tokens=256,seed=23,root_review=bindings["root"],selected_server_review=bindings["selected"],pull=bindings["pull"],completed_by_arm={"A":5000,"B":5000},allowed_next_segment_end=None,resume_required=False,arms=summaries,actual_checkpoint_hashes=actualchecks,same_AB_initialization_and_full40000_order=True,legal_repeated_sample_uses_per_arm=0,official_Object_components=official_components,asset_compatibility_stages=asset_reviews,archive_reconstruction=archive_review,historical_raw_tracked_Git_delivery=historical_raw,all173_R_S_and_mirror_match=True,historical_failure_review=auth["canonical_failure_review"],historical_failure_preserved_and_rebuilt=True,cost={"retained_failed_GPU_seconds":84,"successful_original500_GPU_seconds":6512,"historical_segments_GPU_seconds":6596,"continuous_segment_GPU_seconds":52321,"all_pair_allocated_GPU_seconds":58917,"allocations":[{"job_id":j,"GPU_seconds":c} for j,c in zip(ALLJOBS,COSTS)],"nested_phases_added":False},cache_event_counts=dict(cache),no_checkpoint_tensor_loaded=True,weights_copied_or_deserialized=False,state_or_Git_writes=False,final_release_authorized=False,scientific_closed_loop_claimed=False,limitations=["Optimizer/RNG restoration is supported by the frozen load_state_dict/restore_rng path, one real resumed attempt and exact boundary checkpoint hashes; checkpoint tensors were not independently deserialized.","Historical CUDA failure, its84GPU seconds and original500 root/independent receipts are retained; newly reviewed arm updates total9000.","Submitted48h argv is submission evidence rather than a fresh scheduler TimeLimit observation.","No machine completion existed at audit entry; raw facts are reconstructed independently, not inferred from a machine review."],read_evidence_sha256=dict(sorted(io.readmap.items())),server_read_evidence_sha256=dict(sorted(io.servermap.items())),historical_dual_review_receipts=prior_receipts,new_reviewed_arm_updates=9000,mutable_state_used_as_current_evidence=False,reviewed_utc=datetime.now(timezone.utc).isoformat())
 dest=D/"independent_review.json"
 with dest.open("x") as f:json.dump(out,f,sort_keys=True,indent=2);f.write("\n")
 print(json.dumps(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),status=out["status"],cost=out["cost"],arms={a:{k:summaries[a][k] for k in ["completed_updates","sample_uses","unique_windows","earliest_selected_update","selected_teacher_l1","best_sha256"]} for a in summaries},refs=len(io.readmap))))
if __name__=="__main__":main()
