from __future__ import annotations
import ast,hashlib,json,os,stat,sys
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/Long_legacy6_admission_independent_1032'
E='results/formal_main_v2/engineering/supervision_delivery_1032/Long_legacy6_admission_independent'
PIN={
'independent_review.json':'d3f9a69f8b35cc8134bc04b8c5bdafcaefb8d057fd0e918f20d2a70a9df13c4f',
'historical_identity_evidence.json':'4269f31d00e1af1a5e1c96e0ee20e965522a4b8f9da6f880c97b0abffa5aa799',
'audit_a1.py':'97edae567c859db936c1b93978f56f27d3959b9cc6c35acf5b08127a292badf9',
'manifest.json':'4340ff073b601e9c2063a576364b6a230674be01a1d905ac8f4621c4703b5312'}
ROOT_SUPPORT={'path':'results/formal_main_v2/preflight/heartbeat_20261020T1832/root_runtime_inode_evidence.json','sha256':'3f196ea78201de88c90d252c2d46deb18b0270560494361e457563e84d9bff21'}
PRIOR={'path':'results/formal_main_v2/engineering/supervision_delivery_0830/Long_legacy6_provenance_independent/independent_readiness.json','sha256':'b786128f4f202c93da6a80f44c7c1fbeeacadef78724b76d9bef294615b7a3d5'}
API={'path':'.local/Long_legacy6_consumer_candidate_1032/legacy_proof_api_v3.py','sha256':'7bf7fe93e9eb219273799aed7c2dfe35e23dad91e063db145ac80f1f7b60342d'}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,pin):
 b=p.read_bytes();assert sha(b)==pin,(str(p),sha(b));return b
def ref(name):return {'path':E+'/'+name,'sha256':sha((D/name).read_bytes())}
def put(name,v):
 p=D/name;assert not p.exists(),name
 b=(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return ref(name)
for name,pin in PIN.items():read(D/name,pin)
report=json.loads((D/'independent_review.json').read_bytes())
assert report['decision']=='accept_exact_600_typed_equivalence'
assert report['status']=='passed_independent_admission_recommendation'
assert report['original_controller_environment_identity_condition_satisfied'] is True
assert report['coverage']=={'executed_actions':183676,'full_chunks':23179,'methods':6,'new_scientific_trials':0,'outcome_filtering':False,'tasks':10,'trials':600,'unique_initial_states':100}
assert report['old_execution_version_preserved']=='formal-downstream-root-v1'
assert report['root_adoption_granted_by_this_agent'] is False and report['final_release'] is False
support=json.loads(read(R/ROOT_SUPPORT['path'],ROOT_SUPPORT['sha256']))
assert support['late_ctime_files']==[] and support['no_historical_instance_capture_claim'] is True
assert support['final_initial_state_values_read'] is False and support['no_environment_constructed'] is True
assert len(support['files'])==1350
assert [x['compared_files'] for x in support['packages']]==[1019,39]
assert all(not x['extras_not_in_wheel'] for x in support['packages'])
rows={x['path']:x for x in support['files']};assert len(rows)==1350
wanted=[
'/venv/lib/python3.11/site-packages/robosuite/macros.py',
'/venv/lib/python3.11/site-packages/robosuite/controllers/__init__.py',
'/venv/lib/python3.11/site-packages/robosuite/controllers/controller_factory.py',
'/venv/lib/python3.11/site-packages/robosuite/controllers/base_controller.py',
'/venv/lib/python3.11/site-packages/robosuite/controllers/osc.py',
'/venv/lib/python3.11/site-packages/robosuite/controllers/config/osc_pose.json',
'/venv/lib/python3.11/site-packages/robosuite/robots/single_arm.py',
'/venv/lib/python3.11/site-packages/mujoco/__init__.py',
'/external/LIBERO/libero/libero/envs/env_wrapper.py']
checked=[]
for suffix in wanted:
 matches=[r for path,r in rows.items() if path.endswith(suffix)]
 assert len(matches)==1,suffix
 row=matches[0];p=Path(row['path']);s=p.lstat()
 assert stat.S_ISREG(s.st_mode) and not p.is_symlink()
 assert s.st_ctime_ns==row['ctime_ns'] and s.st_mtime_ns==row['mtime_ns']
 assert s.st_ino==row['inode'] and s.st_dev==row['device']
 assert s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
 assert row['ctime_before_old_six_jobs'] is True and row['current_bytes_equal_distribution'] is True
 checked.append({k:row[k] for k in ('path','sha256','ctime_ns','mtime_ns','inode','device')})
read(R/PRIOR['path'],PRIOR['sha256'])
api_raw=read(R/API['path'],API['sha256']);tree=ast.parse(api_raw)
literal={}
for n in tree.body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name) and t.id in ('ASSESS_FIELDS','ADOPT_FIELDS','MAP','ROOT','SEM'):
    literal[t.id]=ast.literal_eval(n.value)
