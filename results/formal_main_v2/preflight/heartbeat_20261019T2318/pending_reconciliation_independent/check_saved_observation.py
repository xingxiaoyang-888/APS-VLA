"""Read-only reconstruction of already captured scheduler facts; no scheduler calls."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,importlib.util,sys,datetime
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/spatial_pending_reconciliation_independent_1518"
B="results/formal_main_v2/downstream_gateway/55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6/"
PROBE="results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_pending_probe_v2.json"
refs={}
def read(rel,pin=None):
 p=R/rel;b=p.read_bytes();h=hashlib.sha256(b).hexdigest();refs[rel]=h
 if pin:assert h==pin,rel
 return json.loads(b)
def load(rel,pin,name):
 p=R/rel;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==pin;refs[rel]=pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load("scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","pending_independent_c")
g=load("scripts/ops/formal_action_deployment_v1/gateway.py","8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a","pending_independent_g")
probe=read(PROBE,"888c31564d5cb2b4eab5e306c7f2e375b2d56832994dde63f5dbaa26707390f1")
pre=read(B+"preflight.json","a518aa6d2fb38f7758d3bf3b7498d9121f47a0ccd4a4033fdf1317a9bef508a9")
ack=read(B+"sbatch_result.json","4bf3ea640995e4d8f34bb7159b2d5f9ffcaf746b2430b5096850173f101658a4")
failure=read(B+"failed_transaction.json","e507571a2c45d2d86c1ba5944bcd7ff67ced0b8ede719f704f9609a723b9b18c")
jobs=pre["registered_jobs"]+[probe["job"]]
assert g.parse_ack(SimpleNamespace(**{k:ack[k] for k in ("returncode","stdout","stderr")}),{str(x["job_id"]) for x in pre["registered_jobs"]})=="3042529"
calls=[]
def saved_query(argv,**kwargs):
 assert argv[0] in {"sacct","squeue"}
 calls.append(argv)
 return SimpleNamespace(returncode=0,stderr="",stdout=probe["observation"]["raw_sacct" if argv[0]=="sacct" else "raw_squeue"])
snapshot=c.Slurm(runner=saved_query).observe(jobs)
assert snapshot==probe["observation"]
caps=g.reconcile_submission(c,jobs,snapshot,probe["job"],probe["pending"]["request_token"],"3034538",probe["scontrol_corroboration"])
assert caps==probe["capacity"] and len(caps["occupied"])==7 and not caps["unknown"] and not caps["findings"]
row=snapshot["rows"]["3042529"]
assert (row["status"],row["exit_code"],row["gpus"],row["elapsed_seconds"],row["node"])==("FAILED","1:0",1,2,"gpu4002")
assert len(snapshot["rows"])==len(jobs)==258
assert probe["pending"]["request_token"]==probe["scontrol_corroboration"]["comment"]
assert probe["scontrol_corroboration"]["status"]=="FAILED"
checks=["actual_saved_ACK_exact_new_ID","original_parser_rebuilds_all258_saved_rows_and_queue","original_identity_capacity_gate_passes_saved_snapshot","new_FAILED1_0_2GPUseconds_retained"]
# Establish the precise failure branch without claiming the original missing ID.
import copy
missing=copy.deepcopy(snapshot);missing["rows"].pop("3042529")
try:g.reconcile_submission(c,jobs,missing,probe["job"],probe["pending"]["request_token"],"3034538",probe["scontrol_corroboration"])
except ValueError as ex:assert str(ex)=="post-submit accounting incomplete"
else:raise AssertionError("missing accounting row accepted")
checks.append("missing_row_reproduces_exact_gate_error_but_not_original_cause_proof")
bad=copy.deepcopy(probe["scontrol_corroboration"]);bad["comment"]="another-token"
try:g.reconcile_submission(c,jobs,snapshot,probe["job"],probe["pending"]["request_token"],"3034538",bad)
except ValueError as ex:assert "token" in str(ex)
else:raise AssertionError("wrong token accepted")
checks.append("wrong_actual_scontrol_token_rejected")
refs[str(Path(__file__).relative_to(R))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result={"schema":"formal_main_v2","kind":"pending_submission_saved_observation_independent_reconstruction","status":"passed_saved_observation_checks_not_commit_authorization","created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"job_id":"3042529","actual_saved_status":row,"registered_rows":258,"active_GPU_count":7,"new_job_GPU_seconds":2,"checks":checks,"synthetic_query_replay":{"actual_scheduler_invoked":False,"saved_actual_query_argv_reconstructed":calls,"fault_injections":2},"original_missing_accounting_ID_known":False,"accounting_delay_proved":False,"production_state_written":False,"submissions":0,"read_evidence_sha256":refs}
p=D/"saved_observation_reconstruction.json"
with p.open("x") as f:json.dump(result,f,sort_keys=True,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":len(checks),"production_mutation":False}))
