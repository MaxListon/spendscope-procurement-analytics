"""Evidence-first investigation artifacts. Priority points are explicit review heuristics."""

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

RULES = [
    dict(code="coverage_gap", points=30, rule="Attributable-value coverage below 80%"),
    dict(
        code="identity_gap",
        points=20,
        rule="Registration evidence below 50% of attributable value",
    ),
    dict(
        code="large_commitment",
        points=15,
        rule="Largest eligible award at least £10 million",
    ),
    dict(
        code="supplier_concentration",
        points=15,
        rule="Largest supplier at least 50% of attributable value",
    ),
    dict(
        code="largest_award_sensitivity",
        points=20,
        rule="Removing the largest attributed award changes HHI by at least 500 points, or leaves no residual portfolio",
    ),
]


def priority(row):
    residual_hhi = row["hhi_without_largest"]
    active = [
        row["value_coverage"] < 0.8,
        row["registered_value_share"] < 0.5,
        row["largest_eligible_award"] >= 10_000_000,
        row["top1_share"] >= 0.5,
        residual_hhi is None or abs(row["hhi"] - residual_hhi) >= 500,
    ]
    flags = [dict(rule) for rule, enabled in zip(RULES, active) if enabled]
    return dict(priority_points=sum(r["points"] for r in flags), flags=flags)


def snapshot_id(source):
    files = sorted((r["year"], r["sha256"]) for r in source["files"])
    return hashlib.sha256(json.dumps(files, separators=(",", ":")).encode()).hexdigest()


def records(con, query):
    return json.loads(
        con.sql(query).df().to_json(orient="records", double_precision=15)
    )


def build_workspace(con, stage, root, source, statistics):
    con.execute((root / "sql/investigations.sql").read_text())
    if not con.sql(
        "SELECT (SELECT count(*) FROM investigation_awards)=(SELECT count(*) FROM eligible)"
    ).fetchall()[0][0]:
        raise ValueError("Investigation export multiplied eligible awards")
    summaries = records(con, "SELECT * FROM investigation_summary ORDER BY buyer_key")
    suppliers = records(
        con,
        "SELECT bs.*,a.identity_basis FROM buyer_supplier bs JOIN (SELECT buyer_key,supplier_key,min(identity_basis) identity_basis FROM attributed GROUP BY buyer_key,supplier_key) a USING(buyer_key,supplier_key) ORDER BY bs.buyer_key,bs.award_value DESC,bs.supplier_key",
    )
    awards = records(
        con,
        "SELECT * FROM investigation_awards ORDER BY buyer_key,amount DESC,award_key",
    )
    supplier_groups, award_groups = defaultdict(list), defaultdict(list)
    for row in suppliers:
        supplier_groups[row["buyer_key"]].append(row)
    for row in awards:
        award_groups[row["buyer_key"]].append(row)
    intervals = {r["buyer_key"]: r for r in statistics["buyers"]}
    inputs = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder, suffixes in (
            ("src/spendscope", {".py"}),
            ("sql", {".sql"}),
            ("R", {".R"}),
            ("data/review", {".json", ".csv"}),
        )
        for p in sorted((root / folder).glob("*"))
        if p.is_file() and p.suffix in suffixes
    }
    dataset = hashlib.sha256(
        json.dumps(
            dict(source=snapshot_id(source), inputs=inputs),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    shards = defaultdict(dict)
    for row in summaries:
        key = row["buyer_key"]
        row.update(priority(row))
        grouped = supplier_groups[key]
        linked = award_groups[key]
        total = row["attributed_value"]
        if abs(sum(s["award_value"] for s in grouped) - total) > max(
            0.01, total * 1e-10
        ):
            raise ValueError("Investigation supplier amounts do not reconcile")
        if len(linked) != row["total_awards"] or abs(
            sum(a["amount"] for a in linked) - row["total_value"]
        ) > max(0.01, row["total_value"] * 1e-10):
            raise ValueError("Investigation eligible awards do not reconcile")
        for supplier in grouped:
            supplier["share"] = supplier["award_value"] / total
        shards[key[:2]][key] = dict(
            summary=row, suppliers=grouped, awards=linked, statistics=intervals.get(key)
        )
    output = stage / "docs/workspace"
    output.mkdir(parents=True, exist_ok=True)
    queue = sorted(
        summaries,
        key=lambda r: (
            -r["priority_points"],
            -r["largest_eligible_award"],
            r["buyer_key"],
        ),
    )
    index = dict(
        schema_version=1,
        dataset_id=dataset,
        source_retrieved=source["retrieved"],
        rules=RULES,
        buyers=[
            {
                **{
                    k: r[k]
                    for k in (
                        "buyer_key",
                        "buyer_name",
                        "total_value",
                        "total_awards",
                        "attributed_awards",
                        "attributed_value",
                        "value_coverage",
                        "registered_value_share",
                        "largest_eligible_award",
                        "top1_share",
                        "hhi",
                        "hhi_without_largest",
                        "supported",
                        "priority_points",
                    )
                },
                "flags": [f["code"] for f in r["flags"]],
            }
            for r in queue
        ],
        profile_count=len(summaries),
        excluded_zero_attribution_buyers=con.sql(
            "SELECT count(DISTINCT buyer_key) FROM eligible WHERE buyer_key NOT IN (SELECT buyer_key FROM buyer_concentration)"
        ).fetchall()[0][0],
        scope="Profiles cover every buyer identity with at least one attributable award. Eligible awards without any attributable supplier remain in headline totals but have no concentration profile. Priority points allocate evidence-review effort; they are not risk, fraud, performance or savings scores.",
    )
    (output / "index.json").write_text(
        json.dumps(index, allow_nan=False, separators=(",", ":"))
    )
    for prefix, profiles in sorted(shards.items()):
        (output / f"{prefix}.json").write_text(
            json.dumps(
                dict(dataset_id=dataset, profiles=profiles),
                allow_nan=False,
                separators=(",", ":"),
            )
        )
    screen = (
        json.loads((root / "data/review/registry_screen.json").read_text())
        if (root / "data/review/registry_screen.json").exists()
        else {"records": []}
    )
    if screen["records"]:
        from .validation import hash_sample

        fields = [
            "supplier_key",
            "supplier_name",
            "evidence_url",
            "outcome",
            "registry_name",
            "reviewer",
            "checked_on",
            "rationale",
        ]
        for name, rows in (
            ("independent_registry_review.csv", screen["records"]),
            (
                "second_registry_review.csv",
                hash_sample(screen["records"], "second-review-subset-v1", 40),
            ),
        ):
            with (stage / "reports" / name).open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: row[k] for k in fields[:3]})
    con.sql("SELECT * FROM investigation_summary ORDER BY buyer_key").df().to_csv(
        stage / "reports/investigation_metrics.csv", index=False
    )
    return index
