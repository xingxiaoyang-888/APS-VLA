"""Execute a root-registered formal stage with source checks and one writer."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=P/'results/formal_main_v2'
ENTRIES={'acceptance':'scripts/verify_formal_acceptance.py','train':'scripts/run_formal_future.py',
         'development':'scripts/eval_formal_selector_libero.py','final':'scripts/eval_formal_selector_libero.py',
         'collect':'scripts/profile_formal.py','profile':'scripts/profile_formal.py'}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--invocation',type=Path,required=True);args=parser.parse_args()
    source=Path(__file__).resolve().parents[2];path=args.invocation.resolve()
    if not os.environ.get('SLURM_JOB_ID') or R/'invocations' not in path.parents or P/'snapshots' not in source.parents:
        raise ValueError('Formal stages require project Slurm and immutable registered paths')
    invocation=json.loads(path.read_text())
    if invocation.get('schema')!='formal_main_v2' or invocation.get('stage') not in ENTRIES or invocation.get('source_root')!=str(source):
        raise ValueError('Unknown formal stage/source')
    if invocation.get('entrypoint')!=ENTRIES[invocation['stage']]:raise ValueError('Stage/entrypoint mismatch')
    argv=invocation.get('argv')
    if not isinstance(argv,list) or any(not isinstance(x,str) or '\0' in x for x in argv):raise ValueError('Invalid argv')
    if not isinstance(invocation.get('stage_key'),str) or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in invocation['stage_key']):
        raise ValueError('Invalid stage lock identity')
    inventory=json.loads((source/'source_manifest.json').read_text())
    if inventory['source_sha256']!=invocation['source_sha256']:raise ValueError('Source inventory mismatch')
    for rel,sha in inventory['files'].items():
        target=(source/rel).resolve()
        if source not in target.parents or digest(target)!=sha:raise ValueError('Frozen source changed: '+rel)
    for filename,sha in invocation['watched_files'].items():
        if digest(filename)!=sha:raise ValueError('Registered input changed: '+filename)
    locks=R/'stage_locks';locks.mkdir(parents=True,exist_ok=True)
    receipts=R/'job_receipts';receipts.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter();utc=datetime.now(timezone.utc).isoformat();job=os.environ['SLURM_JOB_ID']
    with (locks/(invocation['stage_key']+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=subprocess.run([sys.executable,str(source/invocation['entrypoint']),*argv],cwd=source)
    receipt={'schema':'formal_main_v2','job_id':job,'stage':invocation['stage'],'stage_key':invocation['stage_key'],
             'invocation_sha256':digest(path),'source_sha256':inventory['source_sha256'],'started_utc':utc,
             'exit_code':result.returncode,'wall_seconds':time.perf_counter()-started}
    output=receipts/(job+'.json');temporary=output.with_suffix('.partial')
    temporary.write_text(json.dumps(receipt,indent=2)+'\n');temporary.replace(output)
    raise SystemExit(result.returncode)

if __name__=='__main__':main()
