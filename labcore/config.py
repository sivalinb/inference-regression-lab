"""Evaluate trusted, repository-owned Pkl; verify offline snapshots."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def load_config(root: Path):
    source = root / "config/default.pkl"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    binary = os.environ.get("PKL_BIN") or shutil.which("pkl")
    if binary:
        result = subprocess.run(
            [binary, "eval", "--format", "json", str(source)],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return json.loads(result.stdout), {"mode": "Pkl evaluated", "sha256": digest}
    snapshot = json.loads((root / "config/default.json").read_text())
    if snapshot["source_sha256"] != digest:
        raise ValueError("Pkl snapshot is stale. Run python scripts/export_config.py with Pkl installed.")
    return snapshot["config"], {"mode": "Verified exported snapshot", "sha256": digest}
