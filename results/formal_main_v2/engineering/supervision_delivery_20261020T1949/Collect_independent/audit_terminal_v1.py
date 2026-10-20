from __future__ import annotations
from pathlib import Path
import sys,hashlib,importlib.util,json,traceback,argparse
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/collect_terminal_independent_20261020T1949')
p=D/'audit_raw_v1.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='07fe8b598f495d25ed0e0aebc651def88679ae8a794afceeb717a7f6581d339f'
spec=importlib.util.spec_from_file_location('collect_raw_independent_reused',p);a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
R,P,S=a.R,a.P,a.S
check,read,digest,ref,save,sig=a.check,a.read,a.digest,a.ref,a.save,a.sig
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py';CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'
def load(name,rel):
 spec=importlib.util.spec_from_file_location(name,R/rel);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
clean=lambda d:{k:v for k,v in d.items() if k!='reviewed_utc'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--spatial-root-sha',required=True);ap.add_argument('--object-root-sha',required=True);args=ap.parse_args()
 for rel,h in a.PINS.items():check(digest(R/rel)==h,'original dependency:'+rel)
 raw=read(D/'raw_observation_review.json');check(digest(D/'raw_observation_review.json')=='944740a98a1e92ffa5bb2816b48550bf36059160804339b183696295587d5ccf' and raw['status']=='passed_raw_observation_checks_not_terminal_acceptance','prior independent raw evidence exact')
 filemap=read(D/'P_raw_files.json')['files']; rawmaps={x['relative']:x for x in filemap}
 sys.path.insert(0,str(S/'src'))
 from cti_vla.evaluation import formal_profiling
 check(Path(formal_profiling.__file__).resolve()==S/'src/cti_vla/evaluation/formal_profiling.py','frozen S source imported')
 reviewer=load('collect_action_reviewer_independent_1949',REVIEWER);consumer=load('collect_action_consumer_independent_1949',CONSUMER)
 reports=[];allpulls={};allregjobs=[]
 for item,rootsha in zip(a.JOBS,[args.spatial_root_sha,args.object_root_sha]):
  suite,jid=item['suite'],item['job'];rr='results/formal_main_v2/downstream_reviews/'+jid+'.json'
  check(digest(R/rr)==rootsha,suite+' exact original root result')
  root=read(R/rr);check(root['status']=='passed' and root['scientific_complete'] is True and root['reviewed_by']=='root' and root['stage']=='collect' and root['suite']==suite,suite+' root scope')
  jobs=root['registered_jobs_at_review'];mine=[j for j in jobs if str(j['job_id'])==jid];check(len(mine)==1,suite+' unique job record');job=mine[0];allregjobs.append(job)
  check(job['status']=='COMPLETED' and job['exit_code']=='0:0' and job['elapsed_seconds']==item['seconds'] and job['gpus']==1,suite+' immutable registered terminal fact')
  check([str(j['job_id']) for j in jobs if j.get('stage_key')==job['stage_key']]==[jid],suite+' no other prior/current duplicate allocation')
  C='results/formal_main_v2/execution/'+item['prefix']+'_collect_action_v1_20261020T1825/'
  IN='results/formal_main_v2/invocations/'+suite+'_collect_648ce4233e78353e_attempt01.json';Orel='results/formal_main_v2/'+suite+'/downstream/collect/648ce4233e78353e/attempt01'
  check(job['invocation']==IN and job['invocation_sha256']==item['inv'] and job['run_root']==str(P/Orel),suite+' registered original invocation/output')
  check(job['execution_contract']==ref(C+'execution_contract.json') if 'execution_contract' in job else job['action_execution_contract']==ref(C+'execution_contract.json'),suite+' original contract identity')
  pref=root['pull_ref'];check(digest(R/pref['path'])==pref['sha256'],suite+' root-bound original pull bytes');pull=read(R/pref['path'])
  check(pull['status']=='verified_nonweight_snapshot' and pull['final_evidence'] is True and pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False and not pull['missing'] and not pull['excluded'],suite+' complete genuine terminal nonweight pull')
  check(jid in pull['requested_job_ids'] and set(pull['requested_job_ids'])<=set(x['job'] for x in a.JOBS),suite+' pull exact authorized jobs')
  if pref['path'] not in allpulls:
   names=set()
   for f in pull['files']:
    path=f['relative'];check(path not in names,'pull unique path:'+path);names.add(path)
    check(digest(R/path)==digest(P/path)==f['sha256'] and (R/path).stat().st_size==(P/path).stat().st_size==f['bytes'],'pull exact original P/R:'+path)
   allpulls[pref['path']]=pref
  pm={f['relative']:f for f in pull['files']}
  for path,f in rawmaps.items():
   if path.startswith(Orel+'/'):check(pm[path]['sha256']==f['sha256'] and pm[path]['bytes']==f['bytes'],suite+' independent raw bytes included:'+path)
  rebuilt=reviewer.review(R,job=job,invocation_ref=ref(IN),pull_ref=pref,registered_jobs=jobs,expected_contract_ref=ref(C+'execution_contract.json'))
  check(clean(rebuilt)==clean(root),suite+' original reviewer full reconstruction equal except time')
  evidence=reviewer.Evidence(R);consumed=consumer.review_downstream_output(evidence,ref(rr),expected_stage='collect',suite=suite,run_root=job['run_root'])
  check(clean(consumed)==clean(rebuilt),suite+' original consumer reconstructs original source/adapter/trajectories')
  evidence.unchanged()
  check(rebuilt['observations']==30 and rebuilt['completed_collection_trajectories']==10 and rebuilt['scientific_complete'] is True,suite+' actual complete collection only')
  for key in ['weights_read','final_state_values_read','final_release','old_report_or_invocation_fabricated']:check(rebuilt[key] is False,suite+' boundary:'+key)
  cost=rebuilt['cost'];check(cost['current_gpu_seconds']==cost['all_attempt_gpu_seconds']==item['seconds'] and len(cost['allocations'])==1 and str(cost['allocations'][0]['job_id'])==jid,suite+' all allocations exactly once')
  prior=next(x for x in raw['jobs'] if x['job_id']==jid)
  check(rebuilt['known_policy_calls']==prior['policy_calls'],suite+' raw and original reviewer policy counts match')
  for path,h in rebuilt['evidence_sha256'].items():check(digest(R/path)==h,suite+' reconstructed evidence exact:'+path)
  proof=dict(original_reviewer_source=ref(REVIEWER),original_consumer_source=ref(CONSUMER),root_receipt=ref(rr),reviewer_equal_except_reviewed_utc=True,consumer_equal_except_reviewed_utc=True,canonical_rebuilt_without_time_sha256=sig(clean(rebuilt)),evidence_sha256=rebuilt['evidence_sha256'],actual_runtime_review=rebuilt['actual_runtime_review'],cost=cost,pull_ref=pref)
  save(jid+'_reconstruction_proof.json',proof)
  report=dict(schema='formal_main_v2',kind='independent_collect_terminal_review',status='passed',reviewed_by='independent',job_id=jid,suite=suite,stage='collect',scientific_complete=True,scope='Fixed dense collect panel only; no scientific success-trial addition and no O2A or component timing result',root_review=ref(rr),pull_receipt=pref,invocation=ref(IN),action_execution_contract=ref(C+'execution_contract.json'),panel=prior['panel'],observations=30,collection_trajectories=10,collection_control_steps=prior['control_steps'],collection_policy_calls=prior['policy_calls'],tasks=prior['tasks'],cost=cost,scientific_success_trials_added=0,new_success_trials=0,O2A_measurements_produced=False,latency_samples_added=0,final_release=False,sealed_values_read=False,weight_bytes_read=False,models_loaded=False,production_or_state_or_Git_writes=False,Slurm_queries=False,original_reviewer_and_consumer_both_executed=True,prior_independent_raw_review=dict(path=str((D/'raw_observation_review.json').relative_to(R)),sha256=digest(D/'raw_observation_review.json')),reconstruction_proof=dict(path=str((D/(jid+'_reconstruction_proof.json')).relative_to(R)),sha256=digest(D/(jid+'_reconstruction_proof.json'))))
  save(jid+'_independent_review.json',report);reports.append(dict(job_id=jid,suite=suite,independent_review=dict(path=str((D/(jid+'_independent_review.json')).relative_to(R)),sha256=digest(D/(jid+'_independent_review.json'))),root_review=ref(rr),observations=30,gpu_seconds=item['seconds']))
 inventory=read(R/a.I)
 for rel,h in inventory['files'].items():check(digest(R/rel)==digest(S/rel)==h,'frozen source unchanged at exit:'+rel)
 for path,h in a.watched.items():check(digest(path)==h,'immutable input unchanged:'+path)
 save('terminal_independent_index.json',dict(schema='formal_main_v2',kind='independent_collect_terminal_index',status='passed',reviewed_by='independent',checks_passed=len(a.checks),checks=a.checks,jobs=reports,observations=60,collection_trajectories=20,gpu_seconds=723,gpu_hours=723/3600,scientific_success_trials_added=0,latency_samples_added=0,final_release=False,frozen_files_unchanged=173,original_reviewer_and_consumer_both_executed=True,production_or_state_or_Git_writes=False,Slurm_queries=False,root_Slurm_observation=ref(a.OBS),pull_receipts=list(allpulls.values()),utc=a.datetime.now(a.timezone.utc).isoformat()))
 print(json.dumps(dict(status='passed',checks=len(a.checks),jobs=reports,index_sha256=digest(D/'terminal_independent_index.json'))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  save('terminal_failure_v1.json',dict(status='failed',type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks_passed=len(a.checks)));raise
