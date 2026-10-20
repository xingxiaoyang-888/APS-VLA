"""Exact Spatial64 seed23 terminal continuous recovery independent raw audit.
No review() call that reads pending or publishes production. No tensor load,
scheduler call, state/Git mutation or final-state access. Root proof is bound only
after raw reconstruction, and lack of root proof never yields final passed.
"""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import argparse,ast,hashlib,importlib.util,json,math,random,sys,os,time,traceback
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/Spatial64seed23_terminal_1032"
helper=R/"results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258.py"
assert hashlib.sha256(helper.read_bytes()).hexdigest()=="fd566045bc20e76a10dc05b7ed56377d9817231bb5538eb828c087eb7dd5ef1a"
sp=importlib.util.spec_from_file_location("independent_io_2130",helper)
io=importlib.util.module_from_spec(sp);sp.loader.exec_module(io)
need,read,raw,jrows,close,sig,shafile=io.need,io.read,io.raw,io.jrows,io.close,io.sig,io.shafile
P,H,S=io.P,io.H,io.S
REL="results/formal_main_v2/libero_spatial/k64/seed23/training"
JOBS=["3024716","3025205","3043399","3044479"];ALLJOBS=["3024716","3025205","3028522","3043399","3044479"]
ENDS=[500,1000,1500,5000];STARTS=[0,500,1000,1500];COSTS=[3281,5203,73,3401,30522]
AUTH="configs/experiments/formal_main_v2_cuda_single_recovery_3028522_v1.json"
AUTHSHA="7411a2e5e0d7e2123eea8bfea4c2bbaccb037d54b09697180340a597e3cfb18a"
REVIEWER="scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py"
FAILURE="scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py"

def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No child/network/scheduler allowed')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   need(not any('sealed' in x.lower() or x.lower()=='test' for x in p.parts),'sealed/test forbidden')
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)))
   if writing:need(D in p.parents,'private writes only')
