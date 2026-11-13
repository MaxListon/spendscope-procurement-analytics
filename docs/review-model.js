/* Shared review validation for browser storage and regression tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.SpendScopeReview = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const transitions = {
    open: ["in_review"],
    in_review: ["awaiting_evidence", "closed"],
    awaiting_evidence: ["in_review"],
    closed: ["in_review"],
  };
  const fields = [
    "event_id",
    "dataset_id",
    "buyer_key",
    "previous_event_id",
    "status",
    "reviewer",
    "note",
    "evidence_url",
    "questions",
    "created_at",
  ];
  function text(v, max, name) {
    if (typeof v !== "string" || v.length > max) throw Error("Invalid " + name);
    return v.trim();
  }
  function validateEvent(e) {
    if (
      !e ||
      typeof e !== "object" ||
      Array.isArray(e) ||
      Object.keys(e).some((k) => !fields.includes(k))
    )
      throw Error("Unrecognized review event");
    const v = {};
    for (const k of fields) v[k] = e[k];
    if (
      !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        v.event_id,
      ) ||
      !/^[0-9a-f]{64}$/.test(v.dataset_id) ||
      !/^[0-9a-f]{24}$/.test(v.buyer_key)
    )
      throw Error("Invalid event or dataset identity");
    if (
      v.previous_event_id !== null &&
      !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        v.previous_event_id,
      )
    )
      throw Error("Invalid previous event");
    if (!Object.hasOwn(transitions, v.status))
      throw Error("Invalid review status");
    v.reviewer = text(v.reviewer, 80, "reviewer");
    v.note = text(v.note, 4000, "decision note");
    v.questions = text(v.questions, 4000, "questions");
    v.evidence_url = text(v.evidence_url, 2048, "evidence URL");
    if (!v.reviewer || v.note.length < 20)
      throw Error(
        "Provide reviewer initials and a decision note of at least 20 characters",
      );
    if (v.evidence_url) {
      let u;
      try {
        u = new URL(v.evidence_url);
      } catch {
        throw Error("Evidence must be an HTTPS URL");
      }
      if (u.protocol !== "https:" || u.username || u.password)
        throw Error("Evidence must be an HTTPS URL without credentials");
    }
    if (v.status === "closed" && (!v.evidence_url || v.questions))
      throw Error(
        "Closing requires an evidence URL and no unresolved questions. Keep unresolved cases awaiting evidence.",
      );
    if (
      typeof v.created_at !== "string" ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(v.created_at) ||
      !Number.isFinite(Date.parse(v.created_at)) ||
      new Date(v.created_at).toISOString() !== v.created_at
    )
      throw Error("Invalid observation time");
    return v;
  }
  function history(events) {
    if (!events.length) return [];
    const rows = events.map(validateEvent),
      ids = new Set(rows.map((e) => e.event_id));
    if (ids.size !== rows.length) throw Error("Duplicate event IDs");
    const cases = new Set(rows.map((e) => e.dataset_id + "|" + e.buyer_key));
    if (cases.size !== 1) throw Error("Mixed cases in history");
    const next = new Map();
    for (const e of rows) {
      if (next.has(e.previous_event_id))
        throw Error("Branched history requires reconciliation");
      next.set(e.previous_event_id, e);
    }
    const ordered = [];
    let previous = null,
      state = "open";
    while (next.has(previous)) {
      const e = next.get(previous);
      if (ordered.length >= rows.length) throw Error("Cyclic history");
      if (e.status !== state && !transitions[state].includes(e.status))
        throw Error("Invalid review transition");
      ordered.push(e);
      state = e.status;
      previous = e.event_id;
    }
    if (ordered.length !== rows.length)
      throw Error("Incomplete or cyclic history");
    return ordered;
  }
  function merge(existing, incoming) {
    if (!Array.isArray(incoming) || incoming.length > 20000)
      throw Error("Invalid or oversized review archive");
    const all = new Map();
    for (const raw of [...existing, ...incoming]) {
      const e = validateEvent(raw);
      const old = all.get(e.event_id);
      if (old && JSON.stringify(old) !== JSON.stringify(e))
        throw Error("An existing event was altered");
      all.set(e.event_id, e);
    }
    const groups = new Map();
    for (const e of all.values()) {
      const k = e.dataset_id + "|" + e.buyer_key;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(e);
    }
    for (const rows of groups.values()) history(rows);
    return [...all.values()];
  }
  return { transitions, validateEvent, history, merge };
});
