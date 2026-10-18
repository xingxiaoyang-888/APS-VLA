"""Independent real Slurm empty-Comment regression; no scheduler execution."""
import importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
import pytest
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'scripts/ops/formal_autonomous_training_v1'
sys.path.insert(0,str(D));import controller as c
RAW=R/'results/formal_main_v2/preflight/autonomous_execution_v1/sacct_column_failure_raw.json'
OLD=R/'results/formal_main_v2/preflight/autonomous_execution_v1/controller_before_empty_comment_fix.py.txt'
BASE='10|RUNNING|0:0|7|gres/gpu=1|n|cti-formal'
def raw_snapshot():
    assert c.file_sha(RAW)=='c50b09f3ed3af41714a648c7b867faf0d2279052443d262e146e634e36435430'
    v=json.loads(RAW.read_bytes());assert v['returncode']==0
    ids=set(v['argv'][v['argv'].index('-j')+1].split(','));return v,ids

def test_all237_real_rows_keep_empty_final_comment():
    v,ids=raw_snapshot();lines=[l for l in v['stdout'].splitlines() if l.strip()]
    assert len(ids)==len(lines)==237 and all(len(l.split('|'))==8 for l in lines)
    result=c.parse_sacct(v['stdout'],ids);assert set(result)==ids
    for line in lines:
        values=line.split('|');r=result[values[0]]
        assert r['scheduler_comment']==values[7] and r['scheduler_name']==values[6]
        assert r['elapsed_seconds']==int(values[3]) and r['allocation']==values[4]
    assert sum(r['scheduler_comment']=='' for r in result.values())==237

def test_pre_fix_exact_original_reproduces_actual_failure():
    assert c.file_sha(OLD)=='4ac7dfa79345ec8a3db3ad1aa44c560d887ea691813d778bb8e1851e55ea9eec'
    namespace={'__name__':'retained_old_parser','__file__':str(OLD)};exec(compile(OLD.read_text(),str(OLD),'exec'),namespace)
    v,ids=raw_snapshot()
    with pytest.raises(ValueError,match='unexpected sacct columns'):namespace['parse_sacct'](v['stdout'],ids)

def test_real237_snapshot_through_Slurm_observe_uses_only_stubbed_calls():
    v,ids=raw_snapshot();rows=c.parse_sacct(v['stdout'],ids)
    jobs=[dict(job_id=jid,status=rows[jid]['status']) for jid in sorted(ids)]
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        assert argv[0] in ('sacct','squeue')
        if argv[0]=='sacct':return SimpleNamespace(returncode=0,stdout=v['stdout'],stderr='')
        qids=argv[argv.index('-j')+1].split(',')
        return SimpleNamespace(returncode=0,stdout=''.join(jid+'|'+rows[jid]['status']+'|\n' for jid in qids if rows[jid]['status'] not in c.TERMINAL),stderr='')
    got=c.Slurm(runner=runner).observe(jobs)
    assert got['rows']==rows and got['raw_sacct']==v['stdout']
    assert all(cmd[0] in ('sacct','squeue') for cmd in calls)

@pytest.mark.parametrize('tail,expected',[('|',''),('|comment','comment'),('|comment|','comment'),('||','')])
def test_eight_columns_and_optional_single_format_delimiter(tail,expected):
    r=c.parse_sacct(BASE+tail+'\n',{'10'})['10'];assert r['scheduler_comment']==expected and r['gpus']==1

@pytest.mark.parametrize('tail',['','|comment|surplus','|comment||','|||'])
def test_missing_or_extra_real_columns_rejected(tail):
    with pytest.raises(ValueError,match='unexpected sacct columns'):c.parse_sacct(BASE+tail+'\n',{'10'})

def test_empty_comment_does_not_weaken_registered_id_uniqueness():
    raw=BASE+'|\n'
    with pytest.raises(ValueError,match='foreign or duplicate'):c.parse_sacct(raw,{'11'})
    with pytest.raises(ValueError,match='foreign or duplicate'):c.parse_sacct(raw+raw,{'10'})

def test_blank_lines_and_zero_GPU_CPU_empty_comment():
    raw='\n  \n11|COMPLETED|0:0|3|billing=1,cpu=1,mem=2G,node=1|cpui134|cti-auto-cpucheck|\n'
    row=c.parse_sacct(raw,{'11'})['11'];assert row['gpus']==0 and row['scheduler_comment']=='' and row['elapsed_seconds']==3
