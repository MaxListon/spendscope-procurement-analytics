"""Conservative name screening; never treats a name match as identity verification."""

import hashlib
from html.parser import HTMLParser
import re
import unicodedata


class RegistryPage(HTMLParser):
    """Extract only the profile heading, company number and explicit former-name cells."""

    def __init__(self):
        super().__init__()
        self.names = []
        self.number = ""
        self.capture = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1" or (
            tag == "td" and attrs.get("id", "").startswith("previous-name-")
        ):
            self.capture = (tag, "name")
            self.parts = []
        elif attrs.get("id") == "company-number":
            self.capture = (tag, "number")
            self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.capture and tag == self.capture[0]:
            value = " ".join("".join(self.parts).split())
            if self.capture[1] == "name":
                self.names.append(value)
            else:
                self.number = value
            self.capture = None


def canonical_name(value):
    value = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    words = re.findall(r"[^\W_]+", value)
    return " ".join("limited" if word == "ltd" else word for word in words)


def classify(published_name, registry_names):
    """No fuzzy similarity, trading-name assumption, or automatic conflict holdback."""
    key = canonical_name(published_name)
    return (
        "name_agrees"
        if key and any(key == canonical_name(name) for name in registry_names)
        else "needs_review"
    )


def frame_digest(frame):
    import json

    return hashlib.sha256(
        json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_screen(frame, spec, original):
    """Reconstruct selection and labels from frozen observations; fail on altered evidence."""
    from collections import Counter
    from datetime import datetime
    from .validation import hash_sample

    if (
        frame_digest(frame) != original["frame_sha256"]
        or spec["frame_sha256"] != original["frame_sha256"]
        or spec["frame_count"] != len(frame)
        or spec["selection_seed"] != original["selection_seed"]
        or spec["original_reviewed_cases"] != 40
        or spec["expanded_sample_size"] != 200
    ):
        raise ValueError("Expanded screen does not use the frozen original frame")
    selected = hash_sample(frame, original["selection_seed"], 200)
    if [r["supplier_key"] for r in selected[:40]] != [
        r["supplier_key"] for r in original["records"]
    ]:
        raise ValueError("Original audit prefix changed")
    if len(spec["records"]) != 160:
        raise ValueError("Expanded screen requires all 160 additional observations")
    for expected, row in zip(selected[40:], spec["records"]):
        if any(
            expected[k] != row.get(k)
            for k in ("supplier_key", "supplier_name", "award_links")
        ):
            raise ValueError("Expanded screen is not the selected frozen sample")
        url = (
            "https://find-and-update.company-information.service.gov.uk/company/"
            + row["supplier_key"].split(":", 1)[1]
        )
        if row.get("evidence_url") != url:
            raise ValueError("Expanded screen cites a different company")
        observed = datetime.fromisoformat(row["observed_at"])
        if observed.tzinfo is None:
            raise ValueError("Evidence time must include its timezone")
        if row["access"] == "observed":
            if (
                not row["registry_names"]
                or not all(
                    isinstance(n, str) and n.strip() for n in row["registry_names"]
                )
                or not re.fullmatch(r"[0-9a-f]{64}", row.get("page_sha256", ""))
                or row["outcome"]
                != classify(row["supplier_name"], row["registry_names"])
            ):
                raise ValueError(
                    "Registry observation and name classification disagree"
                )
        elif (
            row["access"] != "not_observed"
            or row["registry_names"]
            or row["outcome"] != "not_observed"
            or not row.get("observation_error")
        ):
            raise ValueError("Unavailable registry evidence must remain explicit")
    counts = Counter(r["outcome"] for r in spec["records"])
    return dict(
        expanded_sample_size=200,
        original_reviewed_cases=40,
        automated_cases=160,
        outcomes={
            k: counts[k] for k in ("name_agrees", "needs_review", "not_observed")
        },
        interpretation=spec["interpretation"],
        last_observation=max(r["observed_at"] for r in spec["records"]),
    )
