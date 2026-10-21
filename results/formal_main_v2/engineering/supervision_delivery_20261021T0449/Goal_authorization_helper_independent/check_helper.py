"""Static-only review of exact root publication helper; never execute helper."""
from pathlib import Path
import ast,json,hashlib,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_remaining5_authorization_helper_review_20261021T0449'
HP='.local/authorize_goal_remaining5_20261021T0449.py'
PIN='9f4670a47d49c3f744ce79d7fbcac82aca53a1b611ff10d7b52cb384a8fbc7ce'
E='scripts/ops/formal_goal_remaining5_gate_v1/entry.py'
EPIN='b6704f4c7847d40c9072902152cec8771e4f013fda63c1bb4207504e3aa99e30'
G='scripts/ops/formal_goal_remaining5_dispatch_v1/gateway.py'
GPIN='45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b'
checks=[]
def req(ok,text):
 if not ok:raise ValueError(text)
 checks.append(text)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(rel,pin):
 b=(R/rel).read_bytes();req(sha(b)==pin,'pin '+rel);return b.decode()
def put(name,value):
 b=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
 with (D/name).open('xb') as f:f.write(b)
 return dict(path=str((D/name).relative_to(R)),sha256=sha(b),bytes=len(b))
def ref(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(R)),sha256=sha(b),bytes=len(b))
src=load(HP,PIN);entry=load(E,EPIN);gateway=load(G,GPIN)
req(sha((P/E).read_bytes())==EPIN and sha((P/G).read_bytes())==GPIN,'actual R/P exact runtime and gateway')
tree=ast.parse(src);compile(tree,str(R/HP),'exec')
env={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Constant)}
req(env['M']=='200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f' and env['GS']==GPIN and env['SS']=='f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b','final package and dispatcher pins')
assigns={n.targets[0].id:n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['auth','root','admission']}
et=ast.parse(entry);validate=next(n for n in et.body if isinstance(n,ast.FunctionDef) and n.name=='validate_authorization')
fixed=next(n.value for n in ast.walk(validate) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='fixed')
authkeys={k.value for k in assigns['auth'].keys};fixedkeys={k.value for k in fixed.keys}
req(authkeys==fixedkeys|{'root_review','independent_review','original_invocation'},'exact runtime authorization field set')
runtime_review=next(n for n in et.body if isinstance(n,ast.FunctionDef) and n.name=='check_review')
review_fixed=next(n.value for n in ast.walk(runtime_review) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='fixed')
rootkeys={k.value for k in assigns['root'].keys}
req({k.value for k in review_fixed.keys()}<=rootkeys,'root readiness supplies every final runtime required field')
av={k.value:v for k,v in zip(assigns['auth'].keys,assigns['auth'].values)}
for k,v in zip(fixed.keys,fixed.values):
 if isinstance(v,ast.Constant):req(ast.literal_eval(av[k.value])==v.value,'fixed auth literal '+k.value)
rv={k.value:v for k,v in zip(assigns['root'].keys,assigns['root'].values)}
for k,v in zip(review_fixed.keys,review_fixed.values):
 if isinstance(v,ast.Constant):req(ast.literal_eval(rv[k.value])==v.value,'fixed readiness literal '+k.value)
req(ast.literal_eval(rv['reviewed_by'])=='root','root reviewed_by distinct role')
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
run=[n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='run']
req(len(run)==1 and len(run[0].keywords)==1 and run[0].keywords[0].arg=='submit' and ast.literal_eval(run[0].keywords[0].value) is False,'only native transaction run is submit=False')
req(not any(isinstance(n.func,ast.Name) and n.func.id in ['exec','eval'] for n in calls),'no dynamic helper execution')
req(not any(isinstance(n.func,ast.Attribute) and n.func.attr in ['submit','release','cas','atomic_json'] for n in calls),'no direct submit/release/state write method')
req('fcntl.flock(lock,fcntl.LOCK_EX)' in src and 'assert h(R/"results/experiment_supervisor/state.json")==ST' in src,'shared writer lock and exact state CAS before publication')
req('assert not (r/rel).exists()' in src and 'assert not (R/DEST).exists()' in src,'all root target preexistence refusal')
req('with p.open("xb")' in src and 'os.fsync(f.fileno())' in src,'exclusive fsync writes')
req('assert not c.OUTPUT.exists() and not c.RAW.exists()' in src,'no prior target output/raw attempt')
req('e.check_review(ctx,ind,"independent",M,ctx.config_sha)' in src and 'e.check_review(ctx,root,"root",M,ctx.config_sha)' in src,'actual final readiness validators before publication')
req('e.validate_authorization(ctx,auth,ctx.config_sha,M,mp["files"][PROD+"/entry.py"])' in src,'actual final authorization validator before publication')
req('h(ctx.ORIGINAL)==inv["sha256"]' in src,'actual prepared invocation SHA checked')
req('n not in seen' in src and '".." not in pp.parts' in src and 'len(b)==rr["bytes"] and sha(b)==rr["sha256"]' in src,'bounded independent manifest archive byte checks')
req('assert out["status"]=="read_only_ready_not_submitted" and out["state_sha256"]==ST' in src,'each native read-only result checked')
req(src.index('with (R/"results/experiment_supervisor/.writer.lock")')<src.index('for n,b,rr in rows:put')<src.index('for key in mp["pair_keys"]:',src.index('dry=R/E/')),'read-only native observations occur after locked publication')
for name in ['root_readiness.json','independent_readiness.json','root_authorization.json','dispatch_admission.json']:
 req('("'+name+'",' in src,'exact per-pair payload '+name)
report={'schema':'formal_main_v2','kind':'Goal_remaining5_root_authorization_helper_static_review','status':'passed_static_exact_helper_interface_scope','reviewed_by':'spatial588_recovery_author_2054','review_scope':'root helper source and final runtime/gateway interface only','helper':dict(path=HP,sha256=PIN),'runtime_source':dict(path=E,sha256=EPIN),'dispatch_source':dict(path=G,sha256=GPIN),'checks':checks,'blockers':[],'actual_helper_execution_by_reviewer':False,'actual_independent_runtime_manifest_required_at_execution':True,'native_read_only_observation_still_required':True,'new_GPU_submissions':0,'GPU_execution_authorized':False,'scientific_results_accepted':0,'state_modified':False,'final_values_read':False,'notes':['Final runtime source review manifest/report remain exact required CLI inputs, not invented by this static review.','Helper makes five metadata authorizations; only a later separate root submit may launch GPUs.','Publication is fail-closed and exclusive; partial write or failed native check must be reconciled by root, never rerun blindly.','Actual native admission rechecks all runtime references, source maps, saved process argv, fresh capacity and then complete registered Slurm projection/lease under the shared lock.','The helper checks root pending/reservation early; autonomous pending and final/all-mode scope are also fail-closed in the reviewed native Transaction.'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
rr=put('independent_review.json',report)
with (D/'README.md').open('x') as f:f.write('Static-only exact root authorization helper review. No helper execution, publication, scheduler query or GPU action was performed by the reviewer. The final runtime/gateway validators and native read-only admission remain real execution requirements.\n')
mr=put('delivery_manifest.json',dict(schema='formal_main_v2',root=str(D.relative_to(R)),file_count=3,files=[ref(D/n) for n in ['check_helper.py','independent_review.json','README.md']]))
print(json.dumps(dict(status=report['status'],checks=len(checks),review=rr,manifest=mr)))
