from __future__ import annotations
import argparse,ast,contextlib,copy,datetime,hashlib,importlib.util,io,json,os,pathlib,re,subprocess,sys,time,traceback
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
R=H/'control_repo'
S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
C=H/'storage_migration_candidates/action_gpu_v3_server_entry_v1'
O=H/'storage_migration_candidates/action_gpu_v3_server_entry_independent_v1'
REVIEW_SHA='6f7822ecf546d5d7e0fbac574b08c3d02b51177ee59e0bf0069cdf2577a2377f'
ENTRY_SHA='2db9a8fa4ef2dcf3eb73e02dbf30e7b4c1adc56b11772c783d76c88dfb3ce07b'
AUDIT_REL='.local/action_execution_gpu_v3_independent_0840/independent_review.json'
ENTRY=C/'entry.py'
checks=[]
read={}
def sha(p):
    b=Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest()
def record(name, fn):
    start=time.monotonic()
    try:
        detail=fn()
        checks.append(dict(name=name,passed=True,seconds=time.monotonic()-start,detail=detail))
    except Exception:
        checks.append(dict(name=name,passed=False,seconds=time.monotonic()-start,error=traceback.format_exc()))
def assert_(v,msg):
    if not v:raise AssertionError(msg)
def same_hash(path,expected):
    got=sha(path);assert_(got==expected,'SHA mismatch '+str(path));read[str(path)]=got
def load():
    d={'__name__':'_independent_entry','__file__':str(ENTRY)}
    exec(compile(ENTRY.read_bytes(),str(ENTRY),'exec'),d)
    return type('ModuleView',(),{})(),d
def command(d,mode='--validate-only'):
    return [str(ENTRY),'--independent-review',AUDIT_REL,'--independent-sha256',d['INDEPENDENT_SHA'],'--entry-sha256',ENTRY_SHA,mode]
def call(d,args):
    stdout,stderr=io.StringIO(),io.StringIO()
    with mock.patch.object(sys,'argv',args),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        d['main']()
    return stdout.getvalue(),stderr.getvalue()
def reject(d,args,kind,text=None):
    try:call(d,args)
    except kind as exc:
        assert_(text is None or text in str(exc),'unexpected rejection '+str(exc))
        return dict(rejected=kind.__name__,reason=str(exc))
    raise AssertionError('unexpected acceptance')
