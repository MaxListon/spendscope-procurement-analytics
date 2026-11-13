from pathlib import Path
import duckdb


def test_case_evidence_uses_exact_key_not_shared_buyer_name():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE attributed (buyer_key VARCHAR,buyer_name VARCHAR,award_key VARCHAR,ocid VARCHAR,title VARCHAR,amount DOUBLE,supplier_key VARCHAR,supplier_name VARCHAR,identity_basis VARCHAR,source_url VARCHAR)"
    )
    con.executemany(
        "INSERT INTO attributed VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                key,
                "Home Office",
                award,
                "process-" + award,
                "Commitment",
                amount,
                "supplier",
                "Example Limited",
                "name-only",
                "https://example.test/" + award,
            )
            for key, award, amount in [
                ("case", "a", 100),
                ("case", "b", 100),
                ("other", "c", 999),
            ]
        ],
    )
    query = (Path(__file__).parents[1] / "sql/decision_case.sql").read_text()
    rows = con.execute(query, ["case"]).df()
    assert rows.award_key.tolist() == ["a", "b"]
    assert rows.amount.sum() == 200
    assert set(rows.buyer_key) == {"case"}
    assert rows.source_url.tolist() == [
        "https://example.test/a",
        "https://example.test/b",
    ]
    assert con.execute(query, ["case' OR 1=1 --"]).df().empty
    con.close()
