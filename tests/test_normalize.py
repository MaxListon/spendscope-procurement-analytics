import copy
import math
import pytest
from spendscope.normalize import normalize_awards, normalized_name, supplier_identity


@pytest.fixture
def record():
    return {
        "ocid": "p1",
        "date": "2024-01-01T00:00:00Z",
        "buyer": {"id": "b1", "name": "Council"},
        "awards": [
            {
                "id": "a1",
                "date": "2023-05-01",
                "status": "active",
                "value": {"amount": 100, "currency": "GBP"},
                "suppliers": [{"id": "s1", "name": "Acme Ltd"}],
            }
        ],
    }


def test_joint_award_counted_once(record):
    record["awards"][0]["suppliers"].append({"id": "s2", "name": "Other Ltd"})
    a, s = normalize_awards(record)
    assert (
        len(a) == 1
        and a[0]["amount"] == 100
        and a[0]["supplier_count"] == 2
        and len(s) == 2
    )
    assert all("amount" not in link for link in s)


def test_duplicate_supplier_not_double_counted(record):
    record["awards"][0]["suppliers"] *= 2
    a, s = normalize_awards(record)
    assert a[0]["supplier_count"] == 1 and len(s) == 1


@pytest.mark.parametrize(
    "value", [None, 0, -1, float("nan"), float("inf"), True, "100"]
)
def test_invalid_amount_quarantined(record, value):
    record["awards"][0]["value"]["amount"] = value
    a, _ = normalize_awards(record)
    assert not a[0]["eligible"] and a[0]["exclusion_reason"] == "amount"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("status", "cancelled", "status"),
        ("date", "2099-01-01", "award_date"),
        ("date", "bad", "award_date"),
    ],
)
def test_exclusion_rules(record, field, value, reason):
    record["awards"][0][field] = value
    assert normalize_awards(record)[0][0]["exclusion_reason"] == reason


def test_currency_not_converted(record):
    record["awards"][0]["value"]["currency"] = "USD"
    assert normalize_awards(record)[0][0]["exclusion_reason"] == "currency"


def test_missing_supplier_keeps_headline(record):
    record["awards"][0]["suppliers"] = []
    a, s = normalize_awards(record)
    assert a[0]["eligible"] and a[0]["supplier_count"] == 0 and not s


def test_repeated_award_rejected(record):
    record["awards"] *= 2
    with pytest.raises(ValueError):
        normalize_awards(record)


def test_registered_identity_preferred():
    s = {"id": "local", "name": "Acme"}
    parties = {"local": {"identifier": {"scheme": "GB-COH", "id": "123"}}}
    assert supplier_identity(s, parties) == ("GB-COH:00000123", "registered", "acme")


def test_local_id_does_not_merge_different_names():
    a = supplier_identity({"id": "shared", "name": "Acme"}, {})
    b = supplier_identity({"id": "shared", "name": "Other"}, {})
    assert a[0] != b[0]


def test_conservative_names():
    assert normalized_name("  ACME, Ltd. ") == normalized_name("Acme Ltd")
    assert normalized_name("Acme Limited") != normalized_name("Acme Ltd")


def test_period_reversal(record):
    record["awards"][0]["contractPeriod"] = {
        "startDate": "2025-01-01",
        "endDate": "2023-01-01",
    }
    assert not normalize_awards(record)[0][0]["period_valid"]
