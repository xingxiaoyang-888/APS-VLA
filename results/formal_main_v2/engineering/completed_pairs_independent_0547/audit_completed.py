"""Independent completed-pair audit. Writes only beside this script; no GPU/Slurm/state mutation."""
import ast,copy,hashlib,importlib.util,json,math,random,sys,time,traceback
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
H=Path("/share/home/u15016/XXY_CVPR/CTI-VLA")
S=P/"snapshots/formal_main_v2_run_564be0995e"
A=R/".local/completed_pairs_independent_0547"
INV="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
INV_SHA="5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926"
evidence={}
def signature(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def require(b,m):
 if not b:raise ValueError(m)
def local(p):
 p=Path(p)
 if not p.is_absolute():p=R/p
 require(p.is_relative_to(R) or p.is_relative_to(S),"read outside control/frozen root")
 require(not any(x.is_symlink() for x in (p,*p.parents)),"symlink read")
 require(not any("sealed" in x.lower() for x in p.parts),"sealed path")
 require(p.suffix.lower() not in (".pt",".pth",".ckpt",".safetensors"),"tensor content forbidden here")
 require(p!=R/"results/experiment_supervisor/state.json","mutable state must use signed request snapshot")
 return p
def read(p,h=None):
 p=local(p);b=p.read_bytes();got=hashlib.sha256(b).hexdigest()
 require(h is None or got==h,"SHA differs "+str(p))
 require(str(p) not in evidence or evidence[str(p)]==got,"bytes changed "+str(p))
 evidence[str(p)]=got;return b
def obj(p,h=None):return json.loads(read(p,h))
def load(p,name,h=None):
 p=local(p);b=read(p,h);sp=importlib.util.spec_from_file_location(name,p)
 m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(b,str(p),"exec"),m.__dict__);return m
def save(p,v):
 require(A in p.parents,"audit output escape")
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write("\n")
def close(x,y,msg):
 require(math.isfinite(float(x)) and math.isfinite(float(y)) and math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12),msg)
def current_checkpoint(pair,arm,filename,expected):
 p=Path(pair["checkpoint_root_server"])/arm/filename
 require(p==H/f"checkpoints/formal_main_v2/{pair['suite']}/k{pair['visual_tokens']}/seed{pair['seed']}/{arm}/{filename}","checkpoint root")
 require(filename in ("best.pt","resume.pt") and not any(x.is_symlink() for x in (p,*p.parents)),"checkpoint alias")
 before=p.stat();dig=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):dig.update(b)
 after=p.stat()
 require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),"checkpoint changed during hash")
 require(dig.hexdigest()==expected and after.st_size>0,"actual checkpoint SHA differs")
 return dict(arm=arm,filename=filename,path=str(p),sha256=dig.hexdigest(),bytes=after.st_size,stable_during_hash=True,mtime_ns=after.st_mtime_ns,device=after.st_dev,inode=after.st_ino,deserialized=False)
