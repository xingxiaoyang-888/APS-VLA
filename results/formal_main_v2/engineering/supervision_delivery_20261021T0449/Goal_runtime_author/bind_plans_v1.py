from pathlib import Path
import hashlib,json,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_remaining5_runtime_20261021T0449';Q=D/'package';PD=R/'.local/goal_remaining5_plans_20261021T0449/v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n')
 return sha(p)
assert sha(PD/'candidate_index.json')=='638ec6f36339aa3a43a78266a60c58427aa40f22979f442cd740432962a28d3f'
index=json.loads((PD/'candidate_index.json').read_bytes())
keys=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
decision={'path':'results/formal_main_v2/preflight/heartbeat_20261021T1249/Goal_remaining5_root_design_decision.json','sha256':'728ba315807e6f17990e548b969d31c1721e5f080fc5de10ef8b530918b492fd'}
storage={'path':'results/formal_main_v2/preflight/heartbeat_20261021T1249/Goal_remaining5_storage_root_decision.json','sha256':'0f3f291473ad57e9d06f1c213310890801aa20a84e2f4b8ea7c5c656a97d1fd7'}
for ref in (decision,storage):assert sha(R/ref['path'])==ref['sha256']
pkg='scripts/ops/formal_goal_remaining5_gate_v1'
registry={'version':'goal-remaining5-prospective-single-attempt-v1','pair_keys':keys,'pairs':{},'root_fixed_design':decision,'root_storage_decision':storage}
resources={'partition':'L40','gres':'gpu:l40:1','cpus_per_task':7,'mem':'64G','wall_seconds':7200,'no_requeue':True,'excluded_nodes':['gpu4020']}
for key in keys:
 row=index['pairs'][key];sub=Q/'pairs'/key;sub.mkdir(parents=True)
 spec=row['specification'];raw=(PD/'publication'/spec['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==spec['sha256']
 with (sub/'specification.json').open('xb') as f:f.write(raw)
 plans={name:row[name] for name in ('execution_manifest','scientific_plan','effective_plan','execution_contract','source_provenance','specification')}
 for name,ref in plans.items():assert sha(PD/'publication'/ref['path'])==ref['sha256']
 x='results/formal_main_v2/execution/goal_remaining5_v1/'+key
 rawpath=R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01'
 c={'schema':'formal_main_v2','kind':'goal_remaining5_single_attempt_configuration','version':registry['version'],'pair_key':key,'stage_key':'goal_remaining5_v1/'+key,'suite':'libero_goal','seed':row['training_seed'],'tokens':row['budget'],'method_ids':row['method_ids'],'runtime_seed':17,'environment_seed':0,'maximum_trials':200,'unique_development_states':100,'wait_steps':10,'action_chunk':8,'max_control_steps':300,'maximum_attempts':1,'automatic_retry':False,'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True,'historical_actions_forced':False,'resources':resources,'planned_invocation_path':str(P/row['planned_invocation_path']),'plans':plans,'prefix':{'path':str(P/pkg/'pairs'/key/'specification.json'),'sha256':spec['sha256']},'output':str(P/x/'attempt01'),'final_evaluation_enabled':False,'maximum_total_control_steps':60000,'maximum_total_policy_queries':7600,'maximum_total_wait_steps':2000,'policy_watchdog_seconds':60.0,'raw_observation_root':str(rawpath),'observer_root':str(rawpath/'observer'),'root_storage_decision':storage,'root_fixed_design':decision,'schema_note':'One new attempt for this exact own pair; original scientific A/B loop and runtime seed17/env0 preserved. Prepared original invocation and real readiness are separately pinned by root authorization. Old200 remains HOLD; no final release.'}
 pin=put(sub/'config.json',c)
 registry['pairs'][key]={'config_sha256':pin,'specification_sha256':spec['sha256']}
rp=put(Q/'registry.json',registry)
s=(Q/'scope.py.in').read_text().replace('__REGISTRY_SHA_PENDING__',rp).replace("X=x,BASE=P/x","X=x,OUT=x+'/attempt01',BASE=P/x")
with (Q/'scope.py').open('x') as f:f.write(s)
old=(R/'scripts/ops/formal_goal_full200_gate_v1/run.slurm').read_text()
new=old.replace('cti-goal-full200','cti-goal-remaining5').replace('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/slurm/','/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/slurm/')
new=new.replace('CTI_GOAL_FULL200_AUTH_SHA256','CTI_GOAL_REMAINING5_AUTH_SHA256').replace('formal_goal_full200_gate_v1','formal_goal_remaining5_gate_v1')
dollar=chr(36)
new=new.replace(': "'+dollar+'{CTI_GOAL_REMAINING5_AUTH_SHA256',': "'+dollar+'{CTI_GOAL_REMAINING5_PAIR_KEY:?Exact remaining-five pair required}"\n: "'+dollar+'{CTI_GOAL_REMAINING5_AUTH_SHA256')
new=new.replace('--authorization "'+dollar+'P/results/formal_main_v2/engineering/goal_full200_20261021T0110/root_authorization.json"','--pair-key "'+dollar+'CTI_GOAL_REMAINING5_PAIR_KEY" --authorization "'+dollar+'P/results/formal_main_v2/execution/goal_remaining5_v1/'+dollar+'CTI_GOAL_REMAINING5_PAIR_KEY/root_authorization.json"')
with (Q/'run.slurm').open('x') as f:f.write(new.rstrip()+'\n')
(Q/'entry.pre_cpu_v1.py').write_bytes((Q/'entry.py').read_bytes())
(Q/'paired_input_gate.pre_cpu_v1.py').write_bytes((Q/'paired_input_gate_v1.py').read_bytes())
gate=(Q/'paired_input_gate_v1.py').read_text()
gate=gate.replace("+'\\\\n').encode('utf8')","+'\\n').encode('utf8')")
(Q/'paired_input_gate_v1.py').write_text(gate)
for p in Q.glob('*.py'):ast.parse(p.read_text())
put(D/'binding_result.json',{'plan_index':{'path':str(PD/'candidate_index.json'),'sha256':sha(PD/'candidate_index.json')},'registry_sha256':rp,'root_decisions':[decision,storage],'pairs':registry['pairs'],'production_installed':False,'actual_GPU':False})
print(json.dumps({'registry_sha256':rp,'status':'five_pairs_exact_plans_bound'}))
