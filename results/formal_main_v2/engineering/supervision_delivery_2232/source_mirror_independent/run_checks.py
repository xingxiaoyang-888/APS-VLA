"""Isolated restore tests of exact mirror helper; no production writes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
SRC='scripts/ops/restore_formal_source_mirror_v1.py';PIN='36c6981e806acfe5e1ee8a920ec0f0c905c366b63a32ada829b79a41dd41a80a'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def expect_reject(name,fn,checks,after=None):
 try:fn()
 except (AssertionError,ValueError,FileExistsError,RuntimeError) as e:
  if after:assert after(),name+' post-failure integrity'
  checks.append({'name':name,'status':'passed','rejected':type(e).__name__,'message':str(e)});return
 raise AssertionError(name+' unexpectedly accepted')
def tree(root):
 return {str(p.relative_to(root)):(sha(p.read_bytes()),p.stat().st_size,p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
def main():
 assert __debug__,'tested invocation requires normal nonoptimized Python'
 raw=(R/SRC).read_bytes();assert sha(raw)==PIN
 spec=importlib.util.spec_from_file_location('mirror_helper_independent',R/SRC);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 invbytes=(R/mod.INV).read_bytes();assert sha(invbytes)==mod.PIN
 rows=json.loads(invbytes)['files'];assert len(rows)==173
 F=D/'isolated';F.mkdir(exist_ok=False);checks=[];source_refs={}
 for rel,h in rows.items():
  assert Path(rel).suffix in {'.py','.json','.md','.toml','.slurm','.sh','.txt'}
  # Exact frozen inventory contains source code and registration metadata, no state/checkpoint payload.
  assert rel!='results/experiment_supervisor/state.json' and not any(x in Path(rel).parts for x in ['weights','checkpoints','sealed'])
  p=R/rel;b=p.read_bytes();assert sha(b)==h
  q=F/rel;q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write(b)
  source_refs[rel]={'sha256':h,'bytes':len(b)}
 ip=F/mod.INV;ip.parent.mkdir(parents=True,exist_ok=True)
 with ip.open('xb') as f:f.write(invbytes)
 mirror=F/mod.MIRROR;canonical_before=tree(F)
 expect_reject('verify_only_missing_does_not_create_mirror',lambda:mod.restore(F,verify_only=True),checks,lambda:not mirror.exists() and tree(F)==canonical_before)
 bad_inventory=invbytes+bytes([32]);ip.write_bytes(bad_inventory)
 expect_reject('fixed_inventory_SHA_rejects_even_whitespace',lambda:mod.restore(F),checks,lambda:not mirror.exists() and ip.read_bytes()==bad_inventory)
 ip.write_bytes(invbytes)
 agent=F/'AGENTS.md';good=agent.read_bytes();agent.write_bytes(good+b'INVALID')
 expect_reject('source_mismatch_before_any_destination_write',lambda:mod.restore(F),checks,lambda:not mirror.exists() and agent.read_bytes()==good+b'INVALID')
 agent.write_bytes(good)
 foreign=D/'foreign';foreign.mkdir();(F/'snapshots').symlink_to(foreign,target_is_directory=True)
 expect_reject('destination_parent_symlink_rejected',lambda:mod.restore(F),checks,lambda:not list(foreign.iterdir()))
 (F/'snapshots').unlink()
 moved=F/'AGENTS.canonical.md';agent.rename(moved);agent.symlink_to(moved)
 expect_reject('canonical_source_symlink_rejected',lambda:mod.restore(F),checks,lambda:not mirror.exists() and moved.read_bytes()==good)
 agent.unlink();moved.rename(agent)
 result=mod.restore(F);assert result=={'status':'verified_exact_canonical_source_mirror','files':173,'already_present':0,'new_source_aliases':173,'original_server_provenance_reverified':False,'weights_or_sealed_values_read':False}
 assert all((F/rel).read_bytes()==(mirror/rel).read_bytes() and sha((mirror/rel).read_bytes())==h for rel,h in rows.items())
 checks.append({'name':'restore_all173_exact_bytes','status':'passed','result':result})
 before=tree(F);repeat=mod.restore(F);assert repeat['already_present']==173 and repeat['new_source_aliases']==0 and tree(F)==before
 checks.append({'name':'idempotent_restore_never_rewrites_existing','status':'passed','result':repeat})
 verified=mod.restore(F,verify_only=True);assert verified['new_source_aliases']==0 and tree(F)==before
 checks.append({'name':'verify_only_complete_no_byte_or_mtime_change','status':'passed'})
 dest=mirror/'AGENTS.md';dest.write_bytes(b'MISMATCH');state=tree(F)
 expect_reject('existing_mismatched_target_never_overwritten',lambda:mod.restore(F),checks,lambda:tree(F)==state)
 dest.write_bytes(good);dest.unlink();dest.symlink_to(agent);state=tree(F)
 expect_reject('existing_destination_symlink_rejected',lambda:mod.restore(F),checks,lambda:tree(F)==state and dest.is_symlink())
 dest.unlink();dest.write_bytes(good)
 for path in ['../outside',str(D/'absolute'),'bad'+chr(92)+'path']:
  expect_reject('safe_path_rejects_'+repr(path),lambda path=path:mod.safe(F,path),checks)
 # Verify original helper, fixed inventory and all canonical source bytes unchanged.
 assert (R/SRC).read_bytes()==raw and (R/mod.INV).read_bytes()==invbytes
 for rel,h in rows.items():assert sha((R/rel).read_bytes())==h
 assert mod.restore(F,verify_only=True)['already_present']==173
 receipt={'schema':'formal_main_v2','kind':'formal_source_mirror_delivery_independent_review','status':'passed_isolated_CPU_review','review_role':'independent',
  'utc':datetime.now(timezone.utc).isoformat(),'helper':{'path':SRC,'sha256':PIN},'inventory':{'path':mod.INV,'sha256':mod.PIN},'checks':checks,'tests':len(checks),'failures':0,
  'source_files':source_refs,'source_count':173,'total_source_bytes':sum(x['bytes'] for x in source_refs.values()),
  'exact_mirror_namespace':mod.MIRROR,'canonical_sources_unchanged':True,'production_mirror_written':False,'production_entrypoints_changed':False,
  'weights_or_sealed_values_read':False,'supervisor_state_read_or_written':False,'Git_or_Slurm_used':False,'independent_only_wrote_private_fixture_and_reports':True,
  'limits':['Restoration is deterministic reconstruction from Git canonical bytes, not re-verification of original server provenance.',
   'All checks were exercised with normal Python -B and __debug__=True; the helper uses assert and is not qualified for Python -O/PYTHONOPTIMIZE.',
   'Symlink protections reject preexisting symlink files/parents below the resolved project root; this is a trusted single-writer reconstruction utility, not a hostile concurrent-filesystem isolation boundary.',
   'The isolated source/mirror fixtures are excluded from Git delivery; preserve canonical sources, helper and exact original mapping instead.']}
 rr=save('independent_review.json',receipt)
 print(json.dumps({'receipt':rr,'tests':len(checks),'bytes':receipt['total_source_bytes']}))
if __name__=='__main__':main()
