from pathlib import Path
import hashlib,json,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_runtime_20261021T0449';Q=D/'package'
for n in ('entry.py','consumer.py'):
 with (Q/(n+'.pre_hardening_v2')).open('xb') as f:f.write((Q/n).read_bytes())
s=(Q/'entry.py').read_text()
s=s.replace('from contextlib import ExitStack','from contextlib import ExitStack,contextmanager')
s=s.replace("result['existing_metadata_only']=True;result['new_submission_authorized']=False","result['status']='passed_existing_ACK_metadata_source_only';result['existing_metadata_only']=True;result['new_submission_authorized']=False;result['new_GPU_submission_allowed']=False")
insert=r'''
class MetadataBoundAbort(BaseException):
 """Stop original adapter/output publication before a bounded metadata overflow."""
@contextmanager
def bounded_adapter_scope(ctx,legacy,job):
 # Only this fresh legacy module instance's I/O helpers; original run code/source,
 # values, file names and original serializer remain intact. Always restore.
 append=legacy.append;publish=legacy.publish
 seen={'append_calls':0,'publish_calls':0,'paths':{}}
 def inspect(path,value,*,is_append):
  path=Path(path)
  expected=P/'results/formal_main_v2/adapter_invocations'
  require_path(path,path)
  if path.parent!=expected or not re.fullmatch(re.escape(job)+r'_[0-9a-f]{32}[.](jsonl|json)',path.name):
   raise MetadataBoundAbort('unregistered adapter output path')
  encoded=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,**({} if is_append else {'indent':2}))+'\n').encode('utf8')
  limit=4194304
  existing=path.stat().st_size if is_append and path.exists() else 0
  if len(encoded)+existing>limit:
   raise MetadataBoundAbort('adapter metadata prewrite 4MiB file bound exceeded; prefix retained')
  if is_append:
   seen['append_calls']+=1
   if seen['append_calls']>1024:raise MetadataBoundAbort('adapter event count exceeded')
  else:
   seen['publish_calls']+=1
   if seen['publish_calls']>1:raise MetadataBoundAbort('adapter receipt duplicate publication')
  seen['paths'][str(path)]=len(encoded)+existing
 def checked_append(path,value):
  inspect(path,value,is_append=True)
  return append(path,value)
 def checked_publish(path,value):
  inspect(path,value,is_append=False)
  return publish(path,value)
 legacy.append=checked_append;legacy.publish=checked_publish
 try:yield seen
 finally:
  intact=legacy.append is checked_append and legacy.publish is checked_publish
  legacy.append=append;legacy.publish=publish
  if not intact:raise MetadataBoundAbort('adapter bounded metadata bindings changed')
'''
pos=s.index('def redirect_runtime_output(');s=s[:pos]+insert+'\n'+s[pos:]
s=s.replace("return legacy.run(a, mode='evaluate', source_root=S, source_inventory=Path(inv['source_inventory']), adapter_sha256=LSHA, resume=False)",
"""with bounded_adapter_scope(ctx,legacy,job) as metadata_guard:
                    outcome=legacy.run(a, mode='evaluate', source_root=S, source_inventory=Path(inv['source_inventory']), adapter_sha256=LSHA, resume=False)
                emit('bounded_adapter_metadata_restored',storage=metadata_guard,original_run_source_unchanged=True)
                return outcome""")
s=s.replace("len(b)<=8*1024*1024","len(b)<=4*1024*1024")
assert 'with bounded_adapter_scope(ctx,legacy,job)' in s
ast.parse(s);(Q/'entry.py').write_text(s)
c=(Q/'consumer.py').read_text()
needle="require(job.get('stage_key') == ctx.stage_key"
c=c.replace(needle,"require(job.get('method_ids')==ctx.methods,'registered exact pair method IDs required')\n    "+needle)
needle="require(all((e['seq'] == i"
# add source-bound adapter storage witness before existing full outer validation
idx=c.index("    starts = [e for e in outer")
c=c[:idx]+"""    bounded=[e for e in outer if e['event']=='bounded_adapter_metadata_restored']
    require(len(bounded)==1 and bounded[0]['original_run_source_unchanged'] is True and bounded[0]['storage']['publish_calls']==1 and 1<=bounded[0]['storage']['append_calls']<=1024,'original adapter metadata writer guards restored once')
    require(all(type(n) is int and 0<=n<=4194304 for n in bounded[0]['storage']['paths'].values()),'actual adapter file bounds')
"""+c[idx:]
ast.parse(c);(Q/'consumer.py').write_text(c)
with (D/'hardening_v2_result.json').open('x') as f:json.dump({'changes':['read-only ACK verification output exact schema','fresh legacy module bounded append/publish scope with restoration','global and archived original adapter each <=4MiB so aggregate four files <=16MiB','registered method_ids and adapter guard terminal reconstruction'],'files':{n:hashlib.sha256((Q/n).read_bytes()).hexdigest() for n in ('entry.py','consumer.py')},'no_scientific_source_or_loop_change':True},f,indent=2)
print(json.dumps({'status':'private_hardening_complete','entry':hashlib.sha256(s.encode()).hexdigest(),'consumer':hashlib.sha256(c.encode()).hexdigest()}))
