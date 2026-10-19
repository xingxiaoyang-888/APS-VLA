"""Independent Object64 seed41 terminal training audit, server-only CPU/byte hashes.
Uses unchanged private I/O primitives only; raw counters/selection recomputed here.
No scheduler, state, Git, tensor deserialization, or final-state access.
"""
from pathlib import Path
from collections import Counter, defaultdict
import ast,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/object64seed41_independent_2232"
helper=R/"results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258.py"
assert hashlib.sha256(helper.read_bytes()).hexdigest()=="fd566045bc20e76a10dc05b7ed56377d9817231bb5538eb828c087eb7dd5ef1a"
sp=importlib.util.spec_from_file_location("independent_io_0943",helper)
io=importlib.util.module_from_spec(sp);sp.loader.exec_module(io)
need,read,raw,jrows,close,sig,shafile=io.need,io.read,io.raw,io.jrows,io.close,io.sig,io.shafile
P,H,S=io.P,io.H,io.S
REL="results/formal_main_v2/libero_object/k64/seed41/training"
MACHINE_DIR="results/formal_main_v2/autonomous_training/run_v1/reviews/libero_object_k64_seed41_64064d625c3c474eb751c78807b6946c"
ROOTREF=MACHINE_DIR+"/machine_review.json"
ROOTSHA="62f118eacf2f4691e44d3735623e6c882b08030069b8b14fc049703083001425"
SELECTED=MACHINE_DIR+"/selected_server_hashes.json"
SELECTEDSHA="79d1243fee08c662c47164980e5ebf082a0e17bfcca2479ff643b4f5008702a5"
PULL="results/formal_main_v2/pulls/20261019T215443Z_58826646465f/receipt.json"
PULLSHA="1518b74a2ef0331fcd2dc09619df6289fb37a9418fafa3035a641f8c90183c7c"
JOBS=["3028482","3037535"]
ENDS=[500,5000]
STARTS=[0,500]
COSTS=[2645,60018]

