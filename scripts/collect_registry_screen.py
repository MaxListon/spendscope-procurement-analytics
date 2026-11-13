"""Observe an expanded frozen sample using public registry profile pages.

Run deliberately; never invoked by analysis builds or CI. Does not approve identities.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import certifi
import duckdb
from spendscope.registry_screen import RegistryPage, classify, frame_digest
from spendscope.validation import hash_sample


def observe(row):
    number = row["supplier_key"].split(":", 1)[1]
    url = "https://find-and-update.company-information.service.gov.uk/company/" + number
    result = dict(
        row,
        evidence_url=url,
        observed_at=datetime.now(timezone.utc).isoformat(),
        access="not_observed",
        registry_names=[],
        outcome="not_observed",
    )
    try:
        with urlopen(
            Request(
                url, headers={"User-Agent": "SpendScope-public-evidence-review/0.4"}
            ),
            context=ssl.create_default_context(cafile=certifi.where()),
            timeout=30,
        ) as response:
            if response.url != url:
                raise ValueError("Registry redirected away from the selected identity")
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("Unexpected registry page size")
            page = RegistryPage()
            page.feed(body.decode("utf-8"))
            if (
                not page.names
                or page.number.replace("Company number", "").strip() != number
            ):
                raise ValueError(
                    "Registry profile number/heading could not be verified"
                )
            result.update(
                access="observed",
                registry_names=page.names,
                page_sha256=hashlib.sha256(body).hexdigest(),
                outcome=classify(row["supplier_name"], page.names),
            )
    except (HTTPError, URLError, TimeoutError, ValueError, UnicodeError) as error:
        result["observation_error"] = str(error)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    spec = json.loads((root / "data/review/random_registry_audit.json").read_text())
    with duckdb.connect(str(root / "data/warehouse.duckdb"), read_only=True) as con:
        frame = (
            con.sql(
                "SELECT s.supplier_key,max(s.supplier_name) supplier_name,count(*) award_links FROM awards a JOIN suppliers s USING(award_key) WHERE a.eligible AND a.supplier_count=1 AND NOT a.notice_review_block AND s.identity_basis IN ('registered','registry-audit-conflict') AND s.supplier_key LIKE 'GB-COH:%' GROUP BY s.supplier_key ORDER BY s.supplier_key"
            )
            .df()
            .to_dict("records")
        )
    if frame_digest(frame) != spec["frame_sha256"]:
        raise ValueError("Frozen frame no longer matches; do not silently resample")
    # Preserve the original 40 audited cases and extend their original hash ordering to 200.
    selected = hash_sample(frame, spec["selection_seed"], 200)
    if [r["supplier_key"] for r in selected[:40]] != [
        r["supplier_key"] for r in spec["records"]
    ]:
        raise ValueError("Original sample prefix changed")
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(observe, selected[40:]))
    document = dict(
        frame_count=len(frame),
        frame_sha256=spec["frame_sha256"],
        selection_seed=spec["selection_seed"],
        original_reviewed_cases=40,
        expanded_sample_size=200,
        records=records,
        interpretation="160 additional automated registry-name screens, not independent human labels or matching precision. Original 40-case audit stays separate. Nonmatches require review and never change attribution automatically.",
    )
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    from collections import Counter

    print(dict(Counter(r["outcome"] for r in records)))


if __name__ == "__main__":
    main()
