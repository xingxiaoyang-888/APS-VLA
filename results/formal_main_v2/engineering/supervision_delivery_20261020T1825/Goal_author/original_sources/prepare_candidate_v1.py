"""Read-only original preparation plus private receipt. No GPU execution entry.

This v1 candidate intentionally cannot launch or execute a real attempt. Root
must separately review an original-chain runner and bounded admission before a
future GPU job. --execute always rejects before reading inputs or allocating.
"""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).parent
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T1644/Goal_t0_forensic'
ORIGINAL=P/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json'
PIN='c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803'
PREFIX_PIN='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28'
WRAPPER_PIN='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'
LEGACY_PIN='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def load(path,name,expected):
    if sha(path)!=expected:raise ValueError('source pin differs: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--report-name',default='prepare_v1.json')
    opts=parser.parse_args(argv)
    if opts.execute:raise RuntimeError('GPU execution is not implemented or authorized by this CPU-only candidate')
    name=Path(opts.report_name)
    if name.name!=opts.report_name or name.suffix!='.json':raise ValueError('private receipt basename only')
    output=D/name
    if output.exists():raise FileExistsError('retain existing preparation receipt')
    if sha(ORIGINAL)!=PIN or sha(E/'original_prefix58.json')!=PREFIX_PIN:raise ValueError('original fixed inputs changed')
    invocation=json.loads(ORIGINAL.read_text())
    wrapper=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','prefix58_prepare_original_wrapper',WRAPPER_PIN)
    context=wrapper.verify(invocation,project=P)
    legacy=load(P/'scripts/ops/formal_evaluation_adapter.py','prefix58_prepare_original_adapter',LEGACY_PIN)
    args=copy.deepcopy(context['args']);args.prepare_only=True
    prepared=legacy.run(args,mode='evaluate',source_root=S,source_inventory=Path(invocation['source_inventory']),
                        adapter_sha256=LEGACY_PIN,resume=False)
    if prepared.get('gpu_calls')!=0 or prepared.get('test_opened') is not False:raise ValueError('not CPU-only development preparation')
    with legacy.source_imports(S):
        from cti_vla.evaluation import formal_trials
        original_panel=json.loads((P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json').read_text())
        current=json.loads(args.development_panel.read_text())
        if original_panel!=current:raise ValueError('original development panel content changed')
        prefix=json.loads((E/'original_prefix58.json').read_text())['rows']
        keys=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')
        actual=[{k:v for k,v in formal_trials._identity(current,state,mid).items() if k in keys}
                for state in current['states'] for mid in invocation['method_ids']][:58]
        if actual!=[{k:row[k] for k in keys} for row in prefix]:raise ValueError('original first58 no longer exact')
    cuda=sys.modules.get('torch.cuda')
    if cuda is not None and cuda.__dict__.get('_initialized'):raise ValueError('unexpected CUDA initialization in preparation')
    selected=context['original_plan']['invocation']
    report=dict(schema='formal_main_v2',kind='goal_prefix58_CPU_preparation',status='passed_CPU_preparation_only',
                original_invocation=dict(path=str(ORIGINAL),sha256=PIN),
                original_prefix=dict(path=str(E/'original_prefix58.json'),sha256=PREFIX_PIN),
                original_entrypoint=invocation['entrypoint'],original_wrapper_sha256=WRAPPER_PIN,
                source_sha256=invocation['source_sha256'],original_prepare_result=prepared,
                original_argument_changes_for_this_check={'prepare_only':True},
                proposed_future_argument_changes_only=['output: fresh engineering subtree','stop_after:58'],
                exact_prefix_identities=actual,unique_development_states=29,CPU_only=True,GPU_calls=0,
                scientific_trials_added=0,Goal_scientific_HOLD_unchanged=True,
                actual_GPU_entry_implemented=False,actual_GPU_authorized=False,
                missing_before_GPU=['independent observer/AST code audit','reviewed original-chain GPU runner with one-attempt admission',
                                    'root engineering authorization and <=8 GPU capacity accounting','real bounded engineering observation'])
    with output.open('x') as f:json.dump(report,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'status':report['status'],'GPU_calls':0,'prefix_trials':58,'report_sha256':sha(output)}))
    return report
if __name__=='__main__':main()
