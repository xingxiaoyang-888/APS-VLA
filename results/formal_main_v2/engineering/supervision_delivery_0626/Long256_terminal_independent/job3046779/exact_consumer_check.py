"""Consume the genuine published root result with the exact versioned consumer."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys,copy,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py';R_SHA='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py';C_SHA='16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'
ROOTREF='results/formal_main_v2/downstream_reviews/3046779.json';INV='results/formal_main_v2/invocations/libero_10_development_5185766bb353c8e6_attempt01.json';I_SHA='94f108d569f8b35e5f14abe9c84dc03da38b5f0d1ad311f0fb293fcbf0e4dd4f'
BASE='results/formal_main_v2/libero_10/downstream/development/5185766bb353c8e6/attempt01'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root-sha256',required=True);args=p.parse_args()
 assert sha((R/REVIEWER).read_bytes())==R_SHA and sha((R/CONSUMER).read_bytes())==C_SHA
 spec=importlib.util.spec_from_file_location('Long3046779_actual_reviewer',R/REVIEWER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 evidence=m.Evidence(R);rootref={'path':ROOTREF,'sha256':args.root_sha256};saved=evidence.read_ref(rootref)
 assert saved['job_id']=='3046779' and saved['stage']=='development' and saved['suite']=='libero_10' and saved['invocation_ref']=={'path':INV,'sha256':I_SHA}
 current=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());job=next(x for x in current['registered_jobs'] if x['job_id']=='3046779')
 snapjob=next(x for x in saved['registered_jobs_at_review'] if x['job_id']=='3046779');assert snapjob==job
 assert (job['status'],job['exit_code'],job['elapsed_seconds'],job['gpus'])==('COMPLETED','0:0',2937,1)
 consumer=m.load(evidence,CONSUMER,C_SHA)
 reconstructed=consumer.review_downstream_output(evidence,rootref,expected_stage='development',suite='libero_10',run_root=str(P/BASE))
 assert reconstructed['scientific_complete'] is True and reconstructed['completed_trials']==reconstructed['expected_trials']==200
 assert reconstructed['raw_invocation_job_ids']==['3046779'] and reconstructed['historical_transition'] is None
 assert reconstructed['unfinished_attempts_unknown_cost']==0 and reconstructed['final_release'] is False
 assert reconstructed['cost']['current_gpu_seconds']==reconstructed['cost']['all_attempt_gpu_seconds']==2937
 assert len(reconstructed['cost']['allocations'])==1
 directpath=D/'direct_raw_audit_a1.json';assert sha(directpath.read_bytes())=='364a86aedd4516d367af408181ce00b50ff8acfcfe4704fbba25b12ed7c294aa';direct=json.loads(directpath.read_bytes())
 sm=reconstructed['reconstructed_summary']
 assert {mid:v['successes'] for mid,v in sm['methods'].items()}==direct['successes']
 assert sm['cost']['policy_calls_total']==direct['raw_policy_calls']==6750
 assert sm['unique_initial_states']==direct['unique_development_initial_states']==100
 # Formal pull files must be byte-identical to independently checked completed P artifacts.
 cross=[]
 for path,obs in direct['read_files'].items():
  q=Path(path)
  if q.is_relative_to(P/BASE):
   rel=q.relative_to(P).as_posix()
   assert evidence.watch(rel)==obs['sha256']
   assert sha(q.read_bytes())==obs['sha256']
   assert (R/rel).stat().st_size==obs['bytes']
   cross.append({'relative':rel,**obs})
 assert len(cross)==7
 # Source/identity and closure consumers never read a checkpoint or sealed value.
 assert not any(Path(x).suffix in {'.pt','.pth','.safetensors','.bin','.init','.pruned_init'} for x in evidence.files)
 evidence.unchanged()
 result={'schema':'formal_main_v2','kind':'Long3046779_independent_exact_consumer_verification','status':'passed_actual_terminal_development_only',
  'utc':datetime.now(timezone.utc).isoformat(),'root_review':rootref,'reviewer_source_sha256':R_SHA,'consumer_source_sha256':C_SHA,
  'exact_published_consumer_used':True,'consumer_or_validator_modified':False,'reconstructed_root_equal_except_reviewed_utc':True,
  'actual_current_job_equals_immutable_terminal_snapshot':True,'root_result':{k:reconstructed[k] for k in ['schema','kind','status','execution_version','job_id','stage','suite','scientific_complete','completed_trials','expected_trials','cost','raw_invocation_job_ids','action_semantics_sha256','actual_runtime_review','historical_transition','offline_validator_derivation']},
  'direct_raw_ref':{'path':directpath.relative_to(R).as_posix(),'sha256':sha(directpath.read_bytes())},
  'actual_R_P_direct_raw_matches':cross,'evidence_sha256':evidence.files,
  'weights_loaded':False,'sealed_values_read':False,'state_modified':False,'Slurm_submitted':False,'P_modified':False,
  'final_release':False,'O2A_latency_verified':False,'whole_suite_22_methods_complete':False,
  'limits':['This verifies only fresh Long A256/B256 seed17 200 development trials under the new runtime.','It does not equate old legacy-prefix results with new action semantics, open final states or prove a success-latency improvement.']}
 print(json.dumps({'receipt':save('exact_consumer_verification_a1.json',result),'evidence_count':len(evidence.files),'complete':True}))
if __name__=='__main__':
 try:main()
 except Exception as e:
  failure={'status':'failed_no_source_modified','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  save('exact_consumer_failure_a1.json',failure);print(json.dumps(failure));raise
