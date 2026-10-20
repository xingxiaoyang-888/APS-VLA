# CPU-only immutable-input forensic reconstruction; no experiment launch or gate mutation.
from pathlib import Path
import ast,hashlib,json,time
from collections import Counter
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).resolve().parent
INITIAL='5d0e63172c7ef5d2be8e9451bfca1200b0af32b8a31d6f2b82ea23aef37a2172';TASK='libero_goal:put_the_wine_bottle_on_top_of_the_cabinet:state-0042:env-0'
OA='97bfd36f45edd0e11cfa4595638347815487a897fe42218488e75f7594f2760d';OB='5967f63ad305137d44d4cdfe2a6c77aeee725cbab63c4b8ebe5edaa5a1867294';METHODS=['A256_seed17','B256_seed17'];CHECKS=[]
def check(name,ok):
 CHECKS.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,value):
 p=D/name
 if p.exists():raise RuntimeError('immutable output exists: '+name)
 p.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def target(x):return x.get('event')=='result' and x.get('suite')=='libero_goal' and x.get('task_id')==2 and x.get('source_state_index')==42 and x.get('state_trial_id')==TASK and x.get('initial_state_sha256')==INITIAL

def run():
 started=time.monotonic();refs=json.loads((D/'pinned_inputs.json').read_text())
 for k,r in refs.items():check('input:'+k,sha(r['path'])==r['sha256'])
 def data(k):return json.loads(Path(refs[k]['path']).read_text())
 def lines(k):return [json.loads(l) for l in Path(refs[k]['path']).read_text().splitlines()]
 def source(k):return Path(refs[k]['path']).read_text()
 inv=data('source_inventory');check('173 frozen inventory files',len(inv['files'])==173)
 def frozen_check(phase):
  for rel,digest in inv['files'].items():
   for root,name in [(R,'R'),(S,'S')]:check('frozen_'+phase+':'+name+':'+rel,sha(root/rel)==digest)
 frozen_check('before')
 ledger=lines('ledger');events=lines('probe_events');oe=lines('original_action_events');results=[x for x in ledger if x.get('event')=='result'];starts=[x for x in ledger if x.get('event')=='start']
 check('ledger count/events',len(ledger)==401 and Counter(x['event'] for x in ledger)=={'invocation':1,'start':200,'result':200});check('200 unique result ids',len({x['trial_id'] for x in results})==200)
 check('state-major AB order',all([results[i]['method'],results[i+1]['method']]==METHODS and results[i]['state_trial_id']==results[i+1]['state_trial_id'] for i in range(0,200,2)))
 targets=[x for x in results if target(x)];check('exact target arms',[x['method'] for x in targets]==METHODS);check('target hashes',[x['chunks'][0]['observation_sha256'] for x in targets]==[OA,OB])
 for k,v in [('task_id',4),('initial_state_sha256','0'*64),('state_trial_id',TASK.replace('0042','0038'))]:
  other=dict(targets[0]);other[k]=v;check('negative ambiguous identity:'+k,not target(other))
 check('only development',all(x['split']=='development' for x in starts+results));check('all configured seeds/waits/chunks',all(x['environment_seed']==0 and x['runtime_seed']==17 and x['configured_wait_steps']==10 and x['action_chunk']==8 for x in results))
 check('target ordinals57/58',[results.index(x)+1 for x in targets]==[57,58]);check('prior56 counts',sum(x['policy_calls'] for x in results[:56])==916 and sum(x['control_steps'] for x in results[:56])==7124 and sum(x['wait_steps'] for x in results[:56])==560)
 prefix=[]
 for i,x in enumerate(results[:58]):
  y={k:x[k] for k in ('trial_id','state_trial_id','method','task_id','task_name','source_state_index','initial_state_sha256','environment_seed','runtime_seed','policy_calls','control_steps','wait_steps','created_utc')};y.update(ordinal=i+1,start_utc=starts[i]['created_utc'],start_ledger_index=ledger.index(starts[i]),result_ledger_index=ledger.index(x),t0_postquery_hash=x['chunks'][0]['observation_sha256'],executed_actions_sha256=hashlib.sha256(json.dumps(x['executed_actions'],sort_keys=True,separators=(',',':')).encode()).hexdigest());prefix.append(y)
 write('original_prefix58.json',{'source':refs['ledger'],'kind':'observed_history_not_new_execution','unique_development_states':len({x['state_trial_id'] for x in prefix}),'rows':prefix,'success_outcomes_not_used':True})
 ft=source('formal_trials_source');lr=source('libero_runtime_source');en=source('formal_entry_source');ps=source('probe_source');ew=source('env_wrapper_source')
 f=next(n for n in ast.parse(ft).body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_formal_trials');calls=[(ast.unparse(n.func),n.lineno) for n in ast.walk(f) if isinstance(n,ast.Call)]
 for label in ['reseed','environment_factory','run_episode','env.close']:check('source call:'+label,any(k==label for k,l in calls))
 at=ft.index('def evaluate_formal_trials');check('reseed and new env inside method loop',ft.index('for identifier in methods:',at)<ft.index('reseed()',at)<ft.index('env, instruction = environment_factory(state)',at))
 check('original hash after query before policy step',lr.index('chunk = predict_chunk(observation, instruction)')<lr.index('"observation_sha256": _observation_hash(observation)')<lr.index('observation, _, done, _ = env.step(action.tolist())'))
 check('no original perarray/prequery evidence',all('prequery_sha256' not in x['chunks'][0] and 'per_array_difference' not in x['chunks'][0] for x in targets));check('reset suppression source','finally:' in ew and 'continue' in ew[ew.index('    def reset('):ew.index('    def reset(')+700])
 check('probe source fresh environment','for index,mid in enumerate(ORDER)' in ps and 'env,instruction,identity=factory(state)' in ps and 'env.close()' in ps)
 check('original runtime restored',data('original_action_completion')['runtime_restored'] and data('original_action_completion')['immutable_inputs_unchanged']);check('original23 event sequence',[x['seq'] for x in oe]==list(range(23)));check('probe443 event sequence',[x['seq'] for x in events]==list(range(443)))
 c=data('probe_completion');pd=c['diagnostics'];q=pd['query_records'];check('probe completed GPU',c['real_GPU_probe_completed'] is True and c['exit_code']==0);check('fixedABBA3',[x['method_id'] for x in q]==['A256_seed17','B256_seed17','B256_seed17','A256_seed17']*3)
 check('probe12/120/0',len(q)==12 and sum(x['wait_actions_executed'] for x in q)==120 and sum(x['policy_actions_executed'] for x in q)==0);check('probe commonB prepost',all(x['prequery_sha256']==x['postquery_sha256']==OB and x['input_unchanged'] for x in q));check('six pairs equal',len(pd['pair_diagnostics'])==6 and all(x['prequery_equal'] and x['postquery_equal'] for x in pd['pair_diagnostics']))
 check('probe science HOLD',pd['scientific_gate']=='HOLD' and pd['scientific_trials_accepted']==0 and pd['retry_authorized'] is False and c['original_200_trials_replaced'] is False)
 selected=data('probe_selected_state');check('same target initial identity',selected['trial_id']==TASK and selected['initial_state_sha256']==INITIAL and selected['task_id']==2 and selected['source_state_index']==42)
 comparisons=[]
 for t in targets:
  b=t['chunks'][0]
  for z in [x for x in q if x['method_id']==t['method']]:
   a=np.asarray(b['environment_actions']);az=np.asarray(z['environment_actions']);n=np.asarray(b['normalized_actions']);nz=np.asarray(z['normalized_actions'])
   row={'original_trial_id':t['trial_id'],'probe_label':z['label'],'method':t['method'],'same_all_metadata':b['metadata']==z['policy_metadata'],'same_retained_indices':b['metadata']['retained_indices']==z['policy_metadata']['retained_indices'],'environment_actions_equal':bool(np.array_equal(a,az)),'environment_actions_max_abs_difference':float(np.max(np.abs(a-az))),'normalized_actions_equal':bool(np.array_equal(n,nz)),'normalized_actions_max_abs_difference':float(np.max(np.abs(n-nz)))}
   check('same metadata:'+z['label'],row['same_all_metadata']);check('same tokens:'+z['label'],row['same_retained_indices']);check('action equality direction:'+z['label'],row['environment_actions_equal']==t['method'].startswith('B'));comparisons.append(row)
 job=next(j for j in data('original_state_snapshot')['registered_jobs'] if str(j['job_id'])=='3049679');alloc=data('probe_scheduler')['scheduler']['rows']['3050711'];cmd=job['downstream_gateway']['actual_sbatch_argv'][-1];sl=source('probe_slurm');threads={'OMP_NUM_THREADS':'7','OPENBLAS_NUM_THREADS':'7','MKL_NUM_THREADS':'7','TF_NUM_INTRAOP_THREADS':'7','TF_NUM_INTEROP_THREADS':'1'}
 for k,v in threads.items():check('same configured threads:'+k,k+'='+v in cmd and k+'='+v in sl)
 check('camera256 configured both','camera_heights=256' in en and 'camera_widths=256' in en and 'camera_heights=256' in ps and 'camera_widths=256' in ps)
 check('seed17 code both',all(x in en and x in ps for x in ['random.seed(17)','np.random.seed(17)','torch.manual_seed(17)']));check('envseed0 both','env.seed(0)' in en and 'env.seed(0)' in ps);check('common oneDNN warning not differential','oneDNN custom operations are on' in source('original_stderr') and 'oneDNN custom operations are on' in source('probe_stderr'))
 write('source_reading.json',{'source_call_sites':calls,'original_hash_timing':'after predict_chunk returns, before first policy env.step','environment_lifecycle':'fresh/reseed each trial; close in finally','reset_gap':'finally:continue suppresses internal reset exceptions; no retries logged; no retry occurrence inferred','configured_threads':threads,'original_runtime_thread_counts':'not recorded','original_node':job['node'],'probe_node':alloc['node'],'node_difference_not_causal_proof':True,'original_runtime':data('original_config')['runtime'],'probe_runtime':data('probe_identity')['runtime']})
 write('same_arm_query_comparison.json',{'kind':'diagnostic_only_no_gate_acceptance','rows':comparisons,'same_metadata_and_tokens_not_equivalence':True})
 proposal={'version':'goal-original-prefix-t0-diagnostic-draft-v1','status':'proposal_only_not_authorized_not_run','maximum_attempts':1,'automatic_retry':False,'GPU_jobs':1,'GPUs':1,'hard_Slurm_wall_seconds':1800,'counts_toward_eight_GPU_slots':True,'scientific_trials_accepted':0,'original200_HOLD_unchanged':True,'sealed_values_access':False,'requires_root_and_independent_review_before_submission':True,'source_inventory':refs['source_inventory'],'original_invocation':refs['original_invocation'],'original_panel':refs['panel'],'checkpoint_identities':{t['method']:t['chunks'][0]['metadata']['selector_checkpoint_sha256'] for t in targets},'prefix':{'path':str(D/'original_prefix58.json'),'sha256':sha(D/'original_prefix58.json')},'fixed_scope':'Original first58 state-major A/B trial identities,29 previously used development states, no substitution based on success','same_settings':{'suite':'libero_goal','tokens':256,'seed':17,'envseed':0,'camera':[256,256],'wait_steps':10,'action_chunk':8,'max_control_steps':300},'maximum_trials':58,'maximum_policy_controls':17400,'maximum_dummy_controls':580,'historical_actual_actions_replayed':False,'execution_semantics':'Re-execute unchanged original closed-loop policy/environment in exact fixed identity/order prefix, stopping after58. Never force recorded actions, observations or early termination to match. Record actual divergence. This is source/order re-execution, not exact realized-trajectory replay.','historical_action_replay_limitation':'Recorded actions alone omit model-call/GPU history; predict then override actions changes closed-loop semantics. Neither is adopted as exact reproduction.','why58':'Shortest original invocation prefix including both offending A and paired B, derived from anomaly location, not performance. Prior12-query probe omitted first56 rollouts.','observer':'New explicit reviewed observer; copy five original obs arrays/hash/dtype/shape and simulator/RNG state at reset,set_init,each dummy and t0 pre/post query. No extra policy/step/reset/render/update_observables/random/warmup/synchronization calls. Preserve returned objects and original query timer. No scientific latency inference from instrumented run.','observer_validation':'CPU mutation/RNG sentinels and AST differential prove only passive capture plus fixedstop58; bind source,checkpoint,loading order. GPU records array/RNG equality around observer. Observer changes timing/history and cannot be asserted completely non-perturbing.','application_timeout':'Best effort because inherited reset swallows exceptions; Slurm1800-second bound required. Do not silently patch reset.','fail_closed':['identity or observer semantics unproven: no submission','visible exception/corrupt trace: stop and preserve; no automatic retry','58 complete or1800seconds ends one attempt','prequery different: locate first reset/set_init/wait component divergence','prequery same/postquery different: directly supports input mutation investigation only','images differ but proprio/sim match: rendering investigation candidate, not harmlessness proof','target not reproduced: inconclusive,HOLD unchanged','all cases: original200 remains rejected; no automatic scientific retry'], 'repair_policy':'No repair justified yet. Reproduced-cause patch requires separately registered CPU and real-GPU validation and root approval; never weaken hash gate or retro-accept original200.'}
 write('proposed_single_attempt_registration.json',proposal)
 limitations=['Original has only aggregate postquery t0 hash, no original array/prequery/RNG/sim trace; changed component/time unknown.','Probe did not execute earlier56 rollouts or policy actions; AB/BA concerns query/reset order, not model-loading order.','Different nodes observed, matching thread configuration; missing runtime thread/reset retry evidence cannot be treated as a cause.','Postquery timing does not prove model input mutation; unchanged probe inputs do not exclude nonreproduced original mutation.','Prior terminal report said history-dependent; this report only establishes discrepancy in longer-history run. History dependence is unproved.','Same A tokens/metadata do not establish observation or action equivalence; action differences are diagnostic only.']
 summary={'schema':'formal_main_v2','kind':'read_only_Goal_t0_forensic','created_utc':datetime.now(timezone.utc).isoformat(),'cause':'undetermined','original_mismatch_reproduced':False,'original_hashes':{'A':OA,'B':OB},'all_probe_hash':OB,'original_target_ordinals':[57,58],'prior_A_history':{'trials':56,'queries':916,'policy_controls':7124,'dummy_controls':560},'target_identity':{'state_trial_id':TASK,'initial_state_sha256':INITIAL,'task_id':2,'source_state_index':42},'both_fresh_env_and_reseed':True,'original_hash_timing':'postquery before policy step','same_arm_comparisons':comparisons,'probe':{'queries':12,'dummy_controls':120,'policy_controls':0},'existing_GPU_seconds':{'3049679':job['elapsed_seconds']*job['gpus'],'3050711':alloc['elapsed_seconds']*alloc['gpus']},'already_accounted_costs_not_added_again':True,'new_GPU_jobs':0,'new_GPU_seconds':0,'new_scientific_trials':0,'original200_HOLD_unchanged':True,'source_state_canonical_docs_git_Slurm_mutations':False,'checkpoint_weight_bytes_read':False,'sealed_values_read':False,'limitations':limitations,'next_step':'Single fixed-prefix engineering proposal only; root decides; no present repair or retry authorization.'}
 frozen_check('after')
 for k,r in refs.items():check('input_unchanged:'+k,sha(r['path'])==r['sha256'])
 check('no original200 release',proposal['original200_HOLD_unchanged'] and not proposal['automatic_retry'] and proposal['scientific_trials_accepted']==0)
 summary.update(checks_passed=len(CHECKS),CPU_wall_seconds=time.monotonic()-started);write('report.json',summary);write('checks.json',{'kind':'CPU evidence assertions, not new GPU acceptance','passed':len(CHECKS),'checks':CHECKS})
 report=f'''# Goal t0 异常取证（只读，未启动新实验）

原3049679的200条继续HOLD。probe3050711未复现原A的97bfd36f…，原因未定；不能部署修复、放宽hash门槛或补认原结果。

- 原异常A/B是第57/58条。此前56条累计916次策略query、7124个策略控制动作、560等待动作。原入口和探针均每条重设seed、新建并关闭环境；不能归因为环境复用。
- 原t0 hash在predict_chunk返回后、第一策略动作前记录。没有原prequery和逐数组原件，不能判定差异来自reset/等待/query，更不能由此断言模型改了输入。
- 探针12query/120dummy/0policy，所有pre/post均5967f63a…，与原B相同；未重演前56条历史。AB/BA只平衡query/reset顺序，加载顺序仍A后B。
- 同arm比较：原B和6次probeB首chunk完全一致；原A和6次probeA的token、全部metadata相同，但归一化动作最大差0.00390625、环境动作最大差0.0035470145716998136。token相同不等于输入/动作相同，不用于成功率判断。
- 两次配置同seed17/envseed0、256相机、wait10/chunk8、相同checkpoint；OMP/BLAS/MKL/TF配置相同。原gpu4025、探针gpu4023不同仅为事实，不证明节点原因。原实际线程数、reset内部重试未记录。共同reset源码的finally:continue不能证明原来发生了重试。

下一步仅建议：一次1GPU、最长30分钟、固定前58条（29个已用开发初态、原顺序，含异常A/B），计入8槽，不自动重试。沿原闭环策略实际产生动作，不强制历史动作或终止结果；是同源入口和顺序的前缀重执行，不能称为实际轨迹逐动作重放。记录首个历史偏离以及reset/set_init/等待/t0query前后五数组、sim/RNG和身份。observer经CPU/AST及GPU被动性检查，不新增render/step/query/随机调用，仍须承认时间扰动；不把该运行用于测速。

pre一致而post变化才支持输入修改方向；pre已不同先定位reset/等待。图像单独变化也不可视为无害。未复现/超时/证据不足均继续HOLD，无自动科学重跑。具体草案见proposed_single_attempt_registration.json，尚未授权或执行。原200不会因为probe通过而补认。

{len(CHECKS)}项CPU证据检查通过，含173文件R/S前后核验；新GPU成本0。原2034秒及probe354秒已计成本，不重复累计。来源SHA见pinned_inputs.json，原前缀见original_prefix58.json。未读取封存值/权重，未改变状态、canonical、Git或Slurm。
'''
 (D/'report.md').write_text(report,encoding='utf-8')
 files={str(p.relative_to(D)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(D.rglob('*')) if p.is_file()};write('manifest.json',{'kind':'private_forensic_delivery','private_root':str(D),'files':files,'checks_passed':len(CHECKS),'new_GPU_jobs':0,'new_scientific_trials':0,'original200_HOLD_unchanged':True,'root_integration_only':True,'transport_bundle_sha256':'3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'})
 print(json.dumps({'manifest':str(D/'manifest.json'),'manifest_sha256':sha(D/'manifest.json'),'report_sha256':sha(D/'report.json'),'proposal_sha256':sha(D/'proposed_single_attempt_registration.json'),'checks':len(CHECKS)}))
if __name__=='__main__':run()