def replay_original(pair_key,entry):
 outref=entry["machine_output"];out=obj(outref["path"],outref["sha256"]);base=(R/outref["path"]).parent
 req=obj(base/"request.json");machine=obj(base/"machine_review.json");selected=obj(base/"selected_server_hashes.json")
 require(machine["kind"]=="automatic_machine_training_review" and machine["status"]=="passed_machine_reconstruction" and machine["independent_review"] is False and machine["root_signature_claimed"] is False,"machine envelope")
 raw=machine["original_review"];jobs=req["registered_jobs"]
 require(req["pair_key"]==pair_key and req["job_id"]==raw["job_id"] and req["mode"]=="terminal","request identity")
 require(machine["raw_input_evidence"]["results/experiment_supervisor/state.json"]==req["state_sha256"],"historical registry binding")
 require(raw["completed_by_arm"]=={"A":5000,"B":5000} and raw["allowed_next_segment_end"] is None,"complete boundary")
 for ref in entry["evidence_refs"]:read(ref["path"],ref["sha256"])
 require(out["decision"]=="complete" and out["completed_by_arm"]==entry["completed_by_arm"] and out["selected_checkpoints_verified"] is True,"machine outcome")
 pulls=[p for p in machine["raw_input_evidence"] if p.startswith("results/formal_main_v2/pulls/") and p.endswith("/receipt.json")]
 require(len(pulls)==1,"exact final terminal pull")
 pull=pulls[0];read(pull,machine["raw_input_evidence"][pull])
 validator=load(machine["reviewer"]["path"],"_independent_segment_"+pair_key,machine["reviewer"]["sha256"])
 Original=validator.Evidence;captured=[]
 historical={"registered_jobs":copy.deepcopy(jobs),"pending_submission":None}
 class HistoricalEvidence(Original):
  def __init__(self,*args,**kw):super().__init__(*args,**kw);captured.append(self)
  def read(self,p):
   path=Path(p)
   if str(p)==validator.STATE or (path.is_absolute() and path==R/validator.STATE):
    return copy.deepcopy(historical)
   return super().read(p)
 validator.Evidence=HistoricalEvidence
 try:
  rebuilt=validator.review(raw["job_id"],source_inventory=INV,pull_receipt=pull,verify_server_resume=False,root=R)
 finally:validator.Evidence=Original
 require(rebuilt==raw,"original raw review does not reconstruct exactly from immutable request")
 require(len(captured)==1,"one evidence instance")
 for p,h in captured[0].hashes.items():read(p,h)
 # Modules loaded by the original validator are separately source-bound here.
 for mod in list(sys.modules.values()):
  p=getattr(mod,"__file__",None)
  if p and Path(p).suffix==".py" and Path(p).is_absolute() and Path(p).is_relative_to(R):read(p)
 return raw,req,out,selected,machine,pull

