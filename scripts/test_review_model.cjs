"use strict";
const { test } = require("node:test"),
  assert = require("node:assert/strict");
const model = require("../src/spendscope/web/review-model.js");
const id = (n) => "00000000-0000-4000-8000-" + String(n).padStart(12, "0");
const event = (n, previous = null, status = "in_review") => ({
  event_id: id(n),
  dataset_id: "a".repeat(64),
  buyer_key: "b".repeat(24),
  previous_event_id: previous,
  status,
  reviewer: "ML",
  note: "Inspected the original award notice.",
  evidence_url: "https://example.test/notice",
  questions: "",
  created_at: "2026-11-13T00:00:00.000Z",
});
test("history follows parent links rather than import order or clock", () => {
  const a = event(1),
    b = event(2, id(1), "awaiting_evidence"),
    c = event(3, id(2));
  assert.deepEqual(
    model.history([c, a, b]).map((e) => e.event_id),
    [id(1), id(2), id(3)],
  );
});
test("cannot close an untouched case or skip evidence", () => {
  assert.throws(() => model.history([event(1, null, "closed")]));
  const a = event(1),
    b = event(2, id(1), "closed");
  assert.equal(model.history([a, b]).length, 2);
  assert.throws(() => model.validateEvent({ ...b, evidence_url: "" }));
  assert.throws(() =>
    model.validateEvent({ ...b, questions: "Identity still unresolved" }),
  );
});
test("reopen preserves prior decision rather than replacing it", () => {
  const a = event(1),
    b = event(2, id(1), "closed"),
    c = event(3, id(2));
  assert.equal(model.merge([a, b], [c]).length, 3);
});
test("restore is idempotent and refuses edits to known entries", () => {
  const a = event(1);
  assert.equal(model.merge([a], [a]).length, 1);
  assert.throws(() =>
    model.merge(
      [a],
      [{ ...a, note: "An altered account of what was inspected." }],
    ),
  );
});
test("competing branches, missing parents and cycles are rejected", () => {
  const a = event(1);
  assert.throws(() => model.merge([a], [event(2, id(1)), event(3, id(1))]));
  assert.throws(() => model.history([event(2, id(1))]));
  assert.throws(() => model.history([event(1, id(2)), event(2, id(1))]));
});
test("dataset histories remain separate and incompatible cases cannot share a chain", () => {
  const a = event(1),
    b = { ...event(2), dataset_id: "c".repeat(64) };
  assert.equal(model.merge([a], [b]).length, 2);
  assert.throws(() =>
    model.history([a, { ...event(2, id(1)), buyer_key: "d".repeat(24) }]),
  );
});
test("unsafe URLs, missing actors, oversized notes and unexpected fields are rejected", () => {
  for (const patch of [
    { evidence_url: "javascript:alert(1)" },
    { evidence_url: "https://user:secret@example.test" },
    { reviewer: "" },
    { note: "x".repeat(4001) },
    { is_independently_verified: true },
  ])
    assert.throws(() => model.validateEvent({ ...event(1), ...patch }));
});
test("archive must be bounded and an array", () => {
  assert.throws(() => model.merge([], {}));
  assert.throws(() => model.merge([], Array(20001).fill(event(1))));
});
