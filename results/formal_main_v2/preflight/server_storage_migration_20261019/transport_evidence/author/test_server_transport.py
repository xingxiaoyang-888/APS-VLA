"""Finite CPU checks; all writes are confined to this server candidate directory."""
from __future__ import annotations
import contextlib, hashlib, importlib.util, io, json, os, shutil, subprocess, sys, time
from pathlib import Path
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
C = Path(__file__).resolve().parent
REAL_H = Path("/share/home/u15016/XXY_CVPR/CTI-VLA")
REAL_P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
REAL_R = REAL_H / "control_repo"
REAL_S = REAL_P / "snapshots/formal_main_v2_run_564be0995e"
REAL_INV = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
FILES = ("server_transport.py", "run_server_control.py", "bin/ssh", "bin/scp")
REAL_INPUTS = {}
SYNTHETIC_DESCRIPTION = {}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p, name):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def canonical_json(obj):
    return (json.dumps(obj,sort_keys=True,indent=2)+"\n").encode()

class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = load(C/"server_transport.py", "real_transport")
        cls.real.verify_bundle(sha(C/"bundle_manifest.json"))
        inv = json.loads((REAL_R/REAL_INV).read_bytes())
        cls.real.verify_frozen()
        for base in (REAL_R, REAL_S):
            for rel, checksum in inv["files"].items():
                REAL_INPUTS[str(base/rel)] = checksum
        REAL_INPUTS[str(REAL_R/REAL_INV)] = sha(REAL_R/REAL_INV)
        for rel in (*FILES, "bundle_manifest.json", "test_server_transport.py"):
            REAL_INPUTS[str(C/rel)] = sha(C/rel)
        cls.work = C/"tests_work_a1"
        cls.work.mkdir(exist_ok=False)
        cls.h = cls.work/"H";cls.p = cls.work/"P"
        cls.r = cls.h/"control_repo";cls.s=cls.p/"snapshots/formal_main_v2_run_564be0995e"
        cls.bundle = cls.work/"bundle";(cls.bundle/"bin").mkdir(parents=True)
        # Only 1.67 MB of registered source bytes, twice. No repo, data, weights or states.
        for base in (cls.r, cls.s):
            for rel in inv["files"]:
                dst=base/rel;dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes((REAL_S/rel).read_bytes())
        synthetic_inv = dict(inv, source_root_server=str(cls.s))
        invpath=cls.r/REAL_INV;invpath.parent.mkdir(parents=True,exist_ok=True)
        invpath.write_bytes(canonical_json(synthetic_inv))
        core=(C/"server_transport.py").read_text()
        changes=[
          ('H = Path("'+str(REAL_H)+'")','H = Path("'+str(cls.h)+'")'),
          ('P = Path("'+str(REAL_P)+'")','P = Path("'+str(cls.p)+'")'),
          ('INVENTORY_SHA = "'+sha(REAL_R/REAL_INV)+'"','INVENTORY_SHA = "'+sha(invpath)+'"'),
        ]
        for old,new in changes:
            assert core.count(old)==1
            core=core.replace(old,new)
        for rel in FILES:
            dst=cls.bundle/rel
            dst.write_bytes(core.encode() if rel=="server_transport.py" else (C/rel).read_bytes())
            if rel.startswith("bin/"):dst.chmod(0o755)
        manifest=json.loads((C/"bundle_manifest.json").read_bytes())
        manifest.update(control_root=str(cls.r),runtime_root=str(cls.p),
                        files={rel:sha(cls.bundle/rel) for rel in FILES})
        (cls.bundle/"bundle_manifest.json").write_bytes(canonical_json(manifest))
        cls.manifest_sha=sha(cls.bundle/"bundle_manifest.json")
        cls.t=load(cls.bundle/"server_transport.py","synthetic_transport")
        cls.t.verify_frozen()
        SYNTHETIC_DESCRIPTION.update({
          "root":str(cls.work),"real_source_count":len(inv["files"]),
          "source_files_are_actual_registered_bytes":True,
          "only_core_constant_replacements":changes,
          "inventory_only_replaced_field":"source_root_server",
          "inventory_sha_recomputed_for_isolated_roots":True,
          "scientific_modules_modified":False,"real_control_repo_written":False,
          "copied_source_bytes":2*sum((REAL_S/p).stat().st_size for p in inv["files"])
        })
    def setUp(self):
        self.area=self.h/"cases"/self._testMethodName
        self.area.mkdir(parents=True)
    def write(self,p,data=b"abc"):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
    def control(self,script,*,code="print('ok')\n",env_extra=None,extra=()):
        entry=self.r/"scripts"/(script+".py");self.write(entry,code.encode())
        audit_rel="results/formal_main_v2/control_transport/"+script+".jsonl"
        env=dict(os.environ);env["PYTHONDONTWRITEBYTECODE"]="1"
        env.update(env_extra or {})
        cmd=[sys.executable,"-B",str(self.bundle/"run_server_control.py"),
             "--bundle-manifest-sha256",self.manifest_sha,"--entrypoint","scripts/"+entry.name,
             "--entrypoint-sha256",sha(entry),"--audit-relative",audit_rel,*extra]
        result=subprocess.run(cmd,cwd=self.work,env=env,capture_output=True,timeout=40)
        audit=self.r/audit_rel
        rows=[json.loads(x) for x in audit.read_bytes().splitlines()] if audit.exists() else []
        return result,rows,audit,cmd
    def test_01_real_173_and_bundle(self):
        self.assertEqual(len(self.real.verify_frozen()),173)
        self.assertEqual(set(self.real.verify_bundle(sha(C/"bundle_manifest.json"))["files"]),set(FILES))
    def test_02_copy_binary_round_trip(self):
        raw=bytes(range(256))*513
        src=self.write(self.area/"input.jsonl",raw);dst=self.p/"scratch"/"upload.jsonl"
        dst.parent.mkdir(parents=True)
        first=self.t.copy_single(str(src),str(dst))
        out=self.area/"download.jsonl";second=self.t.copy_single(str(dst),str(out))
        self.assertEqual(out.read_bytes(),raw)
        self.assertEqual(first["sha256"],sha(src));self.assertEqual(second["bytes"],len(raw))
    def test_03_identical_is_no_write_and_different_rejected(self):
        a=self.write(self.area/"a.json",b"one");b=self.write(self.area/"b.json",b"one")
        before=b.stat()
        self.assertEqual(self.t.copy_single(str(a),str(b))["action"],"same_bytes_no_write")
        self.assertEqual((before.st_ino,before.st_mtime_ns),(b.stat().st_ino,b.stat().st_mtime_ns))
        a.write_bytes(b"two")
        with self.assertRaisesRegex(ValueError,"overwriting"):self.t.copy_single(str(a),str(b))
        self.assertEqual(b.read_bytes(),b"one")
    def test_04_ssh_unknown_shapes_before_scope(self):
        invalid=[[],["-q","tongji-cvpr","true"],["-o","BatchMode=no","tongji-cvpr","true"],
                 ["-o","BatchMode=yes","other","true"],["-o","BatchMode=yes","tongji-cvpr",""],
                 ["-o","BatchMode=yes","tongji-cvpr","printf","x"]]
        with mock.patch.object(self.t,"scope",side_effect=AssertionError("scope reached")):
            for argv in invalid:
                with self.subTest(argv=argv),self.assertRaises(ValueError):self.t.run_ssh(argv)
    def test_05_scp_unknown_shapes(self):
        for args in [[],["-r","a","b"],["-q","a","b","c"],["-q","other:/x","/x"],
                     ["-q","tongji-cvpr:/x","tongji-cvpr:/y"],["-q","/x","/y"]]:
            with self.subTest(args=args),self.assertRaises(ValueError):self.t.parse_scp(args)
    def test_06_forbidden_paths_before_filesystem(self):
        values=["/etc/passwd",str(self.h)+"/../escape",str(self.h)+"//x",
                str(self.h/"weights/x.json"),str(self.h/"checkpoints/x.json"),
                str(self.h/"results/x.pt.partial"),str(self.h/"results/x.safetensors"),
                str(self.h/"test/x.json"),str(self.h/"results/sealed_final.json"),
                str(self.h/"results/init_states_test.json"),str(self.h/"results/final_states.jsonl"),
                str(self.h/"results/panel.json"),str(self.h/"results/final_registry.json")]
        with mock.patch.object(self.t,"no_links",side_effect=AssertionError("filesystem reached")):
            for v in values:
                with self.subTest(path=v),self.assertRaises(ValueError):self.t.project_path(v)
            with self.assertRaises(ValueError):
                self.t.project_path(str(self.s/"src/ok.py"),copy_target=True)
    def test_07_legal_scientific_source_names(self):
        p=self.write(self.area/"src"/"initial_states.py",b"source")
        self.assertEqual(self.t.project_path(str(p)),p)
        self.assertEqual(self.t.project_path(str(self.h/"results/downstream/final/trials.jsonl")),
                         self.h/"results/downstream/final/trials.jsonl")
    def test_08_symlink_sources_parents_and_destinations(self):
        src=self.write(self.area/"src.json",b"x")
        for path,target in [(self.area/"link.json",src),(self.area/"parent",self.area)]:
            path.symlink_to(target)
        for a,b in [(self.area/"link.json",self.area/"a.json"),
                    (self.area/"parent/src.json",self.area/"b.json"),
                    (src,self.area/"link.json")]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):self.t.copy_single(str(a),str(b))
    def test_09_regular_file_only_no_fifo_block(self):
        fifo=self.area/"fifo.json";os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError,"regular"):self.t.copy_single(str(fifo),str(self.area/"dest.json"))
        with self.assertRaisesRegex(ValueError,"regular"):self.t.copy_single(str(self.area),str(self.area/"dest.json"))
    def test_10_no_same_path_or_missing_parent(self):
        src=self.write(self.area/"src.json")
        with self.assertRaises(ValueError):self.t.copy_single(str(src),str(src))
        with self.assertRaises(FileNotFoundError):
            self.t.copy_single(str(src),str(self.area/"missing"/"target.json"))
        self.assertFalse((self.area/"missing").exists())
    def test_11_publish_conflict_keeps_other_bytes(self):
        src=self.write(self.area/"src.json",b"new");dst=self.area/"dst.json"
        link=os.link
        def racing(*args,**kw):
            dst.write_bytes(b"other")
            return link(*args,**kw)
        with mock.patch.object(self.t.os,"link",side_effect=racing):
            with self.assertRaises(FileExistsError):self.t.copy_single(str(src),str(dst))
        self.assertEqual(dst.read_bytes(),b"other")
        self.assertEqual(len(list(self.area.glob(".dst.json.transport-*.partial"))),1)
    def test_12_source_mutation_rejected_before_publication(self):
        src=self.write(self.area/"src.json",b"start")
        original=self.t.signature;calls=[]
        def changing(st):
            calls.append(1)
            if len(calls)==1:src.write_bytes(b"changed bytes")
            return original(st)
        with mock.patch.object(self.t,"signature",side_effect=changing):
            with self.assertRaisesRegex(ValueError,"source changed"):
                self.t.copy_single(str(src),str(self.area/"dst.json"))
        self.assertFalse((self.area/"dst.json").exists())
    def test_13_bundle_change_rejected(self):
        p=self.bundle/"bin/scp";raw=p.read_bytes()
        try:
            p.write_bytes(raw+b"\n# changed\n")
            with self.assertRaisesRegex(ValueError,"source SHA"):
                self.t.verify_bundle(self.manifest_sha)
        finally:p.write_bytes(raw)
    def test_14_runner_actual_f_SSH_stdin_exit_and_grandchild(self):
        code = """import json,subprocess,sys,shlex
import formal_supervisor as f
assert f.SSH==['ssh','-o','BatchMode=yes','tongji-cvpr']
r=f.remote("printf transport_ok")
assert r=='transport_ok'
cmd=shlex.quote(sys.executable)+" -B -c "+shlex.quote("import sys; sys.stdout.buffer.write(sys.stdin.buffer.read()[::-1])")
p=subprocess.run(f.SSH+[cmd],input=b'abc\\x00xyz',capture_output=True,check=True)
assert p.stdout==b'zyx\\x00cba'
p=subprocess.run(f.SSH+["printf stderr_marker >&2; exit 7"],capture_output=True)
assert p.returncode==7 and b'stderr_marker' in p.stderr
grand="import formal_supervisor as f; print(f.remote('printf grandchild_ok'))"
p=subprocess.run([sys.executable,'-B','-c',grand],capture_output=True,check=True)
assert p.stdout==b'grandchild_ok\\n'
print(json.dumps({'original_SSH':f.SSH,'subprocess_inheritance':True}))
"""
        result,rows,audit,_=self.control("actual_f_inheritance",code=code)
        self.assertEqual(result.returncode,0,result.stderr.decode())
        self.assertEqual(rows[0]["event"],"control_start");self.assertEqual(rows[-1]["event"],"control_end")
        self.assertTrue(rows[-1]["source173_and_entrypoint_unchanged"])
        starts=[r for r in rows if r["event"]=="ssh_start"];ends=[r for r in rows if r["event"]=="ssh_end"]
        self.assertEqual(len(starts),4);self.assertEqual({r["call_id"] for r in starts},{r["call_id"] for r in ends})
        self.assertIn(7,[r["returncode"] for r in ends])
        for r in starts:self.assertEqual(r["original_argv"][:4],["ssh","-o","BatchMode=yes","tongji-cvpr"])
    def test_15_runner_preserves_entry_exit_code(self):
        result,rows,_,_=self.control("exit_code",code="import sys\nprint('out')\nprint('err',file=sys.stderr)\nraise SystemExit(23)\n")
        self.assertEqual(result.returncode,23);self.assertEqual(result.stdout,b"out\n")
        self.assertIn(b"err",result.stderr);self.assertEqual(rows[-1]["returncode"],23)
        self.assertTrue(rows[-1]["source173_and_entrypoint_unchanged"])
    def test_16_nested_scope_rejected_without_journal(self):
        result,rows,audit,_=self.control("nested_scope",env_extra={"CTI_SERVER_CONTROL_ROOT":str(self.r)})
        self.assertNotEqual(result.returncode,0);self.assertFalse(audit.exists())
        self.assertIn(b"nested transport scope",result.stderr)
    def test_17_frozen_drift_rejected_before_child(self):
        p=self.r/"scripts/formal_supervisor.py";raw=p.read_bytes()
        try:
            p.write_bytes(raw+b"\n# mutation\n")
            result,rows,audit,_=self.control("frozen_changed")
            self.assertNotEqual(result.returncode,0);self.assertFalse(audit.exists())
            self.assertIn(b"frozen bytes differ",result.stderr)
        finally:p.write_bytes(raw)
    def test_18_shim_inactive_or_outside_scope_rejected(self):
        env={k:v for k,v in os.environ.items() if not k.startswith("CTI_SERVER_CONTROL_")}
        cmd=[str(self.bundle/"bin/ssh"),"-o","BatchMode=yes","tongji-cvpr","printf must_not_run"]
        p=subprocess.run(cmd,cwd=self.r,env=env,capture_output=True)
        self.assertEqual(p.returncode,255);self.assertNotIn(b"must_not_run",p.stdout)
        audit=self.r/"results/formal_main_v2/control_transport/outside.jsonl"
        audit.parent.mkdir(parents=True,exist_ok=True);audit.write_bytes(b"")
        env.update(CTI_SERVER_CONTROL_ROOT=str(self.r),CTI_SERVER_CONTROL_BIN=str(self.bundle/"bin"),
                   CTI_SERVER_CONTROL_VERSION=self.t.VERSION,CTI_SERVER_CONTROL_MANIFEST_SHA256=self.manifest_sha,
                   CTI_SERVER_CONTROL_JOURNAL=str(audit))
        p=subprocess.run(cmd,cwd=self.work,env=env,capture_output=True)
        self.assertEqual(p.returncode,255);self.assertEqual(audit.read_bytes(),b"")
    def test_19_real_scp_shims_in_child(self):
        src=self.write(self.r/"results/upload_source.json",bytes(range(100)))
        dest=self.p/"results/transport_upload.json";dest.parent.mkdir(parents=True,exist_ok=True)
        back=self.r/"results/transport_back.json"
        code=f"""import subprocess
subprocess.run(['scp','-q','results/upload_source.json','tongji-cvpr:{dest}'],check=True)
subprocess.run(['scp','-q','tongji-cvpr:{dest}','results/transport_back.json'],check=True)
subprocess.run(['scp','-q','results/upload_source.json','tongji-cvpr:{dest}'],check=True)
"""
        result,rows,_,_=self.control("actual_scp",code=code)
        self.assertEqual(result.returncode,0,result.stderr.decode());self.assertEqual(back.read_bytes(),src.read_bytes())
        ends=[r for r in rows if r["event"]=="scp_end"]
        self.assertEqual(len(ends),3);self.assertEqual(ends[-1]["action"],"same_bytes_no_write")
    def test_20_reuse_audit_rejected(self):
        result,rows,audit,cmd=self.control("same_audit")
        self.assertEqual(result.returncode,0);raw=audit.read_bytes()
        p=subprocess.run(cmd,cwd=self.work,capture_output=True)
        self.assertNotEqual(p.returncode,0);self.assertEqual(audit.read_bytes(),raw)
    @classmethod
    def tearDownClass(cls):
        cls.real.verify_frozen()
        for p,checksum in REAL_INPUTS.items():
            assert sha(p)==checksum,"real input changed: "+p

