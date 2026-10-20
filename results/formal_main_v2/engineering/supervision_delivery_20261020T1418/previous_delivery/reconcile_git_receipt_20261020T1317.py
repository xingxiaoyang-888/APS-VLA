from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
BASE='26b4d9eb5ec9e5229b8e1c303e2b3a8980b065e7'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def rd(rel,pin):
 assert h(R/rel)==pin
 return json.loads((R/rel).read_bytes())
def git(*args):
 return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=True).stdout
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('gitreceiptreconcile20261020ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';state_before=h(sp)
 old=rd('.local/git_commit_1317.json','f35c4145a7e6da42727664fd63b379166bf744822930ab0b299b4de30362820f')
 req=rd(B+'/git_required_files.json','92873d61084854ce176e1b677fc8697fb1e3bb7479047bb8b877150567d0a1c1')
 guard=rd(B+'/git_index_guard.json','d1c0aac04f8e02d787098361525e707ab6bb7817b08c923d286dee45ac3b00da')
 delivery=rd(B+'/git_delivery.json','e7f6cd6929b678556a9f246e0a57be2834cbf0dc567fc694054fa5d2a9d8ea5b')
 tr='results/formal_main_v2/control_transport/heartbeat_1317_delivery.jsonl'
 assert h(R/tr)=='c845a9aed7e9cc50726d3852a1b00ab7c8365895c26c9c0f7cb57401508130aa'
 ended=json.loads((R/tr).read_bytes().splitlines()[-1]);assert ended['returncode']==1 and ended['source173_and_entrypoint_unchanged']
 head=git('rev-parse','HEAD').decode().strip()
 assert len(head)==40 and head not in [BASE,old['commit']]
 assert git('rev-list','--parents','-n','1',head).decode().strip().split()==[head,BASE]
 assert not git('diff','--cached','--name-only').strip()
 names=git('diff-tree','--no-commit-id','--name-only','-r','-z',BASE,head).decode().split('\0');names={x for x in names if x}
 rows=req['files']+[ref(B+'/'+n) for n in ['git_required_files.json','git_index_guard.json','git_whitespace_diagnostic.json','git_delivery.json']]
 assert len({r['path'] for r in rows})==len(rows) and names=={r['path'] for r in rows}
 assert guard['status']=='verified_index_archive_delivery' and guard['frozen_files_verified_in_worktree_and_index']==173 and delivery['baseline']==BASE
 assert delivery['new_root_GPU_submissions']==['3049622','3049632','3049657','3049679'] and delivery['new_development_trials_accepted']==800
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())
 assert not (names & set(inventory['files']))
 process=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 verified_bytes=0
 try:
  for row in rows:
   name=row['path'];assert '\n' not in name and '\r' not in name
   process.stdin.write((head+':'+name+'\n').encode());process.stdin.flush()
   header=process.stdout.readline().decode().strip().split();assert len(header)==3 and header[1]=='blob',name
   size=int(header[2]);assert size==row['bytes'],name
   digest=hashlib.sha256();remaining=size
   while remaining:
    block=process.stdout.read(min(1<<20,remaining));assert block,name
    digest.update(block);remaining-=len(block)
   assert process.stdout.read(1)==b'\n' and digest.hexdigest()==row['sha256'],name
   verified_bytes+=size
  process.stdin.close();error=process.stderr.read();assert process.wait(timeout=30)==0 and not error
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=30)
 assert h(sp)==state_before and not git('diff','--cached','--name-only').strip()
 out='.local/git_commit_20261020T1317.json'
 receipt=dict(status='existing_successful_commit_verified_after_receipt_name_collision',utc=datetime.now(timezone.utc).isoformat(),
  commit=head,baseline=BASE,files=len(rows),committed_files_sha256_verified=len(rows),committed_bytes_verified=verified_bytes,
  original_index_guard=ref(B+'/git_index_guard.json'),required_files=ref(B+'/git_required_files.json'),delivery=ref(B+'/git_delivery.json'),
  original_control_end=ref(tr),preserved_old_receipt=ref('.local/git_commit_1317.json'),
  failure_phase='Only post-commit receipt open(x); commit itself was already successful.',new_Git_commits=0,new_GPU_jobs=0,
  index_empty=True,shared_state_unchanged=True,weights_added=False,sealed_final_values_added=False,
  root_complete=64,accepted_development_trials=800,current_action_development_trials=2800)
 with (R/out).open('x') as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(status=receipt['status'],commit=head,files=len(rows),receipt=ref(out))),flush=True)
