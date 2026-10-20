from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';D=R/'.local/spatial_object_collect_20261020T1825';GREL='scripts/ops/formal_action_deployment_posttraining_v1/gateway.py';GSHA='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83';WSHA='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p)}
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def put(p,raw):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw;return
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def save(p,v):put(p,(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
def load(p,pin,name):
 assert h(safe(p))==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--suite',choices=['Spatial','Object'],required=True);ap.add_argument('--gateway-review',required=True);ap.add_argument('--gateway-review-sha256',required=True);ap.add_argument('--plan-review',required=True);ap.add_argument('--plan-review-sha256',required=True);a=ap.parse_args()
g=load(R/GREL,GSHA,'completedcollectgateway');c=load(R/g.CONTROLLER,g.CONTROLLER_SHA,'completedcollectcontroller')
grp=safe(R/a.gateway_review);prp=safe(R/a.plan_review);assert h(grp)==a.gateway_review_sha256 and h(prp)==a.plan_review_sha256;gr=read(grp);pr=read(prp)
assert gr['kind']=='formal_downstream_server_gateway_independent_CPU_review' and gr['status']=='passed_CPU_review' and not gr['blockers'] and gr['files'][GREL]==GSHA
assert pr['status']=='passed' and pr['execution_version']=='formal-downstream-action-v1' and pr['reviewed_by']=='independent' and pr['production_chain_complete'] is True
suite=a.suite;prefix='results/formal_main_v2/execution/'+suite.lower()+'_collect_action_v1_20261020T1825';private=D/suite/'plan_v1';out=R/prefix
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read(sp);assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 plan=read(out/'effective_plan.json');science=read(out/'scientific_plan.json');action=read(out/'execution_contract.json');ready=read(private/'runtime_readiness_draft.json');inv=plan['invocation']
 assert inv['stage']=='collect' and inv['suite']=='libero_'+suite.lower() and inv['method_ids']==['dense'] and inv['resume'] is False and inv['final_values_read_locally'] is False
 assert h(out/'effective_plan.json')==g.COMPLETED_COLLECTION_PLANS[inv['suite']]['sha256'] and pr['runtime_sources']==action['files'] and ready['runtime_sources']==action['files']
 assert not any(j.get('experiment')=='formal_main_v2' and j.get('mode')=='collect' and j.get('suite')==inv['suite'] for j in s['registered_jobs']) and not (P/plan['output_relative']).exists() and not (R/plan['invocation_relative']).exists()
 for role,reference in ready['component_reviews'].items():
  component=read(R/reference['path']);assert h(R/reference['path'])==reference['sha256'] and component['component']==role and component['status']=='passed_CPU_review' and not component.get('blockers')
 for rel,pin in inv['support_files'].items():assert h(safe(R/rel))==h(safe(P/rel))==pin
 for rel,pin in read(R/g.INVENTORY)['files'].items():assert h(safe(R/rel))==h(safe(S/rel))==pin
 original_wrapper=load(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24','collectrootoriginalwrapper');original_args=original_wrapper.verify(science['invocation'])
 assert not science['invocation']['resume']
 import torch
 assert not torch.cuda.is_initialized()
 source_registration=read(out/'collection_selection_registration.json');manifest=read(out/'dense_development.json');panel=read(R/manifest['development_panel']);selected=[min([r for r in panel['states'] if r['task_id']==t],key=lambda r:r['source_state_index']) for t in range(10)]
 assert source_registration['selected_states']==selected and source_registration['expected_observations']==30 and source_registration['success_based_replacement'] is False
 assert h(sp)==before
 put(out/'gateway_independent_review.json',grp.read_bytes());put(out/'independent_plan_review.json',prp.read_bytes())
 rootreview={'schema':'formal_main_v2','kind':'formal_collect_runtime_root_CPU_review','status':'passed','reviewed_by':'root','execution_version':'formal-downstream-action-v1','runtime_sources':action['files'],'production_chain_complete':True,'effective_plan':ref(out/'effective_plan.json'),'scientific_plan':ref(out/'scientific_plan.json'),'actual_P_original_scientific_wrapper_verification':True,'new_GPU_acceptance':False,'scientific_success_trials_added':0,'final_values_read':False,'source_files_173_unchanged':True,'selection_matches_frozen_development_min_index_each_task':True,'source_registration':ref(out/'collection_selection_registration.json'),'original_collector_prepare_only':ref(private/'original_collector_prepare_only.json'),'independent_plan_review':ref(out/'independent_plan_review.json'),'prior_component_proofs_inherited_explicitly':ready['component_reviews'],'CPU_only_limits':'Production-chain proof verifies unchanged source, actual P metadata/wrapper and existing component GPU acceptance; no claim of newly collected data or measured latency.','utc':datetime.now(timezone.utc).isoformat()}
 save(out/'root_runtime_review.json',rootreview)
 ready.update(status='passed',reviewed_by='root',active=True,production_chain_complete=True,raw_consumer_ready=True,pending_runtime_publication_roles=[],root_review=ref(out/'root_runtime_review.json'),independent_review=ref(out/'independent_plan_review.json'))
 for p in [out/'root_runtime_review.json',out/'independent_plan_review.json']:
  ready['runtime_publication_files'][str(p.relative_to(R))]=h(p)
 save(out/'runtime_readiness.json',ready)
 for rel,pin in ready['runtime_publication_files'].items():assert h(R/rel)==pin;put(P/rel,(R/rel).read_bytes())
 put(P/prefix/'runtime_readiness.json',(out/'runtime_readiness.json').read_bytes())
 prepared=copy.deepcopy(inv);prepared.update(registered_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=plan['plan_sha256'],runtime_readiness=ref(out/'runtime_readiness.json'));save(out/'prepared_invocation.json',prepared)
 auth=read(private/'submission_authorization_draft.json');auth.update(version=g.VERSION,status='approved_for_exactly_one_registered_downstream_submission',gateway_files=g.source_files(R),independent_review=ref(out/'gateway_independent_review.json'),runtime_readiness=ref(out/'runtime_readiness.json'),prepared_invocation=ref(out/'prepared_invocation.json'))
 reserve=read(private/'reservation_root_record_draft.json');reserve.update(status='approved_for_exact_downstream_request',authorization_intent_sha256=g.intent_sha(auth));save(out/'reservation_root_record.json',reserve);auth['root_reservation']=ref(out/'reservation_root_record.json');save(out/'submission_authorization.json',auth)
 checked,e,p,sc,prep=g.validate_authorization(R,ref(out/'submission_authorization.json'));assert p==plan and sc==science and prep==prepared
 wrapper=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py',WSHA,'collectrootactualactionwrapper');ctx=wrapper.verify(prepared,project=P);assert ctx['original_plan']==science and ctx['effective_plan']==plan and not torch.cuda.is_initialized()
 assert h(sp)==before
 receipt={'schema':'formal_main_v2','status':'collect_prepared_root_independent_CPU_verified_not_submitted','suite':inv['suite'],'authorization':ref(out/'submission_authorization.json'),'root_review':ref(out/'root_runtime_review.json'),'independent_review':ref(out/'independent_plan_review.json'),'gateway_review':ref(out/'gateway_independent_review.json'),'state_unchanged':True,'state_sha256':before,'new_GPU_jobs':0,'actual_P_action_wrapper_verified_after_publication':True,'final_values_read':False,'utc':datetime.now(timezone.utc).isoformat()};save(B/(suite+'_collect_readiness.json'),receipt);print(json.dumps(receipt))
