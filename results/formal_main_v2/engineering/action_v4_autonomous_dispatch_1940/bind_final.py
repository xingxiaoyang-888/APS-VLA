from pathlib import Path
import ast,copy,datetime,hashlib,importlib.util,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/action_v4_autonomous_dispatch_1940';OLD=R/'.local/action_v3_autonomous_dispatch_1808'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mod(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def assign(source,name,value):
 node=next(n for n in ast.parse(source).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name)
 lines=source.splitlines(keepends=True);return ''.join(lines[:node.lineno-1])+name+'='+repr(value)+'\n'+''.join(lines[node.end_lineno:])
binding_path=R/'results/formal_main_v2/preflight/heartbeat_20261019T0340/action_v4_root_binding.json'
assert sha(binding_path)=='b794d8bb982b49577a2139b5edbd924aedc605a46ae484bd819438b7fe8e42bd'
b=json.loads(binding_path.read_text());expected={'root_review':'27db3a1a68821ffa56233b16e50e8af88b536e496de64f6d25cd307cf1636e52','gpu_registration':'96dea708c5efd8da465952877d41de36cbe8dd56e3c3a5b5fc256488d255f164','node_registration':'6f9358a980219bfaf6e8f867d657e72815e4ae08a1501fe378353f31415716b4','reservation':'90ec791baeac23aeb3facc909cd95f6d7db0345ab76ed1f99c7f6f10211636a5'}
paths=json.loads((D/'templates/final_binding_input.template.json').read_text())['paths']
for key,digest in expected.items():assert b[key]=={'path':paths[key],'sha256':digest} and sha(R/b[key]['path'])==digest
assert not (D/'final_binding.json').exists()
fac=(D/'facade.py.unbound.txt').read_text();assert fac.count('__RESERVATION_SHA256__')==1;fac=fac.replace('__RESERVATION_SHA256__',expected['reservation']);assert '__RESERVATION_SHA256__' not in fac
(D/'facade.py').write_text(fac)
entry=(D/'entry.py.unbound.txt').read_text()
for tok,key in [('__ROOT_REVIEW_SHA256__','root_review'),('__GPU_REGISTRATION_SHA256__','gpu_registration'),('__NODE_REGISTRATION_SHA256__','node_registration')]:assert entry.count(tok)==1;entry=entry.replace(tok,expected[key])
entry=assign(entry,'FACADE_SHA',sha(D/'facade.py'));assert '__SHA256__' not in entry
(D/'entry.py').write_text(entry)
fm=mod(D/'facade.py','_bound_v4_facade');em=mod(D/'entry.py','_bound_v4_entry')
assert em.FACADE_SHA==sha(D/'facade.py') and fm.RESERVATION==b['reservation'] and em.REFS['root_review']==b['root_review'] and em.REFS['gpu_registration']==b['gpu_registration'] and em.NODE_REG==b['node_registration']
# Exact AST reversal: changed data literals and v4-labelled diagnostics only.
oldfac=ast.parse((OLD/'facade.py').read_text());newfac=ast.parse(fac.replace('v4','v3'))
oldentry=ast.parse((OLD/'entry.py').read_text());newentry=ast.parse(entry.replace('v4','v3').replace('all_six_v3_sources_unchanged','all_eight_v3_sources_unchanged'))
def restore_assignments(new,old,names):
 for i,node in enumerate(new.body):
  if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in names:
   new.body[i]=copy.deepcopy(next(x for x in old.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id==node.targets[0].id))
restore_assignments(newfac,oldfac,{'RESERVATION'});restore_assignments(newentry,oldentry,{'REL','FACADE_SHA','SOURCE','BINDINGS','REFS','NODE_REG'})
assert ast.dump(oldfac,include_attributes=False)==ast.dump(newfac,include_attributes=False)
assert ast.dump(oldentry,include_attributes=False)==ast.dump(newentry,include_attributes=False)
for name,digest in em.BINDINGS.items():assert sha(R/(em.SOURCE+name))==digest and sha(D/'source'/name)==digest
orig=fm.load(R/(em.SOURCE+'submit.py'),'_bound_original_v4_submit',em.BINDINGS['submit.py'])
checked=orig.c.check_contract(R,root_ref=em.REFS['root_review'],manifest_ref=em.REFS['manifest'],registration_ref=em.REFS['gpu_registration'])
source_checked={}
for name,digest in checked['inventory']['files'].items():
 for base in [R,Path(orig.c.S)]:assert sha(base/name)==digest;source_checked[str(base/name)]=digest
record={'kind':'v4_control_exact_literal_binding_author_record','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings_receipt':{'path':str(binding_path.relative_to(R)),'sha256':sha(binding_path)},'upstream_root_refs':{k:b[k] for k in expected},'files':{n:sha(D/n) for n in ['entry.py','facade.py','test_dispatch.py']},'AST_reversal_equals_reviewed_v3':{'entry':True,'facade':True},'original_execute_submit_and_gate_unchanged':True,'closure':{'watched_files':checked['watched_files'],'deployment_files':checked['deployment_files'],'verified_count':len(checked['watched_files'])},'source173_both_roots':source_checked,'no_model_or_GPU_calls':True,'Slurm_queries':0,'Slurm_submissions':0,'production_state_writes':0,'root_authority_not_created_here':True,'check_only_default':True,'scientific_release':False,'independent_control_review_pending':True}
(D/'final_binding.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'entry_sha256':record['files']['entry.py'],'facade_sha256':record['files']['facade.py'],'test_sha256':record['files']['test_dispatch.py'],'binding_sha256':sha(D/'final_binding.json'),'closure_files':record['closure']['verified_count'],'unchanged_R_S':len(source_checked)},ensure_ascii=False))
