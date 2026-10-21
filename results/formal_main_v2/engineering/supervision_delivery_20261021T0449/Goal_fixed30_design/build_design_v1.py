README="# Goal 自身固定30观测：CPU设计与执行缺口\n\n本包只派生已登记规则的 Goal 选择清单，不是采集计划准入、GPU授权、成功率结果或O2A结果。Goal 原200仍HOLD。没有修改canonical/P/state/Git/冻结源，也未读取封存值或权重。\n\n原 formal_main_v2.profiling 和冻结 fixed_profile_states 已确定：每个task0..9选该套件100开发初态中 source_state_index 最小者。Goal的10个索引为 **7,2,3,4,4,1,10,1,4,9**。本包直接执行原纯函数和开发面板校验器，生成10个原身份与30个first/middle/last槽位，不另选科研面板。空间位置、状态内容SHA和任务顺序绑定Goal面板 ce8e3d31…；中末实际步号与观测/NPZ哈希尚不存在，清单显式为null，不伪造未来观测。\n\n每条原Dense512两视角轨迹只运行一次，runtime seed17、环境seed0、wait10、chunk8、Goal horizon300、query watchdog60秒。采集所有post-wait、每控制步实际执行前观测的哈希，从实际N个观测中保留0、floor((N−1)/2)、N−1三份原始观测；N<3必须失败，不能填充、换初态或按成功率筛选。最大10轨迹/3000policy控制步/380策略query，另100wait步。采集ledger独立，所有正常失败保留；采集不增成功率分母，不产生额外唯一科研初态，不视作完整延迟。\n\nGoal官方基座为moojink/openvla-7b-oft-finetuned-libero-goal，revision c2d0f9fbbd82674683b397ff923168a12f6a307b；继承原Goal输入验收 frozen_model_sha25685703124930f24771cd4d04a4e88309710fcfc230e4891a1e6578d7ec14a45a2。这是原元数据引用，不冒称本轮重新读权重验收。Goal component-filename/asset兼容层必须进入新collect完整闭包，不能只换suite字符串。\n\n前三套件Long3047982、Spatial3053503、Object3053518各30已验收。本包核其原计划/根及独审引用，并以原选择函数重建10个身份和30个实际first/middle/last步号；没有重复GPU，也没有冒称重做原完整科学consumer。详细引用在prior_accepted_collection_evidence.json。\n\n当前HOLD项见readiness_gaps.json：Goal-own dense execution manifest、原collect scientific/effective plan、完整源与实际P wrapper核验、新exact-one gateway、root/independent readiness、锁/CAS和八槽含所有模式容量、独占新attempt与精确回存、最终真实原consumer+独审。旧posttraining collect gateway只授权两份确切Spatial/Object计划；旧exclusive full200与本轮remaining5也只授权其各自A/B开发，均不能拿来提交Goal dense collect。训练控制器已完成，不能为填槽重启。\n\n建议下一轮先由原suite_rows/make_execution派生Goal dense-only身份和原collect计划，再为这一确切计划新建一次性网关；需同时排除Goal其他活动开发/采集冲突。提交不确定仅对唯一原ACK补登记，不清pending重发；失败输出与成本全部保留，不自动重试。单GPU资源、节点排除、源/配置/数据/模型身份和原action语义按新确切计划双审，不在此CPU设计中伪填收据。\n\n30份五组件理论裸数组载荷11798640B仅作内容量参考，不是NPZ、报告、临时文件或日志总上界；实际存储/精确allowlist需后续独审。全部产物只服务器；NPZ为非权重开发观测，可按未来实际逐SHA allowlist回存Git，不能泛化到任意raw或封存值。\n\n这30份仅为Goal未来自身计时输入，不能用其他套件观测或Spatial延迟替代。全部72checkpoint、16参考身份、四套件开发收据及最终清单全局冻结前不开展完整O2A或分项计时；root global release前最终35200仍封存。\n"
"""CPU design only: derive Goal's already registered fixed30 selection; no science execution."""
from pathlib import Path
import ast,copy,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).parent
assert D==R/'.local/goal30_fixed_observation_design_20261021T0449'
evidence={};checks=[];negative=0
def digest(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin=None):
 p=R/rel;b=p.read_bytes();h=digest(b)
 if pin:assert h==pin
 evidence[rel]={'sha256':h,'bytes':len(b)}
 return json.loads(b) if p.suffix=='.json' else b.decode()
