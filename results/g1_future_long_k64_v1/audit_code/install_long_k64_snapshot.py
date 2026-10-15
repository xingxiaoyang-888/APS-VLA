"""Uploaded to this project's .local; installs one new immutable source copy."""
from pathlib import Path
import hashlib, json, tarfile

project = Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA').resolve()
target = project / 'snapshots/g1_future_long_k64_v1'
if target.exists():
    raise SystemExit('Snapshot already exists; refusing to replace it')
archive = project / '.local/g1_future_long_k64_v1.tar.gz'
target.mkdir()
with tarfile.open(archive, 'r:gz') as tar:
    for item in tar.getmembers():
        final = (target / item.name).resolve()
        if target not in final.parents or not item.isfile():
            raise ValueError('Unsafe or unexpected archive member')
    tar.extractall(target)
manifest = json.loads((target / 'source_manifest.json').read_text(encoding='utf-8'))
for name, digest in manifest['files'].items():
    if hashlib.sha256((target / name).read_bytes()).hexdigest() != digest:
        raise ValueError('Snapshot file mismatch: ' + name)
assert hashlib.sha256(json.dumps(manifest['files'], sort_keys=True).encode()).hexdigest() == manifest['source_sha256']
print(json.dumps({'status':'verified', 'files':len(manifest['files']), 'source_sha256':manifest['source_sha256']}))
