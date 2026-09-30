"""Run from the repository root after editing the Pkl source."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
source = root / "config/default.pkl"
binary = os.environ.get("PKL_BIN") or shutil.which("pkl")
if not binary:
    raise SystemExit("Install Pkl or set PKL_BIN")
config = json.loads(subprocess.check_output([binary, "eval", "--format", "json", str(source)], text=True))
snapshot = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "config": config}
(source.with_suffix(".json")).write_text(json.dumps(snapshot, indent=2) + "\n")
print("Exported", source.with_suffix(".json"))
