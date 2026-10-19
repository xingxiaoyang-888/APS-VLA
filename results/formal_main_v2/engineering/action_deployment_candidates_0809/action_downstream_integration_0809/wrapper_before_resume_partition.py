"""Candidate v2 parent. Uses explicit new execution identity and immutable inner science.

No compatibility projection is ever published as an old v1 execution receipt.
This entry is fail-closed until exact root readiness and complete consumers exist.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

RUNTIME_REL='scripts/ops/formal_action_deployment_v1/runtime_scope.py'
WRAPPER_REL='scripts/ops/formal_action_deployment_v1/wrapper.py'
ENTRY_REL='scripts/ops/formal_action_deployment_v1/entry.py'
CONTRACT_REL='scripts/ops/formal_action_deployment_v1/contract.py'
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
OLD='scripts/server/run_formal_downstream.py'
OLD_SHA='f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24'


def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):h.update(block)
 return h.hexdigest()


def require(ok,message):
 if not ok:raise ValueError(message)


def verify(invocation, *, project=P):
 project=Path(project)
 require(invocation.get('wrapper')==WRAPPER_REL and sha(project/WRAPPER_REL)==invocation.get('wrapper_sha256'),'Actual parent source identity mismatch')
 support=invocation.get('support_files',{})
 require(re.fullmatch('[0-9a-f]{64}',str(support.get(CONTRACT_REL))) and sha(project/CONTRACT_REL)==support[CONTRACT_REL],'Contract source must match before import')
 contract=load(project/CONTRACT_REL,'action_exec_contract')
 require(invocation.get('version')==contract.VERSION and invocation.get('wrapper')==WRAPPER_REL,'Explicit actual v2 wrapper identity required')
 readiness=contract.read_ref(project,invocation.get('runtime_readiness'))
 expected={'schema':'formal_main_v2','kind':'formal_action_runtime_readiness','status':'passed','reviewed_by':'root',
  'execution_version':contract.VERSION,'scientific_settings_changed':False,'final_evaluation_enabled':False,'raw_consumer_ready':True}
 require(all(readiness.get(k)==v for k,v in expected.items()),'Complete root runtime/consumer readiness is required')
 effective=contract.read_ref(project,readiness.get('effective_plan'))
 original=contract.read_ref(project,invocation['scientific_plan'])
 runtime_contract=contract.read_ref(project,invocation['action_execution_contract'])
 contract.validate_effective(original,effective,scientific_plan_ref=invocation['scientific_plan'],
  execution_contract_ref=invocation['action_execution_contract'],execution_contract=runtime_contract)
 require(set(invocation)==set(effective['invocation'])|{'registered_utc','plan_sha256','runtime_readiness'},'Prepared invocation has extra/missing fields')
 require({k:invocation[k] for k in effective['invocation']}==effective['invocation'],'Prepared invocation changed effective plan')
 require(isinstance(invocation['registered_utc'],str) and invocation['registered_utc'],'Registration time required')
 require(readiness.get('plan_sha256')==effective['plan_sha256']==invocation['plan_sha256'],'Readiness/effective plan identity mismatch')
 require(readiness.get('runtime_sources')==runtime_contract['files'],'Ready sources are not exact execution/reviewer/consumer sources')
 for role in ('root_review','independent_review'):
  reviewed=contract.read_ref(project,readiness.get(role))
  require(reviewed.get('status')=='passed' and reviewed.get('execution_version')==contract.VERSION,'Runtime readiness needs matching root and independent passed evidence')
  require(reviewed.get('runtime_sources')==runtime_contract['files'],'Reviewer did not bind all runtime/consumer files')
  require(reviewed.get('production_chain_complete') is True,'Partial candidate audit cannot authorize production')
 require(readiness['root_review']!=readiness['independent_review'],'Root review is not independent evidence')
 for name,checksum in invocation['support_files'].items():
  contract.relative(name);require(sha(project/name)==checksum,'Support bytes changed: '+name)
 for name,checksum in invocation['watched_files'].items():
  p=Path(name);require(p.resolve()==p and (project in p.parents),'Noncanonical runtime watch')
  contract.relative(p.relative_to(project).as_posix());require(sha(p)==checksum,'Runtime input changed: '+name)
 if original['invocation']['resume']:
  transition=contract.read_ref(project,runtime_contract['transition'])
  contract.validate_transition(transition,original,root=project,execution_contract=runtime_contract)
 require(sha(project/OLD)==OLD_SHA,'Original scientific-plan validator changed')
 original_wrapper=load(project/OLD,'original_plan_validator_not_execution')
 # This validates only the declared original science. The old wrapper is not run.
 args=original_wrapper.verify(original['invocation'])
 require(runtime_contract['runtime_contract'].get('checkpoint')==str(args.checkpoint),'Runtime loader guard must bind the exact original base')
 runtime=load(project/RUNTIME_REL,'action_deployment_runtime')
 runtime.validate_contract(project_root=project,source_root=Path(invocation['source_root']),contract=runtime_contract['runtime_contract'])
 return dict(args=args,original_plan=original,effective_plan=effective,execution_contract=runtime_contract,
  readiness=readiness,contract=contract,original_wrapper=original_wrapper,runtime=runtime)


def archive_action_evidence(project,output,job,invocation_sha):
 require(sha(project/OLD)==OLD_SHA,'Original archive helper source changed')
 old=load(project/OLD,'action_archive_original_publish')
 source=project/'results/formal_main_v2/action_execution_invocations'/job
 artifacts=[]
 for name in ('identity.json','events.jsonl','completion.json'):
  p=source/name
  if not p.exists():continue
  require(p.resolve()==p,'Noncanonical action evidence')
  before=p.stat();data=p.read_bytes();after=p.stat()
  require((before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),'Action evidence still changing')
  target=output/'action_execution'/job/name;old.publish_bytes(target,data)
  checksum=hashlib.sha256(data).hexdigest();require(sha(p)==sha(target)==checksum,'Action archive byte mismatch')
  artifacts.append(dict(source=str(p),path=str(target),sha256=checksum,bytes=len(data)))
  if name.endswith('.json'):
   row=json.loads(data);require(row.get('job_id')==job and row.get('invocation_sha256')==invocation_sha,'Foreign action evidence')
 return artifacts


def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--invocation',type=Path,required=True);parser.add_argument('--invocation-sha256',required=True)
 args=parser.parse_args(argv);job=os.environ.get('SLURM_JOB_ID','')
 require(os.name=='posix' and re.fullmatch('[0-9]+',job),'Registered server Slurm execution required')
 require(Path(__file__).resolve()==P/WRAPPER_REL,'Exact production wrapper path required')
 require(args.invocation.resolve()==args.invocation and args.invocation.parent==P/'results/formal_main_v2/invocations','Exact invocation path required')
 require(sha(args.invocation)==args.invocation_sha256,'Invocation SHA changed')
 inv=json.loads(args.invocation.read_text());output=Path(inv['run_root'])
 require(output.resolve()==output and P/'results/formal_main_v2' in output.parents,'Formal output only')
 require(sha(P/OLD)==OLD_SHA,'Original archive helper source changed')
 require(sha(P/WRAPPER_REL)==inv.get('wrapper_sha256'),'Parent source differs from root invocation')
 old=load(P/OLD,'action_parent_original_archive')
 start=time.perf_counter();receipt=dict(schema='formal_main_v2',kind='formal_downstream_job_receipt',execution_version='formal-downstream-action-v1',
  job_id=job,invocation_sha256=args.invocation_sha256,run_root=str(output),stage=inv['stage'],stage_key=inv['stage_key'],
  source_sha256=inv['source_sha256'],adapter_sha256=inv['adapter_sha256'],wrapper_sha256=inv['wrapper_sha256'],
  action_execution_contract=inv['action_execution_contract'],scientific_plan=inv['scientific_plan'],runtime_readiness=inv.get('runtime_readiness'),
  stage_completed_claimed=False,original_scientific_wrapper_executed=False,started_utc=datetime.now(timezone.utc).isoformat(),
  cost_scope='Complete Slurm allocation, including validation/loading/errors, counted once separately')
 code=1
 try:
  locks=P/'results/formal_main_v2/stage_locks';locks.mkdir(parents=True,exist_ok=True)
  with ExitStack() as stack:
   names=[inv['stage_key'],*[f"{inv['suite']}_{inv['stage']}_{mid}" for mid in inv['method_ids']]]
   require(len(names)==len(set(names)),'Duplicate stage/method lock')
   for name in sorted(names):
    require(bool(re.fullmatch('[A-Za-z0-9_-]+',name)),'Invalid stage lock')
    f=stack.enter_context((locks/(name+'.lock')).open('a'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   verify(inv)
   result=subprocess.run([sys.executable,'-B',str(P/ENTRY_REL),'--invocation',str(args.invocation),'--invocation-sha256',args.invocation_sha256],cwd=inv['source_root'])
   code=result.returncode
 except BaseException as e:receipt.update(error_type=type(e).__name__,error=str(e))
 finally:
  try:
   artifacts,records=old.archive_adapter_evidence(root=P,output=output,job_id=job,invocation=inv)
   receipt.update(adapter_artifacts=artifacts,adapter_receipts=records)
   action=archive_action_evidence(P,output,job,args.invocation_sha256);receipt['action_execution_artifacts']=action
   if code==0:
    require(len(action)==3 and len(artifacts)==2 and len(records)==1 and records[0]['status']=='returned','Incomplete successful execution evidence')
    completion=json.loads((output/'action_execution'/job/'completion.json').read_text())
    require(completion.get('status')=='returned' and completion.get('exit_code')==0 and completion.get('runtime_restored') is True,'Runtime failed/restoration absent')
   for name,checksum in inv['support_files'].items():require(sha(P/name)==checksum,'Support changed during run')
  except BaseException as e:code=1;receipt.update(archive_error_type=type(e).__name__,archive_error=str(e))
  receipt.update(exit_code=code,status='returned' if code==0 else 'failed',wall_seconds=time.perf_counter()-start,finished_utc=datetime.now(timezone.utc).isoformat())
  old.publish(P/'results/formal_main_v2/job_receipts'/(job+'.json'),receipt)
 return code


if __name__=='__main__':raise SystemExit(main())
