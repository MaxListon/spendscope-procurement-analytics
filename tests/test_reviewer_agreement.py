from copy import deepcopy
import pytest
from spendscope.reviewer_agreement import compare_reviewers, validate_labels


def examples():
    expected = {
        str(i): dict(
            supplier_name=f"Fixture company {i}",
            evidence_url=f"https://example.test/{i}",
        )
        for i in range(2)
    }
    first = [
        dict(
            supplier_key=k,
            **row,
            outcome="compatible",
            registry_name=row["supplier_name"],
            reviewer="First",
            checked_on="2026-11-13",
            rationale="Synthetic test label; not an actual registry review.",
        )
        for k, row in expected.items()
    ]
    second = deepcopy(first)
    for r in second:
        r["reviewer"] = "Second"
    second[1]["outcome"] = "unresolved"
    return expected, first, second


def test_submitted_agreement_retains_disagreements():
    frame, left, right = examples()
    result = compare_reviewers(left, right, frame, frame)
    assert result["raw_agreement"] == 0.5 and result["disagreement_keys"] == ["1"]
    assert sum(c["cases"] for c in result["label_matrix"]) == 2
    assert "cannot establish independence" in result["interpretation"]


@pytest.mark.parametrize(
    "mutation",
    [
        "blank",
        "missing",
        "duplicate",
        "url",
        "name",
        "reviewer",
        "rationale",
        "date",
        "no_observed_name",
    ],
)
def test_incomplete_or_altered_labels_cannot_be_scored(mutation):
    frame, rows, _ = examples()
    if mutation == "blank":
        rows[0]["outcome"] = ""
    if mutation == "missing":
        rows.pop()
    if mutation == "duplicate":
        rows[1] = deepcopy(rows[0])
    if mutation == "url":
        rows[0]["evidence_url"] = "https://example.test/wrong"
    if mutation == "name":
        rows[0]["supplier_name"] = "Another name"
    if mutation == "reviewer":
        rows[0]["reviewer"] = ""
    if mutation == "rationale":
        rows[0]["rationale"] = "yes"
    if mutation == "date":
        rows[0]["checked_on"] = "not a date"
    if mutation == "no_observed_name":
        rows[0]["registry_name"] = ""
    with pytest.raises(ValueError):
        validate_labels(rows, frame)


def test_same_declared_reviewer_does_not_qualify_as_second_review():
    frame, rows, _ = examples()
    with pytest.raises(ValueError):
        compare_reviewers(rows, rows, frame, frame)
