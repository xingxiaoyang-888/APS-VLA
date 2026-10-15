"""Install one reviewed snapshot and register read-only parent cache inheritance."""
from pathlib import Path
import json,shlex,subprocess
r=Path('F:/CTI-VLA');experiment='g1_future_long_k64_v1'
P='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA';S=P+'/snapshots/'+experiment;R=P+'/results/'+experiment
OLD=P+'/snapshots/g1_future_long_v1';PY='/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python'
ssh=['ssh','-o','BatchMode=yes','tongji-cvpr'];scp=['scp','-q','-o','BatchMode=yes']
def run(cmd):
    value=subprocess.run(cmd,capture_output=True,text=True)
    if value.returncode:raise RuntimeError(value.stdout+value.stderr)
    return value.stdout
assert (r/'.local/g1_future_long_k64_v1.tar.gz').is_file()
run(scp+[str(r/'.local/g1_future_long_k64_v1.tar.gz'),str(r/'.local/install_long_k64_snapshot.py'),'tongji-cvpr:'+P+'/.local/'])
print(run(ssh+[PY+' '+shlex.quote(P+'/.local/install_long_k64_snapshot.py')]))
run(ssh+['mkdir -p '+shlex.quote(R+'/references')+' '+shlex.quote(R+'/seed17')+' '+shlex.quote(R+'/seed23')+' '+shlex.quote(R+'/seed41')])
for src,name in [('results/g1_future_long/source_g1_future_long_v1.json','parent_source_inventory.json'),
                 ('results/g1_future_long_multiseed_v1/source_g1_future_long_multiseed_v1.json','multiseed_source_inventory.json')]:
    run(scp+[str(r/src),'tongji-cvpr:'+R+'/references/'+name])
for script in ('g1_future_long_k64.slurm','g1_future_long_profile.slurm'):
    run(ssh+['bash -n '+shlex.quote(S+'/scripts/server/'+script)])
for seed in (17,23,41):
    args={'project-root':P,'source-root':S,'parent-run':P+'/results/g1_future_long_v1',
        'parent-config':OLD+'/configs/experiments/g1_future_long_v1.json',
        'parent-source-inventory':R+'/references/parent_source_inventory.json',
        'parent-runner':OLD+'/scripts/run_g1_future.py',
        'target-config':S+f'/configs/experiments/g1_future_long_k64_seed{seed}_v1.json',
        'windows':S+'/configs/manifests/long_future_v1/windows.json',
        'protocol':S+'/configs/manifests/long_future_v1/protocol.json',
        'asset-manifest':S+'/configs/assets/openvla_oft_libero_long.json',
        'output':R+f'/seed{seed}/budget_reuse_registration.json'}
    command='PYTHONPATH='+shlex.quote(S+'/src')+' PYTHONDONTWRITEBYTECODE=1 '+PY+' '+shlex.quote(S+'/scripts/register_long_budget_reuse.py')+' '+ ' '.join('--'+key+' '+shlex.quote(value) for key,value in args.items())
    print(run(ssh+[command]))
    local=r/f'results/{experiment}/seed{seed}';local.mkdir(exist_ok=True)
    run(scp+['tongji-cvpr:'+args['output'],str(local/'budget_reuse_registration.json')])
print('New frozen source and all3 explicit input/cache contracts installed; no GPU jobs yet')
