from pathlib import Path
import hashlib,json,difflib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
def ref(rel):
 p=D/rel;return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
for name in ['object23_bridge_cpu_attempt01_20261020T1530','object23_bridge_cpu_attempt02_20261020T1530','object23_P_prepare_attempt01_20261020T1530']:
 src=R/('results/formal_main_v2/control_transport/'+name+'.jsonl');raw=src.read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
 assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==0,rows[-1]
 put('transport/'+name+'.jsonl',raw)
publication='results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_probe_and_Object_metadata_publication.json'
assert sha(R/publication)=='b9c376d0c5f660d2e328f305ee2c6995f0e5c2abcf5b813d3271efe7a11a4b2d'
put('root_metadata_publication.json',(R/publication).read_bytes())
put('bridge_v1_to_v2.diff',''.join(difflib.unified_diff((D/'bridge_v1.py').read_text().splitlines(True),(D/'bridge_v2.py').read_text().splitlines(True),fromfile='bridge_v1.py',tofile='bridge_v2.py')).encode())
proof=json.loads((D/'attempt02/development.json.evidence.json').read_text());needed=proof['files'];runtime=json.loads((D/'runtime_check01/read_evidence_sha256.json').read_text())
put('required_existing_evidence.json',{'schema':'formal_main_v2','kind':'exact_source_dependency_index','factory_files_relative_R':needed,'P_readonly_runtime_files_absolute':runtime,'historical_raw_evidence_not_fabricated':True,'checkpoint_bytes_not_in_package':True,'description':'Original bytes already on server; this index binds references, not a claim that all are duplicated in this candidate. Original startup verifier reconstructs canonical failure closure.'})
text='''# Object256 seed23 来源兼容桥候选

仅处理 `libero_object / 256 / seed23` 的 A/B 已选 checkpoint。候选没有提交GPU，没有改变训练或开发科学设置，也没有获得 root 科学准入。

- 保留 3028460 原 CUDA 启动失败、原错误日志及0步边界；成功 metadata 只属于3039258、3042627。三个分配完整计账58,917 GPU秒，其中失败84秒；不重新训练。
- `bridge_v2.py` 是当前候选；`bridge_v1.py` 及两轮CPU记录全部保留。版本化私有副本严格绑定原 consumer SHA，以四处精确替换实现三个操作差异：成功/失败来源分开；失败走原 raw verifier；原 pull 的三个失败外部文件保留失败作业所有权。全部成功训练、173源、F00/F01/F03、选模与部署收据检查仍走原函数。没有伪造普通metadata或改变原consumer。
- `policy_v1.json` 硬绑定唯一pair、三job、原失败、恢复root/独审、连续准入、终验root/独审、selected-server证明和两个checkpoint SHA。任一改变即拒绝。
- `attempt02/cpu_checks.json`：41/41 CPU通过；原factory仍按旧metadata错误拒绝；新factory完整科学门槛通过；终态消费者能重建完全相同的显式版本proof。负例覆盖遗漏失败、篡改费用/种子/checkpoint、伪装成功、漏独审等。
- `runtime_check01/P_check_only.json`：root精确发布两个静态JSON后，真实P原wrapper.verify与action runtime metadata检查通过。它们未加载模型/环境、未读取权重或封存值。新action wrapper因缺真实root readiness正确拒绝。四项P准备检查是CPU元数据证据，不能称GPU通过。

## 后续集成门槛

1. 独立审核此候选与原失败来源链，root决定版本化准入；当前不可提交。
2. 生产factory、planner、gateway独立重建和终态来源consumer必须明确使用同一桥。`control_modules()`仅创建私有工厂/planner实例；`auditor().review_invocation()`提供开发期终态接口。原生产gateway仍使用旧consumer，不能直接通过当前生产gateway提交。不得静默替换全局helper或按异常放行。
3. 科学manifest已按原字节在R/P发布；桥源码、调用、state、Slurm、root readiness均未发布。有效计划预览引用私有路径，仅用于审阅，不能直接用于部署。
4. root整合后必须重建精确计划、验证生产gateway和终态consumer的来源proof一致，并执行真实root/独立readiness、当时锁内CAS/重复提交/8槽检查。当前checkpoint原字节仍需部署前由原运行入口核验。
5. 只允许既定100个开发初态×A/B=200条，保持测试封存。不授权其他pair、预算、最终评测或自动重试。

`author_state_snapshot.json`明确为作者只读原子文件快照，不是root writer-lock/CAS授权；root最初观察与发布收据另有精确SHA。所有已有失败和版本均保留。最终seal自身的闭合transport位于候选外，将由root按返回SHA单独归档，避免递归自哈希。
'''
put('README.md',text.encode())
put('author_lookup_and_write_notes.json',{'retained_read_only_lookup_failure':{'path':'scripts/ops/server_control_transport_v1/README.md','error':'FileNotFoundError','resolution':'Read SERVER_WORKSPACE.md and storage registration for exact transport'},'retained_in_memory_generator_failure':{'error':'SyntaxError from nested triple quotes while composing seal script','server_files_written':False,'correction':'Use distinct outer and inner literal quote delimiters; no source or science changes'},'GPU_runs':0})
report={'schema':'formal_main_v2','kind':'bounded_object256s23_source_bridge_candidate_handoff','status':'CPU_verified_pending_independent_and_root_integration','version':'object256-seed23-startup-source-bridge-v2','bridge':ref('bridge_v2.py'),'policy':ref('policy_v1.json'),'CPU':ref('attempt02/cpu_checks.json'),'P_check_only':ref('runtime_check01/P_check_only.json'),'scientific_manifest':ref('attempt02/development.json'),'source_provenance':ref('attempt02/development.json.evidence.json'),'scientific_plan_private':ref('runtime_check01/scientific_plan.json'),'effective_plan_private_preview':ref('runtime_check01/effective_plan_private_preview.json'),'GPU_runs':0,'Slurm_submissions':0,'state_writes':False,'Git_writes':False,'canonical_writes_by_author':False,'root_metadata_publication':{'path':publication,'sha256':sha(R/publication)},'science_admission':False,'production_gateway_ready':False,'production_terminal_consumer_ready':False,'final_release':False,'new_planned_development_trials':200,'historical_allocation_GPU_seconds':58917,'failed_startup_GPU_seconds':84,'test_opened':False,'scope':['libero_object','256','seed23','A','B'],'source173_changed':False}
put('handoff.json',report)
entries=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert p.resolve()==p and p.suffix.lower() not in ('.pt','.bin','.safetensors','.pyc')
  entries.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
put('delivery_manifest.json',{'schema':'formal_main_v2','kind':'full_private_candidate_delivery','status':'sealed_not_admitted','root':str(D),'files':entries,'file_count':len(entries),'total_bytes':sum(x['bytes'] for x in entries),'include_previous_versions_and_expected_failures':True,'GPU_runs':0,'source_dependencies':'required_existing_evidence.json','outer_seal_transport_not_self_hashed':'results/formal_main_v2/control_transport/object23_seal_20261020T1530.jsonl'})
print(json.dumps({'manifest':ref('delivery_manifest.json'),'handoff':ref('handoff.json'),'file_count':len(entries),'bytes':sum(x['bytes'] for x in entries),'ready_to_submit':False}))
