"""Independent v2-only delta checks. No state mutation, scheduler or main execution."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,json,datetime
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
D=R/".local/spatial_pending_reconciliation_independent_1518";B="results/formal_main_v2/preflight/heartbeat_20261019T2318"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/".local/reconcile_commit_1518.py";new=R/".local/reconcile_commit_1518_v2.py"
assert h(old)=="7a978396858622e0ad1aa2fa54699db499cf563a5d7327a3d4bfe6d977729490"
assert h(new)=="e30ab4fe979812baa07a8eb5e71d342bd9a40de76763ff49e93099f9b61116d4"
a=ast.parse(old.read_bytes());b=ast.parse(new.read_bytes())
wa=next(x for x in a.body if isinstance(x,ast.With));wb=next(x for x in b.body if isinstance(x,ast.With))
def target(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
start=next(i for i,x in enumerate(wb.body) if target(x,"probe"))
end=next(i for i,x in enumerate(wb.body) if i>start and target(x,"caps"))
oldnode=next(x for x in wa.body if target(x,"corroboration"))
rev=copy.deepcopy(b);wr=next(x for x in rev.body if isinstance(x,ast.With))
wr.body[start:end]=[copy.deepcopy(oldnode)]
receipt=next(x for x in wr.body if target(x,"receipt"))
receipt.value.keywords=[x for x in receipt.value.keywords if x.arg!="terminal_identity_recovery"]
assert ast.dump(rev,include_attributes=False)==ast.dump(a,include_attributes=False),"v2 contains undeclared code changes"
block=ast.Module(body=wb.body[start:end],type_ignores=[])
assert not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in {"submit","record","atomic_json","write_bytes","write_text"} for x in ast.walk(block))
program=compile(block,str(new),"exec",dont_inherit=True)
raw=json.loads((D/"v2_actual_terminal_queries.json").read_bytes())
prior=json.loads((R/B/"Spatial_pending_probe_v2.json").read_bytes())
results=[]
for case in ["success","wrong_control_error","control_stdout","different_account_user","different_start_time","extra_account_row","changed_snapshot","changed_pending"]:
 answers=copy.deepcopy(raw["queries"]);snapshot=copy.deepcopy(prior["observation"]);pending=copy.deepcopy(prior["pending"])
 if case=="wrong_control_error":answers[0]["stderr"]="permission denied\n"
 if case=="control_stdout":answers[0]["stdout"]="unexpected live row\n"
 if case=="different_account_user":answers[1]["stdout"]=answers[1]["stdout"].replace("|u15016|","|another_user|")
 if case=="different_start_time":
  fields=answers[1]["stdout"].rstrip("\n").split("|");fields[8]="2026-10-19T23:21:39";answers[1]["stdout"]="|".join(fields)+"\n"
 if case=="extra_account_row":answers[1]["stdout"]+=answers[1]["stdout"]
 if case=="changed_snapshot":snapshot["rows"]["3042529"]["elapsed_seconds"]=3
 if case=="changed_pending":pending["plan_sha256"]="f"*64
 calls=[]
 def run(argv):
  k=len(calls);assert k<2 and argv==answers[k]["argv"];calls.append(argv)
  return SimpleNamespace(**{n:answers[k][n] for n in ["returncode","stdout","stderr"]})
 namespace=dict(R=R,P=P,B=B,h=h,json=json,p=pending,snapshot=snapshot,scheduler=SimpleNamespace(run=run))
 outcome=None
 try:exec(program,namespace);outcome="accepted"
 except AssertionError:outcome="rejected"
 assert outcome==("accepted" if case=="success" else "rejected"),case
 if case=="success":
  x=namespace["recovery_identity"];assert x["terminal_state_unchanged"] is True and x["scontrol_live_record_expired"] is True
  assert x["fresh_sacct"]["stdout"]==raw["queries"][1]["stdout"]
 results.append({"case":case,"passed":True,"outcome":outcome,"replayed_query_count":len(calls)})
out={"schema":"formal_main_v2","kind":"known_terminal_scontrol_expiration_delta_CPU_checks","status":"passed_CPU_delta_checks","source_sha256":h(new),"AST_reverse_to_v1_exact":True,"tests":results,"actual_Slurm_queries_in_tests":0,"state_writes":0,"real_main_executed":False,"query_source":{"path":str((D/"v2_actual_terminal_queries.json").relative_to(R)),"sha256":h(D/"v2_actual_terminal_queries.json")},"historical_probe":{"path":B+"/Spatial_pending_probe_v2.json","sha256":h(R/B/"Spatial_pending_probe_v2.json")},"test_sha256":h(Path(__file__))}
q=D/"v2_delta_CPU_checks.json"
with q.open("x") as f:json.dump(out,f,indent=2,sort_keys=True);f.write("\n")
print(json.dumps({"path":str(q),"sha256":h(q),"tests":len(results),"declared_diff_only":True}))
