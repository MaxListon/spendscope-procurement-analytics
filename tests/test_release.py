"""Release checks catch missing static dependencies and stale generated artifacts."""

from html.parser import HTMLParser
from pathlib import Path
import json
import subprocess
import sys
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src") and v:
                self.paths.append(v)


def test_local_dashboard_assets_exist():
    for page in ("index.html", "research.html"):
        path = ROOT / "docs" / page
        parser = Links()
        parser.feed(path.read_text())
        for link in parser.paths:
            parsed = urlsplit(link)
            if not parsed.scheme and parsed.path:
                target = (path.parent / unquote(parsed.path)).resolve()
                assert target.is_relative_to((ROOT / "docs").resolve())
                assert target.is_file(), f"{page}: missing {link}"


def test_executed_r_has_substantial_outputs():
    d = json.loads((ROOT / "reports/r_analysis.json").read_text())
    assert d["replicates"] == 500
    assert len(d["categories"]) >= 9
    assert len(d["buyers"]) == 30
    assert all(0 < r["hhi"] <= 10000.00001 for r in d["buyers"])


def test_artifact_fingerprints():
    subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")], check=True)


def test_manifest_contains_only_portable_analysis_inputs():
    manifest = json.loads((ROOT / "reports/build_manifest.json").read_text())
    assert all(
        ".egg-info/" not in name and "__pycache__/" not in name
        for name in manifest["inputs"]
    )
