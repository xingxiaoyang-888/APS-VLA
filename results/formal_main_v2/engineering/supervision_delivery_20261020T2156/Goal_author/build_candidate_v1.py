"""Build a private production-integration candidate. Never publishes or authorizes."""
from pathlib import Path
import ast,hashlib,json
D=Path(__file__).parent;R=D.parents[1];OLD=R/'scripts/ops/formal_goal_prefix58_observer_v2';PREV=R/'.local/goal_cpu_gate_20261020T2054';OUT=D/'package';OUT.mkdir(exist_ok=False)
PKG='scripts/ops/formal_goal_paired_input_gate_v1';STAGE='goal_paired_input_gate_20261020T2156';VERSION='goal-paired-input-gate-single-attempt-v1';P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
def sha(b):return hashlib.sha256(b).hexdigest()
def pinned(p,pin):
 b=p.read_bytes();assert sha(b)==pin,(str(p),sha(b));return b
proof=[]
def replace(t,a,b,n=1):
 assert t.count(a)==n,(a,t.count(a),n)
 proof.append({'old':a,'new':b,'occurrences':n});return t.replace(a,b)
raw=pinned(OLD/'entry.py','da3e094a98104d08735d6da6a180b326f79ae077e710880aa9117b39b911e31f');text=raw.decode()
text=replace(text,'formal_goal_prefix58_observer_v2','formal_goal_paired_input_gate_v1')
text=replace(text,'goal_prefix58_20261020T1825',STAGE)
text=replace(text,"VERSION='goal-prefix58-single-attempt-v2'","VERSION='"+VERSION+"'")
text=replace(text,"'observer_v3.py','ast_observer_v2.py','config.json'","'observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','config.json'")
text=replace(text,"'cti-goal-prefix58-v2:'","'cti-goal-paired-input-v1:'")
text=replace(text,"'observer_gaps_fixed':True","'observer_gaps_fixed':True,'paired_input_gate_CPU_passed':True,'pre_policy_pair_equality_gate':True,'all_query_input_integrity_gate':True,'original_policy_error_retained_then_halt':True")
text=replace(text,"ob=load(P/PKG/'observer_v3.py','g58_passive_observer',package['files'][PKG+'/observer_v3.py']);ad=load(P/PKG/'ast_observer_v2.py','g58_ast_observer',package['files'][PKG+'/ast_observer_v2.py']);observer=ob.PassiveObserver(OUTPUT/'observer',prefix)","ob=load(P/PKG/'paired_input_gate_v1.py','g58_paired_input_gate',package['files'][PKG+'/paired_input_gate_v1.py']);ad=load(P/PKG/'ast_gate_v2.py','g58_paired_input_ast',package['files'][PKG+'/ast_gate_v2.py']);observer=ob.PairedInputGate(OUTPUT/'observer',allow_cpu_fixture=False);require(observer.allow_cpu_fixture is False and observer.sink is None,'production observer cannot use CPU fixtures or injected sinks')")
text=replace(text,"finish['original_prefix_trials']==58 and finish['scientific_trials_added']==0","finish['original_prefix_trials']==58 and finish['scientific_trials_added']==0 and finish['exact_paired_t0_checks']==29 and finish['runtime_context']=='real_environment_engineering'")
text=replace(text,"observer_failed=getattr(observer,'dead',None),","observer_failed=getattr(observer,'dead',None),runtime_context='real_environment_engineering',last_paired_input_abort=getattr(observer,'last_gate_abort',None),accepted_queries_retained=sum(getattr(observer,'query_counts',{}).values()),executed_policy_steps_retained=getattr(observer,'executed_policy_steps',0),paired_t0_checks_retained=len(getattr(observer,'paired_keys',set())),")
text=replace(text,'One explicitly authorized Goal prefix58 engineering attempt; no submission API.','One explicitly authorized Goal paired-input58 engineering attempt; no submission API.')
(OUT/'entry.py').write_text(text)
protected=['prepare_original','validate_config','validate_authorization','validate_review_ref','validate_dispatch','validate_prefix']
a={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)};b={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
assert all(a[n]==b[n] for n in protected if n!='validate_dispatch')
# Only request-token prefix differs within the dispatch validator.
assert a['validate_dispatch'].replace('cti-goal-prefix58-v2:','cti-goal-paired-input-v1:')==b['validate_dispatch']
entry_proof=proof;proof=[]
for name,pin in [('observer_v3.py','7a33c4ec531e0524a5e30b51e18205dc7d354868afa6190e3f39dcf14b283241'),('ast_observer_v2.py','e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e'),('prefix58.json','1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28')]:
 (OUT/name).write_bytes(pinned(OLD/name,pin))
gate=pinned(PREV/'paired_input_gate_v1.py','11f5f892a1d5939f83717fe20adae62e61015fa1453da020f001f768ea657fbd').decode()
gate=replace(gate,"R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')","R=Path(__file__).resolve().parent")
gate=replace(gate,"OBSERVER='scripts/ops/formal_goal_prefix58_observer_v2/observer_v3.py'","OBSERVER='observer_v3.py'")
gate=replace(gate,"PREFIX='scripts/ops/formal_goal_prefix58_observer_v2/prefix58.json'","PREFIX='prefix58.json'")
gate=replace(gate,"VERSION='goal-before-policy-paired-input-gate-cpu-candidate-v1'","VERSION='goal-before-policy-paired-input-gate-engineering-v1'")
gate=replace(gate,"  self.query_pending=None;self.query_counts={};self.state_baselines={};self.paired_keys=set()","  self.runtime_context='synthetic_CPU_fixture' if allow_cpu_fixture else 'real_environment_engineering'\n  self.query_pending=None;self.query_counts={};self.state_baselines={};self.paired_keys=set()")
gate=replace(gate,"'candidate_gate_open'","'paired_input_gate_open'")
gate=replace(gate,"'GPU_authorized':False","'runtime_context':self.runtime_context,'CPU_fixture_enabled':self.allow_cpu_fixture,'GPU_authorization_owned_by_outer':True")
gate=replace(gate,"'status':'CPU_candidate_prefix_checked_not_GPU_admitted'","'status':'prefix_inputs_checked_engineering_only','runtime_context':self.runtime_context")
gate=replace(gate,"'candidate_gate_finished'","'paired_input_gate_finished'")
gate=replace(gate,'Candidate only: exact before-query pairing and input-integrity engineering gate.','Exact before-query pairing and input-integrity engineering gate.')
(OUT/'paired_input_gate_v1.py').write_text(gate);gate_proof=proof;proof=[]
ad=pinned(PREV/'ast_gate_v2.py','8665595129d018ac99746e9138408b11ef64b2b1cef08b919f8b3d71ffb2f833').decode()
ad=replace(ad,"R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')","R=Path(__file__).resolve().parent")
ad=replace(ad,"BASE='scripts/ops/formal_goal_prefix58_observer_v2/ast_observer_v2.py'","BASE='ast_observer_v2.py'")
(OUT/'ast_gate_v2.py').write_text(ad);ast_proof=proof
config=json.loads(pinned(OLD/'config.json','224ca0a8bce551c9d7becf3e13b8e879b5716ffbbf172eb73801dacef8a05265'))
config.update(stage_key=STAGE,version=VERSION,output=str(P/'results/formal_main_v2/engineering'/STAGE/'attempt01'))
config['prefix']['path']=str(P/PKG/'prefix58.json')
config['schema_note']='Private candidate pending root and independent readiness plus exact held dispatch. Fresh same-identity58 diagnostic, not exact old-history replay. Original actions/order/settings unchanged. Old200 and new Goal science remain HOLD; all observer cost is engineering only.'
(OUT/'config.json').write_text(json.dumps(config,sort_keys=True,indent=2)+'\n')
sl=pinned(OLD/'run.slurm','f479db9047bf9d9a9d07d9e9e650483b0a903bd8db8f97a0488b943ec9f56f3c').decode().replace('cti-goal-prefix58','cti-goal-paired-input').replace('formal_goal_prefix58_observer_v2','formal_goal_paired_input_gate_v1').replace('goal_prefix58_20261020T1825',STAGE).replace('CTI_PREFIX58_AUTH_SHA256','CTI_PAIRED_INPUT_AUTH_SHA256')
(OUT/'run.slurm').write_text(sl)
files={PKG+'/'+p.name:sha(p.read_bytes()) for p in sorted(OUT.iterdir())};assert len(files)==8
(OUT/'package_manifest.json').write_text(json.dumps({'schema':'formal_main_v2','version':VERSION,'files':files},sort_keys=True,indent=2)+'\n')
(D/'source_derivation.json').write_text(json.dumps({'status':'private_candidate_not_published','old_entry_sha256':sha(raw),'entry_replacements':entry_proof,'gate_replacements':gate_proof,'AST_engine_replacements':ast_proof,'unchanged_protected_entry_functions':protected,'gate_algorithm_AST_and_paired_input_decisions_unchanged':True,'copied_exact_files':['observer_v3.py','ast_observer_v2.py','prefix58.json'],'GPU_jobs':0,'production_writes':0},sort_keys=True,indent=2)+'\n')
print(json.dumps({'package_manifest_sha256':sha((OUT/'package_manifest.json').read_bytes()),'entry_sha256':files[PKG+'/entry.py'],'config_sha256':files[PKG+'/config.json'],'files':files},sort_keys=True))
