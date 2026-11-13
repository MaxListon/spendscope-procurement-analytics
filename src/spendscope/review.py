"""Versioned evidence decisions; targeted review never masquerades as population accuracy."""

from pathlib import Path
import json
import pandas as pd
from .normalize import normalized_name


def apply_identity_review(links, path):
    """Approve exact (registration key, observed normalized name) pairs only."""
    decisions = pd.read_csv(path, keep_default_na=False)
    required = {
        "supplier_key",
        "normalized_name",
        "decision",
        "canonical_name",
        "evidence_url",
        "checked_on",
        "rationale",
    }
    if not required.issubset(decisions.columns):
        raise ValueError("Identity review schema incomplete")
    if decisions.duplicated(["supplier_key", "normalized_name"]).any():
        raise ValueError("Conflicting duplicate identity decisions")
    if not set(decisions.decision).issubset({"accept", "reject", "unresolved"}):
        raise ValueError("Unknown identity decision")
    for row in decisions.itertuples():
        if row.normalized_name != normalized_name(row.normalized_name):
            raise ValueError("Review aliases must be normalized explicitly")
        number = row.supplier_key.removeprefix("GB-COH:")
        expected = f"https://find-and-update.company-information.service.gov.uk/company/{number}"
        if not row.supplier_key.startswith("GB-COH:") or row.evidence_url != expected:
            raise ValueError("Registration decision must cite the same company number")
        if not row.canonical_name or not row.checked_on or not row.rationale:
            raise ValueError("Identity decision lacks evidence metadata")
        match = (links.supplier_key == row.supplier_key) & (
            links.normalized_name == row.normalized_name
        )
        # Do not rescue placeholders, malformed identifiers or empty names.
        match &= links.identity_basis.isin(["registered", "collision"])
        if row.decision == "accept":
            links.loc[match, "identity_basis"] = "registered-reviewed"
            links.loc[match, "supplier_name"] = row.canonical_name
        elif row.decision == "reject":
            links.loc[match, "identity_basis"] = "review-rejected"
    return decisions


def attach_notice_review(awards, path):
    spec = json.loads(Path(path).read_text())
    seen = set()
    awards["notice_review_status"] = "not_reviewed"
    awards["notice_review_block"] = False
    for row in spec["records"]:
        key = row["award_key"]
        if key in seen:
            raise ValueError("Repeated notice review award key")
        seen.add(key)
        if row["access_status"] not in ("observed", "not_observed"):
            raise ValueError("Invalid notice observation status")
        if row["block_attribution"] and (
            row["access_status"] != "observed" or not row["flags"]
        ):
            raise ValueError(
                "Attribution holdback requires an observed, documented issue"
            )
        matches = awards.award_key == key
        if int(matches.sum()) != 1:
            raise ValueError("Reviewed award missing or duplicated in current universe")
        award = awards.loc[matches].iloc[0]
        if (
            award.source_url != row["source_url"]
            or abs(award.amount - row["snapshot_amount"]) > 0.01
        ):
            raise ValueError("Notice evidence belongs to a different source record")
        awards.loc[matches, "notice_review_status"] = (
            "unresolved"
            if row["block_attribution"]
            else "observed"
            if row["access_status"] == "observed"
            else "not_observed"
        )
        awards.loc[matches, "notice_review_block"] = row["block_attribution"]
    return spec
