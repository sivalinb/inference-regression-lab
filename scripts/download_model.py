"""Download a pinned, ~101 MiB public GGUF model and verify its SHA-256."""
from pathlib import Path
import hashlib
import json
import time
import requests

root=Path(__file__).resolve().parents[1]
name='SmolLM2-135M-Instruct-Q4_K_M.gguf'
url='https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/09816acd5d99df7be770d85ea30822623dab342c/'+name
expected='2e8040ceae7815abe0dcb3540b9995eaa1fa0d2ca9e797d0a635ae4433c68c2d'
directory=root/'artifacts/models'
directory.mkdir(parents=True,exist_ok=True)
target=directory/name
if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==expected:
    print(target)
    raise SystemExit(0)
partial=directory/(name+'.partial')
digest=hashlib.sha256()
total=0
try:
    with requests.get(url,stream=True,timeout=(10,45)) as response:
        response.raise_for_status()
        with partial.open('wb') as f:
            for chunk in response.iter_content(1024*1024):
                total+=len(chunk)
                if total>128*1024*1024: raise ValueError('Model exceeded pinned download size budget')
                digest.update(chunk);f.write(chunk)
    if digest.hexdigest()!=expected: raise ValueError('Model checksum mismatch')
    partial.replace(target)
except BaseException:
    partial.unlink(missing_ok=True)
    raise
(directory/'provenance.json').write_text(json.dumps({'url':url,'sha256':expected,'bytes':total,'license':'Apache-2.0','retrieved_at':time.time()},indent=2))
print(target)
