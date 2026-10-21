from pathlib import Path
import hashlib,json,copy,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_independent_20261021T0449/metadata_post_review';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249'
checks=[]
def require(v,m):
 checks.append({'check':m,'passed':bool(v)})
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(Path(p).relative_to(R)),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def read(p,pin):require(sha(p)==pin,'SHA '+str(p));return json.loads(Path(p).read_bytes())
receipt=read(B/'method_ids_metadata_receipt.json','7120074bd1ee53f2ce363c496a51de51fbeac91558c902e2d6f9da7323ad6819')
before=read(B/'method_ids_supervisor_snapshot_before.json','54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d')
after=read(R/'results/experiment_supervisor/state.json','d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba')
helper=R/'.local/complete_goal_method_metadata_20261021T0449.py';require(sha(helper)=='147641bbb46ae868c79e173159a4caf8c6913b09c6c8b5376731f40ed030d815','exact root helper source')
methods=['A256_seed17','B256_seed17'];docs={p:read(R/p,h) for p,h in receipt['source_refs'].items()};require(len(docs)==5,'five exact original source references')
config=docs['scripts/ops/formal_goal_full200_gate_v1/config.json'];spec=docs['scripts/ops/formal_goal_full200_gate_v1/specification.json'];ad=docs['results/formal_main_v2/engineering/goal_full200_20261021T0110/dispatch_admission.json'];root=docs['results/formal_main_v2/preflight/heartbeat_20261021T1134/Goal3054717_root_acceptance.json'];ind=docs['results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_independent/independent_terminal_review.json']
require(config['method_ids']==ad['method_ids']==methods,'original runtime configuration and original admission exact methods')
require([v['method_id'] for v in spec['method_identities']]==methods and len(spec['rows'])==200,'original fixed specification same methods/200')
require(set(x['method'] for x in spec['rows'])==set(methods),'all original specification rows agree')
require(root['status']=='accepted_new200_only' and root['current_trials']==200 and set(root['methods'])==set(methods),'original root raw terminal acceptance methods')
require(ind['status']=='passed_new200_terminal_independent_review' and ind['blockers']==[],'original independent terminal proof retained')
for label,s in [('before',before),('after',after)]:
 require(len(s['registered_jobs'])==303,label+' all303 rows')
 require(len({str(j['job_id']) for j in s['registered_jobs']})==303,label+' IDs unique')
 require(sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs'])==273,label+' formal273 allocations')
old=[j for j in before['registered_jobs'] if str(j['job_id'])=='3054717'];new=[j for j in after['registered_jobs'] if str(j['job_id'])=='3054717'];require(len(old)==len(new)==1,'one target job')
old,new=old[0],new[0];require('method_ids' not in old and new['method_ids']==methods,'only missing exact field added')
projection=copy.deepcopy(after);next(j for j in projection['registered_jobs'] if str(j['job_id'])=='3054717').pop('method_ids');require(projection==before,'entire state semantic equality after removing exactly new field')
require({k:v for k,v in new.items() if k!='method_ids'}==old,'every original job field preserved')
require(old['status']==new['status']=='COMPLETED' and old['exit_code']==new['exit_code']=='0:0' and old['elapsed_seconds']==new['elapsed_seconds']==2205 and old['gpus']==new['gpus']==1,'original completion and exact2205 GPU seconds unchanged')
require(new['original_sbatch_ACK']==old['original_sbatch_ACK']=='3054717\n' and old['invocation_sha256']==new['invocation_sha256']==ad['authorization']['sha256'],'original ACK/authorization unchanged')
require(old['pair_id']==ad['pair_id']==spec['method_identities'][0]['pair_id']==spec['method_identities'][1]['pair_id'],'original pair identity consistent')
require(receipt['only_added_field']=={'method_ids':methods} and receipt['state_before_sha256']==sha(B/'method_ids_supervisor_snapshot_before.json') and receipt['state_after_sha256']==sha(R/'results/experiment_supervisor/state.json'),'root receipt agrees with independently rebuilt actual difference')
s=helper.read_text();tree=ast.parse(s);require('with c.exclusive_lock(R/\'results/experiment_supervisor/.writer.lock\'):' in s and 'c.atomic_json(p,new,BEFORE)' in s,'root source exact existing writer-lock/CAS path')
require(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('submit','observe','release') for n in ast.walk(tree)),'helper contains no scheduler invocation')
report={'schema':'formal_main_v2','kind':'Goal3054717_method_ids_actual_postchange_independent_review','status':'passed_actual_single_field_metadata_review','reviewed_by':'independent','review_timing':'Root already applied the correction before this helper/source and actual state diff independent review; no prior independent execution approval claimed','state_before':ref(B/'method_ids_supervisor_snapshot_before.json'),'state_after':ref(R/'results/experiment_supervisor/state.json'),'root_receipt':ref(B/'method_ids_metadata_receipt.json'),'helper':ref(helper),'source_refs':receipt['source_refs'],'only_semantic_difference':{'registered_jobs.job_id=3054717.method_ids':methods},'registered_rows':303,'formal_allocations':273,'original_ACK_and_cost_preserved':True,'all_other_fields_preserved':True,'scientific_results_changed':False,'GPU_execution_authorized':False,'production_plan_runtime_admitted':False,'new_Slurm_calls':0,'blockers':[],'check_count':len(checks),'checks':checks}
with (D/'independent_review.json').open('x') as f:json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
manifest={'schema':'formal_main_v2','kind':'independent_audit_delivery_manifest','source_root':str(D.relative_to(R)),'file_count':2,'files':[ref(D/x) for x in ('audit.py','independent_review.json')]}
with (D/'delivery_manifest.json').open('x') as f:json.dump(manifest,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'review':ref(D/'independent_review.json'),'manifest':ref(D/'delivery_manifest.json'),'checks':len(checks)},sort_keys=True))
