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
    for page in (
        "index.html",
        "research.html",
        "case-studies.html",
        "walkthrough.html",
        "workspace.html",
    ):
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


def test_executed_analysis_uses_process_clusters_and_review_inputs():
    d = json.loads((ROOT / "reports/r_analysis.json").read_text())
    assert d["unit"] == "procurement process (ocid)"
    assert all(r["processes"] <= r["awards"] for r in d["categories"])
    assert any(r["processes"] < r["awards"] for r in d["categories"])
    manifest = json.loads((ROOT / "reports/build_manifest.json").read_text())
    assert "data/review/identity_decisions.csv" in manifest["inputs"]
    assert "data/review/notice_checks.json" in manifest["inputs"]
    assert "data/review/baseline_v01.json" in manifest["inputs"]


def test_placeholder_suppliers_are_not_exported_as_real_suppliers():
    import pandas as pd
    from spendscope.normalize import normalized_name, is_placeholder

    suppliers = pd.read_csv(ROOT / "reports/supplier_summary.csv")
    assert not any(is_placeholder(normalized_name(x)) for x in suppliers.supplier_name)
