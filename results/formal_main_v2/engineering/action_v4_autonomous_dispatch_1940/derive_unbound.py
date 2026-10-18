from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/action_v4_autonomous_dispatch_1940';OLD=R/'.local/action_v3_autonomous_dispatch_1808';C=R/'.local/action_runtime_lifecycle_v4_1940'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assign(source,name,value):
 tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name)
 lines=source.splitlines(keepends=True);return ''.join(lines[:node.lineno-1])+name+'='+repr(value)+'\n'+''.join(lines[node.end_lineno:])
T=D/'templates';manifest=json.loads((T/'source_publication_manifest.json').read_text());src=D/'source';src.mkdir()
for target,row in manifest['files'].items():
 if row.get('reuse_original_v3_path'):continue
 p=R/row['candidate_path'];assert sha(p)==row['sha256'];(src/Path(target).name).write_bytes(p.read_bytes())
paths=json.loads((T/'final_binding_input.template.json').read_text())['paths']
fac=(OLD/'facade.py').read_text().replace('v3','v4')
fac=assign(fac,'RESERVATION',{'path':paths['reservation'],'sha256':'__RESERVATION_SHA256__'})
(D/'facade.py').write_text(fac)
entry=(OLD/'entry.py').read_text().replace('v3','v4').replace('action_v4_autonomous_dispatch_1808','action_v4_autonomous_dispatch_1940')
entry=assign(entry,'FACADE_SHA',sha(D/'facade.py'))
bind={p.name:sha(p) for p in src.iterdir()};entry=assign(entry,'BINDINGS',bind)
refs={'root_review':{'path':paths['root_review'],'sha256':'__ROOT_REVIEW_SHA256__'},'manifest':{'path':'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/source/candidate_manifest.json','sha256':bind['candidate_manifest.json']},'gpu_registration':{'path':paths['gpu_registration'],'sha256':'__GPU_REGISTRATION_SHA256__'}}
entry=assign(entry,'REFS',refs);entry=assign(entry,'NODE_REG',{'path':paths['node_registration'],'sha256':'__NODE_REGISTRATION_SHA256__'})
entry=entry.replace('all_eight_v4_sources_unchanged','all_six_v4_sources_unchanged')
(D/'entry.py').write_text(entry)
(D/'entry.py.unbound.txt').write_text(entry);(D/'facade.py.unbound.txt').write_text(fac)
test=(OLD/'test_dispatch.py').read_text().replace('v3','v4')
test=test.replace("R/(entry.SOURCE+'submit.py')","D/'source/submit.py'").replace("R/(entry.SOURCE+'node_exclusion.py')","D/'source/node_exclusion.py'")
oldblock="""    for rel in [fmod.SUPERVISOR_REL,fmod.RESERVATION['path'],fmod.ACTIVATION['path'],entry.NODE_REG['path']]:put(rel,(R/rel).read_bytes())
    nr=json.loads((R/entry.NODE_REG['path']).read_bytes())
    for rel in nr['failure_evidence_sha256']:put(rel,(R/rel).read_bytes())
    put(orig.c.WRAPPER,(R/orig.c.WRAPPER).read_bytes())
"""
newblock="""    # Synthetic root-only records for isolated tests; never production acceptance.
    for rel in [fmod.SUPERVISOR_REL,fmod.ACTIVATION['path']]:put(rel,(R/rel).read_bytes())
    reservation=json.loads((D/'templates/reservation.template.json').read_text())['payload_template']
    reservation['synthetic_CPU_fixture_only']=True
    reservation['registration']=entry.REFS['gpu_registration']
    data=(json.dumps(reservation,sort_keys=True)+'\\n').encode()
    monkeypatch.setattr(fmod,'RESERVATION',{'path':fmod.RESERVATION['path'],'sha256':hashlib.sha256(data).hexdigest()})
    put(fmod.RESERVATION['path'],data)
    nr=json.loads((D/'templates/node_registration.template.json').read_text())['payload_template']
    nr['synthetic_CPU_fixture_only']=True
    data=(json.dumps(nr,sort_keys=True)+'\\n').encode()
    monkeypatch.setattr(entry,'NODE_REG',{'path':entry.NODE_REG['path'],'sha256':hashlib.sha256(data).hexdigest()})
    put(entry.NODE_REG['path'],data)
    for rel in nr['failure_evidence_sha256']:put(rel,(R/rel).read_bytes())
    put(orig.c.WRAPPER,(D/'source/probe.slurm').read_bytes())
"""
assert oldblock in test;test=test.replace(oldblock,newblock)
(D/'test_dispatch.py').write_text(test)
changes={'author':'server_v3_audit','production_semantics_unchanged':True,'facade':'all lowercase v3 labels -> v4; RESERVATION path/SHA literal only','entry':'all v3 labels -> v4; REL path; six new-source BINDINGS; FACADE_SHA, REF and NODE_REG literal values; two original v3 files kept in unmodified launcher contract closure','tests':'same 34 cases; only candidate import paths and explicitly synthetic unpublished reservation/node fixture construction differ','source_candidates':{n:sha(src/n) for n in bind},'upstream':{n:sha(OLD/n) for n in ['entry.py','facade.py','test_dispatch.py']},'unbound_file_sha256':{n:sha(D/n) for n in ['entry.py','facade.py','test_dispatch.py']},'final_SHA_binding_pending_root':True}
(D/'derivation_unbound.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(changes,ensure_ascii=False))
