"""Verify generated reports against recorded source-code and artifact fingerprints."""

import hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
m = json.loads((root / "reports/build_manifest.json").read_text())
for group in ("inputs", "outputs"):
    for name, expected in m[group].items():
        path = root / name
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError(f"Changed or missing {group} file: {name}")
q = json.loads((root / "reports/quality.json").read_text())
if not all(q["contracts"].values()):
    raise ValueError("Data contract failure")
print(
    f"Verified {len(m['inputs'])} inputs and {len(m['outputs'])} outputs; all data contracts passed."
)

if (root / "docs/reports/build_manifest.json").read_bytes() != (
    root / "reports/build_manifest.json"
).read_bytes():
    raise ValueError("Published manifest differs from report manifest")
