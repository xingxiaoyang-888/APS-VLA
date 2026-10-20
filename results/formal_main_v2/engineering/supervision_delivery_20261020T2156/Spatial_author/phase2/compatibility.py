"""Bounded Spatial12 compatibility admission. No general legacy or release bypass.

The immutable author proof records source-derived historical identity, not a
captured old controller or RNG dump. Independent review plus explicit root
adoption is mandatory. Every use rechecks the exact original raw12 prefix and
its full emitted and executed action bytes, including unused chunk tails.
"""
from pathlib import Path
import hashlib,json,math,struct
VERSION='formal-spatial12-compatibility-adoption-v1'
ADOPTION='results/formal_main_v2/execution/spatial588_pre_dispatch_v1/legacy12_root_adoption.json'
PHASE1_SHA='20d8ee977e9735592660025acd4769c74935963f419d582f5c32fe74000ae5d3'
PROOF_SHA='c2b46372be33cfe35c53643211b602102652d3662fb74a58553142a6e6a944f2'
SEMANTICS='cbcee0a9ba3d6d81345cedf4c01bbca4f5be232f522e52903d9a887b7008db23'
_C=None

def bind_control(control):
 global _C
 if _C is not None:raise ValueError('compatibility control cannot be rebound')
 _C=control

def req(v,m):
 if not v:raise ValueError(VERSION+': '+m)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def sig(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
def bundle(n):
 req(_C is not None,'private control binding required')
 p=_C.policy();req(n in p['compatibility_bundle_files'],'unknown compatibility bundle file')
 f=_C.BASE/n;req(f.resolve()==f and not f.is_symlink(),'canonical exact bundle path')
 raw=f.read_bytes();req(sha(raw)==p['compatibility_bundle_files'][n],'compatibility artifact drift: '+n);return raw

def proof():
 p=json.loads(bundle('compatibility_proof.json'));req(sha(bundle('phase1_manifest.json'))==PHASE1_SHA and sha(bundle('compatibility_proof.json'))==PROOF_SHA,'frozen phase1 identity differs')
 req(p['schema']=='formal_main_v2' and p['kind']=='bounded_Spatial12_legacy_development_compatibility_candidate' and p['status']=='author_compatibility_passed_pending_independent_root_adoption' and p['production_admission'] is False,'author proof cannot self-adopt')
 req(p['counts']=={'chunks':122,'executed_actions':917,'trials':12} and p['target']['action_semantics_sha256']==SEMANTICS,'exact12 action proof required')
 req(p['full122_chunks_and917_executed_actions_byte_equal'] is True and p['no_controller_clipping_changed_components'] is True and p['unknown_historical_instance_capture_not_invented'] is True,'exact byte/controller proof missing')
 req(p['new_GPU_seconds']==p['new_scientific_trials']==0 and p['weights_read'] is False and p['sealed_values_read'] is False,'proof scope expanded')
 return p

def descriptor():
 p=proof();rel=lambda n:(_C.BASE/n).relative_to(_C.R).as_posix()
 return {'schema':'formal_main_v2','kind':'exact_Spatial12_compatibility_descriptor','version':VERSION,'author_proof':{'path':rel('compatibility_proof.json'),'sha256':PROOF_SHA},'phase1_manifest':{'path':rel('phase1_manifest.json'),'sha256':PHASE1_SHA},'scope':p['scope'],'legacy_job_id':'3022743','legacy_origin_preserved':True,'legacy_trial_ids':p['legacy_trial_ids'],'original_prefix':p['original_prefix'],'target_action_semantics_sha256':SEMANTICS,'root_adoption':ADOPTION,'final_release':False,'profiling_authorized':False,'automatic_submission':False,'new_GPU_seconds':0,'new_scientific_trials':0}

def f64(matrix,width=7):
 req(type(matrix)is list,'action matrix must be list')
 parts=[]
 for row in matrix:
  req(type(row)is list and len(row)==width,'action width differs')
  for x in row:
   req(type(x) in (int,float) and math.isfinite(x),'nonfinite/non-numeric action')
   parts.append(struct.pack('<d',float(x)))
 return b''.join(parts)

def audit_prefix(evidence,*,postrun=False):
 p=proof();e=_C.Evidence(evidence);policy=_C.policy()
 for n,h in policy['compatibility_bundle_files'].items():req(e.watch((_C.BASE/n).relative_to(_C.R).as_posix())==h,'bundle evidence SHA differs')
 req(p['scope']=={'stage':'development','suite':'libero_spatial','methods':policy['method_ids'],'total_panel_trials':600,'legacy_trials':12,'remaining_trials':588},'compatibility scope changed')
 pref=p['original_prefix'];req(pref['job_id']=='3022743' and {k:pref[k] for k in ('path','bytes','sha256')}==policy['prefix_ledger'] and pref['root_review']==policy['prefix_review'],'proof/prefix policy differs')
 e.watch(pref['path']);ledger=e.path(pref['path']);req(ledger.stat().st_size>=pref['bytes'] and (postrun or ledger.stat().st_size==pref['bytes']),'prefix length drift')
 with ledger.open('rb') as stream:raw=stream.read(pref['bytes'])
 req(sha(raw)==pref['sha256'] and raw.endswith(b'\n'),'original raw prefix changed')
 lines=raw.splitlines(keepends=True);rows=[json.loads(x) for x in lines]
 req(len(rows)==25 and [str(x.get('slurm_job_id')) for x in rows if x.get('event')=='invocation']==['3022743'],'fabricated prefix invocation')
 expected=p['legacy_trial_ids'];req(len(expected)==len(set(expected))==12,'fixed legacy12 set')
 results=[x for x in rows if x.get('event')=='result'];starts=[x for x in rows if x.get('event')=='start']
 req([x['trial_id'] for x in results]==[x['trial_id'] for x in starts]==expected,'legacy trial order/set differs')
 records=[json.loads(x) for x in bundle('per_trial_compatibility.jsonl').splitlines()];chunks=[json.loads(x) for x in bundle('per_chunk_compatibility.jsonl').splitlines()]
 req(len(records)==12 and len(chunks)==122 and [x['trial_id'] for x in records]==expected,'proof trial/chunk scope differs')
 for ref in [p['manifest'],p['original_config'],p['panel'],pref['root_review']]:req(e.watch(ref['path'])==ref['sha256'],'immutable prefix identity differs')
 manifest=e.read(p['manifest']['path']);req(manifest['split']=='development' and manifest['suite']=='libero_spatial' and manifest['environment']==p['environment'],'science environment changed')
 identities={x['identity']['method_id']:x['identity'] for x in manifest['methods']};req(identities==p['method_identities'],'original checkpoint/config/input identities changed')
 counts={'trials':0,'chunks':0,'executed_actions':0};chunk_cursor=0
 offsets=[];offset=0
 for line in lines:offsets.append(offset);offset+=len(line)
 for record,row,start in zip(records,results,starts):
  for field in ('trial_id','state_trial_id','task_id','task_name','method','source_state_index','initial_state_sha256','action_chunk','configured_wait_steps','environment_seed','runtime_seed','run_signature','split','suite'):
   req(record[field]==row[field]==start[field],'trial start/result/proof identity: '+field)
  req(row['status']=='completed' and record['outcome']=={k:row[k] for k in ('status','success','termination','control_steps')},'original outcome changed')
  req(record['method_identity_sha256']==sig(identities[row['method']]),'method/base/selector identity differs')
  for kind,r in [('start',start),('result',row)]:
   at=rows.index(r);saved=record['source'][kind+'_line'];req(saved=={'line':at+1,'byte_offset':offsets[at],'bytes':len(lines[at]),'sha256':sha(lines[at])},'raw line location/byte proof changed')
  queue=[];metadata=[]
  for idx,chunk in enumerate(row['chunks']):
   req(chunk['control_step']==idx*8,'exact full8 chunk sequence')
   env=chunk['environment_actions'];norm=chunk['normalized_actions'];req(len(env)==len(norm)==8,'full emitted8 tail omitted')
   env_bytes=f64(env);norm_bytes=f64(norm)
   req(all(abs(x)<=1 for action in env for x in action),'old pure range predicate/controller clipping can differ')
   c=chunks[chunk_cursor];req(c['trial_id']==row['trial_id'] and c['chunk']==idx and c['environment_f64le_sha256']==sha(env_bytes) and c['normalized_f64le_sha256']==sha(norm_bytes) and c['metadata_sha256']==sig(chunk['metadata']) and c['observation_sha256']==chunk['observation_sha256'],'chunk bytes/metadata/observation proof differs')
   queue.extend(env);metadata.append(sig(chunk['metadata']));counts['chunks']+=1;chunk_cursor+=1
  executed=f64(row['executed_actions']);req(len(row['executed_actions'])==row['control_steps'] and executed==f64(queue[:row['control_steps']]),'executed action queue differs')
  req(record['full_emitted_chunks']==len(row['chunks']) and record['executed_actions']==row['control_steps'] and record['full_emitted_f64le_sha256']==sha(f64(queue)) and record['executed_f64le_sha256']==sha(executed) and record['metadata_sequence_sha256']==sig(metadata),'trial action digest differs')
  req(record['old_runtime']==record['target_runtime'] and record['old_runtime']['RNG_unchanged'] is True and record['old_runtime']['executed_f64le_sha256']==sha(executed) and record['old_runtime']['new_simulator_execution'] is False,'CPU old/new byte identity differs')
  req(record['clip6_changed_components']==record['clip7_diagnostic_changed_components']==0 and record['legacy_origin_preserved'] is True and record['new_scientific_trial'] is False and record['target_action_semantics_sha256']==SEMANTICS,'unproved trial admitted')
  counts['trials']+=1;counts['executed_actions']+=row['control_steps']
 req(counts==p['counts'],'exact12/122/917 counts differ')
 history=json.loads(bundle('historical_identity.json'))
 req(history['kind']=='source_derived_historical_Spatial_controller_identity' and history['job_id']=='3022743' and history['actual_historical_controller_instance_capture'] is False,'historical inference mislabeled')
 rng=history['RNG'];req(rng['old_full_snapshot_recorded'] is False and rng['historical_full_snapshot_required'] is False and rng['CPU_python_numpy_unchanged'] is True and rng['same_frozen_factory_and_trial_loop'] is True and rng['only_removed_branch_is_pure_numpy_range_predicate'] is True and rng['no_new_rng_calls_or_action_changes'] is True,'registered deterministic RNG rule missing')
 req(history['limits']['control_delta'] is True and history['limits']['input_min']==-1 and history['limits']['input_max']==1,'controller semantic identity differs')
 e.unchanged();return descriptor()

def validate_adoption_documents(root,independent,*,independent_ref):
 d=descriptor();p=proof()
 req(type(independent_ref)is dict and set(independent_ref)=={'path','sha256'} and independent_ref['path'].startswith('results/formal_main_v2/') and independent_ref['path']!=ADOPTION,'canonical independent root archive required')
 want={'schema':'formal_main_v2','kind':'Spatial12_legacy_compatibility_root_adoption','version':VERSION,'status':'root_adopted','reviewed_by':'root','compatibility_descriptor':d,'independent_review':independent_ref,'source_closure':_C.closure(),'legacy_origin_preserved':True,'historical_controller_is_source_inference':True,'new_GPU_seconds':0,'new_scientific_trials':0,'final_release':False,'profiling_authorized':False}
 req(all(root.get(k)==v for k,v in want.items()),'root adoption missing or differs from exact legacy scope')
 req(independent.get('schema')=='formal_main_v2' and independent.get('kind')=='Spatial12_legacy_compatibility_independent_review' and independent.get('status')=='passed' and independent.get('proof_sha256')==PROOF_SHA and independent.get('phase1_manifest_sha256')==PHASE1_SHA and independent.get('scope')==p['scope'] and independent.get('blockers')==[] and independent.get('reviewed_by')=='independent' and independent.get('full_original_author_reconstruction_passed') is True and independent.get('independent_byte_and_queue_reconstruction_passed') is True and independent.get('production_admission') is False and independent.get('new_GPU_seconds')==0 and independent.get('new_scientific_trials')==0,'independent exact proof is missing or failed')
 return d

def check_adoption(evidence,*,invocation=None,postrun=False):
 e=_C.Evidence(evidence);d=audit_prefix(evidence,postrun=postrun);root=e.read(ADOPTION);ref=root.get('independent_review')
 req(type(ref)is dict and set(ref)=={'path','sha256'},'independent ref required')
 req(ref['path'].startswith('results/formal_main_v2/') and ref['path']!=ADOPTION,'independent report must be a separate archived record')
 req(e.watch(ref['path'])==ref['sha256'],'independent report SHA differs');ind=e.read(ref['path']);validate_adoption_documents(root,ind,independent_ref=ref)
 if invocation is not None:
  _C.scope_invocation(invocation);ref=invocation.get('action_execution_contract');req(type(ref)is dict and set(ref)=={'path','sha256'},'actual new runtime contract required')
  req(e.watch(ref['path'])==ref['sha256'],'new runtime contract changed');contract=e.read(ref['path']);reviewer=_C._original(_C.REVIEWER)
  req(reviewer.semantic_identity(contract)==SEMANTICS,'new runtime action semantics differ from legacy proof')
  req(contract['runtime_contract']['suite']=='libero_spatial' and contract['runtime_contract']['stage']=='development' and contract['scientific_settings_changed'] is False and contract['final_evaluation_enabled'] is False,'runtime scope changed')
 e.unchanged();return d

def adoption_proposal():
 return {'schema':'formal_main_v2','kind':'Spatial12_legacy_compatibility_root_adoption','version':VERSION,'status':'candidate_requires_independent_and_root_adoption','reviewed_by':None,'compatibility_descriptor':descriptor(),'independent_review':None,'source_closure':_C.closure(),'legacy_origin_preserved':True,'historical_controller_is_source_inference':True,'new_GPU_seconds':0,'new_scientific_trials':0,'final_release':False,'profiling_authorized':False}
