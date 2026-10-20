"""Private, unactivated Long600 explicit compatibility proof API candidate.
No production module is edited. Old root/invocation/version remain genuine old
execution. Synthetic fixtures can validate structure but never produce a proof.
"""
from __future__ import annotations
import hashlib,json,math,struct,sys,types
from pathlib import Path
from collections import Counter
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');H=R.parent
OLD='formal-downstream-root-v1';NEW='formal-downstream-action-v1';VERSION='long-legacy6-proof-candidate-v3'
ROOT={'path':'results/formal_main_v2/downstream_reviews/3019954.json','sha256':'cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba'}
MAP={'path':'.local/legacy6_typed_bridge_0927/equivalence_map_candidate.json','sha256':'f3c7c2e3b3d4546748c4705bb8cba7f29c050470a22645215f7a894f899d3cc0'}
PRIOR={'path':'results/formal_main_v2/engineering/supervision_delivery_0830/Long_legacy6_provenance_independent/independent_readiness.json','sha256':'b786128f4f202c93da6a80f44c7c1fbeeacadef78724b76d9bef294615b7a3d5'}
IDENTITY_SUPPORT={'path':'results/formal_main_v2/preflight/heartbeat_20261020T1832/root_runtime_inode_evidence.json','sha256':'3f196ea78201de88c90d252c2d46deb18b0270560494361e457563e84d9bff21'}
SEM='4ef98a5beb21bfa790a8a0f484334d6d9020a481a517d8f89534562524025d7d'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'];JOBS=['3016981','3017161','3017959','3018505','3019176','3019954']
HELPER='scripts/formal_execution_manifests.py';CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'
SOURCE_SHA={HELPER:'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',CONSUMER:'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034','scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','.local/legacy6_typed_bridge_0927/build_map_v1.py':'f0958f6bbdbb1b9f45894c38cf57de1b4b8753b1f06dc2da23b43ce0e21e7c20'}
class Rejected(ValueError):pass
def require(ok,msg):
 if not ok:raise Rejected(msg)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def signature(v):return digest(canonical(v))
def pairs(xs):
 d={}
 for k,v in xs:require(k not in d,'duplicate JSON key');d[k]=v
 return d
def decode(b):
 def bad(x):raise Rejected('nonfinite JSON '+x)
 return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def valid_ref(v,*,receipt=False):
 require(type(v) is dict and set(v)=={'path','sha256'},'exact path/SHA reference required')
 path=v['path'];require(type(path) is str,'reference path type');p=Path(path)
 require(not p.is_absolute() and '..' not in p.parts and ':' not in path and '\\' not in path and p.as_posix()==path,'canonical relative reference')
 require(type(v['sha256']) is str and len(v['sha256'])==64 and all(c in '0123456789abcdef' for c in v['sha256']),'reference SHA')
 if receipt:require(path.startswith('results/formal_main_v2/'),'real adoption must be an immutable results receipt, not a private fixture')
 return v

def _load(evidence,rel):
 expected=SOURCE_SHA[rel];require(evidence.watch(rel)==expected,'exact source changed '+rel)
 p=evidence.path(rel);raw=p.read_bytes();require(digest(raw)==expected,'source race')
 m=types.ModuleType('_legacy600_'+digest((rel+expected).encode())[:24]);m.__file__=str(p);m.__package__='';sys.modules[m.__name__]=m
 exec(compile(raw,str(p),'exec',dont_inherit=True),m.__dict__);return m

def _evidence():
 # Always create the unchanged original Evidence implementation; callers cannot
 # supply a forged provider to skip IO/weight/final-value path restrictions.
 p=R/HELPER;raw=p.read_bytes();require(digest(raw)==SOURCE_SHA[HELPER],'helper SHA')
 m=types.ModuleType('_legacy600_exact_helper');m.__file__=str(p);m.__package__='';sys.modules[m.__name__]=m
 exec(compile(raw,str(p),'exec',dont_inherit=True),m.__dict__)
 ev=m.Evidence(R);ev.watch(HELPER);return ev

