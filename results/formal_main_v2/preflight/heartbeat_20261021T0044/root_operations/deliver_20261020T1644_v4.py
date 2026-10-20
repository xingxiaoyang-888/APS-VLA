from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,re,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
BASELINE='88a0fea9b76a7f904ec0e9ce0c848b3b3413f36d'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';SNAP_SHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
RAW=[x['path'] for x in json.loads((R/SNAP).read_bytes())['files']];assert len(RAW)==9
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def checked(x):assert h(R/x['path'])==x['sha256'];return rd(x['path'])
def put(n,b):
 p=R/n;assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
def save(n,x):put(n,(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+chr(10)).encode())
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--extra-inputs',required=True);ap.add_argument('--extra-inputs-sha256',required=True);args=ap.parse_args();extra=checked(dict(path=args.extra_inputs,sha256=args.extra_inputs_sha256))
assert extra['status']=='root_exact_delivery_scope' and extra['baseline']==BASELINE and extra['root_completed_arms']==72
c=module('git1644ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASELINE and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress'];key='last_terminals_integrity_review_20261020T1644'
 assert f[key]['status']=='passed' and f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000
 assert f['current_action_development_trial_count']==5200 and f['completed_development_trials']==6412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None
 checked(f[key]['independent_review']);checked(f[key]['root_acceptance']);checked(state['last_root_supervision_snapshot'])
 sources={};transports={};open_transports=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split(chr(0)):
  if not row:continue
  name=row[3:]
  if not name.startswith('results/formal_main_v2/control_transport/'):continue
  rows=[json.loads(x) for x in (R/name).read_bytes().splitlines()]
  assert rows and rows[0]['event']=='control_start'
  if rows[-1]['event']!='control_end':open_transports.append(name);continue
  transports[name]=h(R/name);rel=rows[0].get('entrypoint','')
  if len(Path(rel).parts)==2 and Path(rel).parts[0]=='.local':
   pin=rows[0]['entrypoint_sha256'];assert h(R/rel)==pin;dst=B+'/root_operations/'+Path(rel).name;put(dst,(R/rel).read_bytes());sources[dst]=dict(original=rel,sha256=pin)
 for row in extra.get('additional_root_files',[]):
  rel=row['path'];assert rel.startswith('.local/') and h(R/rel)==row['sha256'];dst=B+'/root_operations/'+Path(rel).name;put(dst,(R/rel).read_bytes());sources[dst]=dict(original=rel,sha256=row['sha256'])
 own=Path(__file__).relative_to(R).as_posix();put(B+'/root_operations/'+Path(own).name,(R/own).read_bytes())
 save(B+'/root_operation_sources_v4.json',dict(status='exact_sources_preserved',sources=sources,closed_transports=transports,open_transports_excluded=open_transports))
 archived={}
 for receipt in [B+'/evidence_delivery_initial.json',B+'/root_post_integration_acceptance.json',*extra.get('archive_receipts',[])]:
  data=rd(receipt)
  for row in data.get('copies',[]):
   s=row['source'];a=row['archive'];assert a['path'].startswith(E+'/') or a['path'].startswith(B+'/');assert h(R/a['path'])==a['sha256']==s['sha256'];assert (R/a['path']).stat().st_size==s['bytes'];archived[a['path']]=ref(a['path'])
 ignore=R/'.gitignore';prior=ignore.read_text();adds=['!/'+p.relative_to(R).as_posix() for p in sorted((R/E).rglob('*.log')) if '!/'+p.relative_to(R).as_posix() not in prior.splitlines()]
 for name in extra.get('exact_gitignore_exceptions',[]):
  assert name.startswith('results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k64_seed23_2f71f57773be4dc38b46df6b6b9f4462/') and Path(name).name in ['stdout.log','stderr.log']
  assert any(x['path']==name and h(R/name)==x['sha256'] for x in extra['additional_exact'])
  if '!/'+name not in prior.splitlines():adds.append('!/'+name)
 retained_exact=[]
 for name,row in sorted(archived.items()):
  p=R/name
  if p.name=='.writer.lock':
   assert name.startswith(E+'/Object_production_independent/lifecycle/fixtures/') and p.stat().st_size==0 and row['sha256']=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
  elif name==E+'/Goal_prefix58_independent/synthetic_blobs_lossless.tar.gz':
   assert p.stat().st_size==314395 and row['sha256']=='efc0884788806d464c3a4e6fbbe11554f7b56d5e1968701387d53af8d404a001'
  else:continue
  retained_exact.append(ref(name))
  if '!/'+name not in prior.splitlines():adds.append('!/'+name)
 assert len(retained_exact)==48
 save(B+'/git_delivery_ignore_repair_v4.json',dict(status='exact_archived_fixture_and_lossless_tar_inclusion',retained_failure_transport=ref('results/formal_main_v2/control_transport/deliver_turn_20261020T1644.jsonl'),prior_source=ref('.local/deliver_20261020T1644_v3.py'),original_failure='Complete archive assertion rejected 47 zero-byte archived fixture locks and one verified lossless CPU diagnostic archive excluded by global ignore patterns.',previous_index_untouched=True,exact_files=retained_exact,live_lock_rule_unchanged=True,science_and_state_unchanged=True))
 if adds:ignore.write_text(prior+chr(10)+'# Exact immutable audit evidence, 20261020T1644.'+chr(10)+chr(10).join(adds)+chr(10))
 exact={'.gitignore','results/experiment_supervisor/state.json',args.extra_inputs}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记','正式下游阻塞登记_20261020T1644'])
 exact.update('results/formal_main_v2/libero_goal/k64/seed41/training/segment_reviews/'+n for n in ['3043877.json','3043877_independent.json'])
 for row in extra.get('additional_exact',[]):assert h(R/row['path'])==row['sha256'];exact.add(row['path'])
 ev='results/formal_main_v2/autonomous_training/run_v1/events';idx=rd(ev+'/index.json');assert idx['version']==1
 for row in idx['sealed']:assert h(R/ev/row['path'])==row['sha256'];exact.add(ev+'/'+row['path'])
 exact.update([ev+'/index.json',ev+'/'+idx['active']]);excluded=[];selected=[]
 allowed_live={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out',*open_transports}
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split(chr(0)):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or name.startswith(B+'/') or name.startswith(E+'/')
  if name.startswith('results/formal_main_v2/control_transport/'):accept=name in transports
  assert name not in RAW,'Lossless archived raw originals must remain ignored'
  if not accept:excluded.append(name);continue
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5');selected.append(name)
 assert set(excluded)<=allowed_live,excluded
 assert set(archived)<=set(selected)
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'Full archive delivery missing'
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 save(B+'/git_required_files.json',dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)]));git('add','--',B+'/git_required_files.json')
 assert set(git('diff','--cached','--name-only').stdout.decode().splitlines())==set(selected)|{B+'/git_required_files.json'}
 guard=module('git1644guard','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
 check=guard.check(R,SNAP,SNAP_SHA,RAW,B+'/git_required_files.json');assert check['status']=='verified_index_archive_delivery' and check['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard.json',check)
 diag=git('diff','--cached','--check',check=False);save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()));exceptions=[]
 if diag.returncode:
  assert not diag.stderr
  for line in diag.stdout.decode().splitlines():
   if not re.match(r'^.*?:[0-9]+: ',line):continue
   match=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',line);assert match,line
   name=match.group(1);assert name in archived,name;exceptions.append(name)
  assert exceptions
 exceptions=sorted(set(exceptions));git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='exact_index_and173_frozen_verified',utc=datetime.now(timezone.utc).isoformat(),baseline=BASELINE,root_completed_arms=72,reviewed_arm_updates=360000,independent_post_review=f[key]['independent_review'],new_GPU_jobs=extra['new_GPU_jobs'],new_development_accepted=800,Goal_original200_HOLD=True,final_sealed=True,weights_added=False,excluded_live=excluded,original_archive_whitespace_preserved=[ref(n) for n in exceptions],index_guard=ref(B+'/git_index_guard.json'),summary=state['last_root_supervision_snapshot']))
 for name in ['git_index_guard.json','git_whitespace_diagnostic.json','git_delivery.json']:git('add','--',B+'/'+name);assert git('show',':'+B+'/'+name).stdout==(R/B/name).read_bytes()
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines());git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 result=git('commit','-m',extra['commit_message']);head=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_20261020T1644.json',dict(commit=head,baseline=BASELINE,files=count,root_complete=72,index_guard='passed',new_GPU_jobs=extra['new_GPU_jobs'],final_sealed=True))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=head,files=count,summary=result.stdout.decode().splitlines()[:2])),flush=True)