class RecordingResult(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test);self.started=time.monotonic()
    def stopTest(self,test):
        self.timings.append((str(test),time.monotonic()-self.started))
        super().stopTest(test)
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.timings=[]

def main():
    log=C/"tests_a1.log"
    started=time.time()
    with log.open("x") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordingResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(TransportTests))
    suite=ET.Element("testsuite",name="server_transport_v1_cpu",tests=str(result.testsRun),
                     failures=str(len(result.failures)),errors=str(len(result.errors)),
                     skipped=str(len(result.skipped)),time=str(time.time()-started))
    failures={str(t):tb for t,tb in result.failures};errors={str(t):tb for t,tb in result.errors}
    for name,seconds in result.timings:
        case=ET.SubElement(suite,"testcase",name=name,time=str(seconds))
        if name in failures:ET.SubElement(case,"failure").text=failures[name]
        if name in errors:ET.SubElement(case,"error").text=errors[name]
    with (C/"tests_a1.xml").open("xb") as f:f.write(ET.tostring(suite,encoding="utf-8",xml_declaration=True))
    out={"status":"passed_CPU_only" if result.wasSuccessful() else "failed_CPU_only",
         "tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
         "skipped":len(result.skipped),"wall_seconds":time.time()-started,
         "python":sys.version,"scope":SYNTHETIC_DESCRIPTION,
         "real_173_R_and_S_before_after":True,
         "read_evidence_sha256":REAL_INPUTS,
         "test_source_sha256":sha(__file__),"log_sha256":sha(log),
         "xml_sha256":sha(C/"tests_a1.xml")}
    with (C/"tests_a1.json").open("xb") as f:f.write(canonical_json(out))
    print(json.dumps({k:out[k] for k in ("status","tests","failures","errors","skipped","wall_seconds")}))
    return 0 if result.wasSuccessful() else 1

if __name__=="__main__":raise SystemExit(main())
