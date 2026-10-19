"""Independent exact Long16 action envelopes. No signing, publishing or execution."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
from xml.etree.ElementTree import Element,SubElement,tostring
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
OUT=R/'.local/long_action_outer_audit_1827'
AUTHOR='.local/long_action_outer_1827'
OLD='.local/long_development_1722'
PREFIX='scripts/ops/formal_action_deployment_v1/'
DEST='results/formal_main_v2/execution/long_remaining16_action_v1_1827'
INVENTORY='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
PANEL='configs/manifests/formal_main_v2/libero_10/initial_states/development.json'
ROOTCHECK='results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json'
PUB='results/formal_main_v2/preflight/heartbeat_20261020T0227/Long_outer_candidate_publication.json'
PAIRS=((128,23),(128,41),(256,17),(256,23),(256,41),(64,17),(64,23),(64,41))
OLD6={'dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'}
EXPECTED={f'{a}{k}_seed{s}' for k,s in PAIRS for a in ('A','B')}
PINS={
 INVENTORY:'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',
 PANEL:'46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268',
 ROOTCHECK:'e3b08dff62a583e910aecd04179841017e10f1216f6a19f431036fe056ff5757',
 PUB:'c919f5be4d4574f09f6e1f7884d4a05bdf43c0d9f3a41b8c30afd7e1900e67f1',
 AUTHOR+'/prepare.py':'87b998c474ed548d31d79f8bcc47e5d6fcc17eaebd0e43b824658595cd851a11',
 AUTHOR+'/outer_index.json':'e4c18587396f3f8cee3330bd01104a8db7ca3be38f6b28361e6f11cd425c5f22',
 AUTHOR+'/publication_map.json':'6fd6543dcb538335122ee369609e3ed68a2faaf9c1bdf33cca207890e9241f7f',
 AUTHOR+'/test_outer.py':'5e63d437ba0b125209e1f139d0150ab2ac7ad115d6125b54cb8ee899436962fc',
 OLD+'/plan_index.json':'e27f3c8973e778bd98b31327cbfe9b02c91faee4ad73af14e8c6cb8aa0132890',
 'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
 'scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',
 'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
 PREFIX+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
 PREFIX+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',
 PREFIX+'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',
 PREFIX+'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
 PREFIX+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
 PREFIX+'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
 PREFIX+'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
evidence={};checks=[]
def require(x,m):
 if not x:raise ValueError(m)
def safe(p):
 p=Path(p)
 require(p.is_absolute() and (R in p.parents or P in p.parents),'outside project')
 low=p.as_posix().lower()
 require(not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints','test') for x in p.parts),'forbidden directory')
 require(p.suffix.lower() not in {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'},'weights/states forbidden')
 if p.suffix.lower() not in {'.py','.pyc','.pyo'} and any(x in low for x in ('init_state','initial_state','final_state','test_state')):
  require(p in (R/PANEL,P/PANEL),'only exact registered development panel permitted')
 require(p.resolve()==p,'noncanonical path')
 return p
def sha(p):
 h=hashlib.sha256()
 with safe(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def watch(value,h=None):
 p=safe(Path(value) if Path(value).is_absolute() else R/value);actual=sha(p)
 require(h is None or actual==h,'SHA mismatch: '+str(p))
 key=str(p.relative_to(R)) if R in p.parents else str(p)
 require(key not in evidence or evidence[key]==actual,'between-read drift: '+key)
 evidence[key]=actual
 return p
def read(value,h=None):return json.loads(watch(value,h).read_bytes())
def ref(value):return read(value['path'],value['sha256'])
def emit(name,value):
 p=OUT/name;require(OUT in p.parents and p.resolve()==p,'private output')
 p.parent.mkdir(parents=True,exist_ok=True)
 raw=value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(rel):
 p=watch(rel,PINS[rel]);name='ind1827_'+p.stem
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def passed(name,**details):
 checks.append(dict(name=name,status='passed',**details));print('PASS '+name,flush=True)
def rejects(name,fn,expected=None):
 try:fn()
 except (ValueError,AssertionError) as ex:
  require(expected is None or expected in str(ex),'wrong rejection for '+name+': '+str(ex))
  passed(name,rejection=str(ex))
 else:raise AssertionError('negative accepted: '+name)
def main():
 started=time.monotonic()
 for rel,h in PINS.items():watch(rel,h)
 watch(__file__)
 interface=read('.local/long_action_outer_audit_1827/interface_preparation.json','cf6fac8dcf75b3d5d3d70b1d7a409343f701bbeecf9eda53cf3e715741345478')
 inv=read(INVENTORY)
 require(len(inv['files'])==173,'source count')
 for rel,h in inv['files'].items():watch(rel,h);watch(S/rel,h)
 for rel,h in PINS.items():
  if rel.startswith(PREFIX):watch(P/rel,h)
 passed('frozen173_R_S_and_seven_published_runtime_sources_R_P')
 sys.path[:0]=[str(R/'src'),str(R/'scripts')]
 planner=load('scripts/ops/formal_downstream_supervisor.py')
 helper=load('scripts/formal_execution_manifests.py')
 c=load(PREFIX+'contract.py');rt=load(PREFIX+'runtime_scope.py')
 inner_wrapper=load('scripts/server/run_formal_downstream.py');outer_wrapper=load(PREFIX+'wrapper.py')
 idx=read(AUTHOR+'/outer_index.json');mapping=ref(idx['publication_map'])
 require(len(mapping['files'])==24 and len(idx['shards'])==8,'candidate count')
 require(idx['submission_authorized'] is False and idx['scientific_settings_changed'] is False and idx['final_release'] is False,'candidate authorization drift')
 for item in mapping['files']:
  require(item['canonical_path'].startswith(DEST+'/'),'wrong canonical namespace')
  b=watch(item['candidate']['path'],item['sha256']).read_bytes()
  require(len(b)==item['bytes']==item['candidate']['bytes'],'candidate bytes')
  for project in (R,P):
   require(watch(project/item['canonical_path'],item['sha256']).read_bytes()==b,'canonical not original bytes')
 passed('twenty_four_actual_canonical_R_P_files_equal_candidate_bytes')
 state_path=R/'results/experiment_supervisor/state.json'
 state_raw=state_path.read_bytes();state=json.loads(state_raw);before=copy.deepcopy(state)
 state_ref=emit('state_snapshot_at_independent_reconstruction.json',state_raw);watch(state_ref['path'],state_ref['sha256'])
 require(state.get('pending_submission') is None,'unresolved actual pending')
 jobs=state['registered_jobs'];ids=[j['job_id'] for j in jobs];require(len(ids)==len(set(ids)),'duplicate registry')
 old=[j for j in jobs if j.get('experiment')=='formal_main_v2' and j.get('suite')=='libero_10' and j.get('mode')=='development']
 require({j['job_id'] for j in old}=={'3016981','3017161','3017959','3018505','3019176','3019954'},'old Long history changed/new target exists')
 require(all(set(j['method_ids'])==OLD6 and j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['gpus']==1 for j in old),'old allocation identity')
 require(sum(j['elapsed_seconds']*j['gpus'] for j in old)==10531,'old costs missing')
 for j in old:watch(j['invocation'],j['invocation_sha256'])
 oldreview=read('results/formal_main_v2/downstream_reviews/3019954.json','cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba')
 passed('actual_full_registry_unchanged_old600_and_all10531_GPU_seconds_retained',registry_rows=len(jobs))
 panel=read(PANEL);watch(P/PANEL,PINS[PANEL])
 from cti_vla.data.formal_initial_states import load_formal_development_panel
 require(load_formal_development_panel(R/PANEL)==panel,'original panel parser')
 require(len(panel['states'])==100 and len({(s['task_id'],s['source_state_index']) for s in panel['states']})==100,'panel cardinality')
 require({s['task_id'] for s in panel['states']}==set(range(10)),'task IDs')
 require(all(sum(s['task_id']==task for s in panel['states'])==10 for task in range(10)),'per-task panel')
 selected=read(ROOTCHECK)
 oldidx=read(OLD+'/plan_index.json')
 expected_sources={k:v for k,v in PINS.items() if k.startswith(PREFIX)}
 expected_sources[c.ACTION_ADAPTER]=c.ACTION_SHA
 scope=rt.make_contract(project_root=R,source_root=S,suite='libero_10',stage='development')
 require(scope==rt.make_contract(project_root=P,source_root=S,suite='libero_10',stage='development'),'R/P runtime shape')
 for project in (R,P):
  for path,h in rt.validate_contract(scope,project_root=project,source_root=S).items():watch(path,h)
 passed('actual_R_P_runtime_contract_inherits_only_3039197_engineering')
 all_inputs={};pairs=[];seen=[]
 for (budget,seed),row,oldrow in zip(PAIRS,idx['shards'],oldidx['plans']):
  name=f'k{budget}_seed{seed}';mids=[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}']
  require(row['pair']==name and row['method_ids']==mids,'pair ordering/method identity')
  science=ref(row['scientific_plan']);body=ref(row['action_execution_contract']);outer=ref(row['effective_plan'])
  require(watch(row['scientific_plan']['path']).read_bytes()==watch(oldrow['scientific_plan']['path'],oldrow['scientific_plan']['sha256']).read_bytes(),'original scientific raw bytes changed')
  require(body['runtime_contract']==scope and body['files']==expected_sources and body['transition'] is None,'wrong runtime body/legacy transition')
  require(body['GPU_acceptance']==c.GPU_REFS,'wrong inherited GPU evidence')
  manifest=read(oldrow['canonical_path'],oldrow['candidate']['sha256'])
  require(manifest['development_panel']==PANEL and manifest['development_panel_sha256']==PINS[PANEL],'panel changed')
  require(manifest['environment']==dict(action_chunk=8,environment_seed=0,runtime_seed=17,wait_steps=10,max_steps=520),'environment changed')
  require([m['identity']['method_id'] for m in manifest['methods']]==mids,'manifest methods')
  checkpoint_rows=[]
  for m in manifest['methods']:
   i=m['identity'];proof=selected['all18_selected'][i['method_id']];receipt=read(m['receipt'])
   require(i['visual_tokens']==budget and i['training_seed']==seed,'budget/seed mismatch')
   require(m['checkpoint']==proof['checkpoint_path'] and i['checkpoint_sha256']==proof['checkpoint_sha256']==receipt['checkpoint_sha256'],'selected identity changed')
   require(receipt['metadata']['update']==proof['selected_update'],'reselection detected')
   require(i['deployment_receipt_sha256']==c.signature(receipt),'semantic deployment receipt SHA')
   ref(proof['root_review']);ref(proof['independent_review'])
   checkpoint_rows.append(dict(method_id=i['method_id'],checkpoint=m['checkpoint'],sha256=i['checkpoint_sha256'],selected_update=proof['selected_update'],original_identity=i))
  args_data=ref(oldrow['plan_arguments'])
  rebuilt=planner.plan(SimpleNamespace(**args_data),state,project=R,helper=helper)
  require(rebuilt==science,'original planner real registry differs')
  require(state==before,'planner mutated or filtered supplied registry')
  inner=science['invocation'];effective=outer['invocation']
  require(inner['method_ids']==mids and inner['resume'] is False and inner['prior_job_ids']==[] and inner['prior_allocation_cost']==[],'nonfresh pair')
  require(inner['prior_review'] is None and inner['repair_record'] is None and inner['stop_after'] is None,'unexpected predecessor or stop')
  require(not (R/science['output_relative']).exists() and not (P/science['output_relative']).exists(),'output exists')
  require(not (R/science['invocation_relative']).exists() and not (P/science['invocation_relative']).exists(),'invocation exists')
  rebuilt_outer=c.effective_plan(science,scientific_plan_ref=row['scientific_plan'],execution_contract_ref=row['action_execution_contract'],execution_contract=body)
  require(rebuilt_outer==outer and c.validate_effective(science,outer,scientific_plan_ref=row['scientific_plan'],execution_contract_ref=row['action_execution_contract'],execution_contract=body),'outer reconstruction')
  require(outer['plan_sha256']==row['plan_sha256'] and science['plan_sha256']==row['scientific_plan_sha256'],'plan signature')
  require(effective['argv']==inner['argv'] and effective['source_provenance']==inner['source_provenance'],'science or source proof changed')
  require(effective['version']=='formal-downstream-action-v1' and c.resume_prefix_inputs(inner)=={},'new identity or fresh prefix mismatch')
  actual_args=inner_wrapper.verify(inner)
  require(str(actual_args.checkpoint)==scope['checkpoint'],'wrong runtime base')
  rejects('new_wrapper_without_root_readiness_'+name,lambda:outer_wrapper.verify(effective,project=P),'Exact path/SHA reference required')
  projection=ref(row['runtime_projection'])
  inputs=dict(effective['watched_files'])
  for source in (outer['publish_files'],effective['support_files']):
   for rel,h in source.items():
    key=str(P/rel);require(key not in inputs or inputs[key]==h,'closure collision');inputs[key]=h
  require(projection['inputs']==inputs and projection['runtime_sources']==body['files'],'projection missing/extra input')
  require(projection['scientific_plan']==row['scientific_plan'] and projection['effective_plan']==row['effective_plan'] and projection['action_execution_contract']==row['action_execution_contract'] and projection['plan_sha256']==outer['plan_sha256'],'projection binds wrong plan')
  for path,h in inputs.items():
   watch(path,h);require(path not in all_inputs or all_inputs[path]==h,'shared input conflict');all_inputs[path]=h
  for rel,h in effective['root_evidence_sha256'].items():watch(rel,h)
  pair=dict(pair=name,method_ids=mids,scientific_plan=row['scientific_plan'],effective_plan=row['effective_plan'],
   action_execution_contract=row['action_execution_contract'],plan_sha256=outer['plan_sha256'],scientific_plan_sha256=science['plan_sha256'],
   stage_key=inner['stage_key'],run_root=inner['run_root'],invocation_relative=science['invocation_relative'],
   checkpoint_identities=checkpoint_rows,runtime_sources=body['files'],runtime_projection=row['runtime_projection'],
   expected_trials=200,unique_development_initial_states=100,resume=False,prior_job_ids=[],prior_allocation_cost=[],
   runtime_input_count=len(inputs))
  pairs.append(pair);seen+=mids
  passed('actual_original_and_outer_reconstruction_with_inner_P_verify_'+name)
 require(len(seen)==len(set(seen))==16 and set(seen)==EXPECTED and not set(seen)&OLD6,'partition')
 require(len({r['stage_key'] for r in pairs})==len({r['run_root'] for r in pairs})==8,'output collision')
 passed('exact_disjoint_sixteen_methods_eight_pair200_same100_initial_states')
 first=idx['shards'][0];science=ref(first['scientific_plan']);body=ref(first['action_execution_contract']);outer=ref(first['effective_plan'])
 def check(plan,contract=body,science_ref=None):
  return c.validate_effective(science,plan,scientific_plan_ref=science_ref or first['scientific_plan'],
   execution_contract_ref=first['action_execution_contract'],execution_contract=contract)
 def mutate_outer(name,fn):
  value=copy.deepcopy(outer);fn(value);value['plan_sha256']=c.signature({k:v for k,v in value.items() if k!='plan_sha256'})
  rejects(name,lambda:check(value))
 mutate_outer('changed_raw_argv_rejected',lambda x:x['invocation']['argv'].append('--resume'))
 mutate_outer('old_six_identity_replacement_rejected',lambda x:x['invocation'].update(method_ids=['A128_seed17','B128_seed17']))
 mutate_outer('old_allocation_or_prefix_injection_rejected',lambda x:x['invocation'].update(prior_job_ids=['3019954']))
 mutate_outer('watch_omission_rejected',lambda x:x['invocation']['watched_files'].pop(next(iter(x['invocation']['watched_files']))))
 mutate_outer('support_omission_rejected',lambda x:x['invocation']['support_files'].pop(c.RUNTIME))
 mutate_outer('source_provenance_rewrite_rejected',lambda x:x['invocation'].update(source_provenance={}))
 mutate_outer('legacy_version_masquerade_rejected',lambda x:x['invocation'].update(version='formal-downstream-root-v1'))
 mutate_outer('resource_extension_rejected',lambda x:x['resources'].update(time='48:00:00'))
 rejects('cross_pair_scientific_ref_swap_rejected',lambda:check(outer,science_ref=idx['shards'][1]['scientific_plan']))
 corrupt=copy.deepcopy(body);corrupt['transition']=dict(path='results/formal_main_v2/not_read.json',sha256='0'*64)
 rejects('fresh_contract_cannot_inherit_legacy_transition',lambda:check(outer,contract=corrupt))
 badscope=copy.deepcopy(scope);badscope['policy']['action_values']='clip'
 rejects('runtime_action_change_rejected',lambda:rt.validate_contract(badscope,project_root=P,source_root=S))
 rejects('final_stage_refused',lambda:rt.make_contract(project_root=P,source_root=S,suite='libero_10',stage='final'))
 for rel in ('../escape.json','results/sealed/panel.json','results/weights/best.pt'):
  rejects('forbidden_ref_'+rel.replace('/','_'),lambda rel=rel:c.read_ref(P,dict(path=rel,sha256='0'*64)))
 # Original pure gate with full actual registry plus an explicit in-memory adverse row.
 gate=dict(evidence=helper.Evidence(R),suite='libero_10',methods=first['method_ids'])
 args=SimpleNamespace(**ref(oldidx['plans'][0]['plan_arguments']))
 adverse=copy.deepcopy(state);adverse['registered_jobs'].append(dict(experiment='formal_main_v2',job_id='999999991',mode='development',
  suite='libero_10',method_ids=first['method_ids'],stage_key=first['stage_key'],status='RUNNING',run_root=first['run_root']))
 rejects('real_original_gate_rejects_duplicate_active_pair',lambda:planner.prior_contract(args,adverse,gate,R))
 pending=copy.deepcopy(state);pending['pending_submission']={'status':'unknown'}
 rejects('real_original_planner_rejects_pending',lambda:planner.plan(args,pending,project=R))
 require(state==before,'audit mutated state object')
 for key,h in list(evidence.items()):watch(key,h)
 passed('all_immutable_read_evidence_rehashed_after_checks')
 elapsed=time.monotonic()-started
 result=dict(schema='formal_main_v2',kind='Long16_action_outer_independent_reconstruction',
  status='passed_exact_pre_execution_plan_audit',utc=datetime.now(timezone.utc).isoformat(),
  author_index=dict(path=AUTHOR+'/outer_index.json',sha256=PINS[AUTHOR+'/outer_index.json']),
  root_publication=dict(path=PUB,sha256=PINS[PUB]),checks=checks,passed_checks=len(checks),elapsed_seconds=elapsed,
  state_snapshot=state_ref,full_registry_rows=len(jobs),registry_filtered=False,state_writes=0,
  state_raw_sha256_after_observation=hashlib.sha256(state_path.read_bytes()).hexdigest(),
  pairs=pairs,expected_total_trials=1600,common_unique_initial_states=100,all_runtime_inputs=all_inputs,
  old_Long_trial_count=600,old_Long_GPU_seconds=10531,
  checkpoint_bytes_read=False,actual_GPU_runtime_chain_verified=False,new_GPU_seconds=0,new_trials=0,
  positive_full_outer_wrapper_check='pending_genuine_root_readiness',root_readiness_created=False,
  submission_authorized=False,Slurm_queries=0,production_writes=0,
  synthetic_scope='Only in-memory adverse invocation/contract/registry inputs. All positive plans, source evidence, P dependencies and original validators are real and unpatched.',
  read_evidence_sha256=evidence)
 resultref=emit('reconstruction.json',result)
 suite=Element('testsuite',name='Long16_outer_independent',tests=str(len(checks)),failures='0',errors='0',skipped='0',time=f'{elapsed:.6f}')
 for item in checks:SubElement(suite,'testcase',name=item['name'])
 xmlref=emit('checks.xml',tostring(suite,encoding='utf-8',xml_declaration=True)+b'\n')
 reviewrows=[]
 for pair in pairs:
  row=copy.deepcopy(pair)
  row.update(schema='formal_main_v2',kind='formal_action_development_plan_independent_review',status='passed',
   execution_version=c.VERSION,review_role='independent',reviewed_by='train64',suite='libero_10',stage='development',
   scientific_settings_changed=False,allowed_stages=['development'],final_evaluation_enabled=False,
   O2A_enabled=False,global_freeze_enabled=False,
   production_chain_complete=True,
   production_chain_complete_meaning='Exact pre-execution scientific, control/source and consumer integration path validated. Not an executed GPU chain. Root readiness, full outer wrapper.verify(P), fresh live capacity/pending/CAS and one-use authorization remain mandatory.',
   actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,
   inherited_engineering_GPU_evidence=c.GPU_REFS,old_new_outcome_equivalence_established=False,
   old600_results_relabelled=False,original_Long600_GPU_seconds_retained=10531,
   independent_reconstruction=resultref,independent_checks=xmlref,
   source173_R_S_unchanged=True,actual_inner_wrapper_P_verified=True,
   actual_outer_source_and_plan_P_closure_verified=True,
   positive_full_outer_wrapper_verification_pending_root_readiness=True,
   all_methodIDs_and_checkpoints_original=True,transition=None,
   root_readiness_signed_by_reviewer=False,submission_authorized=False,production_state_changed_by_reviewer=False,
   canonical_review_path=DEST+'/'+pair['pair']+'/plan_independent_review.json',
   author_source=dict(path=AUTHOR+'/prepare.py',sha256=PINS[AUTHOR+'/prepare.py']),
   root_publication=dict(path=PUB,sha256=PINS[PUB]),
   source_component_authorship_boundary='This reviewer previously authored the gateway. Its component correctness is inherited from its separate independent component review; this audit independently reconstructs these eight author-created real plans and exact published byte closures.',
   required_before_submission=[
    'Root must sign exact per-plan root review/readiness and independently compare all four plan references, method IDs and runtime sources; nested minimal runtime fields alone do not establish plan equality.',
    'Publish real prepared invocation/readiness and all typed root/independent metadata byte-identically to P; run the unchanged full new wrapper.verify(P).',
    'Root gateway must recheck full live registry, actual scheduler identities, controller lease, capacity<=8 including all reservations, pair uniqueness and durable pending/CAS; do not consume another request reservation.',
    'Actual new runtime journals, completed trials and all allocation costs require separate terminal review. None exists or is inferred here.'
   ])
  rr=emit('shards/'+pair['pair']+'/plan_independent_review.json',row)
  reviewrows.append(dict(pair=pair['pair'],method_ids=pair['method_ids'],candidate=rr,canonical_path=row['canonical_review_path'],
   scientific_plan=pair['scientific_plan'],effective_plan=pair['effective_plan'],action_execution_contract=pair['action_execution_contract'],plan_sha256=pair['plan_sha256']))
 idxref=emit('independent_index.json',dict(schema='formal_main_v2',kind='Long16_action_outer_independent_plan_index',
  status='passed_eight_exact_pre_execution_plans_pending_root_readiness',shards=reviewrows,
  total_planned_trials=1600,unique_initial_states_per_method=100,old600_GPU_seconds_retained=10531,
  actual_GPU_runtime_chain_verified=False,submission_authorized=False,root_readiness_created=False,
  reconstruction=resultref,checks=xmlref,full_registry_rows=len(jobs),source173_unchanged=True))
 print(json.dumps(dict(independent_index=idxref,reconstruction=resultref,checks=len(checks),duration_seconds=elapsed)),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  emit('audit_failure.json',dict(status='failed',error=repr(e),traceback=traceback.format_exc(),checks=checks,read_evidence_sha256=evidence))
  raise
