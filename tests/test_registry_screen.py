from copy import deepcopy
import json
from pathlib import Path
import pytest
from spendscope.registry_screen import (
    RegistryPage,
    classify,
    validate_screen,
    frame_digest,
)
from spendscope.validation import hash_sample


def test_names_use_explicit_heading_and_former_cells_only():
    page = RegistryPage()
    page.feed(
        '<h1>Example &amp; Sons LTD</h1><p id="company-number">Company number <strong>12345678</strong></p><td id="previous-name-1">Previous Limited</td><div>Unrelated marketing name</div>'
    )
    assert page.names == ["Example & Sons LTD", "Previous Limited"]
    assert page.number == "Company number 12345678"
    assert classify("EXAMPLE AND SONS Limited", page.names) == "name_agrees"
    assert classify("Previous Ltd", page.names) == "name_agrees"
    assert classify("Example Group Ltd", page.names) == "needs_review"
    assert classify("", [""]) == "needs_review"


def screen_fixture():
    frame = [
        dict(
            supplier_key=f"GB-COH:{i:08d}",
            supplier_name=f"Company {i} Ltd",
            award_links=1,
        )
        for i in range(210)
    ]
    selected = hash_sample(frame, "seed", 200)
    original = dict(
        frame_sha256=frame_digest(frame), selection_seed="seed", records=selected[:40]
    )
    rows = [
        dict(
            r,
            evidence_url="https://find-and-update.company-information.service.gov.uk/company/"
            + r["supplier_key"].split(":")[1],
            observed_at="2026-11-13T00:00:00+00:00",
            access="observed",
            registry_names=[r["supplier_name"]],
            outcome="name_agrees",
            page_sha256="a" * 64,
        )
        for r in selected[40:]
    ]
    spec = dict(
        frame_sha256=original["frame_sha256"],
        frame_count=len(frame),
        selection_seed="seed",
        original_reviewed_cases=40,
        expanded_sample_size=200,
        records=rows,
        interpretation="Screen only",
    )
    return frame, spec, original


def test_reconstructs_extended_sample_and_keeps_unavailable_cases():
    frame, spec, original = screen_fixture()
    spec["records"][0].update(
        access="not_observed",
        outcome="not_observed",
        registry_names=[],
        observation_error="HTTP 404",
    )
    summary = validate_screen(frame, spec, original)
    assert summary["outcomes"] == dict(name_agrees=159, needs_review=0, not_observed=1)


@pytest.mark.parametrize(
    "mutation", ["reorder", "label", "url", "hash", "date", "frame", "missing"]
)
def test_tampered_screen_rejected(mutation):
    frame, spec, original = screen_fixture()
    if mutation == "reorder":
        spec["records"].reverse()
    if mutation == "label":
        spec["records"][0]["outcome"] = "needs_review"
    if mutation == "url":
        spec["records"][0]["evidence_url"] += "0"
    if mutation == "hash":
        spec["records"][0]["page_sha256"] = ""
    if mutation == "date":
        spec["records"][0]["observed_at"] = "2026-11-13"
    if mutation == "frame":
        frame[0]["award_links"] = 2
    if mutation == "missing":
        spec["records"].pop()
    with pytest.raises(ValueError):
        validate_screen(frame, spec, original)