def _read_ref(ev,ref,*,receipt=False):
 valid_ref(ref,receipt=receipt);require(ev.watch(ref['path'])==ref['sha256'],'reference bytes changed')
 return decode(ev.path(ref['path']).read_bytes())

ASSESS_FIELDS={'schema','kind','version','status','review_role','synthetic','map_ref','legacy_root_ref','target_action_semantics_sha256','original_condition','decision','same_controller_environment','old_instance_hash_claimed','old_full_RNG_dump_required','historical_provenance_ref','supporting_evidence_refs','reviewer_source_ref','final_release'}
ADOPT_FIELDS={'schema','kind','version','status','review_role','synthetic','map_ref','legacy_root_ref','target_action_semantics_sha256','identity_assessment_ref','same_controller_environment','old_instance_hash_claimed','old_full_RNG_dump_required','independent_adoption_ref','reviewer_source_ref','final_release'}
def _documents(assessment,root,independent,*,assessment_ref,root_ref,independent_ref,synthetic):
 # This pure structure gate grants no authorization. Real IO API below always
 # calls with synthetic=False; tests use the separate synthetic-only function.
 require(type(synthetic) is bool,'synthetic type')
 valid_ref(assessment_ref);valid_ref(root_ref);valid_ref(independent_ref)
 require(len({assessment_ref['path'],root_ref['path'],independent_ref['path']})==3,'three distinct actual documents required')
 require(type(assessment) is dict and set(assessment)==ASSESS_FIELDS,'typed identity assessment required')
 require(assessment['schema']=='formal_main_v2' and assessment['kind']=='formal_legacy_controller_environment_identity_assessment' and assessment['version']=='long-legacy6-identity-v1' and assessment['status']=='passed' and assessment['review_role']=='independent','positive independent identity assessment required')
 require(assessment['original_condition']=='controller and environment were identical' and assessment['decision']=='sufficient_historical_source_chain','original identity judgment required')
 require(assessment['historical_provenance_ref']==PRIOR,'exact historical source-chain basis')
 require(type(assessment['supporting_evidence_refs']) is list and IDENTITY_SUPPORT in assessment['supporting_evidence_refs'],'exact additional runtime inode/source evidence required')
 require(len({x['path'] for x in assessment['supporting_evidence_refs']})==len(assessment['supporting_evidence_refs']),'duplicate identity support refs')
 for item in assessment['supporting_evidence_refs']:valid_ref(item,receipt=True)
 for role,doc in [('root',root),('independent',independent)]:
  require(type(doc) is dict and set(doc)==ADOPT_FIELDS,'typed adoption fields')
  require(doc['schema']=='formal_main_v2' and doc['kind']=='formal_legacy_development_equivalence_adoption' and doc['version']=='long-legacy6-adoption-v1' and doc['status']=='passed' and doc['review_role']==role,'positive matching-role adoption required')
  require(doc['identity_assessment_ref']==assessment_ref,'both adoptions must bind same exact identity assessment')
  require(doc['independent_adoption_ref']==(independent_ref if role=='root' else None),'root must bind this independent adoption; independent must not self-bind')
 for doc in [assessment,root,independent]:
  require(doc['synthetic'] is synthetic,'synthetic documents cannot enter real proof path')
  require(doc['map_ref']==MAP and doc['legacy_root_ref']==ROOT and doc['target_action_semantics_sha256']==SEM,'same exact map/root/target required')
  require(doc['same_controller_environment'] is True and doc['old_instance_hash_claimed'] is False and doc['old_full_RNG_dump_required'] is False and doc['final_release'] is False,'identity/measurement/final claim mismatch')
  valid_ref(doc['reviewer_source_ref'],receipt=True)
 require(root['reviewer_source_ref']!=independent['reviewer_source_ref'],'root and independent must not be the same review source')
 return {'status':'document_structure_checked_only','synthetic':synthetic,'production_reuse_authorized':False}

def validate_synthetic_adoption_fixture(*,assessment,root,independent,assessment_ref,root_ref,independent_ref):
 """Pure CPU test-only output; impossible to return the production envelope."""
 out=_documents(assessment,root,independent,assessment_ref=assessment_ref,root_ref=root_ref,independent_ref=independent_ref,synthetic=True)
 return {**out,'kind':'synthetic_adoption_schema_check','new_scientific_trials':0,'real_proof_returned':False}

