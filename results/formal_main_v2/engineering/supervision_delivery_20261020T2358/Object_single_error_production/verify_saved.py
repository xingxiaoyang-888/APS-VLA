from pathlib import Path
import hashlib,sys
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_production_20261020T2358')
p=D/'verify_cpu.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='011b7ee6b9542ab9f79db576ddc004ae4d3321d78bbe347f17098dbf46d08956'
sys.path.insert(0,str(D))
import verify_cpu
sys.argv=['verify_cpu.py','--verify-saved','cpu_final.json']
verify_cpu.main()
