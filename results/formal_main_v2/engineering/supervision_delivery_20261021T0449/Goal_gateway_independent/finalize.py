from pathlib import Path
import argparse,hashlib,json,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_gateway_independent_20261021T0449';A=R/'.local/goal_remaining5_dispatch_20261021T0449'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,pin=None):
 b=p.read_bytes()
 if pin:assert sha(b)==pin,(p,'SHA changed')
 return json.loads(b)
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n')
 return ref(p)
def ref(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
ap=argparse.ArgumentParser();ap.add_argument('--runtime-manifest',type=Path,required=True);ap.add_argument('--runtime-manifest-sha256',required=True);ap.add_argument('--dispatch-scope',type=Path,required=True);ap.add_argument('--dispatch-scope-sha256',required=True);args=ap.parse_args()
pkg=read(args.runtime_manifest,args.runtime_manifest_sha256);scope=read(args.dispatch_scope,args.dispatch_scope_sha256)
assert scope['runtime_manifest_sha256']==args.runtime_manifest_sha256 and scope['runtime_files']==pkg['files']
assert sha((A/'gateway_v3.py').read_bytes())=='45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b'
control=read(D/'control_CPU_v3_preliminary_review.json','05e63288c56a12af305d09a5dde7ba7f60a9d51bcfb97214e91c7f49f61a6639')
cross=read(D/'cross_interface_review.json');admission=read(D/'admission_CPU_review.json')
for result in (cross,admission):
 assert result['status']=='passed' and result['package_manifest_sha256']==args.runtime_manifest_sha256 and result['scope_sha256']==args.dispatch_scope_sha256
assert control['author_replay']['positive']==302 and control['author_replay']['rejections']==383 and not control['findings']
files={**{rel:sha((args.runtime_manifest.parent/Path(rel).relative_to('scripts/ops/formal_goal_remaining5_gate_v1')).read_bytes()) for rel in pkg['files']}}
assert files==pkg['files']
# Preserve exact completed transport journals and candidate source fixes. Journals
# for this finalizer are archived separately by root, after its transport returns.
journal_names=['goal_remaining5_gateway_independent_control_0449.jsonl','goal_remaining5_gateway_independent_control_v3_0449.jsonl','goal_remaining5_gateway_independent_cross_0449.jsonl','goal_remaining5_gateway_independent_admission_0449.jsonl']
for name in journal_names:
 p=R/'results/formal_main_v2/control_transport'/name;assert p.is_file()
 dst=D/'transport'/name;dst.parent.mkdir(exist_ok=True);dst.open('xb').write(p.read_bytes())
report={'schema':'formal_main_v2','kind':'Goal_remaining5_atomic_dispatch_independent_review','status':'passed','reviewed_by':'spatial588_recovery_author_2054_independent_of_root_gateway_author',
 'review_scope':'source_and_CPU_only','GPU_execution_authorized':False,'production_admitted':False,'actual_P_verified':False,
 'dispatch_files':cross['dispatch_files'],'package_manifest_sha256':args.runtime_manifest_sha256,'runtime_files':pkg['files'],
 'scope':scope['pairs'],'scope_sha256':args.dispatch_scope_sha256,'blockers':[],
 'checks':{'original_author_positive':302,'original_author_rejections':383,
 'independent_control_positive':control['independent_positive_count'],'independent_control_rejections':control['independent_negative_count'],
 'real_final_source_cross_interface_positive':cross['positive_count'],'real_final_source_cross_interface_rejections':cross['negative_count'],
 'real_admission_function_structural_CPU_positive':admission['positive_count'],'real_admission_function_structural_CPU_rejections':admission['negative_count']},
 'evidence':{name:ref(D/name) for name in ('control_CPU_preliminary_review.json','control_CPU_v3_preliminary_review.json','author_replay_v3.json','v2_actual_runtime_interface_rejection.json','cross_interface_review.json','cross_interface_CPU_fixtures.json','admission_CPU_review.json')},
 'v2_retained_but_not_approved_for_production':{'source_sha256':'7de77ebb179dfe465e490290ab33ff280109cd28225dcbfe6a9b859a0d5207b3','reason':'actual new runtime requires pair_key in reservation and dispatch; v3 adds exactly those two fields and preserves all transaction guards'},
 'guarantees_reviewed':['five explicit immutable contexts, no old module global changes','same shared writer lock, raw-byte CAS and nonblocking lifecycle lease verification','all registered scheduler IDs and all-mode GPU capacity; requested pending GPUs count even before allocation','same-pair and unknown Goal occupancy refuse; no reuse of old completed256s17 authorization','both root and autonomous pending refuse except exact original ACK reconciliation','pending and intent durable before one held sbatch; original ACK persists before held identity/registration','one registered job and complete held dispatch proof before one release','BaseException and unknown ACK/release preserve evidence and HOLD; never clear/reissue','terminal same-scope fragments forbid repeat regardless missing link details','runtime/source/plan/admission bindings and precise resource/no-requeue/token paths','actual new runtime dispatch validator and raw-consumer job precheck accept unchanged generated registration for all five scopes','final values not read and release remains false'],
 'limitations':['control fixtures use in-memory fake scheduler; no actual scheduler request made','admission root/independent/actual-P receipts are memory-only explicit CPU fixtures; none saved as production evidence','consumer.validate_job was exercised, but no future real raw terminal outcome exists or is manufactured','my own plan author package is not independently certified here; separate agent reviews plans and runtime','final runtime main/GPU execution and canonical P verification were not run by this audit'],
 'remaining_root_prerequisites':['separate plans and runtime independent source/CPU reviews','exact canonical R/P publication and rebuilt original plans using current registry','genuine root/independent plan receipts and exact prepared original invocation per pair','actual P verify captures, fresh aggregate five-pair R/P storage, root runtime/admission receipts','native read-only admission and full actual scheduler/lease check under lock before each held transaction','one root-authorized submission per pair and future real raw consumer plus independent terminal acceptance'],
 'new_scientific_trials':0,'new_GPU_submissions':0,'state_written':False,'canonical_or_P_written':False,'weights_copied':False,'final_values_read':False}
review=save(D/'independent_review.json',report)
readme='''# Goal remaining-five 原子网关独立审查\n\n本包独立审核 root 编写的网关；作者本人编写的五pair计划未在本审计中自审，它们由另一代理审查。最终审核范围为源码与 CPU。全部测试只在服务器私有目录写入，未查询或提交 Slurm，未写 canonical/P/state/Git，未运行或捏造新科学试验。\n\n固定 v3 网关绑定最终20文件runtime和exact scope。原302正/383拒逐条重建；独立新增重复碎片、同pair/跨模式、双pending、持久化/BaseException、原ACK、不重复release、完整sacct确认与成本检查。原v2缺少两处pair_key被实际runtime函数拒绝，证据保留；v3恰仅增加两字段，实际 Native.dispatch_proof 经最终 entry.validate_dispatch 和 consumer.validate_job 对全部五scope闭合。\n\nCPU admission 测试在内存中使用明确标注的根/独审/actual-P结构fixture，只验证真实函数的字段/来源/接口守卫。这些fixture不落到生产路径，不代表真实根采用、actual P、工程验收或GPU成功。已有原始控制器和注册作业状态仅通过保存的真实日志重建。\n\nroot仍须另行完成计划/runtime独审、精确发布、真实根收据和prepared invocation、actual P、全五pair保守存储容量及每次原子提交前真实容量/lease对账。正常作业仅一个attempt，不自动重试。未来完整原始日志consumer和独立终审不在本包中预记成功。\n'''
(D/'README.md').open('x').write(readme)
rows=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='delivery_manifest.json':rows.append(ref(p))
manifest=save(D/'delivery_manifest.json',{'schema':'formal_main_v2','kind':'Goal_remaining5_gateway_independent_delivery_manifest','root':str(D.relative_to(R)),'file_count':len(rows),'files':rows})
print(json.dumps({'review':review,'manifest':manifest,'checks':report['checks']},sort_keys=True))
