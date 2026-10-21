"""Root utility: generate private readiness/prepared invocations only AFTER real reviews.
Canonical R/P publication and any actual-P check belong to root; never submits.
"""
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_plans_20261021T0449/v2'
BUILDER_SHA='3d84ce954a5d6b3d74cbe430518b12bdba93fe25bc17631bf743cc75698b6ffa'
def load_builder():
 p=D/'build_plans.py';assert hashlib.sha256(p.read_bytes()).hexdigest()==BUILDER_SHA
 sp=importlib.util.spec_from_file_location('remaining5_builder',p);b=importlib.util.module_from_spec(sp);sys.modules[sp.name]=b;exec(compile(p.read_bytes(),str(p),'exec'),b.__dict__);return b
b=load_builder()
def expected_review(item,index,role):
 b.require(role in ('root','independent'),'review role')
 return dict(schema=b.ROUND,kind='Goal_remaining5_plan_'+role+'_review',status='passed',reviewed_by=role,pair_key=item['pair_key'],pair_id=item['pair_id'],execution_version='formal-downstream-action-v1',scientific_plan=item['scientific_plan'],effective_plan=item['effective_plan'],execution_manifest=item['execution_manifest'],source_provenance=item['source_provenance'],specification=item['specification'],original_builders=index['original_builders'],scientific_settings_changed=False,original_scientific_guards_preserved=True,production_chain_complete=True,production_chain_complete_meaning='Original metadata/source/consumer pre-execution closure only; not new GPU execution or typed runtime admission',actual_GPU_runtime_chain_verified=False,actual_new_runtime_P_verified=False,final_evaluation_enabled=False)
def validate_review(value,item,index,role,action_files):
 expected=expected_review(item,index,role)
 b.require(all(value.get(k)==v for k,v in expected.items()),'real exact '+role+' plan review required')
 b.require(value.get('runtime_sources')==action_files,'original action runtime closure differs')
 b.require(value.get('blockers')==[],'plan review contains blockers')
 b.require(isinstance(value.get('review_evidence'),dict) and value['review_evidence'],'actual review evidence references required')
 for label,ref in value['review_evidence'].items():
  b.require(isinstance(label,str) and isinstance(ref,dict) and set(ref)=={'path','sha256'},'review evidence must be exact references')
  p=R/ref['path'];b.require(ref['path'].startswith('results/formal_main_v2/') and '..' not in p.parts and not any('sealed' in x.lower() for x in p.parts),'canonical nonsealed review evidence only');b.no_links(p);b.require(b.sha(p)==ref['sha256'],'actual review evidence SHA differs')
 return True

