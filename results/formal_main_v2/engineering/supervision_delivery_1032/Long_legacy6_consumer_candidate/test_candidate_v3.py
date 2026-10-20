"""Author focused CPU checks; synthetic adoption never grants a real proof."""
import copy,hashlib,json,os,sys,time,traceback,types
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/Long_legacy6_consumer_candidate_1032'
START=time.perf_counter();CPU=time.process_time();checks=[]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('no process/network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'} or p.name=='init_states_test.json' or (p.name=='panel.json' and 'final' in p.parts):raise RuntimeError('forbidden values')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and p.parent!=D:raise RuntimeError('private output only')
def write(name,v):
 with (D/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
sys.dont_write_bytecode=True;sys.addaudithook(guard)
try:
 p=D/'legacy_proof_api_v3.py';source=p.read_bytes();assert hashlib.sha256(source).hexdigest()=='7bf7fe93e9eb219273799aed7c2dfe35e23dad91e063db145ac80f1f7b60342d'
 m=types.ModuleType('_legacy600_candidate_test');m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(source,str(p),'exec',dont_inherit=True),m.__dict__)
 def ref(tag):return {'path':'results/formal_main_v2/engineering/SYNTHETIC_IN_MEMORY_ONLY/'+tag,'sha256':hashlib.sha256(tag.encode()).hexdigest()}
 ar,rr,ir=ref('identity.json'),ref('root.json'),ref('independent.json')
 shared={'schema':'formal_main_v2','status':'passed','synthetic':True,'map_ref':m.MAP,'legacy_root_ref':m.ROOT,'target_action_semantics_sha256':m.SEM,'same_controller_environment':True,'old_instance_hash_claimed':False,'old_full_RNG_dump_required':False,'final_release':False}
 a={**shared,'kind':'formal_legacy_controller_environment_identity_assessment','version':'long-legacy6-identity-v1','review_role':'independent','original_condition':'controller and environment were identical','decision':'sufficient_historical_source_chain','historical_provenance_ref':m.PRIOR,'supporting_evidence_refs':[m.IDENTITY_SUPPORT],'reviewer_source_ref':ref('identity_source.py')}
 def adoption(role):return {**shared,'kind':'formal_legacy_development_equivalence_adoption','version':'long-legacy6-adoption-v1','review_role':role,'identity_assessment_ref':ar,'independent_adoption_ref':ir if role=='root' else None,'reviewer_source_ref':ref(role+'_review.py')}
 root,ind=adoption('root'),adoption('independent')
 kw={'assessment_ref':ar,'root_ref':rr,'independent_ref':ir}
 positive=m.validate_synthetic_adoption_fixture(assessment=a,root=root,independent=ind,**kw)
 assert positive['synthetic'] is True and positive['production_reuse_authorized'] is False and positive['real_proof_returned'] is False
 checks.append({'case':'synthetic_valid_documents_structure_only','passed':True,'real_proof_returned':False})
 def rejects(name,fn):
  try:fn()
  except (m.Rejected,ValueError) as e:checks.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError(name+' accepted')
 rejects('synthetic_never_enters_real_document_gate',lambda:m._documents(a,root,ind,synthetic=False,**kw))
 for name,change in [
  ('null_root',lambda aa,rr,ii:(aa,None,ii)),
  ('negative_identity',lambda aa,rr,ii:(dict(aa,same_controller_environment=False),rr,ii)),
  ('draft_independent',lambda aa,rr,ii:(aa,rr,dict(ii,status='draft'))),
  ('different_map',lambda aa,rr,ii:(aa,rr,dict(ii,map_ref=ref('wrong_map.json')))),
  ('different_identity_ref',lambda aa,rr,ii:(aa,dict(rr,identity_assessment_ref=ref('other_identity.json')),ii)),
  ('root_unbound_independent',lambda aa,rr,ii:(aa,dict(rr,independent_adoption_ref=None),ii)),
  ('same_root_independent_source',lambda aa,rr,ii:(aa,dict(rr,reviewer_source_ref=ii['reviewer_source_ref']),ii)),
  ('fake_historical_instance',lambda aa,rr,ii:(dict(aa,old_instance_hash_claimed=True),rr,ii)),
  ('invented_full_RNG_dump_requirement',lambda aa,rr,ii:(dict(aa,old_full_RNG_dump_required=True),rr,ii)),
  ('final_release_overclaim',lambda aa,rr,ii:(aa,dict(rr,final_release=True),ii))]:
  aa,bb,cc=change(copy.deepcopy(a),copy.deepcopy(root),copy.deepcopy(ind));rejects(name,lambda:m._documents(aa,bb,cc,synthetic=True,**kw))
 public={'legacy_root_ref':m.ROOT,'equivalence_map_ref':m.MAP,'root_adoption_ref':None,'independent_adoption_ref':None,'identity_assessment_ref':None,'suite':'libero_10','stage':'development','target_action_semantics_sha256':m.SEM}
 rejects('public_missing_real_adoptions',lambda:m.consume_legacy_development_proof(**public))
 rejects('public_final_rejected_before_IO',lambda:m.consume_legacy_development_proof(**dict(public,stage='final')))
 rejects('public_private_fixture_path_rejected',lambda:m.consume_legacy_development_proof(**dict(public,root_adoption_ref={'path':'.local/fixture.json','sha256':'0'*64})))
 rejects('public_changed_map_rejected',lambda:m.consume_legacy_development_proof(**dict(public,equivalence_map_ref=ref('different_map.json'))))
 rejects('path_traversal',lambda:m.valid_ref({'path':'results/formal_main_v2/../bad','sha256':'0'*64},receipt=True))
 evidence=m.inspect_legacy_evidence_only(legacy_root_ref=m.ROOT,equivalence_map_ref=m.MAP,suite='libero_10',stage='development',target_action_semantics_sha256=m.SEM)
 assert evidence['status']=='evidence_reconstructed_without_adoption' and evidence['production_reuse_authorized'] is False and evidence['totals']=={'trials':600,'chunks':23179,'actions':183676}
 checks.append({'case':'real_old_consumer_and_complete_raw_map_reconstruction','passed':True,'kind':'real_evidence_inspection_no_adoption'})
 report={'schema':'formal_main_v2','kind':'author_legacy600_consumer_candidate_CPU_review','status':'focused_CPU_checks_passed_no_real_adoption','source_sha256':hashlib.sha256(source).hexdigest(),'tests':checks,'actual_evidence':evidence,'synthetic_fixture_status':'in-memory only; not written as real adoptions and cannot enter public real API','real_adoption_receipts_created':0,'production_api_real_positive_executed':False,'original600_reused':False,'original600_rerun':False,'production_state_Git_source_changed':False,'new_GPU_seconds':0,'new_scientific_trials':0,'historical_GPU_seconds_preserved':10531,'CPU_wall_seconds':time.perf_counter()-START,'CPU_process_seconds':time.process_time()-CPU,'Long22_assembly_implemented':False,'final_release':False}
 write('CPU_review_v3.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['tests','actual_evidence']}))
except BaseException as e:
 write('CPU_failure_v3.json',{'error':str(e),'traceback':traceback.format_exc(),'completed_checks':checks,'CPU_wall_seconds':time.perf_counter()-START,'CPU_process_seconds':time.process_time()-CPU,'new_GPU_seconds':0,'real_adoption_receipts_created':0});raise
