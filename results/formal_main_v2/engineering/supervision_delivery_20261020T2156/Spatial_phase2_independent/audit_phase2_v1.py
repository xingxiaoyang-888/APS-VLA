"""Independent Spatial588 phase2 CPU review. No state/P/Git/Slurm mutation.
Only private audit outputs are written. Approval and new-allocation fixtures
exist only as in-memory bytes and never establish production evidence.
"""
from pathlib import Path
from types import ModuleType, SimpleNamespace
import ast,copy,hashlib,json,math,struct,sys,traceback
from datetime import datetime,timezone

R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/spatial_phase2_independent_20261020T2156'
B=R/'.local/spatial588_integration_20261020T2156/phase2_v2'
assert D.is_dir() and D.resolve()==D and not D.is_symlink()
MANREL=sys.argv[1];MANSHA=sys.argv[2]
assert MANREL=='.local/spatial588_integration_20261020T2156/phase2_v2_manifest.json'
PIN={
'control.py':'e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683',
'compatibility.py':'97773b017ae379dca050006bfbc255e68fe2d9e17924c90204a22bf0b102a5af',
'policy.json':'7341ba48d9c1a70557f8a883af40ac13b34caabe407fac2b9947fefc08fc9e87'}
PHASE1_REF={'path':'.local/spatial12_independent_20261020T2156/independent_review.json','sha256':'3cb7efa91ebbdb42c8ae91afef2f34ade5b237ee169a369a721353b0840bbf50'}
checks=[];readfiles={};synthetic=[];partial={}

def sha(b): return hashlib.sha256(b).hexdigest()
def jraw(v): return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def sig(v): return sha(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
def get(rel,expected=None):
    p=R/rel;assert p.resolve()==p and not p.is_symlink() and R in p.parents
    raw=p.read_bytes();h=sha(raw)
    if expected is not None: assert h==expected,(rel,h,expected)
    readfiles[rel]={'sha256':h,'bytes':len(raw)}
    return raw
def put(name,v):
    p=D/name;assert p.resolve()==p and p.parent==D
    with p.open('xb') as f: f.write(jraw(v))
    return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())}
def ok(name,v=True,detail=None):
    assert v,name
    item={'name':name,'passed':True}
    if detail is not None:item['detail']=detail
    checks.append(item)
def reject(name,fn):
    try:fn()
    except (ValueError,AssertionError,KeyError,FileNotFoundError,TypeError) as exc:
        checks.append({'name':name,'passed':True,'expected_rejection':str(exc)[:1000]});return
    raise AssertionError('Unexpected acceptance: '+name)
def mutate(v,k,x):
    out=copy.deepcopy(v);out[k]=x;return out

