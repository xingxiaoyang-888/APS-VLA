from pathlib import Path
import subprocess,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;PY='/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python'
reports=[]
for row in json.loads((D/'test_path_derivations.json').read_bytes()):
 p=D/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['derived_sha256']
 ans=subprocess.run([PY,'-B',str(p)],capture_output=True,text=True,timeout=240)
 out={'path':row['path'],'returncode':ans.returncode,'stdout':ans.stdout,'stderr':ans.stderr,'CPU_only':True}
 with (D/(row['path']+'.execution.json')).open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps({'test':row['path'],'returncode':ans.returncode}),flush=True)
 if ans.returncode!=0:raise RuntimeError('Independent CPU test failed: '+row['path'])
 reports.append(out)
with (D/'CPU_replay_execution.json').open('x') as f:json.dump(reports,f,indent=2);f.write('\n')
