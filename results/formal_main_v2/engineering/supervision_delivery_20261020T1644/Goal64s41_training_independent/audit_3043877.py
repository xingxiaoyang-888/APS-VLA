"""Independent Goal64 seed41 terminal training audit, server-only CPU/byte hashes.
Uses unchanged private I/O primitives only; raw counters/selection recomputed here.
No scheduler, state, Git, tensor deserialization, or final-state access.
"""
from pathlib import Path
from collections import Counter, defaultdict
import ast,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/Goal64s41_independent_20261020T1644"
helper=R/"results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258.py"
assert hashlib.sha256(helper.read_bytes()).hexdigest()=="fd566045bc20e76a10dc05b7ed56377d9817231bb5538eb828c087eb7dd5ef1a"
sp=importlib.util.spec_from_file_location("independent_io_0943",helper)
io=importlib.util.module_from_spec(sp);sp.loader.exec_module(io)
need,read,raw,jrows,close,sig,shafile=io.need,io.read,io.raw,io.jrows,io.close,io.sig,io.shafile
P,H,S=io.P,io.H,io.S
REL="results/formal_main_v2/libero_goal/k64/seed41/training"
MACHINE_DIR="results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k64_seed41_52f6f42a36e14f90b7e9bdd1e7ec0f0e"
ROOTREF=MACHINE_DIR+"/machine_review.json"
ROOTSHA="0d005f0dd0f61a637fb3e5b4b579d910777fb864b7f3bd12e0960d0d3592cc20"
SELECTED=MACHINE_DIR+"/selected_server_hashes.json"
SELECTEDSHA="ba5a413defe4164a6078d59c82f9173b0b1fdee6bebc57a4fddd6c4994ebfbc0"
PULL="results/formal_main_v2/pulls/20261020T154007Z_c117dc57f32d/receipt.json"
PULLSHA="3100cca98ad41b65f10ed707455462bcf845ae0aba513d96160ad44d777a9750"
JOBS=["3043877"]
ENDS=[5000]
STARTS=[0]
COSTS=[59575]

def validate_hard64_observation(x,ref):
 need(x["episode_id"]==ref["episode_id"] and x["task_id"]==ref["task_id"],"val source")
 ids=x["retained_indices"]
 need(len(ids)==64 and all(type(i)==int and 0<=i<512 for i in ids) and ids==sorted(set(ids)) and sum(i<256 for i in ids)==32,"hard64 original packing")
 actions=x["normalized_actions"]
 need(len(actions)==8 and all(len(y)==7 for y in actions) and all(type(z) in (int,float) and math.isfinite(z) for y in actions for z in y),"finite8x7")
 for name in ("teacher_l1","demonstration_l1"):
  need(type(x[name]) in (int,float) and math.isfinite(x[name]) and x[name]>=0,"finite nonnegative validation metric")

def select_validation(vals):
 need(sorted(vals)==list(range(0,5001,500)),"all eleven selection nodes required")
 for key,v in vals.items():
  need(v["update"]==key,"selection node identity")
  need(type(v["teacher_l1"]) in (int,float) and math.isfinite(v["teacher_l1"]) and v["teacher_l1"]>=0,"finite nonnegative selection metric")
 return min(vals.values(),key=lambda v:(v["teacher_l1"],v["update"]))

