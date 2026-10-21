from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_full200_author_20261021T0110';K=D/'package'
hist=D/'before_outer_hardening';hist.mkdir(exist_ok=False)
for name in ['entry.py','consumer.py','paired_input_gate_v1.py']:(hist/name).write_bytes((K/name).read_bytes())
p=K/'entry.py';s=p.read_text()
# Typed equality rejects JSON true as 1 and false as 0.
s=s.replace("def require(ok,msg):","def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)\ndef require(ok,msg):")
for o,n in [("c.get(k)==v","same(c.get(k),v)"),("a.get(k)==v","same(a.get(k),v)"),("value.get(k)==v","same(value.get(k),v)"),("d.get(k)==v","same(d.get(k),v)"),("res.get(k)==v","same(res.get(k),v)")]:s=s.replace(o,n)
s=s.replace("  with eventpath.open('a',encoding='utf-8')","  require(len(events)<1024 and len(json.dumps(row,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())<=65536,'outer event storage bound exceeded; fail closed without truncation')\n  with eventpath.open('a',encoding='utf-8')")
p.write_text(s)
p=K/'paired_input_gate_v1.py';s=p.read_text()
s=s.replace("    # Preserve returned numeric actions", "    self._need(len(jbytes(dict(chunk.metadata)))<=32768,'returned metadata exceeds original-ledger storage bound')\n    # Preserve returned numeric actions")
p.write_text(s)
p=K/'consumer.py';s=p.read_text()
needle="   require(set(arrays)=={'agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'},'all five raw arrays')"
s=s.replace(needle,needle+"\n   expected_schema={'agentview_image':('uint8',[256,256,3],196608),'robot0_eye_in_hand_image':('uint8',[256,256,3],196608),'robot0_eef_pos':('float64',[3],24),'robot0_eef_quat':('float64',[4],32),'robot0_gripper_qpos':('float64',[2],16)}\n   require(all((arrays[k]['dtype'],arrays[k]['shape'],arrays[k]['bytes'])==v for k,v in expected_schema.items()),'exact actual five-component storage schema')")
s=s.replace("c=row['chunks'][qi];require", "c=row['chunks'][qi];require(len(canonical(c['metadata']))<=32768,'original chunk metadata storage bound');require")
old="   require(ev.watch(row['path'])==row['sha256']"
assert old not in s # actual two spaces
old="  require(ev.watch(row['path'])==row['sha256'] and ev.path(row['path']).stat().st_size==row['bytes'],'pulled bytes changed');files[row['path']]=row['sha256']"
assert s.count(old)==1
new="""  blobprefix=OUT+'/observer/blobs/'
  if row['path'].startswith(blobprefix):
   tail=row['path'][len(blobprefix):];require(re.fullmatch('[0-9a-f]{64}(?:[.]bin|[.]rng[.]json)',tail),'only exact content-addressed passive sim/RNG blobs')
   path=project/row['path'];require(path.resolve()==path and not any(x.is_symlink() for x in [path,*path.parents]),'local passive blob symlink')
   data=path.read_bytes();require(digest(data)==row['sha256'] and len(data)==row['bytes']<=65536 and tail.startswith(digest(data)+'.'),'local passive blob bytes')
  else:require(ev.watch(row['path'])==row['sha256'] and ev.path(row['path']).stat().st_size==row['bytes'],'pulled bytes changed')
  files[row['path']]=row['sha256']"""
s=s.replace(old,new)
s=s.replace(" ev.unchanged()\n return", " for path,v in rawproof['raw_blob_refs'].items():\n  data=Path(path).read_bytes();require(digest(data)==v['sha256'] and len(data)==v['bytes'],'raw blob changed during reconstruction')\n ev.unchanged()\n return")
p.write_text(s)
for p in K.glob('*.py'):ast.parse(p.read_text())
m=json.loads((K/'package_manifest.json').read_bytes());m['version']='goal-full200-prospective-single-attempt-v1';m['files']={('scripts/ops/formal_goal_full200_gate_v1/'+p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(K.iterdir()) if p.is_file() and p.name!='package_manifest.json'}
(K/'package_manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
print(json.dumps({'manifest':hashlib.sha256((K/'package_manifest.json').read_bytes()).hexdigest(),'files':m['files']}))
