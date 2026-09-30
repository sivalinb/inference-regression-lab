"""Explicit public-source catalogue, bounded downloads, hashes, and provenance."""
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import requests


def catalogue(root):
    return json.loads((Path(root) / "data/sources.json").read_text())


def fetch_source(root, source_id):
    source = next(x for x in catalogue(root) if x["id"] == source_id)
    url = source["download_url"]
    allowed = {"raw.githubusercontent.com", "api.github.com", "earthquake.usgs.gov", "huggingface.co"}
    if urlparse(url).scheme != "https" or urlparse(url).hostname not in allowed:
        raise ValueError("Source URL is outside the public-data allowlist")
    data = bytearray()
    # Redirects must be separately reviewed in the catalogue; prevent SSRF through them.
    with requests.get(url, timeout=(5, 30), stream=True, allow_redirects=False,
                      headers={"User-Agent": "PortfolioInfrastructureLabs/1.0"}) as response:
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Source returned a redirect or non-content response")
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 15_000_000:
                raise ValueError("Public source exceeds 15 MB download budget")
    directory = Path(root) / "artifacts/sources"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (source_id + ".data")
    path.write_bytes(data)
    provenance = {**source, "retrieved_at": time.time(), "sha256": hashlib.sha256(data).hexdigest(),
                  "bytes": len(data), "local_path": str(path)}
    path.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2))
    return provenance
