from pathlib import Path
import collections,hashlib,json,math,re,sys,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=Path(__file__).parent;OUT='results/formal_main_v2/engineering/goal_full200_20261021T0110/attempt01';ROOT=P/OUT;RAW=R/'results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01';PKG=P/'scripts/ops/formal_goal_full200_gate_v1'
N=0;refs={};metadata={}
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(p.read_bytes())
def yes(v,msg):
 global N
 N+=1
 if not v:raise AssertionError(msg)
def strict(b):
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:raise AssertionError('duplicate JSON key')
   out[k]=v
  return out
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(AssertionError('invalid numeric literal')))
def read(p):
 b=p.read_bytes();metadata[str(p)]=dict(sha256=sha(b),bytes=len(b));return strict(b)
def lines(p):
 b=p.read_bytes();yes(b.endswith(b'\n'),'JSONL complete tail '+str(p));metadata[str(p)]=dict(sha256=sha(b),bytes=len(b));return [strict(x) for x in b.splitlines()]
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def blob(v,obs):
 p=Path(v['path']) if obs else ROOT/'observer'/v['path']
 yes(p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'raw canonical non-symlink path')
 if obs:yes(v['storage']=='root_approved_raw_observations' and p.parent==RAW and p.name==v['sha256']+'.bin','fixed5 raw root only')
 else:yes(v['storage']=='attempt_local' and p.parent==ROOT/'observer/blobs' and re.fullmatch(v['sha256']+r'(?:\.bin|\.rng\.json)',p.name),'local passive typed reference')
 b=p.read_bytes();yes(len(b)==v['bytes'] and sha(b)==v['sha256'],'actual raw bytes/hash')
 ref=dict(sha256=v['sha256'],bytes=v['bytes'],kind='five_component_observation' if obs else 'passive_sim_or_RNG')
 yes(str(p) not in refs or refs[str(p)]==ref,'deduplicated reference identity stable')
 refs[str(p)]=ref;return b
