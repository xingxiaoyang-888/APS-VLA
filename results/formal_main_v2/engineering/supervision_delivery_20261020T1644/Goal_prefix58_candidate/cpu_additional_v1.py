"""Additional RNG/AST and no-GPU-entry negative sentinels. CPU only."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from types import ModuleType,SimpleNamespace
import numpy as np
D=Path(__file__).parent
E=D.parents[1]/'results/formal_main_v2/engineering/supervision_delivery_20261020T1644/Goal_t0_forensic'
checks=[]
def ck(name,value):
    checks.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def run():
    ob=load(D/'observer_v2.py','prefix58_extra_observer')
    prep=load(D/'prepare_candidate_v1.py','prefix58_extra_prepare')
    prefix=json.loads((E/'original_prefix58.json').read_text())['rows']
    actual_torch=sys.modules.get('torch');actual_cuda=sys.modules.get('torch.cuda')
    calls=[]
    class State:
        device=SimpleNamespace(type='cpu');dtype='torch.uint8'
        def __init__(self,arr):self.arr=arr.copy()
        def numpy(self):calls.append('state_numpy');return self.arr
    class Generator:
        def __init__(self,label):self.label=label;self.value=np.arange(8,dtype=np.uint8)
        def get_state(self):calls.append('readonly_'+self.label);return State(self.value)
        def seed(self):raise AssertionError('observer called seed')
    torch=ModuleType('torch');cuda=ModuleType('torch.cuda')
    cpu_gen=Generator('CPU');cuda_gen=Generator('CUDA')
    torch.default_generator=cpu_gen;cuda._initialized=True;cuda.default_generators=(cuda_gen,)
    def forbidden(*a,**k):raise AssertionError('observer initialized/synchronized/drew CUDA state')
    for k in ('synchronize','_lazy_init','current_device','get_rng_state','get_rng_state_all','manual_seed','seed','random'):
        setattr(cuda,k,forbidden)
    try:
        sys.modules['torch']=torch;sys.modules['torch.cuda']=cuda
        observer=ob.PassiveObserver(D/'cpu_extra_rng',prefix,allow_cpu_fixture=True)
        observer.capture('already_initialized_generators')
        ck('already_initialized_CPU_CUDA_readonly_generators',calls.count('readonly_CPU')==calls.count('readonly_CUDA')==3)
        ck('getstate_copied_without_mutation',np.array_equal(cpu_gen.value,np.arange(8,dtype=np.uint8))
           and np.array_equal(cuda_gen.value,np.arange(8,dtype=np.uint8)))
        for which in ('CPU','CUDA'):
            gen=cpu_gen if which=='CPU' else cuda_gen
            def mutate(event,gen=gen):gen.value[0]+=1
            negative=ob.PassiveObserver(D/('cpu_extra_mutated_'+which),prefix,allow_cpu_fixture=True,sink=mutate)
            try:negative.capture('mutation')
            except ob.ObserverAbort:ck('detect_'+which+'_RNG_state_mutation',negative.dead)
            else:ck('detect_'+which+'_RNG_state_mutation',False)
        cuda._initialized=False;calls.clear()
        value=ob.global_rng()
        ck('uninitialized_CUDA_is_missing_never_initialized','missing' in value['torch_cuda'] and calls==['readonly_CPU','state_numpy'])
    finally:
        if actual_torch is None:sys.modules.pop('torch',None)
        else:sys.modules['torch']=actual_torch
        if actual_cuda is None:sys.modules.pop('torch.cuda',None)
        else:sys.modules['torch.cuda']=actual_cuda
    before=set(D.rglob('*'))
    try:prep.main(['--execute'])
    except RuntimeError as e:ck('GPU_entry_rejects_before_any_work','not implemented or authorized' in str(e))
    else:ck('GPU_entry_rejects_before_any_work',False)
    ck('rejected_GPU_entry_created_no_files',set(D.rglob('*'))==before)
    # Unknown simulator property is not inspected through a fallback.
    class Unknown:
        @property
        def sim(self):raise AssertionError('getter must not execute')
    meta,raw=ob.passive_environment(Unknown())
    ck('opaque_sim_getter_not_called',bool(meta.get('missing')) and not raw)
    report={'status':'passed_additional_CPU_sentinels_only','checks':checks,'passed':len(checks),'GPU_calls':0,
            'real_CUDA_generator_tested':False,'CUDA_branch_fixture_only':True,'scientific_trials_added':0}
    with (D/'cpu_additional_v1.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({k:report[k] for k in ['status','passed','GPU_calls']}))
if __name__=='__main__':run()
