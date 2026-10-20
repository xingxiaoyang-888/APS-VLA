"""Independent read-only admission of exact Long legacy600 typed equivalence.
Source-derived historical identity is explicit; no retrospective instance claim,
GPU/simulator/model execution, state/Git changes or production admission.
"""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, math, os, random, sys, time, traceback, zipfile
from collections import Counter
from datetime import datetime, timezone
import numpy as np
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
H=R.parent;S=P/"snapshots/formal_main_v2_run_564be0995e";SP=H/"venv/lib/python3.11/site-packages"
D=R/".local/Long_legacy6_admission_independent_1032"
B="results/formal_main_v2/engineering/supervision_delivery_0927/Long_legacy6_typed_bridge"
PRIOR="results/formal_main_v2/engineering/supervision_delivery_0727/Long_legacy6_CPU_candidate"
HIST="results/formal_main_v2/engineering/supervision_delivery_0830/Long_legacy6_provenance_independent/independent_readiness.json"
RUN="results/formal_main_v2/libero_10/downstream/development/8c843c1d4ee8383c/attempt01"
ROOT="results/formal_main_v2/downstream_reviews/3019954.json"
MAN="results/formal_main_v2/execution/libero_10_development_first_pair_v1.json"
REG="configs/experiments/formal_main_v2_action_execution_compat_v1.json"
INV="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
TARGET="results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed23/execution_contract.json"
ADAPT="results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py"
V4="results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl"
OLD="formal-downstream-root-v1";NEW="formal-downstream-action-v1"
SEM="4ef98a5beb21bfa790a8a0f484334d6d9020a481a517d8f89534562524025d7d"
METHODS=["dense","uniform256","uniform128","uniform64","A128_seed17","B128_seed17"]
JOBS=["3016981","3017161","3017959","3018505","3019176","3019954"]
PINS={B+"/report.json":"123d73d7a4e5622fd3048efc69058ce19b3d480c28f1ef33a874302b08ead508",
B+"/equivalence_map_candidate.json":"f3c7c2e3b3d4546748c4705bb8cba7f29c050470a22645215f7a894f899d3cc0",
B+"/manifest.json":"fb84c6cfc2f69832bb0d8ce6e0fae87e23e19645fd4a262dd9fa418fa9b9f011",
B+"/per_trial_equivalence_candidates.jsonl":"1b2124cb9abaae350f5cd6b9f921721256f7f38cfa56a05240f1f694ca396c4e",
B+"/build_map_v1.py":"f0958f6bbdbb1b9f45894c38cf57de1b4b8753b1f06dc2da23b43ce0e21e7c20",
REG:"0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe",
INV:"5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926",
ROOT:"cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba",
MAN:"d8c22787050b3223390627d74a804505c62f470b064bab112c2c230c4369051a",
HIST:"b786128f4f202c93da6a80f44c7c1fbeeacadef78724b76d9bef294615b7a3d5",
TARGET:"ecab6b824d17f52e26b788e47a021d767c79b8606a6ab342388962e1de0d9db6",
PRIOR+"/report.json":"22a47a847ed81d7a18360354dd6a53b8e1153c716df78a87264bcbca25c49f18",
PRIOR+"/per_trial.jsonl":"2ea56052bf56432858cfb0930707e158054da84c6a68d822b369b4b0cb4e1fbc",
PRIOR+"/per_chunk.jsonl":"ccd1d56775752ac9c8d0d1381b2caf932c7327bfd4670bcca1cdc90b14a6dbc0",
ADAPT:"b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185",
V4:"54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c",
"scripts/formal_execution_manifests.py":"614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89",
"scripts/ops/formal_action_deployment_v1/consumer.py":"16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034",
"scripts/ops/formal_action_deployment_v1/reviewer.py":"9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd"}
checks=Counter();watched={};began=time.perf_counter()
def need(ok,msg,group="general"):
    if not ok:raise ValueError(msg)
    checks[group]+=1
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()
def sig(v):return digest(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode())
def unique(items):
    d={}
    for k,v in items:
        if k in d:raise ValueError("duplicate JSON key")
        d[k]=v
    return d
