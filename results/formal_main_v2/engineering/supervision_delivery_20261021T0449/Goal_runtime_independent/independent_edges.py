from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=Path(__file__).parent;A=R/'.local/goal_remaining5_runtime_20261021T0449';Q=A/'package';O=D/'independent_edge_outputs';O.mkdir(exist_ok=False)
checks=[];negatives=0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def reject(n,f,base=False):
 global negatives
 try:f()
 except BaseException as e:
  if isinstance(e,(AssertionError,KeyboardInterrupt,SystemExit)):raise
  if base:ck(n+'_BaseException',not isinstance(e,Exception))
  negatives+=1;ck(n,True,{'error_type':type(e).__name__,'error':str(e)});return
 raise AssertionError(n+' accepted')
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def save(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def extract(path,name,env):
 t=ast.parse(path.read_text());n=next(v for v in t.body if isinstance(v,ast.FunctionDef) and v.name==name);ns=dict(env)
 exec(compile(ast.Module(body=[n],type_ignores=[]),str(path)+'::<independent-isolated-original-function>','exec'),ns)
 return ns[name]

pm=json.loads((Q/'package_manifest.json').read_bytes());ck('package_pin',sha(Q/'package_manifest.json')=='200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f')
for path,pin in pm['files'].items():
 rel=Path(path).relative_to('scripts/ops/formal_goal_remaining5_gate_v1')
 ck('candidate_'+path,sha(Q/rel)==pin)
 for root in [R,P]:ck('actual_published_'+str(root)+'_'+path,sha(root/path)==pin and (root/path).resolve()==root/path)
for root in [R,P]:ck('manifest_published_'+str(root),sha(root/'scripts/ops/formal_goal_remaining5_gate_v1/package_manifest.json')==sha(Q/'package_manifest.json'))
e=load(Q/'entry.py','remaining5_independent_edges_entry');c=load(Q/'consumer.py','remaining5_independent_edges_consumer');s=load(Q/'storage.py','remaining5_independent_edges_storage')
old=Q/'entry.py.pre_ACK_and_encoding_v4';ck('original_c267_retained',sha(old)=='c2677e03c5475563e822fbbdadd3457b1b71c059e0a7982d31ca107dc8cff8fa')
# Independently reconstruct the exact former ACK-only false rejection, in memory.
ctx=e.context(e.scope.KEYS[0]);calls=[]
def capacity_fail(*args,**kwargs):calls.append(kwargs);raise ValueError('CPU simulated capacity consumed by already-running own ACK')
env=dict(e.__dict__)
env.update(_verify_sources=lambda *a:{'files':{e.PKG+'/storage.py':'cpu'}},prepare_original=lambda *a:({},None,None,None),read=lambda *a:{'rows':[]},validate_prefix=lambda *a:{'fixed200':True},load=lambda *a:SimpleNamespace(verify_storage=capacity_fail),ref=lambda *a:{'path':str(ctx.ORIGINAL),'sha256':'a'*64},sha=lambda *a:'b'*64)
oldfn=extract(old,'_verify',env);newfn=extract(Q/'entry.py','_verify',env)
reject('old_ACK_only_false_rejection_reproduced',lambda:oldfn(ctx,'c'*64,False))
ck('old_called_capacity_when_not_fresh',calls==[{'must_be_fresh':False,'aggregate_pair_keys':e.scope.KEYS}])
calls.clear();v=newfn(ctx,'c'*64,False)
ck('corrected_ACK_only_no_capacity_call',calls==[] and v['storage']['fresh_submission_capacity_verified'] is False and v['storage']['new_submission_authorized'] is False)
reject('new_fresh_still_checks_capacity',lambda:newfn(ctx,'c'*64,True));ck('fresh_full_five',calls==[{'must_be_fresh':True,'aggregate_pair_keys':e.scope.KEYS}])
# Former check encoded compact/default bytes, but actual output was indented.
value={'detail':['']*1400000};measured=json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode();written=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
ck('old_encoding_bound_actual_counterexample',len(measured)<=8*1024*1024<len(written),{'old_measured_bytes':len(measured),'actual_written_bytes':len(written),'ceiling':8*1024*1024})
reject('new_exact_encoding_rejects_same_value',lambda:e.bounded_json_bytes(value,8*1024*1024,indent=2),True)
for indent in [None,2]:
 value={'utf8':'输入','escape':'\n"\\','v':[1,2,3]};data=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=indent)+'\n').encode()
 ck('exact_write_bytes_'+str(indent),e.bounded_json_bytes(value,len(data),indent=indent)==data)
 reject('newline_accounted_'+str(indent),lambda:e.bounded_json_bytes(value,len(data)-1,indent=indent),True)