def ref(rel):return dict(path=rel,**evidence[rel])
def write(n,v):
 b=(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with (D/n).open('xb') as f:f.write(b)
 return {'path':n,'sha256':digest(b),'bytes':len(b)}
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def reject(name,fn):
 global negative
 try:fn()
 except ValueError:negative+=1;ck(name,True)
 else:ck(name,False)
REG='configs/experiments/formal_main_v2.json'
reg=read(REG,'a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
SRC='src/cti_vla/evaluation/formal_profiling.py'
src=read(SRC,'56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80')
ck('R_and_frozen_S_profiling_identical',(S/SRC).read_bytes()==src.encode())
sys.path.insert(0,str(S/'src'))
nodes=[n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name in ['fixed_profile_states','selected_control_steps','profile_registration']]
ck('exact_three_original_pure_functions',len(nodes)==3)
ns={'FORMAL_SCHEMA':'formal_main_v2'}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(S/SRC),'exec'),ns)
ns['profile_registration'](reg)
ck('already_registered_state_rule',reg['profiling']['source']=='lowest source_index development state each task; one fixed dense collection trajectory')
ck('already_registered_phase_rule',reg['profiling']['observations_per_suite']==30 and '0,floor((N-1)/2),N-1' in reg['profiling']['observation_indices'])
selectionproof={'original_source':ref(SRC),'functions':{n.name:{'AST_sha256':digest(ast.dump(n,include_attributes=False).encode()),'source':ast.get_source_segment(src,n)} for n in nodes},'execution_scope':'CPU only original pure functions and development-panel validator; no simulator/policy/weights'}
prior=[]
refs=[('Long','libero_10','3047982','long_collect_action_v1_0830'),('Spatial','libero_spatial','3053503','spatial_collect_action_v1_20261020T1825'),('Object','libero_object','3053518','object_collect_action_v1_20261020T1825')]
for label,suite,jid,x in refs:
 panelrel=f'configs/manifests/formal_main_v2/{suite}/initial_states/development.json'
 dev=read(panelrel);selected=ns['fixed_profile_states'](dev)
 reviewrel=f'results/formal_main_v2/downstream_reviews/{jid}.json'
 rv=read(reviewrel);indrel=f'results/formal_main_v2/downstream_reviews/{jid}_independent.json';ind=read(indrel)
 ck(label+'_root_accepted30',rv['status']=='passed' and rv['observations']==30 and rv['completed_collection_trajectories']==10 and rv['scientific_complete'] is True and rv['final_state_values_read'] is False)
 ck(label+'_distinct_independent_evidence',indrel!=reviewrel and 'passed' in str(ind.get('status','')))
 planrefs={}
 for name in ['scientific_plan.json','effective_plan.json','dense_development.json','execution_contract.json','runtime_readiness.json','submission_authorization.json']:
  rel=f'results/formal_main_v2/execution/{x}/{name}';read(rel);planrefs[name]=ref(rel)
 run=Path(rv['run_root']).relative_to(P)
 trajectories=[]
 for row in selected:
  rel=(run/f"task{row['task_id']:02d}/receipt.json").as_posix()
  rec=read(rel);n=rec['trajectory']['control_steps']
  ck(label+str(row['task_id'])+'_fixed_identity',all(rec['state'][k]==row[k] for k in ['trial_id','task_id','task_name','source_state_index','initial_state_sha256']))
  ck(label+str(row['task_id'])+'_original_actual_phase_rule',[o['control_step'] for o in rec['observations']]==ns['selected_control_steps'](n))
  ck(label+str(row['task_id'])+'_collection_not_scientific',rec['new_success_trials'] is False and rec['test_opened'] is False)
  trajectories.append({'state':{k:row[k] for k in ['task_id','task_name','source_state_index','initial_state_sha256']},'actual_control_steps':n,'selected_control_steps':ns['selected_control_steps'](n),'receipt':ref(rel)})
 prior.append({'suite':suite,'job_id':jid,'root_terminal_review':ref(reviewrel),'independent_terminal_review':ref(indrel),'plans':planrefs,'development_panel':ref(panelrel),'accepted_observations_from_prior_review':30,'selection_metadata_rebuilt_now':True,'full_original_consumer_rerun_now':False,'trajectories':trajectories})
