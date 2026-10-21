"""Bounded Git v5 static-only correction; prior final delivery package is unchanged."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
checks=[];refs={}
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)));assert v,n
def raw(n,h):
 b=(R/n).read_bytes();ck('sha/'+n,hashlib.sha256(b).hexdigest()==h);refs[n]=dict(sha256=h,bytes=len(b));return b
v4=raw('.local/deliver_20261021T0110_v4.py','4c5380c823ecbcfd4b4e9fd0e3080fceecf7d4c9e22e99deb9555c6c02885e45').decode()
v5=raw('.local/deliver_20261021T0110_v5.py','a46e639d89543aa2c943d6d404e60b7dfcd4cf064da8c1ac0ac792a20313335f').decode()
ast.parse(v5)
start=v5.index(" pknown='results/formal_main_v2/pulls/20261021T013702Z_1056842ddda1/receipt.json'")
stop=v5.index(' opened=[];closed=[];sources=[]',start)
block=v5[start:stop]
normal=v5[:start]+v5[stop:]
normal=normal.replace("'.local/deliver_20261021T0110_v5.py',",'').replace("root_operation_sources_v2.json","root_operation_sources_v1.json")
ck('entire_remaining_v5_exactly_v4',normal==v4)
ck('same_exact_pull_pin_and_acceptance_flags',all(s in block for s in ["'ca9d4e64b02abde022ecb6ac83c4653be0c0882485bd0f73478f69570f3e8a60'","known_pull['final_evidence']","not known_pull['weights_copied']","not known_pull['sealed_initial_states_copied']","not known_pull['missing']"]))
ck('each_precise_member_verified_before_known',all(s in block for s in ["for row in known_pull['files']:","assert ref(row['relative'])==dict(path=row['relative'],sha256=row['sha256'],bytes=row['bytes'])","known.add(row['relative'])"]) and block.index('assert ref(')<block.index('known.add('))
ck('no_wildcard_extension_to_known',"known.add(row['relative'])" in block and "glob(" not in block and "rglob(" not in block)
ck('new_failure_receipt_does_not_overwrite_old_source_receipt',"'git_initial_allowlist_failure.json'" in block and "save(B+'/root_operation_sources_v2.json'" in v5 and "def save(n,v):" in v5 and "p.open('x')" in v5)
pull=json.loads(raw('results/formal_main_v2/pulls/20261021T013702Z_1056842ddda1/receipt.json','ca9d4e64b02abde022ecb6ac83c4653be0c0882485bd0f73478f69570f3e8a60'))
ck('exact14_existing_nonweight_evidence',len(pull['files'])==14 and pull['final_evidence'] and not pull['weights_copied'] and not pull['sealed_initial_states_copied'] and not pull['missing'])
paths=[]
for row in pull['files']:
 n=row['relative'];b=raw(n,row['sha256']);ck('pull_bytes/'+n,len(b)==row['bytes']);paths.append(n)
ck('three_previously_unknown_members_are_same_pull_members',set(['results/formal_main_v2/job_receipts/3054201.json','results/slurm/cti-formal-downstream_3054201.err','results/slurm/cti-formal-downstream_3054201.out'])<=set(paths))
raw('results/experiment_supervisor/state.json','bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa')
raw('results/formal_main_v2/preflight/heartbeat_20261021T0910/final_summary.json','6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2')
original=json.loads(raw('.local/delivery_independent_20261021T0110/delivery_manifest.json','78b8538489ffa542b5e0f8d36ab3764d563f6f2e11744d129a9b57d6dd04a890'))
review=json.loads(raw('.local/delivery_independent_20261021T0110/actual_review_v2.json','69434136678f7ce1549de4e5b10c37d5272276263ab75e9ba06effb3debe7d8a'))
ck('prior_actual_final_review_inherited_not_reexecuted',original['file_count']==12 and review['status']=='passed_final_delivery_review' and review['blockers']==[] and review['state_sha256']=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa')
report=dict(schema='formal_main_v2',kind='bounded_git_allowlist_correction_independent_review',status='passed_bounded_git_allowlist_review',reviewed_by='independent',blockers=[],scope='Only exact v4-to-v5 source delta and the same 14 already-reviewed Spatial pull member hashes; prior 3146-item final audit inherited unchanged. Git helper is not executed by this audit.',checks=list(checks),state_sha256=review['state_sha256'],final_summary_sha256='6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2',prior_final_review=dict(path='.local/delivery_independent_20261021T0110/actual_review_v2.json',sha256='69434136678f7ce1549de4e5b10c37d5272276263ab75e9ba06effb3debe7d8a'),source173_verification_inherited=True,final_sealed=True,exact14_nonweight_allowlist=paths,source_diff=''.join(difflib.unified_diff(v4.splitlines(True),v5.splitlines(True))),current_Git_index_independently_queried=False,empty_index_still_required_by_unchanged_guard=True,Git_operations=0,new_live_Slurm_queries=0,new_GPU_submissions=0,state_writes=0,P_writes=0,future_commit_or_push_verified=False,refs=refs)
out=D/'independent_review.json'
with out.open('x') as f:json.dump(report,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
files=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(D.iterdir()) if p.is_file()]
manifest=dict(schema='formal_main_v2',kind='bounded_git_allowlist_independent_manifest',status='frozen',source_root=str(D),files=files,file_count=len(files),review=dict(path=out.relative_to(R).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),bytes=out.stat().st_size),prior_12_file_audit_unchanged=True)
m=D/'delivery_manifest.json'
with m.open('x') as f:json.dump(manifest,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
print(json.dumps(dict(status=report['status'],checks=len(checks),review_sha256=manifest['review']['sha256'],manifest_sha256=hashlib.sha256(m.read_bytes()).hexdigest(),file_count=len(files))))