assert set(literal)=={'ASSESS_FIELDS','ADOPT_FIELDS','MAP','ROOT','SEM'}
assert literal['MAP']=={'path':'.local/legacy6_typed_bridge_0927/equivalence_map_candidate.json','sha256':'f3c7c2e3b3d4546748c4705bb8cba7f29c050470a22645215f7a894f899d3cc0'}
assert literal['ROOT']=={'path':'results/formal_main_v2/downstream_reviews/3019954.json','sha256':'cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba'}
assert literal['SEM']==report['target_action_semantics_sha256']
read(R/literal['MAP']['path'],literal['MAP']['sha256'])
source_ref=ref('audit_a1.py')
common={'schema':'formal_main_v2','status':'passed','review_role':'independent','synthetic':False,'map_ref':literal['MAP'],'legacy_root_ref':literal['ROOT'],'target_action_semantics_sha256':literal['SEM'],'same_controller_environment':True,'old_instance_hash_claimed':False,'old_full_RNG_dump_required':False,'reviewer_source_ref':source_ref,'final_release':False}
assessment={**common,'kind':'formal_legacy_controller_environment_identity_assessment','version':'long-legacy6-identity-v1','original_condition':'controller and environment were identical','decision':'sufficient_historical_source_chain','historical_provenance_ref':PRIOR,'supporting_evidence_refs':[ROOT_SUPPORT,ref('independent_review.json'),ref('historical_identity_evidence.json'),ref('original_consumer_and_AST_proof.json')]}
assert set(assessment)==literal['ASSESS_FIELDS']
assessment_ref=put('identity_assessment.json',assessment)
adoption={**common,'kind':'formal_legacy_development_equivalence_adoption','version':'long-legacy6-adoption-v1','identity_assessment_ref':assessment_ref,'independent_adoption_ref':None}
assert set(adoption)==literal['ADOPT_FIELDS']
adoption_ref=put('independent_adoption.json',adoption)
put('typed_document_generation.json',{'schema':'formal_main_v2','kind':'independent_legacy600_typed_document_generation','status':'passed','independent_scientific_report_ref':ref('independent_review.json'),'identity_assessment_ref':assessment_ref,'independent_adoption_ref':adoption_ref,'schema_source':API,'root_metadata_support_ref':ROOT_SUPPORT,'independent_rechecked_root_critical_files':checked,'source_continuity_inference':'Ordinary Linux inode ctime predating all six old runs, exact wheel bytes, actual old import paths, no private macros, exact factory and registered arguments support historical controller/environment equality. Current metadata is not a historical instance capture.','old_0830_report_preserved':True,'production_API_executed':False,'root_adoption_written':False,'new_scientific_trials':0,'new_GPU_seconds':0,'state_Git_or_production_changed':False,'final_release':False})
# Preserve the original completed audit manifest before extending private package.
initial=(D/'manifest.json').read_bytes()
with (D/'manifest_initial_a1.json').open('xb') as f:f.write(initial)
files=[]
for p in sorted(D.iterdir()):
 if p.is_file() and p.name!='manifest.json':
  b=p.read_bytes();files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)})
manifest={'schema':'formal_main_v2','kind':'independent_review_package_manifest','scope':'Long legacy600 independent admission and explicit typed wrappers only','private_root':D.relative_to(R).as_posix(),'archive_destination':E,'files':files,'independent_report_ref':ref('independent_review.json'),'identity_assessment_ref':assessment_ref,'independent_adoption_ref':adoption_ref,'new_GPU_seconds':0,'state_Git_or_production_changed':False}
b=(json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
(D/'manifest.json').write_bytes(b)
print(json.dumps({'status':'passed','report':ref('independent_review.json'),'identity_assessment':assessment_ref,'independent_adoption':adoption_ref,'manifest':{'path':(D/'manifest.json').relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)},'critical_source_files_rechecked':len(checked)}))
