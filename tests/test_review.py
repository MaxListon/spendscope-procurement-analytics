"""Counterexamples prevent source placeholders and incorrect identity approvals from becoming suppliers."""

import json
from pathlib import Path
import duckdb
import pandas as pd
import pytest
from spendscope.normalize import normalize_awards, supplier_identity
from spendscope.pipeline import identity_collisions
from spendscope.review import apply_identity_review, attach_notice_review


@pytest.mark.parametrize(
    "name",
    [
        "Various",
        "Multiple Suppliers",
        "N/A",
        "A list of successful suppliers can be found in the attachments a",
        "A list of succesful suppliers can be found in the attachments ar",
        "Refer to the attachments area",
    ],
)
def test_placeholder_is_not_a_supplier_even_with_a_registration(name):
    key, basis, _ = supplier_identity(
        {"id": "s", "name": name},
        {"s": {"identifier": {"scheme": "GB-COH", "id": "123"}}},
    )
    assert basis == "placeholder" and key.startswith("placeholder:")


@pytest.mark.parametrize(
    "number", ["00000000", "000000000", "213089972", "not provided"]
)
def test_invalid_company_registration_is_not_labeled_registered(number):
    _, basis, _ = supplier_identity(
        {"id": "s", "name": "Named Ltd"},
        {"s": {"identifier": {"scheme": "GB-COH", "id": number}}},
    )
    assert basis == "invalid-registration"


def test_empty_name_is_unknown_despite_registration():
    assert (
        supplier_identity(
            {"id": "s", "name": ""},
            {"s": {"identifier": {"scheme": "GB-COH", "id": "123"}}},
        )[1]
        == "unknown"
    )


def write_decisions(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def decision(name="softcat plc", **changes):
    row = dict(
        supplier_key="GB-COH:02174990",
        normalized_name=name,
        decision="accept",
        canonical_name="SOFTCAT PLC",
        evidence_url="https://find-and-update.company-information.service.gov.uk/company/02174990",
        checked_on="2026-11-12",
        rationale="Exact registration and legal-name evidence",
    )
    return {**row, **changes}


def test_exact_review_does_not_rescue_other_aliases_or_subsidiaries(tmp_path):
    links = pd.DataFrame(
        [
            dict(
                supplier_key="GB-COH:02174990",
                normalized_name=n,
                identity_basis="registered",
                supplier_name=n,
            )
            for n in ["softcat plc", "softcat us holdings inc", "sofcat plc"]
        ]
    )
    identity_collisions(links)
    path = write_decisions(
        tmp_path / "review.csv",
        [decision(), decision("softcat us holdings inc", decision="reject")],
    )
    apply_identity_review(links, path)
    assert list(links.identity_basis) == [
        "registered-reviewed",
        "review-rejected",
        "collision",
    ]
    assert links.iloc[0].supplier_name == "SOFTCAT PLC"


@pytest.mark.parametrize(
    "rows",
    [
        [decision(), decision()],
        [
            decision(
                evidence_url="https://find-and-update.company-information.service.gov.uk/company/00000123"
            )
        ],
        [decision(decision="probably")],
        [decision(rationale="")],
    ],
)
def test_invalid_review_fails_closed(tmp_path, rows):
    path = write_decisions(tmp_path / "review.csv", rows)
    links = pd.DataFrame(
        columns=["supplier_key", "normalized_name", "identity_basis", "supplier_name"]
    )
    with pytest.raises(ValueError):
        apply_identity_review(links, path)


def test_unobserved_notice_cannot_be_called_verified_or_blocked(tmp_path):
    path = tmp_path / "notices.json"
    path.write_text(
        json.dumps(
            {
                "records": [
                    dict(
                        award_key="k",
                        access_status="not_observed",
                        block_attribution=True,
                        flags="mismatch",
                    )
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="observed"):
        attach_notice_review(pd.DataFrame(), path)


def test_source_issues_do_not_remove_headline_awards():
    rows = []
    links = []
    for i, (name, amount, ident, blocked) in enumerate(
        [
            ("Real Ltd", 100, None, False),
            ("Various", 200, None, False),
            ("Another Ltd", 300, "000000000", False),
            ("Unresolved Ltd", 400, None, True),
        ]
    ):
        record = {
            "ocid": str(i),
            "buyer": {"id": "b", "name": "Buyer"},
            "parties": [],
            "awards": [
                {
                    "id": "a",
                    "date": "2023-01-01",
                    "status": "active",
                    "value": {"amount": amount, "currency": "GBP"},
                    "suppliers": [{"id": "s", "name": name}],
                }
            ],
        }
        if ident:
            record["parties"] = [
                {"id": "s", "identifier": {"scheme": "GB-COH", "id": ident}}
            ]
        a, s = normalize_awards(record)
        a[0]["notice_review_block"] = blocked
        rows += a
        links += s
    con = duckdb.connect()
    con.register("a", pd.DataFrame(rows))
    con.register("s", pd.DataFrame(links))
    con.execute(
        "create table awards as select * from a; create table suppliers as select * from s"
    )
    con.execute((Path(__file__).parents[1] / "sql/marts.sql").read_text())
    assert con.sql("select sum(amount) from eligible").fetchall()[0][0] == 1000
    assert con.sql("select sum(amount) from attributed").fetchall()[0][0] == 100
    assert (
        con.sql("select value_coverage from buyer_concentration").fetchall()[0][0]
        == 0.1
    )
    con.close()
