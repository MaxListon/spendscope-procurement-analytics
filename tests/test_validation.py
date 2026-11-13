import hashlib
import pytest
from spendscope.validation import hash_sample, wilson, related_process_clusters


def test_audit_sampling_is_order_invariant_and_seeded():
    rows = [{"supplier_key": str(i)} for i in range(100)]
    a = hash_sample(rows, "fixed", 20)
    assert a == hash_sample(list(reversed(rows)), "fixed", 20)
    assert a != hash_sample(rows, "other", 20)
    assert len({r["supplier_key"] for r in a}) == 20
    expected = sorted(
        rows,
        key=lambda r: hashlib.sha256(
            ("fixed|" + r["supplier_key"]).encode()
        ).hexdigest(),
    )[:20]
    assert a == expected


@pytest.mark.parametrize("n,k", [(0, 0), (10, -1), (10, 11)])
def test_wilson_rejects_invalid_counts(n, k):
    with pytest.raises(ValueError):
        wilson(k, n)


def test_wilson_known_example_and_zero_success():
    low, high = wilson(36, 40)
    assert low == pytest.approx(0.7694822477)
    assert high == pytest.approx(0.9604204713)
    assert wilson(0, 10)[0] == 0
    assert wilson(10, 10)[1] == 1


def test_related_process_components_keep_transitive_links():
    records = {
        "a": {"relatedProcesses": [{"scheme": "ocid", "identifier": "b"}]},
        "b": {"relatedProcesses": [{"scheme": "ocid", "identifier": "c"}]},
        "c": {},
        "d": {},
    }
    mapping, summary = related_process_clusters(records)
    assert mapping == {"a": "a", "b": "a", "c": "a", "d": "d"}
    assert (
        summary["processes_in_linked_components"] == 3
        and summary["resolved_edges"] == 2
    )


def test_incomplete_declarations_never_invent_links():
    mapping, summary = related_process_clusters(
        {
            "a": {
                "relatedProcesses": [
                    {"id": "1", "relationship": ["parent"]},
                    {"scheme": "ocid", "identifier": "outside"},
                    {"scheme": "other", "identifier": "b"},
                    {"scheme": "ocid", "identifier": "a"},
                ]
            },
            "b": {},
        }
    )
    assert mapping == {"a": "a", "b": "b"}
    assert summary["missing_or_non_ocid_identifier"] == 2
    assert summary["target_outside_universe"] == 1 and summary["self_links"] == 1
    assert summary["resolved_edges"] == 0


def audit_fixture(tmp_path):
    import duckdb, json

    con = duckdb.connect()
    con.execute(
        "create table awards(award_key varchar,eligible boolean,supplier_count integer,notice_review_block boolean)"
    )
    con.execute(
        "create table suppliers(award_key varchar,supplier_key varchar,supplier_name varchar,identity_basis varchar)"
    )
    frame = []
    for i in (1, 2, 3):
        key = f"GB-COH:{i:08d}"
        name = f"Company {i}"
        con.execute("insert into awards values(?,true,1,false)", [str(i)])
        con.execute(
            "insert into suppliers values(?,?,?,'registered')", [str(i), key, name]
        )
        frame.append(dict(supplier_key=key, supplier_name=name, award_links=1))
    chosen = hash_sample(frame, "audit", 2)
    records = []
    for i, r in enumerate(chosen):
        records.append(
            {
                **r,
                "outcome": "compatible" if i == 0 else "name_conflict",
                "block_attribution": i == 1,
                "evidence_url": "https://find-and-update.company-information.service.gov.uk/company/"
                + r["supplier_key"].split(":")[1],
                "rationale": "Observed registry name evidence",
                "checked_on": "2026-11-12",
                "access": "observed",
                "registry_name": r["supplier_name"]
                if i == 0
                else "Different legal name",
            }
        )
    spec = dict(
        frame_count=3,
        frame_sha256=hashlib.sha256(
            json.dumps(frame, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        selection_seed="audit",
        selected_from_commit="test",
        interpretation="Test frame only",
        records=records,
    )
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(spec))
    return con, path, spec


def test_random_audit_holdbacks_do_not_erase_raw_links(tmp_path):
    from spendscope.validation import registry_audit

    con, path, spec = audit_fixture(tmp_path)
    _, summary = registry_audit(con, path)
    assert summary["sample_size"] == 2 and summary["confirmed_agreement_rate"] == 0.5
    assert con.sql("select count(*) from suppliers").fetchall()[0][0] == 3
    assert (
        con.sql(
            "select count(*) from suppliers where identity_basis='registry-audit-conflict'"
        ).fetchall()[0][0]
        == 1
    )
    con.close()


@pytest.mark.parametrize(
    "change", ["frame", "sample", "evidence", "label", "unobserved"]
)
def test_random_audit_fails_on_tampered_frame_or_evidence(tmp_path, change):
    import json
    from spendscope.validation import registry_audit

    con, path, spec = audit_fixture(tmp_path)
    if change == "frame":
        spec["frame_sha256"] = "changed"
    elif change == "sample":
        spec["records"].reverse()
    elif change == "evidence":
        spec["records"][0]["evidence_url"] = "https://example.com"
    elif change == "label":
        spec["records"][0]["block_attribution"] = True
    else:
        spec["records"][0]["access"] = "not_observed"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        registry_audit(con, path)
    con.close()
