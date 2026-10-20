"""Bounded CPU gateway scope/AST tests. No live scheduler or publication.
This is not readiness, complete gateway runtime validation, or authorization.
"""
from pathlib import Path
from types import ModuleType,SimpleNamespace
import ast,copy,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent.parent;B=D/'phase3_gateway';C=D/'phase2_v2'
def sha(b):return hashlib.sha256(b).hexdigest()
graw=(B/'gateway.py').read_bytes();assert sha(graw)=='aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c'
g=ModuleType('_spatial588_gateway_CPU');g.__file__=str(B/'gateway.py');exec(compile(graw,g.__file__,'exec'),g.__dict__)
craw=(C/'control.py').read_bytes();assert sha(craw)=='e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683';c=ModuleType('_spatial588_control_CPU');c.__file__=str(C/'control.py');exec(compile(craw,c.__file__,'exec'),c.__dict__)
base=R/'scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py';assert sha(base.read_bytes())=='873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb'
checks=[]
def okay(name):checks.append({'name':name,'passed':True})
def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,AssertionError,FileNotFoundError) as e:checks.append({'name':name,'expected_rejection':str(e)[:300]});return
 raise AssertionError('forbidden acceptance '+name)
def top(src):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(src).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=top(base.read_text());b=top(graw)
changed=[k for k in a if a[k]!=b[k]];assert changed==['validate_authorization','completed_training_development_gate','capacity_gate','Gateway','_exact_development_authorization','_exact_development_control','_exact_development_plan']
for n in ['FrozenPlan','NativeIO','parse_ack','check_observed_identity','corroborate_new_job','reconcile_submission','submission_argv','registered_comment','Evidence','main','source_files']:
 assert a[n]==b[n];okay('unchanged_original_'+n)
def methods(src,cls):return {n.name:ast.dump(n,include_attributes=False) for n in next(x for x in ast.parse(src).body if isinstance(x,ast.ClassDef) and x.name==cls).body if isinstance(n,ast.FunctionDef)}
x=methods(base.read_text(),'Gateway');y=methods(graw,'Gateway');assert [n for n in x if x[n]!=y[n]]==['_job'];okay('Gateway_run_writer_lock_CAS_single_ACK_pending_reconcile_failure_stop_byte_semantics_unchanged')
real_load=g.load
def fake_control_load(path,pin,name):
 assert path==R/g.SCOPED_DEVELOPMENT_PLANS['libero_spatial']['control']['path'] and pin==sha(craw)
 return c