def guarded():
    events=[]
    def guard(event,args):
        write=False
        if event=='open':
            mode,flags=args[1],args[2]
            write=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
        if write or event in {'os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.chmod','os.truncate','subprocess.Popen','os.system','socket.connect','socket.bind'}:
            events.append(dict(event=event))
            raise RuntimeError('independent read-only audit rejected '+event)
    sys.addaudithook(guard)
    _,d=load()
    before={rel:(R/rel).exists() for rel in [*(d['SOURCE']+n for n in d['EXPECTED']),d['AUTHOR'],d['AUDIT'],d['TYPED'],d['REVIEW'],d['REG'],d['NODE'],d['CHECK'],d['SCRIPT_ARCHIVE']]}
    assert_(not any(before.values()),'an actual publication already exists')
    validation={}
    def actual():
        _,m=load()
        out,err=call(m,command(m))
        assert_(err=='','unexpected stderr')
        validation.update(json.loads(out))
        assert_(validation['status']=='validated_server_candidate_no_publication_root_decision_pending','wrong diagnostic status')
        for k in ('files_written','subprocess_calls','SSH_calls','Slurm_submissions','GPU_seconds'):assert_(validation[k]==0,k)
        for k in ('root_approval_recorded','actual_GPU_acceptance','scientific_release'):assert_(validation[k] is False,k)
        return {k:validation[k] for k in ('status','candidate_files','frozen_source_files','planned_publications','deployment_files','root_approval_recorded')}
    record('actual_real_evidence_validation_under_write_network_and_process_denial',actual)
    record('missing_mode_rejected',lambda:reject(d,command(d)[:-1],SystemExit,'2'))
    record('contradictory_modes_rejected',lambda:reject(d,command(d)+['--root-approve-cpu-registration'],SystemExit,'2'))
    record('candidate_location_cannot_publish_even_with_root_flag',lambda:reject(d,command(d,'--root-approve-cpu-registration'),ValueError,'reviewed installed R entry'))
    def bad_entry():
        args=command(d);args[args.index('--entry-sha256')+1]='0'*64
        return reject(d,args,ValueError,'reviewed entry SHA differs')
    record('wrong_entry_SHA_rejected',bad_entry)
    def bad_receipt():
        args=command(d);args[args.index('--independent-sha256')+1]='0'*64
        return reject(d,args,ValueError,'final reviewed v3 independent bytes')
    record('wrong_original_independent_SHA_rejected',bad_receipt)
    def bad_root():
        _,m=load();m['ROOT']=C
        return reject(m,command(m),ValueError,'wrong server control root')
    record('wrong_control_root_rejected',bad_root)
    def drift():
        _,m=load();m['MIGRATION_BINDINGS']=dict(m['MIGRATION_BINDINGS']);m['MIGRATION_BINDINGS']['SERVER_WORKSPACE.md']='0'*64
        return reject(m,command(m),ValueError,'evidence SHA differs')
    record('workspace_policy_pin_drift_rejected',drift)
    def evidence_path_guards():
        bad=['../escape.json','/tmp/file.json','F:/CTI-VLA/x.json','a//b.json','a/./b.json','results/sealed/x.json','results/panel.json','results/final_registry.json','results/weights/x.json','results/test/x.json','results/file.pt','results/experiment_supervisor/state.json',d['SYNTHETIC_STATE'].replace('CPU_only0','CPU_only1')]
        with mock.patch.object(Path,'resolve',side_effect=AssertionError('forbidden path reached filesystem')):
            for path in bad:
                try:d['safe'](path,synthetic=True)
                except ValueError:pass
                else:raise AssertionError('path unexpectedly accepted '+path)
        try:d['safe'](d['SYNTHETIC_STATE'])
        except ValueError:pass
        else:raise AssertionError('synthetic state requires explicit CPU exception')
        assert_(d['safe'](d['SYNTHETIC_STATE'],synthetic=True)==R/d['SYNTHETIC_STATE'],'exact synthetic exception missing')
        return dict(rejected_before_filesystem=len(bad),synthetic_exception='only exact CPU fixture')
    record('path_and_unique_synthetic_authority_boundaries',evidence_path_guards)
    def occupied():
        _,m=load();original=Path.exists;target=R/m['REG']
        def exists(p):return True if p==target else original(p)
        original_lstat=Path.lstat; regular_stat=ENTRY.lstat()
        def lstat(p):return regular_stat if p==target else original_lstat(p)
        with mock.patch.object(Path,'exists',exists),mock.patch.object(Path,'lstat',lstat):
            return reject(m,command(m),ValueError,'destination already exists')
    record('existing_registration_refused_before_publication',occupied)
    def closure():
        rows=validation['deployment_mapping']
        assert_(len(rows)==305 and len({x['server'] for x in rows})==len(rows),'closure count or duplicates')
        assert_(sum(x['server'].startswith(str(S)+'/') for x in rows)==173,'frozen closure mismatch')
        for row in rows:
            assert_(row['server'].startswith(d['RUNTIME_ROOT']+'/'),'off-runtime closure')
            assert_(row['path'] not in (d['REG'],d['REVIEW'],d['SYNTHETIC_STATE']),'self-cycle or synthetic state deployed')
            assert_('pytest_' not in row['path'] and 'synthetic_' not in row['path'],'fixture leaked into deployment')
        for p,h in validation['read_evidence_sha256'].items():same_hash(R/p,h)
        assert_(validation['read_evidence_sha256'][d['AUTHOR_INPUT']]==d['AUTHOR_SHA'],'wrong original author')
        assert_(validation['read_evidence_sha256'][AUDIT_REL]==d['INDEPENDENT_SHA'],'wrong original independent')
        return dict(deployment_files=len(rows),read_refs=len(validation['read_evidence_sha256']),frozen_sources=173)
    record('closure_identity_no_synthetic_deployment_or_root_hash_cycle',closure)
    def no_side_effects():
        assert_(not events,'audit observed forbidden operations')
        assert_(before=={rel:(R/rel).exists() for rel in before},'publication path changed')
        return dict(forbidden_operations=events,publication_paths_unchanged=len(before),actual_publications=0)
    record('all_guarded_runs_without_mutation_or_transport',no_side_effects)
    print(json.dumps(dict(checks=checks,validation=validation,read_evidence_sha256=read,denied_events=events),ensure_ascii=False))
    return 0 if all(x['passed'] for x in checks) else 1
