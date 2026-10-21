"""Bounded exact-source static follow-up; none of the reviewed programs are executed."""
from pathlib import Path
import ast,difflib,hashlib,json
D=Path(__file__).parent;R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
pins={
'.local/final_snapshot_20261021T0110_v1.py':'49cc46f515e495005a661059d091aa2b5ae4d8432689d4da470c5efa56c44d70',
'.local/final_snapshot_20261021T0110_v2.py':'cfe25974a9b7ba9c53cda1eda4464fc8a5b3c190bdc4015a24e468bfedb11320',
'.local/deliver_20261021T0110_v1.py':'d9c592c4985b8b8c00677705fdaa084bc1a0b17ed5df2a77b97f1c73efa41282',
'.local/deliver_20261021T0110_v2.py':'c57fc34115730edff15eb029fa572e4a0142ebf41ea627476e476fda15eec354',
'.local/deliver_20261021T0110_v3.py':'b7fe5efe56f9d763e23163db0fa1d037aeac09fe24d688a97eefaaedf0dab790',
'.local/deliver_20261021T0110_v4.py':'4c5380c823ecbcfd4b4e9fd0e3080fceecf7d4c9e22e99deb9555c6c02885e45',
'.local/archive_packages_20261021T0110_v4.py':'3effbbdcb614144e07f9bc9a1c99fba43aa0376d6ddd839c14264bbbfeb5ff56',
'.local/archive_packages_20261021T0110_v5.py':'6d4c584f958158785d5b98b7ab50f475f47be32e792bb3fa33dd3ec7c62b755a',
'.local/archive_packages_20261021T0110_v6.py':'04f38c99941b109b71530ec30ae5ea30db6db16b5cad965fc7e7ffd893e1a67d'}
sources={};checks=[]
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)));assert v,n
for n,h in pins.items():
 raw=(R/n).read_bytes();ck('sha/'+n,hashlib.sha256(raw).hexdigest()==h);ast.parse(raw);sources[n]=raw.decode()
def s(n):return sources['.local/'+n+'_20261021T0110_v'+str(versions[n])+'.py']
a=sources['.local/final_snapshot_20261021T0110_v1.py'];b=sources['.local/final_snapshot_20261021T0110_v2.py']
ck('only_science_HOLD_line',b==a.replace('summary["Goal_original200_and_new_science_HOLD"]=g.get("job_id") is None','summary["Goal_original200_and_new_science_HOLD"]=True'))
v4=sources['.local/deliver_20261021T0110_v4.py'];v1=sources['.local/deliver_20261021T0110_v1.py']
for marker in ["with c.exclusive_lock","git('diff','--cached','--name-only').stdout==b''","audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')","frozen_files_verified_in_worktree_and_index']==173","no_glob_add_of_ignored_outputs","--cached','--check","prospective_Goal_raw_runtime_scope_deferred_to_exact_terminal_archive"]:
 ck('protected_guard/'+marker,marker in v1 and marker in v4)
ck('Git_no_live_scheduler',not any(x in v4 for x in ["'sbatch'","'scontrol'","'squeue'","'sacct'"]))
ck('latest_manifest_bounded_path',all(x in v4 for x in ["m.get('source_root',str((R/original['path']).parent))","assert '..' not in declared.parts","declared.resolve()==declared and declared.is_relative_to(R/parent)","if 'copied_files' in receipt","assert sorted((x['path'],x['sha256'],x['bytes']) for x in receipt['copied_files'])"]))
av6=sources['.local/archive_packages_20261021T0110_v6.py']
ck('archive_only_exact_owned_source',all(x in av6 for x in ["m.get('source_root',str(p.parent))","assert '..' not in declared.parts","declared=safe(declared if declared.is_absolute() else R/declared)","declared.is_relative_to(R/root)","src.stat().st_size==row['bytes'] and h(src)==row['sha256']","with q.open('xb')","assert not raws","not_runtime_admission=True"]))
diffs={}
for prefix,versions in [('deliver',[1,2,3,4]),('archive_packages',[4,5,6])]:
 for old,new in zip(versions,versions[1:]):
  n1=f'.local/{prefix}_20261021T0110_v{old}.py';n2=f'.local/{prefix}_20261021T0110_v{new}.py'
  diffs[n2]=''.join(difflib.unified_diff(sources[n1].splitlines(True),sources[n2].splitlines(True),fromfile=n1,tofile=n2))
r=dict(schema='formal_main_v2',status='passed_bounded_static_update_review',reviewed_by='independent',scope='Manual exact-diff static review plus SHA/AST/guard checks; reviewed root programs not executed; final actual state review still required.',blockers=[],source_pins=pins,checks=list(checks),reviewed_diffs=diffs,findings=['Snapshot v2 preserves Goal old200/new science HOLD independent of engineering job allocation.','Git v2-v4 changes only precise manifest-member root handling, exact archive implementation pin, copied-file mapping, and preservation of its own prior source versions.','Archive v5/v6 resolves an absent root from manifest parent and accepts explicit absolute/server-project-relative roots only inside the previously allowed owner root; exact manifest/file identities remain required.','Root source/CPU candidate archives do not imply runtime or scientific admission.'],new_live_Slurm_queries=0,new_GPU_submissions=0,state_writes=0,Git_operations=0,P_writes=0,future_Git_or_actual_snapshot_verified=False)
out=D/'static_update_review.json'
with out.open('x') as f:json.dump(r,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status=r['status'],checks=len(checks),sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