g.load=fake_control_load
scientific=json.loads((C/'SYNTHETIC_planner_fixture.json').read_text())['synthetic_plan_NOT_FOR_SUBMISSION'];effective=copy.deepcopy(scientific)
# CPU scope parser only. Full validate_authorization/FrozenPlan.prepare remain
# dependent on real canonical adoption/readiness and are not claimed passed.
args=dict(stage='development',source_inventory=g.INVENTORY,execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
allowed=g.SCOPED_DEVELOPMENT_PLANS['libero_spatial'];auth={'plan':{'path':allowed['path'],'sha256':'1'*64},'scientific_plan':{'path':allowed['scientific_path'],'sha256':'2'*64},'prepared_invocation':{'path':allowed['prepared_path'],'sha256':'3'*64},'plan_arguments':args,'explicit_source_control':c.descriptor(),'legacy12_compatibility':c.compatibility_module().descriptor()}
assert g._exact_development_authorization(auth)==allowed;assert g._exact_development_plan(R,auth,effective,scientific) is c;okay('exact_CPU_scope_only_original588_attempt03')
for field in ['plan','scientific_plan','prepared_invocation']:
 for value in ['results/formal_main_v2/foreign.json','.local/foreign.json','results/formal_main_v2/final/sealed.json']:
  bad=copy.deepcopy(auth);bad[field]['path']=value;reject(field+'_other_path',lambda bad=bad:g._exact_development_authorization(bad))
 bad=copy.deepcopy(auth);bad[field]['sha256']='not_sha';reject(field+'_missing_exactSHA',lambda bad=bad:g._exact_development_authorization(bad))
for key,value in [('stage','final'),('stage','collect'),('stage','full'),('stage','components'),('resume',False),('stop_after',12),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('repair_record',None),('output_relative','foreign'),('execution_manifest','foreign.json'),('profile_panel','final/sealed.json')]:
 bad=copy.deepcopy(auth);bad['plan_arguments'][key]=value;reject('args_'+key+'_'+str(value),lambda bad=bad:g._exact_development_authorization(bad))
for key,value in [('suite','libero_object'),('method_ids',['A64_seed23','B64_seed23']),('resume',False),('prior_job_ids',['3022743']),('prior_job_ids',['3022743','3042529','999999999']),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('stage','full'),('stop_after',12),('pre_dispatch_history',{}),('legacy12_compatibility',{})]:
 inv=copy.deepcopy(effective['invocation']);inv[key]=value;reject('scope_'+key,lambda inv=inv:g._exact_development_control(R,inv))
for field in ['legacy12_compatibility','explicit_source_control']:
 bad=copy.deepcopy(auth);bad[field]={};reject('auth_'+field,lambda bad=bad:g._exact_development_plan(R,bad,effective,scientific))
for key,wrong in [('invocation_relative','results/formal_main_v2/invocations/libero_spatial_development_8c843c1d4ee8383c_attempt04.json'),('output_must_exist',False),('output_relative','foreign')]:
 bad=copy.deepcopy(effective);bad[key]=wrong;bad['plan_sha256']=sha(g.canonical({k:v for k,v in bad.items() if k!='plan_sha256'}));reject('plan_'+key,lambda bad=bad:g._exact_development_plan(R,auth,bad,scientific))
for out in ['', '3054000\n3054001\n', '3042529\n', '3054000 garbage\n']:
 reject('ambiguous_or_duplicate_ack_'+repr(out),lambda out=out:g.parse_ack(SimpleNamespace(returncode=0,stdout=out),{'3042529'}))
assert g.parse_ack(SimpleNamespace(returncode=0,stdout='399999999\n'),{'3042529'})=='399999999';okay('original_unambiguous_ACK_parser')
reject('nonzero_ack',lambda:g.parse_ack(SimpleNamespace(returncode=1,stdout='399999999\n'),set()))
for token in ['../bad.json','/tmp/evil.json','results/final/sealed.json','results/checkpoints/x.pt']:
 reject('forbidden_path_'+token,lambda token=token:g.relative(token))
# Scope/capacity gate must reject before consulting owner files or scheduler.
fake=SimpleNamespace(capacity=lambda *a:{'unknown':[],'findings':[],'occupied':['x']*8})
state={'pending_submission':None,'registered_jobs':[{'job_id':'3034538','gpus':0}],'autonomous_training_v1':{'activation':g.ACTIVATION,'activation_sha256':g.ACTIVATION['sha256'],'controller_job_id':'3034538','root_submission_hold':None,'reserved_GPU_slots':1,'reservation_root_record':{'path':'CPU_ONLY','sha256':'0'*64}}}
snap={'rows':{'3034538':{'gpus':0,'status':'COMPLETED'}},'queue':{}};a2={**auth,'controller_activation':g.ACTIVATION,'controller_job_id':'3034538','root_reservation':state['autonomous_training_v1']['reservation_root_record']}
reject('eight_GPU_slots_occupied',lambda:g.capacity_gate(fake,state,snap,a2,effective))
for badcaps in [{'unknown':['x'],'findings':[],'occupied':[]},{'unknown':[],'findings':['inconsistent'],'occupied':[]}]:
 fake.capacity=lambda *a,badcaps=badcaps:badcaps;reject('unknown_or_inconsistent_capacity',lambda:g.capacity_gate(fake,state,snap,a2,effective))
bad=copy.deepcopy(state);bad['pending_submission']={'known_job_id':None};reject('pending_without_ACK_cannot_clear',lambda:g.capacity_gate(fake,bad,snap,a2,effective))
for v in [0,2,8]:
 bad=copy.deepcopy(state);bad['autonomous_training_v1']['reserved_GPU_slots']=v;reject('dedicated_reservation_'+str(v),lambda bad=bad:g.capacity_gate(fake,bad,snap,a2,effective))
summary={'schema':'formal_main_v2','kind':'Spatial588_gateway_scoped_author_CPU_review','status':'passed_bounded_CPU_candidate_HOLD_actual_canonical_readiness','checks':checks,'check_count':len(checks),'changed_AST_functions':changed,'gateway_sha256':sha(graw),'base_sha256':sha(base.read_bytes()),'controller_submission_or_restart':False,'new_GPU_seconds':0,'new_scientific_trials':0,'state_Git_P_mutations':False,'actual_canonical_readiness_verified':False,'actual_new_P_wrapper_verify':False,'full_gateway_transaction_replayed':False,'full_terminal_consumer_executed':False,'limitations':['Root canonical adoption/repair/transition/effective plan/readiness not yet installed','Candidate scope tests use the explicitly SYNTHETIC scientific plan in memory; no production authorization','Whole original transaction AST retained; actual new gateway independent audit and real P verify still required']}
(B/'author_CPU_tests.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'report_sha256':sha((B/'author_CPU_tests.json').read_bytes())}))
