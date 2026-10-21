from pathlib import Path
import hashlib,runpy,sys
p=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_gateway_20261021T0110/verify_cpu.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='21149d9e50067520598de510c7f1e2c4b225279cec2e7ad7f7e86b3c1f120340'
sys.argv=[str(p),'--verify-saved']
runpy.run_path(str(p),run_name='__main__')
