"""Score genuine completed review submissions. Blank worksheets fail closed."""

import argparse
import json
from pathlib import Path
from spendscope.reviewer_agreement import compare_reviewers, read_labels
from spendscope.validation import hash_sample


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads((args.root / "data/review/registry_screen.json").read_text())[
        "records"
    ]
    frame = {r["supplier_key"]: r for r in records}
    subset = {
        r["supplier_key"]: r
        for r in hash_sample(records, "second-review-subset-v1", 40)
    }
    result = compare_reviewers(
        read_labels(args.first), read_labels(args.second), frame, subset
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Submitted-label agreement:", result["raw_agreement"])


if __name__ == "__main__":
    main()
