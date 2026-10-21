#!/usr/bin/env python3
"""Fixed CPU evidence diagnosis only; no environment/model imports or execution."""
from pathlib import Path, PurePosixPath
import ast, copy, hashlib, io, json, math, sys, tarfile, time, traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_bounded_diagnostic_20261020T2358'
O=P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01'
N=P/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01'
AR=R/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01/observer'
T=R/'.local/goal_terminal_independent_20261020T2253'
KEYS=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
IDENTITY='libero_goal:put_the_bowl_on_the_stove:state-0012:env-0:B256_seed17'
PINS={
str(O/'original_run/trials.jsonl'):'984fdcf8a311d483f31c117aeeb34552a1971fa0b06f4db167e02b67ef8d039e',
str(N/'original_run/trials.jsonl'):'60cceb3556ca25e190178b047d58e700cd55403d333a54cecac05116deaf1906',
str(O/'observer/events.jsonl'):'6586699a2247e86729f4a43f93a2d63c9d9254362b5de99c74976336e11ba42b',
str(N/'observer/events.jsonl'):'ae80ae45e4a6364fd338555bba387ff028bd803a2a2bb112221c1c17858bd7b9',
str(N/'observer/gate.jsonl'):'f253f0bf2dde666f3d8591813b9885e2e7472988a0bd849436e3feaceaa44c46',
str(O/'outer/completion.json'):'8c686a37d1ad4556ac06f6963166a9e2840fa2661e5805fb2c3e8b91ed26d483',
str(N/'outer/completion.json'):'ebd1813f5dc506ccb7a286a5aa750e6e6fbb775f935bb54598df2314bc345d38',
str(N/'outer/events.jsonl'):'4613115d4508f723d1e912083ca2ebfcacce8136dc02f83689d7d8b537f1dabe',
str(O/'original_run/config.json'):'07bbc7066a8c739622f175087e7af098735dd4bb1baeb98ff6d7634e2dc9ad07',
str(N/'original_run/config.json'):'07bbc7066a8c739622f175087e7af098735dd4bb1baeb98ff6d7634e2dc9ad07',
str(R/'src/cti_vla/evaluation/libero_runtime.py'):'2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781',
str(P/'snapshots/formal_main_v2_run_564be0995e/src/cti_vla/evaluation/libero_runtime.py'):'2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781',
str(R/'scripts/ops/formal_goal_paired_input_gate_v1/observer_v3.py'):'7a33c4ec531e0524a5e30b51e18205dc7d354868afa6190e3f39dcf14b283241',
str(R/'scripts/ops/formal_goal_paired_input_gate_v1/paired_input_gate_v1.py'):'389cab5bb9e8464fa3666fac23db34be9e500a8ea92f7cea12223406796797d0',
str(R/'scripts/ops/formal_goal_paired_input_gate_v1/ast_observer_v2.py'):'e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e',
str(R/'scripts/ops/formal_goal_paired_input_gate_v1/package_manifest.json'):'7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec',
str(AR/'blob_archive_manifest.json'):'471ce3a437018859550bba77c6b456b6c5fa8ca52477a41dc6bbf551a7e58be8',
str(T/'terminal_review.json'):'e48e5f5a0855c81280ea9cd4eb014aefe45c3b18d324836930b5a5ef1e1d4d61',
str(T/'archive_review.json'):'3b7166d6422cbf4551fcd54a0f7d15a08e30d6b0f2de8d2d644f5578f6dd8fd5',
str(T/'bounded_diagnostic.json'):'c1b9de88b2781ade315b3db5bb3000473ca74d36f994adfc00ac11e297dfa354',
str(T/'historical_comparison.json'):'6e247d501f964581bdc13a0a86332b84f5dfa1d338abbef4c8ba4009d3597b3d',
}
checks=[];reads={};blob_reads={};start=time.perf_counter()
def digest(b):return hashlib.sha256(b).hexdigest()
def jb(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def need(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise ValueError(label)
def rd(p,expected=None):
 p=Path(p);need(p.is_file() and not p.is_symlink(),'regular source '+str(p))
 b=p.read_bytes();actual=digest(b)
 if expected is not None:need(actual==expected,'SHA '+str(p))
 reads[str(p)]={'sha256':actual,'bytes':len(b)}
 return b
def out(name,value):
 p=D/name
 need(p.parent==D and not p.exists(),'new private output '+name)
 p.write_bytes(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n')
def rows(b):return [json.loads(x) for x in b.splitlines() if x.strip()]
def blob(base,ref):
 rel=PurePosixPath(ref['path']);need(not rel.is_absolute() and '..' not in rel.parts and rel.parts[0]=='blobs','exact blob relative path')
 p=base/'observer'/ref['path'];raw=rd(p,ref['sha256']);need(len(raw)==ref['bytes'],'blob size')
 blob_reads[str(p)]={'sha256':digest(raw),'bytes':len(raw)}
 return raw
def observed(base,event):
 result={}
 need(set(event['observation_arrays'])==set(KEYS),'five observed components')
 for key in KEYS:
  meta=event['observation_arrays'][key];raw=blob(base,meta['blob'])
  need(meta['sha256']==digest(raw) and meta['bytes']==len(raw),'array byte identity '+key)
  dtype=np.dtype(meta['dtype']);shape=tuple(meta['shape'])
  need(not dtype.hasobject and len(raw)==math.prod(shape)*dtype.itemsize,'array shape/dtype size '+key)
  arr=np.frombuffer(raw,dtype=dtype).reshape(shape)
  need(np.isfinite(arr).all(),'finite selected observed '+key)
  result[key]={'dtype':str(dtype),'shape':list(shape),'bytes':raw}
 return result
def obs_hash(parts):
 h=hashlib.sha256()
 for key in KEYS:
  v=parts[key];h.update(key.encode()+v['dtype'].encode()+str(tuple(v['shape'])).encode()+v['bytes'])
 return h.hexdigest()
def classify(e):
 for k in ('integrity','identity_same','schema_same'):
  if e.get(k) is not True:raise ValueError('untrusted '+k)
 if e.get('old_sampling')!='post_policy' or e.get('new_sampling')!='pre_and_post_policy':raise ValueError('unknown capture timing')
 if e.get('new_pre')!=e.get('new_post'):raise ValueError('new input mutation')
 if e.get('old_pre_available') not in (True,False):raise ValueError('missing availability')
 if e['old_pre_available'] and e.get('old_pre') is None:raise ValueError('claimed capture missing')
 if not e['old_pre_available'] and e.get('old_pre') is not None:raise ValueError('unproven old pre supplied')
 if e['old_post']==e['new_post']:decision='no_logged_post_observation_difference'
 elif not e['old_pre_available']:decision='post_observation_difference_origin_unresolved'
 elif e['old_pre']!=e['new_pre']:decision='pre_policy_input_difference_observed'
 else:decision='old_observation_changed_within_policy_interval'
 return {'decision':decision,'root_cause_identified':False,'scientific_release':False,'old200_adopted':False,
         'equal_commands_before_boundary':e.get('actions_before_same') is True,
         'intermediate_simulator_or_rng_equality_proved':False,
         'old_pre_policy_equality_proved':e['old_pre_available'] and e['old_pre']==e['new_pre']}
def main():
 need(Path(__file__).resolve().parent==D and D.is_dir(),'exact private directory')
 content={p:rd(p,sha) for p,sha in PINS.items()}
 contract=json.loads(rd(D/'contract.json'))
 need(contract['fixed_ordinal']==30 and contract['new_GPU_jobs']==0 and contract['scientific_trials_added']==0,'CPU scope contract')
 old=rows(content[str(O/'original_run/trials.jsonl')]);new=rows(content[str(N/'original_run/trials.jsonl')])
 ot=[r for r in old if r.get('event')=='result'];nt=[r for r in new if r.get('event')=='result']
 need(len(ot)==len(nt)==58,'both complete fixed58')
 need([r['trial_id'] for r in ot]==[r['trial_id'] for r in nt],'same exact ordered58 identities')
 fields=('control_step','observation_sha256','normalized_actions','environment_actions','metadata')
 changed=[]
 for i,(a,b) in enumerate(zip(ot,nt),1):
  aa=[{k:c[k] for k in fields} for c in a['chunks']];bb=[{k:c[k] for k in fields} for c in b['chunks']]
  if aa!=bb or a['executed_actions']!=b['executed_actions']:changed.append(i)
 need(changed==[30],'only ordinal30 logged trace change among all58')
 a,b=ot[29],nt[29]
 need(a['trial_id']==b['trial_id']==IDENTITY and a['task_id']==b['task_id']==1 and a['source_state_index']==b['source_state_index']==12,'fixed diagnostic identity')
 need(len(a['chunks'])==len(b['chunks'])==11,'fixed11 queries')
 idkeys=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method','environment_seed','runtime_seed','configured_wait_steps','action_chunk','run_signature')
 need({k:a[k] for k in idkeys}=={k:b[k] for k in idkeys},'all identity and runtime fields')
 oe=[e for e in rows(content[str(O/'observer/events.jsonl')]) if e.get('ordinal')==30]
 ne=[e for e in rows(content[str(N/'observer/events.jsonl')]) if e.get('ordinal')==30]
 gate=[e for e in rows(content[str(N/'observer/gate.jsonl')]) if e.get('ordinal')==30]
 need(not any(e.get('control_step',0) not in (None,0) for e in oe),'old recorder has no nonzero query raw capture')
 qs={}
 for q,c in enumerate(b['chunks']):
  step=8*q
  need(c['control_step']==a['chunks'][q]['control_step']==step,'query ordinal/step alignment')
  pre=[e for e in ne if e.get('control_step')==step and e.get('phase') in ('t0_query_before','query_before')]
  post=[e for e in ne if e.get('control_step')==step and e.get('phase') in ('t0_query_after','query_after')]
  need(len(pre)==len(post)==1,'unique pre/post')
  pre,post=pre[0],post[0]
  need(pre['trial_identity']['trial_id']==post['trial_identity']['trial_id']==IDENTITY,'capture identity')
  pa=observed(N,pre);po=observed(N,post)
  need(pa==po and obs_hash(pa)==pre['observation_sha256']==post['observation_sha256']==c['observation_sha256'],'new exact before/after and ledger hash')
  ge=[e for e in gate if e.get('event')=='query_integrity_passed' and e.get('control_step')==step]
  need(len(ge)==1 and ge[0]['capture_event_index']==post['event_index'],'new immutable query receipt')
  for action_name in ('environment_actions','normalized_actions'):
   m=ge[0]['returned_actions'][action_name];raw=bytes.fromhex(m['bytes_hex'])
   need(digest(raw)==m['sha256'] and len(raw)==m['bytes'],'action raw receipt')
   arr=np.frombuffer(raw,dtype=np.dtype(m['dtype'])).reshape(tuple(m['shape']))
   need(arr.tolist()==c[action_name],'new actions raw equal original ledger')
  qs[q]={'pre':pre,'post':post,'parts':pa,'gate':ge[0]}
 oldt0=next(e for e in oe if e.get('phase')=='t0_query_before')
 need(observed(O,oldt0)==qs[0]['parts'],'old/new t0 raw observation bytes')
 t0_sim={}
 for field in ('sim','sim_array_blobs','global_rng'):
  need(oldt0[field]==qs[0]['pre'][field],'old/new initial '+field);t0_sim[field]=True
 for base,e in ((O,oldt0),(N,qs[0]['pre'])):
  blob(base,e['global_rng'])
  for ref in e['sim_array_blobs'].values():blob(base,ref)
 first_hash=next(i for i,(x,y) in enumerate(zip(a['chunks'],b['chunks'])) if x['observation_sha256']!=y['observation_sha256'])
 first_action=next(i for i,(x,y) in enumerate(zip(a['executed_actions'],b['executed_actions'])) if x!=y)
 need(first_hash==9 and first_action==72,'first visible hash q9 and command72')
 need(all(all(a['chunks'][i][k]==b['chunks'][i][k] for k in fields) for i in range(9)),'prior9 posthash/chunks/meta equal')
 need(a['executed_actions'][:72]==b['executed_actions'][:72],'prior72 logged environment commands exact')
 for i in range(64,72):
  ge=[e for e in gate if e.get('event')=='policy_step_executed' and e.get('control_step')==i]
  need(len(ge)==1,'bounded step raw receipt')
  m=ge[0]['action'];raw=bytes.fromhex(m['bytes_hex']);arr=np.frombuffer(raw,dtype=np.dtype(m['dtype'])).reshape(tuple(m['shape']))
  need(digest(raw)==m['sha256'] and arr.tolist()==b['executed_actions'][i]==a['executed_actions'][i],'exact command delivered '+str(i))
 raw=content[str(R/'src/cti_vla/evaluation/libero_runtime.py')].decode()
 tree=ast.parse(raw);run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_episode')
 calls=[n for n in ast.walk(run) if isinstance(n,ast.Call)]
 pred=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='predict_chunk']
 hashes=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='_observation_hash']
 actionsteps=[n for n in calls if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='env' and n.func.attr=='step' and ast.unparse(n.args[0])=='action.tolist()']
 need(len(pred)==len(hashes)==len(actionsteps)==1 and pred[0].lineno<hashes[0].lineno<actionsteps[0].lineno,'hash is post-policy before next env step')
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_observation_hash')
 names=next(n.iter for n in ast.walk(fn) if isinstance(n,ast.For))
 need(ast.literal_eval(names)==KEYS,'frozen hash fixed five raw fields')
 timing={'source_sha256':PINS[str(R/'src/cti_vla/evaluation/libero_runtime.py')],'function_source':ast.get_source_segment(raw,fn),
 'predict_line':pred[0].lineno,'hash_line':hashes[0].lineno,'action_step_line':actionsteps[0].lineno,
 'old_nonzero_hash_sampling':'after predict_chunk returns, before next env.step',
 'old_pre_policy_values_at_step64_and72_recorded':False,
 'new_pre_post_identity_and_bytes_verified':True,
 'hash_covers':list(KEYS),'hash_includes_each':['name UTF8','dtype string','shape tuple string','C-order raw bytes'],
 'hash_does_not_cover':['instruction','simulator hidden state','controller internal state','global or environment RNG','wall-clock','renderer hidden state','preprocessed tensor','model activations']}
 old_outer=rows(rd(O/'outer/events.jsonl'));new_outer=rows(content[str(N/'outer/events.jsonl')])
 os=next(e for e in old_outer if e.get('event')=='engineering_start');ns=next(e for e in new_outer if e.get('event')=='engineering_start')
 need(os['original_invocation']==ns['original_invocation'],'same original invocation')
 env_old={k:v for k,v in os['environment'].items() if k!='SLURM_JOB_ID'};env_new={k:v for k,v in ns['environment'].items() if k!='SLURM_JOB_ID'}
 need(env_old==env_new,'same recorded environment except allocationID')
 op=next(e['proof'] for e in old_outer if e['event']=='prefix_observer_scope_enter')
 npf=next(e['proof'] for e in new_outer if e['event']=='prefix_observer_scope_enter')
 for k in ('active_run_code_sha256','original_trial_code_sha256','observer_trial_code_sha256'):
  need(op[k]==npf[k],'same recorded original code '+k)
 for k in ('frozen_original_ast_sha256','original_ast_sha256','accepted_action_amplitude_branch_sha256','accepted_action_branch_deletions'):
  need(op['run_episode'][k]==npf['run_episode'][k],'same accepted original loop '+k)
 need(op['run_episode']['original_calls']==npf['run_episode']['original_calls'],'same original calls hash timing in both')
 environment={'config_sha256':PINS[str(N/'original_run/config.json')],'recorded_environment_except_job_id':env_new,
 'runtime':json.loads(content[str(N/'original_run/config.json')])['runtime'],
 'same_node_name_and_gpu_model':True,'same_physical_GPU_proved':False,
 'observer_layouts_different':op['observer_run_code_sha256']!=npf['observer_run_code_sha256'],
 'old_scope_run_code':op['observer_run_code_sha256'],'new_scope_run_code':npf['observer_run_code_sha256'],
 'observer_passivity_does_not_prove_equal_wallclock_or_external_scheduling':True}
 # Finite, predeclared hashes only; no inference, rendering, environment, or trajectory generation.
 target=a['chunks'][9]['observation_sha256'];candidates=[]
 for q in (8,9,10):
  h=obs_hash(qs[q]['parts']);candidates.append({'kind':'whole_query','query_index':q,'step':8*q,'sha256':h,'matches_old_q9_post':h==target})
 for neighbour in (8,10):
  for key in KEYS:
   parts=dict(qs[9]['parts']);parts[key]=qs[neighbour]['parts'][key];h=obs_hash(parts)
   candidates.append({'kind':'single_component_substitution','base_query':9,'substituted_key':key,'from_query':neighbour,'sha256':h,'matches_old_q9_post':h==target})
 need(len(candidates)==13,'fixed3 whole plus10 single-component hypotheses')
 matches=[x for x in candidates if x['matches_old_q9_post']]
 # Verify only the five q9 blobs against the already fully audited archive; do not re-audit all10741.
 archive=json.loads(content[str(AR/'blob_archive_manifest.json')]);wanted={qs[9]['pre']['observation_arrays'][key]['blob']['path']:qs[9]['parts'][key]['bytes'] for key in KEYS}
 need(archive['blob_count']==10741 and archive['old200_adopted'] is False and archive['new_scientific_trials']==0,'inherited archive scope')
 picked=[];seen=set()
 for part in archive['parts']:
  names={m['path']:m for m in part['members']};wanted_here=set(wanted)&set(names)
  if not wanted_here:continue
  pb=rd(R/part['path'],part['sha256']);need(len(pb)==part['compressed_bytes'],'selected archive part size')
  with tarfile.open(fileobj=io.BytesIO(pb),mode='r:gz') as tf:
   for name in sorted(wanted_here):
    members=[m for m in tf.getmembers() if m.name==name];need(len(members)==1 and members[0].isfile() and not members[0].issym(),'unique regular archived selected member')
    data=tf.extractfile(members[0]).read();m=names[name]
    need(data==wanted[name] and digest(data)==m['sha256'] and len(data)==m['bytes'],'selected archive member equals true query bytes')
    seen.add(name);picked.append({'part':part['path'],'part_sha256':part['sha256'],'member':name,'sha256':digest(data),'bytes':len(data)})
 need(seen==set(wanted),'all5 critical raw components recovered from exact archived members')
 evidence={'integrity':True,'identity_same':True,'schema_same':True,'old_sampling':'post_policy','new_sampling':'pre_and_post_policy',
  'old_pre_available':False,'old_pre':None,'old_post':target,'new_pre':b['chunks'][9]['observation_sha256'],'new_post':b['chunks'][9]['observation_sha256'],'actions_before_same':True}
 decision=classify(evidence)
 tests=[]
 def test(name,x,expected=None,reject=False):
  try:y=classify(x)
  except ValueError as err:
   need(reject,'unexpected classifier rejection '+name);tests.append({'name':name,'expected_rejection':True,'passed':True,'reason':str(err)});return
  need(not reject and y['decision']==expected and y['scientific_release'] is False and y['old200_adopted'] is False and y['root_cause_identified'] is False,'classifier case '+name)
  tests.append({'name':name,'expected':expected,'passed':True,'result':y})
 test('real_missing_old_pre',dict(evidence),expected='post_observation_difference_origin_unresolved')
 for field in ('integrity','identity_same','schema_same'):
  x=dict(evidence);x[field]=False;test('reject_'+field,x,reject=True)
 for field,value in [('old_sampling','pre_policy'),('new_sampling','post_policy'),('new_post','MUTATED'),('old_pre_available',None),('old_pre','UNSUPPORTED')]:
  x=dict(evidence);x[field]=value;test('reject_'+field,x,reject=True)
 x=dict(evidence);x.update(old_pre_available=True);test('reject_claimed_old_pre_without_bytes',x,reject=True)
 x=dict(evidence);x['old_post']=x['new_post'];test('same_post_does_not_prove_old_pre',x,expected='no_logged_post_observation_difference')
 x=dict(evidence);x.update(old_pre_available=True,old_pre=target);test('synthetic_world_A_pre_existing_difference',x,expected='pre_policy_input_difference_observed')
 y=dict(evidence);y.update(old_pre_available=True,old_pre=y['new_pre']);test('synthetic_world_B_old_policy_interval_change',y,expected='old_observation_changed_within_policy_interval')
 need({k:x[k] for k in evidence if k not in ('old_pre_available','old_pre')}=={k:y[k] for k in evidence if k not in ('old_pre_available','old_pre')},'two distinct causes compatible with same actual recorded observation projection')
 x=dict(evidence);x['actions_before_same']=False;test('unequal_actions_does_not_imply_a_cause',x,expected='post_observation_difference_origin_unresolved')
 # Negative byte/hash tests operate on private in-memory values, never source bytes.
 base=qs[9]['parts'];mod=copy.deepcopy(base);raw=mod[KEYS[0]]['bytes'];mod[KEYS[0]]['bytes']=bytes([raw[0]^1])+raw[1:]
 need(obs_hash(mod)!=obs_hash(base),'in-memory image-bit corruption detected')
 mod=copy.deepcopy(base);mod[KEYS[2]]['dtype']='int64';need(obs_hash(mod)!=obs_hash(base),'dtype corruption detected')
 mod=copy.deepcopy(base);mod[KEYS[0]]['shape']=[256,768];need(obs_hash(mod)!=obs_hash(base),'shape corruption detected')
 need('torch' not in sys.modules and 'mujoco' not in sys.modules,'no model or simulator imported')
 boundary={'status':'passed_fixed_CPU_evidence_analysis_pending_independent_review','trial_id':IDENTITY,'ordinal':30,
 'job_ids':['3053440','3054127'],'same_identity_runtime_and_source_evidence':True,'changed_logged_trace_ordinals':changed,
 'first_different_post_policy_observation_query':9,'first_different_post_policy_observation_control_step':72,
 'last_equal_post_policy_observation_query':8,'last_equal_post_policy_observation_control_step':64,
 'logged_post_hash_interval':'after query8 policy return at step64 through after query9 policy return at step72',
 'first_different_environment_command_index':first_action,'equal_logged_commands_before_boundary':72,'commands64_through71_equal':True,
 'old_pre_query_equality_at64_or72_proved':False,'intermediate_simulator_and_rng_equality_proved':False,
 'initial_observation_sim_and_recorded_rng_equal':t0_sim,'classification':decision,
 'finite_candidate_count':len(candidates),'finite_candidate_matches':matches,
 'finite_candidate_interpretation':'Only these exact observed neighboring inputs/substitutions are tested; failure to match does not identify which old component differed or its cause.',
 'original200_HOLD':True,'new_Goal_science_HOLD':True,'scientific_trials_added':0,'new_GPU_jobs':0,'new_GPU_seconds':0,
 'cause_identified':False,'old_failure_repaired':False,'next_action':'independent CPU review of this fixed evidence package; no automatic engineering rerun'}
 missing=[
 {'evidence':'old3053440 query9/step72 five raw observation arrays immediately before and after predict_chunk','effect':'Cannot classify pre-existing input divergence versus old within-policy input change; cannot identify differing image/proprio component.'},
 {'evidence':'old3053440 intermediate simulator/hidden controller/RNG/renderer state at step64 and72 (and intra-eight-step trace)','effect':'Equal commands and t0 recorded state do not imply same intermediate dynamics; no causal localization to physics, rendering, scheduler, RNG, or controller.'},
 {'evidence':'old nonzero query instruction raw bytes/preprocessed tensors and contemporaneous per-component pre/post metadata','effect':'Raw five-array posthash does not cover all actual policy input/transforms; same source/config supports identity but not a captured all-input equality proof.'},
 {'evidence':'controlled causal contrast for recorder overhead versus unrecorded nondeterminism','effect':'Observer guards prove recorded values unchanged during capture only; different observation frequency perturbs time and is not causal proof.'}]
 propositions=[
 {'claim':'Different logged environment commands before step72 caused first divergence','decision':'excluded_as_logged_command_value_difference','scope':'Commands0..71 are equal; hidden controllers/physics responding differently remains unresolved.'},
 {'claim':'Frozen five-array hash schema or recorded source/config differed','decision':'excluded_within_verified_pins','scope':'Same config and active original loop identity, same five-field schema; not proof of every unlogged hardware state.'},
 {'claim':'New3054127 policy mutated observed inputs within the selected11 queries','decision':'excluded_for_recorded_inputs_in_new_attempt','scope':'Raw pre/post arrays and gate receipts match; not retrospective proof for3053440 or old200.'},
 {'claim':'Old step72 input was already different before inference','decision':'unresolved','missing_evidence':missing[0]['evidence']},
 {'claim':'Old inference modified input and created its posthash difference','decision':'unresolved','missing_evidence':missing[0]['evidence']},
 {'claim':'Image-only, proprio-only, simulator, RNG, controller, renderer, timing cause','decision':'unresolved','missing_evidence':missing[0]['evidence']+'; '+missing[1]['evidence']},
 {'claim':'Same terminal success repairs the discrepancy or permits old200','decision':'not_a_valid_admission_rule','scope':'No outcome is used to choose diagnosis identity, admit results, or release science.'}]
 out('source_timing_and_hash_contract.json',timing)
 out('recorded_environment_identity.json',environment)
 out('fixed_neighbor_hypothesis_tests.json',{'contract':contract,'target_old_posthash':target,'candidates':candidates,'matches':matches,'automatic_retry':False,'scientific_release':False})
 out('selected_archive_member_verification.json',{'inherited_archive_manifest_sha256':PINS[str(AR/'blob_archive_manifest.json')],'selected_query':9,'selected_member_count':len(picked),'members':picked,'whole_archive_reaudit':False})
 out('classifier_CPU_tests.json',{'kind':'synthetic logical classifier tests, not experiment evidence','tests':tests,'test_count':len(tests),'no_raw_sources_mutated':True,'scientific_release':False})
 out('missing_evidence_and_propositions.json',{'missing':missing,'propositions':propositions,'automatic_engineering_rerun_authorized':False})
 out('boundary_evidence.json',boundary)
 # Sources are sealed and rehashed after all CPU work; only D and transport journal were writable.
 for p,m in list(reads.items()):
  need(digest(Path(p).read_bytes())==m['sha256'],'source stable through CPU analysis '+p)
 out('source_inventory.json',{'files':reads,'file_count':len(reads),'selected_raw_blobs':blob_reads,'raw_blob_count':len(blob_reads),'no_weights_read':True,'no_final_sealed_data_read':True})
 out('execution_report.json',{'status':'passed_fixed_CPU_diagnostic_author_checks','blockers':[],'check_count':len(checks),'checks':checks,
 'CPU_wall_seconds':time.perf_counter()-start,'scientific_trials_added':0,'GPU_seconds_added':0,'new_GPU_jobs':0,
 'role':'author analysis, independent review pending','old200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False})
 print(json.dumps({'status':'passed_fixed_CPU_diagnostic_author_checks','check_count':len(checks),'raw_blob_count':len(blob_reads),'candidate_matches':len(matches),'report':str(D/'execution_report.json'),'classification':decision},ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException:
  failure={'status':'failed_CPU_diagnostic','traceback':traceback.format_exc(),'checks':checks,'scientific_trials_added':0,'new_GPU_jobs':0,'no_auto_retry':True}
  p=D/'execution_failure_attempt01.json'
  if not p.exists():p.write_bytes(json.dumps(failure,ensure_ascii=False,indent=2).encode()+b'\n')
  raise
