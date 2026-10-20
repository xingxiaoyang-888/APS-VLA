"""Supplement: test unchanged original failed-file ownership consumer, no deployment."""
from pathlib import Path
import importlib.util,sys,json,copy,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/object_bridge_independent_20261020T1644'
p=D/'audit_bridge_v2.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='28d671f46ca30878f15bd346f21b6afc601290230e1415bd0e940be7b1f7123e'
sp=importlib.util.spec_from_file_location('object23_independent_common',p);m=importlib.util.module_from_spec(sp);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
m.D=D/'attempt02/ownership_supplement';m.D.mkdir(exist_ok=False)
try:
 bridge=m.load(m.E/'bridge_v2.py','8785b42fe62dd513f796871875547c894de972516ac9762ad60a89d3df9a7c8e');policy=bridge.policy();ref=policy['references']['final_root'];saved=m.rd(ref['path'],ref['sha256'])
 jobs={j['job_id']:j for j in saved['registered_pair_jobs_at_review']};last=jobs['3042627'];candidates=[]
 for path,pin in saved['evidence_sha256'].items():
  if path.startswith('results/formal_main_v2/pulls/') and path.endswith('/receipt.json'):
   doc=m.rd(path,pin)
   if any(x.get('job_id')=='3042627' and x.get('include_run_root') is True for x in doc['selected_jobs']):candidates.append(path)
 m.check(len(candidates)==1,'exact original last-job pull');receipt=candidates[0]
 ownref=policy['references']['ownership_verifier'];own=m.load(ownref['path'],ownref['sha256'])
 required=list(saved['files']);failure_history=saved['startup_failure_history']
 expected=own.require_pulled_startup_ownership(m.Evidence(),receipt,last,required,jobs,failure_history)
 m.check(expected==saved['startup_pull_ownership'] and len(expected)==3 and set(expected.values())=={'3028460'},'actual original ownership consumer retains exact three external failed files')
 external=sorted(expected);target=external[0]
 class Overlay(m.Evidence):
  def __init__(self,fn):super().__init__();self.fn=fn
  def read(self,n):
   value=super().read(n);rel=self.path(n).relative_to(R).as_posix()
   return self.fn(rel,copy.deepcopy(value))
 def mutate_receipt(fn):
  def op(path,value):
   if path==receipt:fn(value)
   return value
  return op
 cases=[
 ('external failure reassigned current job',lambda d:next(x for x in d['files'] if x['relative']==target).update(job_ids=['3042627'])),
 ('failed allocation removed selected_jobs',lambda d:d.update(selected_jobs=[x for x in d['selected_jobs'] if x['job_id']!='3028460'])),
 ('failed allocation accounting omitted',lambda d:d['accounting_after']['jobs'].pop('3028460')),
 ('failure billing changed',lambda d:d['accounting_after']['jobs']['3028460'].update(elapsed_seconds=0)),
 ('external unpublished action',lambda d:next(x for x in d['files'] if x['relative']==target).update(action='pending')),
 ('external wrong server path',lambda d:next(x for x in d['files'] if x['relative']==target).update(path='/wrong')),
 ('external wrong length',lambda d:next(x for x in d['files'] if x['relative']==target).update(bytes=1)),
 ('external wrong hash',lambda d:next(x for x in d['files'] if x['relative']==target).update(sha256='0'*64)),
 ('pull incomplete missing',lambda d:d.update(missing=['synthetic_missing'])),
 ('failed pull omitted run root',lambda d:next(x for x in d['selected_jobs'] if x['job_id']=='3028460').update(include_run_root=False)),
 ('failed pull active overlap',lambda d:next(x for x in d['selected_jobs'] if x['job_id']=='3028460').update(active_overlapping_job_ids=['synthetic']))]
 for name,fn in cases:
  ev=Overlay(mutate_receipt(fn));m.negative(name,lambda ev=ev:own.require_pulled_startup_ownership(ev,receipt,last,required,jobs,failure_history))
 m.negative('failed external file missing required set',lambda:own.require_pulled_startup_ownership(m.Evidence(),receipt,last,[n for n in required if n!=target],jobs,failure_history))
 m.negative('unexpected extra owner in bridge receipt',lambda:bridge.pull_with_original_ownership(m.Evidence(),saved={**saved,'startup_pull_ownership':{}},job=last,shared=own._shared,required=required,receipt=receipt),'only exact final startup-aware pull allowed')
 report={'schema':'formal_main_v2','kind':'independent_source_ownership_semantic_negative_supplement','status':'passed','checks':len(m.CHECKS),'negative_cases':len(m.NEG),'actual_original_receipt':{'path':receipt,'sha256':m.h((R/receipt).read_bytes())},'exact_retained_failed_owners':expected,'original_verifier':ownref,'candidate_code_changed':False,'synthetic_method':'read-only in-memory overlay of genuine receipt after its real hash read, deliberately testing downstream semantic validation independently from the earlier cryptographic pin; never published as real evidence','production_writes':False,'Slurm_calls':0,'GPU_runs':0,'weights_or_final_states_read':False}
 m.write('checks.json',m.CHECKS);m.write('negative_cases.json',m.NEG);m.write('input_hashes.json',m.READS);m.write('independent_review.json',report)
 print(json.dumps(report))
except BaseException as e:
 import traceback
 m.write('failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':m.CHECKS,'negative_cases':m.NEG});raise