def independent_raw(pair,raw,selected):
 suite,budget,seed=pair["suite"],pair["visual_tokens"],pair["seed"]
 config=obj(pair["path"],pair["sha256"])
 require(config["training"]["updates"]==5000 and config["training"]["effective_batch"]==8 and config["future"]["horizon"]==8 and config["future"]["weight_B"]==.1,"registered fixed training")
 require(config["selection"]["updates"]==list(range(0,5001,500)) and config["selection"]["tie_break"]=="earliest_update","eleven-node selection")
 manifest=obj(config["data"]["windows"]);pool=manifest["train_window_ids"];valid=manifest["validation_window_ids"]
 lookup={x["window_id"]:x for x in manifest["windows"]}
 order=[];rng=random.Random(seed)
 while len(order)<40000:
  epoch=list(pool);rng.shuffle(epoch);order.extend(epoch[:40000-len(order)])
 require(len(order)==40000 and set(order).issubset(set(pool)),"registered complete-pool order")
 root=R/raw["output_relative"];summary=obj(root/"training_summary.json")
 require(summary["status"]=="completed" and summary["pair_complete"] is True and summary["test_opened"] is False and summary["checkpoint_unchanged"] is True,"pair finalization")
 jobs=raw["registered_pair_jobs_at_review"];ids=[j["job_id"] for j in jobs]
 require(all(j["status"]=="COMPLETED" and j["exit_code"]=="0:0" and j["gpus"]==1 for j in jobs),"retained terminal clean history")
 bill=sum(j["elapsed_seconds"]*j["gpus"] for j in jobs)
 require(bill==raw["pair_allocated_gpu_seconds"],"all historical allocation cost")
 for j in jobs:
  inv=obj(j["invocation"],j["invocation_sha256"])
  require(inv["source_sha256"]==raw["source_sha256"] and inv["stage_key"]==j["stage_key"],"historical invocation source")
  jr=obj(f"results/formal_main_v2/job_receipts/{j['job_id']}.json")
  require(jr["invocation_sha256"]==j["invocation_sha256"],"historical wrapper receipt identity")
  if "autonomous_execution" in j:
   require(j["autonomous_execution"]["target_updates_per_arm"]==5000 and j["autonomous_execution"]["scientific_source_unchanged"] is True,"continuous target/source")
   require(j["autonomous_control"]["wall_seconds"]==172800 and j["autonomous_control"]["soft_wall_seconds"]==169200,"continuous wall time")
 reports={};zero={};arms={};actual_checks=[]
 for arm in ("A","B"):
  report=obj(root/arm/"training_report.json");deploy=obj(root/arm/"deployment_receipt.json");reports[arm]=report
  require(summary["arms"][arm]==report,"pair final report differs")
  require(report["training_updates_completed"]==5000 and report["committed_samples"]==40000 and report["next_sample_cursor"]==40000 and report["vla_parameters_unchanged"] is True,"completed5000/cursor/frozen")
  require(report["initial_scorer_sha256"]==obj(root/arm/"training_order.json")["initial_scorer_sha256"],"initial scorer identity")
  require(obj(root/arm/"training_order.json")["samples"]==order and report["sample_order_sha256"]==signature(order),"independent seeded order")
  require(report["unique_committed_windows"]==len(set(order)) and report["unique_attempted_windows"]==len(set(order)),"actual set coverage")
  by_task=defaultdict(list)
  for wid in order:by_task[str(lookup[wid]["task_id"])].append(wid)
  usage={task:dict(samples=len(vals),unique_windows=len(set(vals)),unique_episodes=len({lookup[v]["episode_id"] for v in vals}),phase_sample_counts=dict(Counter(lookup[v]["phase"] for v in vals))) for task,vals in by_task.items()}
  require(report["committed_sampling_by_task"]==usage and report["attempted_completed_sampling_by_task"]==usage,"task/episode/phase usage")
  evaluated=[];val_rows={}
  for ev in report["evaluations"]:
   update=ev["update"];p=R/Path(ev["artifact_path"]).relative_to(P)
   v=obj(p,ev["artifact_sha256"]);obs=v["observations"]
   require(v["arm"]==arm and v["update"]==update and v["windows"]==len(valid) and [x["window_id"] for x in obs]==valid,"validation full ordered panel")
   tasks=defaultdict(list)
   for row in obs:
    mask=row["retained_indices"]
    require(mask==sorted(set(mask)) and len(mask)==budget and sum(x<256 for x in mask)==budget//2 and all(type(x)is int and 0<=x<512 for x in mask),"hard token packing")
    require(len(row["normalized_actions"])==8 and all(len(a)==7 and all(math.isfinite(z) for z in a) for a in row["normalized_actions"]),"action chunk")
    require(row["episode_id"]==lookup[row["window_id"]]["episode_id"] and row["task_id"]==lookup[row["window_id"]]["task_id"],"validation data identity")
    tasks[str(row["task_id"])].append(row["teacher_l1"])
   macro=sum(sum(xs)/len(xs) for xs in tasks.values())/len(tasks)
   close(macro,v["validation_metric"],"independent task macro");close(macro,ev["validation_metric"],"selection metric")
   evaluated.append((update,macro));val_rows[update]=obs
  require([x[0] for x in evaluated]==list(range(0,5001,500)),"validation update sequence")
  best=min(evaluated,key=lambda x:(x[1],x[0]))
  require(best[0]==report["best_update"]==deploy["metadata"]["update"],"earliest minimum update")
  close(best[1],report["best_validation_metric"],"best metric");close(best[1],deploy["metadata"]["validation_metric"],"metadata metric")
  require(deploy["metadata"]["per_camera_budgets"]==[budget//2]*2 and deploy["training_complete"] is True and deploy["completed_updates"]==5000,"final deployment")
  zero[arm]=val_rows[0]
  starts=[];ends=[];micro=[];valevents=[];commits=[];last=0;previous_sha=None;chains=[]
  for path in sorted((root/arm/"attempts").glob("*/cost_events.jsonl")):
   b=read(path);require(b.endswith(b"\n"),"incomplete successful journal")
   rows=[json.loads(x) for x in b.splitlines()];first=rows[0];end=rows[-1]
   require(first["event"]=="attempt_start" and first["completed_update"]==last and first["next_sample_cursor"]==last*8 and first["resumed"]==(len(chains)>0),"actual attempt continuity")
   require(first["identity"]==report["identity"] and first["job_id"] in ids,"actual identity/job")
   for event in rows:
    kind=event["event"]
    if kind=="update_start":
     u=event["update"];starts.append(u);require(event["window_ids"]==order[(u-1)*8:u*8],"update raw order")
    elif kind=="sample_end":micro.append(event["window_id"])
    elif kind=="update_end":
     u=event["update"];ends.append(u);close(event["alpha"],.1+.95*(1+math.cos(math.pi*(u-1)/4999)),"original5000 cosine")
     expected=.5*(event["teacher_l1"]+event["demonstration_l1"])
     require(math.isclose(event["action_loss"],expected,rel_tol=1e-5,abs_tol=1e-7),"fixed action loss")
     expected=event["action_loss"]+(0 if arm=="A" else .1*event["future_mse"])
     require(math.isclose(event["loss"],expected,rel_tol=1e-5,abs_tol=1e-7),"fixed A/B objective")
    elif kind=="validation_end":valevents.append(event["update"])
    elif kind=="checkpoint_commit":
     commits.append(event["completed_update"]);previous_sha=event["resume_sha256"]
   require(end["event"]=="attempt_end" and end["status"]==("completed" if end["completed_update"]==5000 else "checkpointed"),"clean terminal attempt")
   last=end["completed_update"];require(commits[-1]==last,"final full commit")
   chains.append(dict(job_id=first["job_id"],attempt_id=first["attempt_id"],start_update=first["completed_update"],end_update=last,resumed=first["resumed"],resume_sha256=previous_sha))
  require(starts==ends==list(range(1,5001)) and micro==order,"exactly5000 updates/40000 samples no replay")
  require(valevents==list(range(0,5001,500)) and set(commits)==set(range(0,5001,50)),"no omitted/repeated validation; full50 checkpoints")
  require([x["job_id"] for x in chains]==ids,"all attempts and allocations align")
  require(report["attempted_forward_backward_samples_completed"]==40000 and raw["replayed_or_uncommitted_samples"]==0,"no replay accounting")
  spec=next(x for x in raw["server_resume_checklist"] if x["arm"]==arm)
  require(spec["sha256"]==previous_sha,"latest raw commit to actual resume spec")
  actual_checks.append(current_checkpoint(pair,arm,"resume.pt",previous_sha))
  sel=next(x for x in selected["checks"] if x["arm"]==arm)
  require(sel["sha256"]==report["best_checkpoint_sha256"]==deploy["checkpoint_sha256"] and sel["path"]==report["best_checkpoint"],"selected receipt/report alignment")
  actual_checks.append(current_checkpoint(pair,arm,"best.pt",sel["sha256"]))
  arms[arm]=dict(best_update=best[0],best_task_macro_teacher_l1=best[1],best_checkpoint_sha256=sel["sha256"],updates=5000,samples=40000,unique_windows=len(set(order)),validation_windows=len(valid),validation_nodes=len(evaluated),attempt_chain=chains,initial_scorer_sha256=report["initial_scorer_sha256"],sample_order_sha256=signature(order),sampling_by_task=usage)
 require(reports["A"]["initial_scorer_sha256"]==reports["B"]["initial_scorer_sha256"] and zero["A"]==zero["B"],"matched A/B initialization and initial hard behavior")
 require(reports["A"]["identity"]["specification"]==reports["B"]["identity"]["specification"],"matched training specification")
 require(reports["A"]["future_head_parameters"]==0 and reports["B"]["future_head_parameters"]>0,"A/B head training only")
 compatibility={}
 if suite=="libero_object":
  hist=raw["runtime_compatibility_history"]
  vals=list(hist.values()) if isinstance(hist,dict) else hist
  require({x["job_id"] for x in vals}==set(ids),"all Object metadata stage history")
  require(all(x["loader_restored"] is True and x["source_inputs_unchanged"] is True and x["exact_target_suite_loads"]==1 for x in vals),"Object loader restoration")
  compatibility=dict(metadata_job_ids=ids,all_loader_restored=True,all_input_bytes_unchanged=True,original_asset_manifest_identity_retained=True)
 return dict(arms=arms,actual_checkpoint_checks=actual_checks,allocated_GPU_seconds=bill,job_ids=ids,validation_windows_per_node=len(valid),train_pool_windows=len(pool),compatibility=compatibility)
def run_pair(key,snapshot,registration):
 entry=snapshot["completed_entries"][key]
 raw,req,out,selected,machine,pull=replay_original(key,entry)
 pairs=[p for p in registration["pairs"] if f"{p['suite']}_k{p['visual_tokens']}_seed{p['seed']}"==key];require(len(pairs)==1,"registered exact pair")
 pair=pairs[0]
 ownjobs=[j for j in snapshot["registered_jobs"] if (j["suite"],j["visual_tokens"],j["training_seed"])==(pair["suite"],pair["visual_tokens"],pair["seed"])]
 require(ownjobs==raw["registered_pair_jobs_at_review"],"completed snapshot historical jobs differ")
 res=independent_raw(pair,raw,selected)
 read(Path(__file__))
 for p,h in list(evidence.items()):read(p,h)
 result=dict(schema="formal_main_v2",kind="independent_completed_training_evidence_review",status="passed",reviewed_utc=datetime.now(timezone.utc).isoformat(),pair_key=key,job_id=raw["job_id"],completed_by_arm={"A":5000,"B":5000},allowed_next_training_update=None,
  machine_output=entry["machine_output"],machine_vs_independent="Machine receipt re-executed using its immutable original request registry; independent raw sequence/task-macro/mask/loss/selected-file rechecks follow. No machine field is relabelled as independent.",
  validation_updates=list(range(0,5001,500)),original_raw_validator_rebuilt_exactly=True,full_history_and_allocation_cost_retained=True,**res,
  limits=["Optimizer/RNG tensor contents are not deserialized by this audit. Restoration assurance combines exact frozen core/F03 identity, chronological completed-update/cursor/commit journals, historical invocation identity and freshly hashed resume files.","Validation teacher/demo errors are recomputed from logged per-window errors, not a new model inference.","No GPU/model/environment run; no scientific final/test release. Full allocation billing is retained without adding nested cache timings."],
  production_state_modified=False,new_GPU_runs=0,Slurm_calls=0,checkpoint_deserialized=False,checkpoint_copied=False,sealed_state_values_read=False,
  read_evidence_sha256=dict(sorted(evidence.items())))
 path=A/(key+"_independent.json");save(path,result)
 print(json.dumps(dict(pair=key,status="passed",path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),GPU_seconds=res["allocated_GPU_seconds"],best={a:res["arms"][a]["best_update"] for a in ("A","B")},refs=len(evidence))),flush=True)
 return result
def main():
 snapshot=obj(A/"requested_pairs_snapshot_v2.json","1cdcc808693bc724f3210747611d94aa937fe27f70076c3abde1fe8108608c5a")
 for rel in ("SERVER_WORKSPACE.md","docs/服务器工作区与GitHub同步.md","scripts/ops/formal_autonomous_training_v1/README.md","scripts/ops/formal_autonomous_training_v1/worker.py","scripts/ops/formal_autonomous_training_v1/execution.py","scripts/ops/formal_autonomous_training_v1/controller.py","scripts/ops/formal_autonomous_training_v1/backend.py"):read(rel)
 inventory=obj(INV,INV_SHA);require(len(inventory["files"])==173,"173 frozen files")
 for p,h in inventory["files"].items():read(R/p,h);read(S/p,h)
 registration=obj("configs/experiments/formal_main_v2.json");common=dict(evidence)
 targets=sys.argv[1:] or list(snapshot["completed_entries"])
 for key in targets:
  evidence.clear();evidence.update(common);run_pair(key,snapshot,registration)
if __name__=="__main__":main()