def main():
 raw(helper.relative_to(R).as_posix())
 machine=read(ROOTREF,ROOTSHA);selected=read(SELECTED,SELECTEDSHA)
 need(machine["kind"]=="automatic_machine_training_review" and machine["status"]=="passed_machine_reconstruction" and machine["root_signature_claimed"] is False and machine["independent_review"] is False,"machine identity not independent")
 root=machine["original_review"]
 need(root["status"]=="local_passed_remote_required" and root["completed_by_arm"]=={"A":5000,"B":5000},"original machine raw preserved")
 raw(machine["reviewer"]["path"],machine["reviewer"]["sha256"])
 raw("SERVER_WORKSPACE.md","fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62")
 raw("docs/服务器工作区与GitHub同步.md","a871dbefb420ac06ad4818fbf85116ae9db243839911afff999ebf9b49e83854")
 raw("results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3034570_v3.py","bdca1e2f330ca32abc0aecf2ecc31a8f1a4769c3cb1a28d8ced479ac12645b64")
 need(root["job_id"]=="3037535" and root["suite"]=="libero_object" and root["visual_tokens"]==64 and root["seed"]==41,"root pair")
 need(root["allowed_next_segment_end"] is None and root["resume_required"] is False,"no5500")
 need(selected["status"]=="verified_actual_server_bytes" and selected["kind"]=="automatic_machine_selected_checkpoint_hashes" and selected["job_id"]=="3037535" and selected["root_signature_claimed"] is False,"machine actual best proof")
 inventory=read("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
 need(len(inventory["files"])==173 and root["source_sha256"]==inventory["source_sha256"],"source173")
 for rel,h in inventory["files"].items():
  raw(rel,h);need(shafile(S/rel)["sha256"]==h,"actual S source "+rel)
 configrel="configs/experiments/formal_main_v2/libero_object_k64_seed41.json"
 config=read(configrel,inventory["files"][configrel]);need(read(REL+"/registered_config.json")==config,"run config")
 need(config["seed"]==41 and config["tokens_per_camera"]==32 and config["training"]["updates"]==5000 and config["training"]["effective_batch"]==8,"full unchanged config")
 need(config["selection"]["updates"]==list(range(0,5001,500)),"11 validation nodes")
 jobs={str(j["job_id"]):j for j in root["registered_pair_jobs_at_review"]}
 need(set(jobs)==set(JOBS) and len(root["registered_pair_jobs_at_review"])==2,"exact two actual allocations")
 for jid,cost,end in zip(JOBS,COSTS,ENDS):
  j=jobs[jid];need((j["status"],j["exit_code"],j["elapsed_seconds"],j["gpus"],j["segment_end"])==("COMPLETED","0:0",cost,1,end),"terminal bill")
 need(sum(j["elapsed_seconds"]*j["gpus"] for j in jobs.values())==root["pair_allocated_gpu_seconds"]==62663,"actual unique bill")
 oldinv=read(jobs["3028482"]["invocation"],jobs["3028482"]["invocation_sha256"])
 newinv=read(jobs["3037535"]["invocation"],jobs["3037535"]["invocation_sha256"])
 contract=newinv["autonomous_execution"];need(contract==jobs["3037535"]["autonomous_execution"],"same execution contract")
 need(contract["target_updates_per_arm"]==5000 and contract["soft_wall_seconds"]==169200 and contract["allocation_time"]=="48:00:00","continuous engineering target")
 need(contract["completed_before"]=={"A":500,"B":500},"migration boundary")
 for key in ["authorization","adapter","source_inventory","acceptance_review","predecessor_review"]:
  ref=contract[key];raw(ref["path"],ref["sha256"])
 stripped=list(newinv["argv"])
 need(stripped[-1]=="--resume" and "--resume" not in oldinv["argv"],"fresh prior and explicit new resume")
 stripped.pop()
 for key,value in [("--stop-after-updates","500"),("--max-wall-seconds","12600")]:stripped[stripped.index(key)+1]=value
 need(stripped==oldinv["argv"],"only approved target/wall changes and explicit resume from exact prior checkpoint")
 need(newinv["runtime_compatibility"]==oldinv["runtime_compatibility"],"same Object compatibility")
 prior_root_ref=REL+"/segment_reviews/3028482.json"
 prior_root_sha="c4dc908e8b479df36797364decf8255c5fabcbbd2f5d222cb9ac5f992a01710e"
 rr=read(prior_root_ref,prior_root_sha)
 need(rr["status"]=="passed" and rr["job_id"]=="3028482" and rr["completed_by_arm"]=={"A":500,"B":500},"prior actual500 boundary")
 prior_ind_ref=REL+"/segment_reviews/3028482_independent.json"
 prior_ind_sha="650aea7830c2c470ed795d845291e2a64ef518e0ba1b598d63c3120e1d49a148"
 prior_ind=read(prior_ind_ref,prior_ind_sha)
 need(prior_ind["kind"]=="independent_segment_review" and prior_ind["status"]=="passed" and prior_ind["root_review_sha256"]==prior_root_sha and prior_ind["completed_validation_updates"]==[0,500] and prior_ind["pair_allocated_gpu_seconds"]==2645 and prior_ind["seed"]==41 and prior_ind["visual_tokens"]==64,"prior independently reviewed500 retained")
 pred=read(contract["predecessor_review"]["path"],contract["predecessor_review"]["sha256"])
 need(pred["original_review"]["completed_by_arm"]=={"A":500,"B":500} and pred["status"]=="passed_machine_reconstruction","predecessor500")
 prior_checks=[rr["server_resume_checks"]]
 need(pred["server_resume_checks"]==prior_checks[0]==contract["resume_checks_before"],"root and observed prelaunch exact500 checkpoints")
 request=read(MACHINE_DIR+"/request.json","31ec9e9faf4282cbd00faaf2e4e0bdedfcbd20cfe3c79e654fca748b5af1f01b")
 need(request["job_id"]=="3037535" and request["pair_key"]=="libero_object_k64_seed41" and request["mode"]=="terminal" and request["check_only"] is False,"machine exact request")
 raw(MACHINE_DIR+"/outcome.json","d3e4c3e6ef34e3f9f2329098a60ed553ebb88a5d2614ce68fd3613abf1dda3f8")
 argv=jobs["3037535"]["autonomous_control"]["actual_sbatch_argv"]
 for x in ["--no-requeue","--time=48:00:00","--gres=gpu:l40:1","--exclude=gpu4020","--job-name=cti-formal"]:need(x in argv,"actual submitted option "+x)
 gate=read("results/formal_main_v2/libero_object/acceptance/root_review.json")
 need(gate["status"]=="passed" and gate["source_sha256"]==root["source_sha256"],"own GPU acceptance")
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
 rng=random.Random(41);order=[]
 while len(order)<40000:
  epoch=list(train);rng.shuffle(epoch);order.extend(epoch)
 order=order[:40000]
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
  for key,rel in [("window_manifest_sha256",config["data"]["windows"]),("data_protocol_sha256",config["data"]["protocol"]),("input_acceptance_sha256",gate["output_relative"]+"/input_acceptance.json"),("f01_report_sha256",gate["output_relative"]+"/f01_k64.json"),("resume_acceptance_sha256",gate["output_relative"]+"/resume_acceptance.json"),("resume_journal_sha256",gate["output_relative"]+"/f03_calls.jsonl")]:need(ident[key]==io.readmap[rel],"gate identity "+key)
  need(ident["frozen_model_sha256"]==report["frozen_model_sha256"]==f00["frozen_model_sha256"],"base frozen identity")
  savedorder=read(base+"/training_order.json")
  need(savedorder["samples"]==order and savedorder["order_sha256"]==report["sample_order_sha256"]==sig(order),"full40000 seeded order")
  need(savedorder["initial_scorer_sha256"]==report["initial_scorer_sha256"] and savedorder["train_pool_sha256"]==sig(train),"matched start")
  bytask=defaultdict(list)
  for wid in order:bytask[str(lookup[wid]["task_id"])].append(wid)
  sampling={t:{"samples":len(ids),"unique_windows":len(set(ids)),"unique_episodes":len({lookup[i]["episode_id"] for i in ids}),"phase_sample_counts":dict(Counter(lookup[i]["phase"] for i in ids))} for t,ids in bytask.items()}
  need(sampling==report["committed_sampling_by_task"]==report["attempted_completed_sampling_by_task"],"actual unique sampling")
  paths=sorted((R/base/"attempts").glob("*/cost_events.jsonl"));need(len(paths)==2,"two attempts")
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
      ids=x["retained_indices"];need(len(ids)==64 and ids==sorted(set(ids)) and all(type(i)==int and 0<=i<512 for i in ids) and sum(i<256 for i in ids)==32,"hard64 original packing")
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
  md=dep["metadata"];need(md["arm"]==arm and md["suite"]=="libero_object" and md["seed"]==41 and md["visual_tokens"]==64 and md["per_camera_budgets"]==[32,32] and md["update"]==best["update"],"deployment identity")
  close(md["validation_metric"],best["teacher_l1"])
  need(dep["evaluations"]==report["evaluations"] and dep["pair_config"]==config and dep["training_config"]=={**config,"arm":arm},"deployment original config and selection")
  resume=shafile(H/"checkpoints/formal_main_v2/libero_object/k64/seed41"/arm/"resume.pt");resume["arm"]=arm
  need(resume["sha256"]==allcommits[-1]["resume_sha256"] and resume==next(x for x in machine["server_resume_checks"] if x["arm"]==arm),"actual final resume")
  checkpoint=shafile(H/"checkpoints/formal_main_v2/libero_object/k64/seed41"/arm/"best.pt")
  proof=next(x for x in selected["checks"] if x["arm"]==arm)
  need(checkpoint["path"]==report["best_checkpoint"]==proof["path"] and checkpoint["sha256"]==dep["checkpoint_sha256"]==proof["sha256"] and checkpoint["bytes"]==proof["bytes"],"actual selected best")
  actualchecks.append(dict(arm=arm,resume=resume,best=checkpoint,selected_update=best["update"],validation_metric=best["teacher_l1"]))
  summaries[arm]=dict(completed_updates=5000,sample_uses=40000,unique_windows=len(set(sampleids)),cursor=40000,attempts=byattempt,validation=[vals[u] for u in sorted(vals)],earliest_selected_update=best["update"],selected_teacher_l1=best["teacher_l1"],selected_expert_l1=best["expert_l1"],best_sha256=checkpoint["sha256"],gradient_range=[min(grad),max(grad)],replayed_or_uncommitted_samples=0)
 need(initial["A"]==initial["B"] and reports["A"]["initial_scorer_sha256"]==reports["B"]["initial_scorer_sha256"],"matched AB")
 summary=read(REL+"/training_summary.json")
 need(summary["arms"]==reports and summary["status"]=="completed" and summary["pair_complete"] is True and summary["job_id"]=="3037535" and summary["test_opened"] is False and summary["checkpoint_unchanged"] is True,"pair complete")
 final=read(REL+"/finalizations/3037535_ff11e398c517.json")
 need(final["status"]=="verified" and final["kind"]=="training" and final["result_sha256"]==io.readmap[REL+"/training_summary.json"] and final["checkpoint_unchanged"] is True,"final source/base provenance")
 need(final["source_files"]==gate["source_files"]==summary["source_files"],"all producer sources")
 cache=Counter();paths=sorted((R/REL/"cache_events").glob("*.jsonl"));need(len(paths)==2,"two actual cache logs")
 for p in paths:
  for row in jrows(p.relative_to(R).as_posix()):
   need(row["job_id"] in jobs,"cache owner");cache[row["event"]]+=1
 need(dict(cache)==root["cache_event_counts"],"raw cache totals")
 pull=read(PULL,PULLSHA)
 need(pull["status"]=="verified_nonweight_snapshot" and pull["final_evidence"] is True and pull["weights_copied"] is False and pull["sealed_initial_states_copied"] is False and not pull["missing"] and not pull["skipped"],"complete final pull")
 before=read(str(Path(PULL).parent/"inventory_before.json"),pull["inventory_sha256"]);after=read(str(Path(PULL).parent/"inventory_after.json"))
 need(before==after,"stable double inventory");rows={r["relative"]:r for r in before["files"]};need(len(rows)==len(before["files"]),"unique inventory")
 for when in ["accounting_before","accounting_after"]:
  for jid,j in jobs.items():
   bill=pull[when]["jobs"][jid];need(all(bill[k]==j[k] for k in ["status","exit_code","elapsed_seconds"]),"actual bill")
   need(dict(x.split("=",1) for x in bill["allocation"].split(",") if "=" in x).get("gres/gpu")=="1","GPU allocated")
 for r in pull["files"]:
  rel=r["relative"];data=raw(rel,r["sha256"]);need(len(data)==r["bytes"],"pull bytes")
  need(all(r[k]==rows[rel][k] for k in ["path","sha256","bytes","job_ids"]),"pull stable values")
  need(r["path"]==str(P/rel) and r["action"] in ["same_sha_skipped","downloaded_verified"],"exact raw origin")
  need(shafile(P/rel)["sha256"]==r["sha256"],"P raw unchanged")
 for rel,h in root["files"].items():raw(rel,h)
 for rel,h in machine["raw_input_evidence"].items():
  if rel!="results/experiment_supervisor/state.json":raw(rel,h)
 for jid,j in jobs.items():
  receipt=read(f"results/formal_main_v2/job_receipts/{jid}.json")
  need(receipt["exit_code"]==receipt["runner_exit_code"]==0 and receipt["errors"]==[] and receipt["loader_restored"] is True and receipt["source_inputs_unchanged"] is True,"restored Object adapter")
  need(receipt["invocation_sha256"]==j["invocation_sha256"] and receipt["runtime_compatibility"]==j["runtime_compatibility"],"same actual metadata execution")
  events=jrows(REL+f"/compatibility/{jid}/compatibility_events.jsonl");need([r['event'] for r in events]==['stage_start','asset_metadata_compat_enter','stage_runner_start','asset_metadata_compat_load_start','asset_metadata_compat_load_complete','stage_runner_return','asset_metadata_compat_exit','stage_end'] and [r['seq'] for r in events]==list(range(8)),"exact8 metadata")
  shared=io.load('scripts/review_formal_acceptance.py');me=shared.Evidence(R)
  actualinv=read(j['invocation'],j['invocation_sha256'])
  rebuilt=shared.review_runtime_compatibility(me,job=j,invocation=actualinv,receipt=receipt,inventory=inventory,pull_receipt=PULL)
  need(rebuilt['event_count']==8,'original metadata verifier exact scope')
  me.unchanged()
  for rel,h in me.hashes.items():raw(rel,h)
 canonical_ref=REL+"/segment_reviews/3037535.json"
 canonical_sha="d2836fab19c5c11cd1baba1a102ec7e677ebab781091f2b2bcb103f35825ddf8"
 extra=read(canonical_ref,canonical_sha)
 need(extra["kind"]=="root_segment_review" and extra["status"]=="passed","canonical root typed")
 for key in ["job_id","suite","visual_tokens","seed","source_sha256","completed_by_arm","allowed_next_segment_end","resume_required","pair_allocated_gpu_seconds","cache_event_counts","files"]:
  need(extra[key]==root[key],"canonical root agrees with independent raw reconstruction "+key)
 need(extra["server_resume_checks"]==[x["resume"] for x in actualchecks],"canonical actual resume proof")
 root_best_ref="results/formal_main_v2/preflight/heartbeat_20261020T0632/3037535_selected_server.json"
 root_best_sha="eba38f0776ed8021f2ff77ac25d4bdd5fce52ff60fb5c2fa34fdfd7aa066a9bc"
 root_best=read(root_best_ref,root_best_sha)
 need(root_best["status"]=="verified_actual_server_bytes" and root_best["job_id"]=="3037535" and root_best["weights_copied"] is False and root_best["optimizer_rng_deserialized"] is False and root_best["root_review"]=={"path":canonical_ref,"sha256":canonical_sha},"root actual best proof exact binding")
 need(len(root_best["checks"])==2 and {x["arm"] for x in root_best["checks"]}=={"A","B"},"two actual selected checks")
 for x in actualchecks:
  proof=next(v for v in root_best["checks"] if v["arm"]==x["arm"])
  need(all(proof[k]==x["best"][k] for k in ["path","sha256","bytes"]),"fresh independently hashed best equals root bytes")
 parallel_root={"path":canonical_ref,"sha256":canonical_sha,"kind":extra["kind"],"status":extra["status"],"selected_server_proof":{"path":root_best_ref,"sha256":root_best_sha},"prior_reviewed_updates_per_arm":500,"new_reviewed_arm_updates":9000,"prior_root_review":{"path":prior_root_ref,"sha256":prior_root_sha},"prior_independent_review":{"path":prior_ind_ref,"sha256":prior_ind_sha}}
 raw("results/formal_main_v2/engineering/terminal_delivery_1518/independent/audit_3036313.py","41a4990834803841865431c553f0f89df681e7b1ee551d4e98c98ddd993898d0")
 raw("results/formal_main_v2/engineering/terminal_delivery_1932/independent/audit_3037054.py","f87bd1e386a09de6628abb3e35a33fe6b40bd566a4aba9c0d049be8d5b117ba6")
 raw("AGENTS.md","f32733b595a747a9f82f5ac5949ee62cfa5a9fc750c97f5e4fb97d0f6a9e4510")
 raw(Path(__file__).relative_to(R).as_posix())
 for rel,h in io.readmap.items():need(hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,"input drift")
 out=dict(schema="formal_main_v2",kind="independent_completed_training_review",status="passed_complete_training_only",job_id="3037535",suite="libero_object",visual_tokens=64,seed=41,machine_review={"path":ROOTREF,"sha256":ROOTSHA},selected_server_review={"path":SELECTED,"sha256":SELECTEDSHA},pull={"path":PULL,"sha256":PULLSHA},completed_by_arm={"A":5000,"B":5000},allowed_next_segment_end=None,resume_required=False,arms=summaries,actual_checkpoint_hashes=actualchecks,same_AB_initialization_and_full40000_order=True,all173_R_and_S_match=True,cost={"historical_segments_GPU_seconds":2645,"continuous_segment_GPU_seconds":60018,"all_pair_allocated_GPU_seconds":62663,"allocations":[{"job_id":j,"GPU_seconds":c} for j,c in zip(JOBS,COSTS)],"nested_phases_added":False},cache_event_counts=dict(cache),no_checkpoint_tensor_loaded=True,final_release_authorized=False,scientific_closed_loop_claimed=False,limitations=["Optimizer/RNG restoration is supported by the frozen load_state_dict/restore_rng path, real resumed attempt and exact before/after checkpoint hashes; tensors were not independently deserialized.","Submitted 48h argv is bound as submission evidence, not re-labelled as a fresh scheduler TimeLimit observation.","Selected update/metric are independently reconstructed from raw validation plus deployment metadata; the machine byte probe does not assert these validation fields."],read_evidence_sha256=dict(sorted(io.readmap.items())),server_read_evidence_sha256=dict(sorted(io.servermap.items())),parallel_root_reconstruction=parallel_root,machine_status_not_claimed_as_independence=True,mutable_state_used_as_current_evidence=False,reviewed_utc=datetime.now(timezone.utc).isoformat())
 dest=D/"3037535_independent_review.json"
 with dest.open("x") as f:json.dump(out,f,sort_keys=True,indent=2);f.write("\n")
 print(json.dumps(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),status=out["status"],cost=out["cost"],arms={a:{k:summaries[a][k] for k in ["completed_updates","sample_uses","unique_windows","earliest_selected_update","selected_teacher_l1","best_sha256"]} for a in summaries},refs=len(io.readmap))))
if __name__=="__main__":main()