goalrel='configs/manifests/formal_main_v2/libero_goal/initial_states/development.json'
goal=read(goalrel,'ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9')
ck('Goal_development_panel_R_P_identical',(P/goalrel).read_bytes()==(R/goalrel).read_bytes())
chosen=ns['fixed_profile_states'](goal)
ck('Goal_original100_states10tasks',len(goal['states'])==100 and len(chosen)==10 and [r['task_id'] for r in chosen]==list(range(10)))
ck('Goal_exact_registered_minimum_indices',[r['source_state_index'] for r in chosen]==[7,2,3,4,4,1,10,1,4,9])
bad=copy.deepcopy(goal);bad['split']='final';reject('refuse_non_development_panel',lambda:ns['fixed_profile_states'](bad))
bad=copy.deepcopy(goal);bad['states'][0]['source_state_index']+=1;reject('refuse_changed_signed_state_panel',lambda:ns['fixed_profile_states'](bad))
for n in [3,4,9,299,300]:
 ck('phase_rule_'+str(n),ns['selected_control_steps'](n)==[0,(n-1)//2,n-1])
for n in [0,1,2,-1,True,3.0,'3',None]:
 reject('no_padding_or_invalid_count_'+repr(n),lambda n=n:ns['selected_control_steps'](n))
states=[{k:r[k] for k in ['trial_id','task_id','task_name','source_file','source_state_index','initial_state_sha256']} for r in chosen]
slots=[]
for state in states:
 for phase,expression in [('first','0'),('middle','floor((N-1)/2)'),('last','N-1')]:
  slots.append({'slot_ordinal':len(slots)+1,'slot_id':state['trial_id']+':'+phase,'state':state,'phase':phase,'control_step_expression':expression,'actual_control_steps_N':None,'actual_observation_sha256':None,'actual_npz_sha256':None,'actual_observation_id_template':f"task{state['task_id']:02d}:state{state['source_state_index']:04d}:step<selected_control_step:04d>",'status':'planned_registered_rule_not_collected'})
ck('Goal30_distinct_fixed_slots',len(slots)==len({x['slot_id'] for x in slots})==30)
assetrel='configs/assets/openvla_oft_libero_goal.json';asset=read(assetrel,'6aaef6cd88a3968a13591fc196a3498c1780c7aab7a5e782a53c1967911a0ed5')
strictrel='configs/assets/formal_main_v2_strict/libero_goal.json';strict=read(strictrel,'e55eac83f28854318524ba87fc6554c7a9708b328700232c055deb66a72e0d6c')
acceptrel='results/formal_main_v2/libero_goal/acceptance/root_review.json';accept=read(acceptrel,'d994d25717d59f3b709944f3e8b2582c173ebd14febb853f49e5eec61ce8dddc')
inputrel=accept['output_relative']+'/input_acceptance.json';inp=read(inputrel,'a25927ec8a25e1bc72cb87fb963216223ea8307a830699f0bee87c583fe92cb0')
ck('Goal_official_base_revision',asset['repository']==strict['repository']=='moojink/openvla-7b-oft-finetuned-libero-goal' and asset['revision']==strict['revision']==inp['model_revision']==reg['suites']['libero_goal']['model_revision'])
ck('Goal_existing_input_identity',accept['status']=='passed' and accept['files']['input_acceptance.json']==evidence[inputrel]['sha256'] and inp['frozen_model_sha256']=='85703124930f24771cd4d04a4e88309710fcfc230e4891a1e6578d7ec14a45a2')
for rel in ['scripts/profile_formal.py','scripts/ops/formal_evaluation_adapter.py','scripts/ops/formal_action_deployment_v1/contract.py','scripts/ops/formal_action_deployment_v1/wrapper.py','scripts/ops/formal_action_deployment_v1/reviewer.py','scripts/ops/formal_action_deployment_v1/consumer.py','scripts/ops/formal_action_deployment_posttraining_v1/gateway.py','configs/experiments/formal_main_v2_goal_component_compat_v1.json','docs/正式下游阻塞登记_20261021T0334.md']:
 read(rel)
oldgw=read('scripts/ops/formal_action_deployment_posttraining_v1/gateway.py')
ck('old_completed_training_gateway_excludes_Goal',"'libero_goal':" not in oldgw[oldgw.index('COMPLETED_COLLECT_PLANS'):] if 'COMPLETED_COLLECT_PLANS' in oldgw else "'libero_spatial': {'path':" in oldgw and "'libero_object': {'path':" in oldgw)
collection={'schema':'formal_main_v2','kind':'Goal_fixed30_collection_design','status':'fixed_selection_CPU_design_execution_HOLD','suite':'libero_goal','mode':'collect','selection_authority':ref(REG),'development_panel':ref(goalrel),'registered_rule_source':ref(SRC),'selected_state_rule':reg['profiling']['source'],'selected_states':states,'observation_slots':slots,'expected_observations':30,'dense_trajectories':10,'method_ids':['dense'],'visual_tokens':512,'environment':{'runtime_seed':17,'environment_seed':0,'wait_steps':10,'action_chunk':8,'max_control_steps':300,'query_watchdog_seconds':60},'maximum_policy_control_steps':3000,'maximum_policy_queries':380,'maximum_wait_steps':100,'phase_rule':reg['profiling']['observation_indices'],'minimum_actual_control_observations_per_trajectory':3,'replacement_or_padding_allowed':False,'success_based_selection':False,'official_base':{'asset_manifest':ref(assetrel),'strict_compatibility_manifest':ref(strictrel),'repository':asset['repository'],'revision':asset['revision'],'frozen_model_sha256':inp['frozen_model_sha256'],'input_acceptance':ref(inputrel),'inherited_root_acceptance':ref(acceptrel)},'weights_read_or_deserialized_this_design':False,'actual_observations_collected':0,'new_success_trials':0,'new_unique_scientific_initial_states':0,'O2A_or_components_authorized':False,'global_freeze_replaced_by_collection':False,'sealed_values_read':False,'GPU_submission_authorized':False,'automatic_retry':False,'maximum_attempts_proposed':1,'single_GPU_job_proposed':1,'all_allocated_seconds_count_once':True,'originalGoal200_HOLD':True,'final_release':False}
blockers=[
 {'id':'G30_PLAN','requirement':'Build Goal-own Dense512 execution manifest with original suite_rows/make_execution, own acceptance/source/model identities, original collect scientific plan and exact action execution contract; no A/B/full200 invocation reuse.'},
 {'id':'G30_SOURCE_AND_RUNTIME','requirement':'Root and independent review full Goal collect source closure including Goal component-filename and asset metadata compatibility, actual original profiling collect/action semantics, frozen-source guards and actual P wrapper verification.'},
 {'id':'G30_GATEWAY','requirement':'Implement and separately audit a new exact-one Goal collect gateway; old completed-training gateway admits exactly Spatial/Object plans and cannot be widened implicitly. Neither full200 nor remaining5 gateway permits dense collection.'},
 {'id':'G30_TRANSACTION','requirement':'Before any unique held submission, reconcile registered project jobs/pending original token/ACK, prove terminated training-controller identity/available lease, writer-lock/CAS reservation, all-mode8GPU cap and Goal-suite overlap exclusion; no fill-slot controller restart.'},
 {'id':'G30_STORAGE_AND_PULL','requirement':'Freeze own new attempt output and exact metadata/raw NPZ/log pull inventory, verify actual server capacity/permissions before launch, retain every attempted output/cost. Expected30 five-component uncompressed observation payload is11798640B, not a final NPZ/log capacity bound; derive actual serialization/temporary/log budget.'},
 {'id':'G30_TERMINAL','requirement':'After real terminal, original reviewer plus original consumer and different-agent review must rebuild10 dense trajectories/all controls/queue/finite/actions, exact fixed state identities andN>=3 first/middle/last NPZ hashes, original base unchanged, one allocation and no success/latency denominator increment. Failed/short collection stops without substituting states.'},
 {'id':'G30_TIMING_CLOSED','requirement':'Collect30 alone opens no latency test. All72 checkpoints,16reference identities,four suite development receipts and final manifest still need global freeze before same-checkpoint fullO2A and independent components; final35200 remains sealed until root globalrelease.'}
]
write('source_rule_derivation.json',selectionproof)
write('prior_accepted_collection_evidence.json',{'schema':'formal_main_v2','kind':'inherited_prior_fixed30_selection_evidence','suites':prior,'full_terminal_audits_rerun':False,'new_GPU_seconds':0})
write('Goal_fixed30_design.json',collection)
write('readiness_gaps.json',{'schema':'formal_main_v2','status':'HOLD_no_Goal_collect_entry_or_GPU_authorization','blockers':blockers,'actual_scientific_plan_generated':False,'actual_observation_bytes_generated':False,'canonical_or_P_writes':0})
write('source_inventory.json',{'schema':'formal_main_v2','files':evidence,'weights_or_sealed_values_read':False,'source_files_unchanged':True})
report={'status':'passed_CPU_fixed_selection_design_only','checks':checks,'check_count':len(checks),'rejections':negative,'production_ready':False,'GPU_submissions':0,'scientific_trials_added':0,'collection_completed':False,'blockers':blockers}
write('CPU_design_report.json',report)
with (D/'README.md').open('x',encoding='utf8') as f:f.write(README)
files=[]
for p in sorted(D.iterdir()):
 if p.is_file():files.append({'path':p.name,'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size})
m=write('delivery_manifest.json',{'schema':'formal_main_v2','kind':'Goal_fixed30_CPU_design_delivery','status':'frozen_design_only_execution_HOLD','source_root':str(D),'file_count':len(files),'files':files,'canonical_or_P_writes':0,'new_GPU_submissions':0,'weights_or_sealed_values_read':False})
print(json.dumps({'manifest':m,'checks':len(checks),'rejections':negative,'selected_source_indices':[r['source_state_index'] for r in states]}))
