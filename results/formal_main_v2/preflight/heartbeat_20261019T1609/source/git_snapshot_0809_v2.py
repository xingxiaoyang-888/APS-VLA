from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys
from datetime import datetime, timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
PY=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python')
B='results/formal_main_v2/preflight/heartbeat_20261019T1609'
SELF=R/'.local/git_snapshot_0809_v2.py'
assert os.name=='posix' and Path(__file__).resolve()==SELF
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(rel,data):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
 return {'path':rel,'sha256':sha(data),'bytes':len(data)}
def dump(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def git(*args,input=None):
 p=subprocess.run(['git','-C',str(R),*args],input=input,capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
 return p.stdout
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert sha(cp.read_bytes())=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('root_git_controller',cp)
c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
checker=R/'scripts/ops/check_nonweight_archive_stage.py'
assert sha(checker.read_bytes())=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
sp=importlib.util.spec_from_file_location('root_stage_precheck',checker)
g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 head=git('rev-parse','HEAD').decode().strip()
 assert head=='dd720a1c55ec5ebd611239fc580708343c03b966',head
 preexisting=set(git('diff','--cached','--name-only','-z').decode().split('\0'))-{''}
 operational=R/'.local/deliver_action_candidates_0809.py'
 assert sha(operational.read_bytes())=='9554d48d66f35aadecdb0e7eaa075ab12d9e60cfcfa1eff599a1683407fb7a0d'
 assert (R/(B+'/source/deliver_action_candidates_0809.py')).read_bytes()==operational.read_bytes()
 assert (R/(B+'/source/git_snapshot_0809.py')).read_bytes()==(R/'.local/git_snapshot_0809.py').read_bytes()
 put(B+'/source/git_snapshot_0809_v2.py',SELF.read_bytes())
 roots=[B,'results/formal_main_v2/engineering/action_deployment_candidates_0809','scripts/ops/formal_action_deployment_v1']
 names=[]
 for rel in roots:
  for p in (R/rel).rglob('*'):
   assert not p.is_symlink()
   if p.is_file():names.append(p.relative_to(R).as_posix())
 names.extend(['docs/完整实验计划.md','docs/实验进度.md','docs/正式主实验规划.md','docs/正式主实验阶段结论.md','docs/正式动作执行入口接入记录.md','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl','results/formal_main_v2/control_transport/action_candidates_delivery_0809.jsonl'])
 names=sorted(set(names))
 ignored_logs=[n for n in names if n.startswith('results/formal_main_v2/engineering/action_deployment_candidates_0809/') and n.endswith('.log')]
 assert len(ignored_logs)==16
 assert preexisting<=set(names+[B+'/git_required_files.json']),sorted(preexisting-set(names))
 ig=R/'.gitignore'
 assert sha(ig.read_bytes())=='8f812072c9a904c2ebdd59a727c2c7a1331b492c205eb20a318afc355db6ecab'
 newignore=ig.read_bytes()+b'\n# Exact CPU author/independent audit logs retained for action deployment candidates.\n'+('\n'.join('!/'+n for n in ignored_logs)+'\n').encode()
 ig.write_bytes(newignore)
 failure=put(B+'/git_snapshot_attempt1.json',dump({'kind':'delivery_attempt_failure','returncode':1,'cause':'Git generic *.log ignored 16 exact CPU audit logs; partial stage inspected and preserved.','affected_paths':ignored_logs,'transport_audit':'results/formal_main_v2/control_transport/action_candidates_git_snapshot_0809.jsonl','bounded_fix':'Exact ignore exceptions only; no forced staging or source/science change.','GPU_seconds':0}))
 names.extend(['.gitignore',failure['path'],'results/formal_main_v2/control_transport/action_candidates_git_snapshot_0809.jsonl'])
 names=sorted(set(names))
 rows=[]
 for rel in names:
  g.lexical(rel)
  data=(R/rel).read_bytes()
  assert len(data)<100*(1<<20)
  rows.append({'path':rel,'sha256':sha(data),'bytes':len(data)})
 req=B+'/git_required_files_v2.json'
 put(req,dump({'schema':'cti_nonweight_archive_stage_v1','kind':'required_files','files':rows}))
 names.append(req)
 git('add','--pathspec-from-file=-','--pathspec-file-nul',input=('\0'.join(names)+'\0').encode())
 snap='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0547_union17_v2.json'
 assert sha((R/snap).read_bytes())=='3f3d25952624f489f3182bc3111c1e070e7ecc52218d9ab6e4059a4941e8f6f3'
 raw=json.loads((R/snap).read_text())['files']
 assert len(raw)==17
 transport=R/'scripts/ops/server_control_transport_v1/run_server_control.py'
 assert sha(transport.read_bytes())=='302a3e6d16143d5a54eb542916278a7ab2eb3c6478a55593a61584d4a7cf0af5'
 argv=[str(PY),'-B',str(checker),'--project-root',str(R),'--snapshot',snap,'--snapshot-sha256','3f3d25952624f489f3182bc3111c1e070e7ecc52218d9ab6e4059a4941e8f6f3','--required-files',req]
 for row in raw:argv.extend(['--raw-path',row['path']])
 print(json.dumps({'status':'staged_explicit_delivery','files':len(names),'writer_lock_held':True}),flush=True)
 p=subprocess.run(argv,cwd=R,capture_output=True,timeout=300)
 stdoutref=put(B+'/git_index_archive_check.stdout.json',p.stdout)
 stderrref=put(B+'/git_index_archive_check.stderr.txt',p.stderr)
 if p.returncode:raise RuntimeError('Archive stage guard failed; preserved output. No commit. '+p.stderr.decode(errors='replace')[-2000:])
 result=json.loads(p.stdout)
 assert result['status']=='verified_index_archive_delivery'
 assert result['frozen_files_verified_in_worktree_and_index']==173
 assert len(result['raw_paths_restored_exactly'])==17
 additions=[stdoutref['path'],stderrref['path']]
 for rel in additions:
  g.lexical(rel)
  assert (R/rel).is_file() and not (R/rel).is_symlink()
  assert (R/rel).stat().st_size<1<<20
 git('add','--pathspec-from-file=-','--pathspec-file-nul',input=('\0'.join(additions)+'\0').encode())
 for row in rows:
  assert sha(git('show',':'+row['path']))==row['sha256'],row['path']
 # The only additions after the full index check are the completed checker receipt and transport audit.
 assert set(git('diff','--cached','--name-only','-z').decode().split('\0'))-{''}<=set(names+additions)
 frozen=json.loads((R/g.INVENTORY).read_text())['files']
 changed=set(git('diff','--cached','--name-only','-z').decode().split('\0'))
 assert not changed.intersection(frozen)
 for rel,expected in frozen.items():assert sha(git('show',':'+rel))==expected
 message='Publish independently audited action deployment candidates and supervisor evidence'
 committed=git('commit','-m',message).decode()
 after=git('rev-parse','HEAD').decode().strip()
 assert after!=head
 receipt={'status':'committed_server_only','utc':datetime.now(timezone.utc).isoformat(),'head_before':head,'commit':after,'required_files':len(rows),'extra_checker_receipts':additions,'frozen_files_unchanged':173,'raw_log_archives_restored':17,'weights_added':False,'normal_training_state_not_mutated_by_this_script':True,'push_pending':True}
 put('.local/git_snapshot_0809_v2_result.json',dump(receipt))
 print(json.dumps(receipt,ensure_ascii=False),flush=True)
