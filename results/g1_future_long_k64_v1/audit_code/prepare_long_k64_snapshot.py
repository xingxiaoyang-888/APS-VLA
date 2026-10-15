from pathlib import Path
import hashlib, json, subprocess, tarfile

root = Path('F:/CTI-VLA')
dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', 'src', 'scripts', 'configs', 'tests', 'AGENTS.md', 'pyproject.toml'], cwd=root, text=True)
if dirty.strip():
    raise SystemExit('Commit the reviewed source before freezing: ' + dirty)
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode('utf-8').split('\0')
selected = sorted(p for p in paths if p and (p.startswith(('src/', 'scripts/', 'configs/', 'tests/'))
    or p in ('AGENTS.md', 'README.md', 'pyproject.toml', '.gitattributes')))
files = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in selected}
inventory = {
    'base_or_current_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'dirty': False, 'tracked_only': True, 'files': files,
    'source_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
    'source_root_server': '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/g1_future_long_k64_v1',
}
out = root / 'results/g1_future_long_k64_v1'
out.mkdir(parents=True, exist_ok=True)
manifest = out / 'source_g1_future_long_k64_v1.json'
if manifest.exists():
    raise SystemExit('Source inventory already frozen; do not replace it silently')
manifest.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
archive = root / '.local/g1_future_long_k64_v1.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for p in selected:
        tar.add(root / p, arcname=p, recursive=False)
    tar.add(manifest, arcname='source_manifest.json', recursive=False)
print(json.dumps({'source_sha256':inventory['source_sha256'], 'files':len(files),
                  'archive':str(archive), 'bytes':archive.stat().st_size}))
