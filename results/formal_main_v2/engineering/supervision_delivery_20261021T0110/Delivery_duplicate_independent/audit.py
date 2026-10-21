from pathlib import Path
from datetime import datetime,timezone
import ast,collections,hashlib,json,os,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/delivery_duplicate_independent_20261021T0110'
B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110'
ENTRY='.local/finish_git_delivery_20261021T0110_v7.py'
EPIN='a3f450e360213c87a4ba86acfe3b6b80cd70a9b0f3dbb65e628bec249b8c62be'
OLD=B+'/git_required_files_v1.json'
OPIN='3cb1d212fec9f588b442b955d65d8a2d11228bb4d92cb3bfc747527c7600e919'
IPIN='c3c21b95e148b8e7b94381a5518fda2a9845d8451a13f80c864c9c61e2361e3c'
SPIN='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
SUM='6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2'
BASE='98817e8d996e8db750191cccb8b01a7ba81da169'
TRACE='results/formal_main_v2/control_transport/git_delivery_v6_20261021T0110.jsonl'
checks=[]
def ck(name,value):
 if not value:raise AssertionError(name)
 checks.append({'name':name,'passed':True})
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(n):
 b=(R/n).read_bytes();return {'path':n,'sha256':sha(b),'bytes':len(b)}
def git(*args):
 env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_OPTIONAL_LOCKS']='0'
 c=subprocess.run(['git','-c','core.quotepath=false','-c','core.fsmonitor=false',*args],cwd=R,env=env,capture_output=True,check=True)
 return c.stdout