def decode(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def watch(rel,expected=None):
    p=Path(rel);p=p if p.is_absolute() else R/p
    need(p.resolve()==p and not p.is_symlink(),"noncanonical evidence "+str(p),"paths")
    h=sha(p);key=p.relative_to(R).as_posix() if R in p.parents else str(p)
    need(expected is None or h==expected,"SHA mismatch "+key,"pins")
    need(key not in watched or watched[key]["sha256"]==h,"evidence changed "+key,"pins")
    watched[key]={"sha256":h,"bytes":p.stat().st_size}
    return {"path":key,"sha256":h}
def read(rel,expected=None):
    watch(rel,expected);p=Path(rel);return decode((p if p.is_absolute() else R/p).read_bytes())
def save(name,value,jsonl=False):
    p=D/name
    with p.open("x",encoding="utf-8") as f:
        if jsonl:
            for row in value:f.write(json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n")
        else:f.write(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    return {"path":p.relative_to(R).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size}
def load(name,rel):
    p=Path(rel);p=p if p.is_absolute() else R/p
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),"exec",dont_inherit=True),m.__dict__);return m
def bytes7(value):
    a=np.asarray(value,dtype="<f8")
    need(a.ndim==2 and a.shape[1]==7 and np.isfinite(a).all(),"finite seven-column actions","actions")
    return a.tobytes(order="C")
def rng():
    n=np.random.get_state()
    return sig({"python":random.getstate(),"numpy":[n[0],n[1].tolist(),n[2],n[3],n[4]]})
def guard(event,args):
    if event in ("subprocess.Popen","os.system","os.posix_spawn","socket.connect","socket.bind"):
        raise RuntimeError("No subprocess/network/scheduler")
    if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).absolute()
        if set(p.suffixes)&{".pt",".pth",".bin",".ckpt",".safetensors",".pkl",".pickle",".init",".pruned_init"} or any(x.lower() in ("weights","checkpoints","sealed") for x in p.parts) or p.name=="init_states_test.json" or (p.name=="panel.json" and "final" in p.parts):
            raise RuntimeError("Forbidden weight/sealed payload")
        if str(p).endswith("/results/experiment_supervisor/state.json"):raise RuntimeError("No mutable state read")
        mode,flags=args[1:3]
        writing=any(x in str(mode or "") for x in "wax+") or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)))
        if writing and D not in p.parents:raise RuntimeError("Private audit writes only")
sys.dont_write_bytecode=True
sys.addaudithook(guard)

def replay(row,fn,rt):
    # Engineering-only deterministic recorded-action harness: not a LIBERO rollout.
    obs={"agentview_image":np.zeros((1,1,3),dtype=np.uint8),"robot0_eye_in_hand_image":np.zeros((1,1,3),dtype=np.uint8),"robot0_eef_pos":np.zeros(3),"robot0_eef_quat":np.array([0.,0.,0.,1.]),"robot0_gripper_qpos":np.zeros(2)}
    class Env:
        def __init__(self):self.actions=[]
        def reset(self):return obs
        def set_init_state(self,x):return obs
        def step(self,action):
            self.actions.append(action)
            return obs,0.,bool(row["success"] and len(self.actions)==row["control_steps"]+10),{}
    class Policy:
        def __init__(self):self.i=0
        def reset(self):self.i=0
        def __call__(self,ob,text):
            c=row["chunks"][self.i];self.i+=1
            return rt.PolicyChunk(np.asarray(c["normalized_actions"],dtype=np.float32),np.asarray(c["environment_actions"],dtype=np.float64),c["metadata"])
    env=Env();before=rng()
    out=fn(env,Policy(),"recorded CPU equivalence",np.zeros(1),wait_steps=10,max_steps=520,policy_watchdog_seconds=60.)
    need(rng()==before,"CPU replay RNG changed","replay")
    for k in ("status","success","termination","control_steps","wait_steps","policy_calls"):
        need(out[k]==row[k],"CPU replay output "+k,"replay")
    need(bytes7(env.actions[:10])==bytes7([list(rt.DUMMY_ACTION)]*10),"wait unchanged","replay")
    need(bytes7(env.actions[10:])==bytes7(row["executed_actions"])==bytes7(out["executed_actions"]),"executed bytes unchanged","replay")
    for a,b in zip(out["chunks"],row["chunks"]):
        need(bytes7(a["normalized_actions"])==bytes7(b["normalized_actions"]) and bytes7(a["environment_actions"])==bytes7(b["environment_actions"]) and a["metadata"]==b["metadata"],"emitted chunk changed","replay")
    need(len(out["chunks"])==len(row["chunks"]),"all emitted chunk coverage","replay")
    return {"executed_f64le_sha256":digest(bytes7(out["executed_actions"])),"all_wait_and_control_actions_f64le_sha256":digest(bytes7(env.actions)),"python_numpy_RNG_unchanged":True,"new_GPU_or_simulator_execution":False}

