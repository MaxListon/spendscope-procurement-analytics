"""Pinned source -> relational warehouse -> SQL marts -> R analysis -> dashboard."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
import certifi
import duckdb
import pandas as pd
from .normalize import normalize_awards, date
from .review import apply_identity_review, attach_notice_review
from .reporting import business_cases


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def build_lock(root):
    lock = root / ".build.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    try:
        yield
    finally:
        lock.unlink()


def get_sources(root, offline):
    spec = json.loads((root / "data/sources.json").read_text())
    paths = []
    for item in spec["files"]:
        path = root / f"data/raw/{item['year']}.jsonl.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            if offline:
                raise FileNotFoundError(path)
            temp = path.with_suffix(".download")
            try:
                with (
                    urllib.request.urlopen(
                        item["url"],
                        timeout=120,
                        context=ssl.create_default_context(cafile=certifi.where()),
                    ) as response,
                    open(temp, "wb") as f,
                ):
                    shutil.copyfileobj(response, f)
                if sha(temp) != item["sha256"]:
                    raise ValueError(
                        "Source changed; review and explicitly repin before rebuilding"
                    )
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
        if sha(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError(f"Fingerprint mismatch: {path.name}")
        paths.append(path)
    return paths


def load_latest(paths):
    latest = {}
    lines = 0
    duplicates = 0
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                lines += 1
                ocid = record.get("ocid")
                dt = date(record.get("date"))
                if not ocid or not dt:
                    raise ValueError("Process missing valid ocid or release date")
                canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
                signature = hashlib.sha256(canonical.encode()).hexdigest()
                previous = latest.get(ocid)
                if previous:
                    duplicates += 1
                    if previous[0] == dt and previous[1] != signature:
                        raise ValueError(
                            "Conflicting process snapshots at same timestamp"
                        )
                if previous is None or (dt, signature) > previous[:2]:
                    latest[ocid] = (dt, signature, record)
    return latest, dict(
        source_lines=lines,
        unique_processes=len(latest),
        repeated_process_snapshots=duplicates,
    )


def identity_collisions(links):
    registered = links[links.identity_basis == "registered"]
    counts = registered.groupby("supplier_key").normalized_name.nunique()
    keys = set(counts[counts > 1].index)
    links.loc[links.supplier_key.isin(keys), "identity_basis"] = "collision"
    return keys


def build(root, offline=False):
    with (
        build_lock(root),
        tempfile.TemporaryDirectory(prefix=".stage-", dir=root) as directory,
    ):
        stage = Path(directory)
        (stage / "reports").mkdir()
        (stage / "docs").mkdir()
        paths = get_sources(root, offline)
        latest, quality = load_latest(paths)
        rows = []
        links = []
        for ocid in sorted(latest):
            a, s = normalize_awards(latest[ocid][2])
            rows.extend(a)
            links.extend(s)
        del latest
        awards = pd.DataFrame(rows)
        suppliers = pd.DataFrame(links)
        collisions = identity_collisions(suppliers)
        review_root = root / "data/review"
        if review_root.is_dir():
            decisions = apply_identity_review(
                suppliers, review_root / "identity_decisions.csv"
            )
            notice_review = attach_notice_review(
                awards, review_root / "notice_checks.json"
            )
        else:
            decisions = pd.DataFrame(columns=["decision"])
            notice_review = {"records": []}
            awards["notice_review_status"] = "not_reviewed"
            awards["notice_review_block"] = False
        quality.update(
            award_rows=len(awards),
            identity_decisions=decisions.decision.value_counts().to_dict(),
            placeholder_supplier_links=int(
                (suppliers.identity_basis == "placeholder").sum()
            ),
            invalid_registration_links=int(
                (suppliers.identity_basis == "invalid-registration").sum()
            ),
            reviewed_registered_links=int(
                (suppliers.identity_basis == "registered-reviewed").sum()
            ),
            notice_records_checked=len(notice_review["records"]),
            notice_pages_observed=sum(
                x["access_status"] == "observed" for x in notice_review["records"]
            ),
            notice_attribution_holdbacks=int(awards.notice_review_block.sum()),
            supplier_links=len(suppliers),
            registered_identity_collisions=len(collisions),
            exclusion_counts=awards.exclusion_reason.value_counts().to_dict(),
            missing_supplier_awards=int((awards.supplier_count == 0).sum()),
            multi_supplier_awards=int((awards.supplier_count > 1).sum()),
            unknown_supplier_links=int((suppliers.identity_basis == "unknown").sum()),
        )
        con = duckdb.connect(str(stage / "warehouse.duckdb"))
        con.execute("SET threads=1")
        con.register("award_frame", awards)
        con.register("supplier_frame", suppliers)
        con.execute("CREATE TABLE awards AS SELECT * FROM award_frame")
        con.execute("CREATE TABLE suppliers AS SELECT * FROM supplier_frame")
        con.execute((root / "sql/marts.sql").read_text())
        checks = {
            "unique_award_keys": con.sql(
                "SELECT count(*)=count(DISTINCT award_key) FROM awards"
            ).fetchall()[0][0],
            "no_orphan_supplier_links": con.sql(
                "SELECT count(*)=0 FROM suppliers s ANTI JOIN awards a USING(award_key)"
            ).fetchall()[0][0],
            "attribution_unique": con.sql(
                "SELECT count(*)=count(DISTINCT award_key) FROM attributed"
            ).fetchall()[0][0],
            "annual_count_conserves": con.sql(
                "SELECT (SELECT sum(awards) FROM annual)=(SELECT count(*) FROM eligible)"
            ).fetchall()[0][0],
            "value_conserves": con.sql(
                "SELECT abs((SELECT sum(award_value) FROM annual)-(SELECT sum(amount) FROM eligible))<0.01"
            ).fetchall()[0][0],
            "concentration_bounds": con.sql(
                "SELECT bool_and(hhi>0 AND hhi<=10000.000001 AND top1_share<=top5_share+1e-10 AND top5_share<=1.000000001 AND value_coverage<=1.000000001) FROM buyer_concentration"
            ).fetchall()[0][0],
            "no_placeholder_attribution": con.sql(
                "SELECT count(*)=0 FROM attributed WHERE identity_basis NOT IN ('registered','registered-reviewed','name-only')"
            ).fetchall()[0][0],
            "no_review_holdback_attribution": con.sql(
                "SELECT count(*)=0 FROM attributed WHERE notice_review_block"
            ).fetchall()[0][0],
            "no_multi_award_attribution": con.sql(
                "SELECT count(*)=0 FROM attributed WHERE supplier_count<>1"
            ).fetchall()[0][0],
        }
        if not all(checks.values()):
            raise ValueError(f"Contract failure: {checks}")
        tables = {}
        for table in [
            "annual",
            "categories",
            "buyer_concentration",
            "supplier_summary",
            "identity_review",
            "buyer_evidence",
            "comparison_thresholds",
        ]:
            df = con.sql(f"SELECT * FROM {table}").df()
            df.to_csv(stage / f"reports/{table}.csv", index=False)
            tables[table] = json.loads(df.to_json(orient="records"))
        # Deliberately exclude individual supplier names, contacts and addresses from statistical input.
        con.sql(
            "SELECT award_key,ocid,year,category,amount FROM eligible ORDER BY award_key"
        ).df().to_csv(stage / "reports/statistical_input.csv", index=False)
        con.sql(
            "SELECT award_key,ocid,buyer_key,buyer_name,supplier_key,identity_basis,amount FROM attributed ORDER BY award_key"
        ).df().to_csv(stage / "reports/attributed_input.csv", index=False)
        drill = con.sql(
            "SELECT award_key,title,buyer_name,year,category,amount,supplier_count,source_url,notice_review_status FROM eligible ORDER BY amount DESC,award_key LIMIT 200"
        ).df()
        tables["largest_awards"] = json.loads(drill.to_json(orient="records"))
        if review_root.is_dir():
            con.sql(
                "SELECT s.* FROM suppliers s JOIN (SELECT supplier_key FROM suppliers WHERE identity_basis='name-only' GROUP BY supplier_key HAVING count(*)>=2) k USING(supplier_key) ORDER BY s.supplier_key,s.award_key LIMIT 300"
            ).df().to_csv(stage / "reports/name_only_review_queue.csv", index=False)
            shutil.copy2(
                review_root / "identity_decisions.csv",
                stage / "reports/identity_decisions.csv",
            )
            shutil.copy2(
                review_root / "notice_checks.json", stage / "reports/notice_checks.json"
            )
        con.close()
        quality["contracts"] = checks
        (stage / "reports/quality.json").write_text(
            json.dumps(quality, indent=2) + "\n"
        )
        r_env = os.environ.copy()
        r_env["R_LIBS_USER"] = os.pathsep.join(
            x for x in (str(root / ".Rlibrary"), r_env.get("R_LIBS_USER", "")) if x
        )
        subprocess.run(
            [
                "Rscript",
                str(root / "R/analyze.R"),
                str(stage / "reports"),
                str(stage / "docs"),
            ],
            check=True,
            env=r_env,
        )
        for required in ("category-analysis.svg", "research.html"):
            artifact = stage / "docs" / required
            if not artifact.is_file() or artifact.stat().st_size == 0:
                raise ValueError(f"R output missing: {required}")
        r = json.loads((stage / "reports/r_analysis.json").read_text())
        payload = dict(
            annual=tables["annual"],
            categories=tables["categories"],
            buyers=tables["buyer_concentration"],
            suppliers=tables["supplier_summary"][:200],
            awards=tables["largest_awards"],
            quality=quality,
            buyer_evidence=tables["buyer_evidence"],
            comparison_thresholds=tables["comparison_thresholds"],
            notice_review=notice_review,
            statistics=r,
            source=json.loads((root / "data/sources.json").read_text()),
            scope="Active positive GBP awards dated 2022–2024 in selected compiled process snapshots. Not actual payments.",
        )
        memo, cases = business_cases(payload, review_root / "baseline_v01.json")
        (stage / "EXECUTIVE_MEMO.md").write_text(memo)
        (stage / "docs/case-studies.html").write_text(cases)
        (stage / "docs/data.json").write_text(
            json.dumps(payload, allow_nan=False, separators=(",", ":"))
        )
        (stage / "reports/analysis.json").write_text(
            json.dumps(payload, indent=2, allow_nan=False) + "\n"
        )
        for name in ("index.html", "style.css", "app.js", "research.css"):
            shutil.copy2(root / f"src/spendscope/web/{name}", stage / f"docs/{name}")
        shutil.copytree(stage / "reports", stage / "docs/reports")
        inputs = {
            str(f.relative_to(root)): sha(f)
            for folder in ("src", "sql", "R", "data/review", "scripts")
            for f in sorted((root / folder).rglob("*"))
            if f.is_file()
            and "__pycache__" not in str(f)
            and f.suffix
            in {".py", ".html", ".css", ".js", ".sql", ".R", ".csv", ".json"}
        }
        for f in ("data/sources.json", "pyproject.toml", "requirements-lock.txt"):
            inputs[f] = sha(root / f)
        manifest = dict(
            inputs=inputs,
            outputs={
                str(f.relative_to(stage)): sha(f)
                for f in sorted(stage.rglob("*"))
                if f.is_file() and f.name != "warehouse.duckdb"
            },
        )
        (stage / "reports/build_manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        shutil.copy2(
            stage / "reports/build_manifest.json",
            stage / "docs/reports/build_manifest.json",
        )
        # All computations and R checks must succeed before published artifacts are replaced.
        for folder in ("reports", "docs"):
            for f in (stage / folder).rglob("*"):
                if f.is_file():
                    target = root / f.relative_to(stage)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(f, target)
        os.replace(stage / "EXECUTIVE_MEMO.md", root / "EXECUTIVE_MEMO.md")
        os.replace(stage / "warehouse.duckdb", root / "data/warehouse.duckdb")
        print(
            json.dumps(
                dict(awards=len(awards), checks=checks, quality=quality), indent=2
            )
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    build(args.root.resolve(), args.offline)


if __name__ == "__main__":
    main()
