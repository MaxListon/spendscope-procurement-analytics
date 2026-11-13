"""Compare independently rebuilt analytical results; exclude platform-specific build metadata."""

import argparse
import json
import math
from pathlib import Path


def compare(expected, actual, path="$"):
    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(expected) is not type(actual) or expected != actual:
            raise ValueError(f"{path}: boolean mismatch")
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if (
            not math.isfinite(expected)
            or not math.isfinite(actual)
            or not math.isclose(expected, actual, rel_tol=1e-10, abs_tol=1e-7)
        ):
            raise ValueError(f"{path}: numerical mismatch {expected!r} != {actual!r}")
    elif isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            raise ValueError(f"{path}: schema mismatch")
        for key in expected:
            compare(expected[key], actual[key], f"{path}.{key}")
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            raise ValueError(f"{path}: length mismatch")
        for i, (left, right) in enumerate(zip(expected, actual)):
            compare(left, right, f"{path}[{i}]")
    elif type(expected) is not type(actual) or expected != actual:
        raise ValueError(f"{path}: value mismatch")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    compare(json.loads(args.expected.read_text()), json.loads(args.actual.read_text()))
    print("Independent analytical rebuild matches the committed results.")


if __name__ == "__main__":
    main()