def main():
 yes(h(PKG/'consumer.py')=='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b','canonical consumer pin')
 yes(h(PKG/'package_manifest.json')=='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec','package pin')
 package=read(PKG/'package_manifest.json')
 for name,pin in package['files'].items():yes(h(P/name)==h(R/name)==pin,'all actual runtime source pins '+name)
 spec=read(PKG/'specification.json');yes(h(PKG/'specification.json')=='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad','original fixed200 specification')
 completion=read(ROOT/'outer/completion.json');outer=lines(ROOT/'outer/events.jsonl');ledger=lines(ROOT/'original_run/trials.jsonl');events=lines(ROOT/'observer/events.jsonl');gate=lines(ROOT/'observer/gate.jsonl')
 yes(completion['status']=='returned_200_prospective_pending_terminal_review' and completion['job_id']=='3054717' and completion['exit_code']==0 and completion['errors']==[] and not completion['observer_failed'] and completion['original_runtime_restored'],'genuine clean outer')
 yes(completion['raw_event_sha256']==h(ROOT/'outer/events.jsonl') and completion['wall_seconds']<=2206,'outer byte chain and allocation wall bound')
 keys=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')
 results=[x for x in ledger if x['event']=='result'];starts=[x for x in ledger if x['event']=='start'];inv=[x for x in ledger if x['event']=='invocation']
 yes(len(results)==len(starts)==len(spec['rows'])==200 and len(inv)==1 and inv[0]['slurm_job_id']=='3054717','one actual invocation and200start/result')
 yes([x['event'] for x in ledger]==['invocation']+['start','result']*200,'full original ledger order')
 yes([{k:x[k] for k in keys} for x in results]==[{k:x[k] for k in keys} for x in spec['rows']],'200original fixed order and identities')
 yes(len({x['state_trial_id'] for x in results})==100 and set(x['method'] for x in results)=={'A256_seed17','B256_seed17'},'100unique states and originalA/B only')
 for a,b in zip(starts,results):
  yes(all(a[k]==b[k] for k in keys) and b['status']=='completed' and type(b['success']) is bool and b['environment_seed']==0 and b['runtime_seed']==17 and b['split']=='development','original matching start/result/seed')
  yes(b['configured_wait_steps']==b['wait_steps']==10 and b['action_chunk']==8 and 1<=b['control_steps']<=300 and b['policy_calls']==math.ceil(b['control_steps']/8),'step/query/warmup bounds')
  yes(len(b['chunks'])==b['policy_calls'] and len(b['executed_actions'])==b['control_steps'],'full real chunk/action cardinalities')
 qtotal=sum(x['policy_calls'] for x in results);stotal=sum(x['control_steps'] for x in results)
 yes(qtotal==3027<=7600 and stotal==23508<=60000 and sum(x['wait_steps'] for x in results)==2000,'full control/query counts within fixed scope')
 schema={'agentview_image':('uint8',[256,256,3],196608),'robot0_eye_in_hand_image':('uint8',[256,256,3],196608),'robot0_eef_pos':('float64',[3],24),'robot0_eef_quat':('float64',[4],32),'robot0_gripper_qpos':('float64',[2],16)}
 obskeys=tuple(schema);captures=[x for x in events if 'phase' in x];byindex={};sig={}
 yes(len(captures)<=21032,'capture hard bound')
 for i,c in enumerate(captures,1):
  yes(c['event_index']==i and c['scientific_trials_added']==0,'sequential real capture')
  arrays=c['observation_arrays'];signatures={}
  if arrays:
   yes(set(arrays)==set(schema),'every observed capture allfive raw arrays')
   agg=hashlib.sha256()
   for key in obskeys:
    a=arrays[key];yes((a['dtype'],a['shape'],a['bytes'])==schema[key],'real five-array dtype shape size')
    b=blob(a['blob'],True);yes(sha(b)==a['sha256'] and len(b)==a['bytes'],'component metadata bound')
    x=np.frombuffer(b,dtype=np.dtype(a['dtype'])).reshape(a['shape']);yes(np.isfinite(x).all(),'raw array finite')
    agg.update(key.encode());agg.update(a['dtype'].encode());agg.update(str(tuple(a['shape'])).encode());agg.update(b)
    signatures[key]={k:a[k] for k in ['dtype','shape','bytes','sha256']}
   yes(agg.hexdigest()==c['observation_sha256'],'allfive raw aggregate exact')
   sig[i]=signatures
  else:yes(c.get('observation_missing')=='no returned observation exists at this marker' and 'observation_sha256' not in c,'no fake empty observation signature')
  yes(c['invariants']=={'global_rng_unchanged':True,'object_identity_and_bytes_unchanged':True,'passive_sim_and_environment_rng_unchanged':True},'passive runtime witness')
  yes(sum(v['bytes'] for v in c['sim_array_blobs'].values())<=8192,'passive simulator capacity')
  for v in c['sim_array_blobs'].values():blob(v,False)
  rb=blob(c['global_rng'],False);yes(len(rb)<=65536 and isinstance(strict(rb),dict),'full serialized RNG bytes valid')
  byindex[i]=c
 yes(not any(e.get('event')=='observer_abort' for e in events),'no discarded observer abort')
 loader=['existing_loader_event:'+x for x in ('asset_metadata_compat_load_start','asset_metadata_compat_load_complete','deployment_base_load_start','goal_component_load_start','goal_component_load_complete','goal_component_load_start','goal_component_load_complete','deployment_base_load_complete')]
 expected=[(x,None,None,None,None) for x in loader]
 for ordinal,row in enumerate(results,1):
  identity={k:row[k] for k in keys}
  for phase in ['trial_begin_before_reseed','reseed_after','factory_before','factory_after','reset_before','reset_after','set_init_before','set_init_after']:expected.append((phase,identity,ordinal,None,None))
  for t in range(10):expected.extend([('wait_before',identity,ordinal,None,t),('wait_after',identity,ordinal,None,t+1)])
  for qi in range(row['policy_calls']):expected.extend([('t0_query_before' if qi==0 else 'query_before',identity,ordinal,qi*8,None),('t0_query_after' if qi==0 else 'query_after',identity,ordinal,qi*8,None)])
 expected.append(('original_runner_returned',None,None,None,None))
 yes([(c['phase'],c['trial_identity'],c['ordinal'],c['control_step'],c['wait_steps']) for c in captures]==expected,'exact complete native loader/trial/wholequery capture topology')
 ends=[e for e in events if e.get('event')=='trial_end'];yes(len(ends)==200 and [e['trial_identity']['trial_id'] for e in ends]==[r['trial_id'] for r in results],'all200end witnesses in originalorder')
 yes(gate[0]['event']=='paired_input_gate_open' and gate[0]['CPU_fixture_enabled'] is False and gate[0]['prefix_sha256']==h(PKG/'specification.json') and gate[-1]['event']=='paired_input_gate_finished','real immutable gate lifecycle noCPUfixture')
 yes(not any(e['event']=='paired_input_gate_abort' for e in gate),'no gate abort')
 expected_gate=[]
 for ordinal,row in enumerate(results,1):
  expected_gate.append(('t0_pair_gate',ordinal,None,row['trial_id']))
  for t in range(row['control_steps']):
   if t%8==0:expected_gate.append(('query_integrity_passed',ordinal,t,row['trial_id']))
   expected_gate.append(('policy_step_executed',ordinal,t,row['trial_id']))
 yes([(e['event'],e['ordinal'],e.get('control_step'),e['trial_identity']['trial_id']) for e in gate[1:-1]]==expected_gate,'complete pair/query/action gate order')
 bytrial={r['trial_id']:r for r in results};t0={};paired={};counts=collections.Counter();checkpoint_sets=collections.defaultdict(set);queryproof=[]
 for e in gate[1:-1]:
  tid=e['trial_identity']['trial_id'];row=bytrial[tid];yes(e['trial_identity']=={k:row[k] for k in keys} and e['scientific_trials_added']==0,'gate whole identity exact')
  if e['event']=='t0_pair_gate':
   cap=byindex[e['capture_event_index']];yes(cap['phase']=='t0_query_before' and cap['trial_identity']==e['trial_identity'],'pre-first-policy actual capture')
   b=bytes.fromhex(e['instruction_utf8_hex']);b.decode('utf8');content=dict(components=sig[cap['event_index']],instruction_utf8_sha256=sha(b));yes(content==e['content'],'t0 content from raw five arrays and instruction')
   t0[tid]=content;state=row['state_trial_id']
   if row['method']=='A256_seed17':yes(state not in paired and e['pairing']=='baseline_recorded_before_first_policy','uniqueA baseline');paired[state]=content
   else:yes(e['pairing']=='exact_before_policy_pair_passed' and paired[state]==content,'allfive same-state beforeB exact')
  elif e['event']=='query_integrity_passed':
   after=byindex[e['capture_event_index']];before=byindex[e['capture_event_index']-1];qi=counts[(tid,'query')]
   yes(before['trial_identity']==after['trial_identity']==e['trial_identity'] and before['control_step']==after['control_step']==qi*8,'query ordered actual beforeafter')
   yes(set(before['observation_arrays'])==set(after['observation_arrays'])==set(schema) and before['observation_arrays']==after['observation_arrays'],'allquery five complete beforeafter raw identity')
   rawinst=bytes.fromhex(e['instruction_utf8_hex']);rawinst.decode('utf8');content=dict(components=sig[before['event_index']],instruction_utf8_sha256=sha(rawinst))
   yes(content==e['content'] and sig[before['event_index']]==sig[after['event_index']] and content['instruction_utf8_sha256']==t0[tid]['instruction_utf8_sha256'],'allquery complete raw content unchanged')
   yes(e['input_identity_before']==e['input_identity_after'],'policy input mapping/array pointers unchanged')
   ch=row['chunks'][qi];yes(ch['observation_sha256']==after['observation_sha256'],'original ledger postpolicy observation binding')
   for name in ['normalized_actions','environment_actions']:
    a=e['returned_actions'][name];b=bytes.fromhex(a['bytes_hex']);yes(sha(b)==a['sha256'] and len(b)==a['bytes'],'returned action real bytes')
    arr=np.frombuffer(b,dtype=np.dtype(a['dtype'])).reshape(a['shape']);yes(arr.shape==(8,7) and np.isfinite(arr).all() and np.array_equal(arr,np.array(ch[name])),'entire raw returned actionchunk equals original ledger')
   meta=ch['metadata'];yes(meta['future_head_calls']==0 and meta['language_cache']=='disabled' and meta['scorer_calls']==meta['packing_calls']==meta['policy_calls']==meta['vision_calls']==1 and meta['visual_tokens']==256 and meta['per_camera_budgets']==[128,128] and meta['training_seed']==17,'single deployment path andfixedtoken nofuture')
   yes(len(set(meta['retained_indices']))==256 and all(0<=x<512 for x in meta['retained_indices']) and sum(x<256 for x in meta['retained_indices'])==128,'samevisual packing legal indices')
   checkpoint_sets[row['method']].add(meta['selector_checkpoint_sha256'])
   counts[(tid,'query')]+=1;queryproof.append(dict(trial_id=tid,query=qi,before=before['event_index'],after=after['event_index'],observation_sha256=after['observation_sha256']))
  else:
   si=counts[(tid,'step')];a=e['action'];b=bytes.fromhex(a['bytes_hex']);yes(e['control_step']==si and sha(b)==a['sha256'] and len(b)==a['bytes'],'every executed command rawstep ordered')
   arr=np.frombuffer(b,dtype=np.dtype(a['dtype'])).reshape(a['shape']);yes(arr.shape==(7,) and np.isfinite(arr).all() and np.array_equal(arr,np.array(row['executed_actions'][si])),'every executed command equals original ledger')
   chunk=row['chunks'][si//8]['environment_actions'][si%8];yes(np.array_equal(arr,np.array(chunk)),'each env command from its unchanged returned chunk')
   counts[(tid,'step')]+=1
 for row in results:yes(counts[(row['trial_id'],'query')]==row['policy_calls'] and counts[(row['trial_id'],'step')]==row['control_steps'],'allrecorded queries/actions consumed once')
 yes(len(paired)==100 and len(t0)==200 and len(queryproof)==3027,'full100pairs200trials3027queries')
 yes(gate[-1]['event_sha256']==h(ROOT/'observer/events.jsonl') and gate[-1]['all_query_checks']==qtotal and gate[-1]['executed_policy_steps_recorded']==stotal and gate[-1]['exact_paired_t0_checks']==100,'whole-event footer and counts actualbytes')
 for where,kind,extras in [(RAW,'five_component_observation',{'claim.json'}),(ROOT/'observer/blobs','passive_sim_or_RNG',set())]:
  wanted={Path(n).name for n,v in refs.items() if v['kind']==kind};actual={p.name for p in where.iterdir() if p.is_file()}
  yes(actual==wanted|extras,'exact blob directory coverage no unreferenced/omitted payload '+kind)
  yes(not any(p.is_symlink() for p in where.iterdir()),'blob entries notsymlink '+kind)
 claim=read(RAW/'claim.json');yes(claim==completion['raw_observation_claim'] and claim['job_id']=='3054717','exclusive realcompute raw claim')
 for n,v in metadata.items():yes(h(Path(n))==v['sha256'],'raw original metadata remains unchanged')
 summaries={}
 for method in ['A256_seed17','B256_seed17']:
  rr=[x for x in results if x['method']==method];summaries[method]=dict(completed=len(rr),success=sum(x['success'] for x in rr),control_steps=sum(x['control_steps'] for x in rr),policy_calls=sum(x['policy_calls'] for x in rr),checkpoint_sha256=sorted(checkpoint_sets[method]))
 summary=dict(status='passed_independent_raw_reconstruction_pending_original_full_consumer',checks=N,job_id='3054717',trials=200,unique_states=100,paired_before_B=100,queries=qtotal,control_steps=stotal,wait_steps=2000,capture_count=len(captures),observer_event_count=len(events),gate_event_count=len(gate),methods=summaries,blob_count=len(refs),blob_bytes=sum(v['bytes'] for v in refs.values()),blob_counts_by_kind=dict(collections.Counter(v['kind'] for v in refs.values())),metadata=metadata,scientific_trials_admitted=0,old200_HOLD=True,other1000_HOLD=True,old_cause_identified=False,final_release=False,no_Slurm_calls=True,CPU_fixtures=False)
 write('raw_blob_allowlist.json',dict(files=[dict(path=k,**v) for k,v in sorted(refs.items())],file_count=len(refs)))
 write('raw_query_coverage.json',dict(queries=queryproof,query_count=len(queryproof)))
 write('raw_reconstruction.json',summary)
 print(json.dumps({k:summary[k] for k in ['status','checks','trials','queries','control_steps','blob_count','blob_bytes','methods']}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('raw_reconstruction_failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks_completed=N,scientific_trials_admitted=0,Slurm_calls=0));raise
