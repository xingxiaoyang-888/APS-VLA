from pathlib import Path
import hashlib,json,copy,importlib.util,sys,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';A=R/'.local/goal_remaining5_plans_20261021T0449';D=R/'.local/goal_remaining5_independent_20261021T0449/plans_canonical'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0449/Goal_plan_independent'
checks=[]
def ck(v,m):
 checks.append({'check':m,'passed':bool(v)})
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(Path(p).relative_to(R)),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def jref(p):return {'path':str(Path(p).relative_to(R)),'sha256':sha(p)}
def read(p,pin=None):
 if pin:ck(sha(p)==pin,'exact SHA '+str(p))
 return json.loads(Path(p).read_bytes())
def load(p,pin,name):
 ck(sha(p)==pin,'module pin '+str(p));sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
manifest=read(A/'delivery_manifest.json','321e64ca6aa130230c5949bab54b1bcd52f4ef0fec75ad70f2f4161ef1ea683e')
for item in manifest['files']:
 q=Path(item['path']);q=q if q.is_absolute() else (R/q if (R/q).exists() else A/q)
 ck(q.is_file() and sha(q)==item['sha256'],'author archive member '+str(q))
 if 'bytes' in item:ck(q.stat().st_size==item['bytes'],'author archive byte count '+str(q))
indexpath=A/'v2/candidate_index.json';index=read(indexpath,'638ec6f36339aa3a43a78266a60c58427aa40f22979f442cd740432962a28d3f')
b=load(A/'v2/build_plans.py','3d84ce954a5d6b3d74cbe430518b12bdba93fe25bc17631bf743cc75698b6ffa','ind_remaining5_builder');prep=load(A/'v2/prepare_after_reviews_v2.py','a633636dc4cdd64f75d32de72dda5dea34804b1253d7658c21dce97091aa7736','ind_remaining5_prepare')
statepath=R/'results/experiment_supervisor/state.json';state_raw=statepath.read_bytes();ck(hashlib.sha256(state_raw).hexdigest()=='d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba','actual complete303 corrected registry snapshot');state=json.loads(state_raw)
with (D/'state_snapshot.json').open('xb') as f:f.write(state_raw)
ck(state.get('pending_submission') is None and state['autonomous_training_v1'].get('pending_submission') is None,'both pending queues empty')
ck(len(state['registered_jobs'])==303 and sum(x.get('experiment')=='formal_main_v2' for x in state['registered_jobs'])==273,'all actual history retained')
publications=[]
for row in index['publication_map']:
 for base in row['install_roots']:
  root={'R':R,'P':P}[base];q=root/row['destination'];ck(sha(q)==row['sha256'] and q.stat().st_size==row['bytes'],'canonical '+base+' published target '+row['destination']);publications.append({'root':base,'path':row['destination'],'sha256':sha(q)})
ck(len(publications)==75,'exact75 canonical target copies')
h=b.load('scripts/formal_execution_manifests.py');planner=b.load('scripts/ops/formal_downstream_supervisor.py');contract=b.load('scripts/ops/formal_action_deployment_v1/contract.py');runtime=b.load('scripts/ops/formal_action_deployment_v1/runtime_scope.py')
ck(h.Evidence.__module__==h.__name__,'original Evidence no overlay class')
panel=read(R/b.PANEL,b.PANEL_SHA);sys.path.insert(0,str(S/'src'));from cti_vla.evaluation import formal_trials
pairproof=[];invpaths=set()
for key in b.KEYS:
 item=index['pairs'][key];ev=h.Evidence(R);sources=h.source_contract(ev,h.SOURCE_INVENTORY);reg=h.registration_contract(ev,h.REGISTRATION)
 rows=h.suite_rows(ev,reg,'libero_goal',sources,item['method_ids']);manifest_actual=h.make_execution(reg,'libero_goal',rows,split='development');manifest_actual.update(development_panel=b.PANEL,development_panel_sha256=ev.watch(b.PANEL));ev.unchanged()
 def rr(field):r=item[field];return read(R/r['path'],r['sha256'])
 ck(manifest_actual==rr('execution_manifest'),'original source/provenance manifest reconstructed '+key)
 scientific=planner.plan(b.args_for(key),copy.deepcopy(state),project=R,helper=h)
 ck(scientific==rr('scientific_plan'),'canonical original planner no overlay '+key)
 ck(scientific['invocation']['source_provenance']==ev.source_provenance['libero_goal']==rr('source_provenance'),'full own-pair provenance reconstructed '+key)
 action=rr('execution_contract');contract.validate_execution_contract(action,scientific['invocation']);runtime.validate_contract(action['runtime_contract'],project_root=R,source_root=S)
 effective=contract.effective_plan(scientific,scientific_plan_ref=item['scientific_plan'],execution_contract_ref=item['execution_contract'],execution_contract=action)
 ck(effective==rr('effective_plan') and effective['invocation']==rr('invocation_template'),'original effective envelope and raw consumer pre-execution closure '+key)
 for rel,pin in action['files'].items():ck(sha(R/rel)==sha(P/rel)==pin,'exact original action source R/P '+key+' '+rel)
 spec=rr('specification');expected=[dict(ordinal=i+1,**formal_trials._identity(panel,s,mid)) for i,(s,mid) in enumerate((s,m) for s in panel['states'] for m in item['method_ids'])]
 ck(spec['rows']==expected and spec['rows_signature_sha256']==b.sig(expected),'all200 exact original ordered trial identities '+key)
 ck(len({r['state_trial_id'] for r in expected})==100 and len({r['trial_id'] for r in expected})==200,'100 initial states and200 unique method trials '+key)
 ck(spec['scientific_environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':300},'frozen environment independent of training seed '+key)
 ck(spec['maximum_control_steps']==60000 and spec['maximum_policy_queries']==7600 and spec['maximum_new_attempts']==1 and spec['automatic_retry'] is False,'fixed full200 bounds '+key)
 ck(item['planned_invocation_path'] not in invpaths and item['planned_invocation_path']!='results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json','unique own invocation path '+key);invpaths.add(item['planned_invocation_path'])
 ck(scientific['invocation']['prior_job_ids']==[] and scientific['invocation']['prior_allocation_cost']==[] and scientific['invocation']['prior_review'] is None,'no fabricated prior execution '+key)
 pairproof.append({'pair_key':key,'pair_id':item['pair_id'],'method_ids':item['method_ids'],'canonical_scientific_plan':item['scientific_plan'],'execution_manifest':item['execution_manifest'],'effective_plan':item['effective_plan'],'source_provenance':item['source_provenance'],'specification':item['specification'],'original_evidence_files':ev.files,'runtime_sources':action['files'],'original_output':item['original_output'],'future_typed_output':item['actual_runtime_output_proposed'],'original_manifest_and_planner_rebuilt':True,'helper_overlay_used':False,'actual_new_runtime_P_verified':False})
 print(key+' independently reconstructed canonical manifest/planner',flush=True)
