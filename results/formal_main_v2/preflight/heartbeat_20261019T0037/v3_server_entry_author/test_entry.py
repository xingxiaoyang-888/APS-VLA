"""Server-only finite migration checks. No real publication or GPU operation."""
from __future__ import annotations
import ast,contextlib,hashlib,importlib.util,io,json,os,subprocess,sys,time,unittest
from pathlib import Path
from unittest import mock
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
VALIDATION=None
READ={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def load():
 spec=importlib.util.spec_from_file_location('_migration_entry_cpu',C/'entry.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def args(m):
 return [str(C/'entry.py'),'--independent-review','.local/action_execution_gpu_v3_independent_0840/independent_review.json',
         '--independent-sha256',m.INDEPENDENT_SHA,'--entry-sha256',sha(C/'entry.py'),'--validate-only']
def targets(m):
 return [*(m.SOURCE+k for k in m.EXPECTED),m.AUTHOR,m.AUDIT,m.TYPED,m.REVIEW,m.REG,m.NODE,m.CHECK,m.SCRIPT_ARCHIVE]
class MigrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=load()
  cls.before={p:sha(R/p) if (R/p).is_file() else None for p in targets(cls.m)}
  inv=json.loads((R/cls.m.INVENTORY).read_bytes())
  for base in (R,S):
   for rel,checksum in inv['files'].items():
    if sha(base/rel)!=checksum:raise AssertionError('source mismatch '+str(base/rel))
    READ[str(base/rel)]=checksum
  for rel,checksum in cls.m.MIGRATION_BINDINGS.items():
   assert sha(R/rel)==checksum;READ[str(R/rel)]=checksum
  for rel in ('entry.py','legacy_entry.before.py.txt','migration.diff','test_entry.py'):
   READ[str(C/rel)]=sha(C/rel)
 def test_01_real_validate_only_under_write_and_transport_guard(self):
  global VALIDATION
  # Actual entry main and original read-only evidence logic; no mocked proofs.
  harness="""import os,runpy,sys
def audit(event,args):
 if event=='open':
  mode=args[1];flags=args[2]
  if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC)):
   raise RuntimeError('validate-only attempted file mutation')
 if event in {'os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.chmod','os.truncate','subprocess.Popen','os.system','socket.connect'}:
  raise RuntimeError('validate-only forbidden operation: '+event)
sys.addaudithook(audit)
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
"""
  command=[sys.executable,'-B','-c',harness,*args(self.m)]
  p=subprocess.run(command,cwd=C,capture_output=True,timeout=180)
  (C/'validate_only.stdout.json').write_bytes(p.stdout)
  (C/'validate_only.stderr.log').write_bytes(p.stderr)
  (C/'validate_only.execution.json').write_text(json.dumps({
    'command':command,'returncode':p.returncode,'guard':'Python audit rejects writes, subprocess, shell and connect after runpy setup',
    'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},indent=2)+'\n')
  self.assertEqual(p.returncode,0,p.stderr.decode())
  VALIDATION=json.loads(p.stdout)
  self.assertEqual(VALIDATION['status'],'validated_server_candidate_no_publication_root_decision_pending')
  self.assertEqual(VALIDATION['control_root'],str(R))
  for key in ('files_written','subprocess_calls','SSH_calls','Slurm_submissions','GPU_seconds'):
   self.assertEqual(VALIDATION[key],0)
  for key in ('root_approval_recorded','actual_GPU_acceptance','scientific_release'):
   self.assertIs(VALIDATION[key],False)
  self.assertEqual(self.before,{p:sha(R/p) if (R/p).is_file() else None for p in targets(self.m)})
 def test_02_validate_exact_real_evidence_sha(self):
  self.assertIsNotNone(VALIDATION)
  ev=VALIDATION['read_evidence_sha256']
  self.assertEqual(ev[self.m.AUTHOR_INPUT],self.m.AUTHOR_SHA)
  self.assertEqual(ev['.local/action_execution_gpu_v3_independent_0840/independent_review.json'],self.m.INDEPENDENT_SHA)
  for rel,checksum in ev.items():
   self.assertEqual(sha(R/rel),checksum,rel);READ[str(R/rel)]=checksum
 def test_03_wrong_root_rejected_before_metadata_reads(self):
  m=load()
  with mock.patch.object(m,'ROOT',C),mock.patch.object(m,'read_bytes',side_effect=AssertionError('metadata read')):
   with self.assertRaisesRegex(ValueError,'wrong server control root'):
    m.server_workspace_contract(validate_only=True,entry_sha256=sha(C/'entry.py'))
 def test_04_candidate_cannot_publish(self):
  with self.assertRaisesRegex(ValueError,'reviewed installed R entry'):
   self.m.server_workspace_contract(validate_only=False,entry_sha256=sha(C/'entry.py'))
 def test_05_wrong_entry_sha_rejected(self):
  with self.assertRaisesRegex(ValueError,'reviewed entry SHA differs'):
   self.m.server_workspace_contract(validate_only=True,entry_sha256='0'*64)
 def test_06_exact_workspace_policy_pins(self):
  m=load();pins=dict(m.MIGRATION_BINDINGS);pins['SERVER_WORKSPACE.md']='0'*64
  with mock.patch.object(m,'MIGRATION_BINDINGS',pins):
   with self.assertRaisesRegex(ValueError,'evidence SHA differs'):
    m.server_workspace_contract(validate_only=True,entry_sha256=sha(C/'entry.py'))
 def test_07_exact_old_source_pin_retained(self):
  m=load();pins=dict(m.MIGRATION_BINDINGS);pins['.local/action_execution_gpu_v3_root_integration_0840.py']='0'*64
  with mock.patch.object(m,'MIGRATION_BINDINGS',pins):
   with self.assertRaisesRegex(ValueError,'evidence SHA differs'):
    m.server_workspace_contract(validate_only=True,entry_sha256=sha(C/'entry.py'))
 def test_08_mutually_exclusive_root_decision(self):
  m=load()
  for command in (args(m)[:-1],args(m)+['--root-approve-cpu-registration']):
   with self.subTest(args=command),mock.patch.object(sys,'argv',command),contextlib.redirect_stderr(io.StringIO()):
    with self.assertRaises(SystemExit) as exc:m.main()
    self.assertEqual(exc.exception.code,2)
 def test_09_old_scientific_read_gate_functions_unchanged(self):
  before=ast.parse((C/'legacy_entry.before.py.txt').read_text())
  after=ast.parse((C/'entry.py').read_text())
  bf={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,ast.FunctionDef)}
  af={n.name:ast.dump(n,include_attributes=False) for n in after.body if isinstance(n,ast.FunctionDef)}
  for name in bf:
   if name!='main':self.assertEqual(af[name],bf[name],name)
  # All original eight payloads are still the exact author/independent-reviewed bytes.
  for name,(checksum,length) in self.m.EXPECTED.items():
   p=R/self.m.CANDIDATE/name
   self.assertEqual(p.stat().st_size,length);self.assertEqual(sha(p),checksum)
 def test_10_forbidden_paths_rejected_before_filesystem(self):
  bad=['../escape.json','F:/CTI-VLA/x.json','configs/manifests/formal_main_v2/libero_10/initial_states/sealed_final.json',
       'results/final_registry.json','results/test/x.json','results/model.pt','results/checkpoints/x.json',
       '.local/other/state.json','results/final_states.json','results/panel.json']
  with mock.patch.object(Path,'resolve',side_effect=AssertionError('filesystem reached')):
   for path in bad:
    with self.subTest(path=path),self.assertRaises(ValueError):self.m.safe(path,synthetic=True)
 def test_11_unique_synthetic_state_is_not_real_state_authority(self):
  with self.assertRaises(ValueError):self.m.safe(self.m.SYNTHETIC_STATE)
  self.assertEqual(self.m.safe(self.m.SYNTHETIC_STATE,synthetic=True),R/self.m.SYNTHETIC_STATE)
  with self.assertRaises(ValueError):
   self.m.safe(self.m.SYNTHETIC_STATE.replace('synthetic_v3_CPU_only0','synthetic_v3_CPU_only1'),synthetic=True)
  with self.assertRaises(ValueError):self.m.safe('results/experiment_supervisor/state.json',synthetic=True)
 def test_12_no_fixture_or_self_hash_cycle_in_deployment(self):
  self.assertIsNotNone(VALIDATION)
  rows=VALIDATION['deployment_mapping']
  self.assertEqual(len(rows),VALIDATION['deployment_files'])
  self.assertEqual(len({r['server'] for r in rows}),len(rows))
  self.assertEqual(sum(r['server'].startswith(str(S)+'/') for r in rows),173)
  for row in rows:
   self.assertNotIn('pytest_',row['path']);self.assertNotIn('synthetic_',row['path'])
   self.assertNotIn(row['path'],(self.m.REVIEW,self.m.REG,self.m.SYNTHETIC_STATE))
   self.assertTrue(row['server'].startswith(self.m.RUNTIME_ROOT+'/'))
  for rel in self.m.MIGRATION_BINDINGS:
   self.assertEqual(sum(row['path']==rel for row in rows),1)
 def test_13_pending_templates_and_173_remain_exact(self):
  for rel in ('gpu_registration.template.json','root_review.template.json','independent_review.template.json'):
   v=json.loads((R/self.m.CANDIDATE/rel).read_bytes())
   self.assertTrue(v['status'].startswith('pending'))
  for p,checksum in READ.items():self.assertEqual(sha(p),checksum,p)
 def test_14_only_future_postpublication_child_is_check_only(self):
  tree=ast.parse((C/'entry.py').read_text())
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
         and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess']
  self.assertEqual(len(calls),1);self.assertEqual(calls[0].func.attr,'run')
  source=(C/'entry.py').read_text()
  self.assertIn("'--check-only']",source);self.assertNotIn("'--submit'",source)
  self.assertIn("args.root_approve_cpu_registration",source)
 @classmethod
 def tearDownClass(cls):
  for p,checksum in READ.items():assert sha(p)==checksum,'input drift '+p
  assert cls.before=={p:sha(R/p) if (R/p).is_file() else None for p in targets(cls.m)}

class RecordResult(unittest.TextTestResult):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.times=[]
 def startTest(self,t):super().startTest(t);self.start=time.monotonic()
 def stopTest(self,t):self.times.append((str(t),time.monotonic()-self.start));super().stopTest(t)
def main():
 started=time.monotonic()
 with (C/'tests_a1.log').open('x') as f:
  result=unittest.TextTestRunner(stream=f,verbosity=2,resultclass=RecordResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(MigrationTests))
 suite=ET.Element('testsuite',name='action_gpu_v3_server_entry_cpu',tests=str(result.testsRun),
                  failures=str(len(result.failures)),errors=str(len(result.errors)),skipped=str(len(result.skipped)),
                  time=str(time.monotonic()-started))
 failures={str(t):e for t,e in result.failures};errors={str(t):e for t,e in result.errors}
 for name,secs in result.times:
  case=ET.SubElement(suite,'testcase',name=name,time=str(secs))
  if name in failures:ET.SubElement(case,'failure').text=failures[name]
  if name in errors:ET.SubElement(case,'error').text=errors[name]
 with (C/'tests_a1.xml').open('xb') as f:f.write(ET.tostring(suite,encoding='utf-8',xml_declaration=True))
 report=dict(status='passed_CPU_candidate_no_publication' if result.wasSuccessful() else 'failed_CPU_candidate',
             tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
             seconds=time.monotonic()-started,python=sys.version,read_evidence_sha256=READ,
             test_source_sha256=sha(__file__),log_sha256=sha(C/'tests_a1.log'),xml_sha256=sha(C/'tests_a1.xml'))
 with (C/'tests_a1.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:report[k] for k in ('status','tests','failures','errors','skipped','seconds')}))
 return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
