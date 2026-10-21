from pathlib import Path
import hashlib,sys
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_production_20261020T2358')
p=D/'verify_cpu.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='8d3bae103adc5518e188b79873d3fd482c7019b749ece88dac95d395f725741f'
sys.path.insert(0,str(D))
import verify_cpu
sys.argv=['verify_cpu.py','--report','cpu_attempt02.json']
verify_cpu.main()
