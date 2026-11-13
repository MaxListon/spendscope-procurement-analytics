"use strict";
const $ = (id) => document.getElementById(id),
  model = window.SpendScopeReview;
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const num = (n) =>
  new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(n);
const money = (n) =>
  "£" +
  (n >= 1e9
    ? (n / 1e9).toFixed(2) + "bn"
    : n >= 1e6
      ? (n / 1e6).toFixed(2) + "m"
      : num(n));
const pct = (n) => (100 * n).toFixed(1) + "%";
const labels = {
  open: "Open",
  in_review: "In review",
  awaiting_evidence: "Awaiting evidence",
  closed: "Closed with decision",
};
let index,
  profile,
  db,
  events = [],
  filtered = [],
  shownAwards = 20,
  shownSuppliers = 20,
  loadedLast = null;
let statuses = new Map();
let channel;
try {
  channel = new BroadcastChannel("spendscope-review-updates");
  channel.onmessage = () => refreshReviews().catch(showStorageError);
} catch {}
function grid(target, heads, rows) {
  $(target).innerHTML = rows.length
    ? "<table><thead><tr>" +
      heads.map((h) => '<th scope="col">' + esc(h) + "</th>").join("") +
      "</tr></thead><tbody>" +
      rows.join("") +
      "</tbody></table>"
    : '<p class="empty">No matching records.</p>';
}
const td = (s) => "<td>" + esc(s) + "</td>";
function download(name, body, type = "application/json") {
  const blob = new Blob([body], { type }),
    url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csv(rows, keys) {
  const cell = (v) =>
    '"' +
    String(
      typeof v === "string" && /^[=+@\-\t\r]/.test(v) ? "'" + v : (v ?? ""),
    ).replace(/"/g, '""') +
    '"';
  return (
    "\ufeff" +
    [
      keys.map(cell).join(","),
      ...rows.map((r) => keys.map((k) => cell(r[k])).join(",")),
    ].join("\r\n")
  );
}
function sourceLink(url, label) {
  try {
    const u = new URL(url);
    if (u.protocol !== "https:" || u.username || u.password) throw Error();
    return (
      '<a href="' +
      esc(u.href) +
      '" target="_blank" rel="noopener noreferrer">' +
      esc(label) +
      " ↗</a>"
    );
  } catch {
    return esc(label) + " (no usable evidence URL)";
  }
}
function currentHistory(key) {
  return model.history(
    events.filter(
      (e) => e.dataset_id === index.dataset_id && e.buyer_key === key,
    ),
  );
}
function statusFor(key) {
  return statuses.get(key) || "open";
}
function queueFlags(row) {
  return row.flags.map((code) => index.rules.find((r) => r.code === code));
}
function renderQueue() {
  if (!index) return;
  const q = $("queue-search").value.toLowerCase(),
    minimum = Number($("queue-materiality").value),
    support = $("queue-support").value,
    status = $("queue-status").value;
  filtered = index.buyers.filter(
    (r) =>
      (r.buyer_name + " " + r.buyer_key).toLowerCase().includes(q) &&
      r.total_value >= minimum &&
      (support === "all" || r.supported === (support === "supported")) &&
      (status === "all" || statusFor(r.buyer_key) === status),
  );
  $("queue-count").textContent =
    num(filtered.length) +
    " matching profiles · first 200 shown · CSV includes all matches";
  grid(
    "queue-table",
    [
      "Exact buyer identity",
      "Priority points",
      "Reasons for follow-up",
      "Eligible value",
      "Coverage / registration",
      "Review",
    ],
    filtered.slice(0, 200).map(
      (r) =>
        '<tr><td><a href="workspace.html?buyer=' +
        r.buyer_key +
        '">' +
        esc(r.buyer_name) +
        '</a><small class="buyer-id">' +
        esc(r.buyer_key) +
        '</small><span class="tag ' +
        (r.supported ? "" : "warn") +
        '">' +
        (r.supported ? "Supported" : "Limited coverage") +
        "</span></td>" +
        td(r.priority_points + "/100") +
        "<td>" +
        queueFlags(r)
          .map((f) => esc(f.rule) + " (" + f.points + ")")
          .join("<br>") +
        "</td>" +
        td(money(r.total_value)) +
        td(pct(r.value_coverage) + " / " + pct(r.registered_value_share)) +
        td(labels[statusFor(r.buyer_key)] || "History needs attention") +
        "</tr>",
    ),
  );
}
function renderAwards() {
  if (!profile) return;
  const q = $("profile-award-search").value.toLowerCase();
  const rows = profile.awards.filter((a) =>
    (a.title + " " + a.award_key + " " + (a.supplier_name || ""))
      .toLowerCase()
      .includes(q),
  );
  $("profile-award-count").textContent =
    num(rows.length) +
    " matching eligible awards · showing " +
    Math.min(shownAwards, rows.length) +
    " · download includes all " +
    profile.awards.length;
  grid(
    "profile-awards",
    [
      "Award / original notice",
      "Recorded amount",
      "Date",
      "Attribution",
      "Supplier / evidence",
    ],
    rows
      .slice(0, shownAwards)
      .map(
        (a) =>
          "<tr><td>" +
          sourceLink(a.source_url, a.title) +
          '<small class="buyer-id">' +
          esc(a.award_key) +
          "</small></td>" +
          td(money(a.amount)) +
          td(a.award_date) +
          td(a.attributed ? "Included" : "Not attributed") +
          td(
            a.attributed
              ? a.supplier_name + " / " + a.identity_basis
              : a.notice_review_block
                ? "Notice holdback"
                : a.supplier_count !== 1
                  ? "Joint or missing supplier"
                  : "Identity evidence unresolved",
          ) +
          "</tr>",
      ),
  );
  $("more-awards").hidden = rows.length <= shownAwards;
}
function renderSuppliers() {
  grid(
    "supplier-shares",
    [
      "Published supplier",
      "Identity evidence",
      "Attributable value",
      "Awards",
      "Share",
    ],
    profile.suppliers
      .slice(0, shownSuppliers)
      .map(
        (s) =>
          "<tr><td>" +
          esc(s.supplier_name) +
          '<small class="buyer-id">' +
          esc(s.supplier_key) +
          "</small></td>" +
          td(s.identity_basis) +
          td(money(s.award_value)) +
          td(num(s.awards)) +
          "<td>" +
          pct(s.share) +
          '<div class="share-bar"><span style="width:' +
          Math.max(0, Math.min(100, 100 * s.share)) +
          '%"></span></div></td></tr>',
      ),
  );
  $("more-suppliers").hidden = profile.suppliers.length <= shownSuppliers;
}
function renderProfile() {
  const r = profile.summary;
  document.title = r.buyer_name + " | SpendScope investigation";
  $("buyer-name").textContent = r.buyer_name;
  $("buyer-key").textContent =
    "Publication ID: " +
    r.buyer_key +
    " · " +
    (r.supported ? "Supported comparison" : "Limited-coverage comparison") +
    " · Data/rule version " +
    index.dataset_id.slice(0, 12);
  $("buyer-kpis").innerHTML = [
    [
      "Eligible commitments",
      money(r.total_value),
      num(r.total_awards) + " award records",
    ],
    [
      "Attributable commitments",
      money(r.attributed_value),
      pct(r.value_coverage) + " of eligible value",
    ],
    ["Supplier concentration", num(r.hhi), "HHI within attributable subset"],
    [
      "Registration evidence",
      pct(r.registered_value_share),
      num(r.registered_awards) + " attributable awards",
    ],
  ]
    .map(
      ([label, value, note]) =>
        '<article class="kpi"><span>' +
        esc(label) +
        "</span><strong>" +
        esc(value) +
        "</strong><small>" +
        esc(note) +
        "</small></article>",
    )
    .join("");
  $("buyer-flags").innerHTML =
    '<p><span class="points">' +
    r.priority_points +
    "/100 review-priority points</span></p>" +
    r.flags
      .map(
        (f) =>
          '<div class="flag"><strong>' +
          esc(f.code.replaceAll("_", " ")) +
          " · " +
          f.points +
          " points</strong><p>" +
          esc(f.rule) +
          "</p></div>",
      )
      .join("") +
    (r.flags.length
      ? ""
      : "<p>No configured flags. This is not a clean bill of health.</p>");
  const s = profile.statistics;
  $("buyer-sensitivity").innerHTML =
    "<p>Observed HHI: <strong>" +
    num(r.hhi) +
    "</strong>. Without the single largest attributed award: <strong>" +
    (r.hhi_without_largest === null
      ? "No residual portfolio"
      : num(r.hhi_without_largest)) +
    "</strong>.</p><p>Removing one commitment is a descriptive sensitivity check, not a prediction or savings estimate.</p>" +
    (s
      ? "<p>R process-bootstrap interval: <strong>" +
        num(s.hhi_low) +
        "–" +
        num(s.hhi_high) +
        "</strong> (" +
        s.processes +
        " processes, " +
        s.awards +
        " awards). Quarter alternative: " +
        (s.quarter_bootstrap_low === null
          ? "Not supported by enough quarters"
          : num(s.quarter_bootstrap_low) +
            "–" +
            num(s.quarter_bootstrap_high)) +
        ".</p>"
      : "<p>R bootstrap intervals were not calculated for this identity. They cover only the 30 researched supported buyers; no interval is inferred here.</p>");
  renderSuppliers();
  renderAwards();
  renderReview();
}
function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("spendscope-investigation-reviews", 1);
    req.onupgradeneeded = () =>
      req.result.createObjectStore("events", { keyPath: "event_id" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () =>
      reject(
        Error("Browser review storage is unavailable. Analytics still works."),
      );
    req.onblocked = () =>
      reject(
        Error("Close another SpendScope tab to finish opening review storage."),
      );
  });
}
function readEvents() {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("events", "readonly"),
      req = tx.objectStore("events").getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(Error("Could not read the review archive."));
  });
}
function atomicChange(make) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("events", "readwrite"),
      store = tx.objectStore("events"),
      req = store.getAll();
    let result, error;
    req.onsuccess = () => {
      try {
        result = make(req.result);
        for (const e of result) store.put(e);
      } catch (e) {
        error = e;
        tx.abort();
      }
    };
    tx.oncomplete = () => resolve(result);
    tx.onerror = () =>
      reject(error || Error("Review storage failed; no decision was saved."));
    tx.onabort = () =>
      reject(
        error || Error("Review update cancelled; previous history retained."),
      );
  });
}
function showStorageError(error) {
  $("archive-message").textContent = error.message;
  if (profile) $("review-message").textContent = error.message;
}
async function refreshReviews() {
  if (!db) return;
  events = await readEvents();
  const current = events.filter((e) => e.dataset_id === index.dataset_id);
  statuses = new Map();
  const groups = new Map();
  for (const event of current) {
    if (!groups.has(event.buyer_key)) groups.set(event.buyer_key, []);
    groups.get(event.buyer_key).push(event);
  }
  for (const [key, rows] of groups) {
    try {
      const h = model.history(rows);
      statuses.set(key, h[h.length - 1].status);
    } catch {
      statuses.set(key, "invalid");
    }
  }
  $("archive-status").textContent =
    current.length +
    " entries for this data/rule version; " +
    (events.length - current.length) +
    " archived entries from other versions. Export includes both.";
  renderQueue();
  if (profile) renderReview();
}
function renderReview() {
  const ready = !!db;
  $("save-review").disabled = !ready;
  let h;
  try {
    h = currentHistory(profile.summary.buyer_key);
  } catch (error) {
    $("review-state").textContent = error.message;
    $("save-review").disabled = true;
    return;
  }
  const last = h.length ? h[h.length - 1] : null,
    state = last ? last.status : "open";
  loadedLast = last ? last.event_id : null;
  $("review-state").textContent =
    "Current status: " +
    labels[state] +
    ". " +
    (ready
      ? "Entries append to the decision history."
      : "Storage unavailable: review saving is disabled.");
  const next =
    state === "open" ? ["in_review"] : [state, ...model.transitions[state]];
  $("review-next").innerHTML = next
    .map((s) => '<option value="' + s + '">' + labels[s] + "</option>")
    .join("");
  $("review-history").innerHTML = h.length
    ? "<h4>Decision history</h4>" +
      h
        .map(
          (e) =>
            '<article class="history-entry"><strong>' +
            esc(labels[e.status]) +
            "</strong><small> · " +
            esc(e.reviewer) +
            " · " +
            esc(e.created_at) +
            "</small><p>" +
            esc(e.note) +
            "</p>" +
            (e.evidence_url
              ? "<p>" + sourceLink(e.evidence_url, "Recorded evidence") + "</p>"
              : "") +
            (e.questions ? "<p>Unresolved: " + esc(e.questions) + "</p>" : "") +
            "</article>",
        )
        .join("")
    : "<p>No decisions recorded. The queue does not imply a completed review.</p>";
}
for (const id of [
  "queue-search",
  "queue-materiality",
  "queue-support",
  "queue-status",
])
  $(id).addEventListener("input", renderQueue);
