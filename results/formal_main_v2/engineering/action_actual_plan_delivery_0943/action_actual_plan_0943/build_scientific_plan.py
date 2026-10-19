"""Actual pure planner, server-only; prohibits process/network and any writes outside this draft."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,os,sys,traceback
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/action_actual_plan_0943"
sys.dont_write_bytecode=True
def guard(event,args):
    if event in ("subprocess.Popen","os.system","socket.connect"):raise RuntimeError("No scheduler/subprocess/network in actual pure planning")
    if event=="open":
        path,mode,flags=args
        if isinstance(path,(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(path))
            if not p.is_absolute():p=Path.cwd()/p
            lower=str(p).lower()
            if ("sealed" in lower or p.suffix.lower() in {".pt",".pth",".safetensors",".pkl",".pickle",".ckpt",".bin",".pruned_init",".init"}):
                raise RuntimeError("No weight or sealed payload reads in pure planner: "+str(p))
            writing=(isinstance(mode,str) and any(x in mode for x in "wax+")) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
            if writing and D not in p.parents:raise RuntimeError("Planner tried write outside draft: "+str(p))
sys.addaudithook(guard)
state_path=R/"results/experiment_supervisor/state.json";state_raw=state_path.read_bytes();state=json.loads(state_raw)
(D/"state_at_planning.json").write_bytes(state_raw)
arguments=dict(stage="development",source_inventory="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json",
 execution_manifest="results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json",
 output_relative="results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01",
 freeze_directory=None,profile_panel=None,prior_review="results/formal_main_v2/downstream_reviews/3022743.json",
 collection_review=None,repair_record=None,resume=True,stop_after=None)
(D/"plan_arguments.json").write_text(json.dumps(arguments,indent=2)+"\n")
path=R/"scripts/ops/formal_downstream_supervisor.py"
pin="f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571"
assert hashlib.sha256(path.read_bytes()).hexdigest()==pin
spec=importlib.util.spec_from_file_location("actual_read_only_scientific_planner",path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
started=datetime.now(timezone.utc).isoformat()
try:
    result=m.plan(SimpleNamespace(**arguments),copy.deepcopy(state),project=R)
except BaseException as exc:
    (D/"pure_planner_failure.json").write_text(json.dumps(dict(kind="actual_pure_planner_failed",started_utc=started,
       scientific_inputs_synthetic=False,exception_type=type(exc).__name__,error=str(exc),state_at_read_sha256=hashlib.sha256(state_raw).hexdigest(),
       trace=traceback.format_exc(),arguments=arguments),ensure_ascii=False,indent=2)+"\n")
    raise
raw=(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
(D/"scientific_plan.json").write_bytes(raw)
print(json.dumps(dict(kind="actual_scientific_plan_built",plan_sha256=result["plan_sha256"],
 file_sha256=hashlib.sha256(raw).hexdigest(),method_ids=result["invocation"]["method_ids"],
 evidence_count=len(result["invocation"]["root_evidence_sha256"]),published_count=len(result["publish_files"]),
 source_provenance=result["invocation"]["source_provenance"],prior_jobs=result["invocation"]["prior_job_ids"]),ensure_ascii=False))
