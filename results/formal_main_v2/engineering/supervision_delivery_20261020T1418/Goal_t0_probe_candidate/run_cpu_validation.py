from pathlib import Path
import hashlib,json,subprocess,sys,traceback
D=Path(__file__).resolve().parent
result=[]
for name,argv in [('CPU_synthetic',[sys.executable,'-B',str(D/'test_cpu.py')]),('actual_metadata_prepare',[sys.executable,'-B',str(D/'probe.py'),'--config',str(D/'config.json'),'--config-sha256',hashlib.sha256((D/'config.json').read_bytes()).hexdigest()])]:
    p=subprocess.run(argv,capture_output=True,text=True,cwd=D,timeout=180)
    (D/(name+'.stdout.log')).write_text(p.stdout);(D/(name+'.stderr.log')).write_text(p.stderr)
    result.append(dict(name=name,returncode=p.returncode))
    print(json.dumps(result[-1]),flush=True)
with (D/'validation_runs.json').open('x') as f:json.dump(result,f,indent=2)
if any(v['returncode']!=0 for v in result):raise SystemExit(1)
