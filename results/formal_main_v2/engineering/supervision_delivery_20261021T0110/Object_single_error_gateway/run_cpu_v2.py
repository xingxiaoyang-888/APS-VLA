from pathlib import Path
import hashlib,runpy,sys
p=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_gateway_20261021T0110/verify_cpu.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f51bc38716d844bd059782c80ece74767d090b31018a75e0360cf52dfeee0cbf'
sys.argv=[str(p),'--capture-live']
runpy.run_path(str(p),run_name='__main__')
