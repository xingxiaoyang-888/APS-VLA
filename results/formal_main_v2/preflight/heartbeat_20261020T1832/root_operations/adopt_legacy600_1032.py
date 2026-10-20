from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832';E='results/formal_main_v2/engineering/supervision_delivery_1032'
CODE_REVIEW={"path":".local/Long_legacy6_consumer_code_audit_1032/code_audit_review.json","sha256":"d4112140f1c661144ab2aae6acbf674643eabab208ef93d9bc7aaf20deccfb04"}
CODE_MANIFEST={"path":".local/Long_legacy6_consumer_code_audit_1032/manifest.json","sha256":"7d1ce064666dcf217994b51497b20637b6f71b84f034f6563117c66ca7ce6116"}
API='.local/Long_legacy6_consumer_candidate_1032/legacy_proof_api_v3.py'
API_SHA='7bf7fe93e9eb219273799aed7c2dfe35e23dad91e063db145ac80f1f7b60342d'
IND=E+'/Long_legacy6_admission_independent'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel,pin=None):
 if pin:assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def clone(rel,b):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
 return ref(rel)
def save(rel,x):return clone(rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=module('adopt1032ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
start=time.monotonic();cpu=time.process_time()
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 cr=rd(CODE_REVIEW['path'],CODE_REVIEW['sha256'])
 assert cr['status']=='passed' and not cr['blockers'] and cr['suitable_for_minimal_nonfrozen_CPU_proof_application_after_real_receipts']
 assert cr['script']==dict(path=API,sha256=API_SHA) and cr['reviewer']=='/root/long128s41_terminal_0530'
 science=rd(IND+'/independent_review.json','d3f9a69f8b35cc8134bc04b8c5bdafcaefb8d057fd0e918f20d2a70a9df13c4f')
 assert science['status']=='passed_independent_admission_recommendation' and science['decision']=='accept_exact_600_typed_equivalence'
 assert science['original_controller_environment_identity_condition_satisfied'] and science['coverage']['trials']==600
 assert science['coverage']['full_chunks']==23179 and science['coverage']['executed_actions']==183676
 assert science['cost']['new_GPU_seconds']==0 and not science['final_release']
 assess=rd(IND+'/identity_assessment.json','aa6a6edb17b32147e66dfec8fe5cc9373ad7e8d206beaf74bd1ac3b740903e6d')
 indep=rd(IND+'/independent_adoption.json','9f59ff1ddeff85937fb9786196c2ce51aed21507cb3d4ec0842d985abbd678c7')
 inode=rd(B+'/root_runtime_inode_evidence.json','3f196ea78201de88c90d252c2d46deb18b0270560494361e457563e84d9bff21')
 assert inode['status']=='source_chain_supports_no_intervening_file_rewrite' and not inode['late_ctime_files']
 # Exact code review archive is non-scientific; no original receipt is rewritten.
 base=Path(CODE_MANIFEST['path']).parent;manifest=rd(CODE_MANIFEST['path'],CODE_MANIFEST['sha256']);copies=[]
 rows=list(manifest['files'])+[dict(path=CODE_MANIFEST['path'],sha256=CODE_MANIFEST['sha256'],bytes=(R/CODE_MANIFEST['path']).stat().st_size)]
 for row in rows:
  src=Path(row['path'])
  if not src.is_relative_to(base):src=base/src
  assert src.is_relative_to(base) and not src.is_absolute() and '..' not in src.parts
  p=R/src;assert not p.is_symlink() and h(p)==row['sha256'] and p.stat().st_size==row['bytes']
  assert p.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npz','.npy'] and p.stat().st_size<100*(1<<20)
  dst=E+'/Long_legacy6_consumer_code_independent/'+src.relative_to(base).as_posix()
  copies.append(dict(source=dict(path=src.as_posix(),sha256=row['sha256'],bytes=row['bytes']),archive=clone(dst,p.read_bytes())))
 save(B+'/Long_legacy6_consumer_code_independent_delivery.json',dict(source_manifest=CODE_MANIFEST,copies=copies,no_source_transformation=True,new_GPU_jobs=0))
 source_ref=clone(B+'/root_operations/adopt_legacy600_1032.py',Path(__file__).read_bytes())
 basis=save(B+'/Long_legacy600_root_admission_basis.json',dict(schema='formal_main_v2',kind='root_legacy600_admission_judgment',
  status='accepted_for_explicit_development_proof',reviewer='root',independent_scientific_review=ref(IND+'/independent_review.json'),identity_assessment=ref(IND+'/identity_assessment.json'),
  independent_code_review=CODE_REVIEW,API_source=dict(path=API,sha256=API_SHA),root_source=source_ref,runtime_source_evidence=ref(B+'/root_runtime_inode_evidence.json'),
  registered_rule_ref=ref('configs/experiments/formal_main_v2_action_execution_compat_v1.json'),
  judgment='Accept the exact six-method600 Long development trials under the original identity/action rule. Frozen factory/config, original import-path logs, complete wheel/source equality and inode ctimes predating every old job establish source continuity under ordinary filesystem semantics. Independent full action checks and unchanged-branch replay establish removal of an inactive guard only.',
  inference_not_historical_instance_capture=True,old_full_RNG_dump_not_required=True,old_execution_version_preserved=True,
  complete_600_no_outcome_filtering=True,old_GPU_seconds=10531,old_cost_already_counted=True,new_GPU_seconds=0,new_scientific_trials=0,
  root_adoption_scope='Only explicit development compatibility. No automatic general-consumer/global-release/O2A authorization.',final_release=False))
 adoption=dict(indep);adoption.update(review_role='root',independent_adoption_ref=ref(IND+'/independent_adoption.json'),reviewer_source_ref=source_ref)
 root_ref=save(B+'/Long_legacy600_root_adoption.json',adoption)
 assert before==h(R/'results/experiment_supervisor/state.json')
# CPU reconstruction outside writer transaction; no state/registry changes.
api=module('explicit_legacy6001032',API,API_SHA)
proof=api.consume_legacy_development_proof(legacy_root_ref=api.ROOT,equivalence_map_ref=api.MAP,root_adoption_ref=root_ref,
 independent_adoption_ref=ref(IND+'/independent_adoption.json'),identity_assessment_ref=ref(IND+'/identity_assessment.json'),
 suite='libero_10',stage='development',target_action_semantics_sha256=api.SEM)
assert proof['legacy_equivalent_trials']==600 and proof['actual_new_wrapper_trials_added']==0 and proof['new_GPU_seconds']==0
assert not proof['original_invocations_ran_new_wrapper'] and not proof['final_release'] and not proof['old_latency_reused']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 out=save(B+'/Long_legacy600_development_compatibility_proof.json',proof)
 result=save(B+'/Long_legacy600_root_proof_execution.json',dict(schema='formal_main_v2',status='real_adoption_and_explicit_proof_verified',
  source=source_ref,root_basis=basis,root_adoption=root_ref,proof=out,independent_code_review=CODE_REVIEW,
  code_audit_does_not_substitute_scientific_identity_review=True,CPU_wall_seconds=time.monotonic()-start,CPU_process_seconds=time.process_time()-cpu,
  state_or_registry_changed=False,new_GPU_seconds=0,new_scientific_trials=0,legacy_equivalent_trials=600,actual_new_wrapper_trials_added=0,
  production_general_consumer_modified=False,global_release_modified=False,final_release=False))
 print(json.dumps(dict(status='real_development_equivalence_proof_verified',proof=out,execution=result,new_GPU_jobs=0)),flush=True)