def parent():
    started=time.monotonic()
    same_hash(C/'candidate_review.json',REVIEW_SHA)
    author=json.loads((C/'candidate_review.json').read_bytes())
    same_hash(ENTRY,ENTRY_SHA)
    def artifacts():
        for rel,item in author['files'].items():
            same_hash(C/rel,item['sha256'])
            assert_((C/rel).stat().st_size==item['bytes'],'artifact length differs')
        return dict(author_artifacts=len(author['files']))
    record('exact_author_artifacts_preserved',artifacts)
    def evidence():
        for name,checksum in author['read_evidence_sha256'].items():
            p=Path(name)
            assert_(any(p.is_relative_to(base) for base in (R,S,C)),'unexpected evidence location')
            same_hash(p,checksum)
        inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())
        assert_(len(inventory['files'])==173,'inventory count')
        for base in (R,S):
            for rel,checksum in inventory['files'].items():same_hash(base/rel,checksum)
        return dict(author_evidence=len(author['read_evidence_sha256']),frozen_source_count_per_root=173,roots=[str(R),str(S)])
    record('all_read_evidence_and_both_frozen_source_trees',evidence)
    def ast_scope():
        old=ast.parse((C/'legacy_entry.before.py.txt').read_bytes())
        new=ast.parse(ENTRY.read_bytes())
        oldf={x.name:ast.dump(x,include_attributes=False) for x in old.body if isinstance(x,ast.FunctionDef)}
        newf={x.name:ast.dump(x,include_attributes=False) for x in new.body if isinstance(x,ast.FunctionDef)}
        for name,val in oldf.items():
            if name!='main':assert_(newf[name]==val,'original helper modified '+name)
        def constants(tree):
            vals={}
            for n in tree.body:
                if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
                    vals[n.targets[0].id]=ast.dump(n.value,include_attributes=False)
            return vals
        oc,nc=constants(old),constants(new)
        for key,value in oc.items():
            if key not in {'ROOT','CHECK','SCRIPT_ARCHIVE'}:assert_(nc[key]==value,'nonstorage constant changed '+key)
        calls=[n for n in ast.walk(new) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess']
        assert_(len(calls)==1 and calls[0].func.attr=='run','new process call introduced')
        text=ENTRY.read_text()
        assert_("'--check-only']" in text and "'--submit'" not in text,'child mode changed')
        assert_("with path.open('xb')" in text and "require(not safe(rel).exists()" in text,'absence/exclusive creation lost')
        return dict(unchanged_original_helpers=len(oldf)-1,unchanged_original_constants=len(oc)-3,subprocess_calls_in_source=1,child_mode='check-only')
    record('AST_migration_scope_and_original_read_publication_gates',ast_scope)
    run=subprocess.run([sys.executable,'-B',str(Path(__file__).absolute()),'--guarded'],capture_output=True,timeout=90,cwd=O)
    with (O/'guarded_a2.stdout.json').open('xb') as f:f.write(run.stdout)
    with (O/'guarded_a2.stderr.log').open('xb') as f:f.write(run.stderr)
    child=json.loads(run.stdout) if run.stdout else {}
    checks.extend(child.get('checks',[]))
    read.update(child.get('read_evidence_sha256',{}))
    assert_(run.returncode==0 and run.stderr==b'','guarded child failed')
    def unchanged():
        for name,checksum in read.items():assert_(sha(name)==checksum,'input changed '+name)
        return dict(exact_read_paths=len(read))
    record('all_inputs_unchanged_after_independent_boundary_runs',unchanged)
    report=dict(schema='formal_main_v2',kind='action_GPU_v3_server_control_entry_migration_independent_CPU_review',
      version='action-gpu-v3-server-entry-independent-v1',
      status='passed_CPU_independent_migration_review_pending_root_integration' if all(x['passed'] for x in checks) else 'blocked',
      reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='root/server_v3_audit',
      candidate_review=dict(path=str(C/'candidate_review.json'),sha256=REVIEW_SHA),
      entry=dict(path=str(ENTRY),sha256=ENTRY_SHA),
      blockers=[x['name'] for x in checks if not x['passed']],checks=checks,
      tests=dict(total=len(checks),passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),seconds=time.monotonic()-started),
      source_scope='Only control-workspace entry and diagnostic modes; original eight GPU payloads, constructor, 173 frozen files in R and S, scientific settings and prior failures remain exact.',
      operations=dict(local_writes=0,real_control_repo_mutations=0,real_registration_publications=0,Git_mutations=0,Slurm_submissions=0,model_calls=0,sealed_state_reads=0,entry_subprocess_calls=0,auditor_guarded_child_processes=1),
      root_conditions=['Install exact reviewed entry bytes only at R/.local/action_execution_gpu_v3_root_integration_server_v1.py.',
        'Supply exact entry SHA and original v3 independent receipt SHA, then explicit --root-approve-cpu-registration after root acceptance.',
        'Require original submit.py --check-only to succeed and preserve outputs on any failure.',
        'Any subsequent Slurm dispatch remains a separate root transaction with an available slot and original identity/absence/single-attempt gates; no GPU acceptance is implied.'],
      audit_fixture_repair=dict(path=str(O/'audit_fixture_repair_a1.json'),sha256=sha(O/'audit_fixture_repair_a1.json')),
      limitations=['Actual publication branch was deliberately not executed; this review does not grant root approval or GPU acceptance.',
        'Read-only negative cases use in-memory module/path-response substitutions; no real evidence file was modified.',
        'Workspace metadata pins remain exact and will reject later drift.'],
      evidence=dict(driver=dict(path=str(Path(__file__).absolute()),sha256=sha(__file__)),
        stdout=dict(path=str(O/'guarded_a2.stdout.json'),sha256=sha(O/'guarded_a2.stdout.json')),
        stderr=dict(path=str(O/'guarded_a2.stderr.log'),sha256=sha(O/'guarded_a2.stderr.log'))),
      read_evidence_sha256=read)
    with (O/'independent_review.json').open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(status=report['status'],tests=report['tests'],blockers=report['blockers'],
      receipt=str(O/'independent_review.json'),sha256=sha(O/'independent_review.json')),ensure_ascii=False))
    return 0 if not report['blockers'] else 1
if __name__=='__main__':
    raise SystemExit(guarded() if '--guarded' in sys.argv else parent())
