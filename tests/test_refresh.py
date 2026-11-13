from copy import deepcopy
import pytest
from spendscope.refresh import review_refresh


def snapshot():
    return dict(
        annual=[dict(year=2024, awards=100, award_value=1000)],
        buyers=[
            dict(
                buyer_key="a",
                buyer_name="Council",
                attributed_value=800,
                value_coverage=0.8,
                hhi=4000,
                supported=True,
            )
        ],
        quality=dict(contracts={"conservation": True}),
        source=dict(files=[dict(year=2024, sha256="a" * 64)]),
    )


def test_identical_rebuild_is_never_auto_approved():
    result = review_refresh(snapshot(), snapshot())
    assert result["status"] == "no_material_change_detected"
    assert result["auto_approved"] is False
    assert result["metrics"]["attribution_coverage"]["absolute_change"] == 0


def test_changed_source_requires_revalidation_even_when_totals_match():
    after = snapshot()
    after["source"]["files"][0]["sha256"] = "b" * 64
    result = review_refresh(snapshot(), after)
    assert result["source_changed"] and result["status"] == "review_required"
    assert "frozen audit frames" in result["reasons"][0]


def test_denominator_drift_and_support_loss_are_visible():
    after = snapshot()
    after["annual"][0]["award_value"] = 1100
    after["buyers"][0].update(supported=False, value_coverage=800 / 1100)
    result = review_refresh(snapshot(), after)
    assert result["status"] == "review_required"
    assert result["support_transitions"][0]["after"] is False
    assert any("percentage points" in reason for reason in result["reasons"])


def test_buyer_addition_and_removal_preserve_distinction_from_unsupported():
    after = snapshot()
    after["buyers"][0].update(buyer_key="new", supported=False)
    transitions = review_refresh(snapshot(), after)["support_transitions"]
    assert {(r["before"], r["after"]) for r in transitions} == {
        (True, None),
        (None, False),
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "failed_contract",
        "empty_contracts",
        "duplicate",
        "nan",
        "over_attribution",
        "string_support",
    ],
)
def test_invalid_candidates_fail_closed(mutation):
    after = snapshot()
    if mutation == "failed_contract":
        after["quality"]["contracts"]["conservation"] = False
    if mutation == "empty_contracts":
        after["quality"]["contracts"] = {}
    if mutation == "duplicate":
        after["buyers"].append(deepcopy(after["buyers"][0]))
    if mutation == "nan":
        after["buyers"][0]["hhi"] = float("nan")
    if mutation == "over_attribution":
        after["buyers"][0]["attributed_value"] = 1001
    if mutation == "string_support":
        after["buyers"][0]["supported"] = "False"
    with pytest.raises(ValueError):
        review_refresh(snapshot(), after)


def test_concentration_drift_requires_review_even_when_totals_match():
    after = snapshot()
    after["buyers"][0]["hhi"] = 4600
    result = review_refresh(snapshot(), after)
    assert result["status"] == "review_required"
    assert result["largest_hhi_changes"][0]["change"] == 600
