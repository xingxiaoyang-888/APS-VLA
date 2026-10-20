"""Seal author-private 4-plan candidates after root publication; no admission or submission."""
from pathlib import Path
import hashlib,json,argparse
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong64_development_plans_20261020T1530';A=D/'attempt01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
def get(rel,pin):
 p=R/rel;assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(R);assert sha(p)==pin;return json.loads(p.read_text())
def put(name,value):
 p=D/name
 with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
def main():
 ap=argparse.ArgumentParser()
 for name in ['manifest-publication-ref','manifest-publication-sha','config-publication-ref','config-publication-sha']:ap.add_argument('--'+name,required=True)
 args=ap.parse_args();get(args.manifest_publication_ref,args.manifest_publication_sha);get(args.config_publication_ref,args.config_publication_sha)
 report=json.loads((A/'candidate_review.json').read_text());assert report['status']=='original_science_CPU_prepared_new_runtime_readiness_pending' and report['total_planned_trials']==800 and report['new_GPU_seconds']==0
 assert len(report['plans'])==4 and all(x['trials']==200 and x['original_P_scientific_wrapper_verify_passed'] and not x['new_P_wrapper_verify_passed'] for x in report['plans'])
 assert sha(A/'state_at_planning.json')==sha(D/'state_at_planning.json')=='86d2c2ad011cbb52c7367cc93703f67ad6449bb74548fd9a98955244c7658355'
 inputs=[]
 for plan in report['plans']:
  sub=A/plan['group_key'];assert plan['group_key']==f"{plan['suite']}_k{plan['budget']}_seed{plan['seed']}" and plan['budget']==64 and plan['seed'] in [17,41] and plan['suite'] in ['libero_spatial','libero_object']
  inputs.append({**plan,'plan_arguments':ref(sub/'plan_arguments.json'),'candidate_scientific_plan':ref(sub/'scientific_plan.json'),'candidate_effective_plan':ref(sub/'effective_plan.json'),'candidate_action_execution_contract':ref(sub/'execution_contract.json'),'draft_readiness':ref(sub/'runtime_readiness_draft.json'),'draft_authorization':ref(sub/'submission_authorization_draft.json'),'prepared_template':ref(sub/'prepared_invocation_template.json'),'dependency_closure':ref(sub/'runtime_dependency_closure.json')})
 transports=[];(D/'transport_logs').mkdir(exist_ok=False)
 for tag in ['manifests_v1','preview_v1','prepare_v1']:
  source=R/f'results/formal_main_v2/control_transport/nonLong64_development_plans_20261020T1530_{tag}.jsonl';raw=source.read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
  assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==0 and rows[-1]['source173_and_entrypoint_unchanged'] is True
  target=D/'transport_logs'/source.name
  with target.open('xb') as f:f.write(raw)
  transports.append({'original':ref(source),'private_exact_copy':ref(target),'returncode':0,'wall_seconds':(rows[-1]['time_ns']-rows[0]['time_ns'])/1e9})
 handoff=put('handoff.json',{'schema':'formal_main_v2','kind':'four64_development_author_CPU_handoff','status':'exact_author_plans_pending_root_and_independent_readiness_not_submission','candidate_review':ref(A/'candidate_review.json'),'publication_map':ref(A/'publication_map.json'),'immutable_state_snapshot':ref(A/'state_at_planning.json'),'state_origin':ref(D/'state_source.json'),'manifest_publication':{'path':args.manifest_publication_ref,'sha256':args.manifest_publication_sha},'original_P_dependency_publication':{'path':args.config_publication_ref,'sha256':args.config_publication_sha},'training_and_duplicate_checks':ref(D/'training_and_duplicate_checks.json'),'input_dependency_preview':ref(A/'dependency_preview_v1/required_P_copies.json'),'per_plan_inputs':inputs,'exact_original_entrypoints':report['source_files'],'planned_future_trials':800,'unique_initial_states_per_suite':100,'scientific_trials_added':0,'all_draft_gate_values_unapproved':True,'actual_new_P_wrapper_verify_done':False,'actual_GPU_runtime_chain_verified':False,'weights_or_sealed_values_read':False,'production_files_modified_by_author':False,'state_Git_Slurm_modified':False,'excluded_pairs':['libero_spatial_k64_seed23','libero_object_k256_seed23','all libero_goal'],'minimum_root_work':['Publish exact 12 static scientific/effective/action-contract candidates to R/P under shared writer discipline.','Independent current per-plan source/input/consumer audit.','Root genuine per-plan readiness, exact prepared invocation and full actual P action wrapper check-only, followed by independent post-readiness review.','Fresh controller/lease/pending/eight-slot reconciliation, root one-use authorization and single gateway submission.','Original whole-chain consumer plus independent terminal audit; unchanged final/O2A gates.'],'boundaries':['4 pairs each A/B only, 200 trials each; same 100 development states per suite.','Normal scientific configuration, action_v1, once hard Top-k, equal camera budgets, common packing, one policy call and no future head unchanged.','No complete-matrix success-rate claim; existing Goal hold and Object/Spatial history blockers unchanged.','Preparation never grants submission or final release.'],'transport_records':transports,'CPU_cost':{'new_GPU_seconds':0,'preparation_CPU_seconds':report['CPU_process_seconds'],'transport_wall_seconds':sum(x['wall_seconds'] for x in transports)}})
 files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json']
 m=put('delivery_manifest.json',{'schema':'formal_main_v2','kind':'four64_development_author_CPU_delivery','files':files,'publication_allowed':False,'author_candidate_only':True,'GPU_calls':0})
 print(json.dumps({'manifest':m,'handoff':handoff,'review':ref(A/'candidate_review.json'),'publication':ref(A/'publication_map.json')}))
if __name__=='__main__':main()
