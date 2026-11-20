import express from "express";
import { installCoach } from "./coach.js";
import { calibrationSchema } from "../src/spatial.js";
import {replaySchema,verifyReplay} from "../src/replay.js";
import {drillSchema,trainingWorkMs} from "../src/drills.js";
import {installPersonal} from "./personal.js";
import { Workout } from "../src/workout.js";
import { trainingReport } from "./report.js";
import { DatabaseSync } from "node:sqlite";
import { randomUUID } from "node:crypto";
import { resolve } from "node:path";
import { z } from "zod";
import { programs, getProgram, programIds } from "../src/catalog.js";
import { answer, aiConfig } from "./assistant.js";
export function createApp({
  database = ":memory:",
  config,
  readConfig = config ? () => config : aiConfig,
  fetcher = fetch,
  logger = null,
} = {}) {
  const app = express(),
    db = new DatabaseSync(database);
  app.disable("x-powered-by");
  db.exec(
    "CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, program TEXT, started TEXT, seconds INTEGER, hits INTEGER, mode TEXT)",
  );
  db.exec(
    "PRAGMA busy_timeout=5000; CREATE INDEX IF NOT EXISTS sessions_started ON sessions(started DESC,id DESC)",
  );
  if (database !== ":memory:") db.exec("PRAGMA journal_mode=WAL");
  if(!db.prepare("PRAGMA table_info(sessions)").all().some(c=>c.name==="interaction")) db.exec("ALTER TABLE sessions ADD COLUMN interaction TEXT");
  if(!db.prepare("PRAGMA table_info(sessions)").all().some(c=>c.name==="replay"))db.exec("ALTER TABLE sessions ADD COLUMN replay TEXT");
  for(const column of ["calibration", "recommendationId"]) if(!db.prepare("PRAGMA table_info(sessions)").all().some(c=>c.name===column)) db.exec(`ALTER TABLE sessions ADD COLUMN ${column} TEXT`);
  const sessionRow=r=>{const {interaction,replay,calibration,...rest}=r;return {...rest,...(calibration?{calibration:JSON.parse(calibration)}:{}),...(interaction?{interaction:JSON.parse(interaction)}:{})};};
  app.use((req, res, next) => {
    const requestId = randomUUID(),
      start = performance.now();
    res.set("X-Request-ID", requestId);
    res.on("finish", () => {
      // Do not log questions, training summaries, query strings or credentials.
      if (logger) {
        try {
          logger({
            requestId,
            method: req.method,
            route: req.route?.path || "unmatched",
            status: res.statusCode,
            durationMs: Math.round((performance.now() - start) * 100) / 100,
          });
        } catch {
          /* Logging must not interrupt a completed request. */
        }
      }
    });
    next();
  });
  app.use((req, res, next) => {
    const origin = req.get("origin");
    if (origin) {
      try {
        const u = new URL(origin);
        if (
          !["localhost", "127.0.0.1", "[::1]"].includes(u.hostname) &&
          u.host !== req.get("host")
        )
          return res.status(403).json({ error: "来源不允许" });
      } catch {
        return res.status(403).json({ error: "来源不允许" });
      }
    }
    res.set("X-Content-Type-Options", "nosniff");
    next();
  });
  app.use("/api/sessions", express.json({limit:"512kb"}));
  app.use(express.json({ limit: "32kb" }));
  db.exec('CREATE TABLE IF NOT EXISTS workouts(id TEXT PRIMARY KEY, started TEXT, payload TEXT)');
  app.post('/api/workouts', (req,res)=>{
    try {
      const workout=Workout.restore(req.body);
      if(workout.state!=='finished' || workout.summary().workMs<1000)return res.status(400).json({error:'Only complete workouts can be saved'});
      const value=workout.snapshot(), payload=JSON.stringify(value);
      const old=db.prepare('SELECT payload FROM workouts WHERE id=?').get(value.id);
      if(old && old.payload!==payload)return res.status(409).json({error:'Workout ID conflict'});
      if(!old)db.prepare('INSERT INTO workouts VALUES(?,?,?)').run(value.id,value.startedAt,payload);
      res.status(old?200:201).json({id:value.id,summary:workout.summary()});
    }catch {res.status(400).json({error:'Invalid workout record'});}
  });
  app.get('/api/workouts',(req,res)=>res.json(db.prepare('SELECT payload FROM workouts ORDER BY started DESC,id DESC LIMIT 100').all().map(r=>{
    const value=JSON.parse(r.payload);return {...value,summary:Workout.restore(value).summary()};
  })));
  app.get('/api/workouts/:id/report',(req,res)=>{
    const row=db.prepare('SELECT payload FROM workouts WHERE id=?').get(req.params.id);
    if(!row)return res.status(404).json({error:'Workout not found'});
    const value=JSON.parse(row.payload);
    res.attachment('workout-report.json').json({...value,summary:Workout.restore(value).summary(),definitions:{hits:'target interactions, not body repetitions',workMs:'excludes rest and pause'}});
  });
  app.get("/api/health", (req, res) => {
    const config = readConfig();
    res.set("Cache-Control", "no-store").json({
      status: "ok",
      aiConfigured: Boolean(config.key),
      model: config.model,
    });
  });
  app.get("/api/programs", (req, res) => res.json(programs));
  const session = z
    .object({
      calibration: calibrationSchema.optional(),
      recommendationId: z.string().uuid().optional(),
      interaction: drillSchema.optional(),
      replay: replaySchema.optional(),
      id: z.string().uuid().optional(),
      program: z.enum(programIds),
      startedAt: z.string().datetime(),
      activeSeconds: z.number().int().min(1).max(3600),
      hits: z.number().int().min(0).max(10000),
      mode: z.enum(["desktop", "vr"]),
    })
    .strict();
  app.post("/api/sessions", (req, res) => {
    const r = session.safeParse(req.body);
    if (!r.success) return res.status(400).json({ error: "训练记录格式无效" });
    if(r.data.interaction && (r.data.interaction.program!==r.data.program || r.data.interaction.hits!==r.data.hits || r.data.interaction.elapsed>3600000 || Math.abs(Math.round(trainingWorkMs(r.data.program,r.data.interaction.elapsed)/1000)-r.data.activeSeconds)>1)) return res.status(400).json({error:"交互统计与训练记录不一致"});
    if(r.data.replay){try{if(!r.data.interaction)throw new Error("Missing interaction");verifyReplay(r.data.replay,r.data.interaction)}catch{return res.status(400).json({error:"训练回放与统计不一致"})}}
    const x = r.data,
      id = x.id || randomUUID();
    x.startedAt = new Date(x.startedAt).toISOString();
    if(x.recommendationId){
      const decision=db.prepare("SELECT * FROM coach_decisions WHERE id=?").get(x.recommendationId);
      if(!decision?.decision)return res.status(400).json({error:"建议尚未确认"});
      const p=JSON.parse(decision.payload),expected=decision.decision==="accepted"?p.suggested:p.baseline;
      if(x.program!==expected.program||x.mode!==expected.mode||x.interaction?.difficulty!==expected.difficulty||x.activeSeconds>expected.seconds+1)return res.status(400).json({error:"训练设置与已确认建议不一致"});
    }
    const existing = db.prepare("SELECT * FROM sessions WHERE id=?").get(id);
    if (existing) {
      const same =
        (existing.calibration||null)===(x.calibration?JSON.stringify(x.calibration):null) && (existing.recommendationId||null)===(x.recommendationId||null) &&
        existing.program === x.program &&
        Date.parse(existing.started) === Date.parse(x.startedAt) &&
        existing.seconds === x.activeSeconds &&
        existing.hits === x.hits &&
        existing.mode === x.mode && (existing.interaction||null)=== (x.interaction?JSON.stringify(x.interaction):null) && (existing.replay||null)===(x.replay?JSON.stringify(x.replay):null);
      if (!same)
        return res
          .status(409)
          .json({
            error: "同一记录编号的内容不一致，请保留原记录并检查重试内容。",
          });
      return res.json(sessionRow(existing));
    }
    db.prepare("INSERT INTO sessions(id,program,started,seconds,hits,mode,interaction,replay,calibration,recommendationId) VALUES(?,?,?,?,?,?,?,?,?,?)").run(
      id,
      x.program,
      x.startedAt,
      x.activeSeconds,
      x.hits,
      x.mode,
      x.interaction?JSON.stringify(x.interaction):null,
      x.replay?JSON.stringify(x.replay):null,
      x.calibration?JSON.stringify(x.calibration):null,
      x.recommendationId||null,
    );
    res.status(201).json({ id });
  });
  app.get('/api/sessions/:id/replay',(req,res)=>{const row=db.prepare('SELECT interaction,replay FROM sessions WHERE id=?').get(req.params.id);if(!row)return res.status(404).json({error:'Record not found'});if(!row.replay)return res.json({status:'unavailable',reason:'此历史记录没有事件回放'});try{res.json({...verifyReplay(JSON.parse(row.replay),JSON.parse(row.interaction)),replay:JSON.parse(row.replay)})}catch{res.status(409).json({error:'Stored replay validation failed'})}});
  app.get("/api/sessions", (req, res) =>
    res.json(db.prepare("SELECT * FROM sessions ORDER BY started DESC").all().map(sessionRow)),
  );
  const pageQuery = z
    .object({
      limit: z.coerce.number().int().min(1).max(100).default(20),
      offset: z.coerce.number().int().min(0).max(1000000).default(0),
      program: z.enum(programIds).optional(),
      mode: z.enum(["desktop", "vr"]).optional(),
    })
    .strict();
  app.get("/api/session-page", (req, res) => {
    const parsed = pageQuery.safeParse(req.query);
    if (!parsed.success)
      return res.status(400).json({ error: "分页或筛选参数无效" });
    const { limit, offset, program, mode } = parsed.data;
    const clauses = [],
      values = [];
    if (program) {
      clauses.push("program=?");
      values.push(program);
    }
    if (mode) {
      clauses.push("mode=?");
      values.push(mode);
    }
    const where = clauses.length ? " WHERE " + clauses.join(" AND ") : "";
    const { total } = db
      .prepare("SELECT COUNT(*) AS total FROM sessions" + where)
      .get(...values);
    const items = db
      .prepare(
        "SELECT * FROM sessions" +
          where +
          " ORDER BY started DESC,id DESC LIMIT ? OFFSET ?",
      )
      .all(...values, limit, offset);
    res.json({ items:items.map(sessionRow), total, limit, offset });
  });
  const statsQuery = z
    .object({
      days: z.coerce.number().int().min(1).max(90).default(7),
      end: z
        .string()
        .regex(/^\d{4}-\d{2}-\d{2}$/)
        .optional(),
    })
    .strict();
  app.get("/api/stats", (req, res) => {
    const parsed = statsQuery.safeParse(req.query);
    if (!parsed.success) return res.status(400).json({ error: "统计参数无效" });
    const { days } = parsed.data,
      end = parsed.data.end || new Date().toISOString().slice(0, 10);
    const endMs = Date.parse(end + "T00:00:00Z");
    if (
      !Number.isFinite(endMs) ||
      new Date(endMs).toISOString().slice(0, 10) !== end
    )
      return res.status(400).json({ error: "统计日期无效" });
    const startMs = endMs - (days - 1) * 86400000;
    const start = new Date(startMs).toISOString(),
      stop = new Date(endMs + 86400000).toISOString();
    const allTime = db
      .prepare(
        "SELECT COUNT(*) AS sessions, COALESCE(SUM(seconds),0) AS seconds, COALESCE(SUM(hits),0) AS hits FROM sessions",
      )
      .get();
    const rows = db
      .prepare(
        "SELECT substr(started,1,10) AS day, COUNT(*) AS sessions, SUM(seconds) AS seconds, SUM(hits) AS hits FROM sessions WHERE started>=? AND started<? GROUP BY day ORDER BY day",
      )
      .all(start, stop);
    const byDay = new Map(rows.map((row) => [row.day, row]));
    const daily = Array.from({ length: days }, (_, i) => {
      const day = new Date(startMs + i * 86400000).toISOString().slice(0, 10);
      return byDay.get(day) || { day, sessions: 0, seconds: 0, hits: 0 };
    });
    res.json({ timezone: "UTC", allTime, daily });
  });
  app.get('/api/training-report', (req, res) => {
    const rows = db.prepare('SELECT * FROM sessions ORDER BY started DESC,id DESC').all();
    res.attachment('vrfitai-report.json').json(trainingReport(rows.map(sessionRow)));
  });
  app.get("/api/sessions/export", (req, res) => {
    const rows = db
      .prepare("SELECT * FROM sessions ORDER BY started DESC")
      .all();
    res
      .attachment("vrfitai-sessions.csv")
      .type("text/csv")
      .send(
        "\uFEFF课程,开始时间,有效秒数,交互命中,模式\n" +
          rows
            .map((x) =>
              [
                x.interaction?getProgram(x.program).title:getProgram(x.program).legacyTitle,
                x.started,
                x.seconds,
                x.hits,
                x.mode,
              ].join(","),
            )
            .join("\n"),
      );
  });
  const msg = z
    .object({
      role: z.enum(["user", "assistant"]),
      content: z.string().trim().min(1).max(2000),
    })
    .strict();
  const chat = z
    .object({
      messages: z.array(msg).min(1).max(12),
      recommendationId:z.string().uuid().optional(),
      summary: z
        .object({
          program: z.enum(programIds),
          activeSeconds: z.number().int().min(0).max(3600),
          hits: z.number().int().min(0).max(10000),
        })
        .strict()
        .optional(),
    })
    .strict();
  const requests = new Map();
  app.post("/api/chat", async (req, res) => {
    const r = chat.safeParse(req.body);
    if (!r.success || r.data.messages.at(-1)?.role !== "user")
      return res.status(400).json({ error: "对话格式无效" });
    const now = Date.now(),
      key = req.ip;
    for (const [k, v] of requests) if (v.reset < now) requests.delete(k);
    const bucket = requests.get(key) || { count: 0, reset: now + 60000 };
    bucket.count++;
    requests.set(key, bucket);
    if (bucket.count > 10)
      return res
        .status(429)
        .json({ error: "请稍后再发送，每分钟最多 10 次。" });
    try {
      let recommendation;
      if(r.data.recommendationId){
        const row=db.prepare('SELECT payload FROM coach_decisions WHERE id=?').get(r.data.recommendationId);
        if(!row)return res.status(404).json({error:'建议不存在，请返回课程重新生成'});
        const v=JSON.parse(row.payload);
        recommendation={version:v.version,source:v.source,sampleCount:v.sampleCount,basis:v.basis,reason:v.reason,baseline:v.baseline,suggested:v.suggested,coldStart:v.coldStart};
      }
      res.json(await answer({...r.data,recommendation}, readConfig(), fetcher));
    } catch (e) {
      res.status(e.status || 502).json({
        error: e.status ? e.message : "AI 配置或响应异常，请检查服务端。",
      });
    }
  });
  installPersonal(app,db);
  installCoach(app,db);
  app.use("/api", (req, res) => res.status(404).json({ error: "接口不存在" }));
  app.use(express.static(resolve("dist"), {setHeaders(res, file){if(file.endsWith(".html"))res.setHeader("Cache-Control","no-store");}}));
  app.use((err, req, res, next) =>
    res
      .status(err.status === 413 ? 413 : 400)
      .json({ error: err.status === 413 ? "请求内容过大" : "请求格式无效" }),
  );
  return { app, close: () => db.close() };
}
