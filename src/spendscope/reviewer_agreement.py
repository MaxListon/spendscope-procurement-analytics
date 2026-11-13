"""Validate submitted registry labels; do not certify reviewers' independence."""

from collections import Counter
from datetime import date
import csv

LABELS = {"compatible", "conflict", "unresolved", "not_observed"}


def validate_labels(rows, expected):
    if len(rows) != len(expected):
        raise ValueError(
            "Every selected case requires an explicit label, including unavailable evidence"
        )
    output = {}
    for row in rows:
        key = row["supplier_key"]
        if key not in expected or key in output:
            raise ValueError("Unknown or duplicate supplier in reviewer submission")
        target = expected[key]
        if (
            row["supplier_name"] != target["supplier_name"]
            or row["evidence_url"] != target["evidence_url"]
        ):
            raise ValueError(
                "Submission changed the frozen name or company evidence URL"
            )
        if row["outcome"] not in LABELS:
            raise ValueError(
                "Blank or unsupported reviewer label; no completed validation can be claimed"
            )
        if not row["reviewer"].strip() or len(row["rationale"].strip()) < 20:
            raise ValueError("Reviewer identity and substantive rationale are required")
        date.fromisoformat(row["checked_on"])
        if row["outcome"] != "not_observed" and not row["registry_name"].strip():
            raise ValueError("Observed findings require the observed legal name")
        output[key] = row
    return output


def compare_reviewers(first, second, expected_first, expected_second):
    left, right = (
        validate_labels(first, expected_first),
        validate_labels(second, expected_second),
    )
    cells = Counter()
    for key, row in right.items():
        if (
            key not in left
            or left[key]["reviewer"].strip().casefold()
            == row["reviewer"].strip().casefold()
        ):
            raise ValueError(
                "Second-review cases require a different declared reviewer"
            )
        cells[(left[key]["outcome"], row["outcome"])] += 1
    n = len(right)
    if not n:
        raise ValueError("No second-review cases supplied")
    disagreements = [
        key for key in sorted(right) if left[key]["outcome"] != right[key]["outcome"]
    ]
    return dict(
        first_cases=len(left),
        second_cases=n,
        raw_agreement=(n - len(disagreements)) / n,
        disagreement_keys=disagreements,
        label_matrix=[
            dict(first=a, second=b, cases=count)
            for (a, b), count in sorted(cells.items())
        ],
        interpretation="Agreement between submitted categorical labels, including unavailable/unresolved outcomes. Reviewer identities are declared, not authenticated; this tool cannot establish independence or population matching precision. Keep both labels and adjudicate disagreements explicitly.",
    )


def read_labels(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