sys.dont_write_bytecode=True;sys.addaudithook(guard)
def refread(ref):return read(ref['path'],ref['sha256'])
def main(args):
 t0=time.perf_counter();cpu0=time.process_time()
 bindings=read('.local/Spatial64seed23_terminal_1032/bindings.json',args.bindings_sha256)
 root=refread(bindings['root']);selected=refread(bindings['selected']);refread(bindings['root_terminal'])
 need(root['kind']=='root_segment_review' and root['status']=='passed' and root['job_id']=='3044479','exact root identity')
 need(root['completed_by_arm']=={'A':5000,'B':5000} and root['resume_required'] is False and root['allowed_next_segment_end'] is None,'root complete endpoint only')
 need(selected['status']=='verified_actual_server_bytes' and selected['job_id']=='3044479' and selected['root_review']==bindings['root'] and selected['weights_copied'] is False and selected['optimizer_rng_deserialized'] is False,'root selected byte proof')
 PULL=bindings['pull']['path'];PULLSHA=bindings['pull']['sha256']
 raw(helper.relative_to(R).as_posix())
 raw("SERVER_WORKSPACE.md","fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62")
 raw("docs/服务器工作区与GitHub同步.md","d7f0455ef4febb536df199653fd323a1cef98ad66732e5b2ea8edfdf06b75343")
 raw(REVIEWER,"ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4")
 raw(FAILURE,"c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480")
 reviewer=io.load(REVIEWER)
 jobs={j["job_id"]:j for j in root["registered_pair_jobs_at_review"]}
 need(list(sorted(jobs))==list(sorted(ALLJOBS)) and len(root["registered_pair_jobs_at_review"])==5,"all five allocations retained")
 for jid,cost in zip(ALLJOBS,COSTS):
  j=jobs[jid];expected=("FAILED","1:0") if jid=="3028522" else ("COMPLETED","0:0")
  need((j["status"],j["exit_code"])==expected and j["elapsed_seconds"]==cost and j["gpus"]==1,"all actual bill")
  need(j["suite"]=="libero_spatial" and j["visual_tokens"]==64 and j["training_seed"]==23 and j["run_root"]==str(P/REL),"exact own pair")
 need(sum(COSTS)==root["pair_allocated_gpu_seconds"]==42480,"complete cost including retained failed73")
 job=jobs["3043399"];oldj=jobs["3028522"]
 auth=read(AUTH,AUTHSHA)
 need(auth["status"]=="approved_for_exactly_one_original_target_recovery" and auth["kind"]=="cuda_startup_single_recovery_authorization" and auth["original_target"]==1500 and auth["resume"] is True and auth["maximum_new_attempts"]==1 and auth["automatic_retry"] is False and auth["continuous5000_admission_authorized"] is False,"bounded original-target authorization")
 need(job["startup_recovery"]["authorization"]=={"path":AUTH,"sha256":AUTHSHA} and job["startup_recovery"]["failed_job_id"]=="3028522","actual authorization")
 for rel,h in {**auth["original_recovery_files"],**auth["gateway_files"]}.items():raw(rel,h)
 for k in ["canonical_failure_review","canonical_publication","independent_review","root_reservation","repair_record","node_exclusion","controller_activation"]:
  r=auth[k];raw(r["path"],r["sha256"])
 original=read(oldj["invocation"],oldj["invocation_sha256"]);current=read(job["invocation"],job["invocation_sha256"])
 need({k for k in set(original)|set(current) if original.get(k)!=current.get(k)}=={"registered_utc","repair_record"},"only registered repair metadata changes")
 need(current["argv"]==original["argv"] and current["argv"][-1]=="--resume" and current["segment_end"]==1500,"same real resume argv")
 need(current["argv"][current["argv"].index("--stop-after-updates")+1]=="1500" and current["argv"][current["argv"].index("--max-wall-seconds")+1]=="12600","original target and wall")
 need(current["repair_record"]==str(R/auth["repair_record"]["path"]),"actual repair identity")
 need(all("runtime_compatibility" not in x and "component_compatibility" not in x for x in [current,original,job,oldj]),"Spatial stays original runtime")
 for x in ["--no-requeue","--time=04:00:00","--exclude=gpu4020","--comment=cti-cuda-recovery-v1:"+AUTHSHA]:need(x in job["startup_recovery"]["actual_sbatch_argv"],"actual schedule option "+x)
 inventory=read("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
 need(len(inventory["files"])==173 and current["source_sha256"]==inventory["source_sha256"],"source173")
 for rel,h in inventory["files"].items():
  raw(rel,h);need(shafile(S/rel)["sha256"]==h,"actual S source");raw("snapshots/formal_main_v2_run_564be0995e/"+rel,h)
 me=reviewer.Evidence(R);failure=reviewer._startup.require_saved(me,job=oldj)
 need(failure["completed_by_arm"]=={"A":1000,"B":1000} and failure["next_sample_cursor"]=={"A":8000,"B":8000} and failure["current_allocation_new_updates"]==0 and failure["current_allocation_arm_initializations"]==0,"failure did not modify initialized training")
 prior_checks=[]
 for jid,pin in [("3024716","5ce4684febf5fb0827b134b52cde859f7e8e7de56297b7855e2eb55434d8eded"),("3025205","2416c7802db8ab947971ddaaedbb771c8ab9c2edacc8fd52e2f778ba66802876")]:
  p=read(REL+"/segment_reviews/"+jid+".json",pin)
  need(p["status"]=="passed" and p["job_id"]==jid and p["completed_by_arm"]=={a:jobs[jid]["segment_end"] for a in "AB"},"prior actual root boundary")
  prior_checks.append(p["server_resume_checks"])
 need(failure["server_resume_checks"]==prior_checks[-1],"failure preserved exact1000 checkpoints")
 newjob=jobs['3044479'];newinv=read(newjob['invocation'],newjob['invocation_sha256']);cad=newinv['continuous_admission'];ca=refread(cad['authorization'])
 need(cad['authorization']==dict(path='configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json',sha256='1cdb14995f275d03557d86be1b565f615a005d911b994ce8c17a3d229e989411'),'exact continuous authorization')
 need(ca['status']=='approved_exact_once_1500_to5000' and ca['kind']=='root_cuda_recovered_continuous_admission_authorization','real bounded continuous admission')
 for ob in [ca,cad]:
  need(ob['scientific_settings_changed'] is False and ob['single_new_attempt'] is True and ob['automatic_retry'] is False and ob['controller_admission_changed'] is False,'admission scope')
  need(ob['completed_before']=={'A':1500,'B':1500} and ob['historical_GPU_seconds']==11958 and ob['target_updates_per_arm']==5000 and ob['soft_wall_seconds']==169200 and ob['allocation_time']=='48:00:00','exact start/target/cost')
 need(cad['sample_cursor_before']=={'A':12000,'B':12000} and cad['prior_job_ids']==ALLJOBS[:-1] and cad['checkpoint_every_updates']==50 and cad['validation_updates']==list(range(0,5001,500)),'continuous cursor and cadence')
 for key in ['canonical_failure_review','root_recovery_review','independent_recovery_review','terminal_pull','controller_activation','normal_execution_authorization','node_exclusion','historical_document_binding','author_review','independent_review']:
  refread(ca[key])
 for rel,h in {**ca['gateway_files'],**ca['reviewer_publication']}.items():raw(rel,h)
 prior=refread(cad['root_recovery_review']);pind=refread(cad['independent_recovery_review'])
 need(prior['job_id']==pind['job_id']=='3043399' and prior['status']=='passed' and prior['completed_by_arm']=={'A':1500,'B':1500} and pind['status']=='passed_original_target_recovery_only' and pind['root_review']==cad['root_recovery_review'],'real prior dual1500')
 need(prior['server_resume_checks']==pind['actual_server_resume_checks']==cad['resume_checks_before'],'original1500 exact checkpoints')
 prior_checks.append(prior['server_resume_checks'])
 need({k:v for k,v in newjob['continuous_admission'].items() if k not in ['actual_sbatch_argv','request_token']}==cad,'registered/executed continuous contract')
 base=json.loads(json.dumps(newinv));base.pop('continuous_admission');base['segment_end']=1500;base['registered_utc']=current['registered_utc']
 for flag,value in [('--stop-after-updates','1500'),('--max-wall-seconds','12600')]:
  need(base['argv'].count(flag)==1,'unique option');base['argv'][base['argv'].index(flag)+1]=value
 need(base==current and newinv['argv'].count('--resume')==1,'only approved target/wall/registration changed')
 need(all(k not in newinv for k in ['runtime_compatibility','component_compatibility','autonomous_execution']),'Spatial original frozen wrapper')
 sb=newjob['continuous_admission']['actual_sbatch_argv'];need(sb==newjob['startup_recovery']['actual_sbatch_argv'],'exact Slurm metadata')
 for v in ['--no-requeue','--time=48:00:00','--exclude=gpu4020','--chdir='+str(P),'--comment='+newjob['continuous_admission']['request_token']]:need(v in sb,'submitted option')
 need(sb[-1]==str(S/'scripts/server/formal_main.slurm'),'original frozen Slurm entry')
 configrel="configs/experiments/formal_main_v2/libero_spatial_k64_seed23.json"
 config=read(configrel,inventory["files"][configrel]);need(read(REL+"/registered_config.json")==config,"run config")
 need(config["seed"]==23 and config["tokens_per_camera"]==32 and config["training"]["updates"]==5000 and config["training"]["effective_batch"]==8 and config["selection"]["updates"]==list(range(0,5001,500)),"original scientific schedule")
 gate=read("results/formal_main_v2/libero_spatial/acceptance/root_review.json")
 need(gate["status"]=="passed" and gate["source_sha256"]==inventory["source_sha256"],"own F00/F01/F03")
 for name,h in gate["files"].items():raw(gate["output_relative"]+"/"+name,h)
 for rel,h in gate["source_files"].items():raw(rel,h)
 f00=read(gate["output_relative"]+"/input_acceptance.json")
 protocol=read(config["data"]["protocol"]);manifest=read(config["data"]["windows"])
 sys.path.insert(0,str(R/"src"))
 from cti_vla.data.formal_windows import load_formal_protocol,load_formal_windows
 checked=load_formal_protocol(R/config["data"]["protocol"],project_root=R)
 need(load_formal_windows(R/config["data"]["windows"],checked)==manifest,"original full legal pools")
 train=manifest["train_window_ids"];val=manifest["validation_window_ids"];lookup={r["window_id"]:r for r in manifest["windows"]}
 need(len(train)==len(set(train))==34703 and len(val)==len(set(val))==189,"complete Spatial pools")
 need(not set(train)&set(val) and not {lookup[x]["episode_id"] for x in train}&{lookup[x]["episode_id"] for x in val},"episode isolation")
 rng=random.Random(23);order=[]
 while len(order)<40000:
  epoch=list(train);rng.shuffle(epoch);order.extend(epoch)
 order=order[:40000]
 trainer=raw("src/cti_vla/training/formal_future.py").decode()
 constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(trainer).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith("FORMAL_")}
 need('optimizer.load_state_dict(saved["optimizer"])' in trainer and 'restore_rng(saved["rng"])' in trainer,"unchanged optimizer/RNG restore code")
 registration=read("configs/experiments/formal_main_v2.json")
 pair=next(x for x in registration["pairs"] if (x["suite"],x["visual_tokens"],x["seed"])==("libero_spatial",64,23))
 reports={};summaries={};initial={};actualchecks=[]
 for arm in ["A","B"]:
  base=REL+"/"+arm;report=read(base+"/training_report.json");reports[arm]=report
  for key,value in {"schema":"formal_main_v2","arm":arm,"status":"completed","training_updates_completed":5000,"committed_samples":40000,"next_sample_cursor":40000,"unique_committed_windows":len(set(order)),"attempted_forward_backward_samples_completed":40000,"train_pool_windows":34703,"validation_pool_windows":189,"vla_parameters_unchanged":True,"job_ids":JOBS}.items():
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
  need(sampling==report["committed_sampling_by_task"],"actual unique sampling")
  paths=sorted((R/base/"attempts").glob("*/cost_events.jsonl"));need(len(paths)==4,"four successful attempts")
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
     need(active is None and validating is None and r["update"]==cur and cur in range(0,5001,500) and cur not in vals and r["windows"]==189,"exact node once");validating=cur
    elif e=="validation_end":
     need(validating==r["update"] and r["window_forwards"]==189,"full validation")
     vr=base+"/attempts/"+attempt+"/validation_"+str(validating).zfill(5)+".json";v=read(vr,r["artifact_sha256"])
     need(v["arm"]==arm and v["update"]==validating and v["job_id"]==jid and v["attempt_id"]==attempt and v["windows"]==189 and v["tasks"]==10 and v["metric"]=="task_macro_hard_validation_teacher_l1","validation identity")
     need([x["window_id"] for x in v["observations"]]==val,"full ordered189")
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
     close(v["window_weighted_teacher_l1_diagnostic"],sum(x["teacher_l1"] for x in v["observations"])/189)
     vals[validating]={"update":validating,"teacher_l1":metric,"expert_l1":expert,"path":vr,"sha256":io.readmap[vr]}
     if validating==0:initial[arm]=[{k:x[k] for k in ["window_id","episode_id","task_id","teacher_l1","demonstration_l1","retained_indices","normalized_actions"]} for x in v["observations"]]
     validating=None;v_count+=1
    elif e=="checkpoint_commit":
     need(active is None and validating is None and r["completed_update"]==cur,"atomic committed update")
     commits.append(r);allcommits.append(r)
    elif e=="attempt_end":
     need(active is None and validating is None and cur==end and r["completed_update"]==end and r["status"]==("checkpointed" if index<3 else "completed"),"clean committed attempt")
     need(commits[-1]["completed_update"]==end,"last checkpoint");ended=True
    else:raise ValueError("unknown event "+e)
   need(ended and u_count==[500,500,500,3500][index] and v_count==[2,1,1,7][index],"full attempt work")
   byattempt.append({"job_id":jid,"attempt_id":attempt,"start_update":STARTS[index],"end_update":end,"updates":u_count,"validation_nodes":v_count,"journal_rows":len(rows),"last_resume_sha256":commits[-1]["resume_sha256"]})
  need(cur==5000 and sampleids==order and len(sampleids)==40000 and len(set(sampleids))==len(set(order)),"no missing/replayed samples")
  need(set(x["completed_update"] for x in allcommits)==set(range(0,5001,50)) and len(grad)==5000 and max(grad)>0,"all checkpoint/gradient evidence")
  need(sorted(vals)==list(range(0,5001,500)) and [v["update"] for v in report["evaluations"]]==sorted(vals),"11 selection nodes")
  for v in report["evaluations"]:
   obs=vals[v["update"]];need(v["artifact_sha256"]==obs["sha256"] and v["artifact_path"]==str(P/obs["path"]),"raw selection binding");close(v["validation_metric"],obs["teacher_l1"])
  best=min(vals.values(),key=lambda v:(v["teacher_l1"],v["update"]))
  need(report['best_update']==best['update'],'earliest equal-task minimum checkpoint');close(report['best_validation_metric'],best['teacher_l1'])
  dep=read(base+'/deployment_receipt.json')
  need(dep['training_complete'] is True and dep['base_frozen'] is True and dep['checkpoint_unchanged'] is True and dep['completed_updates']==dep['planned_updates']==5000,'complete real deployment receipt')
  need(dep['checkpoint_sha256']==report['best_checkpoint_sha256'] and dep['metadata_sha256']==sig(dep['metadata']),'selected checkpoint and metadata hash')
  md=dep['metadata'];need(md['arm']==arm and md['suite']=='libero_spatial' and md['seed']==23 and md['visual_tokens']==64 and md['per_camera_budgets']==[32,32] and md['update']==best['update'],'deployment identity')
  close(md['validation_metric'],best['teacher_l1'])
  need(dep['evaluations']==report['evaluations'] and dep['pair_config']==config and dep['training_config']=={**config,'arm':arm},'unchanged config/selection')
  resume=shafile(H/'checkpoints/formal_main_v2/libero_spatial/k64/seed23'/arm/'resume.pt');resume['arm']=arm
  need(resume['sha256']==allcommits[-1]['resume_sha256'],'actual terminal committed resume')
  checkpoint=shafile(H/'checkpoints/formal_main_v2/libero_spatial/k64/seed23'/arm/'best.pt');proof=next(x for x in selected['checks'] if x['arm']==arm)
  need(checkpoint['path']==report['best_checkpoint']==proof['path'] and checkpoint['sha256']==dep['checkpoint_sha256']==proof['sha256'] and checkpoint['bytes']==proof['bytes'],'actual selected bytes not only reported hash')
  candidates=[]
  for ev in report['evaluations']:
   artifact=Path(vals[ev['update']]['path']);attempt=artifact.parent.name
   expected=H/'checkpoints/formal_main_v2/libero_spatial/k64/seed23'/arm/'candidates'/(attempt+'_update'+str(ev['update']).zfill(5)+'.pt')
   need(ev['candidate_path']==str(expected),'registered candidate exact path');fact=shafile(expected);need(fact['sha256']==ev['candidate_sha256'],'candidate bytes unchanged')
   candidates.append(dict(update=ev['update'],**fact))
  need('payload["training_complete"] = True' in trainer and 'atomic_torch_save(best_path, payload)' in trainer,'original final candidate metadata completion path')
  rebuilt,required_arm=reviewer.audit_arm(me,arm=arm,relative=REL,pair=pair,config=config,manifest=manifest,identity=ident,constants=constants,jobs=jobs,target=5000)
  need(rebuilt['status']=='completed' and rebuilt['completed']==5000 and rebuilt['samples']==40000 and rebuilt['replayed_or_uncommitted_samples']==0 and rebuilt['resume_sha256']==resume['sha256'],'unchanged original pure arm validator agrees')
  actualchecks.append(resume)
  summaries[arm]=dict(completed_updates=5000,sample_uses=40000,unique_windows=len(set(sampleids)),cursor=40000,latest_start_update=1500,latest_new_updates=3500,attempts=byattempt,validation=[vals[u] for u in sorted(vals)],selected_update=best['update'],selected_teacher_l1=best['teacher_l1'],selected_expert_l1=best['expert_l1'],candidate_byte_checks=candidates,resume=resume,best=checkpoint,gradient_range=[min(grad),max(grad)],original_arm_primitive=rebuilt,replayed_or_uncommitted_samples=0)
 need(initial['A']==initial['B'] and reports['A']['initial_scorer_sha256']==reports['B']['initial_scorer_sha256'],'matched AB initial behavior and scorer')
 summary=read(REL+'/training_summary.json')
 need(summary['arms']==reports and summary['status']=='completed' and summary['pair_complete'] is True and summary['job_id']=='3044479' and summary['test_opened'] is False and summary['checkpoint_unchanged'] is True,'actual pair completion')
 finals=list((R/REL/'finalizations').glob('3044479_*.json'));need(len(finals)==1,'one current finalization');final=read(finals[0].relative_to(R).as_posix())
 need(final['status']=='verified' and final['kind']=='training' and final['result_sha256']==io.readmap[REL+'/training_summary.json'] and final['checkpoint_unchanged'] is True and final['source_files']==gate['source_files']==summary['source_files'],'full training original source/base finalization')
 suite=registration['suites']['libero_spatial'];model=read(suite['model_manifest'],inventory['files'][suite['model_manifest']])
 need(model['repository']=='moojink/openvla-7b-oft-finetuned-libero-spatial' and model['revision']==config['model_revision'],'official Spatial base')
 components=[]
 for row in model['files']:
  if row['path'].startswith(('action_head--','proprio_projector--')):
   fact=shafile(Path(suite['model_root_server'])/row['path']);need(fact['sha256']==row['sha256'] and fact['bytes']==row['size'],'actual official component bytes');components.append(fact)
 need(len(components)==2,'official action/proprio components')
 counts=Counter();cachepaths=list((R/REL/'cache_events').glob('*.jsonl'));need(len(cachepaths)==4,'four successful cache ledgers, no failed startup cache generation')
 cache_id=reports['A']['identity']['cache_identity'];need(cache_id==reports['B']['identity']['cache_identity'],'matched cache identity')
 tree=ast.parse(raw('src/cti_vla/training/formal_records.py').decode());cversion=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='FORMAL_CACHE_VERSION');namespace=sig({'cache_version':cversion,**cache_id})
 for p in cachepaths:
  for row in jrows(p.relative_to(R).as_posix()):need(row['job_id'] in JOBS and row['cache_identity_sha256']==namespace,'cache owner/identity');counts[row['event']]+=1
 pull=read(PULL,PULLSHA)
 need(pull['status']=='verified_nonweight_snapshot' and pull['final_evidence'] is True and pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False and not pull['missing'] and not pull['skipped'],'complete stable nonweight pull')
 need(set(ALLJOBS)<={j['job_id'] for j in pull['selected_jobs']},'all pair allocations in pull')
 before=read(str(Path(PULL).parent/'inventory_before.json'),pull['inventory_sha256']);after=read(str(Path(PULL).parent/'inventory_after.json'));need(before==after,'stable dual inventory')
 inventory_rows={r['relative']:r for r in before['files']};need(len(inventory_rows)==len(before['files'])==len(pull['files']),'unique complete files')
 for when in ['accounting_before','accounting_after']:
  for jid,j in jobs.items():
   bill=pull[when]['jobs'][jid];need(all(bill[k]==j[k] for k in ['status','exit_code','elapsed_seconds']),'all actual allocation bills');need(dict(x.split('=',1) for x in bill['allocation'].split(',') if '=' in x).get('gres/gpu')=='1','oneGPU actual allocation')
 scoped=[r for r in pull['files'] if set(r['job_ids'])&set(ALLJOBS)]
 for row in scoped:
  rel=row['relative'];data=raw(rel,row['sha256']);old=inventory_rows[rel];need(len(data)==row['bytes'] and all(row[k]==old[k] for k in ['path','sha256','bytes','job_ids']),'same complete pulled bytes')
  need(row['path']==str(P/rel) and row['action'] in ['same_sha_skipped','downloaded_verified'],'original P origin');need(shafile(P/rel)['sha256']==row['sha256'],'actual terminal P unchanged')
  if rel.startswith(REL+'/'):need('3044479' in row['job_ids'],'shared run-root current owner')
  if rel in failure['retained_failure_files']:need(row['sha256']==failure['evidence_bundle'][rel]['sha256'],'retained failed original bytes')
 for jid in ALLJOBS:
  for rel in ['results/formal_main_v2/job_receipts/'+jid+'.json',*['results/slurm/cti-formal_'+jid+'.'+ext for ext in ['out','err']]]:
   row=next(r for r in scoped if r['relative']==rel);need(row['job_ids']==[jid],'exact historical external owner')
  rec=read('results/formal_main_v2/job_receipts/'+jid+'.json')
  need(rec['job_id']==jid and rec['invocation_sha256']==jobs[jid]['invocation_sha256'] and rec['source_sha256']==inventory['source_sha256'] and rec['exit_code']==(1 if jid=='3028522' else 0) and 0<rec['wall_seconds']<=jobs[jid]['elapsed_seconds'],'actual original wrapper return and failed cost')
 need(root['suite']=='libero_spatial' and root['visual_tokens']==64 and root['seed']==23,'exact root pair')
 need(root['completed_training_receipts']==[REL+'/'+a+'/deployment_receipt.json' for a in 'AB'],'root complete receipts only')
 need(root['server_resume_checks']==actualchecks and root['cache_event_counts']==dict(counts) and root['startup_failure_history']=={'3028522':failure},'independently rebuilt facts agree')
 for rel,h in root['files'].items():raw(rel,h)
 for rel,h in root.get('evidence_sha256',{}).items():
  if rel!='results/experiment_supervisor/state.json':raw(rel,h)
 archive=None
 if 'archive_snapshot' in bindings:
  raw('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2');codec=io.load('scripts/ops/nonweight_archive.py');aref=bindings['archive_snapshot'];ar,evidence,objects,chunks=codec.verified_plan(R,aref['path'],aref['sha256']);inputs=refread(bindings['archive_inputs'])
  need([{k:x[k] for k in ['path','sha256','bytes']} for x in ar['files']]==inputs['raw'],'exact archive input map')
  for rr,role in evidence.values():need(len(raw(rr['path'],rr['sha256']))==rr['bytes'],'archive evidence')
  class Sink:
   def __init__(self,f):self.f=f;self.n=0;self.h=hashlib.sha256()
   def write(self,b):need(self.f.read(len(b))==b,'decoded archive bytes differ');self.n+=len(b);self.h.update(b);return len(b)
  recovered=[]
  for row in ar['files']:
   need(row['path'].startswith(REL+'/') and json.loads(raw(row['path']).splitlines()[0])['job_id']=='3044479','current registered raw journal archive')
   with (R/row['path']).open('rb') as f:
    sink=Sink(f);codec.verify_object(R,row['manifest'],row['sha256'],row['bytes'],sink=sink);need(not f.read(1) and sink.n==row['bytes'] and sink.h.hexdigest()==row['sha256'],'lossless whole raw journal')
   recovered.append({k:row[k] for k in ['path','bytes','sha256']})
  need(len(recovered)==3,'three current raw journals');archive=dict(snapshot=aref,inputs=bindings['archive_inputs'],files=recovered,status='all_new_raw_logs_losslessly_rebuilt_in_memory',historical_raw_delivery='Original prior dual-review/archive references retained; this terminal audit re-reads all historical raw bytes from the exact stable pull.',filesystem_restore_performed=False)
 me.unchanged()
 for rel,h in me.hashes.items():raw(rel,h)
 raw(Path(__file__).relative_to(R).as_posix())
 for rel,h in io.readmap.items():need(hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,'input drift '+rel)
 out=dict(schema='formal_main_v2',kind='independent_completed_training_review',status='passed_complete_training_only',job_id='3044479',suite='libero_spatial',visual_tokens=64,seed=23,completed_by_arm={'A':5000,'B':5000},allowed_next_segment_end=None,resume_required=False,root_review=bindings['root'],selected_server_review=bindings['selected'],pull=bindings['pull'],arms=summaries,actual_server_resume_checks=actualchecks,official_Spatial_components=components,source173_R_S_mirror_match=True,same_AB_initialization_and_full40000_order=True,historical_failure_preserved_and_rebuilt=True,historical_dual_review_receipts=dict(root=cad['root_recovery_review'],independent=cad['independent_recovery_review']),continuous_admission=cad['authorization'],prior_completed_by_arm={'A':1500,'B':1500},new_reviewed_arm_updates=7000,scientific_matrix_completed_arms_added=2,cost=dict(historical_success_GPU_seconds=8484,retained_FAILED_GPU_seconds=73,successful_original1500_recovery_GPU_seconds=3401,historical_allocation_GPU_seconds=11958,continuous_allocation_GPU_seconds=30522,all_pair_allocated_GPU_seconds=42480,allocations=[dict(job_id=j,GPU_seconds=c) for j,c in zip(ALLJOBS,COSTS)],nested_phases_added=False),cache_event_counts=dict(counts),archive_reconstruction=archive,read_evidence_sha256=dict(sorted(io.readmap.items())),server_read_evidence_sha256=dict(sorted(io.servermap.items())),weights_copied_or_deserialized=False,state_or_Git_writes=False,Slurm_mutated=False,final_release_authorized=False,scientific_closed_loop_claimed=False,CPU_wall_seconds=time.perf_counter()-t0,CPU_process_seconds=time.process_time()-cpu0,limitations=['Optimizer/RNG restore is evidenced by frozen load_state_dict/restore_rng source, complete real resumed events, exact sample cursor/order and checkpoint byte continuity; no checkpoint tensor was independently deserialized.','Failed73GPU seconds and historical successful allocations remain counted once; new independent work verifies7000 arm updates from1500.','Training terminal acceptance does not authorize global freeze, final evaluation, external selectors or any automatic extension.'],reviewed_utc=datetime.now(timezone.utc).isoformat())
 dest=D/'independent_review.json'
 with dest.open('x') as f:json.dump(out,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),status=out['status'],cost=out['cost'],arms={a:{k:summaries[a][k] for k in ['completed_updates','sample_uses','unique_windows','selected_update','selected_teacher_l1']} for a in 'AB'},archive_verified=archive is not None,source_refs=len(io.readmap))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--bindings-sha256',required=True);args=p.parse_args();a=time.perf_counter();b=time.process_time()
 try:main(args)
 except BaseException as e:
  with (D/'audit_a1_failure.json').open('x') as f:json.dump(dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),CPU_wall_seconds=time.perf_counter()-a,CPU_process_seconds=time.process_time()-b,GPU_calls=0,production_changed=False),f,indent=2)
  raise
