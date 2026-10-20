"""Re-run all proof checks without replacing saved results; CPU only."""
from pathlib import Path
import importlib.util,sys,json,hashlib
D=Path(__file__).parent
p=D/'prove_spatial12.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='c317201fb17b12e910eb560b8d908667763e025dea5483317a995f89e0183ea3'
s=importlib.util.spec_from_file_location('_spatial12_rerun',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
def verify(name,value,jsonl=False):
 p=D/name
 raw=p.read_bytes();actual=[json.loads(l) for l in raw.splitlines()] if jsonl else json.loads(raw)
 if name=='report.json':
  actual={k:v for k,v in actual.items() if k!='duration_seconds'};value={k:v for k,v in value.items() if k!='duration_seconds'}
 assert actual==value,'saved proof changes '+name
 return dict(path=p.relative_to(m.R).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
m.save=verify
m.main()
