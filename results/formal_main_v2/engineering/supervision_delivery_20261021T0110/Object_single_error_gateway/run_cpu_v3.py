from pathlib import Path
import hashlib,runpy,sys
p=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_gateway_20261021T0110/verify_cpu.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='3924a950e3d8907561422c0bb3b944102745d601c543030f46a8b0cd50aaba9c'
sys.argv=[str(p),'--capture-live']
runpy.run_path(str(p),run_name='__main__')
