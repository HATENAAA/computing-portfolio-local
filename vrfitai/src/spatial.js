import { z } from 'zod';
export const calibrationSchema = z.object({version:z.literal(1),posture:z.enum(['seated','standing']),height:z.number().min(0.8).max(2),width:z.number().min(0.4).max(1.2)}).strict();
export const defaultCalibration = {version:1,posture:'standing',height:1.45,width:1.1};
// Distances are metres in local-floor space. Upper/lower offsets are reduced for seated use.
export function targetPositions(value=defaultCalibration, compact=false) {
 const c=calibrationSchema.parse(value), w=c.width*(compact?0.73:1), dy=c.posture==='seated'?0.28:0.45;
 return [[-w,c.height,-2.3],[w,c.height,-2.3],[-w*.59,c.height+dy,-2.6],[w*.59,c.height+dy,-2.6],[0,c.height-dy*.65,-2]];
}
export function trackedInputs(frame, referenceSpace, sources, program) {
 const valid=[...sources].filter(s=>s.targetRayMode==='tracked-pointer' && ['left','right'].includes(s.handedness) && frame?.getPose(s.targetRaySpace,referenceSpace));
 return program==='rhythm' ? ['left','right'].every(h=>valid.some(s=>s.handedness===h)) : valid.length>0;
}
export class FrameProbe {
 constructor(){this.samples={desktop:[],vr:[]};this.last=null;this.mode=null;this.losses=0;}
 frame(t,vr){const mode=vr?'vr':'desktop';if(this.last!==null&&this.mode===mode){const a=this.samples[mode];if(a.length>=6000)a.shift();a.push(t-this.last);}this.last=t;this.mode=mode;}
 report(){return {version:1,trackingLosses:this.losses,definition:'Animation callback intervals, not GPU time; rolling last 6000 intervals per mode, includes stalls',...Object.fromEntries(Object.entries(this.samples).map(([k,a])=>{const s=[...a].sort((x,y)=>x-y),mean=a.reduce((x,y)=>x+y,0)/a.length;return [k,{samples:a.length,meanMs:a.length?+mean.toFixed(2):null,fps:a.length?+(1000/mean).toFixed(1):null,p95Ms:a.length?s[Math.ceil(s.length*.95)-1]:null}]}))};}
}
