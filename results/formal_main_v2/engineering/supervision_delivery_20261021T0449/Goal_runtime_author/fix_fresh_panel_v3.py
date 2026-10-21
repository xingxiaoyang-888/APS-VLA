from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_runtime_20261021T0449';Q=D/'package'
for n in ('entry.py','consumer.py'):
 with (Q/(n+'.pre_fresh_panel_v3')).open('xb') as f:f.write((Q/n).read_bytes())
e=(Q/'entry.py').read_text()
e=e.replace("panelpath = Path(inv['run_root']) / 'panel.json'","panelpath = P/'configs/manifests/formal_main_v2/libero_goal/initial_states/development.json'")
needle="a=original_ctx['args']"
e=e.replace(needle,needle+"\n require(Path(a.development_panel)==P/'configs/manifests/formal_main_v2/libero_goal/initial_states/development.json','exact original input development panel, no fabricated historical output')")
e=e.replace("return dict(original_panel=ref(panelpath),","return dict(original_panel=ref(panelpath),panel_is_original_input_not_old_output=True,")
c=(Q/'consumer.py').read_text()
c=c.replace("panel = ev.read(Path(inv['run_root']).relative_to(P).as_posix() + '/panel.json')","panel = ev.read('configs/manifests/formal_main_v2/libero_goal/initial_states/development.json')\n    require(ev.watch('configs/manifests/formal_main_v2/libero_goal/initial_states/development.json')=='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9','original development input panel exact')")
for n,s in [('entry.py',e),('consumer.py',c)]:
 ast.parse(s);(Q/n).write_text(s)
with (D/'fresh_panel_v3_result.json').open('x') as f:json.dump({'status':'fresh_input_panel_dependency_corrected','old_outputs_created':False,'entry_sha256':hashlib.sha256(e.encode()).hexdigest(),'consumer_sha256':hashlib.sha256(c.encode()).hexdigest(),'reason':'Old full200 had old outputs; the five fresh original plans do not. Read the original already-validated development input, never fabricate old run artifacts.'},f,indent=2)
print(json.dumps({'status':'fresh_panel_fixed','entry':hashlib.sha256(e.encode()).hexdigest(),'consumer':hashlib.sha256(c.encode()).hexdigest()}))
