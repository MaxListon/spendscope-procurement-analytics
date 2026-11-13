import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "compare_results", Path(__file__).parents[1] / "scripts/compare_results.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_rebuild_comparison_tolerates_only_roundoff():
    module.compare(
        {"value": 1e9, "supported": True}, {"value": 1e9 + 0.0001, "supported": True}
    )


@pytest.mark.parametrize(
    "expected,actual",
    [
        ({"count": 10}, {"count": 11}),
        ({"supported": True}, {"supported": 1}),
        ({"median": 10}, {"median": 10.01}),
        ({"id": "a"}, {"id": "b"}),
        ({"x": 1}, {"x": 1, "extra": 1}),
        ([1], [1, 2]),
        (1, float("nan")),
    ],
)
def test_rebuild_comparison_rejects_changed_results(expected, actual):
    with pytest.raises(ValueError):
        module.compare(expected, actual)
