import { programIds } from "../src/catalog.js";
import { z } from 'zod';
import { randomUUID } from 'node:crypto';
import { recommend } from '../src/coach.js';
export function installCoach(app,db) {
 db.exec(`CREATE TABLE IF NOT EXISTS coach_decisions(id TEXT PRIMARY KEY,payload TEXT NOT NULL,decision TEXT,created TEXT NOT NULL);`);
 const query=z.object({program:z.enum(programIds),difficulty:z.enum(['easy','medium','hard']),seconds:z.coerce.number().int().min(30).max(300),mode:z.enum(['desktop','vr'])}).strict();
 app.post('/api/coach', (req,res)=>{
  const q=query.safeParse(req.body);if(!q.success)return res.status(400).json({error:'建议参数无效'});
  const rows=db.prepare(`SELECT s.*,r.effort FROM sessions s LEFT JOIN reflections r ON r.recordId=s.id AND r.kind='session' ORDER BY s.started DESC,s.id DESC`).all().map(r=>({...r,startedAt:r.started,interaction:r.interaction?JSON.parse(r.interaction):null,reflection:r.effort?{effort:r.effort}:null}));
  const value={id:randomUUID(),...recommend(rows,q.data)};
  db.prepare('INSERT INTO coach_decisions VALUES(?,?,NULL,?)').run(value.id,JSON.stringify(value),new Date().toISOString());res.status(201).json(value);
 });
 app.put('/api/coach/:id', (req,res)=>{
  const v=z.object({decision:z.enum(['accepted','declined'])}).strict().safeParse(req.body);if(!v.success)return res.status(400).json({error:'选择无效'});
  const row=db.prepare('SELECT * FROM coach_decisions WHERE id=?').get(req.params.id);if(!row)return res.status(404).json({error:'建议不存在'});
  if(row.decision&&row.decision!==v.data.decision)return res.status(409).json({error:'该建议已确认，请重新生成'});
  db.prepare('UPDATE coach_decisions SET decision=? WHERE id=?').run(v.data.decision,req.params.id);res.json({ok:true});
 });
 app.get('/api/coach/evaluation',(req,res)=>{
  const decisions=db.prepare('SELECT * FROM coach_decisions ORDER BY created DESC').all();
  res.attachment('coach-evaluation.json').json({version:1,interpretation:'Descriptive follow-up only; declined suggestions are self-selected fixed-setting comparisons, not randomized causal evidence.',decisions:decisions.map(r=>({id:r.id,created:r.created,decision:r.decision,recommendation:JSON.parse(r.payload),outcomes:db.prepare('SELECT id,seconds,interaction FROM sessions WHERE recommendationId=? ORDER BY started').all(r.id).map(s=>({...s,interaction:s.interaction?JSON.parse(s.interaction):null}))}))});
 });
}
