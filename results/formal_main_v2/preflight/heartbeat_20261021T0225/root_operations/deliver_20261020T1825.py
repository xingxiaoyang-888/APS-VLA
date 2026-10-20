from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,re,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0225';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1825';BASELINE='ad2dea8105531fbd46b3013b234dc92806cdf213'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';SNAP_SHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def cp(src,dst):
 p=R/dst;p.parent.mkdir(parents=True,exist_ok=True);raw=(R/src).read_bytes()
 if p.exists():assert p.read_bytes()==raw
 else:p.open('xb').write(raw)
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','delivery1825ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASELINE and not git('diff','--cached','--name-only').stdout
 s=rd('results/experiment_supervisor/state.json');f=s['formal_main_progress'];assert f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000 and f['current_action_development_trial_count']==5400 and f['completed_development_trials']==6612 and f['completed_final_trials']==0 and f['test_opened'] is False and f['global_release_created'] is False
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 last=s['last_root_supervision_snapshot'];assert last['path']==B+'/final_summary.json' and h(R/last['path'])==last['sha256'];summary=rd(last['path']);assert summary['compatible_development_trials']==6000
 closed=[];opened=[];root_sources=[]
 for raw in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split(chr(0)):
  if not raw:continue
  n=raw[3:]
  if not n.startswith('results/formal_main_v2/control_transport/'):continue
  rows=[json.loads(x) for x in (R/n).read_bytes().splitlines()];assert rows[0]['event']=='control_start'
  if rows[-1]['event']!='control_end':opened.append(n);continue
  closed.append(n);rel=rows[0].get('entrypoint','')
  if len(Path(rel).parts)==2 and Path(rel).parts[0]=='.local':
   assert h(R/rel)==rows[0]['entrypoint_sha256'];dst=B+'/root_operations/'+Path(rel).name;cp(rel,dst);root_sources.append({'source':rel,'archive':ref(dst)})
 for rel in ['.local/deliver_20261020T1825.py','.local/github_push_20261020T1825.py','.local/github_push_20261020T1644_verified.json']:
  dst=B+'/root_operations/'+Path(rel).name;cp(rel,dst);root_sources.append({'source':rel,'archive':ref(dst)})
 save(B+'/root_operation_sources.json',{'status':'exact_sources_preserved','sources':root_sources,'closed_transports':[ref(n) for n in closed],'open_transports_excluded':opened})
 exact={'results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/downstream_reviews/3052166.json','results/formal_main_v2/downstream_reviews/3052166_independent.json','results/formal_main_v2/job_receipts/3052166.json','results/slurm/cti-formal-downstream_3052166.out','results/slurm/cti-formal-downstream_3052166.err'}
 exact.update('docs/'+x+'.md' for x in ['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记','正式Goal前58条工程诊断','正式训练后采集执行登记','正式下游阻塞登记_20261020T1825'])
 prefixes=[B+'/',E+'/','scripts/ops/formal_action_deployment_posttraining_v1/','scripts/ops/formal_goal_prefix58_observer_v2/','results/formal_main_v2/engineering/goal_prefix58_20261020T1825/','results/formal_main_v2/execution/spatial_collect_action_v1_20261020T1825/','results/formal_main_v2/execution/object_collect_action_v1_20261020T1825/','results/formal_main_v2/pulls/20261020T182913Z_b827e776a52c/','results/formal_main_v2/libero_object/downstream/development/b0a59115666b5afa/attempt01/']
 for suite in ['Spatial','Object']:
  auth=rd('results/formal_main_v2/execution/'+suite.lower()+'_collect_action_v1_20261020T1825/submission_authorization.json');sha=h(R/('results/formal_main_v2/execution/'+suite.lower()+'_collect_action_v1_20261020T1825/submission_authorization.json'));consumed=s['autonomous_training_v1']['downstream_reservations_consumed'][sha];jid=consumed['job_id'];j=next(x for x in s['registered_jobs'] if x['job_id']==jid)
  exact.update([j['invocation'],'results/formal_main_v2/submissions/'+jid+'.json']);prefixes.append('results/formal_main_v2/downstream_gateway/'+sha+'/')
 selected=set(exact)|set(closed)
 for pre in prefixes:
  d=R/pre;assert d.is_dir()
  selected.update(p.relative_to(R).as_posix() for p in d.rglob('*') if p.is_file())
 # Only immutable archived evidence may include zero-byte CPU fixture locks, logs, or packed diagnostic arrays.
 for n in selected:
  p=R/n;assert p.is_file() and p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]) and p.stat().st_size<100*(1<<20)
  assert p.suffix.lower() not in ['.pt','.pth','.ckpt','.safetensors','.bin','.pyc','.init','.npz','.npy','.h5','.hdf5'],n
  if p.name=='.writer.lock':assert n.startswith(E+'/') and p.stat().st_size==0,n
 RAW=[x['path'] for x in rd(SNAP)['files']];assert len(RAW)==9 and not set(RAW)&selected
 unselected=[]
 for raw in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split(chr(0)):
  if raw and raw[3:] not in selected:unselected.append(raw[3:])
 assert set(unselected)<=set(opened),unselected
 selected=sorted(selected)
 for i in range(0,len(selected),60):git('add','-f','--',*selected[i:i+60])
 staged=set(git('diff','--cached','--name-only').stdout.decode().splitlines());assert staged<=set(selected)
 save(B+'/git_required_files.json',{'schema':'cti_nonweight_archive_stage_v1','kind':'required_files','files':[ref(n) for n in selected]});git('add','--',B+'/git_required_files.json')
 guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','delivery1825guard');v=guard.check(R,SNAP,SNAP_SHA,RAW,B+'/git_required_files.json');assert v['status']=='verified_index_archive_delivery' and v['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard.json',v)
 diag=git('diff','--cached','--check',check=False);assert not diag.stderr;exceptions=[]
 if diag.returncode:
  for line in diag.stdout.decode().splitlines():
   if not re.match(r'^.*?:[0-9]+: ',line):continue
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',line);assert m,line;n=m.group(1);assert n.startswith((E+'/',B+'/root_operations/')),n;exceptions.append(n)
  assert exceptions
 exceptions=sorted(set(exceptions));save(B+'/git_whitespace_diagnostic.json',{'returncode':diag.returncode,'stdout':diag.stdout.decode(),'exact_archived_source_whitespace_preserved':exceptions})
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_delivery.json',{'schema':'formal_main_v2','status':'exact_index_and173_frozen_verified','baseline':BASELINE,'source_frozen_files':173,'root_complete':72,'compatible_development_trials':6000,'new_development_accepted':200,'new_GPU_jobs':summary['new_GPU_jobs'],'final_sealed':True,'weights_added':False,'all_project_writes_server_only':True,'open_transports_excluded':opened,'index_guard':ref(B+'/git_index_guard.json'),'summary':last,'utc':datetime.now(timezone.utc).isoformat()})
 for n in ['git_index_guard.json','git_whitespace_diagnostic.json','git_delivery.json']:git('add','--',B+'/'+n);assert git('show',':'+B+'/'+n).stdout==(R/B/n).read_bytes()
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines());result=git('commit','-m','Record complete training, Object development, and bounded Goal and collection jobs');head=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_20261020T1825.json',{'commit':head,'baseline':BASELINE,'files':count,'root_complete':72,'index_guard':'passed','final_sealed':True});print(json.dumps({'status':'committed_not_yet_pushed','commit':head,'files':count,'summary':result.stdout.decode().splitlines()[:2]}))
