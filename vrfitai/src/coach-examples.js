import {Drill} from './drills.js';
export const exampleConfig={program:'rhythm',difficulty:'medium',seconds:60,mode:'desktop'};
function sample(id,hits,missed,mistakes,response,effort){
 const d=new Drill('rhythm','medium');Object.assign(d.data,{elapsed:60000,hits,missed,mistakes,serial:hits+missed+1,responses:Array(hits).fill(response),cue:{index:0,start:60000,end:62500,avoid:false,hold:0}});
 return {id:'synthetic-'+id,program:'rhythm',mode:'desktop',seconds:60,startedAt:new Date(Date.UTC(2026,0,id)).toISOString(),interaction:d.snapshot(),reflection:{effort}};
}
export const coachExamples=[
 {id:'cold',title:'冷启动',question:'只有两次同类训练，会直接升级吗？',records:[sample(1,20,0,0,600,4),sample(2,20,0,0,600,4)],expected:'保持设置：样本不足 3 次'},
 {id:'progress',title:'稳定表现',question:'高正确率、较快响应、较低用力感会怎样？',records:[1,2,3].map(i=>sample(i,20,0,0,600,4)),expected:'标准 → 挑战，时长保持 60 秒'},
 {id:'fatigue',title:'疲劳反例',question:'全部选对但用力感为 9，是否还会加难？',records:[1,2,3].map(i=>sample(i,20,0,0,600,9)),expected:'标准 → 舒适，疲劳规则优先'},
 {id:'miss',title:'漏过较多',question:'命中时很快，但漏过很多，是否被误判优秀？',records:[1,2,3].map(i=>sample(i,12,8,0,500,5)),expected:'标准 → 舒适，漏过率 40%'}
];
