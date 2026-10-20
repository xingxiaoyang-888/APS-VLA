"""CPU-only proof against real frozen loop code with deterministic fake env/policy."""
from __future__ import annotations
import ast,copy,hashlib,importlib.util,json,random,sys,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np

R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).parent
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T1644/Goal_t0_forensic'
checks=[];evidence={}

def ck(name,condition,detail=None):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    if not condition: raise AssertionError(name)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def run():
    observer=load(D/'observer_v2.py','prefix58_observer_cpu')
    adapter=load(D/'ast_observer.py','prefix58_ast_cpu')
    ck('candidate_numpy_no_GPU_init',not ('torch.cuda' in sys.modules and sys.modules['torch.cuda'].__dict__.get('_initialized')))
    frozen=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
    for root in (R,S):
        ck('all173_intact_'+root.name,len(frozen['files'])==173 and all(sha(root/k)==v for k,v in frozen['files'].items()))
    prefix_file=E/'original_prefix58.json'
    ck('original_prefix_pin',sha(prefix_file)=='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28')
    prefix=json.loads(prefix_file.read_text())['rows']
    sys.path.insert(0,str(S/'src'))
    from cti_vla.evaluation import libero_runtime as runtime,formal_trials as trials
    accepted=load(P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','accepted_action_cpu')
    ck('original_sources',sha(runtime.__file__)==adapter.RUNTIME_SHA and sha(trials.__file__)==adapter.TRIALS_SHA)
    accepted_tree,instrumented_tree,run_proof=adapter.derive_run(Path(runtime.__file__).read_bytes())
    original_trials,derived_trials,trial_proof=adapter.derive_trials(Path(trials.__file__).read_bytes())
    write(D/'ast_proof.json',dict(run_episode=run_proof,evaluate_formal_trials=trial_proof))
    (D/'instrumented_run_episode.py.txt').write_text(ast.unparse(instrumented_tree)+'\n')
    (D/'instrumented_evaluate_formal_trials.py.txt').write_text(ast.unparse(derived_trials)+'\n')
    ck('AST_projection_run',run_proof['original_ast_sha256']==run_proof['stripped_ast_sha256'])
    ck('AST_projection_trials',trial_proof['original_ast_sha256']==trial_proof['stripped_ast_sha256'])
    ck('original_call_sequence_run',run_proof['original_calls']==run_proof['projected_calls'])
    ck('original_call_sequence_trials',trial_proof['original_calls']==trial_proof['projected_calls'])
    for mut in ('extra_step','extra_render','extra_random','timer_moved','query_change','reset_change'):
        bad=copy.deepcopy(instrumented_tree)
        if mut=='extra_step':bad.body.append(ast.parse('env.step([0]*7)').body[0])
        elif mut=='extra_render':bad.body.append(ast.parse('env.render()').body[0])
        elif mut=='extra_random':bad.body.append(ast.parse('np.random.random()').body[0])
        elif mut=='timer_moved':
            n=next(x for x in ast.walk(bad) if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='query_started')
            n.value=ast.Constant(value=0.0)
        elif mut=='query_change':
            n=next(x for x in ast.walk(bad) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='predict_chunk')
            n.args.reverse()
        else:
            n=next(x for x in ast.walk(bad) if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id==adapter.TEMP)
            n.value=ast.parse('env.reset(1)',mode='eval').body
        try: adapter.assert_projection(accepted_tree,bad)
        except ValueError: ck('reject_AST_'+mut,True)
        else: ck('reject_AST_'+mut,False)
    class FakeEnv:
        def __init__(self,trace):
            self.trace=trace;self.n=0
            native=SimpleNamespace(time=0.,**{k:np.zeros((3,),dtype=np.float64) for k in observer.SIM_FIELDS})
            self.env=SimpleNamespace(sim=SimpleNamespace(data=native),timestep=0,np_random=np.random.RandomState(81))
        def observation(self):
            x=self.n
            return dict(agentview_image=np.full((3,4,3),x,dtype=np.uint8),
                        robot0_eye_in_hand_image=np.full((3,4,3),x+1,dtype=np.uint8),
                        robot0_eef_pos=np.array([x,1,2],dtype=np.float64),
                        robot0_eef_quat=np.array([0,0,0,1.],dtype=np.float64),
                        robot0_gripper_qpos=np.array([.1,.2],dtype=np.float64),
                        unrelated=np.array([x,123],dtype=np.int64))
        def reset(self):self.trace.append(('reset',));self.n=0;return self.observation()
        def set_init_state(self,state):
            self.trace.append(('set_init_state',state.dtype.str,state.tobytes().hex()));return self.observation()
        def step(self,action):
            self.trace.append(('step',tuple(action)));self.n+=1
            self.env.timestep=self.n;self.env.sim.data.time=float(self.n)
            self.env.sim.data.qpos[:]=self.n
            return self.observation(),0.,self.n==27,{}
        def close(self):self.trace.append(('close',))
        def render(self):raise AssertionError('observer requested rendering')
        def get_sim_state(self):raise AssertionError('observer requested simulator getter')
    class FakePolicy:
        def __init__(self,trace):self.trace=trace;self.calls=0
        def reset(self):self.trace.append(('policy_reset',));self.calls=0
        def __call__(self,obs,instruction):
            self.calls+=1;self.trace.append(('query',runtime._observation_hash(obs),instruction))
            # Values beyond one confirm accepted action semantics were preserved.
            a=np.full((8,7),1.5+np.random.uniform(0,0.01)+random.random()/100)
            return runtime.PolicyChunk(a,a,{'fixture':True,'call':self.calls})
    def canonical_result(result):
        result=copy.deepcopy(result);result.pop('wall_seconds',None)
        for chunk in result['chunks']:chunk.pop('engineering_seconds',None)
        return result
    emitted=[]
    def emit(event,**fields):emitted.append(dict(event=event,**fields))
    original_run=runtime.run_episode;original_trial=trials.evaluate_formal_trials
    with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,
                formal_trials_module=trials,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=emit):
        active=runtime.run_episode
        random.seed(117);np.random.seed(117);before=observer.global_rng()
        trace1=[];e1=FakeEnv(trace1);p1=FakePolicy(trace1)
        baseline=runtime.run_episode(e1,p1,'same instruction',[0.,1.,2.],wait_steps=10,max_steps=300)
        rng1=observer.global_rng()
        random.seed(117);np.random.seed(117)
        trace2=[];e2=FakeEnv(trace2);p2=FakePolicy(trace2)
        ob=observer.PassiveObserver(D/'cpu_episode',prefix,allow_cpu_fixture=True)
        ob.current={k:prefix[0][k] for k in observer.IDENTITY_KEYS};ob.begun=1
        with adapter.observer_scope(runtime,trials,ob,emit=emit):
            instrumented=runtime.run_episode(e2,p2,'same instruction',[0.,1.,2.],wait_steps=10,max_steps=300)
        rng2=observer.global_rng()
        ck('exact_original_closed_loop_trace',trace1==trace2)
        ck('exact_original_episode_output_except_wall_timers',canonical_result(baseline)==canonical_result(instrumented))
        ck('same_final_RNG',rng1==rng2)
        ck('same_policy_calls_wait_controls',instrumented['policy_calls']==3 and instrumented['wait_steps']==10 and instrumented['control_steps']==17)
        ck('unclipped_original_actions',instrumented['executed_actions'][0][0]>1.)
        ck('accepted_action_restored_after_observer',runtime.run_episode is active and trials.run_episode is active)
        events=[json.loads(l) for l in ob.journal.read_text().splitlines()]
        phases=[r['phase'] for r in events]
        ck('capture_counts',len(events)==26 and phases[:4]==['reset_before','reset_after','set_init_before','set_init_after']
           and phases.count('wait_before')==phases.count('wait_after')==10
           and phases[-2:]==['t0_query_before','t0_query_after'])
        ck('five_arrays_recorded_when_available',all(set(r['observation_arrays'])==set(observer.OBS_KEYS) for r in events[1:]))
        ck('actual_hash_matches_original',events[-1]['observation_sha256']==instrumented['chunks'][0]['observation_sha256'])
        ck('sim_read_passive_route',all('fields' in r['sim'] for r in events))
        for i,r in enumerate(events):
            ck('object_rng_sim_unchanged_'+str(i),all(r['invariants'].values()))
            for key,m in r['observation_arrays'].items():
                raw=(ob.output/m['blob']['path']).read_bytes()
                ck('blob_reconstruct_'+str(i)+'_'+key,hashlib.sha256(raw).hexdigest()==m['sha256']
                   and np.frombuffer(raw,dtype=m['dtype']).reshape(m['shape']).size>0)
        # Real frozen trial loop: use exact original development panel identities,
        # but fake env/policy and an isolated original TrialLedger. No simulator import.
        panel=json.loads((P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json').read_text())
        ledger=runtime.TrialLedger(D/'cpu_trials.jsonl',run_signature='a'*64)
        trace=[];policies={name:FakePolicy(trace) for name in ['A256_seed17','B256_seed17']}
        def reseed():random.seed(17);np.random.seed(17);trace.append(('reseed',))
        def factory(state):trace.append(('factory',state['task_id'],state['source_state_index']));return FakeEnv(trace),'instruction'
        ob2=observer.PassiveObserver(D/'cpu_prefix58',prefix,allow_cpu_fixture=True)
        with adapter.observer_scope(runtime,trials,ob2,emit=emit):
            count=trials.evaluate_formal_trials(panel,policies,ledger,factory,reseed=reseed,stop_after=58)
        done=ob2.finish()
        terminal=[r for r in ledger.events if r.get('event')=='result']
        ck('58_exact_original_order',count==58 and len(terminal)==58
           and [r['trial_id'] for r in terminal]==[r['trial_id'] for r in prefix])
        ck('29_unique_development_states',len({r['state_trial_id'] for r in terminal})==29)
        ck('original_2_methods',set(r['method'] for r in terminal)=={'A256_seed17','B256_seed17'})
        ck('original_policy_actions_not_replayed',all(len(r['executed_actions'])==17 and r['policy_calls']==3 for r in terminal))
        ck('bounded_complete_no_scientific_admission',done['scientific_trials_added']==0 and done['Goal_scientific_HOLD_unchanged'])
        # False/missing instrumentation must fail, not silently produce a pass.
        def expect_abort(name,fn):
            try:fn()
            except (observer.ObserverAbort,ValueError):ck(name,True)
            else:ck(name,False)
        wrong=copy.deepcopy(prefix);wrong[0],wrong[1]=wrong[1],wrong[0]
        ob_bad=observer.PassiveObserver(D/'cpu_wrong_order',wrong,allow_cpu_fixture=True)
        expect_abort('reject_changed_prefix_order',lambda:ob_bad.trial_begin(trials._identity(panel,panel['states'][0],'A256_seed17'),panel['states'][0]))
        for kind in ('numpy_rng','python_rng','observation_bytes','observation_identity','sim'):
            env=FakeEnv([]);obs=env.observation()
            def sink(event,kind=kind):
                if kind=='numpy_rng':np.random.random()
                elif kind=='python_rng':random.random()
                elif kind=='observation_bytes':obs['agentview_image'][0,0,0]+=1
                elif kind=='observation_identity':obs['agentview_image']=obs['agentview_image'].copy()
                else:env.env.sim.data.qpos[0]+=1
            bad=observer.PassiveObserver(D/('cpu_mutation_'+kind),prefix,allow_cpu_fixture=True,sink=sink)
            expect_abort('reject_observer_mutation_'+kind,lambda:bad.capture('sentinel',env,obs))
            ck('mutation_fail_stop_'+kind,bad.dead)
            expect_abort('reject_retry_'+kind,lambda:bad.capture('sentinel',env,obs))
        # An unrecognized simulator getter is never evaluated.
        class Unreadable:
            @property
            def sim(self):raise AssertionError('opaque sim property must not be called')
        data,blobs=observer.passive_environment(Unreadable())
        ck('opaque_sim_reported_missing',bool(data.get('missing')) and not blobs)
        # A policy exception causes one retained failure and then fail-stop.
        class BadPolicy(FakePolicy):
            def __call__(self,obs,instruction):self.trace.append(('bad_query',));raise RuntimeError('synthetic policy exception')
        failledger=runtime.TrialLedger(D/'cpu_failure_trials.jsonl',run_signature='b'*64)
        ob_fail=observer.PassiveObserver(D/'cpu_failure_observer',prefix,allow_cpu_fixture=True)
        failtrace=[]
        with adapter.observer_scope(runtime,trials,ob_fail,emit=emit):
            expect_abort('policy_exception_aborts_prefix',lambda:trials.evaluate_formal_trials(panel,
                         {'A256_seed17':BadPolicy(failtrace),'B256_seed17':FakePolicy(failtrace)},
                         failledger,lambda state:(FakeEnv(failtrace),'instruction'),reseed=reseed,stop_after=58))
        rows=[r for r in failledger.events if r.get('event')=='result']
        ck('one_failure_no_retry',len(rows)==1 and rows[0]['status']=='policy_error'
           and sum(x[0]=='bad_query' for x in failtrace)==1)
    ck('original_bindings_restored',runtime.run_episode is original_run and trials.evaluate_formal_trials is original_trial)
    ck('no_GPU_initialization',sys.modules['torch.cuda'].__dict__.get('_initialized') is False)
    for root in (R,S):ck('all173_still_intact_'+root.name,all(sha(root/k)==v for k,v in frozen['files'].items()))
    evidence.update(scope_events=emitted,synthetic_prefix=done,baseline_trace_sha256=hashlib.sha256(repr(trace1).encode()).hexdigest(),
                    original_source_inputs_unchanged=True,GPU_calls=0,simulator_imported=False,
                    cpu_only=True,scientific_trials_added=0)
    write(D/'cpu_evidence.json',evidence)
    return dict(status='passed_CPU_candidate_only',checks=checks,passed=len(checks),GPU_calls=0,
                real_environment_accepted=False,scientific_trials_added=0,
                Goal_scientific_HOLD_unchanged=True)

if __name__=='__main__':
    try:report=run()
    except BaseException as e:
        report=dict(status='failed_CPU',checks=checks,error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),
                    GPU_calls=0,scientific_trials_added=0)
        write(D/'cpu_report_v1.json',report);print(json.dumps({k:report[k] for k in ['status','error_type','error']}));raise
    write(D/'cpu_report_v1.json',report);print(json.dumps({k:report[k] for k in ['status','passed','GPU_calls']}))
