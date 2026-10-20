from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent
p=subprocess.run(['bash','-n',str(D/'candidate.slurm')],capture_output=True,text=True)
(D/'slurm_syntax.stdout.log').write_text(p.stdout);(D/'slurm_syntax.stderr.log').write_text(p.stderr)
if p.returncode:raise SystemExit(p.returncode)
# Compile without bytecode; never import the GPU runner here.
for name in ['probe.py','original_loading_prefix.py','test_cpu.py']:
    compile((D/name).read_bytes(),str(D/name),'exec')
result=dict(status='passed',kind='static_candidate_only',slurm_syntax=True,compiled_without_pycache=True,GPU_run=False,Slurm_submitted=False)
with (D/'static_validation.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
