import { z } from "zod";
import { programIds } from "./catalog.js";

const rhythmOrder = [0, 1, 0, 1, 2, 1, 0, 3];
export function rhythmTarget(step) {
  return rhythmOrder[step % rhythmOrder.length];
}
export const difficulties = [
  { id: "easy", label: "舒适", window: 3600, hold: 1500 },
  { id: "medium", label: "标准", window: 2500, hold: 1200 },
  { id: "hard", label: "挑战", window: 1700, hold: 900 },
];
const recallSettings = {
  easy: { count: 3, displayMs: 1000, recallMs: 10000 },
  medium: { count: 4, displayMs: 850, recallMs: 9000 },
  hard: { count: 5, displayMs: 700, recallMs: 8000 },
};
const readyMs = 480;
const cueGapMs = 140;
const targetIndex = z.number().int().min(0).max(4);
function recallStart(cue, settings) {
  return cue.start + readyMs + settings.count * settings.displayMs;
}

export const drillSchema = z
  .object({
    version: z.literal(1),
    program: z.enum(programIds),
    difficulty: z.enum(["easy", "medium", "hard"]),
    interval: z.boolean().optional(),
    elapsed: z.number().finite().min(0).max(7200000),
    seed: z.number().int().min(0).max(4294967295),
    serial: z.number().int().min(0).max(20000),
    hits: z.number().int().min(0).max(10000),
    mistakes: z.number().int().min(0).max(10000),
    missed: z.number().int().min(0).max(10000),
    avoided: z.number().int().min(0).max(10000),
    streak: z.number().int().min(0).max(10000),
    bestStreak: z.number().int().min(0).max(10000),
    responses: z.array(z.number().finite().min(0).max(10000)).max(500),
    cue: z
      .object({
        index: targetIndex,
        start: z.number().finite().min(0),
        end: z.number().finite().min(0),
        avoid: z.boolean(),
        hold: z.number().finite().min(0).max(2000),
        recall: z.object({
          order: z.array(targetIndex).min(3).max(5),
          step: z.number().int().min(0).max(4),
          lastAt: z.number().finite().min(0),
        }).strict().optional(),
      })
      .strict()
      .nullable(),
  })
  .strict()
  .superRefine((s, ctx) => {
    if (
      s.cue &&
      (s.cue.start > s.elapsed ||
        s.cue.end <= s.elapsed ||
        s.cue.end <= s.cue.start)
    )
      ctx.addIssue({ code: "custom", message: "Invalid cue clock" });
    const recall = s.cue?.recall;
    const settings = recallSettings[s.difficulty];
    const sequence = s.program === "sequence";
    if (sequence !== Boolean(recall) || recall && (
      recall.order.length !== settings.count ||
      new Set(recall.order).size !== settings.count ||
      s.cue.index !== recall.order[recall.step] ||
      s.cue.avoid || s.cue.hold !== 0 ||
      s.cue.end !== recallStart(s.cue, settings) + settings.recallMs ||
      recall.lastAt < recallStart(s.cue, settings) ||
      (recall.step === 0 && recall.lastAt !== recallStart(s.cue, settings)) ||
      (recall.step > 0 && recall.lastAt > s.elapsed)
    )) ctx.addIssue({ code: "custom", message: "Invalid recall state" });
    if (
      s.streak > s.bestStreak ||
      s.responses.length > s.hits ||
      s.hits + s.missed + s.avoided > s.serial * (sequence ? settings.count : 1)
    )
      ctx.addIssue({ code: "custom", message: "Invalid interaction counters" });
  });

