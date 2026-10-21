from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_runtime_20261021T0449';Q=D/'package';O=R/'scripts/ops/formal_goal_full200_gate_v1'
s=(O/'consumer.py').read_text()
s=s.replace("PKG='scripts/ops/formal_goal_full200_gate_v1';STAGE='goal_full200_20261021T0110'\nOUT='results/formal_main_v2/engineering/'+STAGE+'/attempt01'\nRUN=OUT+'/original_run'\nRAW=R/'results/formal_main_v2/raw_runtime'/STAGE/'attempt01'\nVERSION='goal-full200-prospective-single-attempt-v1'","PKG='scripts/ops/formal_goal_remaining5_gate_v1'\nVERSION='goal-remaining5-prospective-single-attempt-v1'")
s=s.replace("SPEC_SHA='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'\n","")
t=ast.parse(s)
mapping={'STAGE':'stage_key','OUT':'OUT','RUN':'RUN','RAW':'RAW','SPEC_SHA':'spec_sha'}
names={'validate_job','read_blob','reconstruct_gate'}
class Scope(ast.NodeTransformer):
 def visit_Name(self,n):
  if n.id in mapping:return ast.copy_location(ast.Attribute(value=ast.Name(id='ctx',ctx=ast.Load()),attr=mapping[n.id],ctx=n.ctx),n)
  return n
 def visit_Call(self,n):
  n=self.generic_visit(n)
  if isinstance(n.func,ast.Name) and n.func.id in names:n.args.insert(0,ast.Name(id='ctx',ctx=ast.Load()))
  return n
for i,n in enumerate(t.body):
 if isinstance(n,ast.FunctionDef) and n.name in names|{'review_terminal'}:
  n=Scope().visit(n)
  if n.name in names:n.args.args.insert(0,ast.arg(arg='ctx'))
  t.body[i]=n
ast.fix_missing_locations(t);s=ast.unparse(t)+'\n'
s=s.replace("goal_full200","goal_remaining5")
s=s.replace("root = Path(project) / ctx.OUT","root = ctx.RAW")
s=s.replace("'A256_seed17'","ctx.methods[0]").replace("'B256_seed17'","ctx.methods[1]")
# Slot identity cannot be dropped from either raw journal or typed envelope.
needle="require(gate[0]['CPU_fixture_enabled'] is False"
s=s.replace(needle,"require(gate[0]['pair_key']==ctx.pair_key and gate[0]['prefix_sha256']==ctx.spec_sha,'exact new pair raw gate identity')\n    "+needle)
s=s.replace("original = project / 'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json'\n    require(digest(original.read_bytes()) == 'c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803', 'original science lineage')",
"""terminal_path=project/terminal_ref['path']
    require(digest(terminal_path.read_bytes())==terminal_ref['sha256'],'exact terminal reference')
    rawterminal=strict(terminal_path.read_bytes())
    ctx=scope.context(rawterminal['pair_key'])
    original=project/ctx.ORIGINAL.relative_to(P)
    require_path_identity(original)
    # Exact future prepared invocation is pinned by this pair root authorization.
    authpath=project/ctx.AUTH.relative_to(P)
    authraw=strict(authpath.read_bytes())
    require(authraw['original_invocation']=={'path':str(ctx.ORIGINAL),'sha256':digest(original.read_bytes())},'own exact prepared science lineage')
    effective=strict((project/ctx.plans['effective_plan']['path']).read_bytes())
    require(digest((project/ctx.plans['effective_plan']['path']).read_bytes())==ctx.plans['effective_plan']['sha256'],'own effective plan pin')""")