t=load(A/'v2/test_plans_v3.py','9334c30153740ace4ab445f1edf2c2e080bb8c7b94cc7f567febaf9586dc8369','ind_remaining5_CPU_replay')
replay=t.run(indexpath,sha(indexpath));ck(replay['status']=='passed' and replay['positive']==36 and replay['rejections']==340,'complete saved source CPU positive/refusal replay36/340');write(D/'author_CPU_replay.json',replay)
ck(statepath.read_bytes()==state_raw,'state remained byte-identical throughout independent read')
source=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck(len(source['files'])==173,'173 source set')
for rel,pin in source['files'].items():ck(sha(R/rel)==sha(S/rel)==pin,'original173 R/S '+rel)
report={'schema':'formal_main_v2','kind':'Goal_remaining5_canonical_original_plan_independent_review','status':'passed_canonical_original_plan_and_CPU_review','reviewed_by':'independent','candidate_index':ref(indexpath),'author_manifest':ref(A/'delivery_manifest.json'),'state_snapshot':ref(D/'state_snapshot.json'),'canonical_publication_target_count':75,'publication_files':publications,'pair_count':5,'pairs':pairproof,'helper_overlay_used':False,'original_scientific_guards_preserved':True,'source173_verified':True,'author_CPU_replay':ref(D/'author_CPU_replay.json'),'CPU_positive':36,'CPU_rejections':340,'new_trials':0,'new_GPU_jobs':0,'actual_new_runtime_P_verified':False,'actual_GPU_runtime_chain_verified':False,'production_admitted':False,'old200_HOLD':True,'final_evaluation_enabled':False,'blockers':[],'remaining_production_gates':['root prepared exact invocation and new typed runtime source/CPU review','actual published P entry source/identity/capacity verification','new exact five-scope atomic gateway/aggregate capacity/one ACK admission','new per-pair real raw terminal and independent acceptance'],'check_count':len(checks),'checks':checks}
write(D/'canonical_independent_rebuild.json',report);proofsha=sha(D/'canonical_independent_rebuild.json');reviewmap=[]
for item in index['pairs'].values():
 v=prep.expected_review(item,index,'independent');action=read(R/item['execution_contract']['path'],item['execution_contract']['sha256']);v.update(runtime_sources=action['files'],blockers=[],review_evidence={'canonical_original_rebuild':{'path':E+'/canonical_independent_rebuild.json','sha256':proofsha}},review_scope='Canonical original metadata/source/consumer pre-execution closure plus CPU refusals; no new typed runtime admission',canonical_reconstruction_without_overlay=True)
 q=D/(item['pair_key']+'_plan_independent_review.json');write(q,v);reviewmap.append({'source':str(q.relative_to(R)),'destination':b.X+'/'+item['pair_key']+'/plan_independent_review.json','sha256':sha(q),'bytes':q.stat().st_size})
write(D/'review_publication_map.json',{'evidence_must_be_archived_first':{'source':str((D/'canonical_independent_rebuild.json').relative_to(R)),'destination':E+'/canonical_independent_rebuild.json','sha256':proofsha},'reviews':reviewmap,'production_admitted':False})
files=[ref(p) for p in sorted(D.iterdir()) if p.is_file()];write(D/'delivery_manifest.json',{'schema':'formal_main_v2','kind':'independent_audit_delivery_manifest','source_root':str(D.relative_to(R)),'file_count':len(files),'files':files})
print(json.dumps({'review':ref(D/'canonical_independent_rebuild.json'),'manifest':ref(D/'delivery_manifest.json'),'publication_map':ref(D/'review_publication_map.json'),'checks':len(checks),'CPU_positive':36,'CPU_rejections':340},sort_keys=True))
