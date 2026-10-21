from pathlib import Path
import ast,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_format_correction_20261020T2358';B='results/formal_main_v2/preflight/heartbeat_20261021T0758'
H=lambda b:hashlib.sha256(b).hexdigest();checks=[];refs={}
def ck(x,n):
 assert x,n
 checks.append({'check':n,'passed':True})
def read(n,w=None):
 p=R/n;ck(p.is_file() and p.resolve()==p,'regular:'+n);b=p.read_bytes()
 if w:ck(H(b)==w,'pin:'+n)
 refs[n]={'path':n,'bytes':len(b),'sha256':H(b)};return b
def guard(e,a):
 if e in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('Independent static reviewer does not operate Git/Slurm')
 if e=='open':
  p,m,f=a
  if isinstance(p,(str,bytes)) and ((m and any(c in m for c in 'wax+')) or (isinstance(f,int) and f&(1|2|64|512|1024))):assert Path(p).resolve().is_relative_to(D)
sys.addaudithook(guard)
pins={
'.local/repair_git_format_20261020T2358_v1.py':'4100c380d0284009b17c29dda7a1d86a782575064aa34d743d638a20a2884fa2',
'.local/deliver_20261020T2358_v5.py':'7b3ddbf5a83d692567d282da3e2f4e681f72cb5a1a9f742a974d3feef0ccd4da',
'.local/deliver_20261020T2358_v6.py':'0d308a50847b86786d62ca71f0842749ef913877ad0ec86eac572bfcb60361a3',
'.local/archive_packages_20261020T2358_v1.py':'0ec611a96dbcd1c0796feb66a2688983b678a7911faaafd211af1bae5abb8491',
'.local/archive_packages_20261020T2358_v2.py':'6d4fe8bc192856d71ac4ab50752beb82dda9a840e7f333918398de2e3ce85b6a'}
texts={n:read(n,w).decode() for n,w in pins.items()}
for t in texts.values():ast.parse(t)
repair=texts['.local/repair_git_format_20261020T2358_v1.py'];d5=texts['.local/deliver_20261020T2358_v5.py'];d6=texts['.local/deliver_20261020T2358_v6.py'];a1=texts['.local/archive_packages_20261020T2358_v1.py'];a2=texts['.local/archive_packages_20261020T2358_v2.py']
ck("with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):" in repair,'repair_shared_writer_lock')
ck("len(staged)==224 and set(staged)==set(expected)" in repair and "raw==(R/n).read_bytes()" in repair and "git('show',':'+n)" in repair,'all224_index_and_worktree_exact_bytes_required')
ck("assert check.returncode==2" in repair and "check.stdout.decode()==DOC+':36: new blank line at EOF.\\n'" in repair,'only_exact_EOF_failure_permitted')
ck(repair.index("save(B+'/git_v5_precommit_failure.json'")<repair.index("git('restore','--staged','--',*staged[i:i+60])"),'before_mutation_failure_record_preserved')
ck("for i in range(0,len(staged),60):git('restore','--staged','--',*staged[i:i+60])" in repair and "assert git('diff','--cached','--name-only').stdout==b''" in repair,'exact224_only_index_restore_then_empty')
ck("for n,v in expected.items():assert h(R/n)==v['sha256']" in repair and "(R/DOC).write_bytes(raw[:-1])" in repair and "(R/DOC).read_bytes()+b'\\n'==raw" in repair,'worktree_all_preserved_except_single_LF')
ck("reset" not in repair and "unlink" not in repair and "rmtree" not in repair and "sbatch" not in repair,'no_reset_delete_or_submit')
ck(repair.count("=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'")==2,'exact_state_before_after_unchanged')
replacements=['root_operation_sources','git_ignored_allowlist','git_required_files','git_index_guard','git_whitespace_diagnostic','git_delivery']
want=d5
for name in replacements:want=want.replace(name+'.json',name+'_v6.json')
want=want.replace("'.local/github_push_20261020T2358.py']:","'.local/github_push_20261020T2358.py','.local/deliver_20261020T2358_v6.py']:")
ck(d6==want,'v6_only_six_new_receipt_names_and_own_source_preservation')
ck(a2==a1.replace(":'Delivery_independent'}",":'Delivery_independent','.local/delivery_format_correction_20261020T2358':'Delivery_format_correction'}"),'archiver_only_exact_new_directory_allowlist')
for t,name in [(d6,'delivery_v6'),(a2,'archive_v2')]:
 ck("with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):" in t,'shared_lock:'+name)
 ck('sbatch' not in t and 'squeue' not in t and 'sacct' not in t,'no_Slurm_calls:'+name)
req=json.loads(read(B+'/git_required_files.json','e52831510cbbc626612880054e4f151dd4d6c568eeebfe90a55e4e91979987ea'))
ck(len(req['files'])==223 and len({x['path'] for x in req['files']})==223,'223_required_plus_required_file_itself')
g=json.loads(read(B+'/git_index_guard.json','5129c715ea72a2a49125fb2660f52b059860438e670f9af9888272b60ed57fe7'));ck(g['ordinary_staged_files_verified']==224 and g['frozen_files_verified_in_worktree_and_index']==173 and g['head']=='456014638158b5495df0aa358a55f1c25a4f521c','original_guard_224_and173_receipt')
doc=read('docs/正式下游阻塞登记_20261020T2358.md','d11864b253cdd9b4560db42e2c8d1c090846eddd4622182fc16c82a22ed66aa6')
ck(len(doc)==6300 and doc.endswith(b'\n\n') and not doc.endswith(b'\n\n\n') and H(doc[:-1])=='ad7ecc7406aee39e9afdd0f3323aa27c3a5bbdca3db8bef48b5fed7d8488b966','independent_one_byte_expected_diff')
read('results/experiment_supervisor/state.json','40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a')
report={'schema':'formal_main_v2','kind':'root_delivery_format_correction_static_independent_review','status':'passed_static_repair_and_v6_scope_actual_repair_pending','blockers':[],'check_count':len(checks),'checks':tuple(checks),'sources':refs,'expected_document_after_sha256':H(doc[:-1]),'bytes_removed':1,'scope':'Exact original224 index/worktree identities, one LF in new document only, append-only v6 metadata and exact new archive directory; no actual repair or future Git completion claimed.','actual_repair_verified':False,'new_GPU_submissions':0,'Git_Slurm_state_P_canonical_operations':0}
out=D/'static_review.json';assert not out.exists()
b=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with out.open('xb') as f:f.write(b)
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(b),'check_count':len(checks),'status':report['status']}))
