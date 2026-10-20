from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T0556';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2156'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
refs={
 'Spatial_phase2_v2_author':(E+'/Spatial_author/phase2_v2_manifest_original.json','a2338514ff9e336d7e0470a8326e1009544db9e1c282a8aaf9c22177b4610bbd'),
 'Spatial_phase2_v2_independent':(E+'/Spatial_phase2_independent/independent_history_review.json','db89d100fdc77f3ea7185ca8ffb1d20cbce333a88b627f8d477618f1924f6cc9'),
 'Spatial_gateway_candidate':(E+'/Spatial_author/phase3_gateway_manifest_original.json','4c1ccca16c81a2dec94109cac3a5c4e6743841920d975d0737ea90bd8657cde9'),
 'Object_stage1_author':(E+'/Object_author/stage1_delivery_manifest_original.json','9020eb66c1746924379106baf19cd5d50318bf4283370b900785acba596c1992')}
for n,(p,pin) in refs.items():assert h(R/p)==pin,(n,p)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('handoff2156ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_sha=h(R/'results/experiment_supervisor/state.json');out={
 'schema':'formal_main_v2','status':'CPU_evidence_delivery_only','evidence':{k:{'path':v[0],'sha256':v[1]} for k,v in refs.items()},
 'Spatial_phase2_v2_independent_checks':431,'Spatial_gateway_author_CPU_checks':68,
 'Spatial_gateway_independently_reviewed':False,'Spatial_canonical_install_or_actual_P_verify':False,'Spatial_root_adoption_or_repair':False,
 'Object599_independently_adopted':False,'Object_failed_trial_repair_implemented':False,'new_scientific_trials':0,'new_GPU_jobs':0,
 'state_sha256_unchanged':state_sha,'final_sealed':True,
 'next_integration_steps':[
 'Review the exact new Spatial gateway independently; the 431-check history review does not authorize the new gateway.',
 'Install only the exact phase2_v2 candidate and generate canonical adoption_proposal and repair_proposal with the archived independent receipts. Do not install private CPU proposals or synthetic evidence as actual admission.',
 'Create only the registered Spatial scientific_plan/effective_plan under results/formal_main_v2/execution/spatial588_pre_dispatch_v1; obtain new actual-P closure verification/readiness before any single 588 continuation.',
 'Retain original 3022743 executed legacy12, 393 GPU seconds, and 3042529 predispatch-only failure, 2 GPU seconds; no child adapter or ledger invocation may be fabricated.',
 'Audit Object599 real record compatibility separately; original policy_error and rejected unknown chunk remain. An explicit linked single failed-trial repair is required, not an ordinary resume.',
 'Review Goal job3054127 from its unique original ACK and exact output; no automatic engineering retry or Goal scientific release.'
 ]}
 dst=R/B/'late_CPU_handoff.json';dst.open('x').write(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n');assert h(R/'results/experiment_supervisor/state.json')==state_sha
 print(json.dumps({'status':out['status'],'path':str(dst.relative_to(R)),'sha256':h(dst),'state_unchanged':True}))