# Demonstrate old pre-import gap with an inert private marker; final source refuses before exec.
for modulefile,func,oldname in [('entry.py','scope_module','entry.py.pre_ACK_and_encoding_v4'),('consumer.py','_scope','consumer.py.pre_scope_pin_v5')]:
 sd=O/func;sd.mkdir();marker=sd/'executed_marker';(sd/'scope.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("inert CPU sentinel")\n')
 env={'Path':Path,'hashlib':hashlib,'importlib':importlib,'__file__':str(sd/modulefile)}
 extract(Q/oldname,func,env)();ck(func+'_old_import_gap_reproduced',marker.read_text()=='inert CPU sentinel')
 before=marker.stat().st_mtime_ns
 reject(func+'_new_refuses_before_exec',extract(Q/modulefile,func,env))
 ck(func+'_marker_unchanged',marker.stat().st_mtime_ns==before)
# Actual published prepared invocation and P verification receipts, no new invocation execution.
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249';idxp=B/'Goal_remaining5_actual_P_index.json';ck('actual_P_index_pin',sha(idxp)=='7e449e03818eda3402871b49cf952941f7590318cf640cd32cac96c2ba1f6fad')
idx=json.loads(idxp.read_bytes());captures=[]
for ref in idx['captures']:
 p=R/ref['path'];ck('actual_P_capture_'+p.stem,sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']);row=json.loads(p.read_bytes());captures.append(row)
save(O/'actual_P_captures_read.json',{'index':{'path':str(idxp),'sha256':sha(idxp)},'captures':captures,'scope':'published source metadata storage only; no GPU acceptance inferred'})
prep=B/'Goal_remaining5_prepared_invocations.json';ck('prepared_manifest_pin',sha(prep)=='45a1fe173f83597a8181f5129a5354bbdf0f49143743eac96de2dff8a418e578')
for ref in json.loads(prep.read_bytes())['original_invocations']:
 for root in [R,P]:ck('prepared_'+str(root)+'_'+ref['path'],sha(root/ref['path'])==ref['sha256'])
for key in e.scope.KEYS:
 cx=e.context(key);inv=json.loads(cx.ORIGINAL.read_bytes());effective=json.loads((P/cx.plans['effective_plan']['path']).read_bytes())
 ck(key+'_genuine_inv_extension',set(inv)==set(effective['invocation'])|{'registered_utc','plan_sha256','runtime_readiness'} and {k:inv[k] for k in effective['invocation']}==effective['invocation'])
 ck(key+'_uncreated_attempts',not cx.RAW.exists() and not cx.OUTPUT.exists())
 ck(key+'_method_runtime_seed_independent',inv['method_ids']==cx.methods and cx.config['runtime_seed']==17 and cx.config['seed']==cx.seed)
# Independently exercise physical raw inventory with a private explicit CPU ctx.
raw=O/'physical_raw_CPU_fixture';(raw/'observer/blobs').mkdir(parents=True)
for name in ['claim.json','runtime.stdout','runtime.stderr','observer/events.jsonl','observer/gate.jsonl']:(raw/name).write_bytes(b'CPU only\n')
cx=SimpleNamespace(RAW=raw)
def inventory():return [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(raw.rglob('*')) if p.is_file()]
rows=inventory();ck('raw_inventory_private_positive',len(c.validate_raw_inventory(cx,rows))==5)
for n,transform in [('omission',lambda x:x[:-1]),('duplicate',lambda x:x+[x[0]]),('bad_hash',lambda x:[dict(x[0],sha256='0'*64)]+x[1:]),('bad_bytes',lambda x:[dict(x[0],bytes=x[0]['bytes']+1)]+x[1:])]:reject('raw_'+n,lambda transform=transform:c.validate_raw_inventory(cx,transform(copy.deepcopy(rows))))
extra=raw/('a'*64+'.bin');extra.write_bytes(b'unlisted CPU data');reject('raw_unlisted_physical_file',lambda:c.validate_raw_inventory(cx,rows));ck('raw_extra_not_silently_lost',len(c.validate_raw_inventory(cx,inventory()))==6)
symlink=raw/('b'*64+'.bin');symlink.symlink_to(extra);reject('raw_symlink_alias_rejected',lambda:c.validate_raw_inventory(cx,inventory()));symlink.unlink()
# Capacity budget arithmetic independently, including record newline overhead inside margin.
pupper=200*(4*2**20+64*2**10+4096)+2*16*2**20+16*2**20+16*2**20+1024*65536+16*2**20
rupper=21032*(393288+65536+8192+16384)+68032*16384+2*2**31+2**32
ck('independent_storage_arithmetic',pupper==s.P_UPPER_BYTES==1003782144 and rupper==s.R_UPPER_BYTES==19871439680)
ck('R_margin_covers_newline_and_abort_record_overhead',21032+68032+4*16385+65536<s.R_MARGIN_BYTES)
ck('allfive_same_device_combined_requirement',5*(pupper+s.P_MARGIN_BYTES+rupper+s.R_MARGIN_BYTES)==110415906880)
capacity=s.verify_storage(e.context(e.scope.KEYS[0]));save(O/'independent_login_capacity.json',capacity)
ck('capacity_readonly_no_quota_claim',capacity['new_storage_paths_created'] is False and capacity['quota_not_proven'] is True and capacity['exclusive_claim_required_at_execution'] is True)
# No original package changes; pre-import scope-only correction leaves raw consumer exact.
a=ast.parse((Q/'consumer.py.pre_scope_pin_v5').read_text());b=ast.parse((Q/'consumer.py').read_text())
a.body=[n for n in a.body if not isinstance(n,ast.FunctionDef) or n.name!='_scope'];b.body=[n for n in b.body if not isinstance(n,ast.FunctionDef) or n.name!='_scope'];ck('final_consumer_only_preimport_guard_changed',ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False))
oldpkg=R/'scripts/ops/formal_goal_full200_gate_v1/package_manifest.json';ck('original_full200_manifest_unchanged',sha(oldpkg)=='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec')
for path,pin in json.loads(oldpkg.read_bytes())['files'].items():
 for root in [R,P]:ck('original_package_'+str(root)+'_'+path,sha(root/path)==pin)
source=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())['files'];ck('173_count',len(source)==173)
for root in [R,P/'snapshots/formal_main_v2_run_564be0995e']:
 for path,pin in source.items():ck('frozen173_'+str(root)+'_'+path,sha(root/path)==pin)
save(D/'independent_edges_report.json',{'status':'passed_independent_source_storage_edge_review','checks':checks,'check_count':len(checks),'negative_cases':negatives,'reproduced_old_defects':3,'actual_R_P_publication_verified':True,'actual_P_capture_review':'metadata_source_capacity_only','real_GPU_acceptance':False,'scientific_results_accepted':0,'GPU_submissions':0,'Slurm_queries':0,'production_writes':0})
print(json.dumps({'status':'passed_independent_source_storage_edge_review','check_count':len(checks),'negative_cases':negatives}))
