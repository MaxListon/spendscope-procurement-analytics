"use strict";
const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const number = (x) => new Intl.NumberFormat("en-GB").format(Math.round(x));
const money = (x) =>
  "£" +
  (x >= 1e9
    ? (x / 1e9).toFixed(2) + "bn"
    : x >= 1e6
      ? (x / 1e6).toFixed(1) + "m"
      : number(x));
const pct = (x) => (x * 100).toFixed(1) + "%";
let data,
  filteredBuyers = [];
function table(target, headers, rows) {
  $(target).innerHTML =
    "<table><thead><tr>" +
    headers.map((h) => '<th scope="col">' + esc(h) + "</th>").join("") +
    "</tr></thead><tbody>" +
    rows.join("") +
    "</tbody></table>";
  if (!rows.length)
    $(target).innerHTML = '<p style="padding:20px">No matching records.</p>';
}
const td = (x, cls = "") => '<td class="' + cls + '">' + esc(x) + "</td>";
function buyers() {
  const query = $("buyer-search").value.toLocaleLowerCase();
  const sort = $("buyer-sort").value;
  filteredBuyers = data.buyers
    .filter(
      (r) =>
        r.buyer_name.toLocaleLowerCase().includes(query) &&
        ($("buyer-support").value === "all" || r.supported) &&
        ($("buyer-evidence").value === "all" ||
          (r.registered_value_share >= 0.5 && r.registered_awards >= 10)),
    )
    .sort(
      (a, b) => b[sort] - a[sort] || a.buyer_key.localeCompare(b.buyer_key),
    );
  $("buyer-count").textContent =
    number(filteredBuyers.length) +
    " matching buyers · showing first 200 · CSV includes all matches";
  table(
    "buyer-table",
    [
      "Buyer",
      "Attributable value",
      "Awards",
      "Suppliers",
      "HHI",
      "Largest supplier",
      "Coverage",
      "Registration evidence",
      "Support",
    ],
    filteredBuyers
      .slice(0, 200)
      .map(
        (r) =>
          "<tr>" +
          '<td><a href="workspace.html?buyer=' +
          encodeURIComponent(r.buyer_key) +
          '">' +
          esc(r.buyer_name) +
          '</a><small class="buyer-id">' +
          esc(r.buyer_key) +
          "</small></td>" +
          td(money(r.attributed_value), "num") +
          td(number(r.attributed_awards), "num") +
          td(number(r.suppliers), "num") +
          td(number(r.hhi), "num") +
          td(pct(r.top1_share), "num") +
          td(pct(r.value_coverage), "num") +
          td(pct(r.registered_value_share), "num") +
          '<td><span class="tag ' +
          (r.supported ? "" : "warn") +
          '">' +
          (r.supported ? "Supported" : "Limited") +
          "</span></td></tr>",
      ),
  );
}
function suppliers() {
  const q = $("supplier-search").value.toLocaleLowerCase();
  table(
    "supplier-table",
    ["Supplier", "Attributed value", "Awards", "Buyers", "Identity evidence"],
    data.suppliers
      .filter((r) => r.supplier_name.toLocaleLowerCase().includes(q))
      .map(
        (r) =>
          "<tr>" +
          td(r.supplier_name) +
          td(money(r.award_value), "num") +
          td(number(r.awards), "num") +
          td(number(r.buyers), "num") +
          td(r.identity_basis) +
          "</tr>",
      ),
  );
}
function awards() {
  const q = $("award-search").value.toLocaleLowerCase();
  table(
    "award-table",
    [
      "Award / published notice",
      "Buyer",
      "Year",
      "Value",
      "Suppliers",
      "Review",
    ],
    data.awards
      .filter((r) =>
        (r.title + " " + r.buyer_name).toLocaleLowerCase().includes(q),
      )
      .map(
        (r) =>
          "<tr><td>" +
          (r.source_url.startsWith(
            "https://www.contractsfinder.service.gov.uk/Notice/",
          )
            ? '<a target="_blank" rel="noopener noreferrer" href="' +
              esc(r.source_url) +
              '">' +
              esc(r.title) +
              " ↗</a>"
            : esc(r.title)) +
          "</td>" +
          td(r.buyer_name) +
          td(r.year) +
          td(money(r.amount), "num") +
          td(r.supplier_count, "num") +
          td(r.notice_review_status) +
          "</tr>",
      ),
  );
}
function view(name) {
  const allowed = [
    "overview",
    "buyers",
    "suppliers",
    "awards",
    "validation",
    "methods",
  ];
  if (!allowed.includes(name)) name = "overview";
  document.querySelectorAll(".view").forEach((e) => (e.hidden = e.id !== name));
  document
    .querySelectorAll("nav button")
    .forEach((e) =>
      e.setAttribute("aria-pressed", String(e.dataset.view === name)),
    );
  document.body.dataset.view = name;
  history.replaceState(null, "", "#" + name);
}
document
  .querySelectorAll("nav button")
  .forEach((b) => b.addEventListener("click", () => view(b.dataset.view)));