s=s.replace("config = ev.read(PKG + '/config.json')\n    entry.validate_config(config)","configrel=ctx.CONFIG.relative_to(P).as_posix()\n    config=ev.read(configrel)\n    entry.validate_config(ctx,config)")
s=s.replace("ev.watch(PKG + '/config.json')","ev.watch(configrel)")
s=s.replace("entry.validate_authorization(auth,","entry.validate_authorization(ctx,auth,")
s=s.replace("entry.validate_dispatch(dispatch,","entry.validate_dispatch(ctx,dispatch,")
s=s.replace("entry.check_review(value,","entry.check_review(ctx,value,")
s=s.replace("inventory = terminal['artifacts']","require(terminal['pair_key']==ctx.pair_key and terminal['authorization']['path']==ctx.AUTH.relative_to(P).as_posix() and terminal['dispatch']['path']==ctx.DISPATCH.relative_to(P).as_posix() and terminal['reservation']['path']==ctx.RESERVATION.relative_to(P).as_posix(),'exact pair terminal control refs')\n    require({k:inv[k] for k in effective['invocation']}==effective['invocation'],'prepared original plan reconstructed')\n    inventory = terminal['artifacts']")
a=s.index("    for row in inventory:");b=s.index("    complete = ev.read",a)
s=s[:a]+'''    for row in inventory:
        require(row['path'].startswith(ctx.OUT+'/') and '/observer/' not in row['path'],'only P scientific/outer metadata, never fake observer relocation')
        require(ev.watch(row['path'])==row['sha256'] and ev.path(row['path']).stat().st_size==row['bytes'],'pulled P metadata changed')
        files[row['path']]=row['sha256']
    for name in ['outer/completion.json','outer/events.jsonl','outer/typed_parent.json','original_run/config.json','original_run/panel.json','original_run/trials.jsonl','original_run/closed_loop_report.json']:
        require(ctx.OUT+'/'+name in files,'missing actual scientific metadata: '+name)
    rawfiles=validate_raw_inventory(ctx,terminal['raw_artifacts'])
'''+s[b:]
s=s.replace("spec = ev.read(PKG + '/specification.json')\n    require(ev.watch(PKG + '/specification.json') == ctx.spec_sha","specrel=ctx.SPEC.relative_to(P).as_posix()\n    spec = ev.read(specrel)\n    require(ev.watch(specrel) == ctx.spec_sha")
s=s.replace("ev.unchanged()","require(set(rawproof['raw_blob_refs']).issubset(set(rawfiles)), 'every reconstructed physical blob inventoried')\n    validate_raw_inventory(ctx,terminal['raw_artifacts'])\n    ev.unchanged()")
s=s.replace("'terminal_ref': terminal_ref","'pair_key':ctx.pair_key,'terminal_ref': terminal_ref")
s=s.replace("'evidence_sha256': ev.files","'physical_raw_artifacts':rawfiles,'evidence_sha256': ev.files")
# Insert scope loader without importing an old exclusive module or changing globals.
i=s.index('def require(')
s=s[:i]+'''def _scope():
    p=Path(__file__).parent/'scope.py'
    spec=importlib.util.spec_from_file_location('_goal_remaining5_consumer_scope',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
scope=_scope()
def require_path_identity(path):
    require(path.is_absolute() and path.resolve()==path and not any(x.is_symlink() for x in [path,*path.parents]),'canonical physical path required')
def validate_raw_inventory(ctx,rows):
    require(type(rows) is list and rows and len({r['path'] for r in rows})==len(rows),'unique complete R raw inventory')
    files={}
    for row in rows:
        path=Path(row['path']);require_path_identity(path)
        require(ctx.RAW in path.parents and path.is_file() and type(row['bytes']) is int and row['bytes']>=0,'only own physical R raw attempt')
        rel=path.relative_to(ctx.RAW).as_posix()
        allowed=(rel in ('claim.json','runtime.stdout','runtime.stderr','observer/events.jsonl','observer/gate.jsonl') or re.fullmatch('[0-9a-f]{64}[.]bin',rel) or re.fullmatch('observer/blobs/[0-9a-f]{64}(?:[.]bin|[.]rng[.]json)',rel))
        require(allowed,'unknown physical raw artifact')
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(8<<20),b''):h.update(chunk)
        require(h.hexdigest()==row['sha256'] and path.stat().st_size==row['bytes'],'actual R raw bytes differ')
        files[str(path)]={'sha256':row['sha256'],'bytes':row['bytes']}
    require({str(p) for p in ctx.RAW.rglob('*') if p.is_file()}==set(files),'complete R inventory without omitted physical artifacts')
    for rel in ('claim.json','runtime.stdout','runtime.stderr','observer/events.jsonl','observer/gate.jsonl'):require(str(ctx.RAW/rel) in files,'missing R evidence')
    return files
'''+s[i:]
ast.parse(s)
with (Q/'consumer.py').open('x') as f:f.write(s)
print(json.dumps({'status':'new_context_typed_consumer_written','sha256':hashlib.sha256(s.encode()).hexdigest()}))
