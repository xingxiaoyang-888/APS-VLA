import json,sys,subprocess,time
from pathlib import Path
D=Path(__file__).resolve().parent
cmd=[sys.executable,"-B","-m","pytest",str(D/"test_candidate.py"),"--basetemp="+str(D/"pytest_temp_a1"),"--junitxml="+str(D/"tests_a1.xml"),"-q"]
(D/"tests_a1.command.json").open("x").write(json.dumps(cmd)+"\n")
t=time.monotonic()
with (D/"tests_a1.log").open("x") as f:
    p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=D)
print((D/"tests_a1.log").read_text());print(json.dumps({"returncode":p.returncode,"elapsed_seconds":time.monotonic()-t}))
raise SystemExit(p.returncode)
