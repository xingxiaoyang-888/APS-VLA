import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
A=R/".local/action_v4_autonomous_dispatch_audit_1940"
C=R/".local/action_v4_autonomous_dispatch_1940"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=json.loads((A/"static_binding_review.json").read_text())
assert sha(A/"static_binding_review.json")=="1e6f217d60411ce9401a96804d34545c618da822a0c76de7732fd2c5c6ee2e92"
e=dict(s["read_evidence_sha256"])
for p,h in e.items():assert sha(p)==h,p
for p in [A/"static_binding_review.json",A/"bindings_a1.execution.json",A/"bindings_a1.stdout",A/"bindings_a1.stderr",Path(__file__)]:
 e[str(p)]=sha(p)
assert str(R/"results/experiment_supervisor/state.json") not in e
xml=ET.parse(A/"pytest_a1.xml").getroot()
xs=list(xml) if xml.tag=="testsuites" else [xml]
secs=sum(float(x.attrib.get("time",0)) for x in xs)
author_xml=ET.parse(C/"cpu_final.xml").getroot()
asuites=list(author_xml) if author_xml.tag=="testsuites" else [author_xml]
author_counts={k:sum(int(x.attrib.get(k,0)) for x in asuites) for k in ("tests","failures","errors","skipped")}
assert author_counts==dict(tests=34,failures=0,errors=0,skipped=0)
out={
 "schema":"formal_main_v2",
 "kind":"action_execution_GPU_v4_autonomous_dispatch_independent_CPU_review",
 "version":"action-v4-autonomous-dispatch-independent-1940-v1",
 "status":"passed_CPU_independent_review",
 "reviewed_utc":datetime.now(timezone.utc).isoformat(),
 "reviewer":"train64; independent of server_v3_audit control implementation",
 "files":{str(C/n):h for n,h in s["source_pins"].items()},
 "author_receipt":{"path":str(C/"candidate_review.json"),"sha256":e[str(C/"candidate_review.json")]},
 "root_bindings":s["root_bindings"],
 "independent_tests":{
  "counts":s["independent_tests"],"duration_seconds_JUnit":secs,
  "test_source":{"path":str(A/"test_control_independent.py"),"sha256":e[str(A/"test_control_independent.py")]},
  "command":{"path":str(A/"pytest_a1.command.json"),"sha256":e[str(A/"pytest_a1.command.json")]},
  "JUnit":{"path":str(A/"pytest_a1.xml"),"sha256":e[str(A/"pytest_a1.xml")]},
  "log":{"path":str(A/"pytest_a1.log"),"sha256":e[str(A/"pytest_a1.log")]},
  "coverage":[
   "Actual published execute_submit and node adapter with restricted facade; legacy refresh poisoned and not called.",
   "All registered IDs queried in synthetic Slurm: CPU exemption requires registered and observed zero GPU; mixed eight-GPU modes reject.",
   "Unknown/missing/unsupported/queue mismatch/duplicate pair/pending conflicts fail closed.",
   "Ambiguous scheduler response, known ACK with receipt failure, shared lock conflict and CAS drift retain transaction uncertainty without resend.",
   "Full registered rows, controller fields and historical billing survive exact permitted writes; unrelated mutations are rejected.",
   "Consumed v3 reservation cannot authorize v4; failed v3 record retained and new one-shot uses separate v4 namespace.",
   "Missing shared lock in read-only mode creates no files."
  ],
  "explicit_stand_ins":[
   "No actual Slurm call, production state transaction, remote publication or job acknowledgement: injected synthetic scheduler/transport and own temporary repository.",
   "The runtime scientific closure supplied to transaction fixtures is synthetic; actual published 290-file metadata closure independently rebuilt read-only.",
   "No model/environment/action GPU execution and no checkpoint content load."
  ]
 },
 "author_tests_read_only_cross_check":{"final_counts":author_counts,"rerun_by_this_review":False},
 "static_checks":{
  "entry_facade_exact_mechanical_derivation_from_v3":True,
  "only_changes":"v4 namespace, actual root/GPU/node/reservation references, six-source binding plus reused original-v3 adapter/constructor proof, source-label rename",
  "original_execute_submit_SHA_unchanged":True,
  "actual_deployment_closure_count":290,
  "R_frozen_files":173,"S_frozen_files":173,
  "protected_files_unchanged":380,"author_reference_hashes_verified":501,
  "registered_suite_rows_and_selected_checkpoint_metadata_equal_v3":True,
  "fixed_limits":s["unchanged_limits"],
  "root_intent_excludes_self_reference":True,
  "root_deployment_excludes_root_registration_and_final_control_self_cycle":True,
  "shared_writer_lock_CAS_capacity_and_exact_write_whitelist_unchanged":True,
  "node_exclusion":"gpu4020; future explicit v4 submission only",
  "old_v3_source_and_failed_record_not_rewritten":True,
  "fixed_stage":"formal_main_v2_action_execution_compat_gpu_v4",
  "automatic_retry":False,"max_attempts":1
 },
 "decision":"No CPU control-layer blocker. Root may make the separately registered one-shot engineering submit only after fresh same-lock all-registry Slurm, pending, prior-attempt, reservation and <8 active-GPU checks.",
 "limits":[
  "This receipt does not submit or authorize a retry of v3 and does not establish that v4 GPU engineering passed.",
  "No live capacity claim: root performs the fresh check immediately before submission; healthy jobs must not be cancelled and a ninth active GPU request is forbidden.",
  "Sixteen engineering cells only; no scientific success rate/latency result, no final/test release.",
  "Only root may consume the exact new v4 reservation; current controller and all historical failures/costs remain."
 ],
 "actual_Slurm_queries":0,"actual_Slurm_submissions":0,
 "production_state_reads":0,"production_state_writes":0,
 "GPU_calls":0,"GPU_cost_seconds":0,"checkpoint_contents_read":False,
 "sealed_state_values_read":False,"scientific_release":False,"Windows_project_writes":0,
 "evidence_sha256":dict(sorted(e.items())),
 "read_evidence_sha256":dict(sorted(e.items()))
}
p=A/"independent_review.json"
with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(out,f,indent=2,ensure_ascii=False);f.write("\n")
print(json.dumps({"path":str(p),"sha256":sha(p),"references":len(e),"status":out["status"],"entry_sha256":out["files"][str(C/"entry.py")],"JUnit_seconds":secs}))
