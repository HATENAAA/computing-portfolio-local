import { test } from "node:test";
import assert from "node:assert/strict";
import { TrainingSession } from "../src/session.js";
import { RecoveryStore } from "../src/recovery.js";
const memory = () => {
  const data = new Map();
  return {
    getItem: (k) => data.get(k) ?? null,
    setItem: (k, v) => data.set(k, v),
    removeItem: (k) => data.delete(k),
  };
};
const draft = () => ({
  program: "rhythm",
  mode: "desktop",
  session: {
    durationSeconds: 60,
    elapsedMs: 7500,
    hits: 3,
    startedAt: "2026-11-01T00:00:00.000Z",
  },
});
const pending = () => ({
  id: "54c93f68-4ab1-4f74-bf1b-e6265e67bd1c",
  program: "rhythm",
  mode: "desktop",
  startedAt: "2026-11-01T00:00:00.000Z",
  activeSeconds: 8,
  hits: 3,
});
test("refresh restores elapsed time and hits in paused state without counting time away", () => {
  let time = 0;
  const a = new TrainingSession(() => time);
  a.start(60);
  time = 7500;
  a.hit();
  const b = new TrainingSession(() => time + 100000);
  b.restore(a.snapshot());
  assert.equal(b.state, "paused");
  assert.equal(b.milliseconds(), 7500);
  assert.equal(b.hits, 1);
  b.resume();
  time = 10000;
  assert.equal(b.finish().activeSeconds, 10);
});
test("invalid durations and corrupt session checkpoints are rejected", () => {
  for (const d of [0, -1, NaN, Infinity, 1.5, 3601])
    assert.throws(() => new TrainingSession().start(d));
  for (const change of [
    { elapsedMs: -1 },
    { elapsedMs: 60001 },
    { hits: -1 },
    { hits: 1.5 },
    { durationSeconds: 0 },
    { startedAt: "bad" },
  ])
    assert.throws(() =>
      new TrainingSession().restore({ ...draft().session, ...change }),
    );
});
test("draft storage survives page recreation and retains original training start", () => {
  const storage = memory(),
    a = new RecoveryStore(storage, () => 1000);
  a.write({ draft: draft() });
  const value = new RecoveryStore(storage, () => 100000).read().value;
  assert.deepEqual(value.draft, draft());
  assert.equal(value.pending, null);
});
test("unacknowledged save keeps the same UUID and payload across refresh and retry", () => {
  const storage = memory(),
    a = new RecoveryStore(storage, () => 1000);
  a.write({ pending: pending() });
  const b = new RecoveryStore(storage, () => 2000);
  assert.deepEqual(b.read().value.pending, pending());
  b.write({ pending: b.read().value.pending });
  assert.equal(b.read().value.pending.id, pending().id);
  b.write({});
  assert.equal(b.read().value, null);
});
test("malformed, expired, future and inconsistent checkpoints are discarded explicitly", () => {
  const storage = memory(),
    a = new RecoveryStore(storage, () => 1000);
  a.write({ draft: draft() });
  assert.equal(new RecoveryStore(storage, () => 86402000).read().value, null);
  assert.ok(!storage.getItem(a.key));
  storage.setItem(a.key, '{"version":999}');
  assert.ok(a.read().error);
  a.write({ draft: draft() });
  assert.equal(new RecoveryStore(storage, () => -100000).read().value, null);
  assert.throws(() => a.write({ draft: draft(), pending: pending() }));
});
test("unavailable or full browser storage produces a detectable failure", () => {
  const s = new RecoveryStore({
    getItem() {
      throw Error("blocked");
    },
    removeItem() {
      throw Error("blocked");
    },
    setItem() {
      throw Error("quota");
    },
  });
  assert.ok(s.read().error);
  assert.throws(() => s.write({ draft: draft() }));
});
test("a completed or idle engine never emits an unfinished draft", () => {
  let now = 0;
  const s = new TrainingSession(() => now);
  assert.equal(s.snapshot(), null);
  s.start(30);
  now = 3000;
  s.finish();
  assert.equal(s.snapshot(), null);
});