def main():
    need(Path(__file__).parent==D,"private source")
    for rel,h in PINS.items():watch(rel,h)
    archive=read(B+"/manifest.json")
    for x in archive["files"]:
        p=R/B/Path(x["path"]).name
        watch(p,x["sha256"]);need(p.stat().st_size==x["bytes"],"author archived bytes","archive")
        watch(x["path"],x["sha256"])
    mapping=read(B+"/equivalence_map_candidate.json")
    records=[decode(b) for b in (R/B/"per_trial_equivalence_candidates.jsonl").read_bytes().splitlines()]
    builder=load("independent_typed_map_schema_1032",B+"/build_map_v1.py")
    need(builder.validate_candidate(mapping,records)["trials"]==600,"typed candidate structure","map")
    reg=read(REG);hist=read(HIST);prior=read(PRIOR+"/report.json");inventory=read(INV)
    need(len(inventory["files"])==173,"173 source count","source")
    for rel,h in inventory["files"].items():
        for base in (R,S,R/"snapshots/formal_main_v2_run_564be0995e"):watch(base/rel,h)
    sys.path.insert(0,str(S/"src"))
    from cti_vla.evaluation import libero_runtime as rt
    need(Path(rt.__file__)==S/"src/cti_vla/evaluation/libero_runtime.py","exact frozen source import","source")
    adapt=load("independent_original_action_adapter_1032",ADAPT)
    before=rng();oldfn,newfn,astproof=adapt.derive_function(rt,(S/"src/cti_vla/evaluation/libero_runtime.py").read_bytes())
    need(rng()==before and astproof==prior["single_removed_branch_AST_proof"]==mapping["RNG_scope"]["AST_proof_inherited_from_exact_prior_candidate"],"exact one-branch AST and derivation RNG","replay")
    need(astproof["removed_if_count"]==1 and astproof["other_AST_nodes_unchanged"] is True,"no wider AST edit","replay")
    helper=load("independent_original_execution_helper_1032","scripts/formal_execution_manifests.py")
    consumer=load("independent_original_legacy_consumer_1032","scripts/ops/formal_action_deployment_v1/consumer.py")
    ev=helper.Evidence(R)
    root=consumer.review_downstream_output(ev,watch(ROOT),expected_stage="development",suite="libero_10")
    need(root["scientific_complete"] and root["completed_trials"]==600 and root.get("execution_version",OLD)==OLD,"actual old whole-chain consumer passes without relabel","root")
    manifest=read(MAN);config=read(RUN+"/config.json")
    identities={r["identity"]["method_id"]:r["identity"] for r in manifest["methods"]}
    need(list(identities)==METHODS and mapping["method_identities"]==identities,"all original methods/checkpoints","identity")
    need(manifest["environment"]==mapping["environment"]==dict(environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_steps=520),"original environment settings","identity")
    need(config["manifest"]==manifest and sig(config)==root["run_signature"]==mapping["legacy"]["run_signature"],"old config signature","identity")
    target=read(TARGET)
    for rel,h in {**target["files"],**target["GPU_acceptance"],**target["runtime_contract"]["dependencies"]}.items():watch(rel,h)
    reviewer=load("independent_target_reviewer_1032","scripts/ops/formal_action_deployment_v1/reviewer.py")
    need(reviewer.semantic_identity(target)==SEM==mapping["target"]["action_semantics_sha256"],"exact adopted target semantics","identity")
    need(all(x["frozen_model_sha256"]=="9c8fac3f8dcb40c75182d0a4fc6e5329c09185e5ce9eaa3ba561bb3817c9eb77" and x["model_revision"]=="95220f9a3421a7ff12d4218e73d09ade830fa9a3" and x["future_head_deployed"] is False for x in identities.values()),"same official Long base and no future head","identity")
    # Install provenance was historically committed; current inode metadata is
    # observed now, then used for a labelled source-continuity inference.
    for rel,x in hist["evidence"].items():watch(rel,x["sha256"])
    transfer=read("configs/assets/libero_wheels_transfer.json")
    cutoff=datetime(2026,10,17,tzinfo=timezone.utc).timestamp()
    packageproof=[];statproof=[];totalpackage=0
    for wheel,prefix,expectedcount in [
        ("robosuite-1.4.1-py3-none-any.whl","robosuite/",1019),
        ("mujoco-2.3.7-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl","mujoco/",39)]:
        entry=next(x for x in transfer["files"] if x["path"]==wheel)
        w=P/"external/wheels-libero"/wheel;watch(w,entry["sha256"]);members=[]
        with zipfile.ZipFile(w) as z:
            for zi in z.infolist():
                if not zi.filename.startswith(prefix) or zi.is_dir():continue
                p=SP/zi.filename
                need(p.is_file() and not p.is_symlink() and p.resolve()==p,"package missing/symlink "+str(p),"filesystem")
                a=p.stat();raw=p.read_bytes();expected=digest(z.read(zi));b=p.stat()
                need(digest(raw)==expected,"installed wheel member differs "+zi.filename,"filesystem")
                need(a.st_ino==b.st_ino and a.st_size==b.st_size and a.st_ctime_ns==b.st_ctime_ns and a.st_mtime_ns==b.st_mtime_ns,"member changed while reading","filesystem")
                need(a.st_ctime<cutoff and a.st_mtime<cutoff,"package changed after old jobs "+zi.filename,"filesystem")
                members.append({"path":str(p),"member":zi.filename,"sha256":expected,"bytes":a.st_size,"device":a.st_dev,"inode":a.st_ino,"ctime_ns":a.st_ctime_ns,"mtime_ns":a.st_mtime_ns})
        need(len(members)==expectedcount,"complete installed package member coverage","filesystem")
        packageproof.append({"wheel":str(w),"wheel_sha256":entry["sha256"],"member_count":len(members),"max_ctime_utc":datetime.fromtimestamp(max(x["ctime_ns"] for x in members)/1e9,timezone.utc).isoformat(),"all_installed_bytes_match":True,"all_non_symlink_and_pre_old600_ctime":True})
        statproof.extend(members);totalpackage+=len(members)
    need(not (SP/"robosuite/macros_private.py").exists(),"no current private macro","filesystem")
    freeze=(R/"results/setup/after_libero_freeze.txt").read_text()
    need("robosuite-1.4.1-py3-none-any.whl#sha256=62587cd5888d9d3d813f3ffcc7017f6f77efa618952527a0b9bb139ffd0a3741" in freeze and "mujoco-2.3.7" in freeze,"historical exact installed distributions","historical")
    install=(P/"results/setup/install_libero_local_attempt4.log").read_text()
    need("Verified transferred runtime packages: 11" in install and "Successfully installed" in install and "runtime_imports_passed" in install,"historical install verified and imported","historical")
    limits=decode((SP/"robosuite/controllers/config/osc_pose.json").read_bytes())
    need(limits==hist["factory_chain"]["pinned_distribution_limits"] and limits["control_delta"] is True and limits["input_max"]==1 and limits["input_min"]==-1,"same controller defaults","historical")
    factory=(R/"scripts/eval_formal_selector_libero.py").read_text()
    need(all(t in factory for t in ["random.seed(17)","np.random.seed(17)","torch.manual_seed(17)","env.seed(0)","camera_heights=256, camera_widths=256"]),"frozen reseed and factory","historical")
    wrapper=P/"external/LIBERO/libero/libero/envs/env_wrapper.py"
    watch(wrapper,"2880cad5b3fe46ea105816f42798faf4c22e16839098b679ebcad7b51acfdbd0")
    need(wrapper.stat().st_ctime<cutoff and not wrapper.is_symlink(),"LIBERO current unchanged since pre-old jobs","filesystem")
    need('controller="OSC_POSE"' in wrapper.read_text() and "suite.load_controller_config(default_controller=controller)" in wrapper.read_text(),"same default controller dispatch","historical")
    oldbindings=[]
    for attempt in hist["factory_chain"]["old_attempts"]:
        job=attempt["job_id"];journal=[decode(b) for b in (R/attempt["journal"]).read_bytes().splitlines()]
        official=[x for x in journal if x["event"]=="official_source_verified"]
        need(len(official)==2 and {x["expected_revision"] for x in official}=={"8f1084e3132a39270c3a13ebe37270a43ece2a01","e4287e94541f459edc4feabc4e181f537cd569a8"},"old official source verification "+job,"historical")
        lib=next(x for x in official if x["path"].endswith("/LIBERO"))
        need(lib["verification"]["archive_sha256"]=="e0a261753ce056649da67f4c71938391a8d7c55a3eae53e4c17a5d79649da55c","old whole-LIBERO archive binds factory/assets","historical")
        need(all(datetime.fromisoformat(x["utc"]).timestamp()>cutoff for x in official),"old jobs after observed inode cutoff","historical")
        err=(R/attempt["historical_stderr"]).read_text()
        need(attempt["historical_import_warning_path"] in err and "No private macro file found!" in err,"old actual venv import and no macro "+job,"historical")
        j=next(x for x in root["registered_jobs_at_review"] if x["job_id"]==job)
        inv=read(j["invocation"],j["invocation_sha256"])
        need(inv["version"]==OLD and inv["source_sha256"]==inventory["source_sha256"],"old invocation unchanged source","historical")
        oldbindings.append({"job_id":job,"actual_import_path_warning":attempt["historical_import_warning_path"],"private_macro_absent_in_old_stderr":True,"LIBERO_archive_sha256":lib["verification"]["archive_sha256"],"official_source_verified_utc":lib["utc"],"invocation":watch(j["invocation"],j["invocation_sha256"]),"old_controller_instance_hash_recorded":False})
    need([x["job_id"] for x in oldbindings]==JOBS,"all six old jobs historical bindings","historical")
    v4events=[decode(b) for b in (R/V4).read_bytes().splitlines()]
    cells=[e for e in v4events if e.get("event")=="actual_controller_verified" and e.get("suite")=="libero_10"]
    need(len(cells)==4,"accepted real-GPU target four Long controllers","historical")
    for e in cells:
        c=e["controller"]
        need(c["controller_type"]=="robosuite.controllers.osc.OperationalSpaceController" and c["actual_use_delta"] is True and c["limits"]=={"input_max":[1.]*6,"input_min":[-1.]*6,"output_max":limits["output_max"],"output_min":limits["output_min"]},"target actual controller agrees with historical factory/defaults","historical")
    # Fresh independent action-byte and CPU function equivalence, all full chunks.
    previous={x["trial_id"]:x for x in [decode(b) for b in (R/PRIOR/"per_trial.jsonl").read_bytes().splitlines()]}
    oldchunk=iter(decode(b) for b in (R/PRIOR/"per_chunk.jsonl").read_bytes().splitlines())
    mapby={x["trial_id"]:x for x in records};need(len(mapby)==600,"no duplicate typed records","map")
    statepanel=read(RUN+"/panel.json");states={x["trial_id"]:x for x in statepanel["states"]}
    need(len(states)==100,"100 unique fixed development states","identity")
    offset=0;active=None;job=None;pertrial=[];counts=Counter();stats={m:Counter() for m in METHODS};statecoverage={}
    def line_ref(n,offset,b):return {"line":n,"byte_offset":offset,"bytes":len(b),"sha256":digest(b)}
    for lineno,b in enumerate((R/RUN/"trials.jsonl").open("rb"),1):
        need(b.endswith(b"\n"),"unterminated ledger","raw")
        lr=line_ref(lineno,offset,b);offset+=len(b);row=decode(b)
        need(row["run_signature"]==root["run_signature"],"raw run signature","raw")
        if row["event"]=="invocation":
            need(active is None and row["slurm_job_id"] in JOBS,"raw invocation","raw");job=row["slurm_job_id"];continue
        if row["event"]=="start":
            need(active is None,"overlapping start","raw");active=(row,lr);continue
        need(row["event"]=="result" and active is not None,"raw result pairs","raw")
        start,sr=active;active=None;record=mapby[row["trial_id"]];priorrow=previous[row["trial_id"]];identity=identities[row["method"]]
        need(row["method"]==METHODS[len(pertrial)%6] and row["status"]=="completed","all six methods no outcome selection","raw")
        for k in ["action_chunk","configured_wait_steps","environment_seed","initial_state_sha256","method","run_signature","runtime_seed","source_state_index","split","state_trial_id","suite","task_id","task_name","trial_id"]:
            need(row[k]==start[k],"raw start/result "+k,"raw")
        state=states[row["state_trial_id"]]
        need(all(row[k]==state[k] for k in ["initial_state_sha256","source_state_index","task_id","task_name"]),"fixed state identity","identity")
        need(row["environment_seed"]==0 and row["runtime_seed"]==17 and row["wait_steps"]==row["configured_wait_steps"]==10 and row["action_chunk"]==8 and row["control_steps"]<=520,"unchanged trial controls","identity")
        need(record["source"]["start_line"]==sr and record["source"]["result_line"]==lr and record["source"]["job_id"]==job and record["source"]["run_signature"]==root["run_signature"],"exact typed raw positions","map")
        need(record["method_identity_sha256"]==sig(identity) and record["outcome"]=={k:row[k] for k in ["status","success","termination","control_steps"]},"typed outcome identity unchanged","map")
        queue=[];metadata=[];clip6=clip7=0;maxabs=0.
        for i,c in enumerate(row["chunks"]):
            need(c["control_step"]==8*i and len(c["environment_actions"])==len(c["normalized_actions"])==8,"all emitted chunk8 including unused suffix","actions")
            eb=bytes7(c["environment_actions"]);nb=bytes7(c["normalized_actions"]);a=np.asarray(c["environment_actions"],dtype=np.float64);md=c["metadata"]
            need((np.abs(a)<=1.00001).all(),"old amplitude branch not taken","actions")
            clip7+=np.count_nonzero(a.view(np.uint64)!=np.clip(a,-1,1).view(np.uint64))
            arm=a[:,:6].copy();clip6+=np.count_nonzero(arm.view(np.uint64)!=np.clip(arm,-1,1).view(np.uint64))
            need(md["suite"]=="libero_10" and md["method"]==identity["method"] and md["visual_tokens"]==identity["visual_tokens"] and md["per_camera_budgets"]==[identity["visual_tokens"]//2]*2,"actual deployment budget/method","actions")
            need(md["future_head_calls"]==0 and md["policy_calls"]==md["vision_calls"]==md["packing_calls"]==1 and md["language_cache"]=="disabled" and md["scorer_calls"]==int(identity["method"] in ("A","B")),"same one-forward deployment","actions")
            if identity["method"] in ("A","B"):need(md["selector_checkpoint_sha256"]==identity["checkpoint_sha256"] and md["training_seed"]==17,"actual selected checkpoint","actions")
            need(next(oldchunk)=={"trial_id":row["trial_id"],"chunk_index":i,"control_step":8*i,"environment_f64le_sha256":digest(eb),"normalized_f64le_sha256":digest(nb),"environment_shape_finite_old_range":True,"metadata_sha256":sig(md),"observation_sha256":c["observation_sha256"]},"prior per-chunk exact binding","map")
            queue.extend(c["environment_actions"]);metadata.append(sig(md));maxabs=max(maxabs,float(np.abs(a).max()))
        executed=bytes7(row["executed_actions"]);emitted=bytes7(queue)
        need(executed==bytes7(queue[:row["control_steps"]]) and len(row["executed_actions"])==row["control_steps"],"exact executed queue prefix","actions")
        need(len(row["chunks"])==row["policy_calls"]==(row["control_steps"]+7)//8 and clip6==clip7==0,"counts and inactive native clip","actions")
        oldreplay=replay(row,oldfn,rt);newreplay=replay(row,newfn,rt)
        need(oldreplay==newreplay==priorrow["old_runtime_replay"]==priorrow["new_runtime_replay"],"fresh independent old/new CPU recorded replay","replay")
        a=record["action_evidence"]
        need(a["recorded_executed_f64le_sha256"]==a["old_CPU_replay_executed_sha256"]==a["new_CPU_replay_executed_sha256"]==digest(executed) and a["all_emitted_f64le_sha256"]==digest(emitted),"typed action bytes","map")
        need(a["clip_changed_all7"]==a["clip_changed_arm6"]==0 and a["maximum_absolute_environment_action"]==maxabs and a["full_chunks"]==len(row["chunks"]) and a["executed_actions"]==row["control_steps"],"typed complete coverage","map")
        statecoverage.setdefault(row["state_trial_id"],set()).add(row["method"])
        stats[row["method"]].update(trials=1,successes=int(row["success"]),full_chunks=len(row["chunks"]),executed_actions=row["control_steps"])
        counts.update(trials=1,chunks=len(row["chunks"]),actions=row["control_steps"])
        pertrial.append({"trial_id":row["trial_id"],"method_id":row["method"],"state_trial_id":row["state_trial_id"],"job_id":job,"typed_row_sha256":sig(record),"old_new_fresh_CPU_replay":oldreplay,"full_chunks":len(row["chunks"]),"executed_actions":row["control_steps"],"maximum_absolute_environment_action":maxabs,"branch_never_taken":True,"native_clip_changes":0,"old_execution_version":OLD,"target_action_semantics_sha256":SEM,"new_scientific_trial":False})
    need(active is None and counts==Counter(trials=600,chunks=23179,actions=183676),"complete original600","coverage")
    try:next(oldchunk)
    except StopIteration:pass
    else:raise ValueError("extra prior chunk")
    need(len(statecoverage)==100 and all(v==set(METHODS) for v in statecoverage.values()) and all(v["trials"]==100 for v in stats.values()),"600 Cartesian coverage not600 independent states","coverage")
    need({m:dict(v) for m,v in stats.items()}==read(B+"/report.json")["per_method"],"all outcomes kept","coverage")
    need(root["cost"]["all_attempt_gpu_seconds"]==10531 and sum(x["elapsed_seconds"]*x["gpus"] for x in root["cost"]["allocations"])==10531 and root["raw_invocation_job_ids"]==JOBS,"all six original allocations once","cost")
    need(rt.run_episode is oldfn,"original runtime binding untouched","source")
    # Meaningful rejection tests for exact bytes and typed immutable scope.
    negative=[]
    for label in ["legacy_relabel","subset","changed_action","approval","fake_instance","invented_RNG_gate"]:
        m=copy.deepcopy(mapping);rs=copy.deepcopy(records)
        if label=="legacy_relabel":m["legacy"]["execution_version"]=NEW
        elif label=="subset":rs.pop()
        elif label=="changed_action":rs[0]["action_evidence"]["new_CPU_replay_executed_sha256"]="0"*64
        elif label=="approval":m["adoption"]["production_reuse_authorized"]=True
        elif label=="fake_instance":m["controller_identity"]["old_instance_hash_recorded"]=True
        else:m["RNG_scope"]["old_dump_required_by_registration"]=True
        try:builder.validate_candidate(m,rs)
        except ValueError as e:negative.append({"case":label,"rejected":True,"reason":str(e)})
        else:raise ValueError("negative incorrectly accepted "+label)
    need(bytes7([[0.]+[0.]*6])!=bytes7([[-0.]+[0.]*6]),"signed zero is not falsely equivalent","negative")
    need(bytes7([[0.5]+[0.]*6])!=bytes7([[math.nextafter(.5,1.)]+[0.]*6]),"one ULP is not falsely equivalent","negative")
    for row in statproof:
        st=Path(row["path"]).stat()
        need(st.st_ino==row["inode"] and st.st_dev==row["device"] and st.st_ctime_ns==row["ctime_ns"] and st.st_mtime_ns==row["mtime_ns"] and st.st_size==row["bytes"],"package metadata changed during audit","filesystem")
    for rel,h in inventory["files"].items():need(sha(R/rel)==h and sha(S/rel)==h,"frozen unchanged at audit exit","source")
    ev.unchanged()
    provenance=save("historical_identity_evidence.json",{"kind":"independent_historical_source_continuity_evidence","observed_utc":datetime.now(timezone.utc).isoformat(),"proof_mode":"Historical installation/import/factory records plus current Linux inode continuity inference; not old bound-instance capture","historical_provenance_ref":watch(HIST),"pre_old600_Git_anchors_inherited_exact":hist["historical_installation_evidence"]["pre_old600_Git_anchors"],"package_archives":packageproof,"package_members":statproof,"private_macro_absent_now":True,"private_macro_absent_in_all_old_stderr":True,"old_invocations":oldbindings,"controller_config":limits,"target_actual_v4_controller_cells":cells,"original_identity_condition_satisfied":True,"reason":"Exact installed wheel bytes and ordinary Linux inode ctime predate all old runs; old logs import this same venv without private macros; pinned factory and per-run verified LIBERO archive select the same controller/defaults; accepted target captures match these bytes/parameters.","evidence_limit":"The old per-job controller instance hash was never captured. Current inode observations support source continuity; they are not represented as contemporaneous measurements. No historical full RNG dump is required or supplied."})
    actionsref=save("independent_per_trial_action_review.jsonl",pertrial,True)
    proofref=save("original_consumer_and_AST_proof.json",{"original_root":watch(ROOT),"original_consumer_actual_reconstruction":True,"original_execution_version":OLD,"completed_trials":root["completed_trials"],"cost":root["cost"],"consumer_evidence_sha256":ev.files,"target":watch(TARGET),"target_action_semantics_sha256":SEM,"single_branch_AST_proof":astproof,"fresh_independent_replays":1200,"replay_scope":"600 recorded trajectories x old/new action function, deterministic CPU fake environment; zero LIBERO or policy/model runs","Python_NumPy_RNG_unchanged":True,"production_function_binding_changed":False})
    evidence=save("evidence.json",dict(sorted(watched.items())))
    report={"schema":"formal_main_v2","kind":"independent_legacy600_typed_equivalence_admission_review","status":"passed_independent_admission_recommendation","decision":"accept_exact_600_typed_equivalence","reviewed_by":"independent_non_author","candidate_map":watch(B+"/equivalence_map_candidate.json"),"candidate_author_report":watch(B+"/report.json"),"original_registration":watch(REG),"original_rule":reg["historical_development"]["normal_trial_reuse_rule"],"original_controller_environment_identity_condition_satisfied":True,"identity_reasoning":"The newly checked pre-run inode ctime and exact full-package wheel equality close the earlier in-place-edit continuity gap under ordinary Linux filesystem semantics. Combined with six old actual import paths/no-private-macro warnings and per-invocation verified frozen LIBERO/factory, this is sufficient source-derived controller/environment identity for the exact old600 under the registered rule.","identity_evidence":provenance,"earlier_0830_readiness_updated_by_new_evidence":"Earlier source installation/factory evidence alone left continuity unproven. This review adds 1058 installed package-file hashes and inode metadata predating every old invocation, then independently verifies all action traces; it does not discard or rewrite the earlier report.","checks_passed":sum(checks.values()),"checks_by_group":dict(checks),"coverage":mapping["coverage"],"per_method":{m:dict(v) for m,v in stats.items()},"per_trial_review":actionsref,"original_consumer_AST_and_replay":proofref,"negative_tests":negative,"cost":{"historical_GPU_seconds_counted_once":10531,"new_GPU_seconds":0,"new_scientific_trials":0,"new_cpu_wall_seconds":time.perf_counter()-began},"limits":["Acceptance is for all six original Long development methods on the same100 unique initial states; no outcome subset or relabelled execution version.","The historical bound-controller instance hash and full historical RNG state were not captured. This review uses a labelled source-continuity inference, not fabricated measurements; old RNG dumps are not an added gate.","Recorded-action CPU replays are engineering proofs, not newly executed LIBERO trajectories or policy predictions.","No old O2A latency reuse, no final-state release, no new GPU runs, no checkpoint reselection.","Production reuse still needs root final adoption and a separately versioned, audited typed consumer integration; the existing production consumer is unchanged."],"independent_admission_recommendation":True,"production_reuse_activated":False,"production_consumer_changed":False,"root_adoption_granted_by_this_agent":False,"state_or_Git_changed":False,"weights_or_sealed_values_read":False,"old_execution_version_preserved":OLD,"target_action_semantics_sha256":SEM,"old_latency_reused":False,"final_release":False,"evidence":evidence,"reviewed_utc":datetime.now(timezone.utc).isoformat()}
    reportref=save("independent_review.json",report)
    manifestref=save("manifest.json",{"kind":"independent_admission_audit_manifest","files":[{"path":p.relative_to(R).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(D.iterdir()) if p.is_file() and p.name!="manifest.json"]})
    print(json.dumps({"status":report["status"],"decision":report["decision"],"report":reportref,"manifest":manifestref,"checks":sum(checks.values()),"CPU_wall_seconds":time.perf_counter()-began}))
if __name__=="__main__":
    try:main()
    except BaseException as e:
        save("failure_a1.json",{"error":str(e),"type":type(e).__name__,"traceback":traceback.format_exc(),"checks_by_group":dict(checks),"GPU_runs":0,"production_changed":False})
        raise
