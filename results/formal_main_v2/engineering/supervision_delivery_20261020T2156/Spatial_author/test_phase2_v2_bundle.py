from pathlib import Path
from types import ModuleType
import copy,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'.local/spatial588_integration_20261020T2156/phase2_v2'
sys.dont_write_bytecode=True
c=ModuleType('_sp588_phase2');c.__file__=str(B/'control.py');sys.modules[c.__name__]=c;exec(compile((B/'control.py').read_bytes(),c.__file__,'exec'),c.__dict__)
f,p=c.control_modules();ev=f.Evidence(R);state=json.loads((R/'results/experiment_supervisor/state.json').read_text());jobs=p.formal_jobs(state)
def write(name,value):
 path=B/name;assert path.resolve().parent==B
 path.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
bridge=c.compatibility_module();history=c.verify_history(ev,jobs);compat=bridge.audit_prefix(ev)
write('typed_history_descriptor.json',history);write('compatibility_descriptor.json',compat);write('root_adoption_proposal.json',bridge.adoption_proposal());write('repair_record_proposal.json',c.repair_proposal())
positive=[];negative=[]
def reject(name,fn):
 try:fn()
 except (ValueError,FileNotFoundError,AssertionError,KeyError) as error:negative.append({'name':name,'error':str(error)[:400]});return
 raise AssertionError('accepted forbidden case: '+name)
positive+=['real all395GPU-second history rebuilt','real prefix12/122chunks/917actions byte reverified','bundle source and raw identity closure','original scoped planner/private factory loaded']
reject('production root adoption absent',lambda:bridge.check_adoption(ev))
indref={'path':bridge.INDEPENDENT_REVIEW,'sha256':bridge.INDEPENDENT_SHA}
root=bridge.adoption_proposal();root.update(status='root_adopted',reviewed_by='root',independent_review=indref)
ind=json.loads((R/'.local/spatial12_independent_20261020T2156/independent_review.json').read_text());assert hashlib.sha256((R/'.local/spatial12_independent_20261020T2156/independent_review.json').read_bytes()).hexdigest()=='3cb7efa91ebbdb42c8ae91afef2f34ade5b237ee169a369a721353b0840bbf50'
assert bridge.validate_adoption_documents(root,ind,independent_ref=indref)==compat
positive.append('CPU in-memory schema validates separate root and independent receipt only; no evidence is published')
for field,wrong in [('status','passed'),('reviewed_by','author'),('legacy_origin_preserved',False),('historical_controller_is_source_inference',False),('new_GPU_seconds',2),('new_scientific_trials',12),('final_release',True),('profiling_authorized',True),('source_closure',{}),('independent_review',None)]:
 v=copy.deepcopy(root);v[field]=wrong;reject('root_'+field,lambda v=v:bridge.validate_adoption_documents(v,ind,independent_ref=indref))
for field,wrong in [('schema','other'),('kind','author'),('status','candidate'),('proof_sha256','0'*64),('phase1_manifest_sha256','0'*64),('scope',{}),('blockers',['missing']),('reviewed_by','author'),('full_original_author_reconstruction_passed',False),('independent_byte_and_queue_reconstruction_passed',False),('production_admission',True),('new_GPU_seconds',1),('new_scientific_trials',12)]:
 v=copy.deepcopy(ind);v[field]=wrong;reject('independent_'+field,lambda v=v:bridge.validate_adoption_documents(root,v,independent_ref=indref))
for path in ['.local/not_archived.json',bridge.ADOPTION]:
 ref={**indref,'path':path};v={**root,'independent_review':ref};reject('independent_noncanonical_'+path,lambda v=v,ref=ref:bridge.validate_adoption_documents(v,ind,independent_ref=ref))
for field,wrong in [('legacy_trial_ids',compat['legacy_trial_ids'][:-1]),('legacy_job_id','3042529'),('target_action_semantics_sha256','0'*64),('legacy_origin_preserved',False),('scope',{**compat['scope'],'suite':'libero_object'})]:
 v=copy.deepcopy(root);v['compatibility_descriptor'][field]=wrong;reject('descriptor_'+field,lambda v=v:bridge.validate_adoption_documents(v,ind,independent_ref=indref))
for name,action in [('unknown_bundle',lambda:bridge.bundle('../compatibility_proof.json')),('rebind_control',lambda:bridge.bind_control(c)),('nan_action',lambda:bridge.f64([[float('nan')]*7])),('wide_action',lambda:bridge.f64([[0.]*8])),('bool_action',lambda:bridge.f64([[True]*7]))]:reject(name,action)
for mode in ['final','collect','full','components']:
 args=type('Args',(),{})();args.__dict__.update(stage=mode,source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
 reject('planner_stage_'+mode,lambda args=args:c.scope_args(args))
ev.unchanged()
write('phase2_author_CPU_tests.json',{'schema':'formal_main_v2','status':'passed_CPU_candidate_only','positive':positive,'negative':negative,'positive_count':len(positive),'negative_count':len(negative),'actual_prefix_verified':True,'all395_prior_GPU_seconds_preserved':True,'production_admission':False,'GPU_submissions':0,'new_trials':0,'control_sources':c.closure(),'state_sha256':hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest(),'limitations':['No root adoption exists yet','No new canonical planner/readiness/transition invocation has been released','No new actual P wrapper verify has been run','No new terminal600 proof or result exists']})
print(json.dumps({'status':'passed_CPU_candidate_only','positive':len(positive),'negative':len(negative),'closure':c.closure()}))
