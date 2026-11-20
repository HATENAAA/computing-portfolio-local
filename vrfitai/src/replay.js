import { z } from "zod";
import { Drill, drillSchema } from "./drills.js";
import { programIds } from "./catalog.js";
// Event order is explicit. Times use the effective training clock, excluding pauses.
const seq = z.number().int().min(0).max(11999);
export const replaySchema = z
  .object({
    version: z.literal(1),
    engine: z.literal("drill-1"),
    program: z.enum(programIds),
    difficulty: z.enum(["easy", "medium", "hard"]),
    interval: z.boolean(),
    seed: z.number().int().min(0).max(4294967295),
    complete: z.boolean(),
    events: z
      .array(
        z.union([
          z.tuple([
            seq,
            z.literal("t"),
            z.number().finite().min(0).max(3600000),
            z.number().int().min(-1).max(4),
          ]),
          z.tuple([
            seq,
            z.literal("i"),
            z.number().int().min(0).max(4),
            z.enum(["", "left", "right"]),
          ]),
        ]),
      )
      .max(12000),
  })
  .strict();
function canonical(v) {
  if (Array.isArray(v)) return v.map(canonical);
  if (v && typeof v === "object")
    return Object.fromEntries(
      Object.keys(v)
        .sort()
        .map((k) => [k, canonical(v[k])]),
    );
  return v;
}
function equal(a, b) {
  return JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
}
function newEngine(r) {
  const d = new Drill(r.program, r.difficulty, r.seed);
  d.data.interval = r.interval;
  return d;
}
export function replayEvents(value) {
  const r = replaySchema.parse(value),
    d = newEngine(r);
  for (let n = 0; n < r.events.length; n++) {
    const [s, kind, a, b] = r.events[n];
    if (s !== n) throw new Error("Event sequence is invalid");
    if (kind === "t") {
      if (a < d.data.elapsed) throw new Error("Training clock moved backwards");
      d.advance(a, b, true);
    } else d.input(a, b);
  }
  return { replay: r, drill: d };
}
export function verifyReplay(value, checkpoint) {
  const { replay, drill } = replayEvents(value),
    state = drillSchema.parse(checkpoint);
  if (
    replay.program !== state.program ||
    replay.difficulty !== state.difficulty ||
    replay.interval !== (state.interval !== false)
  )
    throw new Error("Replay configuration differs");
  const same = equal(drill.snapshot(), state);
  if (replay.complete && !same)
    throw new Error("Replay does not match the saved interaction state");
  return {
    status: replay.complete ? "verified" : "incomplete",
    events: replay.events.length,
    engine: replay.engine,
    metrics: replay.complete ? drill.view() : null,
    scope:
      "Deterministic consistency check; does not authenticate physical activity or user identity",
  };
}
// Index once, then seek by replaying at most stride-1 events from an immutable snapshot.
export class ReplayIndex {
  #replay; #checkpoints; #stride;
  constructor(value, stride = 256) {
    if (!Number.isInteger(stride) || stride < 1 || stride > 1024)
      throw new Error("Invalid checkpoint stride");
    this.#replay = structuredClone(replaySchema.parse(value));
    this.#stride = stride;
    this.#checkpoints = new Map();
    const d = newEngine(this.#replay);
    this.#checkpoints.set(0, d.snapshot());
    for (let i = 0; i < this.#replay.events.length; i++) {
      this.#apply(d, i);
      if ((i + 1) % stride === 0) this.#checkpoints.set(i + 1, d.snapshot());
    }
  }
  #apply(d, i) {
    const [seq, kind, a, b] = this.#replay.events[i];
    if (seq !== i) throw new Error("Event sequence is invalid");
    if (kind === "t") {
      if (a < d.data.elapsed) throw new Error("Training clock moved backwards");
      d.advance(a, b, true);
    } else d.input(a, b);
  }
  seek(cursor) {
    if (!Number.isInteger(cursor) || cursor < 0 || cursor > this.#replay.events.length)
      throw new Error("Cursor is outside the replay");
    const start = Math.floor(cursor / this.#stride) * this.#stride;
    const d = Drill.restore(structuredClone(this.#checkpoints.get(start)));
    for (let i = start; i < cursor; i++) this.#apply(d, i);
    return {drill: d, replayedEvents: cursor - start, checkpoint: start};
  }
}
export class RecordedDrill {
  constructor(program = "rhythm", difficulty = "easy", interval = true) {
    this.log = {
      version: 1,
      engine: "drill-1",
      program,
      difficulty,
      interval,
      seed: program === "sequence" ? globalThis.crypto.getRandomValues(new Uint32Array(1))[0] : 7319,
      complete: true,
      events: [],
    };
    this.drill = newEngine(this.log);
    this.lastTick = null;
  }
  get data() {
    return this.drill.data;
  }
  view() {
    return this.drill.view();
  }
  snapshot() {
    return this.drill.snapshot();
  }
  journal() {
    return structuredClone(this.log);
  }
  append(kind, a, b) {
    if (this.log.events.length >= 12000) {
      this.log.complete = false;
      return;
    }
    this.log.events.push([this.log.events.length, kind, a, b]);
  }
  advance(to, hover = -1, active = true) {
    if (
      !active ||
      !Number.isFinite(to) ||
      to < this.data.elapsed ||
      to > 3600000
    )
      return this.view();
    if (
      !this.lastTick ||
      this.lastTick[0] !== to ||
      this.lastTick[1] !== hover
    ) {
      // Recall outcomes depend on time and input order, not frame cadence or pointer movement.
      // Keep half-second samples so the replay still shows the observation phase.
      const sequence = this.data.program === "sequence";
      if (sequence && this.lastTick && this.log.complete &&
          Math.floor(to / 500) === Math.floor(this.lastTick[0] / 500)) {
        this.log.events.at(-1)[2] = to;
      } else this.append("t", to, sequence ? -1 : hover);
      this.lastTick = [to, hover];
    }
    return this.drill.advance(to, hover, true);
  }
  input(index, hand = "") {
    this.append("i", index, hand);
    this.lastTick = null;
    return this.drill.input(index, hand);
  }
  static restore(checkpoint, journal, interval = true) {
    const state = drillSchema.parse(checkpoint),
      out = new RecordedDrill(state.program, state.difficulty, interval);
    if (journal) {
      verifyReplay(journal, state);
      out.log = replaySchema.parse(journal);
      if (
        out.log.program !== state.program ||
        out.log.difficulty !== state.difficulty ||
        out.log.interval !== interval
      )
        throw new Error("Replay configuration differs");
    } else if (!equal(out.snapshot(), state)) out.log.complete = false;
    out.drill = Drill.restore(state);
    out.drill.data.interval = interval;
    return out;
  }
}