def audit_inherited_goal_resume(gate,f00,source):
 ref=gate["output_relative"]+"/resume_acceptance.json"
 report=read(ref,gate["files"]["resume_acceptance.json"])
 need(report["kind"]=="resume_acceptance" and report["status"]=="passed" and report["execution"]=="real_frozen_openvla_slurm" and report["job_id"]=="3012579" and report["suite"]=="libero_goal","inherited real Goal F03 identity")
 need(report["comparison"]=="bitwise equality; no numeric tolerance applied" and report["planned_updates"]==5000 and report["effective_batch"]==8 and report["actual_forward_backward_samples"]==48,"inherited restore scope")
 need(report["test_opened"] is False and report["engineering_weights_reused_for_training"] is False and report["formal_selector_produced"] is False and report["matched_ab_initialization"] is True,"inherited engineering scope only")
 need(report["source_files"]==source and report["frozen_model_sha256"]==f00["frozen_model_sha256"] and report["model_revision"]=="c2d0f9fbbd82674683b397ff923168a12f6a307b","inherited same frozen source/base")
 need(report["validation_updates"]==list(range(0,5001,500)) and report["alpha_first"]==2.0 and report["alpha_last"]==.1,"inherited5000 schedule")
 journal=raw(gate["output_relative"]+"/f03_calls.jsonl",report["journal_sha256"])
 need(len(journal)==report["journal_bytes"]==60942,"inherited original probe journal")
 checked=[]
 for arm,entry in report["arms"].items():
  need(arm in ("A","B") and entry["arm"]==arm and entry["completed_probe_updates"]==2 and entry["next_sample_cursor"]==16 and entry["planned_updates"]==5000,"inherited two update cursor")
  expected_checks={"die_updated","frozen_model_unchanged","head_equal","next_sample_cursor_equal","optimizer_equal","rng_equal","rng_probe_equal","scheduler_position_equal","scorer_equal","step1_snapshot_equal","vla_gradients_absent"}
  need(set(entry["checks"])==expected_checks and all(v is True for v in entry["checks"].values()),"all inherited restore checks")
  need(set(entry["comparisons"])=={"head","optimizer","rng","rng_probe","scorer"},"all inherited restore comparisons")
  for value in entry["comparisons"].values():
   need(value["equal"] is True and value["differences"]==[] and value["reference_sha256"]==value["resumed_sha256"],"exact inherited optimizer/RNG/scorer/head bitwise comparison")
  actual={}
  for pathkey,hashkey in [("step1_checkpoint","step1_checkpoint_sha256"),("continuous_step2_checkpoint","continuous_step2_sha256"),("resumed_step2_checkpoint","resumed_step2_sha256")]:
   path=Path(entry[pathkey]);need(path.is_relative_to(H/"checkpoints/formal_main_v2/engineering/libero_goal/3012579_68caa7d4fc3a/job_3012579"),"exact inherited engineering checkpoint scope")
   actual[pathkey]=shafile(path);need(actual[pathkey]["sha256"]==entry[hashkey],"actual inherited engineering checkpoint bytes")
  need(actual["continuous_step2_checkpoint"]["sha256"]==actual["resumed_step2_checkpoint"]["sha256"],"actual inherited continuous/resumed equality")
  checked.append({"arm":arm,"checks":entry["checks"],"comparisons":entry["comparisons"],"actual_server_checkpoints":actual})
 need(len(checked)==2,"two inherited F03 arms")
 return {"path":ref,"sha256":io.readmap[ref],"job_id":"3012579","probe_seed":report["accepted_pair_config"]["seed"],"probe_visual_tokens":report["accepted_pair_config"]["tokens_per_camera"]*2,"inherited_shared_implementation_qualification_only":True,"this_pair_cross_job_restore_performed":False,"arms":checked,"actual_forward_backward_samples":48,"shared_prerequisite_cost_not_added_to_current_pair":True,"checkpoint_tensors_deserialized":False}

