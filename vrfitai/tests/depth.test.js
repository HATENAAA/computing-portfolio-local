import {test} from 'node:test';
import assert from 'node:assert/strict';
import {targetPositions,defaultCalibration,trackedInputs,FrameProbe} from '../src/spatial.js';
import {recommend} from '../src/coach.js';
import {Drill} from '../src/drills.js';
import {Outbox} from '../src/outbox.js';
import {RecoveryStore} from '../src/recovery.js';
const config={program:'rhythm',difficulty:'easy',seconds:60,mode:'desktop'};
const row=(id,change={})=>{const d=new Drill();d.data.elapsed=60000;d.data.cue={index:0,start:60000,end:63600,avoid:false,hold:0};d.data.serial=21;d.data.hits=20;d.data.responses=Array(20).fill(600);return {id,program:'rhythm',mode:'desktop',seconds:60,startedAt:new Date().toISOString(),interaction:d.snapshot(),reflection:{effort:4},...change};};
test('coach cold start, homogeneous matching, recent samples and bounded changes',()=>{
 assert.equal(recommend([],config).coldStart,true);
 const rows=[row('1'),row('2'),row('3')];const r=recommend(rows,config);assert.equal(r.suggested.difficulty,'medium');assert.equal(r.suggested.seconds,60);assert.equal(r.basis.accuracy,100);
 assert.equal(recommend([rows[0],rows[1],row('4',{mode:'vr'})],config).coldStart,true);
 assert.equal(recommend(rows.map(r=>({...r,reflection:null})),config).coldStart,true);
 assert.equal(recommend(rows.map(r=>({...r,seconds:20})),config).coldStart,true);
 const tired=recommend(rows.map(r=>({...r,reflection:{effort:9}})),config);assert.equal(tired.suggested.seconds,48);assert.equal(tired.suggested.difficulty,'easy');
 assert.equal(recommend([...rows,...rows,...rows],config).sampleCount,5);
});
test('calibration bounds, seated height and compact spatial mapping',()=>{
 const standing=targetPositions();const seated=targetPositions({version:1,posture:'seated',height:1.1,width:.65});assert.ok(seated[2][1]<standing[2][1]);assert.equal(targetPositions(defaultCalibration,true)[0][0],-1.1*.73);
 assert.throws(()=>targetPositions({...defaultCalibration,width:10}));
});
test('tracking requires current poses and both hands for rhythm',()=>{
 const left={handedness:'left',targetRayMode:'tracked-pointer',targetRaySpace:{}},right={...left,handedness:'right',targetRaySpace:{}};const frame={getPose:space=>space===left.targetRaySpace?{}:null};
 assert.equal(trackedInputs(frame,{},[left,right],'rhythm'),false);assert.equal(trackedInputs(frame,{},[left,right],'focus'),true);assert.equal(trackedInputs(null,{},[left,right],'focus'),false);assert.equal(trackedInputs({getPose:()=>({})},{},[left,right],'rhythm'),true);
});
test('performance separates desktop and XR and does not clamp stalls',()=>{
 const p=new FrameProbe();p.frame(0,false);p.frame(10,false);p.frame(100,true);p.frame(110,true);p.frame(210,true);const r=p.report();assert.equal(r.desktop.samples,1);assert.equal(r.vr.samples,2);assert.equal(r.vr.p95Ms,100);
});
const storage=()=>{const m=new Map();return {get length(){return m.size},key:i=>[...m.keys()][i],getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)};};
test('durable outbox survives new instances, rejects mutations and shares UUIDs safely',()=>{
 const s=storage(),a=new Outbox(s),b=new Outbox(s);a.put({id:'a',hits:1});b.put({id:'b',hits:2});b.put({id:'a',hits:1});assert.equal(a.entries().length,2);assert.throws(()=>a.put({id:'a',hits:3}));a.remove('a');assert.equal(b.entries()[0].id,'b');
});
test('calibration and recommendation identity survive pending record recovery',()=>{
 const s=storage(),recovery=new RecoveryStore(s);const pending={id:'e23d0c2e-2931-4e0d-900a-78383b956a86',program:'rhythm',mode:'desktop',startedAt:new Date().toISOString(),activeSeconds:60,hits:0,calibration:defaultCalibration,recommendationId:'e23d0c2e-2931-4e0d-900a-78383b956a86'};recovery.write({pending});assert.deepEqual(recovery.read().value.pending,pending);
});
