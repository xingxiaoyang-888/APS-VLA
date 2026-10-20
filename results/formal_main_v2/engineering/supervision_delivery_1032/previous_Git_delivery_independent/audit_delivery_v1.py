from pathlib import Path
import ast,datetime,difflib,hashlib,json,re,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
O=R/'.local/git_delivery_review_0927'
SCRIPT='.local/deliver_0927.py';PIN='44c57f28163a06649e4c3565d9a16e51c23cd1ac9fea48ccc1ecc40c67b3b825'
SUMMARY={'path':'results/formal_main_v2/preflight/heartbeat_20261020T1727/summary.json','sha256':'5e05c9eb667af2444f4e331a0e52bb304b364ce1d4bb593fee0037695ad6b6eb'}
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(rel):
 p=R/rel;b=p.read_bytes();return {'path':rel,'sha256':sha(b),'bytes':len(b)}
def read(rel,pin):
 b=(R/rel).read_bytes();assert sha(b)==pin,(rel,sha(b),pin);return b
s=read(SCRIPT,PIN).decode();tree=ast.parse(s);compile(s,SCRIPT,'exec')
read(SUMMARY['path'],SUMMARY['sha256'])
bind={n.targets[0].id:n.value for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
pins=ast.literal_eval(bind['TRANSPORT_PINS']);assert isinstance(pins,dict) and len(pins)==12
head=ast.literal_eval(bind['HEAD']);assert head=='7aa8ae7c2167b671bdfcb09f57fc77712d570f45'
B=ast.literal_eval(bind['B']);E=ast.literal_eval(bind['E'])
assert (R/B/'root_operations').is_dir()
assert subprocess.check_output(['git','--no-optional-locks','rev-parse','HEAD'],cwd=R,text=True).strip()==head
assert subprocess.check_output(['git','--no-optional-locks','diff','--cached','--name-only'],cwd=R)==b''
logs=[]
for name,pin in pins.items():
 assert re.fullmatch(r'results/formal_main_v2/control_transport/[A-Za-z0-9_]+\.jsonl',name)
 assert re.fullmatch(r'[0-9a-f]{64}',pin)
 b=read(name,pin);events=[json.loads(x) for x in b.splitlines() if x.strip()]
 assert events[0]['event']=='control_start' and events[-1]['event']=='control_end'
 assert events[-1].get('source173_and_entrypoint_unchanged') is True
 logs.append({**ref(name),'closed':True,'returncode':events[-1].get('returncode')})
modules={
 'scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363',
 'scripts/ops/check_nonweight_archive_stage.py':'ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6',
 'scripts/ops/nonweight_archive.py':'f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'}
for name,pin in modules.items():read(name,pin)
# Frozen bytes are checked directly; the root script checks both worktree/index after staging.
invrel='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
inv=json.loads(read(invrel,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'))
assert len(inv['files'])==173
for name,pin in inv['files'].items():read(name,pin)
rootrel='results/formal_main_v2/downstream_reviews/3047982.json'
root=json.loads(read(rootrel,'45e76fbb32159d53dc7be7e5ca6b25d4d52815d44d0234063f30a69500567479'))
assert len(root['files'])==53
rawrefs=[]
for name,pin in root['files'].items():
 read(name,pin);rawrefs.append(ref(name))
aref=B+'/observation_npz_delivery_allowlist.json'
allow=json.loads(read(aref,'b23a11f750ded441b0dfd1f3c066eb032c783b186e567975b34a14f0856880e1'))
npz={x['path']:x for x in allow['files']};assert len(npz)==30
expected={f'results/formal_main_v2/libero_10/downstream/collect/648ce4233e78353e/attempt01/task{t:02d}/{p}.npz' for t in range(10) for p in ['first','middle','last']}
assert set(npz)==expected=={k for k in root['files'] if k.endswith('.npz')}
auditrel=E+'/Long_observation_delivery_independent/typed_allowlist_review.json'
audit=json.loads(read(auditrel,'17f0aa6d6e34f0b73e04fc9dd30b7a65f9221393cb63427158f102f493a609f2'))
assert audit['status']=='passed' and not audit['blockers'] and audit['allowlist']['sha256']==ref(aref)['sha256']
assert audit['observations']==30 and audit['total_bytes']==11839320 and audit['numpy_allow_pickle'] is False
assert {v['path']:v['sha256'] for v in audit['files']}=={k:v['sha256'] for k,v in npz.items()}
for name,row in npz.items():assert ref(name)=={k:row[k] for k in ('path','sha256','bytes')}
# Confirm mandatory narrow selection, self-binding and index checks remain in the exact reviewed source.
needles=[
 "with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):",
 "assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout",
 "if name.startswith('results/formal_main_v2/control_transport/'):\n   accept=name in TRANSPORT_PINS\n   if accept:assert h(R/name)==TRANSPORT_PINS[name]",
 "if p.suffix=='.npz':assert name in npzs and ref(name)=={k:npzs[name][k] for k in ['path','sha256','bytes']},name",
 "assert set(raw_long)<=set(selected) and set(npzs)<=set(selected) and len([n for n in selected if Path(n).suffix=='.npz'])==30",
 "assert review['status']=='passed' and review['script']==dict(path='.local/deliver_0927.py',sha256=h(Path(__file__)))",
 "assert review['transport_pins']==TRANSPORT_PINS and review['summary']==dict(path=B+'/summary.json',sha256=h(R/B/'summary.json'))",
 "assert audit_manifest['reviewed_script']==review['script']",
 "assert p.suffix in ['.py','.json','.diff','.md'] and p.stat().st_size<100*(1<<20)",
 "assert name not in index.changed\n   _,q=g.same_local_index(index,name,codec);assert q['sha256']==pin",
 "assert set(index.changed)==set(selected)|{B+'/git_required_files.json'}",
 "for row in required_rows:g.same_local_index(index,row['path'],codec,expected=row)",
 "for name,pin in raw_long.items():\n   _,q=g.same_local_index(index,name,codec);assert q['sha256']==pin",
 "for name,row in archived.items():g.same_local_index(index,name,codec,expected=row)",
 "index.unchanged()",
 "weights_or_sealed_simulator_state_payloads_added=False,exact_development_observation_npz_files=30",
 "new_root_GPU_submissions=[],new_development_trials=0",
 "collection_cost_not_double_counted=True,full_latency_not_inferred=True"]
for n in needles:assert n in s,n
locks=[n for n in tree.body if isinstance(n,ast.With)];assert len(locks)==1
lock=locks[0]
for n in ast.walk(tree):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='git' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value in ['add','commit']:
  assert lock.lineno<n.lineno<=lock.end_lineno
assert not any(x in s for x in ['git(\'push\'','git(\'reset\'','git(\'clean\'','git(\'checkout\'','sbatch','scancel'])
# Exact current scope only. NPZ ignored at present is intentionally included by 30 literal .gitignore exceptions.
exact={'.gitignore','results/experiment_supervisor/state.json'}
event='results/formal_main_v2/autonomous_training/run_v1/events'
exact.update([event+'/index.json',event+'/events.000001.jsonl',event+'/events.000000.jsonl'])
exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记','正式Long256三种子与64预算开发进展','正式Long64三种子开发结论','正式Long固定测速观测采集登记','正式Long测速观测验收'])
exact.update(root['files']);exact.update(['results/formal_main_v2/downstream_reviews/3047982.json','results/formal_main_v2/downstream_reviews/3047982_independent.json'])
prefixes=[B+'/',E+'/','results/formal_main_v2/pulls/20261020T092912Z_f00b82b82873/']
selected=[];excluded=[]
status=subprocess.check_output(['git','--no-optional-locks','-c','core.quotepath=false','status','--porcelain=v1','--untracked-files=all','-z'],cwd=R).decode()
for row in status.split('\0'):
 if not row:continue
 code,name=row[:2],row[3:];assert code in (' M','??')
 accept=name in exact or any(name.startswith(p) for p in prefixes)
 if name.startswith('results/formal_main_v2/control_transport/'):accept=name in pins
 if accept:
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  assert p.suffix.lower() not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npy','.h5','.hdf5')
  if p.suffix.lower()=='.npz':assert name in npz
  selected.append(name)
 else:excluded.append(name)
assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0927_delivery.jsonl'},excluded
all_e_files=[p for p in (R/E).rglob('*') if p.is_file()]
assert all(p.suffix.lower()!='.npz' for p in all_e_files)
archived={};delivery_refs=[]
for fname in ['Long_collect_terminal_independent_delivery.json','Long_observation_delivery_independent_delivery.json','Long_legacy6_typed_bridge_delivery.json','previous_Git_delivery_independent_delivery.json']:
 rel=B+'/'+fname;d=json.loads((R/rel).read_bytes());delivery_refs.append(ref(rel))
 for row in d['copies']:
  dest=row['archive']['path'];rr=ref(dest)
  assert rr['sha256']==row['archive']['sha256']==row['source']['sha256'] and rr['bytes']==row['source']['bytes']
  archived[dest]=rr
assert set(archived)<=set(selected)
old='.local/deliver_0830_v2.py';old_bytes=read(old,'2f191c6cf6212fa2507e066ea665ae92eadaea2cb74b6722193197bb22ef9793')
diff=''.join(difflib.unified_diff(old_bytes.decode().splitlines(True),s.splitlines(True),fromfile=old,tofile=SCRIPT))
with (O/'deliver_0830_v2_to_0927.diff').open('x',encoding='utf-8',newline='\n') as f:f.write(diff)
report={'schema':1,'status':'passed','reviewer':'/root/long128s41_terminal_0530',
 'script':{'path':SCRIPT,'sha256':PIN},'transport_pins':pins,'summary':SUMMARY,'blockers':[],
 'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'baseline_HEAD':head,'script_bytes':len(s.encode()),
 'checks':{'script_compiles_without_execution':True,'exact12_transport_logs_closed_and_SHA_bound':True,
 'typed_allowlist_exact30_paths_SHA_bytes_schema_identity_bound':True,'other_NPZ_current_scope_rejected':True,
 'no_general_NPZ_ignore_exception':True,'all53_raw_original_files_SHA_verified':True,
 'shared_writer_lock_covers_state_snapshot_and_Git_mutations':True,'state_gates_fail_closed_if_progress_changes':True,
 'initial_index_empty_and_baseline_HEAD_verified':True,'current_worktree_frozen173_SHA_verified':True,
 'root_runtime_rechecks173_worktree_and_index_after_staging':True,'unchanged_index_verifier_and_codec_pins_verified':True,
 'all_selected_index_bytes_rechecked_against_worktree':True,'manifest_archives_report_code_diff_same_snapshot':True,
 'self_report_binds_script_TRANSPORT_PINS_summary_reviewer':True,'unknown_dirty_paths_fail_closed':True,
 'live_controller_stdout_excluded':True,'collection_not_added_to_success_rate_trials':True,
 'no_Git_push_or_GPU_submission_in_script':True,'no_scientific_settings_or_frozen_sources_changed':True},
 'NPZ_allowlist':ref(aref),'NPZ_typed_review':ref(auditrel),'exact_NPZ_count':30,'exact_NPZ_bytes':11839320,
 'raw_file_count':53,'raw_files':rawrefs,'transport_closure_checks':logs,
 'existing_independent_archived_files_verified':len(archived),'archive_delivery_records':delivery_refs,
 'current_selected_scope_count_before_generated_review_archive':len(selected),
 'current_excluded_live_files':excluded,'dependencies':[{**ref(k),'expected_sha256':v} for k,v in modules.items()],
 'frozen_inventory':ref(invrel),'diff':ref(str((O/'deliver_0830_v2_to_0927.diff').relative_to(R))),
 'limitations':['Static script review plus bounded read-only evidence verification; no Git mutation executed by reviewer.',
 'Array schemas were verified in the pinned typed review; this audit binds those exact file hashes rather than re-running scientific evaluation.',
 'Root runtime performs the full index-byte/frozen173 guard before committing. This report does not claim an executed commit or remote push.',
 'Only this exact 30-file development observation set is permitted; final/sealed initial-state values and weights remain forbidden.'],
 'reviewer_wrote_only_private_directory':True,'reviewer_Git_state_or_production_mutations':False,
 'reviewer_GPU_work':False,'additional_transport_created':False}
p=O/'final_review.json'
with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
files=[]
for p in sorted(O.iterdir()):
 if p.is_file():
  assert p.suffix in ['.py','.json','.diff','.md'];files.append(ref(str(p.relative_to(R))))
man={'schema':1,'reviewed_script':report['script'],'files':files,'status':'passed'}
p=O/'final_manifest.json'
with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(man,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'passed','review':ref(str((O/'final_review.json').relative_to(R))),'manifest':ref(str(p.relative_to(R))),'files':len(files),'closed_transport':len(logs),'raw_original_files':53,'exact_NPZ':30,'existing_archive_files':len(archived)}))
