import gzip
import json
from pathlib import Path
import duckdb
import pandas as pd
import pytest
from spendscope.pipeline import (
    build_lock,
    load_latest,
    identity_collisions,
    get_sources,
    sha,
)
from spendscope.normalize import normalize_awards


def write_source(path, records):
    with gzip.open(path, "wt") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


def test_latest_snapshot_not_summed(tmp_path):
    p = write_source(
        tmp_path / "s.gz",
        [
            {"ocid": "p", "date": "2023-01-01", "awards": []},
            {"ocid": "p", "date": "2024-01-01", "awards": [{"id": "new"}]},
        ],
    )
    latest, q = load_latest([p])
    assert len(latest) == 1 and latest["p"][2]["awards"][0]["id"] == "new"
    assert q["repeated_process_snapshots"] == 1


def test_conflicting_same_timestamp_fails(tmp_path):
    p = write_source(
        tmp_path / "s.gz",
        [
            {"ocid": "p", "date": "2023-01-01", "x": 1},
            {"ocid": "p", "date": "2023-01-01", "x": 2},
        ],
    )
    with pytest.raises(ValueError):
        load_latest([p])


def test_lock_protects_and_cleans(tmp_path):
    with build_lock(tmp_path):
        with pytest.raises(FileExistsError):
            with build_lock(tmp_path):
                pass
    assert not (tmp_path / ".build.lock").exists()


def test_lock_cleans_after_failure(tmp_path):
    with pytest.raises(RuntimeError):
        with build_lock(tmp_path):
            raise RuntimeError()
    assert not (tmp_path / ".build.lock").exists()


def test_fingerprint_rejects_changed_cache(tmp_path):
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/raw/2023.jsonl.gz").write_bytes(b"changed")
    (tmp_path / "data/sources.json").write_text(
        json.dumps({"files": [{"year": 2023, "sha256": "bad", "bytes": 7}]})
    )
    with pytest.raises(ValueError):
        get_sources(tmp_path, True)


def test_identity_conflict_not_silently_merged():
    links = pd.DataFrame(
        [
            {
                "supplier_key": "GB-COH:1",
                "identity_basis": "registered",
                "normalized_name": "one",
            },
            {
                "supplier_key": "GB-COH:1",
                "identity_basis": "registered",
                "normalized_name": "two",
            },
        ]
    )
    assert identity_collisions(links) == {"GB-COH:1"}
    assert set(links.identity_basis) == {"collision"}


def test_sql_concentration_known_answer():
    records = []
    for i, (name, amount, n) in enumerate(
        [("A", 75, 1), ("B", 25, 1), ("Joint", 100, 2)]
    ):
        records.append(
            {
                "ocid": str(i),
                "buyer": {"id": "buyer", "name": "Council"},
                "awards": [
                    {
                        "id": "a",
                        "date": "2023-01-01",
                        "status": "active",
                        "value": {"amount": amount, "currency": "GBP"},
                        "suppliers": [
                            {"id": f"{name}{j}", "name": f"{name}{j}"} for j in range(n)
                        ],
                    }
                ],
            }
        )
    rows = []
    links = []
    for r in records:
        a, s = normalize_awards(r)
        rows += a
        links += s
    award_frame = pd.DataFrame(rows)
    supplier_frame = pd.DataFrame(links)
    con = duckdb.connect()
    con.register("award_frame", award_frame)
    con.register("supplier_frame", supplier_frame)
    con.execute(
        "create table awards as select * from award_frame; create table suppliers as select * from supplier_frame"
    )
    con.execute((Path(__file__).parents[1] / "sql/marts.sql").read_text())
    r = con.sql("select * from buyer_concentration").df().iloc[0]
    assert (
        r.hhi == 6250
        and r.top1_share == 0.75
        and r.value_coverage == 0.5
        and not r.supported
    )
    assert con.sql("select sum(amount) from eligible").fetchall()[0][0] == 200
    assert con.sql("select sum(amount) from attributed").fetchall()[0][0] == 100
    con.close()


def test_failed_analysis_preserves_previous_release(tmp_path, monkeypatch):
    from spendscope.pipeline import build
    import spendscope.pipeline as pipeline
    import shutil

    root = tmp_path
    (root / "data/raw").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "docs/index.html").write_text("previous reviewed release")
    record = {
        "ocid": "p",
        "date": "2023-01-01",
        "buyer": {"id": "b", "name": "Council"},
        "awards": [
            {
                "id": "a",
                "date": "2023-01-01",
                "status": "active",
                "value": {"amount": 100, "currency": "GBP"},
                "suppliers": [{"id": "s", "name": "Named"}],
            }
        ],
    }
    source = write_source(root / "data/raw/2023.jsonl.gz", [record])
    (root / "data/sources.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "year": 2023,
                        "sha256": sha(source),
                        "bytes": source.stat().st_size,
                    }
                ]
            }
        )
    )
    (root / "sql").mkdir()
    shutil.copy2(Path(__file__).parents[1] / "sql/marts.sql", root / "sql/marts.sql")

    def fail(*args, **kwargs):
        raise RuntimeError("R analysis failed")

    monkeypatch.setattr(pipeline.subprocess, "run", fail)
    with pytest.raises(RuntimeError, match="R analysis failed"):
        build(root, True)
    assert (root / "docs/index.html").read_text() == "previous reviewed release"
    assert not (root / ".build.lock").exists()
    assert not list(root.glob(".stage-*"))
