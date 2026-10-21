from pathlib import Path
import ast,hashlib,json,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_full200_author_20261021T0110';K=D/'package'
H=lambda b:hashlib.sha256(b).hexdigest()
def sub(t,a,b):
 assert t.count(a)==1,(a,t.count(a));return t.replace(a,b,1)
def put(n,t):ast.parse(t);(K/n).write_text(t)
hist=D/'before_typed_parent_and_storage_receipt';hist.mkdir()
for n in ['entry.py','paired_input_gate_v1.py','consumer.py','storage.py']:shutil.copyfile(K/n,hist/n)
ref={'path':'results/formal_main_v2/preflight/heartbeat_20261021T0910/Goal_blob_storage_root_decision.json','sha256':'7542920320810275798d8fa7ebf2cd85d7b8b4f60ead315638a261b6ecef44de'}
b=(R/ref['path']).read_bytes();assert H(b)==ref['sha256'];(D/'root_storage_decision_copy.json').write_bytes(b)
entry=(K/'entry.py').read_text()
entry=sub(entry,"STORAGE_SHA='61ffc7702ca9ce2c9f12419017416b3bf8fea852049844310d5b10f4a9c7ea37'","STORAGE_SHA='61ffc7702ca9ce2c9f12419017416b3bf8fea852049844310d5b10f4a9c7ea37'\nSTORAGE_DECISION="+repr(ref))
entry=entry.replace("'raw_observation_root':str(RAW),'root_fixed_design'","'raw_observation_root':str(RAW),'root_storage_decision':STORAGE_DECISION,'root_fixed_design'")
entry=sub(entry," storage=load(P/PKG/'storage.py','goal200_storage',STORAGE_SHA);"," read(R/STORAGE_DECISION['path'],STORAGE_DECISION['sha256'])\n storage=load(P/PKG/'storage.py','goal200_storage',STORAGE_SHA);")
entry=sub(entry," validate_config(read(CONFIG));decision="," validate_config(read(CONFIG));read(R/STORAGE_DECISION['path'],STORAGE_DECISION['sha256']);decision=")
entry=sub(entry," require(all(os.environ.get(k)==v for k,v in THREADS.items()),"," read(R/STORAGE_DECISION['path'],STORAGE_DECISION['sha256']);read(R/ROOT_DECISION_REL,ROOT_DECISION_SHA)\n require(all(os.environ.get(k)==v for k,v in THREADS.items()),")
entry=sub(entry,"  with (outer/'completion.json').open('x',encoding='utf-8') as f:json.dump(complete,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\\n')","  with (outer/'completion.json').open('x',encoding='utf-8') as f:json.dump(complete,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\\n')\n  receipts=[]\n  for artifact in archived_adapter:\n   if artifact['path'].endswith('.json'):\n    item=read(Path(artifact['path']));receipts.append({'path':artifact['path'],'status':item['status'],'runner_status':item.get('runner_status')})\n  parent=dict(schema='formal_main_v2',kind='goal_full200_typed_parent_receipt',execution_version=VERSION,job_id=job,wrapper_sha256=sha(ENTRY),stage_completed_claimed=False,status='returned' if code==0 else 'failed',exit_code=code,wall_seconds=complete['wall_seconds'],source_completion_sha256=sha(outer/'completion.json'),adapter_artifacts=archived_adapter,adapter_receipts=receipts,scientific_trials_added=0,original_goal200_HOLD=True,final_release=False)\n  with (outer/'typed_parent.json').open('x',encoding='utf8') as f:json.dump(parent,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\\n')")
put('entry.py',entry)
cfg=json.loads((K/'config.json').read_text());cfg['root_storage_decision']=ref;(K/'config.json').write_text(json.dumps(cfg,sort_keys=True,indent=2)+'\n')
gate=(K/'paired_input_gate_v1.py').read_text()
gate=sub(gate,'def content_signature(event,instruction):',"def identity_signature(observation):\n return {'mapping_id':id(observation),'components':{k:{'id':id(observation[k]),'pointer':observation[k].__array_interface__['data'][0]} for k in recorder.OBS_KEYS}}\n\ndef content_signature(event,instruction):")
gate=sub(gate,"'content':content,'capture_event_index':event['event_index'],'scientific_trials_added':0}","'content':content,'instruction_utf8_hex':instruction.encode().hex(),'capture_event_index':event['event_index'],'scientific_trials_added':0}")
gate=sub(gate,"'object_guard':obj_guard,'instruction':instruction}","'object_guard':obj_guard,'identity_signature':identity_signature(observation),'instruction':instruction}")
gate=sub(gate,"'control_step':control_step,'content':content,'returned_actions':outputs","'control_step':control_step,'content':content,'instruction_utf8_hex':instruction.encode().hex(),'input_identity_before':pending['identity_signature'],'input_identity_after':identity_signature(observation),'returned_actions':outputs")
put('paired_input_gate_v1.py',gate)
consumer=(K/'consumer.py').read_text()
consumer=sub(consumer,"  require(sig==e['content'],'pair content rebuilt from raw bytes')","  require(sig==e['content'] and digest(bytes.fromhex(e['instruction_utf8_hex']))==sig['instruction_utf8_sha256'],'pair content and instruction rebuilt from raw bytes')")
consumer=sub(consumer,"  c=row['chunks'][qi];","  require(e['input_identity_before']==e['input_identity_after'] and digest(bytes.fromhex(e['instruction_utf8_hex']))==e['content']['instruction_utf8_sha256'],'prepost instruction and mapping/array pointer identities')\n  c=row['chunks'][qi];")
consumer=sub(consumer," require(complete['raw_event_sha256']==files[OUT+'/outer/events.jsonl']"," rawclaim=strict((RAW/'claim.json').read_bytes());require(rawclaim==complete['raw_observation_claim'] and rawclaim['job_id']==job['job_id'] and rawclaim['path']==str(RAW),'exact exclusive actual-node raw claim')\n require(complete['raw_event_sha256']==files[OUT+'/outer/events.jsonl']")
put('consumer.py',consumer)
sources={str(p.relative_to(K)):H(p.read_bytes()) for p in K.iterdir()}
manifest={'schema':'formal_main_v2','version':'goal-full200-prospective-single-attempt-v1','files':{'scripts/ops/formal_goal_full200_gate_v1/'+n:h for n,h in sources.items()}}
(K/'package_manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps({'files':sources,'package_manifest':H((K/'package_manifest.json').read_bytes())}))
