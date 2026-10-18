"""Read only the fixed nonweight runtime inventories; no checkpoint/Slurm access."""
from pathlib import Path
import importlib.util,json,hashlib,os,datetime
D=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cuda_nonweight_check',D/'evidence.py')
e=importlib.util.module_from_spec(s);exec(compile((D/'evidence.py').read_bytes(),str(D/'evidence.py'),'exec'),e.__dict__)
assert e.stable_sha(D/'evidence.py')['sha256']=='96e5e0a653c2ed884f09f7c3bf1ce19f0664c1665921a183bc351a97f5ff9d87'
result={'schema':'formal_main_v2','kind':'candidate_real_nonweight_runtime_inventory_check',
'status':'passed_read_only_metadata_inventory','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'checkpoint_bytes_read':False,'scheduler_calls':0,'GPU_seconds':0,'production_state_changed':False,
'limitation':'No free-slot claim, root authorization, checkpoint freshness, submission, or recovered training is established.',
'cases':{},'read_evidence_sha256':{}}
for jid,case in e.CASES.items():
    ref=f'results/formal_main_v2/{case[0]}/k{case[1]}/seed23/training/startup_failure_reviews/{jid}.json'
    assert e.stable_sha(e.R/ref)['sha256']==case[5];result['read_evidence_sha256'][ref]=case[5]
    proof=json.loads((e.R/ref).read_bytes());out=e.P/proof['output_relative']
    expected={k[len(proof['output_relative'])+1:]:v for k,v in proof['evidence_bundle'].items() if k.startswith(proof['output_relative']+'/')}
    metadata=proof.get('previous_boundary_review')
    if metadata is not None:
        k=metadata['path'][len(proof['output_relative'])+1:];v=expected.pop(k)
        got=e.stable_sha(e.R/metadata['path'])
        assert got=={'sha256':metadata['sha256'],'bytes':v['bytes']}
        result['read_evidence_sha256'][metadata['path']]=got['sha256']
    actual={}
    for directory,dirs,files in os.walk(out,followlinks=False):
        for name in dirs:e.no_links(Path(directory)/name)
        for name in files:
            path=e.no_links(Path(directory)/name);actual[path.relative_to(out).as_posix()]=path
    assert set(actual)==set(expected)|{'.training.lock'},(jid,set(actual)-set(expected),set(expected)-set(actual))
    assert actual['.training.lock'].stat().st_size==0
    total=0
    for name,row in expected.items():
        e.relative(name);got=e.stable_sha(actual[name])
        assert got==dict(sha256=row['sha256'],bytes=row['bytes'])
        result['read_evidence_sha256'][str(actual[name])]=got['sha256'];total+=got['bytes']
    result['cases'][jid]={'raw_runtime_files':len(expected),'raw_runtime_bytes':total,'lock_bytes':0,
        'R_only_exact_previous_review':metadata,'original_target':case[3],'failed_GPU_seconds_retained':case[4]}
print(json.dumps(result,sort_keys=True,indent=2))
