"""Explicit, conservative change review between source snapshots; never auto-approves."""

import math


def unique_rows(rows, key):
    result = {}
    for row in rows:
        identity = row[key]
        if identity in result:
            raise ValueError(f"Duplicate {key}: {identity}")
        result[identity] = row
    return result


def finite(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError("Refresh metrics must be finite numbers")
    return value


def snapshot_metrics(data):
    annual = unique_rows(data["annual"], "year")
    buyers = unique_rows(data["buyers"], "buyer_key")
    total = sum(finite(r["award_value"]) for r in annual.values())
    awards = sum(finite(r["awards"]) for r in annual.values())
    attributed = sum(finite(r["attributed_value"]) for r in buyers.values())
    if total <= 0 or awards <= 0 or not 0 <= attributed <= total * (1 + 1e-10):
        raise ValueError("Invalid refresh totals or attribution denominator")
    if not data["quality"]["contracts"] or not all(
        v is True for v in data["quality"]["contracts"].values()
    ):
        raise ValueError("Refresh candidate contains failed or missing contracts")
    for row in buyers.values():
        if (
            type(row["supported"]) is not bool
            or not 0 <= finite(row["value_coverage"]) <= 1 + 1e-10
            or not 0 <= finite(row["hhi"]) <= 10000 + 1e-7
        ):
            raise ValueError("Invalid buyer evidence metrics")
    return dict(
        eligible_awards=awards,
        recorded_value=total,
        attributable_value=attributed,
        attribution_coverage=attributed / total,
        supported_buyers=sum(r["supported"] for r in buyers.values()),
    ), buyers


def review_refresh(before, after):
    old, old_buyers = snapshot_metrics(before)
    new, new_buyers = snapshot_metrics(after)
    sources = lambda d: sorted((r["year"], r["sha256"]) for r in d["source"]["files"])
    source_changed = sources(before) != sources(after)
    changes = {
        k: dict(before=old[k], after=new[k], absolute_change=new[k] - old[k])
        for k in old
    }
    reasons = []
    if source_changed:
        reasons.append(
            "Source fingerprints changed: revalidate baseline comparisons and frozen audit frames."
        )
    for key in ("eligible_awards", "recorded_value", "attributable_value"):
        if abs(new[key] - old[key]) / max(abs(old[key]), 1) > 0.05:
            reasons.append(f"{key} changed by more than 5%.")
    if abs(new["attribution_coverage"] - old["attribution_coverage"]) > 0.02:
        reasons.append("Attribution coverage changed by more than 2 percentage points.")
    transitions = []
    for key in sorted(old_buyers.keys() | new_buyers.keys()):
        left, right = old_buyers.get(key), new_buyers.get(key)
        if left is None or right is None or left["supported"] != right["supported"]:
            transitions.append(
                dict(
                    buyer_key=key,
                    buyer_name=(right or left)["buyer_name"],
                    before=left["supported"] if left else None,
                    after=right["supported"] if right else None,
                )
            )
    if transitions:
        reasons.append(
            "Buyer population or support gates changed; inspect the transition list."
        )
    largest_hhi_changes = sorted(
        (
            dict(
                buyer_key=k,
                buyer_name=new_buyers[k]["buyer_name"],
                hhi_before=old_buyers[k]["hhi"],
                hhi_after=new_buyers[k]["hhi"],
                change=new_buyers[k]["hhi"] - old_buyers[k]["hhi"],
            )
            for k in old_buyers.keys() & new_buyers.keys()
        ),
        key=lambda r: (-abs(r["change"]), r["buyer_key"]),
    )[:20]
    if any(abs(r["change"]) > 500 for r in largest_hhi_changes):
        reasons.append("At least one buyer HHI changed by more than 500 points.")
    return dict(
        status="review_required" if reasons else "no_material_change_detected",
        auto_approved=False,
        source_changed=source_changed,
        metrics=changes,
        reasons=reasons,
        support_transitions=transitions,
        largest_hhi_changes=largest_hhi_changes,
        interpretation="Review thresholds are operational heuristics, not statistical significance. Every source refresh still requires documented human approval; no new snapshot is claimed by a same-source rebuild.",
    )
