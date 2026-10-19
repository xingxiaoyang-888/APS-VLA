"""Close the CPU preparation evidence; no production writes or submission."""
import hashlib, importlib.util, json, sys, xml.etree.ElementTree as ET
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[1]
PIN="3231fcc6be4c48da80e0a75580ddc05bd4b6197e6423b536f28be6b044b23e18"
assert hashlib.sha256((D/"prepare.py").read_bytes()).hexdigest()==PIN
spec=importlib.util.spec_from_file_location("long1722_finalize_source",D/"prepare.py")
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
protected=a.guard_protected()
index=json.loads((D/"plan_index.json").read_bytes())
manifest_index=json.loads((D/"manifest_index.json").read_bytes())
readmap={}
for name in ("manifest_evidence.json","plan_read_evidence.json"):
    v=json.loads((D/name).read_bytes())
    for rel,h in v["read_evidence_sha256"].items():
        if rel in readmap and readmap[rel]!=h: raise ValueError("read map conflict")
        readmap[rel]=h
publication="results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_manifest_publication.json"
if a.sha(R/publication)!="a016d94f02f95c56aed8dcace698995770610e68041ec8f48eaa3d8ffbeb75c3":
    raise ValueError("root publication pin")
readmap[publication]=a.sha(R/publication)
for rel,h in readmap.items():
    if a.sha(R/rel)!=h: raise ValueError("final read evidence drift: "+rel)
inventory=json.loads((R/a.INVENTORY).read_bytes());S=Path(inventory["source_root_server"])
projection={}
for shard in index["plans"]:
    plan=json.loads((R/shard["scientific_plan"]["path"]).read_bytes())
    a.validate_fresh_plan(plan,shard)
    watches=plan["invocation"]["watched_files"]
    full=dict(watches)
    for rel,h in plan["publish_files"].items():
        target=str(a.P/rel)
        if target in full and full[target]!=h: raise ValueError("publish/watch mismatch")
        full[target]=h
    for dest,h in full.items():
        dp=Path(dest)
        if S in dp.parents:
            rel=dp.relative_to(S).as_posix()
            if inventory["files"].get(rel)!=h: raise ValueError("unregistered snapshot alias")
            role="source_snapshot"
        elif a.P in dp.parents:
            rel=dp.relative_to(a.P).as_posix();role="runtime_input"
        else: raise ValueError("unrecognized server target")
        local=R/rel
        if a.sha(local)!=h: raise ValueError("runtime source bytes")
        v=dict(local_path=rel,server_path=dest,sha256=h,bytes=local.stat().st_size,role=role)
        if dest in projection and projection[dest]!=v: raise ValueError("cross-plan server map conflict")
        projection[dest]=v
projection_ref=a.write("runtime_science_input_projection.json",dict(schema="formal_main_v2",
    kind="original_scientific_plan_runtime_input_projection",status="science_inputs_only_outer_runtime_pending",
    files=[projection[k] for k in sorted(projection)],
    history_evidence_is_not_automatically_runtime_required=True,checkpoint_data_included=False,
    final_values_included=False,new_action_runtime_readiness_included=False))
xml=ET.parse(D/"tests_a1.xml").getroot()
suites=xml.findall("testsuite") if xml.tag!="testsuite" else [xml]
counts={k:sum(int(x.get(k,0)) for x in suites) for k in ("tests","failures","errors","skipped")}
if counts!={"tests":31,"failures":0,"errors":0,"skipped":0}: raise ValueError("author test result")
for name,expected in [("prepare.py",PIN),("test_candidate.py","620373cd8edcd4d738ba0f8976b2366ffbd73b7fb43e6de86a901297d52ce7aa"),
 ("run_tests.py","c7640314859dc2eb0667594f3159978c753189e78955783e831f15f32ebc51a7")]:
    if a.sha(D/name)!=expected: raise ValueError("author source drift")
transport_names=["long16_manifests_1722_a2.jsonl","long16_plans_1722_a1.jsonl","long16_tests_1722_a1.jsonl"]
for name in transport_names:
    p=R/"results/formal_main_v2/control_transport"/name
    events=[json.loads(l) for l in p.read_text().splitlines()]
    if (events[0]["event"]!="control_start" or events[-1]["event"]!="control_end"
            or events[-1]["returncode"]!=0 or not events[-1]["source173_and_entrypoint_unchanged"]):
        raise ValueError("transport evidence failed")
    readmap[p.relative_to(R).as_posix()]=a.sha(p)
