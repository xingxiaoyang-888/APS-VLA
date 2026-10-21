from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/delivery_integration_recovery_independent_20261021T0334'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
ENTRY='.local/integrate_terminals_20261021T0334_v4.py';PIN='1701253256acaa4483edd754d60b7c887a443396ddf4752f164bc4ec874c5c59'
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,ok):
 if not ok:raise AssertionError(name)
 checks.append(dict(name=name,passed=True))
def save(n,b):
 with (D/n).open('xb') as f:f.write(b)
def js(n,v):save(n,(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def ref(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
source=(R/ENTRY).read_text();ck('exact_v4_source',h(R/ENTRY)==PIN);tree=ast.parse(source);compile(tree,ENTRY,'exec')
pre='.local/delivery_independent_20261021T0334/preintegration_review.json';ck('inherits_exact_prior_351_checks',h(R/pre)=='926ea3d1b8d2c171a218136dda989b00711c504fd2cda9af090c574d2b723cba')
state='results/experiment_supervisor/state.json';STATE='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa';ck('state_has_not_changed',h(R/state)==STATE)
op='.local/object_terminal_independent_20261021T0334';mp=op+'/delivery_manifest.json';ck('exact_Object_original_manifest',h(R/mp)=='dd2266f5c9024e81d785583f1c4931f4086ae0d68f8c710f6659eb8261dcab63');m=json.loads((R/mp).read_bytes())
allowed={E+'/Object_independent/'+r['path'] for r in m['files']}|{E+'/Object_independent/delivery_manifest_original.json',E+'/Object_independent/root_publication_mapping.json'}
ck('exact28_existing_publication_no_extra',len(allowed)==28 and {str(p.relative_to(R)) for p in (R/E/'Object_independent').rglob('*') if p.is_file()}==allowed)
mapping=[]
for row in m['files']:
 old=R/op/row['path'];dest=E+'/Object_independent/'+row['path'];new=R/dest
 ck('original_Object_reuse_exact:'+row['path'],h(old)==h(new)==row['sha256'] and old.stat().st_size==new.stat().st_size==row['bytes'] and old.read_bytes()==new.read_bytes() and new.resolve()==new)
 mapping.append(dict(source=op+'/'+row['path'],**ref(dest)))
ck('original_manifest_copy_exact',(R/E/'Object_independent/delivery_manifest_original.json').read_bytes()==(R/mp).read_bytes())
expected=(json.dumps(dict(original_manifest=ref(mp),files=mapping),sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
ck('original_mapping_rebuild_exact28',(R/E/'Object_independent/root_publication_mapping.json').read_bytes()==expected)
gp='.local/goal_terminal_independent_20261021T0334';gm=gp+'/delivery_manifest.json';gr=gp+'/independent_terminal_review.json'
ck('correct_Goal_manifest_fixed',h(R/gm)=='096f81447dd1cad964568a44f6760b9f1517f67b4ea2fdd86a0728a8506a8be6')
ck('correct_Goal_actual_independent_pass',h(R/gr)=='9f89cee7420fa4c4185370b22a4c52c70cd536048b9bd366d5e70095a044e223')
gv=json.loads((R/gr).read_bytes());gmv=json.loads((R/gm).read_bytes())
ck('Goal_actual_complete_consumer_required',gv['status']=='passed_new200_terminal_independent_review' and not gv['blockers'] and gv['complete_original_scientific_consumer'] and gv['trials']==200 and gv['allocation_gpu_seconds']==2205)
ck('Goal_review_bound_in_manifest',any(Path(row['path']).name=='independent_terminal_review.json' and row['sha256']==h(R/gr) and row['bytes']==(R/gr).stat().st_size for row in gmv['files']))
trace='results/formal_main_v2/control_transport/integrate_terminals_20261021T0334_v3.jsonl';events=[json.loads(x) for x in (R/trace).read_bytes().splitlines()]
wrong='096f81447dd1cad964568a44f6760b9f1517f67b4ea2f2dd86a0728a8506a8be6'
ck('original_rejected_typo_trace_exact',events[-1]['returncode']==1 and events[-1]['source173_and_entrypoint_unchanged'] and events[0]['entrypoint_sha256']=='e4f5de6cc298e5ea927d26b6f25281a089912f96baa4044c9a7ead3c7a8b7e48' and events[0]['command'][events[0]['command'].index('--goal-manifest-sha256')+1]==wrong)
ck('no_scientific_acceptance_from_partial_copy',all(not (R/n).exists() for n in [E+'/Goal_independent',B+'/Object3054409_root_acceptance.json',B+'/Goal3054717_root_acceptance.json',B+'/final_summary.json']))
ck('Goal_pins_checked_before_copy',source.index("rd(gp+'/delivery_manifest.json',a.goal_manifest_sha256)")<source.index('with ctl.exclusive_lock'))
ck('only_exact28_reuse_and_no_replace',all(t in source for t in ["assert n in REUSE_EXACT_OBJECT28 and not p.is_symlink() and p.read_bytes()==b,n","p.open('xb').write(b)","assert len(REUSE_EXACT_OBJECT28)==28","all_other_paths_exclusive_create=True"]))
ck('shared_lock_CAS_and_original_guards_retained',source.count("for n,pin in frozen.items():assert h(R/n)==h(S/n)==pin")==2 and "with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')" in source and "assert (R/STATE).read_bytes()==before" in source and "os.replace(tmp,R/STATE)" in source)
# Test only the exact existing-file branch against an in-memory path object.
# No actual publication/state write function is executed.
func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='write')
class FakePath:
 def __init__(self,name,data,symlink=False):self.name=name;self.data=data;self.symlink=symlink
 def exists(self):return True
 def is_symlink(self):return self.symlink
 def read_bytes(self):return self.data
class FakeRoot:
 def __init__(self,items):self.items=items
 def __truediv__(self,n):return self.items[n]
name=sorted(allowed)[0];items={name:FakePath(name,b'exact'),'unknown':FakePath('unknown',b'exact')}
ns=dict(R=FakeRoot(items),REUSE_EXACT_OBJECT28=allowed,ref=lambda n:dict(path=n))
exec(compile(ast.Module(body=[func],type_ignores=[]),'<independent-memory-write-branch>','exec'),ns)
ck('memory_same_bytes_exact_allowed_reused',ns['write'](name,b'exact')==dict(path=name))
rejects=[]
for label,target,data,sym in [('different_bytes',name,b'changed',False),('unlisted_path','unknown',b'exact',False),('symlink',name,b'exact',True)]:
 items[target].symlink=sym
 try:ns['write'](target,data)
 except AssertionError:rejects.append(label)
 else:raise AssertionError('write branch accepted '+label)
 items[target].symlink=False
ck('memory_three_reuse_rejections',rejects==['different_bytes','unlisted_path','symlink'])
ck('state_unchanged_after_review',h(R/state)==STATE)
report=dict(schema='formal_main_v2',kind='root_integration_exact28_partial_publication_recovery_review',status='passed_bounded_exact28_recovery',reviewed_by='independent',blockers=[],entrypoint=ENTRY,entrypoint_sha256=PIN,prior_preintegration_review=ref(pre),scope='Only v3 wrong manifest argument refusal, exact28 Object publication reuse and v4 fixed Goal precheck. Previous351 source/design checks inherited; not repeated scientific consumer or final state/Git review.',state_before_sha256=STATE,original_failure_trace=ref(trace),original_rejected_argument=wrong,correct_Goal_manifest=ref(gm),actual_Goal_independent_report=ref(gr),exact_reuse_files=[ref(n) for n in sorted(allowed)],all_other_outputs_exclusive_create=True,actual_integration_not_executed_by_this_agent=True,required_next='Root may execute exact v4 with fixed correct pins; independent actual final state/docs/Git review still required.',memory_reuse_branch_rejections=rejects,new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,canonical_writes=False,Git_writes=False,final_release=False,check_count=len(checks),checks=checks,utc=datetime.now(timezone.utc).isoformat())
js('recovery_review.json',report);save('reviewed_integrate_v4.py',(R/ENTRY).read_bytes());save('original_rejected_v3_transport.jsonl',(R/trace).read_bytes())
files=[dict(path=p.name,sha256=h(p),bytes=p.stat().st_size) for p in sorted(D.iterdir()) if p.is_file()]
manifest=dict(schema='formal_main_v2',kind='exact28_recovery_independent_delivery',status=report['status'],source_root=str(D),file_count=len(files),files=files,review=dict(path='recovery_review.json',sha256=h(D/'recovery_review.json'),bytes=(D/'recovery_review.json').stat().st_size))
js('delivery_manifest.json',manifest)
print(json.dumps(dict(status=report['status'],checks=len(checks),report_sha256=h(D/'recovery_review.json'),manifest_sha256=h(D/'delivery_manifest.json'),file_count=len(files))))
