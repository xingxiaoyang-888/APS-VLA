"""Explicit server control entry; never changes f.SSH or any scientific code."""
from __future__ import annotations
import argparse
import importlib.util
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_cti_server_control_transport", HERE / "server_transport.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle-manifest-sha256", required=True)
    ap.add_argument("--entrypoint", required=True)
    ap.add_argument("--entrypoint-sha256", required=True)
    ap.add_argument("--audit-relative", required=True)
    ap.add_argument("arguments", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    t.verify_bundle(args.bundle_manifest_sha256)
    pp = PurePosixPath(args.entrypoint)
    t.require(not pp.is_absolute() and pp.as_posix() == args.entrypoint and ".." not in pp.parts
              and pp.parts[0] in {"scripts", ".local"} and pp.suffix == ".py",
              "entrypoint must be an explicit control-repo Python script")
    entry = t.no_links(t.R / args.entrypoint)
    t.require(t.R in entry.parents and t.file_sha(entry) == args.entrypoint_sha256, "entrypoint SHA differs")
    audit_rel = PurePosixPath(args.audit_relative)
    t.require(not audit_rel.is_absolute() and audit_rel.as_posix() == args.audit_relative
              and ".." not in audit_rel.parts, "invalid relative audit path")
    audit = t.journal_path(str(t.R / args.audit_relative))
    t.require(not audit.exists(), "audit already exists; inspect prior invocation")
    env = os.environ.copy()
    t.require(not any(k.startswith(t.PREFIX) for k in env), "nested transport scope rejected")
    frozen = t.verify_frozen()
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("xb") as f:
        f.flush(); os.fsync(f.fileno())
    env.update({
        t.PREFIX + "ROOT": str(t.R), t.PREFIX + "BIN": str(HERE / "bin"),
        t.PREFIX + "MANIFEST_SHA256": args.bundle_manifest_sha256,
        t.PREFIX + "JOURNAL": str(audit), t.PREFIX + "VERSION": t.VERSION,
        "PATH": str(HERE / "bin") + os.pathsep + env.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(t.R / "src") + os.pathsep + str(t.R / "scripts")
                       + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""),
    })
    arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
    command = [sys.executable, "-B", str(entry), *arguments]
    t.emit(audit, "control_start", entrypoint=args.entrypoint, entrypoint_sha256=args.entrypoint_sha256,
           command=command, control_root=str(t.R), runtime_root=str(t.P),
           frozen_source_root=str(t.S), frozen_files=len(frozen),
           bundle_manifest_sha256=args.bundle_manifest_sha256,
           original_SSH_list_unchanged=True)
    code, unchanged = 125, False
    try:
        code = subprocess.run(command, cwd=t.R, env=env).returncode
    finally:
        try:
            t.verify_bundle(args.bundle_manifest_sha256)
            t.verify_frozen()
            t.require(t.file_sha(entry) == args.entrypoint_sha256, "entrypoint changed during control run")
            unchanged = True
        finally:
            t.emit(audit, "control_end", returncode=code, source173_and_entrypoint_unchanged=unchanged)
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    raise SystemExit(main())
