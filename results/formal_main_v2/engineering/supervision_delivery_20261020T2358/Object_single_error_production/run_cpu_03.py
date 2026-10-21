from pathlib import Path
import hashlib,sys
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_production_20261020T2358')
p=D/'verify_cpu.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='16df4b3b55de86ad7511785bc3113188989e6c1c2e64e794a17ec8bd5359540c'
sys.path.insert(0,str(D))
import verify_cpu
sys.argv=['verify_cpu.py','--report','cpu_attempt03.json']
verify_cpu.main()
