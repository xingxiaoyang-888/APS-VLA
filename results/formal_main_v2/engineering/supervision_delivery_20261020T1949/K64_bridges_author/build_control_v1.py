from pathlib import Path
import json,hashlib,ast,re,difflib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
T=R/'scripts/ops/formal_object256s23_source_bridge_v1/control.py'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(v if isinstance(v,str) else json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
assert h(T)=='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f'
rows=[]
for short in ['spatial','object']:
 K=D/short/'package';p=json.loads((K/'policy_v1.json').read_bytes());manifest=D/short/'development.json';assert manifest.exists()
 source=T.read_text();old=source
 mappings=[('Object256','Spatial64' if short=='spatial' else 'Object64'),('object256',short+'64'),('libero_object',p['suite']),('3028460',p['failure_job_id']),('3039258',p['recovery_job_id']),('3042627',p['final_job_id']),('58917',str(p['total_GPU_seconds'])),('8785b42fe62dd513f796871875547c894de972516ac9762ad60a89d3df9a7c8e',h(K/'bridge_v2.py')),('9f4e753fbe9602593c33b6f5031e88006a3d07dacc0ace21ed1a204d8caab999',h(K/'policy_v1.json')),('5f2bdcac8752c0cd06ad8dcb67114920b642db1415f6a88e1335d6c9f10fb028',h(manifest)),('.local/object_bridge_production_20261020T1644/revision03/package',K.relative_to(R).as_posix()),('.local/object_bridge_production_20261020T1644/',(D/short).relative_to(R).as_posix()+'/')]
 for a,b in mappings:source=source.replace(a,b)
 source=re.sub(r'\b256\b','64',source);source=re.sub(r'\b84\b',str(p['failed_GPU_seconds']),source)
 source=source.replace('A256_seed23','A64_seed23').replace('B256_seed23','B64_seed23')
 manifest_line=next(x for x in source.splitlines() if x.startswith('MANIFEST='))
 canonical=f'results/formal_main_v2/execution/{short}64seed23_source_control_v1_20261020T1949/development.json'
 replacement='CANONICAL_MANIFEST='+repr(canonical)+'\nCPU_MANIFEST='+repr(manifest.relative_to(R).as_posix())+'\nMANIFEST=CANONICAL_MANIFEST if BASE.relative_to(R).as_posix()==CANONICAL else CPU_MANIFEST'
 source=source.replace(manifest_line,replacement)
 source=source.replace("'successful_job_ids':['"+p['recovery_job_id']+"','"+p['final_job_id']+"']","'successful_job_ids':"+repr(p['successful_job_ids']))
 source=source.replace("def gateway_module():\n", "def gateway_module():\n # Original RUNNING-controller capacity gate intentionally unchanged; no post-training submission authority here.\n")
 ast.parse(source);write(K/'control.py',source)
 write(D/short/'control_derivation.diff',''.join(difflib.unified_diff(old.splitlines(True),source.splitlines(True),fromfile='published_Object256_control.py',tofile=short+'_k64_private_control.py')))
 readme=f"""# {short}64 seed23 独立历史来源桥候选

仅限 {p['suite']}、64 tokens、seed23、A64/B64，原100开发初态各一次，共200条。原训练和选模不变；失败 {p['failure_job_id']} 保留 {p['failed_GPU_seconds']} GPU秒，完整 {len(p['all_job_ids'])} 次分配共 {p['total_GPU_seconds']} GPU秒。选中A/B分别为 {p['selected_checkpoints']['A']['update']}/{p['selected_checkpoints']['B']['update']} 步；不能复制 Object256 的5000选模结论。

policy_v1.json逐项绑定本pair原根/独审、原始失败重建器、恢复/连续授权、原所有分配、原pull外部文件归属、选中checkpoint。Spatial保留失败前1000边界与五次历史，无asset metadata；Object启动失败保留独立startup_failure_history，不伪造正常metadata。

control.py保持旧Object256显式私有模块注入结构，但只允许本pair固定第一次完整development。closure/descriptor、control_modules、gateway_module、reviewer_module、consumer_module同旧API。私有CPU manifest路径是{manifest.relative_to(R).as_posix()}；root发布后使用{canonical}，manifest原字节相同，但proof/plan/readiness必须从canonical位置重建，不复用private proof。

原gateway容量函数仍要求训练控制器RUNNING。当前3034538正常COMPLETED，本包不授权重启控制器或使用collect专用白名单提交development。另一个有界开发gateway必须只白名单最终两份科学/effective计划，绑定该paircanonical descriptor/closure，检查72/72终验、原owner/退出/lease、全部正式登记容量<=8、pending准确对账、单pair唯一、未知/失败停止、共享锁/CAS及原FrozenPlan内重建。全部原runtime/action/packing/消费/计账门槛保留。

本目录仅CPU候选，尚未root发布或独审、真实P readiness未批准、无GPU/Slurm/科学trial。不得执行main提交。完整动作路径实际GPU仍由root后续单次提交及原终审决定；最终集保持封存，Goal科学HOLD不受影响。
"""
 write(K/'README.md',readme)
 rows.append({'suite':p['suite'],'private_package':K.relative_to(R).as_posix(),'canonical_package':'scripts/ops/formal_'+short+'64s23_source_bridge_v1','canonical_manifest':canonical,'CPU_manifest':manifest.relative_to(R).as_posix(),'manifest_sha256':h(manifest),'files':[{'source':(K/n).relative_to(R).as_posix(),'path':'scripts/ops/formal_'+short+'64s23_source_bridge_v1/'+n,'sha256':h(K/n),'bytes':(K/n).stat().st_size} for n in ['control.py','bridge_v2.py','policy_v1.json','README.md']]})
write(D/'source_publication_manifest_candidate.json',{'status':'private_source_candidate_not_published','pairs':rows,'requires_root_and_independent_review':True,'P_source_publication_required':False,'runtime_sources_unchanged':True,'GPU_runs':0});print(json.dumps(rows))
