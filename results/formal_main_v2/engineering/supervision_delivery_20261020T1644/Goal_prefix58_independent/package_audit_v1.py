'Package all private independent audit evidence, retaining original files.'
from pathlib import Path
import hashlib,json,tarfile,gzip,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;t0=time.process_time()
def h(p):
 d=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):d.update(b)
 return d.hexdigest()
def write(rel,x):
 p=D/rel
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
 return {'source':str(p.relative_to(R)),'path':str(p.relative_to(D)),'sha256':h(p),'bytes':p.stat().st_size}
main=D/'attempt02/independent_review.json';metadata=D/'identity_support.json'
assert h(main)=='24398f0dfb160bb2ee1aa3ef5cfada40427798eb867dd56f9d7479e51a8bb604'
assert h(metadata)=='d92a8ee417e79171486625388e59761cae886d7ed25c177ffde252326b1b49ff'
report=json.loads(main.read_text());meta=json.loads(metadata.read_text());failed=json.loads((D/'attempt01/harness_failure.json').read_text())
logs=['goal_prefix58_independent_cpu_v1_20261020T1644.jsonl','goal_prefix58_independent_cpu_v2_20261020T1644.jsonl','goal_prefix58_independent_metadata_v1_20261020T1644.jsonl']
(D/'transport').mkdir(exist_ok=False);logrefs=[]
for name in logs:
 src=R/'results/formal_main_v2/control_transport'/name;dst=D/'transport'/name;raw=src.read_bytes()
 with dst.open('xb') as f:f.write(raw)
 assert h(src)==h(dst)
 logrefs.append({'original_source':str(src.relative_to(R)),'source':str(dst.relative_to(R)),'path':str(dst.relative_to(D)),'sha256':h(dst),'bytes':len(raw)})
write('transport_audits.json',{'bundle_manifest_sha256':'3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149','exact_completed_audits':logrefs})
blobs=sorted(p for p in D.rglob('*') if p.is_file() and p.parent.name=='blobs')
assert len(blobs)==460 and all(p.suffix in ('.bin','.json') and p.resolve().is_relative_to(D) and not p.is_symlink() for p in blobs)
members=[{'source':str(p.relative_to(R)),'path':str(p.relative_to(D)),'sha256':h(p),'bytes':p.stat().st_size,'kind':'synthetic_CPU_array_or_RNG_blob_nonweight_nonsealed'} for p in blobs]
arc=D/'synthetic_blobs_lossless.tar.gz'
with arc.open('xb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w') as tar:
   for p,row in zip(blobs,members):
    info=tarfile.TarInfo(row['path']);info.size=row['bytes'];info.mode=0o644;info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
    with p.open('rb') as f:tar.addfile(info,f)
verified=[]
with tarfile.open(arc,'r:gz') as tar:
 actual=tar.getmembers();assert [x.name for x in actual]==[r['path'] for r in members]
 for member,row in zip(actual,members):
  assert member.isfile() and not member.issym() and not member.islnk() and not member.name.startswith('/') and '..' not in Path(member.name).parts
  digest=hashlib.sha256();n=0
  with tar.extractfile(member) as f:
   for b in iter(lambda:f.read(1<<20),b''):digest.update(b);n+=len(b)
  assert n==row['bytes']==member.size and digest.hexdigest()==row['sha256'];verified.append(row['path'])
