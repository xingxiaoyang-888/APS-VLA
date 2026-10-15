"""Server CPU-only: bind every timing instance to its actual selected checkpoint."""
from pathlib import Path
import hashlib,importlib.util,json,sys
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/g1_future_long_k64_v1';R=P/'results/g1_future_long_k64_v1'
sys.path.insert(0,str(S/'src'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
reg_path=S/'configs/experiments/g1_future_long_k64_v1.json';reg=json.loads(reg_path.read_text())
rows=[{'name':'dense'}]
for budget in (128,64):
    for seed in (17,23,41):
        if budget==64:
            source=S;run=R/f'seed{seed}';gate=R/'acceptance/f01_acceptance.json';inventory=S/'source_manifest.json'
        elif seed==17:
            source=P/'snapshots/g1_future_long_v1';run=P/'results/g1_future_long_v1'
            gate=run/'acceptance/f01_acceptance.json';inventory=R/'references/parent_source_inventory.json'
        else:
            source=P/'snapshots/g1_future_long_multiseed_v1';run=P/f'results/g1_future_long_multiseed_v1/seed{seed}'
            gate=P/'results/g1_future_long_v1/acceptance/f01_acceptance.json';inventory=R/'references/multiseed_source_inventory.json'
        for arm in ('A','B'):
            receipt_path=run/f'training/{arm}/deployment_receipt.json';receipt=json.loads(receipt_path.read_text())
            report=json.loads((run/f'training/{arm}/training_report.json').read_text())
            checkpoint=Path(report['best_checkpoint'])
            assert sha(checkpoint)==receipt['checkpoint_sha256']==report['best_checkpoint_sha256']
            rows.append({'name':f'{arm}{budget}_seed{seed}','seed':seed,'total_tokens':budget,
                'source_root':str(source),'checkpoint':ref(checkpoint),'receipt':ref(receipt_path),
                'f01_report':ref(gate),'input_acceptance':ref(P/'results/g1_future_long_v1/inputs/input_acceptance.json'),
                'source_inventory':ref(inventory)})
assert [x['name'] for x in rows]==reg['profiling']['method_names']
path=R/'profile_methods.json';assert not path.exists(),'Do not overwrite registered identities'
candidate=path.with_suffix('.json.candidate');assert not candidate.exists()
candidate.write_text(json.dumps({'version':'long-o2a-13-deployments-v1','registration_sha256':sha(reg_path),
    'methods':rows},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('bound_long_profiler',S/'scripts/profile_long_future_observation_to_action.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.method_specs(candidate,reg_path)
candidate.replace(path)
print(json.dumps({'status':'registered','instances':len(rows),'methods_sha256':sha(path),'GPU_calls':0,'checkpoints_copied':False}))
