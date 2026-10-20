"""Read-only CPU reproduction of the frozen candidate tests; not actual-P verification."""
from pathlib import Path
import hashlib,json,sys,types
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object_single_error_candidate_20261020T2253'
PINS={
 'fixed.py':'6766626cf072e9cff149e85a785ea8e8231f30cd8cd555ac4b2c14a8ed8a5bc2',
 'iterator.py':'24bc113599469ce6c95c66a9b9fc49f3f3f5261e10c08ab4e37b4a93ca8d597e',
 'gate.py':'2a016d86d9476dfc8798ed80d8be11c7efda01513096e28aacf91bef7d504bc4',
 'terminal.py':'39fc0c1f77599ee4db6ccf2512a4319fc528d25112c901fabd93fd012820eaba',
 'scope.json':'2d63670412abc28d3217242151ebf82f309ea93c1bb0e90478d817cf58d4a7b4',
 'test_cpu.py':'b370dbc10a78caf746e801394489913a8041aaef367b7db8dc5a1add4f1f3ec2',
 'cpu_tests.json':'cfc6993a1cb4b95714a3c75546acd204d5ccfdceb2e5b60a188d6ffd27d8ac95',
}
for rel,h in PINS.items():
 assert hashlib.sha256((D/rel).read_bytes()).hexdigest()==h,rel
module=types.ModuleType('_object_one_error_readonly_tests');module.__file__=str(D/'test_cpu.py')
exec(compile((D/'test_cpu.py').read_bytes(),str(D/'test_cpu.py'),'exec'),module.__dict__)
saved={};module.publish=lambda n,row:saved.__setitem__(n,row)
module.main()
assert saved['cpu_tests.json']==json.loads((D/'cpu_tests.json').read_text())
before=json.loads((D/'cpu_gate_fixtures.json').read_text())
after=saved['cpu_gate_fixtures.json']
before['all_modes_snapshot'].pop('captured_utc');after['all_modes_snapshot'].pop('captured_utc')
assert before==after
for rel,h in PINS.items():assert hashlib.sha256((D/rel).read_bytes()).hexdigest()==h
print(json.dumps(dict(status='passed_readonly_CPU_reproduction',positive=24,negative=74,changed_project_files=0,
 new_scientific_trials=0,GPU_calls=0,actual_P_verified=False,production_admitted=False)))