files={}
for p in sorted(D.rglob("*")):
    if not p.is_file() or any(part.startswith(("pytest_temp",".pytest_cache","__pycache__")) for part in p.relative_to(D).parts): continue
    if p.name in ("candidate_review.json","delivery_files.json"): continue
    files[p.relative_to(R).as_posix()]=a.sha(p)
pivot=R/".local/spatial_resume_1722/direction_change.json"
files[pivot.relative_to(R).as_posix()]=a.sha(pivot)
if protected!=a.guard_protected(): raise ValueError("protected files changed")
report=dict(schema="formal_main_v2",kind="long16_development_plan_author_CPU_review",
    status="passed_scientific_plan_preparation_only",review_role="author_not_independent",
    source={"path":a.BUILDER,"sha256":a.BUILDER_SHA},planner={"path":a.PLANNER,"sha256":a.PLANNER_SHA},
    original_code_modified=False,read_evidence_mapping_used=False,all_registry_rows=index["full_registry_rows"],
    registry_filtered=False,state_written=False,original_pure_plans_passed=8,
    plan_index={"path":str((D/"plan_index.json").relative_to(R)),"sha256":a.sha(D/"plan_index.json")},
    manifest_index={"path":str((D/"manifest_index.json").relative_to(R)),"sha256":a.sha(D/"manifest_index.json")},
    author_tests=counts,actual_plan_seconds=45.38258964847773,actual_manifest_seconds=40.442800167016685,
    author_pytest_seconds=float(suites[0].get("time")),
    original_development_trials_retained=600,original_development_GPU_seconds_retained=10531,
    prior_action_identity_not_reused_as_new=True,methods=16,engineering_shards=8,planned_trials_per_shard=200,
    planned_trials_total=1600,common_unique_development_initial_states=100,all22_identity_coverage_only=True,
    old_six_new_execution_status="HOLD_SEPARATE_REGISTRATION_REQUIRED",
    projection=projection_ref,scientific_hold_not_released=True,submission_authorized=False,
    new_GPU_allocations=0,new_trials=0,weights_read=False,sealed_values_read=False,Git_changed=False,
    preparation_failures=[dict(attempt="manifests_a1",cause="transport rejected private audit path before entrypoint",
       original_log=".local/long_development_1722/manifests_a1.log",new_GPU_allocations=0)],
    limitations=["Only science manifest and original pure plan stage completed.",
      "No effective action-runtime plan/readiness/prepared invocation/submission authorization generated.",
      "Root must build/review exact action outer contracts and publish full runtime dependency closure.",
      "Root must refresh live registry, capacity/reservation and checkpoint identities before any submission.",
      "Old600 cost is measured history, not a guarantee for future4h shards.",
      "No global release, final/O2A evidence, success result or speed inference."],
    protected_files_sha256=protected,read_evidence_sha256=readmap,author_artifacts_sha256=files)
ref=a.write("candidate_review.json",report)
delivery=[]
for p in sorted(D.rglob("*")):
    if not p.is_file() or any(part.startswith(("pytest_temp",".pytest_cache","__pycache__")) for part in p.relative_to(D).parts): continue
    if p.name=="delivery_files.json": continue
    delivery.append(dict(path=p.relative_to(R).as_posix(),sha256=a.sha(p),bytes=p.stat().st_size))
delivery.append(dict(path=pivot.relative_to(R).as_posix(),sha256=a.sha(pivot),bytes=pivot.stat().st_size))
for name in transport_names:
    p=R/"results/formal_main_v2/control_transport"/name
    delivery.append(dict(path=p.relative_to(R).as_posix(),sha256=a.sha(p),bytes=p.stat().st_size))
dr=a.write("delivery_files.json",dict(schema="formal_main_v2",kind="long16_preparation_exact_archive_files",
    files=delivery,excluded="rebuildable pytest cache/temp only; nothing deleted"))
print(json.dumps(dict(author_review=ref,delivery=dr,root_science_refs=len(readmap),runtime_science_inputs=len(projection))))