def _f64(a):
 require(type(a) is list,'action matrix');flat=[]
 for row in a:
  require(type(row) is list and len(row)==7,'7 action columns')
  for x in row:require(type(x) in (int,float) and math.isfinite(x),'finite numeric action');flat.append(float(x))
 return struct.pack('<'+'d'*len(flat),*flat)

def _raw_rebuild(ev,*,legacy_root_ref,equivalence_map_ref):
 require(legacy_root_ref==ROOT and equivalence_map_ref==MAP,'this bounded API accepts only the registered Long legacy600 map')
 for rel,sha in SOURCE_SHA.items():require(ev.watch(rel)==sha,'source changed')
 consumer=_load(ev,CONSUMER)
 # Exact whole-chain reconstruction, no projection into the new execution.
 old=consumer.review_downstream_output(ev,legacy_root_ref,expected_stage='development',suite='libero_10')
 require(old.get('execution_version',OLD)==OLD and old['scientific_complete'] is True and old['completed_trials']==600,'genuine complete old600 required')
 mapping=_read_ref(ev,equivalence_map_ref);schema=_load(ev,'.local/legacy6_typed_bridge_0927/build_map_v1.py')
 trialref={k:mapping['trial_records'][k] for k in ('path','sha256')};_readable=ev.path(trialref['path']);require(ev.watch(trialref['path'])==trialref['sha256'],'typed trial bytes')
 records=[decode(x) for x in _readable.read_bytes().splitlines()];schema.validate_candidate(mapping,records)
 require(mapping['legacy']['root_review']==legacy_root_ref and mapping['legacy']['run_signature']==old['run_signature'],'map original root/config')
 manifest=_read_ref(ev,mapping['legacy']['execution_manifest']);identities={x['identity']['method_id']:x['identity'] for x in manifest['methods']}
 require(mapping['method_identities']==identities and list(identities)==METHODS,'original complete method identities')
 require(mapping['environment']==manifest['environment'],'same original environment')
 target=_read_ref(ev,mapping['target']['contract']);reviewer=_load(ev,'scripts/ops/formal_action_deployment_v1/reviewer.py')
 require(reviewer.semantic_identity(target)==SEM,'actual target semantics')
 for rel,sha in {**target['files'],**target['GPU_acceptance'],**target['runtime_contract']['dependencies']}.items():require(ev.watch(rel)==sha,'target source/acceptance changed')
 # Map/action evidence must remain immutable. Absolute provenance references are
 # bounded to audited project H/P prefixes and cannot read tensors/sealed states.
 eref={k:mapping['evidence'][k] for k in ('path','sha256')};evidence_map=_read_ref(ev,eref);external={}
 for rel,desc in evidence_map.items():
  p=Path(rel)
  if not p.is_absolute():require(ev.watch(rel)==desc['sha256'],'map evidence changed '+rel);continue
  require((H in p.parents or P in p.parents) and p.resolve()==p and '..' not in p.parts,'external metadata path')
  require(not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'} and not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts),'external weight/sealed forbidden')
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  require(h.hexdigest()==desc['sha256'] and p.stat().st_size==desc['bytes'],'external provenance changed');external[rel]=desc['sha256']
 bytrial={r['trial_id']:r for r in records};require(len(bytrial)==600,'unique600 candidate records')
 ledger=mapping['legacy']['raw_ledger'];require(ev.watch(ledger['path'])==ledger['sha256']==old['files'][ledger['path']],'original ledger SHA')
 offset=0;active=None;job=None;seen=set();states={};totals=Counter();summary={m:Counter() for m in METHODS}
 for n,b in enumerate(ev.path(ledger['path']).open('rb'),1):
  require(b.endswith(b'\n'),'complete ledger line');lr={'line':n,'byte_offset':offset,'bytes':len(b),'sha256':digest(b)};offset+=len(b);r=decode(b)
  require(r['run_signature']==old['run_signature'],'raw config identity')
  if r['event']=='invocation':require(active is None,'unfinished trial');job=r['slurm_job_id'];require(job in JOBS,'known original job');continue
  if r['event']=='start':require(active is None,'trial overlap');active=(r,lr);continue
  require(r['event']=='result' and active is not None,'paired result');start,sr=active;active=None;c=bytrial[r['trial_id']]
  require(r['trial_id'] not in seen,'duplicate genuine result');seen.add(r['trial_id'])
  require(c['source']['job_id']==job and c['source']['start_line']==sr and c['source']['result_line']==lr,'raw trial positions')
  for k in ['trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','suite','split']:require(c[k]==r[k]==start[k],'trial identity '+k)
  require(r['method']==start['method']==c['method_id'] and r['split']=='development' and r['suite']=='libero_10','method/split')
  identity=identities[r['method']];require(c['method_identity_sha256']==signature(identity),'method/checkpoint')
  require(r['environment_seed']==0 and r['runtime_seed']==17 and r['configured_wait_steps']==r['wait_steps']==10 and r['action_chunk']==8,'original environment flags')
  require(c['outcome']=={k:r[k] for k in ['status','success','termination','control_steps']} and r['status']=='completed','original outcome preserved')
  queue=[];clip=0
  for i,ch in enumerate(r['chunks']):
   require(ch['control_step']==8*i and len(ch['environment_actions'])==len(ch['normalized_actions'])==8,'all emitted8 required');_f64(ch['normalized_actions']);_f64(ch['environment_actions'])
   for action in ch['environment_actions']:
    require(all(abs(x)<=1.00001 for x in action),'former rejected range');clip+=sum(abs(x)>1 for x in action)
   md=ch['metadata'];require(md['method']==identity['method'] and md['visual_tokens']==identity['visual_tokens'] and md['future_head_calls']==0,'same deployed method')
   if identity['method'] in ('A','B'):require(md['selector_checkpoint_sha256']==identity['checkpoint_sha256'],'same selected checkpoint')
   queue.extend(ch['environment_actions'])
  require(clip==0 and len(r['chunks'])==r['policy_calls']==math.ceil(r['control_steps']/8),'all clipping inactive and full chunks')
  actual=_f64(r['executed_actions']);require(actual==_f64(queue[:r['control_steps']]) and len(r['executed_actions'])==r['control_steps'],'actual queue prefix')
  a=c['action_evidence'];require(a['recorded_executed_f64le_sha256']==digest(actual)==a['old_CPU_replay_executed_sha256']==a['new_CPU_replay_executed_sha256'] and a['all_emitted_f64le_sha256']==digest(_f64(queue)),'map action hashes bind actual bytes')
  require(a['full_chunks']==len(r['chunks']) and a['executed_actions']==r['control_steps'],'map action counts')
  state=states.setdefault(r['state_trial_id'],{'sha256':r['initial_state_sha256'],'methods':set()});require(state['sha256']==r['initial_state_sha256'] and r['method'] not in state['methods'],'state conflict');state['methods'].add(r['method'])
  totals.update(trials=1,chunks=len(r['chunks']),actions=r['control_steps']);summary[r['method']].update(trials=1,successes=int(r['success']))
 require(active is None and seen==set(bytrial) and totals==Counter(trials=600,chunks=23179,actions=183676),'complete raw600')
 require(len(states)==100 and all(s['methods']==set(METHODS) for s in states.values()),'same100 complete6')
 require(old['cost']['all_attempt_gpu_seconds']==10531 and [a['job_id'] for a in old['cost']['allocations']]==JOBS,'original costs')
 # Close absolute source/package evidence against concurrent changes as well.
 for filename,checksum in external.items():
  ep=Path(filename);require(ep.resolve()==ep,'external path changed while auditing');eh=hashlib.sha256()
  with ep.open('rb') as stream:
   for block in iter(lambda:stream.read(8<<20),b''):eh.update(block)
  require(eh.hexdigest()==checksum,'external evidence changed while auditing')
 ev.unchanged()
 return {'original_review':old,'map':mapping,'trial_records_ref':trialref,'unique_states':{k:v['sha256'] for k,v in states.items()},'method_identities':identities,'per_method':{k:dict(v) for k,v in summary.items()},'evidence_sha256':dict(ev.files),'external_provenance_sha256':external,'totals':dict(totals)}

def inspect_legacy_evidence_only(*,legacy_root_ref,equivalence_map_ref,suite,stage,target_action_semantics_sha256):
 """Read-only engineering inspection. Never an adoption/compatibility proof."""
 require(suite=='libero_10' and stage=='development' and target_action_semantics_sha256==SEM,'only exact Long development scope')
 ev=_evidence();x=_raw_rebuild(ev,legacy_root_ref=legacy_root_ref,equivalence_map_ref=equivalence_map_ref)
 return {'schema':'formal_main_v2','kind':'legacy600_evidence_inspection_only','status':'evidence_reconstructed_without_adoption','totals':x['totals'],'original_execution_version':OLD,'original_GPU_seconds':10531,'evidence_files':len(x['evidence_sha256']),'external_files':len(x['external_provenance_sha256']),'production_reuse_authorized':False,'final_release':False}

def consume_legacy_development_proof(*,legacy_root_ref,equivalence_map_ref,root_adoption_ref,independent_adoption_ref,identity_assessment_ref,suite,stage,target_action_semantics_sha256):
 """Strict real-receipt API. No synthetic flag, release, Slurm or write path."""
 require(suite=='libero_10' and stage=='development' and target_action_semantics_sha256==SEM,'final/other suite or semantics rejected before IO')
 require(legacy_root_ref==ROOT and equivalence_map_ref==MAP,'exact bounded source/map only')
 for r in [root_adoption_ref,independent_adoption_ref,identity_assessment_ref]:valid_ref(r,receipt=True)
 ev=_evidence();root=_read_ref(ev,root_adoption_ref,receipt=True);ind=_read_ref(ev,independent_adoption_ref,receipt=True);assessment=_read_ref(ev,identity_assessment_ref,receipt=True)
 _documents(assessment,root,ind,assessment_ref=identity_assessment_ref,root_ref=root_adoption_ref,independent_ref=independent_adoption_ref,synthetic=False)
 for doc in [root,ind,assessment]:_read_ref_source=doc['reviewer_source_ref'];valid_ref(_read_ref_source,receipt=True);require(ev.watch(_read_ref_source['path'])==_read_ref_source['sha256'],'real review implementation reference changed')
 require(ev.watch(PRIOR['path'])==PRIOR['sha256'],'historical identity evidence changed')
 for item in assessment['supporting_evidence_refs']:_read_ref(ev,item,receipt=True)
 x=_raw_rebuild(ev,legacy_root_ref=legacy_root_ref,equivalence_map_ref=equivalence_map_ref);ev.unchanged()
 return {'schema':'formal_main_v2','kind':'explicit_legacy_development_compatibility_envelope','version':VERSION,'status':'real_bound_adoptions_and_legacy_evidence_verified','suite':suite,'stage':stage,'legacy_execution_version':OLD,'original_root_ref':legacy_root_ref,'original_root_review':x['original_review'],'original_invocations_ran_new_wrapper':False,'target_execution_version':NEW,'target_action_semantics_sha256':SEM,'map_ref':equivalence_map_ref,'trial_records_ref':x['trial_records_ref'],'adoptions':{'root':root_adoption_ref,'independent':independent_adoption_ref,'identity_assessment':identity_assessment_ref},'method_identities':x['method_identities'],'unique_state_identities':x['unique_states'],'per_method':x['per_method'],'original_allocations':x['original_review']['cost']['allocations'],'historical_GPU_seconds':10531,'new_GPU_seconds':0,'new_scientific_trials':0,'additional_independent_initial_states':0,'all600_included':True,'compatibility_class':'legacy_equivalent_not_new_wrapper_execution','legacy_equivalent_trials':600,'actual_new_wrapper_trials_added':0,'raw_trial_ledger_unchanged':True,'evidence_sha256':x['evidence_sha256'],'external_provenance_sha256':x['external_provenance_sha256'],'scope':'compatible development proof only; caller must still apply unchanged all88/four-suite/global freeze and full timing gates','final_release':False,'GPU_submission_authorized':False,'old_latency_reused':False,'production_activation_inferred':False}