try:
    manifest=json.loads(get(MANREL,MANSHA));ok('candidate manifest remains CPU-only',manifest['production_admission'] is False and manifest['GPU_submissions']==0)
    for row in manifest['files']:
        data=get(row['path'],row['sha256']);ok('author frozen artifact '+row['path'],len(data)==row['bytes'])
    ok('author manifest exact count',len(manifest['files'])==manifest['file_count'])
    for name,h in PIN.items():get((B/name).relative_to(R).as_posix(),h)
    raw=(B/'control.py').read_bytes();c=ModuleType('_independent_spatial588_v2')
    c.__file__=str(B/'control.py');c.__package__=''
    exec(compile(raw,c.__file__,'exec',dont_inherit=True),c.__dict__)
    p=c.policy();cl=c.closure();descriptor=c.descriptor();bridge=c.compatibility_module()
    install=json.loads(get((B/'install_files.json').relative_to(R).as_posix()))
    ok('only13 install entries',len(install['files'])==13)
    wanted={row['destination']:row['sha256'] for row in install['files']}
    expected_names={'control.py','compatibility.py','policy.json',*p['compatibility_bundle_files']}
    ok('install closure is exact',set(Path(k).name for k in wanted)==expected_names and len(wanted)==len(expected_names))
    for row in install['files']:
        ok('byte preserving install '+row['destination'],row['source'].startswith(c.PRIVATE+'/') and row['destination']==c.CANONICAL+'/'+Path(row['source']).name and len(get(row['source'],row['sha256']))==row['bytes'])
    # Independent recursive mapping, never global JSON text replacement.
    def project(value):
        if isinstance(value,str):
            return c.CANONICAL+value[len(c.PRIVATE):] if value==c.PRIVATE or value.startswith(c.PRIVATE+'/') else value
        if isinstance(value,list):return [project(x) for x in value]
        if isinstance(value,dict):return {project(k):project(v) for k,v in value.items()}
        return value
    canonical_cl=project(cl);canonical_desc=project(descriptor);canonical_compat=project(bridge.descriptor())
    ok('canonical projected closure exactly install map plus original sources',canonical_cl=={**p['original_sources'],**wanted})
    projection=json.loads(get((B/'canonical_projection.json').relative_to(R).as_posix()))
    ok('independent canonical projection matches author source map',projection['source_closure']==canonical_cl)
    ok('independent canonical history projection matches',projection['typed_history_descriptor']==canonical_desc)
    ok('independent compatibility projection matches',projection['compatibility_descriptor']==canonical_compat)
    ok('private candidate differs from canonical root descriptor',canonical_desc!=descriptor and canonical_cl!=cl)
    ok('canonical projection does not assert publication',projection['actual_canonical_publication_done'] is False)

    # Verify the precise v1->v2 diff independently.
    prev=(R/'.local/spatial588_integration_20261020T2156/phase2/control.py').read_text()
    expected=prev.replace("PRIVATE='.local/spatial588_integration_20261020T2156/phase2'","PRIVATE='.local/spatial588_integration_20261020T2156/phase2_v2'",1)
    expected=expected.replace("REPAIR='results/formal_main_v2/execution/spatial588_pre_dispatch_v1/repair_record.json'","REPAIR='results/formal_main_v2/execution/spatial588_pre_dispatch_v1/repair_record.json'\nHISTORY_REVIEW='results/formal_main_v2/engineering/supervision_delivery_20261020T2156/Spatial_phase2_independent/independent_history_review.json'",1)
    expected=expected.replace("ref=d.get('independent_history_review');require(type(ref)is dict and set(ref)=={'path','sha256'},'independent typed history review required');","ref=d.get('independent_history_review');require(type(ref)is dict and set(ref)=={'path','sha256'} and ref.get('path')==HISTORY_REVIEW,'exact separately archived independent typed history review required');",1)
    ok('control v2 only private relocation and exact independent archive guard',expected.encode()==raw)
    oldcomp=(R/'.local/spatial588_integration_20261020T2156/phase2/compatibility.py').read_text()
    expected_comp=oldcomp.replace("ADOPTION='results/formal_main_v2/execution/spatial588_pre_dispatch_v1/legacy12_root_adoption.json'","ADOPTION='results/formal_main_v2/execution/spatial588_pre_dispatch_v1/legacy12_root_adoption.json'\nINDEPENDENT_REVIEW='results/formal_main_v2/engineering/supervision_delivery_20261020T2156/Spatial_independent/independent_review.json'\nINDEPENDENT_SHA='3cb7efa91ebbdb42c8ae91afef2f34ade5b237ee169a369a721353b0840bbf50'",1)
    expected_comp=expected_comp.replace("independent_ref['path'].startswith('results/formal_main_v2/') and independent_ref['path']!=ADOPTION","independent_ref=={'path':INDEPENDENT_REVIEW,'sha256':INDEPENDENT_SHA}",1).replace("ref['path'].startswith('results/formal_main_v2/') and ref['path']!=ADOPTION","ref=={'path':INDEPENDENT_REVIEW,'sha256':INDEPENDENT_SHA}",1)
    ok('compatibility v2 only exact genuine independent archive path and bytes',expected_comp.encode()==(B/'compatibility.py').read_bytes())

    helper,planner=c.control_modules();RealEvidence=helper.Evidence
    sys.path.insert(0,str(R/'src'))
    state_bytes=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_bytes)
    jobs=planner.formal_jobs(state)
    actual=RealEvidence(R);got=c.verify_history(actual,jobs)
    ok('actual complete prefix root consumer and no-child history rebuilt',got==descriptor)
    ok('actual original12 compatibility gate rebuilt',bridge.audit_prefix(RealEvidence(R))==bridge.descriptor())
    prior={j['job_id']:j for j in jobs if j['job_id'] in ('3022743','3042529')}
    ok('two original allocations exact and unique',len(prior)==2)
    ok('393 executed plus2 no-child preserved',[(prior[x]['status'],prior[x]['exit_code'],prior[x]['elapsed_seconds'],prior[x]['gpus']) for x in ['3022743','3042529']]==[('COMPLETED','0:0',393,1),('FAILED','1:0',2,1)])
    receipt=json.loads(get('results/formal_main_v2/job_receipts/3042529.json','86676fe6e84440069e61f4609008c4e5a9a7c88e883444519479d45767bd011e'))
    ok('no failed adapter invocation invented',receipt['original_scientific_wrapper_executed'] is False and receipt['adapter_artifacts']==receipt['adapter_receipts']==receipt['action_execution_artifacts']==[])
    snap=json.loads(get((B/'raw_failure_snapshot.json').relative_to(R).as_posix()))
    for rel,row in snap['raw_files'].items():
        ok('actual P failed raw identity '+rel,sha((P/rel).read_bytes())==sha(get(rel,row['sha256']))==row['sha256'])
    for row in snap['absence']:
        target=Path(row['directory']);ok('no child files '+str(target),P in target.parents and not list(target.glob(row['pattern'])))
    rawledger=get(p['prefix_ledger']['path'],p['prefix_ledger']['sha256'])
    ok('prefix exact raw592887 bytes',len(rawledger)==592887 and rawledger.endswith(b'\n'))
    rows=[json.loads(line) for line in rawledger.splitlines()]
    results=[x for x in rows if x.get('event')=='result'];starts=[x for x in rows if x.get('event')=='start']
    ok('original only3022743 invocation', [str(x.get('slurm_job_id')) for x in rows if x.get('event')=='invocation']==['3022743'])
    ok('12 originals start/result pairing',len(results)==len(starts)==12 and [x['trial_id'] for x in starts]==[x['trial_id'] for x in results])
    numchunks=actions=0;t0={}
    def encoded(matrix):
        return b''.join(struct.pack('<d',float(x)) for row in matrix for x in row)
    for start,row in zip(starts,results):
        ok('raw status '+row['trial_id'],row['status']=='completed')
        ok('raw identity '+row['trial_id'], all(row[k]==start[k] for k in ['trial_id','state_trial_id','task_id','method','source_state_index','initial_state_sha256','action_chunk','configured_wait_steps','environment_seed','runtime_seed','run_signature','split','suite']))
        full=[]
        for i,chunk in enumerate(row['chunks']):
            ok('full emitted8 '+row['trial_id']+'/'+str(i),chunk['control_step']==i*8 and len(chunk['environment_actions'])==len(chunk['normalized_actions'])==8 and all(len(a)==7 for a in chunk['environment_actions']+chunk['normalized_actions']))
            ok('finite and clipping byte invariant '+row['trial_id']+'/'+str(i),all(type(x) in (int,float) and math.isfinite(x) for a in chunk['environment_actions']+chunk['normalized_actions'] for x in a) and all(-1<=x<=1 for a in chunk['environment_actions'] for x in a))
            full.extend(chunk['environment_actions']);numchunks+=1
        ok('executed queue bytes '+row['trial_id'],len(row['executed_actions'])==row['control_steps'] and encoded(row['executed_actions'])==encoded(full[:row['control_steps']]))
        actions+=row['control_steps']
        t0.setdefault(row['state_trial_id'],[]).append((row['method'],row['chunks'][0]['observation_sha256']))
    ok('12/122/917 independently recomputed',(len(results),numchunks,actions)==(12,122,917))
    ok('two initial states have six methods and equal recorded t0',len(t0)==2 and all(len(v)==6 and {m for m,h in v}==set(p['method_ids']) and len({h for m,h in v})==1 for v in t0.values()))
    partial['actual_history']={'prior_job_ids':['3022743','3042529'],'actual_ledger_invocations':['3022743'],'retained_GPU_seconds':395,'executed_prefix_GPU_seconds':393,'predispatch_failure_GPU_seconds':2,'trials':12,'chunks':122,'executed_actions':917,'unique_initial_states':2}

    # Negative actual-source history checks, using only deep-copied state.
    for jid,key,val in [('3042529','elapsed_seconds',0),('3042529','status','COMPLETED'),('3022743','elapsed_seconds',2),('3042529','invocation',prior['3022743']['invocation'])]:
        js=copy.deepcopy(jobs);next(j for j in js if j['job_id']==jid)[key]=val
        reject('history rejects '+jid+'/'+key,lambda js=js:c.verify_history(RealEvidence(R),js))
    reject('history rejects duplicate allocation',lambda:c.verify_history(RealEvidence(R),jobs+[copy.deepcopy(prior['3042529'])]))
    reject('history rejects omitted failed allocation',lambda:c.verify_history(RealEvidence(R),[j for j in jobs if j['job_id']!='3042529']))
    unknown=copy.deepcopy(prior['3042529']);unknown.update(job_id='999999981',status='UNKNOWN')
    reject('history rejects unknown overlapping job',lambda:c.verify_history(RealEvidence(R),jobs+[unknown]))
    reject('pre-run cannot name imaginary current job',lambda:c.verify_history(RealEvidence(R),jobs,current_job=unknown))

    ind_bytes=get(PHASE1_REF['path'],PHASE1_REF['sha256']);independent=json.loads(ind_bytes)
    ref={'path':bridge.INDEPENDENT_REVIEW,'sha256':bridge.INDEPENDENT_SHA}
    candidate=bridge.adoption_proposal()
    reject('author candidate cannot self-adopt',lambda:bridge.validate_adoption_documents(candidate,independent,independent_ref=ref))
    approved=copy.deepcopy(candidate);approved.update(status='root_adopted',reviewed_by='root',independent_review=ref)
    ok('separate root and exact genuine independent documents positive CPU fixture',bridge.validate_adoption_documents(approved,independent,independent_ref=ref)==bridge.descriptor())
    for path in ['.local/fake.json',bridge.ADOPTION,c.HISTORY_REVIEW,'results/formal_main_v2/foreign.json']:
        reject('independent exact archive rejects '+path,lambda path=path:bridge.validate_adoption_documents(approved,independent,independent_ref={'path':path,'sha256':ref['sha256']}))
    reject('independent digest rejects substitute',lambda:bridge.validate_adoption_documents(approved,independent,independent_ref={'path':ref['path'],'sha256':'0'*64}))
    for key,value in [('status','candidate'),('reviewed_by','author'),('source_closure',{}),('legacy_origin_preserved',False),('historical_controller_is_source_inference',False),('new_GPU_seconds',1),('new_scientific_trials',12),('final_release',True),('profiling_authorized',True),('compatibility_descriptor',canonical_compat)]:
        reject('root adoption rejects '+key,lambda key=key,value=value:bridge.validate_adoption_documents(mutate(approved,key,value),independent,independent_ref=ref))
    for key,value in [('proof_sha256','0'*64),('phase1_manifest_sha256','0'*64),('scope',{}),('status','candidate'),('reviewed_by','root'),('blockers',['unresolved']),('full_original_author_reconstruction_passed',False),('independent_byte_and_queue_reconstruction_passed',False),('production_admission',True),('new_GPU_seconds',1),('new_scientific_trials',12)]:
        reject('independent proof rejects '+key,lambda key=key,value=value:bridge.validate_adoption_documents(approved,mutate(independent,key,value),independent_ref=ref))
    oldschema=copy.deepcopy(independent);oldschema['compatibility_proof_sha256']=oldschema.pop('proof_sha256')
    reject('old wrong proof key is rejected',lambda:bridge.validate_adoption_documents(approved,oldschema,independent_ref=ref))

    # Minimal approval byte overlay. No production path is written.
    mock_history={'kind':'formal_predispatch_history_independent_CPU_review','status':'passed_CPU_review','review_role':'independent','blockers':[],'history_control_sources':cl,'typed_predispatch_history':descriptor,'synthetic_CPU_fixture_NOT_PRODUCTION':True}
    mock_history_bytes=jraw(mock_history)
    repair=c.repair_proposal();repair.update(status='reviewed',reviewed_by='root',independent_history_review={'path':c.HISTORY_REVIEW,'sha256':sha(mock_history_bytes)},synthetic_CPU_fixture_NOT_PRODUCTION=True)
    approved['synthetic_CPU_fixture_NOT_PRODUCTION']=True
    overlay={c.HISTORY_REVIEW:mock_history_bytes,c.REPAIR:jraw(repair),ref['path']:ind_bytes,bridge.ADOPTION:jraw(approved)}
    class OverlayEvidence:
        def __init__(self,project):
            assert Path(project).resolve()==R;self.project=R;self.real=RealEvidence(R);self.files={}
        def __getattr__(self,n):return getattr(self.real,n)
        def key(self,n):return Path(n).relative_to(R).as_posix() if Path(n).is_absolute() else n
        def require(self,paths):return self.real.require([n for n in paths if self.key(n) not in overlay])
        def path(self,n):return self.real.path(n)
        def watch(self,n):
            k=self.key(n);h=sha(overlay[k]) if k in overlay else self.real.watch(k);self.files[k]=h;return h
        def read(self,n):
            k=self.key(n);self.watch(k);return json.loads(overlay[k]) if k in overlay else self.real.read(k)
        def unchanged(self):
            self.real.unchanged()
            for k,h in self.files.items():assert h==(sha(overlay[k]) if k in overlay else self.real.watch(k)),k
    helper.Evidence=OverlayEvidence
    args=SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=p['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=p['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
    # A currently unrelated pending root transaction must never be cleared live.
    # Fixtures use only a copied state and explicitly label that field if needed.
    fixture_state=copy.deepcopy(state)
    pending_was_present=fixture_state.get('pending_submission') is not None
    if pending_was_present:fixture_state['pending_submission']=None
    planned=planner.plan(args,fixture_state,project=R,helper=helper)
    inv=planned['invocation']
    ok('full original scoped planner reconstructed using CPU in-memory approvals',planned['invocation_relative'].endswith('_attempt03.json') and inv['prior_job_ids']==['3022743','3042529'] and inv['pre_dispatch_history']==descriptor and inv['legacy12_compatibility']==bridge.descriptor())
    ok('planner retains original manifest methods output and no extra scientific flags',inv['method_ids']==p['method_ids'] and inv['execution_manifest_sha256']==p['manifest']['sha256'] and inv['run_root']==p['run_root'] and inv['stop_after'] is None and '--resume' in inv['argv'] and not any(x in inv['argv'] for x in ('--sealed-final','--release','--stop-after')))
    ok('planner signature is exact',planner.signature({k:v for k,v in planned.items() if k!='plan_sha256'})==planned['plan_sha256'])
    ok('both allocations retained in plan cost',[(x['job_id'],x['elapsed_seconds']) for x in inv['prior_allocation_cost']]==[('3022743',393),('3042529',2)])
    badstate=copy.deepcopy(fixture_state);badstate['pending_submission']={'unknown_not_cleared':True}
    reject('full planner pending duplicate protection',lambda:planner.plan(args,badstate,project=R,helper=helper))
    for key,value in [('stage','final'),('stage','collect'),('stage','full'),('stage','components'),('resume',False),('stop_after',1),('execution_manifest','foreign.json'),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json')]:
        bad=copy.deepcopy(args);setattr(bad,key,value)
        reject('planner argument scope '+key+'/'+str(value),lambda bad=bad:planner.plan(bad,fixture_state,project=R,helper=helper))
    extra=copy.deepcopy(args);extra.future_parameter=True
    reject('planner forbids unregistered argument',lambda:planner.plan(extra,fixture_state,project=R,helper=helper))
    for path in ['.local/forged.json',c.REPAIR,bridge.ADOPTION,'results/formal_main_v2/other_independent.json']:
        bad=copy.deepcopy(repair);bad['independent_history_review']['path']=path
        saved=overlay[c.REPAIR];overlay[c.REPAIR]=jraw(bad)
        reject('repair exact independent history path '+path,lambda:c.check_repair(OverlayEvidence(R),c.REPAIR,jobs))
        overlay[c.REPAIR]=saved
    changed=copy.deepcopy(mock_history);changed['history_control_sources']=canonical_cl
    oldbytes=overlay[c.HISTORY_REVIEW];oldrepair=overlay[c.REPAIR]
    overlay[c.HISTORY_REVIEW]=jraw(changed);wrongrepair=copy.deepcopy(repair);wrongrepair['independent_history_review']['sha256']=sha(overlay[c.HISTORY_REVIEW]);overlay[c.REPAIR]=jraw(wrongrepair)
    reject('private module cannot consume canonical projection as if same installed closure',lambda:c.check_repair(OverlayEvidence(R),c.REPAIR,jobs))
    overlay[c.HISTORY_REVIEW]=oldbytes;overlay[c.REPAIR]=oldrepair

    # Full original cost chain, genuine two predecessors, no fake failed ledger.
    current=copy.deepcopy(prior['3042529']);current.update(job_id='999999982',status='COMPLETED',raw_status='COMPLETED',exit_code='0:0',elapsed_seconds=101,submitted_utc='2099-01-01T00:00:00+00:00',prior_job_ids=['3022743','3042529'],invocation=planned['invocation_relative'],synthetic_CPU_fixture_NOT_A_JOB=True)
    synthetic_inv=copy.deepcopy(inv)
    synthetic_inv['root_evidence_sha256'][c.REPAIR]=sha(overlay[c.REPAIR])
    synthetic_inv['root_evidence_sha256'][c.HISTORY_REVIEW]=sha(overlay[c.HISTORY_REVIEW])
    current['invocation_sha256']=sha(jraw(synthetic_inv));overlay[current['invocation']]=jraw(synthetic_inv)
    cost_jobs=jobs+[current];old=c.terminal_old(OverlayEvidence(R),cost_jobs,current,synthetic_inv)
    costs=old.allocation_cost(OverlayEvidence(R),planner,cost_jobs,current,synthetic_inv,['3022743','999999982'])
    ok('full derived original cost retains393+2+mock101 exactly once',[(x['job_id'],x['elapsed_seconds']) for x in costs['allocations']]==[('3022743',393),('3042529',2),('999999982',101)] and costs['current_gpu_seconds']==101 and costs['all_attempt_gpu_seconds']==496)
    ok('terminal typed cost still reports true historical395',costs['typed_predispatch_history']['prior_GPU_seconds']==395 and costs['typed_predispatch_history']['predispatch_failure_GPU_seconds']==2)
    for observed in [[],['999999982'],['3022743','3042529','999999982'],['999999982','3022743'],['3022743','999999982','999999982']]:
        reject('observed execution history '+','.join(observed),lambda observed=observed:old.allocation_cost(OverlayEvidence(R),planner,cost_jobs,current,synthetic_inv,observed))
    bad=copy.deepcopy(synthetic_inv);bad['prior_allocation_cost'][1]['elapsed_seconds']=0
    saved_current=overlay[current['invocation']];overlay[current['invocation']]=jraw(bad);badcurrent=copy.deepcopy(current);badcurrent['invocation_sha256']=sha(overlay[current['invocation']]);badjobs=jobs+[badcurrent]
    reject('original cost guard rejects omitted two seconds',lambda:c.terminal_old(OverlayEvidence(R),badjobs,badcurrent,bad).allocation_cost(OverlayEvidence(R),planner,badjobs,badcurrent,bad,['3022743',current['job_id']]))
    overlay[current['invocation']]=saved_current
    badjobs=copy.deepcopy(cost_jobs);badjobs.append(copy.deepcopy(current))
    reject('terminal duplicate allocations rejected',lambda:c.terminal_old(OverlayEvidence(R),badjobs,current,synthetic_inv))
    for name,value in [('status','FAILED'),('status','TIMEOUT'),('status','PREEMPTED'),('status','UNKNOWN'),('exit_code','1:0')]:
        badcurrent=copy.deepcopy(current);badcurrent[name]=value
        reject('terminal non-success rejected '+name+'/'+value,lambda badcurrent=badcurrent:c.terminal_old(OverlayEvidence(R),jobs+[badcurrent],badcurrent,synthetic_inv))
    # Stage checks precede any output/reference read.
    class NeverRead:
        def read(self,*a):raise AssertionError('unexpected I/O')
    consumer=c.consumer_module()
    for stage,suite in [('final','libero_spatial'),('collect','libero_spatial'),('full','libero_spatial'),('components','libero_spatial'),('development','libero_goal')]:
        try:consumer.review_downstream_output(NeverRead(),{},expected_stage=stage,suite=suite)
        except ValueError:ok('consumer rejects before I/O '+stage+'/'+suite)
        else:raise AssertionError('consumer failed early scope rejection')
    # Runtime/audit entry points remain originals, not changes to the 173 science.
    original_sources=dict(p['original_sources'])
    for rel,h in original_sources.items():get(rel,h)
    ok('planner derivation changes exactly2 guarded comparisons',planner._spatial588_derivation['replacements']==2 and planner._spatial588_derivation['original_file_modified'] is False)
    ok('cost derivation changes exactly3 guarded comparisons',old._spatial588_derivation['replacements']==3 and old._spatial588_derivation['original_file_modified'] is False)
    reviewer=c.reviewer_module()
    ok('reviewer dependency derivation exactly1 and unchanged original file',reviewer._spatial588_derivation['replacements']==1 and reviewer._spatial588_derivation['original_file_modified'] is False)
    ok('consumer source file remains exact',consumer._spatial588_derivation['replacements']==0 and consumer._spatial588_derivation['original_file_modified'] is False)
    actual.unchanged()
    for rel,row in readfiles.items():assert sha((R/rel).read_bytes())==row['sha256'],rel
    fixture_note={
      'kind':'independent_CPU_in_memory_fixture_summary_NOT_PRODUCTION','mock_approvals_never_written_to_named_paths':True,
      'mock_current_job_id':'999999982','mock_GPU_seconds_NOT_ACTUAL_COST':101,'mock_total_NOT_ACTUAL_COST':496,
      'real_retained_prior_GPU_seconds':395,'no_mock_ledger_or_scientific_trial_created':True,
      'registered_state_snapshot_sha256':sha(state_bytes),'unrelated_live_pending_was_present':pending_was_present,
      'pending_override_only_in_deep_copied_CPU_fixture':pending_was_present,
      'synthetic_plan_signature_NOT_FOR_SUBMISSION':planned['plan_sha256'],
      'synthetic_plan_NOT_published':True,'memory_overlay_path_names':sorted(overlay),
      'actual_new_P_verification':False,'actual_new_terminal600_consumer':False}
    details_ref=put('independent_test_details.json',{'schema':'formal_main_v2','status':'passed_CPU_review','checks':checks,'check_count':len(checks),'observations':partial,'CPU_fixture':fixture_note,'author_manifest':{'path':MANREL,'sha256':MANSHA}})
    evidence_ref=put('independent_evidence.json',{'source_and_raw_files':readfiles,'candidate_private_closure':cl,'canonical_install_projection':canonical_cl,'original_derived_modules':{'planner':planner._spatial588_derivation,'allocation':old._spatial588_derivation,'reviewer':reviewer._spatial588_derivation,'consumer':consumer._spatial588_derivation},'canonical_and_P_install_verification_claimed':False})
    review={
      'schema':'formal_main_v2','kind':'formal_predispatch_history_independent_CPU_review','status':'passed_CPU_review',
      'review_role':'independent','reviewed_by':'independent','review_agent':'/root/goal_cpu_gate_2054',
      'blockers':[],'author_manifest':{'path':MANREL,'sha256':MANSHA},'history_control_sources':canonical_cl,
      'typed_predispatch_history':canonical_desc,'candidate_private_history_control_sources':cl,
      'candidate_private_typed_predispatch_history':descriptor,'independently_rebuilt_compatibility_descriptor':canonical_compat,
      'canonical_scope_is_deterministic_install_projection':True,'canonical_closure_provenance':'Exact private package file bytes plus explicit destination map; root must install and compare its regenerated canonical closure and descriptors before adoption. This report does not assert actual canonical R/P publication or new P wrapper verification.',
      'actual_new_canonical_P_verification_passed':False,'production_admission':False,
      'legacy12_phase1_independent_review':PHASE1_REF,'legacy_origin_preserved':True,
      'historical_controller_identity_is_source_continuity_inference':True,'historical_controller_instance_or_RNG_dump_invented':False,
      'actual_prior_allocations':partial['actual_history'],'original_prefix_review_fully_rebuilt':True,
      'actual_no_child_failure_forensic_identity_rebuilt':True,'full_original_planner_CPU_fixture_passed':True,
      'full_derived_original_cost_CPU_fixture_passed':True,'checks':len(checks),'test_details':details_ref,'evidence':evidence_ref,
      'new_GPU_seconds':0,'new_GPU_submissions':0,'new_scientific_trials':0,'state_mutated':False,'P_mutated':False,'Git_mutated':False,'sealed_values_read':False,'weights_read':False,
      'required_root_gates':['Byte-identical canonical package installation and regenerated closure/descriptor equality, including actual P source/dependency validation before dispatch','Archive this exact independent report under HISTORY_REVIEW; archive exact Spatial12 independent bytes under fixed INDEPENDENT_REVIEW and SHA; root explicitly regenerates and adopts separate repair and legacy12 records','Fresh genuine scientific/effective plan, transition, runtime root+independent readiness and actual P verify; no synthetic fixture or private proposal may be submitted','Root exact-once submission with pending/token/ACK reconciliation and all-mode eight-slot bound','Original terminal/full-consumer reconstruction on actual600 raw records plus independent terminal audit, with12 legacy-compatible and588 new-wrapper labels and all costs once'],
      'global_final_release':False,'profiling_authorized':False,
      'limitations':['CPU fixture approval overlays and mock101 seconds are not a production plan, permission, run, success rate or GPU cost.','No new588 trial or complete600 terminal result has been produced by this audit.','The source-derived historical controller inference remains bounded to the actual12 valid bytes; it does not generalize to Object599/600 or Goal200.'],
      'utc':datetime.now(timezone.utc).isoformat()}
    revref=put('independent_history_review.json',review)
    paths=sorted(x for x in D.iterdir() if x.is_file())
    delivery={'schema':'formal_main_v2','kind':'Spatial588_phase2_independent_CPU_delivery','status':'passed_CPU_review','review':revref,'files':[{'path':x.relative_to(R).as_posix(),'sha256':sha(x.read_bytes()),'bytes':x.stat().st_size} for x in paths],'new_GPU_seconds':0,'new_scientific_trials':0,'production_admission':False}
    manref=put('delivery_manifest.json',delivery)
    print(json.dumps({'status':'passed_CPU_review','check_count':len(checks),'review':revref,'delivery_manifest':manref},sort_keys=True))
except BaseException as exc:
    if not (D/'failure_a1.json').exists():put('failure_a1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'partial':partial,'new_GPU_seconds':0,'production_admission':False})
    raise