assert arc.stat().st_size<100*1024*1024
archive_ref={'source':str(arc.relative_to(R)),'path':arc.name,'sha256':h(arc),'bytes':arc.stat().st_size}
write('synthetic_blobs_member_manifest.json',{'archive':archive_ref,'member_count':len(members),'total_original_bytes':sum(r['bytes'] for r in members),'members':members,'each_member_stream_verified':True,'originals_retained':True,'contains_real_observation_or_weights':False})
readme='''# Goal prefix58 independent CPU audit

Status: completed with findings; not GPU ready. No Slurm/GPU or scientific trial was run. Original Goal 200 and all new Goal scientific development remain HOLD.

The candidate manifest `9a2f425a...` and all 192 original members were verified without modification. The auditor ran the real pinned accepted `run_episode` and original formal trial loop only against independently written synthetic CPU env/policy fixtures. Exact first58 identities from the original start/result ledger, 29 development states, A/B order, metadata checkpoint identities, and original preceding56 totals of 916 queries/7124 policy controls were checked. The original 173 R/S frozen files are unchanged. This does not rehash checkpoint tensors or run inference.

`attempt02/independent_review.json`: 403 assertions and 17 rejecting negative cases, including preservation of reset/step/query/action order, noncontiguous observation bytes, RNG, binding restoration and fail-stop after a policy exception. `identity_support.json`: 156 metadata assertions. Some assertions intentionally confirm the following counterexamples; the count does not mean an unqualified safety pass.

Findings requiring a bounded new revision before real engineering execution:

1. `G58-AST-01`: inverse AST projection removes observer calls without inspecting argument side effects. An inserted `env.step(...)` or RNG call inside an observer argument survives execution semantics but is stripped from the proof. The actual current derived hooks were independently checked and have no nested call arguments. Minimal fix: exact versioned hook/count/order/argument whitelist before projection, with both new negative cases.
2. `G58-GUARD-02`: final journal writing is followed by object/global-RNG checks but no simulator/environment-RNG recheck. A fake journal writer changed a fake qpos while the event still claimed simulator invariance. This is a coverage counterexample, not evidence that normal OS writes mutate MuJoCo or cause the original anomaly. Minimal fix: compare passive environment after the final write too, and retain failure evidence.
3. `G58-FAILSTOP-03`: initial RNG/object/simulator guard acquisition is outside the fail-stop try block. A synthetic existing-generator read error left no failed latch/journal, and an explicit same-instance CPU retry was accepted. No real automatic retry happened. Minimal fix: include initial acquisition in the fail-stop boundary and test initial-reader failures.

The native MuJoCo and real CUDA generator branches have not been accepted on GPU by this audit. CPU fixtures and synthetic outcomes are excluded from all scientific denominators. Snapshot copying and I/O change elapsed time; the package is not a latency benchmark, a proof of full simulator hidden state identity, or an explanation of the original t0 mismatch. Original query/episode timers retain their code placement, but their numerical timings are not expected equal.

A real single-attempt original-chain outer entry is still missing. `prepare --execute` rejects before source reads or output writes. After the bounded observer revision and independent negatives, root must separately review any original loader/action-context runner, exact sources/checkpoint metadata, development-only prefix and hard <=30 min/one-GPU/eight-slot admission. Do not auto-run, force original actions, accept original200, or clear scientific HOLD. Non-reproduction remains inconclusive.

All failures and outputs are retained. `attempt01/harness_failure.json` was an auditor variable-shadowing error at the final inventory check, not a candidate failure; immutable `independent_cpu_v2.py` corrects that in a fresh attempt02. Its CPU cost is included. A source-bootstrap quoting SyntaxError is separately retained in `package_bootstrap_failure_01.json`.

All 460 tiny raw synthetic CPU array/RNG blobs remain in their original private paths. `synthetic_blobs_lossless.tar.gz` is a lossless optional Git delivery representation with member SHA/length verification. It contains no actual LIBERO observation arrays, weights, or sealed values. Root may publish the archive plus member manifest instead of 460 tiny files without losing evidence. The full delivery manifest still enumerates all originals.
'''
with (D/'README.md').open('x',encoding='utf-8') as f:f.write(readme)
summary={'schema':'formal_main_v2','kind':'independent_goal_prefix58_audit_handoff','status':'completed_with_findings_not_GPU_ready','candidate_manifest':report['candidate_manifest'],'core_report':{'source':str(main.relative_to(R)),'sha256':h(main)},'identity_report':{'source':str(metadata.relative_to(R)),'sha256':h(metadata)},'independent_assertions':report['passed_check_count']+meta['passed_check_count'],'rejecting_negative_cases':report['negative_case_count'],'findings':report['findings'],'test_CPU_seconds_including_failed_harness':failed['CPU_seconds']+report['CPU_seconds']+meta['CPU_seconds'],'failed_harness_retained':True,'new_GPU_seconds':0,'new_Slurm_jobs':0,'scientific_trials_added':0,'Goal_original_200_HOLD_unchanged':True,'all_new_Goal_science_HOLD_unchanged':True,'source_173_unchanged':True,'real_GPU_outer_entry_implemented':False,'real_GPU_acceptance':False,'synthetic_blobs_archive':archive_ref,'packaging_CPU_seconds':time.process_time()-t0,'next_action':'Root review findings; author a narrowly versioned correction and independently recheck before considering any separately reviewed one-attempt engineering GPU runner. No automatic execution.'}
ref=write('handoff_summary.json',summary);print(json.dumps({'handoff':ref,'synthetic_blob_archive':archive_ref,'CPU_seconds_including_failed_harness':summary['test_CPU_seconds_including_failed_harness'],'findings':[x['id'] for x in report['findings']]}))