def main():
 raw(helper.relative_to(R).as_posix())
 machine=read(ROOTREF,ROOTSHA);selected=read(SELECTED,SELECTEDSHA)
 need(machine["kind"]=="automatic_machine_training_review" and machine["status"]=="passed_machine_reconstruction" and machine["root_signature_claimed"] is False and machine["independent_review"] is False,"machine identity not independent")
 root=machine["original_review"]
 need(root["status"]=="local_passed_remote_required" and root["completed_by_arm"]=={"A":5000,"B":5000},"original machine raw preserved")
 raw(machine["reviewer"]["path"],machine["reviewer"]["sha256"])
 raw("SERVER_WORKSPACE.md","fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62")
 raw("docs/服务器工作区与GitHub同步.md","d7f0455ef4febb536df199653fd323a1cef98ad66732e5b2ea8edfdf06b75343")
 raw("results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3034570_v3.py","bdca1e2f330ca32abc0aecf2ecc31a8f1a4769c3cb1a28d8ced479ac12645b64")
 need(root["job_id"]=="3043877" and root["suite"]=="libero_goal" and root["visual_tokens"]==64 and root["seed"]==41,"root pair")
 need(root["allowed_next_segment_end"] is None and root["resume_required"] is False,"no5500")
 need(selected["status"]=="verified_actual_server_bytes" and selected["kind"]=="automatic_machine_selected_checkpoint_hashes" and selected["job_id"]=="3043877" and selected["root_signature_claimed"] is False,"machine actual best proof")
 inventory=read("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
 need(len(inventory["files"])==413 and root["source_sha256"]==inventory["source_sha256"],"source173")
 for rel,h in inventory["files"].items():
  raw(rel,h);need(shafile(S/rel)["sha256"]==h,"actual S source "+rel)
 configrel="configs/experiments/formal_main_v2/libero_goal_k64_seed41.json"
 config=read(configrel,inventory["files"][configrel]);need(read(REL+"/registered_config.json")==config,"run config")
 need(config["seed"]==41 and config["tokens_per_camera"]==32 and config["training"]["updates"]==5000 and config["training"]["effective_batch"]==8,"full unchanged config")
 need(config["selection"]["updates"]==list(range(0,5001,500)),"11 validation nodes")
 jobs={str(j["job_id"]):j for j in root["registered_pair_jobs_at_review"]}
 need(set(jobs)==set(JOBS) and len(root["registered_pair_jobs_at_review"])==1,"exact one fresh allocation")
 for jid,cost,end in zip(JOBS,COSTS,ENDS):
  j=jobs[jid];need((j["status"],j["exit_code"],j["elapsed_seconds"],j["gpus"],j["segment_end"])==("COMPLETED","0:0",cost,1,end),"terminal bill")
 need(sum(j["elapsed_seconds"]*j["gpus"] for j in jobs.values())==root["pair_allocated_gpu_seconds"]==59575,"actual unique bill")
 newinv=read(jobs["3043877"]["invocation"],jobs["3043877"]["invocation_sha256"])
 contract=newinv["autonomous_execution"];need(contract==jobs["3043877"]["autonomous_execution"],"same execution contract")
 need(contract["target_updates_per_arm"]==5000 and contract["soft_wall_seconds"]==169200 and contract["allocation_time"]=="48:00:00","continuous engineering target")
 need(contract["completed_before"]=={"A":0,"B":0} and contract["predecessor_review"] is None and contract["resume_checks_before"]==[],"fresh no invented prior boundary")
 for key in ["authorization","adapter","source_inventory","acceptance_review"]:
  ref=contract[key];raw(ref["path"],ref["sha256"])
 need("--resume" not in newinv["argv"] and newinv["repair_record"] is None,"fresh attempt does not invoke resume/repair")
 base=json.loads(json.dumps(newinv));base.pop("autonomous_execution");base["segment_end"]=500
 for key,value in [("--stop-after-updates","500"),("--max-wall-seconds","12600")]:
  need(base["argv"].count(key)==1,"one execution option");base["argv"][base["argv"].index(key)+1]=value
 need(sig(base)==contract["base_invocation_sha256"],"original pure base invocation exact semantic SHA")
 need(contract["changed_options"]=={"--max-wall-seconds":{"after":"169200","before":"12600"},"--stop-after-updates":{"after":"5000","before":"500"}},"only original target/wall adaptation")
 need(contract["validation_updates"]==list(range(0,5001,500)) and contract["checkpoint_every_updates"]==50 and contract["original_sequential_A_B"] is True,"original training/selection cadence")
 prior_checks=[]
 request=read(MACHINE_DIR+"/request.json","b6f947a447216acff534e30cbc3d958fe86707000da4ce086e2479e0b1502ce9")
 need(request["job_id"]=="3043877" and request["pair_key"]=="libero_goal_k64_seed41" and request["mode"]=="terminal" and request["check_only"] is False,"machine exact request")
 raw(MACHINE_DIR+"/outcome.json","c08fb4bcfcab748885f45216b9d800350849854aba39cad76f5d254c634bd587")
 argv=jobs["3043877"]["autonomous_control"]["actual_sbatch_argv"]
 for x in ["--no-requeue","--time=48:00:00","--gres=gpu:l40:1","--exclude=gpu4020","--job-name=cti-formal"]:need(x in argv,"actual submitted option "+x)
 gate=read("results/formal_main_v2/libero_goal/acceptance/root_review.json")
 need(gate["status"]=="passed" and gate["source_sha256"]==root["source_sha256"],"own GPU acceptance")
 need(gate["suite"]=="libero_goal" and gate["job_id"]=="3012579" and newinv["runtime_compatibility"]==gate["runtime_compatibility"] and newinv["component_compatibility"]==gate["component_compatibility"],"own accepted Goal exact6+4 runtime")
 registration=read("configs/experiments/formal_main_v2.json",inventory["files"]["configs/experiments/formal_main_v2.json"])
 suite=registration["suites"]["libero_goal"];pairs=[p for p in registration["pairs"] if p["suite"]=="libero_goal" and p["visual_tokens"]==64 and p["seed"]==41];need(len(pairs)==1,"exact registered pair");pair=pairs[0]
 expected=["--config",str(S/pair["path"]),"--protocol",str(P/suite["protocol"]),"--windows",str(P/suite["windows"]),"--checkpoint",suite["model_root_server"],"--asset-manifest",str(S/suite["model_manifest"]),"--data-directory",suite["data_root_server"],"--cache-directory",str(P/".local/formal-hf-libero_goal"),"--feature-cache",suite["cache_root_server"],"--training-checkpoints",pair["checkpoint_root_server"],"--input-acceptance-report",str(P/gate["output_relative"]/"input_acceptance.json"),"--acceptance-report",str(P/gate["output_relative"]/"f01_k64.json"),"--output",str(P/REL),"--arm","both","--stop-after-updates","5000","--max-wall-seconds","169200"]
 need(newinv["argv"]==expected,"full Goal scientific argv rebuilt from original registration")
 component_reg=read(newinv["component_compatibility"]["registration"],newinv["component_compatibility"]["files"][newinv["component_compatibility"]["registration"]])
 model=read(component_reg["model_manifest"],component_reg["model_manifest_sha256"])
 need(model["repository"]=="moojink/openvla-7b-oft-finetuned-libero-goal" and model["revision"]==config["model_revision"]==component_reg["model_revision"] and component_reg["checkpoint_root"]==suite["model_root_server"],"Goal official base identity")
 need(component_reg["loader_sha256"]==inventory["files"][component_reg["loader"]] and component_reg["original_component_loader_used"] is True and component_reg["torch_load_replaced"] is False and component_reg["weights_changed"] is False,"original loader retained")
 need([(v["requested"],v["target"]) for v in component_reg["mappings"]]==[("action_head--150000_checkpoint.pt","action_head--50000_checkpoint.pt"),("proprio_projector--150000_checkpoint.pt","proprio_projector--50000_checkpoint.pt")],"only exact official50000 filename projection")
 official_components=[]
 for mp in component_reg["mappings"]:
  source=next(v for v in model["files"] if v["path"]==mp["target"]);need(source["sha256"]==mp["sha256"] and source["size"]==mp["size"],"registered component official bytes")
  actual=shafile(Path(component_reg["checkpoint_root"])/mp["target"]);need(actual["sha256"]==mp["sha256"] and actual["bytes"]==mp["size"],"actual official50000 component bytes");official_components.append(actual)
 for name,h in gate["files"].items():raw(gate["output_relative"]+"/"+name,h)
 f00=read(gate["output_relative"]+"/input_acceptance.json")
 for rel,h in gate["source_files"].items():raw(rel,h)
 inherited_resume=audit_inherited_goal_resume(gate,f00,gate["source_files"])
 protocol=read(config["data"]["protocol"]);manifest=read(config["data"]["windows"])
 sys.path.insert(0,str(R/"src"))
 from cti_vla.data.formal_windows import load_formal_protocol,load_formal_windows
 checked=load_formal_protocol(R/config["data"]["protocol"],project_root=R)
 need(load_formal_windows(R/config["data"]["windows"],checked)==manifest,"full legal window manifest")
 train=manifest["train_window_ids"];val=manifest["validation_window_ids"];lookup={r["window_id"]:r for r in manifest["windows"]}
 need(len(train)==33859 and len(set(train))==33859 and len(val)==len(set(val))==186,"full train/validation pools")
 need(not set(train)&set(val) and not {lookup[x]["episode_id"] for x in train}&{lookup[x]["episode_id"] for x in val},"episode isolation")
 rng=random.Random(41);order=[]
 while len(order)<40000:
  epoch=list(train);rng.shuffle(epoch);order.extend(epoch)
 order=order[:40000]
 need(len(set(order))==33859 and len(order)-len(set(order))==6141,"one full epoch plus legal repeat uses")
 constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(raw("src/cti_vla/training/formal_future.py").decode()).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith("FORMAL_")}
 trainer=raw("src/cti_vla/training/formal_future.py").decode()
 need('optimizer.load_state_dict(saved["optimizer"])' in trainer and 'restore_rng(saved["rng"])' in trainer,"frozen restoration path")
 reports={};summaries={};initial={};actualchecks=[]
 for arm in ["A","B"]:
  base=REL+"/"+arm;report=read(base+"/training_report.json");reports[arm]=report
  for key,value in {"schema":"formal_main_v2","arm":arm,"status":"completed","training_updates_completed":5000,"committed_samples":40000,"next_sample_cursor":40000,"unique_committed_windows":len(set(order)),"attempted_forward_backward_samples_completed":40000,"train_pool_windows":33859,"validation_pool_windows":186,"vla_parameters_unchanged":True,"attempts":1,"resumed_from_update":0,"job_ids":JOBS}.items():
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
  paths=sorted((R/base/"attempts").glob("*/cost_events.jsonl"));need(len(paths)==1,"one fresh attempt")
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
     need(active is None and validating is None and r["update"]==cur and cur in range(0,5001,500) and cur not in vals and r["windows"]==186,"exact node once");validating=cur
    elif e=="validation_end":
     need(validating==r["update"] and r["window_forwards"]==186,"full validation")
     vr=base+"/attempts/"+attempt+"/validation_"+str(validating).zfill(5)+".json";v=read(vr,r["artifact_sha256"])
     need(v["arm"]==arm and v["update"]==validating and v["job_id"]==jid and v["attempt_id"]==attempt and v["windows"]==186 and v["tasks"]==10 and v["metric"]=="task_macro_hard_validation_teacher_l1","validation identity")
     need([x["window_id"] for x in v["observations"]]==val,"full ordered186")
     task=defaultdict(list)
     for x in v["observations"]:
      ref=lookup[x["window_id"]];validate_hard64_observation(x,ref)
      task[str(x["task_id"])].append(x)
     need(len(task)==10,"10 tasks")
     metric=sum(sum(x["teacher_l1"] for x in xs)/len(xs) for xs in task.values())/10
     expert=sum(sum(x["demonstration_l1"] for x in xs)/len(xs) for xs in task.values())/10
     close(metric,v["validation_metric"]);close(metric,r["validation_metric"]);close(expert,v["demonstration_l1"])
     for t,xs in task.items():
      need(v["per_task"][t]["windows"]==len(xs),"task count")
      for k in ["teacher_l1","demonstration_l1"]:close(v["per_task"][t][k],sum(x[k] for x in xs)/len(xs))
     close(v["window_weighted_teacher_l1_diagnostic"],sum(x["teacher_l1"] for x in v["observations"])/186)
     vals[validating]={"update":validating,"teacher_l1":metric,"expert_l1":expert,"path":vr,"sha256":io.readmap[vr]}
     if validating==0:initial[arm]=[{k:x[k] for k in ["window_id","episode_id","task_id","teacher_l1","demonstration_l1","retained_indices","normalized_actions"]} for x in v["observations"]]
     validating=None;v_count+=1
    elif e=="checkpoint_commit":
     need(active is None and validating is None and r["completed_update"]==cur,"atomic committed update")
     commits.append(r);allcommits.append(r)
    elif e=="attempt_end":
     need(active is None and validating is None and cur==end and r["completed_update"]==end and r["status"]==("checkpointed" if index<0 else "completed"),"clean committed attempt")
     need(commits[-1]["completed_update"]==end,"last checkpoint");ended=True
    else:raise ValueError("unknown event "+e)
   need(ended and u_count==[5000][index] and v_count==[11][index],"full attempt work")
   byattempt.append({"job_id":jid,"attempt_id":attempt,"start_update":STARTS[index],"end_update":end,"updates":u_count,"validation_nodes":v_count,"journal_rows":len(rows),"last_resume_sha256":commits[-1]["resume_sha256"]})
  need(cur==5000 and sampleids==order and len(sampleids)==40000 and len(set(sampleids))==len(set(order)),"no missing/replayed samples")
  need(set(x["completed_update"] for x in allcommits)==set(range(0,5001,50)) and len(grad)==5000 and max(grad)>0,"all checkpoint/gradient evidence")
  need(sorted(vals)==list(range(0,5001,500)) and [v["update"] for v in report["evaluations"]]==sorted(vals),"11 selection nodes")
  for v in report["evaluations"]:
   obs=vals[v["update"]];need(v["artifact_sha256"]==obs["sha256"] and v["artifact_path"]==str(P/obs["path"]),"raw selection binding");close(v["validation_metric"],obs["teacher_l1"])
  best=select_validation(vals)
  need(report["best_update"]==best["update"],"earliest min selection");close(report["best_validation_metric"],best["teacher_l1"])
  dep=read(base+"/deployment_receipt.json")
  need(dep["training_complete"] is True and dep["base_frozen"] is True and dep["checkpoint_unchanged"] is True and dep["completed_updates"]==dep["planned_updates"]==5000,"completed deployment")
  need(dep["checkpoint_sha256"]==report["best_checkpoint_sha256"] and dep["metadata_sha256"]==sig(dep["metadata"]),"deployment SHA")
  md=dep["metadata"];need(md["arm"]==arm and md["suite"]=="libero_goal" and md["seed"]==41 and md["visual_tokens"]==64 and md["per_camera_budgets"]==[32,32] and md["update"]==best["update"],"deployment identity")
  close(md["validation_metric"],best["teacher_l1"])
  need(dep["evaluations"]==report["evaluations"] and dep["pair_config"]==config and dep["training_config"]=={**config,"arm":arm},"deployment original config and selection")
  resume=shafile(H/"checkpoints/formal_main_v2/libero_goal/k64/seed41"/arm/"resume.pt");resume["arm"]=arm
  need(resume["sha256"]==allcommits[-1]["resume_sha256"] and resume==next(x for x in machine["server_resume_checks"] if x["arm"]==arm),"actual final resume")
  checkpoint=shafile(H/"checkpoints/formal_main_v2/libero_goal/k64/seed41"/arm/"best.pt")
  proof=next(x for x in selected["checks"] if x["arm"]==arm)
  need(checkpoint["path"]==report["best_checkpoint"]==proof["path"] and checkpoint["sha256"]==dep["checkpoint_sha256"]==proof["sha256"] and checkpoint["bytes"]==proof["bytes"],"actual selected best")
  actualchecks.append(dict(arm=arm,resume=resume,best=checkpoint,selected_update=best["update"],validation_metric=best["teacher_l1"]))
  summaries[arm]=dict(completed_updates=5000,sample_uses=40000,unique_windows=len(set(sampleids)),cursor=40000,attempts=byattempt,validation=[vals[u] for u in sorted(vals)],earliest_selected_update=best["update"],selected_teacher_l1=best["teacher_l1"],selected_expert_l1=best["expert_l1"],best_sha256=checkpoint["sha256"],gradient_range=[min(grad),max(grad)],replayed_or_uncommitted_samples=0,committed_sampling_by_task=sampling,window_pool_coverage=1.0,window_pool_equivalent_traversals=40000/33859)
 need(initial["A"]==initial["B"] and reports["A"]["initial_scorer_sha256"]==reports["B"]["initial_scorer_sha256"],"matched AB")
 summary=read(REL+"/training_summary.json")
 need(summary["arms"]==reports and summary["status"]=="completed" and summary["pair_complete"] is True and summary["job_id"]=="3043877" and summary["test_opened"] is False and summary["checkpoint_unchanged"] is True,"pair complete")
 final=read(REL+"/finalizations/3043877_8493c542000b.json")
 need(final["status"]=="verified" and final["kind"]=="training" and final["result_sha256"]==io.readmap[REL+"/training_summary.json"] and final["checkpoint_unchanged"] is True,"final source/base provenance")
 need(final["source_files"]==gate["source_files"]==summary["source_files"],"all producer sources")
 cache=Counter();paths=sorted((R/REL/"cache_events").glob("*.jsonl"));need(len(paths)==1,"one actual cache log")
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
 asset_reviews={}
 for jid,j in jobs.items():
  receipt=read(f"results/formal_main_v2/job_receipts/{jid}.json")
  need(receipt["exit_code"]==receipt["runner_exit_code"]==0 and receipt["errors"]==[] and receipt["loader_restored"] is True and receipt["source_inputs_unchanged"] is True,"restored Goal metadata adapter")
  need(receipt["invocation_sha256"]==j["invocation_sha256"] and receipt["runtime_compatibility"]==j["runtime_compatibility"],"same actual metadata execution")
  events=jrows(REL+f"/compatibility/{jid}/compatibility_events.jsonl");need([r['event'] for r in events]==['stage_start','asset_metadata_compat_enter','stage_runner_start','asset_metadata_compat_load_start','asset_metadata_compat_load_complete','stage_runner_return','asset_metadata_compat_exit','stage_end'] and [r['seq'] for r in events]==list(range(8)),"exact8 metadata")
  shared=io.load('scripts/review_formal_acceptance.py');me=shared.Evidence(R)
  actualinv=read(j['invocation'],j['invocation_sha256'])
  rebuilt=shared.review_runtime_compatibility(me,job=j,invocation=actualinv,receipt=receipt,inventory=inventory,pull_receipt=PULL)
  need(rebuilt['event_count']==8,'original metadata verifier exact scope')
  component=shared.review_component_compatibility(me,job=j,invocation=actualinv,receipt=receipt,inventory=inventory,metadata_review=rebuilt,pull_receipt=PULL)
  need(component["status"]=="verified" and component["event_count"]==10 and component["exact_component_loads"]==2 and component["original_loader_restored"] is True and component["torch_load_replaced"] is False,"original Goal component verifier")
  asset_reviews[jid]={"metadata":rebuilt,"component":component,"elapsed_seconds":j["elapsed_seconds"],"nested_phase_times_added":False}
  me.unchanged()
  for rel,h in me.hashes.items():raw(rel,h)
 gatejob=gate["job_at_review"];gateinv=read(gatejob["invocation"],gatejob["invocation_sha256"]);gatereceipt=read(f"results/formal_main_v2/job_receipts/{gatejob['job_id']}.json")
 gatepull=gate["runtime_compatibility_review"]["pull_receipt"];raw(gatepull["path"],gatepull["sha256"])
 ge=shared.Evidence(R)
 for rel,h in gate["component_compatibility_review"]["evidence_sha256"].items():need(ge.watch(rel)==h,"original acceptance proof input unchanged")
 gm=shared.review_runtime_compatibility(ge,job=gatejob,invocation=gateinv,receipt=gatereceipt,inventory=inventory,pull_receipt=gatepull["path"])
 gc=shared.review_component_compatibility(ge,job=gatejob,invocation=gateinv,receipt=gatereceipt,inventory=inventory,metadata_review=gm,pull_receipt=gatepull["path"])
 need(gm==gate["runtime_compatibility_review"] and gc==gate["component_compatibility_review"],"original accepted Goal proof fully reconstructed")
 ge.unchanged()
 for rel,h in ge.hashes.items():raw(rel,h)
 asset_reviews[str(gatejob["job_id"]) ]={"metadata":gm,"component":gc,"elapsed_seconds":gatejob["elapsed_seconds"],"shared_prerequisite_not_added_to_pair_bill":True}
 canonical_ref=REL+"/segment_reviews/3043877.json"
 canonical_sha="121ea7c85950ee7b162b642e2e14880f2ec1eb4a1ffcfe3cf34a9ab2b19f6c60"
 extra=read(canonical_ref,canonical_sha)
 need(extra["kind"]=="root_segment_review" and extra["status"]=="passed","canonical root typed")
 for key in ["job_id","suite","visual_tokens","seed","source_sha256","completed_by_arm","allowed_next_segment_end","resume_required","pair_allocated_gpu_seconds","cache_event_counts","files"]:
  need(extra[key]==root[key],"canonical root agrees with independent raw reconstruction "+key)
 need(extra["server_resume_checks"]==[x["resume"] for x in actualchecks],"canonical actual resume proof")
 root_best_ref="results/formal_main_v2/preflight/heartbeat_20261021T0044/3043877_selected_server.json"
 root_best_sha="2731875fc1c0b0a9ef9c57e433fa682969ebf2f172c903dbde89aafb02a73e8c"
 root_best=read(root_best_ref,root_best_sha)
 need(root_best["status"]=="verified_actual_server_bytes" and root_best["job_id"]=="3043877" and root_best["weights_copied"] is False and root_best["optimizer_rng_deserialized"] is False and root_best["root_review"]=={"path":canonical_ref,"sha256":canonical_sha},"root actual best proof exact binding")
 need(len(root_best["checks"])==2 and {x["arm"] for x in root_best["checks"]}=={"A","B"},"two actual selected checks")
 for x in actualchecks:
  proof=next(v for v in root_best["checks"] if v["arm"]==x["arm"])
  need(all(proof[k]==x["best"][k] for k in ["path","sha256","bytes"]),"fresh independently hashed best equals root bytes")
 root_terminal_ref="results/formal_main_v2/preflight/heartbeat_20261021T0044/3043877_root_terminal.json"
 root_terminal=read(root_terminal_ref,"1fc9190ec8ea26c2a655cb9a5c90913f0410ec05b23487475f895871fdede835")
 need(root_terminal["root_review"]=={"path":canonical_ref,"sha256":canonical_sha} and root_terminal["selected_server"]=={"path":root_best_ref,"sha256":root_best_sha} and root_terminal["completed_by_arm"]=={"A":5000,"B":5000} and root_terminal["pair_allocated_GPU_seconds"]==59575 and root_terminal["independent_review_integrated"] is False,"root terminal exact independent pending binding")
 parallel_root={"path":canonical_ref,"sha256":canonical_sha,"kind":extra["kind"],"status":extra["status"],"selected_server_proof":{"path":root_best_ref,"sha256":root_best_sha},"prior_reviewed_updates_per_arm":0,"new_reviewed_arm_updates":10000,"fresh_pair":True}
 raw("results/formal_main_v2/engineering/terminal_delivery_1518/independent/audit_3036313.py","41a4990834803841865431c553f0f89df681e7b1ee551d4e98c98ddd993898d0")
 raw("results/formal_main_v2/engineering/supervision_delivery_2232/Object64seed41_independent/audit_3037535.py","8915925e39aebb194d9b25368025db293ada03e6baf1bf3e6f48ba7ee98e5514")
 raw("AGENTS.md","f32733b595a747a9f82f5ac5949ee62cfa5a9fc750c97f5e4fb97d0f6a9e4510")
 archive_inputs_ref="results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal3043877_archive_inputs.json"
 archive_inputs=read(archive_inputs_ref,"aa11c9f5c7164dcc6ef97a28c3f7e280f9e9c43316fb906ea821776ada7d1f92")
 snapshot="results/formal_main_v2/nonweight_archives/v1/snapshots/Goal64seed41_20261020T1530.json";snapshot_sha="caf74020b7a320bf41fb975ec8a8dcd10b54d9dc800ac51c28cd61d027ee341c"
 raw("scripts/ops/nonweight_archive.py","f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2")
 codec=io.load("scripts/ops/nonweight_archive.py")
 value,evidence,objects,chunks=codec.verified_plan(R,snapshot,snapshot_sha)
 need(len(value["files"])==3 and sum(x["bytes"] for x in value["files"])==186620031,"exact three original archived logs")
 need([{k:x[k] for k in ["path","sha256","bytes"]} for x in value["files"]]==archive_inputs["raw"],"archive input exact original raw map")
 for ref,role in evidence.values():
  data=raw(ref["path"],ref["sha256"]);need(len(data)==ref["bytes"],"archive evidence bytes")
 recovered=[]
 class CompareSink:
  def __init__(self,stream):self.stream=stream;self.h=hashlib.sha256();self.n=0
  def write(self,data):
   need(self.stream.read(len(data))==data,"archive reconstructed chunk differs from retained original bytes")
   self.h.update(data);self.n+=len(data);return len(data)
 for row in value["files"]:
  need(io.readmap[row["path"]]==row["sha256"],"archived content equals independently parsed training evidence")
  with (R/row["path"]).open("rb") as stream:
   sink=CompareSink(stream);codec.verify_object(R,row["manifest"],row["sha256"],row["bytes"],sink=sink)
   need(stream.read(1)==b"" and sink.n==row["bytes"] and sink.h.hexdigest()==row["sha256"],"lossless whole-file reconstruction")
  recovered.append({"path":row["path"],"sha256":sink.h.hexdigest(),"bytes":sink.n,"byte_equal_to_retained_original":True})
 archive_review={"snapshot":{"path":snapshot,"sha256":snapshot_sha},"input_registration":{"path":archive_inputs_ref,"sha256":io.readmap[archive_inputs_ref]},"files":recovered,"filesystem_restoration_performed":False,"summary":codec.summary(snapshot,snapshot_sha,value,objects,chunks,"verified")}
 raw(Path(__file__).relative_to(R).as_posix())
 for rel,h in io.readmap.items():need(hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,"input drift")
 out=dict(schema="formal_main_v2",kind="independent_completed_training_review",status="passed_complete_training_only",job_id="3043877",suite="libero_goal",visual_tokens=64,seed=41,machine_review={"path":ROOTREF,"sha256":ROOTSHA},selected_server_review={"path":SELECTED,"sha256":SELECTEDSHA},pull={"path":PULL,"sha256":PULLSHA},completed_by_arm={"A":5000,"B":5000},allowed_next_segment_end=None,resume_required=False,arms=summaries,actual_checkpoint_hashes=actualchecks,same_AB_initialization_and_full40000_order=True,legal_repeated_sample_uses_per_arm=6141,official_Goal_components=official_components,asset_compatibility_stages=asset_reviews,inherited_resume_qualification=inherited_resume,archive_reconstruction=archive_review,all173_R_and_S_match=True,cost={"historical_segments_GPU_seconds":0,"continuous_segment_GPU_seconds":59575,"all_pair_allocated_GPU_seconds":59575,"allocations":[{"job_id":j,"GPU_seconds":c} for j,c in zip(JOBS,COSTS)],"nested_phases_added":False},cache_event_counts=dict(cache),no_checkpoint_tensor_loaded=True,final_release_authorized=False,scientific_closed_loop_claimed=False,limitations=["This was a single fresh attempt per arm, with no cross-job restore. All 50-update commits and final resume hashes were checked; inherited Goal F03/source and rehashed engineering checkpoints supply shared implementation restoration qualification (seed17,k128). Optimizer/RNG tensors were not independently deserialized.","Submitted 48h argv is bound as submission evidence, not re-labelled as a fresh scheduler TimeLimit observation.","Selected update/metric are independently reconstructed from raw validation plus deployment metadata; the machine byte probe does not assert these validation fields."],read_evidence_sha256=dict(sorted(io.readmap.items())),server_read_evidence_sha256=dict(sorted(io.servermap.items())),parallel_root_reconstruction=parallel_root,machine_status_not_claimed_as_independence=True,mutable_state_used_as_current_evidence=False,reviewed_utc=datetime.now(timezone.utc).isoformat())
 dest=D/"3043877_independent_review.json"
 with dest.open("x") as f:json.dump(out,f,sort_keys=True,indent=2);f.write("\n")
 print(json.dumps(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),status=out["status"],cost=out["cost"],arms={a:{k:summaries[a][k] for k in ["completed_updates","sample_uses","unique_windows","earliest_selected_update","selected_teacher_l1","best_sha256"]} for a in summaries},refs=len(io.readmap))))
if __name__=="__main__":main()
