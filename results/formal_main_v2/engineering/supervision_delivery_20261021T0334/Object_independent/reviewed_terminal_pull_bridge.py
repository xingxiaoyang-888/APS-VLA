"""Read-only, exact four-journal supplement for Object3054409 terminal review.
The original runtime, invocation, 600-cell guards and reviewer source stay exact.
No execution, scheduler mutation, retry, or final-release authority is provided.
"""
from pathlib import Path
from contextlib import contextmanager
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
PKG='scripts/ops/formal_object_single_error_v1'
REVIEW_SHA='c0aa1fc3d7c1607032897d7eede009bb989753daf58911d2b3351b4df7a030a2'
OLD_SHA='753edb55ce21fd43f85499e136a7e52093ecf9feaeafadf0f01cece8fa267202'
PULL='results/formal_main_v2/pulls/terminal_object_20261021T0334/receipt.json'
PULL_SHA='1ab834c09cc562f4fce9224bf98bc6c80d31dbaadcb6a3381c877c1395aad710'
ANALYSIS='results/formal_main_v2/preflight/heartbeat_20261021T1134/terminal_analysis_supervisor_projection.json'
ANALYSIS_SHA='28972a53a01b3bf21e7c2194fe8b7fd31106fd49ed47290beb1a4f871d363513'
JOURNAL='results/formal_main_v2/object_single_error_invocations/3054409/'
FOUR={
 JOURNAL+'action_events.jsonl':('8d40ed3c6498afb6ccd1977f2e6c47ad99705d6b7da310a54db825082ae69ac6',82644),
 JOURNAL+'completion.json':('3fd481e5d668493e632cd6d13b6d61e89be0fc13935ceaa0c59e4ba52b2ef0ec',2549),
 JOURNAL+'identity.json':('a14952078ee5f92ae24d2b23721e0d03e6e39216e80408365b2a7202fb4c336d',11097),
 JOURNAL+'iterator_events.jsonl':('c9427297ac267597f3a8445ea2c40f04d436d664e091b932d8d41e129230e86d',12434)}
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pinned(rel,pin):
 p=R/rel;require(p.resolve()==p and p.is_file() and sha(p)==pin,'changed pinned terminal evidence:'+rel);return p
def extend_verified(original,evidence,scheduler,job,pull_path,jobs):
 """First run all original pull guards, then verify precisely four missing rows."""
 require(job.get('job_id')=='3054409' and pull_path==PULL,'only original completed Object single correction')
 result=original(evidence,scheduler,job,pull_path,jobs)
 require(evidence.watch(PULL)==PULL_SHA,'exact terminal pull receipt')
 pull=evidence.read(PULL)
 base=str(Path(PULL).parent)
 before=evidence.read(base+'/inventory_before.json');after=evidence.read(base+'/inventory_after.json')
 require(before==after and evidence.watch(base+'/inventory_before.json')==pull['inventory_sha256'],'stable actual source inventory')
 rows={x['relative']:x for x in pull['files']};initial={x['relative']:x for x in before['files']}
 require(len(rows)==len(pull['files'])==13 and len(initial)==len(before['files'])==13,'exact unique 13-file pull')
 require(len(result['files'])==9 and set(result['files']).isdisjoint(FOUR)
  and set(rows)==set(initial)==set(result['files'])|set(FOUR),'nine original files plus four specific journals only')
 for when in ('accounting_before','accounting_after'):
  actual=pull[when]['jobs']['3054409']
  require(actual['status']=='COMPLETED' and actual['exit_code']=='0:0' and actual['elapsed_seconds']==326 and actual['gpus']==1,'exact completed allocation')
 verified=dict(result['files'])
 for rel,(digest,size) in FOUR.items():
  a=rows[rel];b=initial[rel];path=evidence.path(rel)
  require(path==R/rel and path.resolve()==path and not path.is_symlink(),'canonical local journal path')
  for item in (a,b):
   require(item['relative']==rel and item['path']==str(P/rel) and item['job_ids']==['3054409']
    and item['sha256']==digest and item['bytes']==size,'exact journal transfer/identity/size')
  require(a['action'] in ('downloaded_verified','same_sha_skipped'),'journal actually copied and checked')
  require(path.stat().st_size==size and evidence.watch(rel)==digest and sha(P/rel)==digest
   and (P/rel).stat().st_size==size,'same actual P/R journal bytes')
  verified[rel]=digest
 return dict(result,files=verified)
@contextmanager
def original_context():
 pinned(PKG+'/reviewer.py',REVIEW_SHA);pinned('scripts/review_formal_downstream.py',OLD_SHA)
 pinned(ANALYSIS,ANALYSIS_SHA);pinned(PULL,PULL_SHA)
 sys.path.insert(0,str(S/'src'));sys.path.insert(0,str(R/PKG))
 # Exact production module filename is part of marshal(code,2). Preload S,
 # not a replacement implementation. Both source bytes remain pinned by review.
 from cti_vla.evaluation import formal_trials
 require(Path(formal_trials.__file__)==S/'src/cti_vla/evaluation/formal_trials.py','fresh original production import context required')
 spec=importlib.util.spec_from_file_location('_object_terminal_original_0334',R/PKG/'reviewer.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 old=module.validators(project=R)[0];saved=old.pulled_candidate
 def supplemented(evidence,scheduler,job,pull_path,jobs):
  return extend_verified(saved,evidence,scheduler,job,pull_path,jobs)
 old.pulled_candidate=supplemented
 try:yield module
 finally:old.pulled_candidate=saved
 require(old.pulled_candidate is saved and sha(R/PKG/'reviewer.py')==REVIEW_SHA and sha(R/'scripts/review_formal_downstream.py')==OLD_SHA,'original source/binding restored')
def envelope(original):
 return dict(schema='formal_main_v2',kind='Object3054409_exact_terminal_pull_bridge_review',
  status='passed_pending_root_and_independent_acceptance',job_id='3054409',
  original_review=original,original_reviewer_sha256=REVIEW_SHA,original_pull_guard_source_sha256=OLD_SHA,
  bridge_source_sha256=sha(Path(__file__)),source_import_context=str(S/'src'),
  original_consumer_guards_retained=True,supplemental_journal_rows={p:dict(sha256=h,bytes=n) for p,(h,n) in FOUR.items()},
  original_9_file_pull_checks_not_skipped=True,analysis_projection=dict(path=ANALYSIS,sha256=ANALYSIS_SHA),
  pull_receipt=dict(path=PULL,sha256=PULL_SHA),science_changed=False,new_GPU_jobs=0,
  scientific_acceptance_by_this_function=False,final_release=False)
def review():
 with original_context() as module:
  result=module.review('3054409',PULL,project=R,state=json.loads((R/ANALYSIS).read_text()))
 return envelope(result)
def consume(reference):
 p=pinned(reference['path'],reference['sha256']);saved=json.loads(p.read_text())
 require(saved.get('kind')=='Object3054409_exact_terminal_pull_bridge_review','exact saved terminal bridge receipt')
 with original_context() as module:
  # Original consume reexecutes its complete original review with only the
  # same four-row evidence projection supplement in scope.
  original=module.consume(saved['original_review'],job_id='3054409',pull_receipt=PULL,project=R,state=json.loads((R/ANALYSIS).read_text()))
 rebuilt=envelope(original);require(saved==rebuilt,'complete original consumer reconstruction differs');return rebuilt
