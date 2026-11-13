"""Generate decision-focused case studies from the executed evidence, not hand-entered metrics."""

from html import escape
import json


def business_cases(data, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    if baseline["source_hashes"] != [x["sha256"] for x in data["source"]["files"]]:
        raise ValueError(
            "Comparison baseline uses different source archives; revalidate it explicitly"
        )
    total = sum(r["award_value"] for r in data["annual"])
    current = sum(r["attributed_value"] for r in data["buyers"])
    old_share = baseline["attributable_value"] / baseline["award_value"]
    share = current / total
    q = data["quality"]
    largest = data["notice_review"]["records"][0]
    buyer = data["statistics"]["buyers"][0]
    audit = data["registry_audit"]["summary"]
    linkage = data["process_linkage"]
    money = lambda x: f"£{x / 1e9:,.2f}bn"
    md = f"""# SpendScope: evidence before supplier prioritization

## Decision

Use the dashboard to prioritize source-record and identity review. Do not interpret award commitments as payments, rankings as verified supplier performance, or hypothetical sensitivity scenarios as savings.

## Case 1 — A source instruction had become a supplier

The upgraded rules identify {q["placeholder_supplier_links"]:,} placeholder links and {q["invalid_registration_links"]:,} malformed registration links across the normalized source. Examples include attachment-list instructions and generic labels such as “Various.” They remain in headline award totals but cannot carry supplier shares.

Using the same pinned archives, combined identity/evidence improvements changed attributable value from {money(baseline["attributable_value"])} ({old_share:.1%} of eligible value) to {money(current)} ({share:.1%}). The difference is a change in analytical attribution, not reduced procurement spend or measured savings. Exact reviewed approvals also restore selected legitimate names, so the difference must not be attributed to one exclusion rule alone.

The versioned evidence review contains {sum(q["identity_decisions"].values())} targeted registration/name cases: {q["identity_decisions"].get("accept", 0)} approvals, {q["identity_decisions"].get("reject", 0)} rejections and {q["identity_decisions"].get("unresolved", 0)} unresolved cases. Five Companies House records anchor the accepted exact names. This is not a random test set or an independent accuracy audit.

## Random validation — a frozen registry sample

A deterministic sample of {audit["sample_size"]} from {audit["frame_count"]:,} previously unreviewed GB-COH identities produced {audit["outcomes"]["compatible"]} compatible registry-name records, {audit["outcomes"]["name_conflict"]} name conflicts and {audit["outcomes"]["not_observed"]} unobserved records. Confirmed agreement is {audit["confirmed_agreement_rate"]:.1%}, with a 95% Wilson interval of {audit["confirmed_agreement_wilson"][0]:.1%}–{audit["confirmed_agreement_wilson"][1]:.1%}. Missing-evidence bounds are {audit["missing_evidence_bounds"][0]:.1%}–{audit["missing_evidence_bounds"][1]:.1%}. The sample was frozen before its registry observations; subsequent conflict holdbacks are documented remediation, not a claim of independently measured post-remediation accuracy.

This is registry-name consistency in a restricted registration-evidence frame, not precision/recall of all supplier matching. Name-only identities, source assignment errors despite a matching legal name, and independent professional validation remain outside this result.

## Case 2 — A framework ceiling is not a payment

The largest recorded award is {money(largest["snapshot_amount"])}: {largest["snapshot_title"]}. The linked notice displays the same amount and {largest["page_supplier_count"]} suppliers, and explains a potential framework covering multiple users, lots and years. Agreement confirms a source representation, not distinct expenditure or that the ceiling will be used. The award stays in headline totals once and is not attributed to each of its suppliers.

Source: {largest["source_url"]}

Twenty large award records were selected for page review; {q["notice_pages_observed"]} linked pages were observed and {q["notice_attribution_holdbacks"]} records were held back from attribution for unresolved stage/context/cardinality issues or attachment-list placeholders. Original amounts are never silently rewritten. Live notice pages and pinned compiled snapshots can represent different points in a procurement's history.

## Case 3 — Related awards change the stability assessment

For the leading supported buyer identity by attributable value, {buyer["buyer_name"]}, {buyer["awards"]} awards belong to {buyer["processes"]} procurement processes. R independently reproduces HHI {buyer["hhi"]:,.0f}. The process-clustered percentile interval is {buyer["hhi_low"]:,.0f}–{buyer["hhi_high"]:,.0f}; the independent-award alternative is {buyer["award_bootstrap_low"]:,.0f}–{buyer["award_bootstrap_high"]:,.0f}. These intervals are descriptive, with {data["statistics"]["buyer_replicates"]} draws under each sampling assumption.

Removing the largest award gives HHI {buyer["hhi_without_largest"]:,.0f}; buyer-specific 99th-percentile capping gives {buyer["hhi_capped"]:,.0f}. Registration evidence covers {buyer["registered_value_share"]:.1%} of this buyer identity's attributable value. Neither the ranking nor interval is a guarantee of operational supplier dependency. Review identity confidence and individual commitments before making a procurement decision.

## Decision worksheet — should this buyer enter a supplier-risk review?

Question: does {buyer["buyer_name"]}'s observed portfolio justify immediately changing supplier strategy? Recommendation: prioritize verification, not a supplier change. The process interval spans {buyer["hhi_low"]:,.0f}–{buyer["hhi_high"]:,.0f}; the largest-award sensitivity changes the point estimate from {buyer["hhi"]:,.0f} to {buyer["hhi_without_largest"]:,.0f}. That instability and {buyer["registered_value_share"]:.1%} registration-evidence coverage make an operational dependency claim premature.

Analyst handoff: download buyer metrics and buyer sensitivity; locate the buyer in the Source explorer; inspect its largest commitments and original notices. Ask the stakeholder for supplier legal IDs, framework/call-off relationships, actual payments, service criticality and substitution lead times. Reconcile these to the observed publication identity before escalating any supplier-risk recommendation.

Acceptance gate: do not recommend a supplier intervention until identity gaps and overlapping commitments are resolved, payment records reconcile to the intended period, and a procurement owner confirms service criticality. Record unresolved discrepancies. This is a proposed decision workflow, not a stakeholder-endorsed action or measured savings.

## Expanded evidence collection — names are a screening signal

The frozen hash ordering now extends to 200 identities: the original 40-case audit plus 160 additional automated registry observations. The latter yield {data["registry_screen"]["summary"]["outcomes"]["name_agrees"]} current/former-name agreements, {data["registry_screen"]["summary"]["outcomes"]["needs_review"]} cases requiring review and {data["registry_screen"]["summary"]["outcomes"]["not_observed"]} unavailable pages. These are not additional human-reviewed accuracy labels. A versioned follow-up queue preserves nonmatches and unavailable evidence; no attribution rule changes automatically.

## Dependence beyond one process

The source provides {linkage["declarations"]} related-process declarations but only {linkage["resolved_edges"]} usable in-universe OCID links. No graph edges are invented from missing identifiers. R therefore also publishes buyer-clustered category medians and calendar-quarter buyer-HHI sensitivity, preserving dependence under broader alternative assumptions. These do not establish true framework/call-off relationships.

## Recommended next action

Begin with source evidence and identity gaps, then request actual purchasing/payment records from a real stakeholder. Conduct an independent labeled supplier review before reporting population matching accuracy. Process clustering still misses unknown links across distinct OCIDs and missing reporting. No external stakeholder validation or measured organizational impact is claimed.

Evidence: reports/quality.json, buyer_evidence.csv, buyer_sensitivity.csv, comparison_thresholds.csv, identity_decisions.csv, notice_checks.json and data/sources.json. Baseline comparison: v{baseline["version"]}, commit {baseline["commit"]}.
"""
    # Markdown paragraphs are simple and source values are escaped before HTML rendering.
    blocks = []
    for block in md.split("\n\n"):
        if block.startswith("# "):
            blocks.append("<h1>" + escape(block[2:]) + "</h1>")
        elif block.startswith("## "):
            blocks.append("<h2>" + escape(block[3:]) + "</h2>")
        elif block.startswith("Source: https://"):
            url = block.removeprefix("Source: ")
            blocks.append(
                f'<p><a href="{escape(url, quote=True)}">Original award notice ↗</a></p>'
            )
        else:
            blocks.append("<p>" + escape(block) + "</p>")
    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SpendScope | Business case studies</title><link rel="stylesheet" href="research.css"></head><body><main><a href="index.html">← Dashboard</a><p class="eyebrow">BUSINESS CASE STUDIES / EXECUTED RESULTS</p>'
        + "".join(blocks)
        + '<p><a href="research.html">R research note ↗</a> · <a href="reports/notice_checks.json">Evidence register ↓</a></p></main></body></html>'
    )
    return md, html
