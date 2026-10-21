from pathlib import Path
import ast,collections,hashlib,importlib.util,json,os,subprocess,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
B='results/formal_main_v2/preflight/heartbeat_20261021T1134';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
V3='.local/stage_delivery_20261021T0334_v3.py';V4='.local/stage_delivery_20261021T0334_v4.py'
PINS={V3:'39eb510bf1bd023efc817e9936074e6c81f6833480463ffe20fdff039abffc51',V4:'4b05a503efab9e57bc8e8b5747dc12fa3474a4d14aade6e8dd61c3a1d52db048','scripts/ops/check_nonweight_archive_stage.py':'ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','results/formal_main_v2/pulls/terminal_goal_20261021T0334/receipt.json':'06fb8a97f8c48aa24aa041b8d34e3f41c53320f08bbd0f136b53ccfa5e85d738','results/formal_main_v2/pulls/terminal_object_20261021T0334/receipt.json':'1ab834c09cc562f4fce9224bf98bc6c80d31dbaadcb6a3381c877c1395aad710',E+'/Goal_archive/archive_manifest.json':'18c61e6a89047e7c4a0cdab7e6111f73a36db0421a3c2b1627a2f01944cf4d21',B+'/Goal_archive_root_verification.json':'c2af89ef9fccc868adc380876546f6e4044b8632cf14e267ea1e3116bd515630'}
N=0;projection={};seen_projection={};source_refs={}
def h(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def yes(v,m):
 global N;N+=1
 if not v:raise AssertionError(m)
def read(n):return json.loads((R/n).read_bytes())
def ref(n):return {'path':n,'sha256':h(R/n),'bytes':(R/n).stat().st_size}
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def git(*args):
 yes(args[0] in ['rev-parse','diff','check-ignore'],'only allowed read-only Git command')
 env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0'
 return subprocess.run(['git','-c','core.quotepath=false','-C',str(R),*args],capture_output=True,env=env)
def main():
 for n,pin in PINS.items():yes(h(R/n)==pin,'source/evidence pin '+n)
 index_before=h(R/'.git/index');state_before=h(R/'results/experiment_supervisor/state.json')
 yes(git('rev-parse','HEAD').stdout.decode().strip()=='328e3b918379a985ef299cee4891138a55874827','exact expected HEAD')
 z=git('diff','--cached','--name-only');yes(z.returncode==0 and z.stdout==b'','no prior staged changes')
 gp=R/'scripts/ops/check_nonweight_archive_stage.py';sp=importlib.util.spec_from_file_location('ind_readonly_lexical',gp);guard=importlib.util.module_from_spec(sp);sp.loader.exec_module(guard)
 v3=(R/V3).read_text();v4=(R/V4).read_text();tree=ast.parse(v4)
 yes("volumes=manifest['parts']" in v4 and "manifest['volumes']" not in v4,'actual parts interface')
 yes("s['compatible_development_trials']==7800" in v4 and "s['current_action_development_trials']==6589" in v4 and "s['final_sealed']" in v4 and "not s['new_GPU_jobs']" in v4,'scientific root snapshot gates remain')
 yes("with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')" in v4 and "h(R/STATE)==a.state_sha256" in v4 and "q['state_after']==ref(STATE)" in v4,'writer lock CAS/root receipt guards remain')
 yes("guard.check(R,SNAP,SSHA,raw,required)" in v4 and "checked['frozen_files_verified_in_worktree_and_index']==173" in v4,'original staged index173 guard remains')
 yes("required=B+'/git_required_files_v1.json';rows=[ref(n) for n in sorted(selected)]" in v4 and "sorted(selected|{required})" in v4,'required generated after rows and not self-referencing')
 yes("git('show',':'+n).stdout==(R/n).read_bytes()" in v4 and "['-f'] if n in ignored_set else []" in v4,'exact byte index proof and explicit ignored set')
 yes("'/raw_runtime/' not in n and '/observer/blobs/' not in n" in v4,'allmode loose observation exclusion explicit')
 git_calls=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='git' and node.args and isinstance(node.args[0],ast.Constant):git_calls.append(node.args[0].value)
 yes(set(git_calls)<=set(['rev-parse','diff','check-ignore','add','show']),'no stage-helper commit/push/reset/remove')
 for base in [B,E]:
  for p in (R/base).rglob('*'):
   if p.is_file():
    n=p.relative_to(R).as_posix();yes(not p.is_symlink() and p.resolve()==p,'no symbolic link '+n);projection[n]=ref(n)
 def package(private,pin,dest):
  mp=private+'/delivery_manifest.json';yes(h(R/mp)==pin,'package pin '+mp);v=read(mp);seen=set();rows=[]
  yes(len(v['files'])==v['file_count'],'declared package member count '+private)
  for x in v['files']:
   n=x['path'];n=Path(n).relative_to(private).as_posix() if n.startswith(private+'/') else n
   yes(not Path(n).is_absolute() and '..' not in Path(n).parts and n not in seen,'canonical unique package path');seen.add(n)
   src=private+'/'+n;yes(ref(src)==dict(path=src,sha256=x['sha256'],bytes=x['bytes']),'exact package source '+src)
   dst=dest+'/'+n;yes(not (R/dst).exists() and dst not in projection,'package destination is new '+dst);projection[dst]=dict(path=dst,sha256=x['sha256'],bytes=x['bytes']);rows.append(dst)
  for dst in [dest+'/delivery_manifest_original.json',dest+'/root_publication_mapping.json']:
   yes(not (R/dst).exists() and dst not in projection,'new generated package metadata '+dst)
   projection[dst]=dict(path=dst,sha256=h(R/mp) if dst.endswith('delivery_manifest_original.json') else None,bytes=(R/mp).stat().st_size if dst.endswith('delivery_manifest_original.json') else None)
  source_refs[mp]=ref(mp)
  return rows
 package('.local/delivery_independent_20261021T0334','c1f2188cd78c7446d0737dd4e20bc084b7be9559eaa3c0bbd18e9b1727b2088c',E+'/Delivery_preintegration')
 package('.local/delivery_integration_recovery_independent_20261021T0334','c28086db779650754129a63d9f5e2343dc1e7e2781478f55ab284164d4a9b4fe',E+'/Delivery_publication_recovery')
 package('.local/goal_remaining5_design_20261021T0334','83b17715c073995fb0ca87efd1151e7bf9b6438ffe2f2a135478d9a12ff93ea3',E+'/Goal_remaining5_design')
 for node in ast.walk(tree):
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in node.targets):
   yes(isinstance(node.value,ast.List),'root source names literal list');names=[]
   for x in node.value.elts:
    if isinstance(x,ast.Constant):names.append(x.value)
    else:yes(ast.unparse(x)=='Path(__file__).name','only dynamic current script name');names.append(Path(V4).name)
 for n in names:
  src='.local/'+n;dst=B+'/root_operations/'+n;yes((R/src).is_file() and not (R/dst).exists() and dst not in projection,'exact root operation source/destination '+n);z=ref(src);projection[dst]=dict(path=dst,sha256=z['sha256'],bytes=z['bytes'])
 for n in ['results/experiment_supervisor/state.json','scripts/ops/formal_object_terminal_pull_bridge_v1/bridge.py','docs/正式下游阻塞登记_20261021T0334.md','docs/正式主实验规划.md','docs/完整实验计划.md','docs/实验进度.md','docs/正式主实验阶段结论.md','docs/正式非Long开发结果.md','docs/正式Goal主预算开发结果.md']:projection[n]=ref(n)
 pulls=['results/formal_main_v2/pulls/terminal_object_20261021T0334/receipt.json','results/formal_main_v2/pulls/terminal_goal_20261021T0334/receipt.json'];selected_pull=[];excluded=[];v3_selected=[];v3_excluded=[]
 for n in pulls:
  projection[n]=ref(n);v=read(n)
  for x in v['files']:
   rel=x['relative'];yes(str(R/rel)==x['local_path'],'true pull destination')
   if rel.endswith('.bin'):v3_excluded.append(rel)
   else:v3_selected.append(rel)
   if '/attempt01/observer/blobs/' in rel:
    yes(n==pulls[1] and (rel.endswith('.bin') or rel.endswith('.rng.json')),'exact Goal passive namespace and type');excluded.append(rel);continue
   yes(ref(rel)==dict(path=rel,sha256=x['sha256'],bytes=x['bytes']),'exact pulled metadata bytes '+rel);projection[rel]=ref(rel);selected_pull.append(rel)
 yes(len(selected_pull)==26 and len(excluded)==15522,'v4 actual receipt count')
 yes(len(v3_selected)==33 and len(v3_excluded)==15515,'v3 concrete blocker reproduced without mutations')
 yes(sum(n.endswith('.bin') for n in excluded)==15515 and sum(n.endswith('.rng.json') for n in excluded)==7,'both passive payload types retained in archive but excluded loose')
 yes(set(selected_pull).isdisjoint(excluded) and len(selected_pull)==len(set(selected_pull)) and len(excluded)==len(set(excluded)),'pull projection unique disjoint')
 pending_traces=[];complete_traces=[]
 for p in sorted((R/'results/formal_main_v2/control_transport').glob('*20261021T0334*.jsonl')):
  ev=[json.loads(x) for x in p.read_bytes().splitlines()];yes(bool(ev) and ev[0]['event']=='control_start','transport start structure')
  n=p.relative_to(R).as_posix()
  if ev[-1]['event']!='control_end':pending_traces.append(n);continue
  projection[n]=ref(n);complete_traces.append(n)
 manifest=read(E+'/Goal_archive/archive_manifest.json');yes(len(manifest['parts'])==24 and manifest['volume_count']==24,'actual24 parts')
 real_volumes=[]
 for x in manifest['parts']:
  n=E+'/Goal_archive/'+x['path'];z=ref(n);yes(z['sha256']==x['sha256'] and z['bytes']==x['bytes'] and z['bytes']<90*(1<<20),'real part exact bytes '+n);yes(n in projection,'realpart included');real_volumes.append(n)
 fixtures=[n for n in sorted(projection) if '/Goal_archive/verifier_fixtures/' in n];yes(len(fixtures)==9 and all(n.endswith('.tar.gz') for n in fixtures),'only9explicit malformed/valid CPU fixture archives')
 future=[B+'/'+x for x in ['remaining5_design_publication.json','git_external_nonweight_allowlist_v1.json','root_transport_manifest.json','git_ignored_allowlist_v1.json','git_required_files_v1.json','git_index_guard_v1.json','git_whitespace_diagnostic_v1.json']]
 for n in future:
  yes(not (R/n).exists(),'generated file fresh '+n);projection[n]={'path':n,'sha256':None,'bytes':None}
 yes(len({n.casefold() for n in projection})==len(projection),'candidate files casefold unique')
 for n,x in projection.items():
  guard.lexical(n);yes('/raw_runtime/' not in n and '/observer/blobs/' not in n,'loose payload excluded '+n)
  if x['bytes'] is not None:yes(0<=x['bytes']<100*(1<<20),'Git bounded file size '+n)
  if n.endswith('.tar.gz'):yes(n in set(real_volumes+fixtures),'onlyexact33knownarchivefiles')
 yes(set(excluded).isdisjoint(projection),'no15522loosepayload leak')
 required=B+'/git_required_files_v1.json';before_required=[n for n in projection if n not in [required,B+'/git_index_guard_v1.json',B+'/git_whitespace_diagnostic_v1.json']]
 yes(required not in before_required and len(before_required)==len(set(before_required)),'required unique and not self-referential')
 ignored=[];notignored=[]
 # One check-ignore invocation is read-only. Paths are existing or the exact future names above.
 z=git('check-ignore','--stdin','-z') if False else None
 env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0'
 z=subprocess.run(['git','-C',str(R),'check-ignore','--stdin','-z'],input=b'\0'.join(n.encode() for n in sorted(projection))+b'\0',capture_output=True,env=env)
 yes(z.returncode in [0,1],'read-only exact candidate ignore query');ignored=[x.decode() for x in z.stdout.split(b'\0') if x]
 yes(set(ignored)<=set(projection),'ignore results only requested paths')
 for n in [B+'/git_ignored_allowlist_v1.json',required,B+'/git_index_guard_v1.json',B+'/git_whitespace_diagnostic_v1.json']:yes(n not in ignored,'late generated file does not require-force '+n)
 for n in real_volumes+fixtures:yes(n in ignored,'archive ignored but explicitly hashed and forced '+n)
 inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';yes(h(R/inventory)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926','frozeninventorypin');v=read(inventory);yes(len(v['files'])==173,'173inventorycount')
 for n,pin in v['files'].items():yes(h(R/n)==pin,'actualR173source '+n)
 yes(h(R/'.git/index')==index_before,'noGitindexmutation')
 yes(h(R/'results/experiment_supervisor/state.json')==state_before,'no concurrent/own state change during precheck')
 yes(h(R/V4)==PINS[V4] and h(R/V3)==PINS[V3],'candidate sources unchanged')
 write('candidate_paths.json',dict(kind='read_only_future_staging_projection_not_actual_index',files=[projection[n] for n in sorted(projection)],generated_values_to_be_computed_by_root=future,complete_transport_files=complete_traces,pending_transport_files_that_must_finish_before_stage=pending_traces,actual_index_writes=0))
 write('v3_rejected_precheck.json',dict(status='rejected_actual_receipt_shape',entrypoint={'path':V3,'sha256':PINS[V3]},actual_15522_passive=dict(bin=15515,rng_json=7),v3_exact_pulled_would_be=33,v3_excluded_would_be=15515,failing_assertion='len(exact_pulled)==26 and len(loose_blob_exclusions)==15522',additional_guard='seven .rng.json paths also fail later /observer/blobs/ exclusion',stage_was_executed=False))
 report=dict(schema='formal_main_v2',kind='Git_stage_delivery_independent_precheck',status='passed_git_stage_precheck',reviewed_by='independent',reviewed_by_agent='/root/spatial588_recovery_audit_2054',entrypoint={'path':V4,'sha256':PINS[V4]},blockers=[],checks=N,actual_stage_executed=False,Git_index_modified=False,state_modified=False,canonical_or_P_modified=False,Slurm_queries=0,GPU_jobs=0,scientific_consumers_rerun=0,source173_worktree_verified=True,original_stage_guard_pin=PINS['scripts/ops/check_nonweight_archive_stage.py'],original_poststage_index_guard_still_required=True,pulled_metadata_and_logs=26,real_Goal_archives=24,CPU_fixture_archives=9,loose_passive_excluded=15522,loose_passive_types=dict(bin=15515,rng_json=7),R_raw_observations_not_selected=True,casefold_unique=True,required_self_reference=False,ignored_explicit_force_paths=len(ignored),ignored_paths=ignored,late_generated_json_files_not_ignored=True,projected_candidate_path_count=len(projection),future_7800_state_required=True,current_action6589_required=True,final_sealed_required=True,root_state_and_summary_CAS_required=True,new_GPU_jobs_must_equal0=True,required_transport_journal_basename='stage_delivery_20261021T0334_v4.jsonl',pending_transport_files_must_finish_before_staging=pending_traces,scope='Precheck of the exact future candidate paths and actual file interfaces only. Root must execute the pinned stage under the existing writer lock, then run the unchanged index/archive guard; this report is not actual stage acceptance.',preserved_rejected_v3_sha256=PINS[V3])
 write('independent_stage_precheck.json',report)
 print(json.dumps(dict(status=report['status'],checks=N,report_sha256=h(D/'independent_stage_precheck.json'),candidate_paths=len(projection),ignored_count=len(ignored),pending_transports=len(pending_traces))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('failure.json',dict(status='audit_failure_preserved',checks=N,error=str(e),traceback=traceback.format_exc(),stage_executed=False));raise
