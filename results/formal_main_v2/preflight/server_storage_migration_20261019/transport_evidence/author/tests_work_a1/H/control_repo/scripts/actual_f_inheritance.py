import json,subprocess,sys,shlex
import formal_supervisor as f
assert f.SSH==['ssh','-o','BatchMode=yes','tongji-cvpr']
r=f.remote("printf transport_ok")
assert r=='transport_ok'
cmd=shlex.quote(sys.executable)+" -B -c "+shlex.quote("import sys; sys.stdout.buffer.write(sys.stdin.buffer.read()[::-1])")
p=subprocess.run(f.SSH+[cmd],input=b'abc\x00xyz',capture_output=True,check=True)
assert p.stdout==b'zyx\x00cba'
p=subprocess.run(f.SSH+["printf stderr_marker >&2; exit 7"],capture_output=True)
assert p.returncode==7 and b'stderr_marker' in p.stderr
grand="import formal_supervisor as f; print(f.remote('printf grandchild_ok'))"
p=subprocess.run([sys.executable,'-B','-c',grand],capture_output=True,check=True)
assert p.stdout==b'grandchild_ok\n'
print(json.dumps({'original_SSH':f.SSH,'subprocess_inheritance':True}))
