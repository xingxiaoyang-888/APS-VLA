from pathlib import Path
import ast,copy,hashlib,importlib.util,json,types,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');A=R/'.local/goal_full200_author_20261021T0110';D=Path(__file__).parent;K=D/'package';O=D/'counterexample_v1';O.mkdir(exist_ok=False)
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
c=load(K/'consumer.py','goal_ind_counterconsumer');src=A/'CPU_full200_v2';fixture=O/'fixture_attempt';fixture.mkdir();shutil.copytree(src/'gated',fixture/'observer')
rawrows=c.jsonl(src/'gated.jsonl');spec=json.loads((K/'specification.json').read_bytes());tree=ast.parse((K/'consumer.py').read_text());orig=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate');node=copy.deepcopy(orig);changes=[]
for n in ast.walk(node):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='CPU fixture forbidden':
  changes.append('Explicit CPU label only');n.args[0]=ast.parse("gate[0]['CPU_fixture_enabled'] is True and gate[0]['runtime_context']=='synthetic_CPU_fixture'",mode='eval').body
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected_schema':
  changes.append('Explicit small CPU image shape only');new=ast.literal_eval(n.value);new['agentview_image']=('uint8',[3,4,3],36);new['robot0_eye_in_hand_image']=('uint8',[3,4,3],36);n.value=ast.parse(repr(new),mode='eval').body
assert len(changes)==2
ast.fix_missing_locations(node);ns={**c.__dict__,'OUT':fixture.relative_to(R).as_posix(),'RAW':src/'gated/CPU_raw_observations'}
readblob=types.FunctionType(c.read_blob.__code__,ns,c.read_blob.__name__,c.read_blob.__defaults__,c.read_blob.__closure__);readblob.__kwdefaults__=c.read_blob.__kwdefaults__;cache={}
def cached(ref,*,observation,output_root,read_refs):
 key=(json.dumps(ref,sort_keys=True),observation,str(output_root))
 if key not in cache:
  refs={};raw=readblob(ref,observation=observation,output_root=output_root,read_refs=refs);cache[key]=(raw,refs)
 raw,refs=cache[key];read_refs.update(refs);return raw
ns['read_blob']=cached
exec(compile(ast.Module(body=[node],type_ignores=[]),'<independent exact2 CPU guards>','exec'),ns)
f=ns['reconstruct_gate'];baseline=f(R,rawrows,specification=spec,job_id='CPU_FIXTURE');events=c.jsonl(fixture/'observer/events.jsonl');gates=c.jsonl(fixture/'observer/gate.jsonl')
q=next(x for x in gates if x['event']=='query_integrity_passed' and x['control_step']==8);idx=q['capture_event_index'];modified=copy.deepcopy(events);changed=[]
for e in modified:
 if e.get('event_index') in (idx-1,idx) and 'phase' in e:
  changed.append({'event_index':e['event_index'],'phase':e['phase'],'original_array_count':len(e['observation_arrays'])});e['observation_arrays']={}
assert len(changed)==2
previous=ns['jsonl']
ns['jsonl']=lambda p:copy.deepcopy(modified) if Path(p)==fixture/'observer/events.jsonl' else previous(p)
result=f(R,rawrows,specification=spec,job_id='CPU_FIXTURE')
assert result['trials']==200 and result['queries']==baseline['queries']==600
proof={'status':'confirmed_raw_integrity_blocker','consumer_sha256':hashlib.sha256((K/'consumer.py').read_bytes()).hexdigest(),'author_manifest_sha256':hashlib.sha256((A/'delivery_manifest.json').read_bytes()).hexdigest(),'CPU_guard_derivation':changes,'changed_capture_events':changed,'operation':'Erase all5 component metadata+blob references at first non-t0 before/after; keep all other original ledger/gate/events unchanged','unmodified_fixture_passed':True,'corrupted_fixture_incorrectly_accepted':True,'returned_trials':result['trials'],'returned_queries':result['queries'],'new_GPU_jobs':[],'production_admitted':False,'required_fix':'Require all5 exact arrays for every observation-bearing phase; independently reconstruct each query content from its raw pre/post captures; validate whole pertrial capture sequence.'}
with (O/'blocker.json').open('x') as f:json.dump(proof,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'path':str((O/'blocker.json').relative_to(R)),'sha256':hashlib.sha256((O/'blocker.json').read_bytes()).hexdigest(),'status':proof['status']}))
