import { programIds } from "./catalog.js";
import { z } from 'zod';
export const planSchema = z.object({version:z.literal(1),blocks:z.array(z.object({
 program:z.enum(programIds),sets:z.number().int().min(1).max(10),
 workSeconds:z.number().int().min(1).max(600),restSeconds:z.number().int().min(0).max(300)
}).strict()).min(1).max(8)}).strict();
export function phasesFor(plan) {
 const config=planSchema.parse(plan),phases=[];
 for(const [block,b] of config.blocks.entries())for(let set=1;set<=b.sets;set++){
  phases.push({type:'work',block,set,program:b.program,ms:b.workSeconds*1000});
  if(b.restSeconds && (set<b.sets || block<config.blocks.length-1))phases.push({type:'rest',block,set,program:b.program,ms:b.restSeconds*1000});
 }
 if(phases.reduce((s,p)=>s+p.ms,0)>7200000)throw new Error('Plan exceeds two hours');
 return phases;
}
export class Workout {
 constructor(config,now=()=>performance.now(),id=crypto.randomUUID()) {
  this.config=structuredClone(planSchema.parse(config));this.phases=phasesFor(config);
  this.total=this.phases.reduce((s,p)=>s+p.ms,0);this.now=now;this.elapsed=0;
  this.endedEarly=false;this.hits=this.phases.map(()=>0);this.state='idle';this.id=id;this.startedAt=null;
 }
 start(){if(this.state!=='idle')return;this.startedAt=new Date().toISOString();this.mark=this.now();this.state='running';}
 tick(){
  if(this.state==='running'){const n=this.now();this.elapsed=Math.min(this.total,this.elapsed+Math.max(0,n-this.mark));this.mark=n;
   if(this.elapsed>=this.total)this.state='finished';}
  return this.position();
 }
 position(){let end=0;for(let i=0;i<this.phases.length;i++){end+=this.phases[i].ms;if(this.elapsed<end)return {...this.phases[i],index:i,remainingMs:end-this.elapsed};}return {type:'finished',index:this.phases.length,remainingMs:0};}
 pause(){this.tick();if(this.state==='running')this.state='paused';}
 resume(){if(this.state==='paused'){this.mark=this.now();this.state='running';}}
 hit(){this.tick();const p=this.position();if(this.state==='running'&&p.type==='work'&&this.hits[p.index]<10000)this.hits[p.index]++;}
 stop(){this.tick();if(['running','paused'].includes(this.state)){this.endedEarly=this.elapsed<this.total;this.state='finished';}}
 summary(){let consumed=0,workMs=0,restMs=0;for(const p of this.phases){const delta=Math.max(0,Math.min(p.ms,this.elapsed-consumed));if(p.type==='work')workMs+=delta;else restMs+=delta;consumed+=p.ms;}
  return {workMs,restMs,hits:this.hits.reduce((a,b)=>a+b,0),completed:this.elapsed===this.total};}
 snapshot(){this.tick();return {version:1,id:this.id,config:this.config,startedAt:this.startedAt,elapsedMs:this.elapsed,hits:[...this.hits],...(this.endedEarly?{endedEarly:true}:{}),...(this.planName?{planName:this.planName}:{})};}
 static restore(value,now=()=>performance.now()){
  const s=z.object({version:z.literal(1),endedEarly:z.boolean().optional(),planName:z.string().min(1).max(60).optional(),id:z.string().uuid(),config:planSchema,startedAt:z.string().datetime(),elapsedMs:z.number().finite().min(0),hits:z.array(z.number().int().min(0).max(10000))}).strict().parse(value);
  const w=new Workout(s.config,now,s.id);
  if(s.elapsedMs>w.total || s.hits.length!==w.phases.length)throw new Error('Checkpoint dimensions invalid');
  let start=0;for(const [i,p] of w.phases.entries()){
   if(s.hits[i] && (p.type==='rest' || s.elapsedMs<start))throw new Error('Impossible hit allocation');start+=p.ms;
  }
  Object.assign(w,{startedAt:s.startedAt,elapsed:s.elapsedMs,hits:[...s.hits],planName:s.planName,endedEarly:s.endedEarly||false,state:s.elapsedMs===w.total||s.endedEarly?'finished':'paused',mark:now()});return w;
 }
}
