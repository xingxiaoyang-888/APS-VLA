"""Candidate actual child entry: new outer execution provenance, unchanged science loop."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback

P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
ENTRY='scripts/ops/formal_action_deployment_v1/entry.py'
WRAPPER='scripts/ops/formal_action_deployment_v1/wrapper.py'
LEGACY='scripts/ops/formal_evaluation_adapter.py'
LEGACY_SHA='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
VERSION='formal-downstream-action-v1'


def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--invocation',type=Path,required=True);parser.add_argument('--invocation-sha256',required=True)
 args=parser.parse_args(argv);job=os.environ.get('SLURM_JOB_ID','')
 if os.name!='posix' or not re.fullmatch('[0-9]+',job) or Path(__file__).resolve()!=P/ENTRY:raise ValueError('Exact registered server action entry required')
 if args.invocation.parent!=P/'results/formal_main_v2/invocations' or args.invocation.resolve()!=args.invocation or hashlib.sha256(args.invocation.read_bytes()).hexdigest()!=args.invocation_sha256:raise ValueError('Exact root invocation required')
 inv=json.loads(args.invocation.read_text())
 if hashlib.sha256((P/WRAPPER).read_bytes()).hexdigest()!=inv.get('wrapper_sha256') or hashlib.sha256((P/ENTRY).read_bytes()).hexdigest()!=inv.get('support_files',{}).get(ENTRY):raise ValueError('Actual wrapper/entry source differs before import')
 wrapper=load(P/WRAPPER,'actual_action_parent_contract')
 directory=P/'results/formal_main_v2/action_execution_invocations'/job;directory.mkdir(parents=True,exist_ok=False)
 identity_path,event_path,completion_path=(directory/n for n in ('identity.json','events.jsonl','completion.json'))
 shared=dict(schema='formal_main_v2',version=VERSION,job_id=job,invocation_sha256=args.invocation_sha256,
  **{k:inv[k] for k in ('stage','stage_key','suite','source_root','source_sha256','execution_manifest_sha256')},
  action_execution_contract=inv['action_execution_contract'],scientific_plan=inv['scientific_plan'],runtime_readiness=inv['runtime_readiness'])
 events=[];errors=[];started=time.perf_counter();code=1;context=None;runtime_restored=False;unchanged=False;result=None;legacy=None;original_run=None;original_code=None
 wrapper.require(wrapper.sha(P/wrapper.OLD)==wrapper.OLD_SHA,'Original archive helper source changed')
 old_publish=load(P/wrapper.OLD,'actual_action_archive')
 def emit(event,**fields):
  if set(fields)&{'kind','seq','utc','event'} or any(fields[k]!=shared[k] for k in set(fields)&set(shared)):raise ValueError('Runtime journal attempted to overwrite identity')
  row=dict(**shared,kind='formal_action_execution_event',seq=len(events),utc=datetime.now(timezone.utc).isoformat(),event=event,
   **{k:v for k,v in fields.items() if k not in shared})
  with event_path.open('a',encoding='utf-8',newline='\n') as f:
   f.write(json.dumps(row,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
  events.append(row)
 emit('action_execution_start',actual_entrypoint=ENTRY,original_scientific_wrapper_executed=False)
 try:
  context=wrapper.verify(inv)
  runtime=context['runtime'];execution_contract=context['execution_contract'];original=context['original_plan']
  if list((P/'results/formal_main_v2/adapter_invocations').glob(job+'_*')):raise ValueError('Existing legacy adapter attempt forbids duplicate execution')
  if wrapper.sha(P/LEGACY)!=LEGACY_SHA:raise ValueError('Original scientific adapter changed')
  legacy=load(P/LEGACY,'actual_unchanged_scientific_adapter');original_run=legacy.run;original_code=original_run.__code__
  identity=dict(**shared,kind='formal_action_execution_identity',actual_entrypoint=ENTRY,actual_wrapper=WRAPPER,
   runtime_sources=execution_contract['files'],runtime_contract=execution_contract['runtime_contract'],
   expected_base_load_calls=1,original_evaluation_adapter=str(P/LEGACY),original_evaluation_adapter_sha256=LEGACY_SHA,
   original_run_code_sha256=legacy.code_sha(original_run),original_scientific_plan_sha256=inv['scientific_plan_sha256'],
   original_scientific_wrapper_executed=False,source_inventory_sha256=inv['source_inventory_sha256'],
   scientific_settings_changed=False,scientific_completion_not_inferred=True)
  old_publish.publish(identity_path,identity)
  def scientific_runner():
   a=context['args'];emit('legacy_adapter_start',original_run_code_sha256=legacy.code_sha(original_run),identity_sha256=wrapper.sha(identity_path))
   try:
    value=legacy.run(a,mode=a.mode,source_root=a.source_root,source_inventory=a.source_inventory,adapter_sha256=LEGACY_SHA,resume=a.resume)
   except BaseException as e:
    emit('legacy_adapter_exception',error_type=type(e).__name__,error=str(e));raise
   emit('legacy_adapter_return',runner_status=value.get('status') if isinstance(value,dict) else None)
   return value
  with legacy.source_imports(Path(inv['source_root'])):
   expected_assets=runtime.expected_asset_identities(project_root=P,source_root=Path(inv['source_root']),contract=execution_contract['runtime_contract'],asset_contract=original['invocation'].get('downstream_asset_compatibility'))
   result=runtime.run_with_asset_contexts(scientific_runner,project_root=P,source_root=Path(inv['source_root']),
    contract=execution_contract['runtime_contract'],asset_contract=original['invocation'].get('downstream_asset_compatibility'),emit=emit)
  proof=runtime.verify_runtime_events(events,execution_contract['runtime_contract'],expected_asset_identities=expected_assets)
  wrapper.require(proof.get('all_source_and_binding_contexts_restored') is True,'Runtime scope must restore every declared binding')
  runtime_restored=True;code=0
 except BaseException as e:
  errors.append(dict(error_type=type(e).__name__,error=str(e)));traceback.print_exception(type(e),e,e.__traceback__)
 finally:
  if legacy is not None:
   if legacy.run is not original_run or original_run.__code__ is not original_code:
    code=1;errors.append(dict(error_type='RuntimeError',error='Original adapter run binding changed'))
    original_run.__code__=original_code;legacy.run=original_run
  if context is not None:
   try:
    for name,checksum in inv['watched_files'].items():wrapper.require(wrapper.sha(name)==checksum,'Runtime watched input changed')
    unchanged=True
   except BaseException as e:code=1;errors.append(dict(error_type=type(e).__name__,error=str(e)))
  ending=dict(status='returned' if code==0 else 'failed',exit_code=code,runtime_restored=runtime_restored,
   immutable_inputs_unchanged=unchanged,errors=errors,scientific_completion_not_inferred=True,
   runner_status=result.get('status') if isinstance(result,dict) else None)
  emit('action_execution_end',**ending)
  complete=dict(**shared,kind='formal_action_execution_completion',**ending,events_sha256=wrapper.sha(event_path),events_path=str(event_path),
   identity_sha256=wrapper.sha(identity_path) if identity_path.exists() else None,
   wall_seconds=time.perf_counter()-started,finished_utc=datetime.now(timezone.utc).isoformat(),
   cost_scope='Nested evidence only; charge entire Slurm allocation once')
  old_publish.publish(completion_path,complete)
 return code


if __name__=='__main__':raise SystemExit(main())
