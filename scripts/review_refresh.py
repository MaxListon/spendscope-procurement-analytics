"""Write a review report; exit 2 for material changes, 1 for invalid data, 0 otherwise."""

import argparse
import json
from pathlib import Path
from spendscope.refresh import review_refresh


def main():
    p = argparse.ArgumentParser()
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = review_refresh(
        json.loads(args.before.read_text()), json.loads(args.after.read_text())
    )
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(result["status"])
    return 2 if result["status"] == "review_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
