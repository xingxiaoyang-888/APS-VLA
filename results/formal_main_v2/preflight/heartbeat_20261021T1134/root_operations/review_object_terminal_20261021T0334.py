from pathlib import Path
import hashlib,json,sys,importlib.util,traceback,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
assert h(R/'scripts/ops/formal_object_single_error_v1/reviewer.py')=='c0aa1fc3d7c1607032897d7eede009bb989753daf58911d2b3351b4df7a030a2'
sys.path.insert(0,str(R/'scripts/ops/formal_object_single_error_v1'))
import reviewer
st=R/B/'terminal_analysis_supervisor_projection.json';assert h(st)=='28972a53a01b3bf21e7c2194fe8b7fd31106fd49ed47290beb1a4f871d363513'
pull='results/formal_main_v2/pulls/terminal_object_20261021T0334/receipt.json'
assert h(R/pull)=='1ab834c09cc562f4fce9224bf98bc6c80d31dbaadcb6a3381c877c1395aad710'
try:
 out=reviewer.review('3054409',pull,project=R,state=json.loads(st.read_text()))
 reviewer.consume(out,job_id='3054409',pull_receipt=pull,project=R,state=json.loads(st.read_text()))
 name='Object_original_terminal_review.json'
except BaseException as e:
 out=dict(kind='original_terminal_reviewer_failure_preserved',entry_sha256=h(Path(reviewer.__file__)),job_id='3054409',pull_receipt=pull,analysis_projection_sha256=h(st),error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),scientific_acceptance=False,state_modified=False)
 name='Object_original_terminal_review_failure.json'
p=R/B/name
with p.open('x') as f:json.dump(out,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(dict(path=str(p.relative_to(R)),sha256=h(p),status=out.get('status'),error=out.get('error'))))
