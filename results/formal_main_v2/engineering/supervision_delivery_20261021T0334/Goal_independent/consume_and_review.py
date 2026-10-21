from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).parent
OUT='results/formal_main_v2/engineering/goal_full200_20261021T0110/attempt01';PKG='scripts/ops/formal_goal_full200_gate_v1';N=0
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def yes(v,m):
 global N
 N+=1
 if not v:raise AssertionError(m)
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def checked(rel,pin):
 p=R/rel;yes(p.resolve()==p and p.is_relative_to(R),'canonical input path');yes(h(p)==pin,'pinned input '+rel);return p
def main():
 ap=argparse.ArgumentParser()
 for n in ['review','review_sha256','terminal','terminal_sha256','pull','pull_sha256']:ap.add_argument('--'+n.replace('_','-'),required=True)
 a=ap.parse_args()
 ref={'path':a.review,'sha256':a.review_sha256};rp=checked(a.review,a.review_sha256);tp=checked(a.terminal,a.terminal_sha256);pp=checked(a.pull,a.pull_sha256)
 rawp=D/'raw_reconstruction.json';yes(h(rawp)=='8dc6c2d7de239f7e4185e89ba728d6eba2bfe71cfcdf9c9f652d2bc2db1ae7f4','our independent raw reconstruction exact')
 raw=read(rawp);allow=read(D/'raw_blob_allowlist.json')
 cp=R/PKG/'consumer.py';yes(h(cp)=='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b','actual canonical consumer unchanged')
 spec=importlib.util.spec_from_file_location('goal3054717_actual_consumer_independent',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
 saved=read(rp);terminal=read(tp);pull=read(pp)
 yes(saved['terminal_ref']=={'path':a.terminal,'sha256':a.terminal_sha256},'saved review binds exact new terminal envelope')
 rebuilt=c.consume(R,ref)
 yes(rebuilt==saved,'full original consumer independently rebuilt every saved field once')
 write('canonical_consumer_reconstruction.json',rebuilt)
 scientific=rebuilt['full_original_scientific_consumer_reconstruction'];gate=rebuilt['raw_gate']
 yes(scientific['scientific_complete'] and scientific['completed_trials']==scientific['expected_trials']==200 and scientific['raw_invocation_job_ids']==['3054717'] and scientific['unfinished_attempts_unknown_cost']==0,'whole new200 actual original consumer complete no old-prefix substitute')
 yes(gate['trials']==200 and gate['paired_t0_checks']==100 and gate['queries']==raw['queries']==3027 and gate['control_steps']==raw['control_steps']==23508 and gate['warmup_steps']==2000,'canonical raw totals independently agree')
 yes(gate['complete_trial_end_witnesses']==200 and gate['complete_observation_phase_raw_rebuilt'] and gate['all_query_content_rebuilt_from_before_and_after_raw'],'all raw phases/trial/query integrity')
 projected={}
 for row in allow['files']:
  p=Path(row['path']);q=R/p.relative_to(P) if p.is_relative_to(P) else p
  projected[str(q)]={k:row[k] for k in ['sha256','bytes']}
 yes(projected==gate['raw_blob_refs'],'all35062 actual blob references exactly independently rebuilt with only P-to-R passive relocation')
 yes(rebuilt['allocation_gpu_seconds']==2205 and rebuilt['allocation_count']==1 and rebuilt['all_prior_allocations_retained_not_added_again'],'2205 GPU seconds charged exactly once')
 yes(rebuilt['runtime']['synthetic_input'] is False and rebuilt['runtime']['original_base_loads']==1 and rebuilt['runtime']['all_source_and_binding_contexts_restored'],'actual nofixture source/runtime restored')
 yes(rebuilt['explicit_adapter_parent_path_derivation']['only_parent_read_relocated_to_actual_typed_receipt'],'explicit original adapter parent read preserved')
 yes(rebuilt['original200_HOLD'] and not rebuilt['old_cause_identified'] and rebuilt['scientific_trials_accepted_by_this_function']==0 and not rebuilt['final_release'],'old200/cause/final scientific scope preserved')
 initial_path=checked('results/formal_main_v2/preflight/heartbeat_20261021T1134/initial_observation.json','0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41');initial=read(initial_path)
 obs=initial['projection']['observation'];rows=obs['rows'];job=rows['3054717']
 yes(job['status']=='COMPLETED' and job['exit_code']=='0:0' and job['gpus']==1 and job['elapsed_seconds']==2205,'independently pinned original Slurm terminal facts')
 yes(initial['formal_unique_allocations']==273 and initial['formal_GPU_seconds']==1994468 and initial['projection']['derived']['occupied']==[] and initial['projection']['derived']['findings']==[] and initial['projection']['derived']['unknown']==[],'global accounting273 total1994468 and no occupied/unknown')
 yes(terminal['job']['job_id']=='3054717' and terminal['job']['elapsed_seconds']==2205 and terminal['job']['gpus']==1 and terminal['job']['status']=='COMPLETED','terminal job exact saved Slurm identities')
 yes(terminal['weights_copied'] is False and terminal['sealed_values_read'] is False,'terminal exact nonweight nonsealed scope')
 artifact_map={row['path']:row for row in terminal['artifacts']}
 yes(len(artifact_map)==len(terminal['artifacts']),'pull artifact paths unique')
 for path,meta in raw['metadata'].items():
  p=Path(path)
  if p.is_relative_to(P/OUT):
   rel=p.relative_to(P).as_posix();yes(rel in artifact_map and artifact_map[rel]['sha256']==meta['sha256'] and artifact_map[rel]['bytes']==meta['bytes'],'independent original P metadata matches exact pull '+rel)
 yes(h(rp)==a.review_sha256 and h(tp)==a.terminal_sha256 and h(pp)==a.pull_sha256,'root immutable evidence remained same')
 report=dict(schema='formal_main_v2',kind='Goal_full200_3054717_independent_terminal_review',status='passed_new200_terminal_independent_review',reviewed_by='independent',reviewed_by_agent='/root/spatial588_recovery_audit_2054',blockers=[],
  new_real_terminal_rebuilt=True,not_inherited_old58_acceptance=True,canonical_consumer_sha256=h(cp),canonical_consumer_reconstruction_sha256=h(D/'canonical_consumer_reconstruction.json'),
  root_review=ref,terminal_manifest={'path':a.terminal,'sha256':a.terminal_sha256},pull_receipt={'path':a.pull,'sha256':a.pull_sha256},
  observation={'path':initial_path.relative_to(R).as_posix(),'sha256':h(initial_path)},raw_independent_report={'path':rawp.relative_to(R).as_posix(),'sha256':h(rawp)},
  independent_raw_checks=raw['checks'],crosscheck_count=N,trials=200,unique_development_states=100,paired_preB_checks=100,policy_queries=3027,executed_policy_steps=23508,wait_steps=2000,
  methods=raw['methods'],all_five_components_raw_byte_identity_verified=True,all_queries_before_after_input_identity_verified=True,all_actions_match_original_returned_chunk_and_ledger=True,complete_original_scientific_consumer=True,
  unique_blob_count=35062,unique_blob_bytes=raw['blob_bytes'],allocation_gpu_seconds=2205,allocation_count=1,old_engineering_allocations_not_recounted=True,
  old200_HOLD=True,other1000_HOLD=True,old_failure_cause_identified=False,root_scientific_acceptance_still_required=True,scientific_trials_accepted_by_auditor=0,
  no_claim_full_O2A_timing=True,final_sealed=True,new_Slurm_queries_by_auditor=0,new_GPU_submissions_by_auditor=0,canonical_state_Git_modified=False,
  limitation='Pass applies only to this new fixed200 execution and fully recorded actual input invariance; it does not explain missing historical q9 arrays or retroactively admit old200.')
 write('independent_terminal_review.json',report)
 print(json.dumps(dict(status=report['status'],review_sha256=h(D/'independent_terminal_review.json'),consumer_reconstruction_sha256=h(D/'canonical_consumer_reconstruction.json'),crosschecks=N)))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('consumer_reconstruction_failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),crosschecks_completed=N,scientific_admission=False));raise
