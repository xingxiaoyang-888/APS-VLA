"""Independent legacy successful-exit compatibility boundary; no scheduler calls."""
from pathlib import Path
import copy,json,sys
import pytest
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');O=R/'.local/autonomous_training_v1/audit'
sys.path.insert(0,str(R/'scripts/ops/formal_autonomous_training_v1'));import controller as c
OBS=R/'results/formal_main_v2/preflight/autonomous_execution_v1/actual_scheduler_observation_v2.json'

def test_all237_actual_capacity_has_eight_occupied_no_findings_and_does_not_mutate():
    assert c.file_sha(OBS)=='2492ba2d92c40118e4046da7789544401effaed6099b0405d842a8ed3d6daa59'
    v=json.loads(OBS.read_bytes());jobs=json.loads((O/'sacct_legacy_registered_snapshot.json').read_bytes())['registered_jobs']
    before=copy.deepcopy(jobs);got=c.capacity(jobs,v['snapshot'])
    assert got==v['capacity'] and len(got['occupied'])==8 and not got['unknown'] and not got['findings'] and jobs==before
    assert sum(j.get('experiment')!=c.ROUND and j['status']=='COMPLETED' and type(j.get('exit_code')) is int and j['exit_code']==0 for j in jobs)==12

def test_previous_parser_only_fix_reproduces_exact12_false_legacy_drifts():
    p=R/'results/formal_main_v2/preflight/autonomous_execution_v1/controller_before_legacy_exit_fix.py.txt'
    assert c.file_sha(p)=='39b9ecdcc7feecf80f05ac3b8012d2f2cb5a79760b6f8ca1465e23e52a16d7a8'
    old={'__name__':'retained_previous_controller','__file__':str(p)};exec(compile(p.read_text(),str(p),'exec'),old)
    v=json.loads(OBS.read_bytes());jobs=json.loads((O/'sacct_legacy_registered_snapshot.json').read_bytes())['registered_jobs']
    found=old['capacity'](jobs,v['snapshot'])['findings'];assert len(found)==12 and all(x.startswith('terminal_identity_drift:') for x in found)

@pytest.mark.parametrize('experiment,old_status,prior_exit,new_status,new_exit,passes',[
    ('legacy_g1f','COMPLETED',0,'COMPLETED','0:0',True),
    ('formal_main_v2','COMPLETED',0,'COMPLETED','0:0',False),
    ('legacy_g1f','COMPLETED',1,'COMPLETED','1:0',False),
    ('legacy_g1f','COMPLETED',False,'COMPLETED','0:0',False),
    ('legacy_g1f','COMPLETED',0.0,'COMPLETED','0:0',False),
    ('legacy_g1f','COMPLETED','0','COMPLETED','0:0',False),
    ('legacy_g1f','COMPLETED',0,'COMPLETED','1:0',False),
    ('legacy_g1f','FAILED',0,'FAILED','0:0',False),
    ('legacy_g1f','COMPLETED',0,'RUNNING','0:0',False),
])
def test_only_historical_completed_integer_zero_is_normalized(experiment,old_status,prior_exit,new_status,new_exit,passes):
    j=dict(job_id='7',experiment=experiment,mode='engineering',status=old_status,exit_code=prior_exit,gpus=1)
    snapshot=dict(rows={'7':dict(status=new_status,exit_code=new_exit,gpus=1)},queue={})
    before=copy.deepcopy(j);result=c.capacity([j],snapshot)
    assert (not result['findings']) is passes and j==before