def prepare(*,index_path,index_sha,pair_key,root_sha,independent_sha,prepared_utc):
 b.require(b.sha(index_path)==index_sha,'index SHA differs');index=json.loads(Path(index_path).read_bytes());b.require(pair_key in b.KEYS and set(index['pairs'])==set(b.KEYS),'fixed five-pair index')
 item=index['pairs'][pair_key];base=b.X+'/'+pair_key
 refs={role:dict(path=base+'/plan_'+role+'_review.json',sha256=pin) for role,pin in [('root',root_sha),('independent',independent_sha)]}
 def read(ref):
  p=R/ref['path'];b.no_links(p);b.require(b.sha(p)==ref['sha256'],'canonical R input differs');return json.loads(p.read_bytes())
 manifest=read(item['execution_manifest']);b.validate_scope(pair_key,manifest)
 contract=b.load('scripts/ops/formal_action_deployment_v1/contract.py');planner=b.load('scripts/ops/formal_downstream_supervisor.py');h=b.load('scripts/formal_execution_manifests.py')
 state=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());b.require(state.get('pending_submission') is None and state.get('autonomous_training_v1',{}).get('pending_submission') is None,'unresolved submission')
 scientific=planner.plan(b.args_for(pair_key),copy.deepcopy(state),project=R,helper=h)
 b.require(scientific==read(item['scientific_plan']),'published original scientific plan no longer rebuilds exactly')
 action=read(item['execution_contract']);effective=contract.effective_plan(scientific,scientific_plan_ref=item['scientific_plan'],execution_contract_ref=item['execution_contract'],execution_contract=action)
 b.require(effective==read(item['effective_plan']),'published effective envelope differs')
 for role in ('root','independent'):validate_review(read(refs[role]),item,index,role,action['files'])
 t=datetime.fromisoformat(prepared_utc);b.require(t.tzinfo is not None,'timezone-aware preparation UTC required')
 b.require(not (R/item['planned_invocation_path']).exists() and not (b.P/item['planned_invocation_path']).exists(),'prepared invocation already published; reconcile, never overwrite')
 readiness=dict(schema=b.ROUND,kind='formal_action_runtime_readiness',status='passed',reviewed_by='root',execution_version=contract.VERSION,scientific_settings_changed=False,final_evaluation_enabled=False,raw_consumer_ready=True,effective_plan=item['effective_plan'],scientific_plan=item['scientific_plan'],plan_sha256=effective['plan_sha256'],runtime_sources=action['files'],support_files=effective['invocation']['support_files'],action_execution_contract=item['execution_contract'],root_review=refs['root'],independent_review=refs['independent'],pair_key=pair_key,pair_id=item['pair_id'],method_ids=item['method_ids'],allowed_suite='libero_goal',allowed_stages=['development'],expected_trials=200,unique_development_initial_states=100,prior_job_ids=[],actual_GPU_runtime_chain_verified=False,actual_new_runtime_P_verified=False,active=False,global_freeze_enabled=False,O2A_enabled=False,production_chain_complete=True,production_chain_complete_meaning='Original metadata/source/consumer pre-execution closure only; future typed runtime authorizations remain separate',activation_meaning='Prepared original invocation only, not GPU submission permission',utc=prepared_utc)
 rr=dict(path=base+'/runtime_readiness.json',sha256=hashlib.sha256(b.encoded(readiness)).hexdigest())
 prepared={**effective['invocation'],'registered_utc':prepared_utc,'plan_sha256':effective['plan_sha256'],'runtime_readiness':rr}
 # Same explicit field relation checked by original wrapper; actual P verification is separate.
 b.require(set(prepared)==set(effective['invocation'])|{'registered_utc','plan_sha256','runtime_readiness'},'prepared field set differs')
 out=D/'prepared'/pair_key;b.write(out/'runtime_readiness.json',b.encoded(readiness));b.write(out/'prepared_invocation.json',b.encoded(prepared))
 report=dict(schema=b.ROUND,kind='Goal_remaining5_prepared_invocation_metadata',pair_key=pair_key,prepared_utc=prepared_utc,readiness=rr,original_invocation=dict(path=item['planned_invocation_path'],sha256=b.sha(out/'prepared_invocation.json')),private_outputs=[dict(source=str((out/'runtime_readiness.json').relative_to(R)),destination=rr['path'],sha256=rr['sha256']),dict(source=str((out/'prepared_invocation.json').relative_to(R)),destination=item['planned_invocation_path'],sha256=b.sha(out/'prepared_invocation.json'))],actual_P_verified=False,new_GPU_jobs=0,production_admitted=False)
 b.write(out/'preparation_record.json',b.encoded(report));return report

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--index',type=Path,required=True);ap.add_argument('--index-sha256',required=True);ap.add_argument('--pair-key',choices=b.KEYS,required=True);ap.add_argument('--root-review-sha256',required=True);ap.add_argument('--independent-review-sha256',required=True);ap.add_argument('--prepared-utc',required=True);a=ap.parse_args()
 print(json.dumps(prepare(index_path=a.index,index_sha=a.index_sha256,pair_key=a.pair_key,root_sha=a.root_review_sha256,independent_sha=a.independent_review_sha256,prepared_utc=a.prepared_utc),sort_keys=True))
if __name__=='__main__':main()