import { Drill } from './drills.js';
export const coachVersion='rules-1';
const levels=['easy','medium','hard'];
export function recommend(records, {program,difficulty,seconds,mode}) {
 const rows=records.filter(r=>r.program===program && r.mode===mode && r.interaction?.difficulty===difficulty && r.seconds>=seconds*.8 && r.seconds<=seconds*1.2 && r.reflection?.effort>=1).sort((a,b)=>b.startedAt.localeCompare(a.startedAt)).slice(0,5);
 const metrics=rows.map(r=>{const v=Drill.restore(r.interaction).view();return {...v,effort:r.reflection.effort}});
 const usable=metrics.length>=3 && metrics.every(v=>v.accuracy!==null && v.reactionMs!==null);
 const avg=k=>metrics.reduce((s,v)=>s+v[k],0)/metrics.length;
 const basis=usable?{accuracy:Math.round(avg('accuracy')),reactionMs:Math.round(avg('reactionMs')),missRate:+(metrics.reduce((s,v)=>s+v.missed,0)/Math.max(1,metrics.reduce((s,v)=>s+v.hits+v.missed+v.avoided,0))).toFixed(3),effort:+avg('effort').toFixed(1)}:null;
 let next=difficulty,time=seconds,reason='至少需要 3 次同课程、同难度、同输入模式、时长相差不超过 20% 且填写用力感的有效记录；当前保持设置。';
 if(usable){
  const threshold=['focus', 'sequence'].includes(program) ? 3000 : 1000;
  if(basis.effort>=8 || basis.accuracy<70 || basis.missRate>.25){next=levels[Math.max(0,levels.indexOf(difficulty)-1)];if(next===difficulty)time=Math.max(30,Math.round(seconds*.8));reason='用力感偏高、正确率偏低或漏过较多，建议降低一级；已是舒适难度时缩短最多 20%。';}
  else if(basis.accuracy>=90 && basis.missRate<=.1 && basis.effort<=6 && basis.reactionMs<=threshold){next=levels[Math.min(2,levels.indexOf(difficulty)+1)];if(next===difficulty)time=Math.min(300,Math.round(seconds*1.2));reason='正确率、漏过、响应时间与用力感均达到规则阈值，建议提高一级；已是挑战难度时延长最多 20%。';}
  else reason='当前表现尚未同时达到调整阈值，建议保持设置。';
 }
 return {version:coachVersion,source:'rule',sampleCount:rows.length,sampleIds:rows.map(r=>r.id),basis,reason,baseline:{program,difficulty,seconds,mode},suggested:{program,difficulty:next,seconds:time,mode},coldStart:!usable};
}
