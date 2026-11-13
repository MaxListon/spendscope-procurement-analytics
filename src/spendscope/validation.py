"""Reproducible audit sampling and conservative observed-source linkage."""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def hash_sample(frame, seed, size):
    if size < 1 or size > len(frame):
        raise ValueError("Invalid audit sample size")
    if len({r["supplier_key"] for r in frame}) != len(frame):
        raise ValueError("Audit frame must have unique registration identities")
    return sorted(
        frame,
        key=lambda r: (
            hashlib.sha256((seed + "|" + r["supplier_key"]).encode()).hexdigest(),
            r["supplier_key"],
        ),
    )[:size]


def wilson(successes, total, z=1.959963984540054):
    if total < 1 or not 0 <= successes <= total:
        raise ValueError("Invalid binomial counts")
    p = successes / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return [
        0.0 if successes == 0 else max(0.0, center - half),
        1.0 if successes == total else min(1.0, center + half),
    ]


def registry_audit(con, path):
    spec = json.loads(Path(path).read_text())
    frame = (
        con.sql(
            "SELECT s.supplier_key,max(s.supplier_name) supplier_name,count(*) award_links FROM awards a JOIN suppliers s USING(award_key) WHERE a.eligible AND a.supplier_count=1 AND NOT a.notice_review_block AND s.identity_basis='registered' AND s.supplier_key LIKE 'GB-COH:%' GROUP BY s.supplier_key ORDER BY s.supplier_key"
        )
        .df()
        .to_dict("records")
    )
    fingerprint = hashlib.sha256(
        json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if len(frame) != spec["frame_count"] or fingerprint != spec["frame_sha256"]:
        raise ValueError(
            "Frozen audit population changed; revalidate the sample explicitly"
        )
    chosen = hash_sample(frame, spec["selection_seed"], len(spec["records"]))
    if [r["supplier_key"] for r in chosen] != [
        r["supplier_key"] for r in spec["records"]
    ]:
        raise ValueError("Audit is not the declared reproducible sample")
    for selected, row in zip(chosen, spec["records"]):
        if selected["supplier_name"] != row["supplier_name"] or row["outcome"] not in (
            "compatible",
            "name_conflict",
            "not_observed",
        ):
            raise ValueError("Audit record does not match its frozen identity")
        if not row.get("rationale") or not row.get("checked_on"):
            raise ValueError("Audit finding lacks rationale or observation date")
        if row["outcome"] != "not_observed" and (
            row.get("access") != "observed" or not row.get("registry_name")
        ):
            raise ValueError("A registry finding requires observed legal-name evidence")
        number = row["supplier_key"].split(":", 1)[1]
        if (
            row["evidence_url"]
            != "https://find-and-update.company-information.service.gov.uk/company/"
            + number
        ):
            raise ValueError("Audit cites a different registration")
        if row["block_attribution"] != (row["outcome"] == "name_conflict"):
            raise ValueError("Audit holdback and documented finding disagree")
    counts = Counter(r["outcome"] for r in spec["records"])
    n = len(chosen)
    compatible = counts["compatible"]
    observed = n - counts["not_observed"]
    summary = dict(
        frame_count=len(frame),
        sample_size=n,
        outcomes=dict(counts),
        confirmed_agreement_rate=compatible / n,
        confirmed_agreement_wilson=wilson(compatible, n),
        observed_only_agreement_rate=compatible / observed if observed else None,
        missing_evidence_bounds=[
            compatible / n,
            (compatible + counts["not_observed"]) / n,
        ],
        selection_seed=spec["selection_seed"],
        selected_from_commit=spec["selected_from_commit"],
        interpretation=spec["interpretation"],
    )
    conflicts = [r["supplier_key"] for r in spec["records"] if r["block_attribution"]]
    # Evidence label changes only the attribution gate; the raw links and award amounts remain intact.
    for key in conflicts:
        con.execute(
            "UPDATE suppliers SET identity_basis='registry-audit-conflict' WHERE supplier_key=? AND identity_basis='registered'",
            [key],
        )
    return spec, summary


def related_process_clusters(records):
    """Use only explicit OCID identifiers pointing to processes inside the selected universe."""
    parents = {key: key for key in records}

    def find(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    count = Counter()
    edges = set()
    for ocid, record in records.items():
        links = record.get("relatedProcesses") or []
        if links:
            count["processes_with_declarations"] += 1
        for link in links:
            count["declarations"] += 1
            identifier = link.get("identifier")
            if (
                link.get("scheme") != "ocid"
                or not isinstance(identifier, str)
                or not identifier.strip()
            ):
                count["missing_or_non_ocid_identifier"] += 1
                continue
            target = identifier.strip()
            if target not in parents:
                count["target_outside_universe"] += 1
                continue
            if target == ocid:
                count["self_links"] += 1
                continue
            left, right = find(ocid), find(target)
            if left != right:
                parents[max(left, right)] = min(left, right)
            edges.add(tuple(sorted((ocid, target))))
    mapping = {key: find(key) for key in sorted(records)}
    sizes = Counter(mapping.values())
    summary = {
        k: int(count[k])
        for k in (
            "processes_with_declarations",
            "declarations",
            "missing_or_non_ocid_identifier",
            "target_outside_universe",
            "self_links",
        )
    }
    summary.update(
        processes=len(records),
        resolved_edges=len(edges),
        connected_components=len(sizes),
        processes_in_linked_components=sum(n for n in sizes.values() if n > 1),
        interpretation="Only declared OCID links with observed in-universe targets are joined. Missing identifiers do not justify inferred framework relationships.",
    )
    return mapping, summary
