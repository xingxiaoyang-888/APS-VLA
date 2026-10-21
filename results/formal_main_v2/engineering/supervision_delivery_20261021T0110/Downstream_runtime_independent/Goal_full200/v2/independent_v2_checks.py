from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile,types,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_full200_author_20261021T0110_v2';OLD=R/'.local/goal_full200_author_20261021T0110'
O=Path(__file__).parent;CHECKS=[];REJECTS=[]
def sh(b):return hashlib.sha256(b).hexdigest()
def ck(n,v,d=None):
 CHECKS.append(dict(name=n,passed=bool(v),detail=d))
 if not v:raise AssertionError(n)
def write(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 mbytes=(D/'delivery_manifest.json').read_bytes();ck('manifest_pin',sh(mbytes)=='e55ba41e0ea407821035784ce1659cfeac07c5ac732334195f943440ed831613')
 m=json.loads(mbytes);ck('exact24_unique_files',m['file_count']==len(m['files'])==len({x['path'] for x in m['files']})==24)
 for x in m['files']:
  p=D/x['path'];b=p.read_bytes();ck('file/'+x['path'],not p.is_symlink() and len(b)==x['bytes'] and sh(b)==x['sha256'])
 count=0
 for bundle in m['archives']:
  members=json.loads((D/bundle['members']['path']).read_bytes())['files'];wanted={x['path']:x for x in members}
  with tarfile.open(D/bundle['archive']['path'],'r:gz') as t:
   entries=t.getmembers();ck('exact archive membership',len(entries)==len(wanted)==len(members)==bundle['file_count'] and all(x.isfile() for x in entries) and set(wanted)=={x.name for x in entries})
   for member in entries:
    b=t.extractfile(member).read();x=wanted[member.name];ck('tar/'+member.name,len(b)==x['bytes'] and sh(b)==x['sha256']);count+=1
 pm=json.loads((D/'package/package_manifest.json').read_bytes());oldpm=json.loads((OLD/'package/package_manifest.json').read_bytes())
 ck('10 production sources',len(pm['files'])==10)
 changed=[]
 for p,h in pm['files'].items():
  a=(D/'package'/Path(p).name).read_bytes();b=(OLD/'package'/Path(p).name).read_bytes()
  ck('production_bytes/'+p,sh(a)==h)
  if a!=b:changed.append(Path(p).name)
 ck('only consumer changed',changed==['consumer.py'])
 newtree=ast.parse((D/'package/consumer.py').read_text());oldtree=ast.parse((OLD/'package/consumer.py').read_text())
 def outer(tree):return ast.dump(ast.Module(body=[x for x in tree.body if not isinstance(x,ast.FunctionDef) or x.name!='reconstruct_gate'],type_ignores=[]),include_attributes=False)
 ck('all other consumer AST unchanged',outer(newtree)==outer(oldtree))
 ck('config identity fixed',sh((D/'package/config.json').read_bytes())=='29bb0fb84ff2dab826a53d5d8170d7ad0347f193f72ddfedc310f05e2a3d3bae')
 ck('fixed 200 specification unchanged',sh((D/'package/specification.json').read_bytes())=='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad')
 ck('original defect evidence exact',(D/'independent_v1_blocker.json').read_bytes()==(O.parent/'counterexample_v1/blocker.json').read_bytes())
 c=load(D/'package/consumer.py','ind_goal_consumer_v2')
 F=O/'independent_fixture';F.mkdir(exist_ok=False)
 source=O.parent/'CPU_full200_v3'
 shutil.copytree(source/'gated',F/'observer')
 rows=c.jsonl(source/'gated.jsonl');events=c.jsonl(F/'observer/events.jsonl');gate=c.jsonl(F/'observer/gate.jsonl')
 spec=json.loads((D/'package/specification.json').read_bytes())
 node=copy.deepcopy(next(x for x in newtree.body if isinstance(x,ast.FunctionDef) and x.name=='reconstruct_gate'));changes=[]
 for n in ast.walk(node):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='CPU fixture forbidden':
   n.args[0]=ast.parse("gate[0]['CPU_fixture_enabled'] is True and gate[0]['runtime_context']=='synthetic_CPU_fixture'",mode='eval').body;changes.append('only runtime CPU label assertion')
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected_schema':
   v=ast.literal_eval(n.value);v['agentview_image']=('uint8',[3,4,3],36);v['robot0_eye_in_hand_image']=('uint8',[3,4,3],36);n.value=ast.parse(repr(v),mode='eval').body;changes.append('only two image dimensions')
 ck('exact two fixture derivations',len(changes)==2,changes);ast.fix_missing_locations(node)
 ns=dict(c.__dict__,OUT=F.relative_to(R).as_posix(),RAW=source/'gated/CPU_raw_observations')
 rb=types.FunctionType(c.read_blob.__code__,ns,'read_blob',c.read_blob.__defaults__,c.read_blob.__closure__);rb.__kwdefaults__=c.read_blob.__kwdefaults__;cache={}
 def cached(ref,*,observation,output_root,read_refs):
  key=(json.dumps(ref,sort_keys=True),observation,str(output_root))
  if key not in cache:
   refs={};val=rb(ref,observation=observation,output_root=output_root,read_refs=refs);cache[key]=(val,refs)
  val,refs=cache[key];read_refs.update(refs);return val
 ns['read_blob']=cached
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<independent explicit two-predicate CPU fixture>','exec'),ns)
 # Exact loader structure is retained in the tested function; these eight marker
 # records are labelled synthetic, built from existing synthetic RNG, not GPU evidence.
 phases=['asset_metadata_compat_load_start','asset_metadata_compat_load_complete','deployment_base_load_start','goal_component_load_start','goal_component_load_complete','goal_component_load_start','goal_component_load_complete','deployment_base_load_complete']
 loaders=[]
 for p in phases:
  e=copy.deepcopy(events[0]);e.update(phase='existing_loader_event:'+p,ordinal=None,trial_identity=None,control_step=None,wait_steps=None);loaders.append(e)
 events=loaders+events;index=0
 for i,e in enumerate(events):
  if 'phase' in e:index+=1;events[i]={**e,'event_index':index}
 gate=[{**g,'capture_event_index':g['capture_event_index']+8} if 'capture_event_index' in g else g for g in gate]
 gate[-1]={**gate[-1],'observer_events':index,'event_sha256':sh(b''.join(c.canonical(e)+b'\n' for e in events))}
 current={'events':events,'gate':gate}
 original_jsonl=ns['jsonl']
 def virtual(p):
  if Path(p)==F/'observer/events.jsonl':return current['events']
  if Path(p)==F/'observer/gate.jsonl':return current['gate']
  return original_jsonl(p)
 ns['jsonl']=virtual
 def call(es=events,gs=gate,rs=rows):
  current.update(events=es,gate=gs);return ns['reconstruct_gate'](R,rs,specification=spec,job_id='CPU_INDEPENDENT')
 proof=call();ck('independent positive full200 raw reconstruction',all(proof[k]==v for k,v in dict(trials=200,paired_t0_checks=100,queries=600,control_steps=3400,warmup_steps=2000,complete_trial_end_witnesses=200).items()))
 def reject(name,es=events,gs=gate,rs=rows,fragment=None):
  try:call(es,gs,rs)
  except (ValueError,KeyError,IndexError,AssertionError) as e:
   ck(name,fragment is None or fragment in str(e),dict(error_type=type(e).__name__,error=str(e)));REJECTS.append(name)
  else:ck(name,False,dict(unexpected_acceptance=True))
 def edit_event(phase,fn):
  es=list(events);i=next(i for i,e in enumerate(es) if e.get('phase')==phase);es[i]=copy.deepcopy(es[i]);fn(es[i]);return es
 def edit_gate(kind,fn):
  gs=list(gate);i=next(i for i,g in enumerate(gs) if g.get('event')==kind and g.get('control_step')==8);gs[i]=copy.deepcopy(gs[i]);fn(gs[i]);return gs
 es=list(events);targets=[]
 for phase in ('query_before','query_after'):
  i=next(i for i,e in enumerate(es) if e.get('phase')==phase and e.get('control_step')==8);es[i]=copy.deepcopy(es[i]);es[i]['observation_arrays']={};targets.append(i)
 reject('original v1 exact simultaneous empty-array counterexample',es=es,fragment='required observation phase')
 for phase in ('reset_after','set_init_before','set_init_after','wait_before','wait_after','t0_query_before','t0_query_after','query_before','query_after'):
  reject('absent proprio '+phase,es=edit_event(phase,lambda e:e['observation_arrays'].pop('robot0_eef_quat')),fragment='required observation phase')
 reject('no fake query content mapping',gs=edit_gate('query_integrity_passed',lambda g:g.update(content={})),fragment='every query content rebuilt')
 reject('no stale observation SHA',es=edit_event('query_after',lambda e:e.update(observation_sha256='f'*64)),fragment='aggregate reconstruction')
 gs=list(gate);i=next(i for i,g in enumerate(gs) if g.get('event')=='query_integrity_passed' and g.get('control_step')==8);gs[i],gs[i+1]=gs[i+1],gs[i]
 reject('cross-type ordered query-step chain',gs=gs,fragment='complete ordered gate chain')
 gs=list(gate);i=next(i for i,g in enumerate(gs) if g.get('event')=='t0_pair_gate');gs[i],gs[i+1]=gs[i+1],gs[i]
 reject('pair must precede first query',gs=gs,fragment='complete ordered gate chain')
 es=list(events);a=next(i for i,e in enumerate(es) if e.get('phase')=='query_before');b=a+1;es[a],es[b]=es[b],es[a]
 # Preserve continuous indices so detection is based on semantic ordering.
 for i in (a,b):es[i]={**es[i],'event_index':events[i]['event_index']}
 reject('capture pre/post semantic order with valid indices',es=es,fragment='complete original capture')
 es=list(events);i=next(i for i,e in enumerate(es) if e.get('event')=='trial_end');es[i]=copy.deepcopy(es[i]);es[i]['status']='policy_error'
 reject('raw trial footer status mismatch',es=es,fragment='one original trial-end')
 es=list(events);i=next(i for i,e in enumerate(es) if e.get('event')=='trial_end');es.pop(i)
 reject('missing original trial end',es=es,fragment='one original trial-end')
 es=list(events);es.insert(-1,{'event':'unexpected_new_outer_event'})
 reject('unrecognized event before final return',es=es,fragment='unknown/extra event')
 reject('missing full terminal return',es=events[:-1],fragment='unknown/extra event')
 gs=list(gate);gs[-1]={**gs[-1],'event_sha256':'0'*64}
 reject('complete raw event bytes footer',gs=gs,fragment='footer binds complete')
 gs=list(gate);gs[-1]={**gs[-1],'original_prefix_trials':199}
 reject('never adopt prefix199',gs=gs,fragment='finish totals')
 es=list(events);es[0],es[1]=es[1],es[0];es[0]={**es[0],'event_index':1};es[1]={**es[1],'event_index':2}
 reject('native loader exact order',es=es,fragment='complete original loader')
 rs=list(rows);i=next(i for i,r in enumerate(rs) if r.get('event')=='result');rs[i]=copy.deepcopy(rs[i]);rs[i]['status']='policy_error'
 reject('policy error never silently deleted',rs=rs,fragment='whole200 completed')
 rs=list(rows);rs[i]=copy.deepcopy(rs[i]);rs[i]['control_steps']=301
 reject('control horizon remains300',rs=rs,fragment='pertrial original300')
 # Production function retains original 256x256 and real-environment assertions.
 prod=types.FunctionType(c.reconstruct_gate.__code__,ns,'unmodified_production',c.reconstruct_gate.__defaults__,c.reconstruct_gate.__closure__);prod.__kwdefaults__=c.reconstruct_gate.__kwdefaults__
 current.update(events=events,gate=gate)
 try:prod(R,rows,specification=spec,job_id='CPU_INDEPENDENT')
 except ValueError as e:ck('unmodified production rejects synthetic image schema','exact actual five-component' in str(e))
 else:ck('unmodified production rejects synthetic image schema',False)
 report={'schema':'formal_main_v2','kind':'Goal_full200_v2_independent_raw_consumer_checks','status':'passed','checks':CHECKS,'independent_rejections':len(REJECTS),'positive_reconstruction':{k:v for k,v in proof.items() if k!='raw_blob_refs'},'raw_refs':proof['raw_blob_refs'],'production_function_source_sha256':sh((D/'package/consumer.py').read_bytes()),'CPU_AST_derivations':changes,'CPU_derived_AST_sha256':sh(ast.dump(node,include_attributes=False).encode()),'synthetic_loader_records':8,'synthetic_loader_records_not_actual_GPU':True,'package_manifest_sha256':sh((D/'package/package_manifest.json').read_bytes()),'author_archive_members_verified':count,'original_counterexample_now_rejected':True,'exact_counterexample_changed_event_indices':targets,'production_ready':False,'actual_P_verified':False,'new_GPU_submissions':0,'new_scientific_trials':0,'old200_HOLD':True,'final_sealed':True}
 write(O/'independent_checks.json',report);print(json.dumps({'status':report['status'],'checks':len(CHECKS),'independent_rejections':len(REJECTS),'review_sha256':sh((O/'independent_checks.json').read_bytes())}))
try:main()
except BaseException as e:
 write(O/'independent_failure.json',dict(checks=CHECKS,error=str(e),type=type(e).__name__,traceback=traceback.format_exc()));raise
