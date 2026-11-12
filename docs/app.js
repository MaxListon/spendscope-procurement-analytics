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
        ($("buyer-support").value === "all" || r.supported),
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
      "Support",
    ],
    filteredBuyers
      .slice(0, 200)
      .map(
        (r) =>
          "<tr>" +
          td(r.buyer_name) +
          td(money(r.attributed_value), "num") +
          td(number(r.attributed_awards), "num") +
          td(number(r.suppliers), "num") +
          td(number(r.hhi), "num") +
          td(pct(r.top1_share), "num") +
          td(pct(r.value_coverage), "num") +
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
    ["Award / published notice", "Buyer", "Year", "Value", "Suppliers"],
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
          "</tr>",
      ),
  );
}
function view(name) {
  const allowed = ["overview", "buyers", "suppliers", "awards", "methods"];
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
for (const id of ["buyer-search", "buyer-support", "buyer-sort"])
  $(id).addEventListener("input", () => data && buyers());
$("supplier-search").addEventListener("input", () => data && suppliers());
$("award-search").addEventListener("input", () => data && awards());
$("export-buyers").addEventListener("click", () => {
  if (!data) return;
  const keys = [
    "buyer_name",
    "attributed_value",
    "attributed_awards",
    "suppliers",
    "hhi",
    "top1_share",
    "value_coverage",
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
        "Sole named supplier; no ID/name conflict",
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
      "</ul><p>Unknown source identities and registered ID/name conflicts are excluded from supplier attribution, never from eligible award totals.</p>";
    buyers();
    suppliers();
    awards();
    view(location.hash.slice(1));
  })
  .catch(() => {
    $("status").textContent =
      "Could not load analysis. Serve this directory over HTTP and check data.json.";
  });
