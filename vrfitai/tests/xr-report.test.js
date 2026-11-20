import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bindXRVisibility, xrAction } from '../src/xr-lifecycle.js';
import { trainingReport } from '../server/report.js';
test('XR visibility pauses without auto resume and removes old listener',()=>{
 const s=new EventTarget();s.visibilityState='visible';let count=0;
 const off=bindXRVisibility(s,()=>count++);
 s.visibilityState='hidden';s.dispatchEvent(new Event('visibilitychange'));
 s.visibilityState='visible';s.dispatchEvent(new Event('visibilitychange'));
 assert.equal(count,1);off();s.visibilityState='hidden';s.dispatchEvent(new Event('visibilitychange'));
 assert.equal(count,1);
});
test('already occluded XR session pauses immediately',()=>{
 const s=new EventTarget();s.visibilityState='visible-blurred';let count=0;
 bindXRVisibility(s,()=>count++ )();assert.equal(count,1);
});
test('in-world action dispatch separates exit, finish, toggle and hit',()=>{
 assert.equal(xrAction({exit:true}),'exit');assert.equal(xrAction({finish:true}),'finish');
 assert.equal(xrAction({pause:true}),'toggle');assert.equal(xrAction({index:2}),'hit');
});
test('report totals all records with per-program grouping and explicit measurement meaning',()=>{
 const rows=[{program:'rhythm',seconds:30,hits:2},{program:'rhythm',seconds:10,hits:1},{program:'flow',seconds:20,hits:4}];
 const r=trainingReport(rows);assert.deepEqual(r.summary,{sessions:3,seconds:60,hits:7});
 assert.equal(r.programs.rhythm.seconds,40);assert.equal(r.programs.flow.sessions,1);
 assert.match(r.definitions.hits,/not exercise repetitions/);assert.equal(r.records.length,3);
});
test('empty report has zero counts',()=>assert.equal(trainingReport([]).summary.seconds,0));