// Effective training time comes from the session, never the wall clock.
export class Drill {
  constructor(program = "rhythm", difficulty = "easy", seed = 7319) {
    if (
      !programIds.includes(program) ||
      !difficulties.some((d) => d.id === difficulty)
    )
      throw new TypeError("Unknown drill");
    this.data = {
      version: 1,
      program,
      difficulty,
      elapsed: 0,
      seed: seed >>> 0,
      serial: 0,
      hits: 0,
      mistakes: 0,
      missed: 0,
      avoided: 0,
      streak: 0,
      bestStreak: 0,
      responses: [],
      cue: null,
    };
    this.spawn(0);
  }
  get settings() {
    return difficulties.find((d) => d.id === this.data.difficulty);
  }
  get resting() {
    return (
      this.data.interval !== false &&
      this.data.program === "flow" &&
      this.data.elapsed % 25000 >= 20000
    );
  }
  random() {
    this.data.seed = (Math.imul(1664525, this.data.seed) + 1013904223) >>> 0;
    return this.data.seed / 4294967296;
  }
  spawn(at) {
    const d = this.data;
    if (d.interval !== false && d.program === "flow" && at % 25000 >= 20000) {
      d.cue = null;
      return;
    }
    if (d.program === "sequence") {
      this.spawnRecall(at);
      return;
    }
    let index =
      d.program === "rhythm"
        ? rhythmTarget(d.serial)
        : Math.floor(this.random() * 5);
    if (d.program === 'focus' && index === d.cue?.index)
      index = (index + 1 + Math.floor(this.random() * 4)) % 5;
    const avoid = d.program === "flow" && d.serial % 4 === 3;
    let end =
      at +
      (d.program === "focus"
        ? this.settings.window * 2.4
        : this.settings.window);
    if (d.interval !== false && d.program === "flow")
      end = Math.min(end, at - (at % 25000) + 20000);
    d.cue = { index, start: at, end, avoid, hold: 0 };
    d.serial++;
  }
  spawnRecall(at) {
    const d = this.data;
    const settings = recallSettings[d.difficulty];
    const positions = [0, 1, 2, 3, 4];
    const order = [];
    for (let i = 0; i < settings.count; i++) {
      const offset = Math.floor(this.random() * positions.length);
      order.push(positions.splice(offset, 1)[0]);
    }
    const cue = {index: order[0], start: at, end: 0, avoid: false, hold: 0};
    const start = recallStart(cue, settings);
    cue.end = start + settings.recallMs;
    cue.recall = {order, step: 0, lastAt: start};
    d.cue = cue;
    d.serial++;
  }
  recallView() {
    const { cue, elapsed, difficulty } = this.data;
    const data = cue?.recall;
    if (!data) return null;
    const settings = recallSettings[difficulty];
    const showTime = elapsed - cue.start - readyMs;
    const until = recallStart(cue, settings);
    if (showTime < 0)
      return {phase: "ready", index: null, step: -1, count: settings.count, progress: 1 + showTime / readyMs};
    if (elapsed >= until)
      return {phase: "recall", index: null, step: data.step, count: settings.count, progress: (cue.end - elapsed) / settings.recallMs};
    const step = Math.floor(showTime / settings.displayMs);
    const within = showTime % settings.displayMs;
    return {phase: "watch", index: within < settings.displayMs - cueGapMs ? data.order[step] : null, step, count: settings.count, progress: within / settings.displayMs};
  }
  advance(to, hover = -1, active = true) {
    if (!active) return this.view();
    const d = this.data;
    if (!Number.isFinite(to) || to < d.elapsed || to > 7200000)
      return this.view();
    while (d.cue && to >= d.cue.end) {
      const end = d.cue.end;
      if (d.cue.avoid) d.avoided++;
      else {
        d.missed += d.cue.recall ? d.cue.recall.order.length - d.cue.recall.step : 1;
        d.streak = 0;
      }
      d.elapsed = end;
      this.spawn(end);
    }
    if (
      !d.cue &&
      d.interval !== false &&
      d.program === "flow" &&
      Math.floor(to / 25000) > Math.floor(d.elapsed / 25000)
    ) {
      this.spawn(Math.floor(to / 25000) * 25000);
      if (d.cue && to >= d.cue.end) return this.advance(to, -1, true);
    }
    const delta = to - d.elapsed;
    d.elapsed = to;
    if (d.program === "focus" && d.cue) {
      d.cue.hold =
        hover === d.cue.index && delta <= 300 ? d.cue.hold + delta : 0;
      if (d.cue.hold >= this.settings.hold) this.success();
    }
    return this.view();
  }
  recordHit(since) {
    const d = this.data;
    d.hits++;
    d.streak++;
    d.bestStreak = Math.max(d.bestStreak, d.streak);
    if (d.responses.length < 500)
      d.responses.push(Math.min(10000, Math.round(d.elapsed - since)));
  }
  success() {
    this.recordHit(this.data.cue.start);
    this.spawn(this.data.elapsed);
  }
  recallInput(index) {
    const d = this.data, cue = d.cue, data = cue.recall;
    if (d.elapsed < recallStart(cue, recallSettings[d.difficulty])) return false;
    if (index !== cue.index) {
      d.mistakes++;
      d.streak = 0;
      return false;
    }
    this.recordHit(data.lastAt);
    data.step++;
    if (data.step === data.order.length) this.spawn(d.elapsed);
    else {
      cue.index = data.order[data.step];
      data.lastAt = d.elapsed;
    }
    return true;
  }
  input(index, hand = "") {
    const d = this.data,
      c = d.cue;
    if (!c || this.resting || d.program === "focus") return false;
    if (c.recall) return this.recallInput(index);
    const correctHand =
      !hand || hand === (c.index % 2 === 0 ? "left" : "right");
    if (
      index !== c.index ||
      c.avoid ||
      (d.program === "rhythm" && !correctHand)
    ) {
      d.mistakes++;
      d.streak = 0;
      if (c.avoid) this.spawn(d.elapsed);
      return false;
    }
    this.success();
    return true;
  }
  view() {
    const d = this.data,
      resolved = d.hits + d.missed + d.avoided;
    const responses = [...d.responses].sort((a, b) => a - b),
      n = responses.length;
    return {
      ...structuredClone(d),
      resting: this.resting,
      ...(d.program === "sequence" ? { recall: this.recallView() } : {}),
      holdProgress: d.cue ? Math.min(1, d.cue.hold / this.settings.hold) : 0,
      accuracy:
        resolved + d.mistakes
          ? Math.round((100 * (d.hits + d.avoided)) / (resolved + d.mistakes))
          : null,
      reactionMs: n
        ? Math.round(
            n % 2
              ? responses[(n - 1) / 2]
              : (responses[n / 2 - 1] + responses[n / 2]) / 2,
          )
        : null,
      score: d.hits * 100 + d.avoided * 50,
    };
  }
  snapshot() {
    return structuredClone(this.data);
  }
  static restore(value) {
    const d = drillSchema.parse(value);
    const engine = new Drill(d.program, d.difficulty);
    engine.data = structuredClone(d);
    return engine;
  }
}

export function trainingWorkMs(program, elapsed, interval = true) {
  if (!Number.isFinite(elapsed) || elapsed < 0)
    throw new RangeError("Invalid training clock");
  return program === "flow" && interval
    ? Math.floor(elapsed / 25000) * 20000 + Math.min(20000, elapsed % 25000)
    : elapsed;
}