window.addEventListener("hashchange", () => view(location.hash.slice(1)));
for (const id of [
  "buyer-search",
  "buyer-support",
  "buyer-sort",
  "buyer-evidence",
])
  $(id).addEventListener("input", () => data && buyers());
$("supplier-search").addEventListener("input", () => data && suppliers());
$("award-search").addEventListener("input", () => data && awards());
$("export-buyers").addEventListener("click", () => {
  if (!data) return;
  const keys = [
    "buyer_key",
    "buyer_name",
    "attributed_value",
    "attributed_awards",
    "suppliers",
    "hhi",
    "top1_share",
    "value_coverage",
    "registered_value_share",
    "registered_awards",
    "supported",
  ];
  // Prefix spreadsheet formula characters in text fields; preserve numeric metrics.
  const quote = (x) => '"' + String(x).replace(/"/g, '""') + '"';
  const safe = (x) =>
    typeof x === "string" && /^[=+@\-\t\r]/.test(x) ? "'" + x : x;
  const csv = [
    keys.join(","),
    ...filteredBuyers.map((r) => keys.map((k) => quote(safe(r[k]))).join(",")),
  ].join("\r\n");
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = "spendscope-buyers.csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
fetch("data.json")
  .then((r) => {
    if (!r.ok) throw Error("Analysis unavailable");
    return r.json();
  })
  .then((d) => {
    const evidence = new Map(d.buyer_evidence.map((r) => [r.buyer_key, r]));
    d.buyers = d.buyers.map((r) => ({ ...r, ...evidence.get(r.buyer_key) }));
    data = d;
    const total = d.annual.reduce((s, r) => s + r.award_value, 0);
    const count = d.annual.reduce((s, r) => s + r.awards, 0);
    const attributed = d.buyers.reduce((s, r) => s + r.attributed_value, 0);
    const supported = d.buyers.filter((r) => r.supported).length;
    $("status").textContent =
      "✓ " +
      Object.values(d.quality.contracts).filter(Boolean).length +
      " runtime data contracts passed · Executed SQL + R analysis";
    $("kpis").innerHTML = [
      [
        "Recorded award value",
        money(total),
        "Eligible awards across three award years",
      ],
      ["Eligible awards", number(count), "One row per process + award ID"],
      [
        "Attributable value",
        pct(attributed / total),
        "After placeholder and evidence holdbacks",
      ],
      [
        "Supported buyers",
        number(supported),
        "≥30 attributable awards · ≥80% coverage",
      ],
    ]
      .map(
        ([label, value, sub]) =>
          '<article class="kpi"><span>' +
          label +
          "</span><strong>" +
          value +
          "</strong><small>" +
          sub +
          "</small></article>",
      )
      .join("");
    const max = Math.max(...d.annual.map((r) => r.award_value));
    $("annual-chart").innerHTML = d.annual
      .map(
        (r) =>
          '<div class="bar-row"><span>' +
          r.year +
          '</span><div class="bar-track"><div class="bar" style="width:' +
          Math.max(0, Math.min(100, (r.award_value / max) * 100)) +
          '%"></div></div><strong>' +
          money(r.award_value) +
          '</strong></div><p class="muted">' +
          number(r.awards) +
          " awards · median " +
          money(r.median_award) +
          "</p>",
      )
      .join("");
    const q = d.quality;
    $("quality").innerHTML =
      "<p>" +
      number(q.source_lines) +
      " source process snapshots → " +
      number(q.unique_processes) +
      " unique processes → " +
      number(q.award_rows) +
      " award records.</p><p>" +
      number(q.repeated_process_snapshots) +
      " repeated process snapshots resolved by latest publication timestamp.</p><p>" +
      number(q.multi_supplier_awards) +
      " multi-supplier awards; " +
      number(q.missing_supplier_awards) +
      " awards without a supplier; " +
      number(q.registered_identity_collisions) +
      " registered IDs associated with different normalized names.</p><h3>Exclusions, first matching rule</h3><ul>" +
      Object.entries(q.exclusion_counts)
        .filter(([k]) => k)
        .map(([k, v]) => "<li>" + esc(k) + ": " + number(v) + "</li>")
        .join("") +
      "</ul><p>" +
      number(q.placeholder_supplier_links) +
      " placeholder supplier links and " +
      number(q.invalid_registration_links) +
      " malformed registration links are excluded from attribution. " +
      number(q.reviewed_registered_links) +
      " links carry exact reviewed registration/name approvals.</p><p>Unresolved identities and notice discrepancies never remove eligible values from headline totals.</p>";
    validation();
    buyers();
    suppliers();
    awards();
    view(location.hash.slice(1));
  })
  .catch(() => {
    $("status").textContent =
      "Could not load analysis. Serve this directory over HTTP and check data.json.";
  });

function validation() {
  const screen = data.registry_screen.summary;
  $("expanded-screen-summary").textContent =
    "The original 40-case audit is preserved. Another " +
    screen.automated_cases +
    " identities extend the same frozen sample to " +
    screen.expanded_sample_size +
    ": " +
    screen.outcomes.name_agrees +
    " have matching current/former legal names, " +
    screen.outcomes.needs_review +
    " need review, and " +
    screen.outcomes.not_observed +
    " pages were unavailable. Automated name consistency does not verify the source supplier assignment. No automatic attribution changes.";
  table(
    "expanded-screen-table",
    ["Published supplier", "Registry names", "Screen outcome", "Evidence"],
    data.registry_screen.records
      .filter((r) => r.outcome !== "name_agrees")
      .map(
        (r) =>
          "<tr>" +
          td(r.supplier_name) +
          td(r.registry_names.join(" / ") || "Not observed") +
          td(r.outcome) +
          '<td><a href="' +
          esc(r.evidence_url) +
          '" target="_blank" rel="noopener noreferrer">' +
          esc(r.supplier_key) +
          " ↗</a></td></tr>",
      ),
  );
  const audit = data.registry_audit.summary;
  $("random-audit-summary").innerHTML =
    "<p><strong>" +
    audit.outcomes.compatible +
    " of " +
    audit.sample_size +
    " records (" +
    pct(audit.confirmed_agreement_rate) +
    ")</strong> have compatible legal-name evidence. " +
    audit.outcomes.name_conflict +
    " name conflicts and " +
    audit.outcomes.not_observed +
    " unobserved registry records remain explicit.</p><p>95% Wilson interval for confirmed agreement: " +
    pct(audit.confirmed_agreement_wilson[0]) +
    "–" +
    pct(audit.confirmed_agreement_wilson[1]) +
    ". Observed-only agreement is " +
    pct(audit.observed_only_agreement_rate) +
    "; missing-evidence bounds are " +
    pct(audit.missing_evidence_bounds[0]) +
    "–" +
    pct(audit.missing_evidence_bounds[1]) +
    ". Frame: " +
    number(audit.frame_count) +
    " distinct registration identities.</p>";
  table(
    "random-audit-table",
    ["Published supplier", "Registry legal name", "Outcome", "Evidence"],
    data.registry_audit.records.map(
      (r) =>
        "<tr>" +
        td(r.supplier_name) +
        td(r.registry_name || "Not observed") +
        td(r.outcome) +
        '<td><a href="' +
        esc(r.evidence_url) +
        '" target="_blank" rel="noopener noreferrer">' +
        esc(r.supplier_key) +
        " ↗</a></td></tr>",
    ),
  );
  const links = data.process_linkage;
  $("linkage-summary").textContent =
    number(links.declarations) +
    " related-process declarations; " +
    number(links.resolved_edges) +
    " resolvable links within the selected universe. Missing identifiers are not inferred.";
  const q = data.quality;
  const pairs = Object.values(q.identity_decisions).reduce((s, n) => s + n, 0);
  $("review-kpis").innerHTML = [
    ["Identity cases", pairs, "Targeted normalized-name/registration pairs"],
    [
      "Notice records selected",
      q.notice_records_checked,
      q.notice_pages_observed + " linked pages observed; spending not verified",
    ],
    [
      "Notice holdbacks",
      q.notice_attribution_holdbacks,
      "Kept in totals; excluded from attribution",
    ],
    [
      "Placeholder links",
      q.placeholder_supplier_links,
      "Attachment instructions and generic labels",
    ],
  ]
    .map(
      ([label, value, sub]) =>
        '<article class="kpi"><span>' +
        esc(label) +
        "</span><strong>" +
        number(value) +
        "</strong><small>" +
        esc(sub) +
        "</small></article>",
    )
    .join("");
  table(
    "notice-review-table",
    [
      "Snapshot award / notice",
      "Recorded value",
      "Page award value",
      "Result",
      "Reason",
    ],
    data.notice_review.records.map(
      (r) =>
        '<tr><td><a href="' +
        esc(r.source_url) +
        '" target="_blank" rel="noopener noreferrer">' +
        esc(r.snapshot_title) +
        " ↗</a></td>" +
        td(money(r.snapshot_amount), "num") +
        td(
          r.page_award_value === null
            ? "Not observed"
            : money(r.page_award_value),
          "num",
        ) +
        td(
          r.access_status === "not_observed"
            ? "Not observed"
            : r.block_attribution
              ? "Unresolved"
              : "Fields observed",
        ) +
        td(r.interpretation) +
        "</tr>",
    ),
  );
  table(
    "threshold-table",
    [
      "Minimum awards",
      "Minimum value coverage",
      "Buyer identities",
      "Attributable value",
    ],
    data.comparison_thresholds.map(
      (r) =>
        "<tr>" +
        td(r.min_awards, "num") +
        td(pct(r.min_coverage), "num") +
        td(number(r.supported_buyers), "num") +
        td(money(r.attributable_value), "num") +
        "</tr>",
    ),
  );
}
