from pathlib import Path
import hashlib,sys
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_production_20261020T2358')
p=D/'verify_cpu.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='13f5828abd2f311b4afe68dc733dd1ede4a9f3d46caf1af8a7e686ed54483614'
sys.path.insert(0,str(D))
import verify_cpu
sys.argv=['verify_cpu.py','--report','cpu_attempt01.json']
verify_cpu.main()