$("profile-award-search").addEventListener("input", () => {
  shownAwards = 20;
  renderAwards();
});
$("more-awards").addEventListener("click", () => {
  shownAwards += 20;
  renderAwards();
});
$("more-suppliers").addEventListener("click", () => {
  shownSuppliers += 20;
  renderSuppliers();
});
$("export-queue").addEventListener("click", () =>
  download(
    "spendscope-investigation-queue.csv",
    csv(
      filtered.map((r) => ({
        ...r,
        flags: r.flags.join(";"),
        review_status: statusFor(r.buyer_key),
      })),
      [
        "buyer_key",
        "buyer_name",
        "priority_points",
        "flags",
        "total_value",
        "attributed_value",
        "value_coverage",
        "registered_value_share",
        "hhi",
        "hhi_without_largest",
        "supported",
        "review_status",
      ],
    ),
    "text/csv;charset=utf-8",
  ),
);
$("export-profile").addEventListener("click", () =>
  download(
    "spendscope-case-" + profile.summary.buyer_key + ".json",
    JSON.stringify(
      {
        schema_version: 1,
        dataset_id: index.dataset_id,
        ...profile,
        review_history: currentHistory(profile.summary.buyer_key),
      },
      null,
      2,
    ),
  ),
);
$("export-awards").addEventListener("click", () =>
  download(
    "spendscope-awards-" + profile.summary.buyer_key + ".csv",
    csv(profile.awards, [
      "award_key",
      "ocid",
      "title",
      "award_date",
      "amount",
      "supplier_count",
      "attributed",
      "supplier_key",
      "supplier_name",
      "identity_basis",
      "notice_review_status",
      "source_url",
    ]),
    "text/csv;charset=utf-8",
  ),
);
$("review-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!db) return;
  $("save-review").disabled = true;
  try {
    const expected = loadedLast;
    const next = model.validateEvent({
      event_id: crypto.randomUUID(),
      dataset_id: index.dataset_id,
      buyer_key: profile.summary.buyer_key,
      previous_event_id: expected,
      status: $("review-next").value,
      reviewer: $("reviewer").value,
      note: $("review-note").value,
      evidence_url: $("review-evidence").value,
      questions: $("review-questions").value,
      created_at: new Date().toISOString(),
    });
    events = await atomicChange((existing) => {
      const history = model.history(
        existing.filter(
          (r) =>
            r.dataset_id === index.dataset_id && r.buyer_key === next.buyer_key,
        ),
      );
      if (
        (history.length ? history[history.length - 1].event_id : null) !==
        expected
      )
        throw Error(
          "Another tab changed this case. Your text is retained; inspect the refreshed history before saving.",
        );
      return model.merge(existing, [next]);
    });
    $("review-note").value = "";
    $("review-questions").value = "";
    $("review-message").textContent =
      "Review entry saved on this device. Export a backup to retain it elsewhere.";
    channel?.postMessage("changed");
    await refreshReviews();
  } catch (error) {
    showStorageError(error);
    await refreshReviews();
  } finally {
    $("save-review").disabled = !db;
  }
});
$("export-reviews").addEventListener("click", async () => {
  try {
    if (!db) throw Error("Review storage is unavailable.");
    const all = await readEvents();
    download(
      "spendscope-review-archive.json",
      JSON.stringify(
        {
          schema_version: 1,
          exported_at: new Date().toISOString(),
          events: all,
        },
        null,
        2,
      ),
    );
    $("archive-message").textContent =
      "Archive exported. It contains your review text; share it deliberately.";
  } catch (error) {
    showStorageError(error);
  }
});
$("import-reviews").addEventListener("change", async (e) => {
  try {
    if (!db) throw Error("Review storage is unavailable.");
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 10_000_000) throw Error("Archive exceeds 10 MB limit.");
    const bundle = JSON.parse(await file.text());
    if (bundle.schema_version !== 1 || !Array.isArray(bundle.events))
      throw Error("Unsupported review archive.");
    const buyers = new Set(index.buyers.map((r) => r.buyer_key));
    for (const event of bundle.events) {
      model.validateEvent(event);
      if (event.dataset_id === index.dataset_id && !buyers.has(event.buyer_key))
        throw Error("Archive references an unknown buyer in this version.");
    }
    events = await atomicChange((existing) =>
      model.merge(existing, bundle.events),
    );
    await refreshReviews();
    channel?.postMessage("changed");
    $("archive-message").textContent =
      "Archive restored without replacing existing history. Older data versions remain separate.";
  } catch (error) {
    showStorageError(error);
  } finally {
    e.target.value = "";
  }
});
(async () => {
  try {
    const response = await fetch("workspace/index.json", { cache: "no-store" });
    if (!response.ok) throw Error("Investigation index could not load.");
    index = await response.json();
    if (
      index.schema_version !== 1 ||
      !/^[a-f0-9]{64}$/.test(index.dataset_id) ||
      !Array.isArray(index.buyers)
    )
      throw Error(
        "Unsupported investigation data version. Reload the current workspace.",
      );
    $("load-status").textContent =
      num(index.profile_count) +
      " exact buyer profiles · historical 2022–2024 snapshots · sources retrieved " +
      index.source_retrieved;
    $("queue-rules").innerHTML = index.rules
      .map(
        (r) =>
          '<p><span class="points">' +
          r.points +
          " points</span> " +
          esc(r.rule) +
          "</p>",
      )
      .join("");
    $("profile-scope").textContent =
      index.scope +
      " " +
      num(index.excluded_zero_attribution_buyers) +
      " eligible buyer identities with zero attributable awards are excluded from concentration profiles.";
    openDb()
      .then((connection) => {
        db = connection;
        return refreshReviews();
      })
      .catch((error) => {
        $("archive-status").textContent = error.message;
      });
    renderQueue();
    const key = new URLSearchParams(location.search).get("buyer");
    if (key !== null) {
      if (
        !/^[a-f0-9]{24}$/.test(key) ||
        !index.buyers.some((r) => r.buyer_key === key)
      )
        throw Error(
          "Unknown buyer identity. Return to workspace.html and select a profile.",
        );
      const response = await fetch(
        "workspace/" + key.slice(0, 2) + ".json?v=" + index.dataset_id,
        { cache: "no-store" },
      );
      if (!response.ok) throw Error("Buyer evidence could not load.");
      const shard = await response.json();
      if (
        shard.dataset_id !== index.dataset_id ||
        !shard.profiles[key] ||
        shard.profiles[key].summary.buyer_key !== key
      )
        throw Error(
          "Buyer evidence version mismatch. Reload the page before reviewing.",
        );
      profile = shard.profiles[key];
      $("queue-view").hidden = true;
      $("buyer-view").hidden = false;
      renderProfile();
    }
  } catch (error) {
    $("load-status").textContent = error.message;
  }
})();
