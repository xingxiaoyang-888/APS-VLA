from pathlib import Path
import ast,difflib,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/last_two_training_independent_20261020T1644'
G=R/'.local/Goal64s41_independent_20261020T1644/audit_3043877_v2.py';O=R/'.local/independent_object3042627_0626/audit_3042627_a4.py'
assert hashlib.sha256(G.read_bytes()).hexdigest()=='6a158d05bad33edda60260afb7375916892303a3b60fda51b85bb3496bb01e46'
assert hashlib.sha256(O.read_bytes()).hexdigest()=='c3cd34abcab95324e962bf54099d4aed223c53f3b980d3ea91c5f38fc66e7792'
g=G.read_text();o=O.read_text();originals={'goal':g,'object':o};changes=[]
def replace(text,a,b):
 assert a in text,('missing',a)
 changes.append({'before':a,'after':b,'occurrences':text.count(a)})
 return text.replace(a,b)
for a,b in [('.local/Goal64s41_independent_20261020T1644','.local/last_two_training_independent_20261020T1644/goal'),('Goal64 seed41','Goal64 seed23'),('seed41','seed23'),('seed"]==41','seed"]==23'),('seed=41','seed=23'),('random.Random(41)','random.Random(23)'),('3043877','3043813'),('59575','66792'),('52f6f42a36e14f90b7e9bdd1e7ec0f0e','2f71f57773be4dc38b46df6b6b9f4462'),('0d005f0dd0f61a637fb3e5b4b579d910777fb864b7f3bd12e0960d0d3592cc20','59ff64687a3bf18e78f1c8abe08b19876b97266b6609b2731c283e749b02869c'),('ba5a413defe4164a6078d59c82f9173b0b1fdee6bebc57a4fddd6c4994ebfbc0','114b689809bc9350e70058e7060d51e62ac6d3f62d4274e34913a2b4b6ef1f04'),('20261020T154007Z_c117dc57f32d','20261020T170126Z_1fd1cd88b439'),('3100cca98ad41b65f10ed707455462bcf845ae0aba513d96160ad44d777a9750','f0633ec7db1a6f09aa92afb332d452e91f81c9d69c6c356bf27df45bdb338036'),('b6f947a447216acff534e30cbc3d958fe86707000da4ce086e2479e0b1502ce9','3a1e7d25d11edc7098e2af832aca9a6edbf1defc4241c0311e529768932d34f7'),('c08fb4bcfcab748885f45216b9d800350849854aba39cad76f5d254c634bd587','20a6cdb948eece17adb847941526f933b93b1ed59ed02a24a77b15ce3ca0ddc1'),('3043813_8493c542000b','3043813_2789ee1aca97')]:g=replace(g,a,b)
g=replace(g,'def main():\n'.replace('\\n','\n'),'def main():\n'.replace('\\n','\n')) if False else g
g=replace(g,'def main():\n'.encode().decode('unicode_escape'),'def main():\n need(len(sys.argv)==2,"one exact bindings SHA")\n bindings=read(".local/last_two_training_independent_20261020T1644/goal/bindings.json",sys.argv[1])\n'.encode().decode('unicode_escape'))
g=replace(g,'canonical_sha="121ea7c85950ee7b162b642e2e14880f2ec1eb4a1ffcfe3cf34a9ab2b19f6c60"','canonical_sha=bindings["root"]["sha256"]\n need(bindings["root"]["path"]==canonical_ref,"exact root scope")'.encode().decode('unicode_escape'))
g=replace(g,'root_best_ref="results/formal_main_v2/preflight/heartbeat_20261021T0044/3043813_selected_server.json"','root_best_ref=bindings["selected"]["path"]')
g=replace(g,'root_best_sha="2731875fc1c0b0a9ef9c57e433fa682969ebf2f172c903dbde89aafb02a73e8c"','root_best_sha=bindings["selected"]["sha256"]')
g=replace(g,'root_terminal_ref="results/formal_main_v2/preflight/heartbeat_20261021T0044/3043813_root_terminal.json"','root_terminal_ref=bindings["root_terminal"]["path"]')
g=replace(g,'read(root_terminal_ref,"1fc9190ec8ea26c2a655cb9a5c90913f0410ec05b23487475f895871fdede835")','read(root_terminal_ref,bindings["root_terminal"]["sha256"])')
a=g.index(' archive_inputs_ref=');b=g.index(' raw(Path(__file__)',a)
g=g[:a]+' archive_review={"status":"not_claimed_here","reason":"All original raw logs independently parsed and R/P SHA verified. Archive/Git publication is a separate root delivery transaction."}\n'.encode().decode('unicode_escape')+g[b:]
for a,b in [('.local/independent_object3042627_0626','.local/last_two_training_independent_20261020T1644/object'),('3042627','3044844'),('3039258','3044017'),('3028460','3028468'),('k256','k64'),('visual_tokens"]==256','visual_tokens"]==64'),('visual_tokens=256','visual_tokens=64'),('tokens_per_camera"]==128','tokens_per_camera"]==32'),('per_camera_budgets"]==[128,128]','per_camera_budgets"]==[32,32]'),('len(ids)==256','len(ids)==64'),('sum(i<256 for i in ids)==128','sum(i<256 for i in ids)==32'),('hard256 original packing','hard64 original packing'),('COSTS=[84,6512,52321]','COSTS=[69,5141,47658]'),('58917','52868'),('6596','5210'),('52321','47658'),('6512','5141'),('retained_failed_GPU_seconds":84','retained_failed_GPU_seconds":69'),('its84GPU','its69GPU')]:o=replace(o,a,b)
o=replace(o,'engineering/terminal_delivery_0943/independent/audit_3044017.py','engineering/terminal_delivery_0943/independent/audit_3039258.py')
o=replace(o,'5f86034d43017d3f89b0d3a73cd90dd8bd22b0b8a54461d0b0a51e5f8df6220e','6619bd4e9a8e75b76200bca401a861bc5c6c1180a54c37cf739da18f55ea019c')
o=replace(o,'3044844_7500f0544661','3044844_83189d165da2')
a=o.index(' archive_inputs=refread(');b=o.index(' raw(Path(__file__)',a)
o=o[:a]+' archive_review={"status":"not_claimed_here","reason":"Original raw journals from both successful attempts independently parsed, historical boundary evidence preserved, and scoped R/P bytes verified. Root handles lossless Git archives separately."}\n historical_raw=[]\n'.encode().decode('unicode_escape')+o[b:]
helperfuncs=g[g.index('def validate_hard64_observation'):g.index('def audit_inherited_goal_resume')]
o=replace(o,'def refread(ref):return read(ref["path"],ref["sha256"])\n'.encode().decode('unicode_escape'),'def refread(ref):return read(ref["path"],ref["sha256"])\n'.encode().decode('unicode_escape')+helperfuncs)
a=o.index('      ref=lookup[x["window_id"]];need(');b=o.index('     need(len(task)==10',a)
o=o[:a]+'      ref=lookup[x["window_id"]];validate_hard64_observation(x,ref);task[str(x["task_id"])].append(x)\n'.encode().decode('unicode_escape')+o[b:]
o=replace(o,'best=min(vals.values(),key=lambda v:(v["teacher_l1"],v["update"]))','best=select_validation(vals)')
o=replace(o,'replayed_or_uncommitted_samples=0)','replayed_or_uncommitted_samples=0,committed_sampling_by_task=sampling,window_pool_coverage=len(set(sampleids))/44068,window_pool_equivalent_traversals=40000/44068)')
for name,text,src in [('goal',g,G),('object',o,O)]:
 dd=D/name;dd.mkdir(exist_ok=True);out=dd/f'audit_{"3043813" if name=="goal" else "3044844"}_v1.py';ast.parse(text)
 with out.open('x') as f:f.write(text)
 diff=''.join(difflib.unified_diff(originals[name].splitlines(True),text.splitlines(True),fromfile=str(src.relative_to(R)),tofile=str(out.relative_to(R))))
 (dd/'template_diff_v1.patch').write_text(diff)
 print(str(out.relative_to(R)),hashlib.sha256(out.read_bytes()).hexdigest(),len(text.splitlines()))
(D/'source_derivation.json').write_text(json.dumps({'templates':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [G,O]],'changes':changes,'scope':'CPU independent training evidence audit only; no state, Git, scheduler, GPU or scientific release writes'},indent=2,ensure_ascii=False)+'\n'.encode().decode('unicode_escape'))
