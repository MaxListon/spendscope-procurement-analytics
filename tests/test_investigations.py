import json
from pathlib import Path
import duckdb
import pandas as pd
import pytest
from spendscope.normalize import normalize_awards
from spendscope.investigations import build_workspace, priority

ROOT = Path(__file__).parents[1]


def portfolio():
    rows, links = [], []
    for buyer, award, name, amount, count in [
        ("one", "a", "A", 75, 1),
        ("one", "b", "A", 25, 1),
        ("one", "c", "B", 25, 1),
        ("one", "d", "Joint", 100, 2),
        ("two", "e", "C", 100, 1),
        ("zero", "f", "Various", 200, 1),
    ]:
        record = dict(
            ocid=award,
            buyer=dict(id=buyer, name="Same published name"),
            awards=[
                dict(
                    id=award,
                    date="2024-01-01",
                    status="active",
                    value=dict(amount=amount, currency="GBP"),
                    suppliers=[
                        dict(id=f"{name}{i}", name=f"{name}{i}" if count > 1 else name)
                        for i in range(count)
                    ],
                )
            ],
        )
        a, s = normalize_awards(record)
        rows += a
        links += s
    con = duckdb.connect()
    con.register("af", pd.DataFrame(rows))
    con.register("sf", pd.DataFrame(links))
    con.execute(
        "CREATE TABLE awards AS SELECT * FROM af; CREATE TABLE suppliers AS SELECT * FROM sf"
    )
    con.execute((ROOT / "sql/marts.sql").read_text())
    return con


def test_profile_conserves_both_denominators_and_keeps_homonyms_apart(tmp_path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "docs").mkdir()
    con = portfolio()
    index = build_workspace(
        con,
        tmp_path,
        ROOT,
        dict(retrieved="2026-11-13", files=[dict(year=2024, sha256="a" * 64)]),
        dict(buyers=[]),
    )
    assert (
        index["profile_count"] == 2 and index["excluded_zero_attribution_buyers"] == 1
    )
    row = next(r for r in index["buyers"] if r["total_awards"] == 4)
    assert row["total_value"] == 225 and row["attributed_value"] == 125
    assert row["hhi"] == pytest.approx(6800) and row[
        "hhi_without_largest"
    ] == pytest.approx(5000)
    shard = json.loads(
        (tmp_path / f"docs/workspace/{row['buyer_key'][:2]}.json").read_text()
    )
    profile = shard["profiles"][row["buyer_key"]]
    assert len(profile["awards"]) == 4
    assert sum(a["amount"] for a in profile["awards"] if a["attributed"]) == 125
    assert sum(s["share"] for s in profile["suppliers"]) == pytest.approx(1)
    assert profile["statistics"] is None
    assert sum(not a["attributed"] for a in profile["awards"]) == 1
    assert (
        next(r for r in index["buyers"] if r["total_awards"] == 1)[
            "hhi_without_largest"
        ]
        is None
    )
    con.close()


def test_priority_thresholds_and_score_are_explicit():
    row = dict(
        value_coverage=0.8,
        registered_value_share=0.5,
        largest_eligible_award=9999999,
        top1_share=0.499,
        hhi=1000,
        hhi_without_largest=1499,
    )
    assert priority(row)["priority_points"] == 0
    row.update(
        value_coverage=0.799,
        registered_value_share=0.499,
        largest_eligible_award=10000000,
        top1_share=0.5,
        hhi_without_largest=1500,
    )
    result = priority(row)
    assert result["priority_points"] == 100
    assert sum(f["points"] for f in result["flags"]) == 100
    row["hhi_without_largest"] = None
    assert priority(row)["priority_points"] == 100