entry=(R/ENTRY).read_bytes();txt=entry.decode();tree=ast.parse(txt)
ck('exact_v7_entry_source',sha(entry)==EPIN)
ck('exact_original_guard_source',ref('scripts/ops/check_nonweight_archive_stage.py')['sha256']=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
ck('exact_shared_lock_controller',ref('scripts/ops/formal_autonomous_training_v1/controller.py')['sha256']=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
ck('index_baseline',sha((R/'.git/index').read_bytes())==IPIN)
ck('HEAD_baseline',git('rev-parse','HEAD').decode().strip()==BASE)
ck('state_baseline',ref('results/experiment_supervisor/state.json')['sha256']==SPIN)
ck('summary_baseline',ref(B+'/final_summary.json')['sha256']==SUM)
oldbytes=(R/OLD).read_bytes();ck('original_required_pin',sha(oldbytes)==OPIN)
value=json.loads(oldbytes)
ck('original_required_schema_and_count',set(value)=={'schema','kind','files'} and value['schema']=='cti_nonweight_archive_stage_v1' and value['kind']=='required_files' and len(value['files'])==633)
index={}
for raw in git('ls-files','--stage','-z').split(b'\0'):
 if not raw:continue
 header,path=raw.split(b'\t',1);mode,oid,stage=header.decode().split();index[path.decode()]={'mode':mode,'oid':oid,'stage':stage}
head={}
for raw in git('ls-tree','-r','-z',BASE).split(b'\0'):
 if not raw:continue
 header,path=raw.split(b'\t',1);mode,kind,oid=header.decode().split();head[path.decode()]={'mode':mode,'oid':oid,'kind':kind}
rows={};duplicates=[];working_oids={};blob_metadata=[]
for row in value['files']:
 n=row['path'];ck('row_exact_fields:'+n,set(row)=={'path','sha256','bytes'})
 p=R/n;b=p.read_bytes();ck('working_exact_reference:'+n,row=={'path':n,'sha256':sha(b),'bytes':len(b)})
 oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();working_oids[n]=oid
 ck('index_exact_content_and_regular_mode:'+n,n in index and index[n]['stage']=='0' and index[n]['mode'] in {'100644','100755'} and index[n]['oid']==oid)
 if n in rows:
  ck('duplicate_is_byte_exact_same_row',rows[n]==row);duplicates.append(row)
 else:rows[n]=row;blob_metadata.append((oid,len(b)))
ck('unique_paths_and_casefold',len(rows)==632 and len({n.casefold() for n in rows})==632)
ck('sole_exact_duplicate',duplicates==[ref(B+'/git_ignored_allowlist_v1.json')])
ck('original_required_staged_exact',git('show',':'+OLD)==oldbytes)
# Validate object availability/size read-only; matching Git blob IDs already bind each full working payload.
ids=sorted(set(blob_metadata));env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_OPTIONAL_LOCKS']='0'
meta=subprocess.run(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],cwd=R,env=env,input=('\n'.join(x[0] for x in ids)+'\n').encode(),capture_output=True,check=True).stdout.decode().splitlines()
ck('all_index_objects_present_exact_size',len(meta)==len(ids) and all(s==oid+' blob '+str(sz) for (oid,sz),s in zip(ids,meta)))
changed=git('diff','--cached','--name-status','--no-renames','--no-ext-diff','--no-textconv','-z').split(b'\0');ck('staged_format',changed[-1]==b'' and (len(changed)-1)%2==0)
staged={changed[i+1].decode():changed[i].decode() for i in range(0,len(changed)-1,2)}
expected={n for n in rows if n not in head or head[n]['oid']!=working_oids[n] or head[n]['mode']!=index[n]['mode']}
unchanged=sorted(set(rows)-expected)
ck('exact_staged_set_no_extras_or_omissions',set(staged)==expected|{OLD} and len(staged)==629)
ck('no_deletion_typechange_or_unmerged',set(staged.values())<={'A','M'})
ck('four_old_members_already_in_HEAD',len(unchanged)==4 and len(expected)==628)
ck('four_unchanged_members_are_original_Spatial',all('/Spatial/' in n or '/spatial_' in n or '/libero_spatial/' in n or 'spatial' in n.lower() for n in unchanged))
trace=(R/TRACE).read_bytes();ck('original_v6_trace_retained_pin',sha(trace)=='99e0f2781411a71a7e3e674a8978df42792c121f27251efe967daf503790f8f3')
events=[json.loads(x) for x in trace.splitlines()];ck('trace_has_control_start_and_end',events[0]['event']=='control_start' and events[-1]['event']=='control_end')
ck('original_final_scientific_delivery_review_inherited_exact',ref(E+'/Delivery_independent/actual_review_v2.json')['sha256']=='69434136678f7ce1549de4e5b10c37d5272276263ab75e9ba06effb3debe7d8a')
# Source-level continuation boundaries, no execution of root finisher.
ck('single_shared_writer_transaction',txt.count("with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):")==1)
ck('baseline_CAS_before_mutations',txt.index("assert h(R/'.git/index')")==txt.index("assert h(R/'.git/index')") and txt.index("assert h(R/'.git/index')")<txt.index("cp(src,dst);added.append(dst)"))
ck('fixed_duplicate_only_and_case_alias_refusal',"if n in rows:assert rows[n]==row;duplicates.append(row)" in txt and "assert duplicates==[ref(B+'/git_ignored_allowlist_v1.json')]" in txt and "len({n.casefold() for n in rows})==632" in txt)
ck('old_failed_list_and_trace_added_not_replaced',"added=[OLD,TRACE]" in txt and "required=B+'/git_required_files_v2.json';newrows={**rows,**{n:ref(n) for n in added}}" in txt)
ck('new_required_unique_sorted_no_self_reference',"'files':[newrows[n] for n in sorted(newrows)]" in txt and "added.append(required)" not in txt)
ck('new_private_audit_exactly_bounded',"1<=len(members)<=8" in txt and "Path(n).name==n" in txt and "Path(n).suffix in {'.py','.json','.md'}" in txt and "row['bytes']<10*(1<<20)" in txt)
ck('audit_report_pins_exact_entry_and_failed_list',"report['entrypoint_sha256']==h(Path(__file__)) and report['original_required_sha256']==OLD_SHA" in txt)
ck('all_output_files_exclusive_create',"assert not p.exists(),n" in txt and "q.open('xb')" in txt and "p.open('xb')" in txt)
ck('original_guard_173_archive_and_lexical_still_required',"checked=guard.check(R,SNAP,SSHA,raw,required)" in txt and "checked['frozen_files_verified_in_worktree_and_index']==173" in txt and "guard.lexical(n);git('add','--',n)" in txt)
ck('state_summary_rechecked_before_commit',txt.rindex("assert h(R/'results/experiment_supervisor/state.json')")<txt.index("result=git('commit'") and txt.rindex("assert h(R/'results/experiment_supervisor/state.json')")>txt.index("checked=guard.check"))
git_literals=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='git' and node.args and isinstance(node.args[0],ast.Constant):git_literals.append(node.args[0].value)
ck('no_reset_clean_checkout_push_or_slurm',set(git_literals)<={'rev-parse','show','diff','add','commit'} and all(x not in txt for x in ['sbatch','scancel','squeue','sacct','shutil.rmtree']))
ck('one_commit_after_guards',git_literals.count('commit')==1 and txt.index("result=git('commit'")>txt.index("checked=guard.check"))
ck('only_two_exact_existing_README_whitespace_exceptions',"allowed={E+'/Goal_full200_dispatch/README.md',E+'/Goal_full200_dispatch_v2/README.md'}" in txt and 'assert set(exceptions)==allowed' in txt and "git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])" in txt)
for n in [B+'/git_required_files_v2.json',B+'/git_index_guard_v1.json',B+'/git_duplicate_list_correction.json',B+'/git_whitespace_diagnostic_v1.json',B+'/git_delivery_v1.json',E+'/Delivery_duplicate_independent',B+'/root_operations/finish_git_delivery_20261021T0110_v7.py','.local/git_commit_20261021T0110.json']:
 ck('exclusive_target_currently_absent:'+n,not (R/n).exists())
ck('index_after_readonly_audit_unchanged',sha((R/'.git/index').read_bytes())==IPIN)
ck('HEAD_after_readonly_audit_unchanged',git('rev-parse','HEAD').decode().strip()==BASE)
ck('state_after_readonly_audit_unchanged',ref('results/experiment_supervisor/state.json')['sha256']==SPIN)
ck('summary_after_readonly_audit_unchanged',ref(B+'/final_summary.json')['sha256']==SUM)
report={'schema':'formal_main_v2','kind':'bounded_duplicate_git_required_list_independent_review','status':'passed_bounded_duplicate_list_correction','reviewed_by':'independent','entrypoint_sha256':EPIN,'original_required_sha256':OPIN,'state_sha256':SPIN,'index_sha256':IPIN,'summary_sha256':SUM,'baseline_HEAD':BASE,'blockers':[],'scope':'Read-only exact 633-row/632-path required-list and 629-entry staged continuation review; inherited scientific audit not rerun. Root v7 not executed, future commit/push not verified.','original_required_rows':633,'unique_required_paths':632,'duplicate_rows':duplicates,'staged_paths':629,'changed_required_paths':628,'unchanged_HEAD_members':unchanged,'all_original_unique_paths_preserved':True,'case_aliases':0,'index_and_HEAD_unchanged':True,'Git_write_commands':False,'new_Slurm_queries':0,'new_GPU_submissions':0,'new_scientific_trials':0,'source173_guard_unchanged':True,'final_sealed':True,'scientific_review_inherited':ref(E+'/Delivery_independent/actual_review_v2.json'),'failure_trace':ref(TRACE),'implementation_notes':['Correction removes only a duplicate metadata row; old failed list and original transport trace remain explicit delivery members.','V7 exact-baseline assertion, shared writer lock, original nonweight/173/archive guard and final state/summary checks remain mandatory before one commit.','Two already archived README whitespace exceptions are exact paths; no scientific/source README bytes are edited.','Audit manifest output copies are create-only. Failed attempts retain evidence; no automatic retry or generic index reset is introduced.'],'local_transport_setup_note':'First memory-only read command used invalid PowerShell type TextEncoding, failed before intended server payload; corrected to System.Text.Encoding. No project/local files were written.','utc':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks}
p=D/'independent_review.json';p.open('x',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
files=[]
for p in sorted(D.iterdir()):
 if p.is_file():b=p.read_bytes();files.append({'path':p.name,'sha256':sha(b),'bytes':len(b)})
manifest={'schema':'formal_main_v2','kind':'bounded_duplicate_git_required_list_independent_delivery','status':'frozen','source_root':str(D),'files':files,'file_count':len(files),'new_GPU_submissions':0,'Git_write_commands':False}
mp=D/'delivery_manifest.json';mp.open('x',encoding='utf-8').write(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'unchanged_HEAD_members':unchanged,'report_sha256':sha((D/'independent_review.json').read_bytes()),'manifest_sha256':sha(mp.read_bytes()),'files':len(files)},ensure_ascii=False))
