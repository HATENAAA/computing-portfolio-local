import { programIds } from "./catalog.js";
import { calibrationSchema } from "./spatial.js";
import { replaySchema } from "./replay.js";
import { z } from "zod";
import { drillSchema } from "./drills.js";
import { TrainingSession } from "./session.js";
const program = z.enum(programIds);
const mode = z.enum(["desktop", "vr"]);
const pending = z
  .object({
    calibration: calibrationSchema.optional(),
    recommendationId: z.string().uuid().optional(),
    interaction: drillSchema.optional(),
    replay: replaySchema.optional(),
    id: z.string().uuid(),
    program,
    mode,
    startedAt: z.string().datetime(),
    activeSeconds: z.number().int().min(1).max(3600),
    hits: z.number().int().min(0).max(10000),
  })
  .strict();
const schema = z
  .object({
    version: z.literal(1),
    savedAt: z.number().finite(),
    draft: z
      .object({
        program,
        mode,
        compact: z.boolean().optional(),
        calibration: calibrationSchema.optional(),
    recommendationId: z.string().uuid().optional(),
    interaction: drillSchema.optional(),
    replay: replaySchema.optional(),
        session: z
          .object({
            durationSeconds: z.number().int().min(1).max(3600),
            elapsedMs: z.number().finite().min(0),
            hits: z.number().int().min(0).max(10000),
            startedAt: z.string().datetime(),
          })
          .strict(),
      })
      .strict()
      .nullable(),
    pending: pending.nullable(),
  })
  .strict()
  .refine((v) => !(v.draft && v.pending));

export class RecoveryStore {
  constructor(storage, now = Date.now) {
    this.storage = storage;
    this.now = now;
    this.key = "vrfitai.recovery.v1";
  }
  write({ draft = null, pending = null }) {
    if (!draft && !pending) return this.storage.removeItem(this.key);
    const value = schema.parse({
      version: 1,
      savedAt: this.now(),
      draft,
      pending,
    });
    if (draft) new TrainingSession().restore(draft.session);
    this.storage.setItem(this.key, JSON.stringify(value));
  }
  read() {
    let raw;
    try {
      raw = this.storage.getItem(this.key);
      if (!raw) return { value: null, error: "" };
      const value = schema.parse(JSON.parse(raw));
      if (
        value.savedAt > this.now() + 60000 ||
        this.now() - value.savedAt > 86400000
      )
        throw new Error("Checkpoint expired");
      if (value.draft) new TrainingSession().restore(value.draft.session);
      return { value, error: "" };
    } catch {
      try {
        this.storage.removeItem(this.key);
      } catch {
        /* read-only storage */
      }
      return {
        value: null,
        error: raw
          ? "上次训练记录已过期或无法读取。"
          : "浏览器未允许临时保存，刷新前请先结束并保存训练。",
      };
    }
  }
}
