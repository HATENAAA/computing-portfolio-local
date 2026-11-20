import {test} from 'node:test';
import assert from 'node:assert/strict';
import {deviceCapabilities} from '../src/capabilities.js';
import {coachExamples,exampleConfig} from '../src/coach-examples.js';
import {recommend} from '../src/coach.js';
import {programs} from '../src/catalog.js';
test('VR preflight distinguishes insecure, missing, unsupported, permitted and rejected capability checks',async()=>{
 assert.equal((await deviceCapabilities({},true)).available,false);
 assert.equal((await deviceCapabilities({xr:{isSessionSupported:()=>assert.fail()}},false)).available,false);
 assert.equal((await deviceCapabilities({xr:{isSessionSupported:async mode=>{assert.equal(mode,'immersive-vr');return true;}}},true)).available,true);
 assert.equal((await deviceCapabilities({xr:{isSessionSupported:async()=>false}},true)).available,false);
 assert.equal((await deviceCapabilities({xr:{isSessionSupported:async()=>{throw Error('denied')}}},true)).available,false);
});
test('review cases reproduce cold start, progress, fatigue priority and missed-target failures using real rules',()=>{
 const outputs=coachExamples.map(e=>recommend(e.records,exampleConfig));
 assert.deepEqual(outputs.map(r=>r.suggested.difficulty),['medium','hard','easy','easy']);
 assert.deepEqual(outputs.map(r=>r.coldStart),[true,false,false,false]);
 assert.equal(outputs[3].basis.missRate,.4);
 assert.equal(outputs[2].basis.accuracy,100);assert.equal(outputs[2].basis.effort,9);
 assert.ok(coachExamples.every(e=>e.records.every(r=>r.id.startsWith('synthetic-'))));
 const before=JSON.stringify(coachExamples);recommend(coachExamples[1].records,exampleConfig);assert.equal(JSON.stringify(coachExamples),before);
});
test('course labels describe selection, dwell, inhibition and recall while retaining stable record identifiers',()=>{
 assert.deepEqual(programs.map(p=>p.id),['rhythm','focus','flow','sequence']);
 assert.deepEqual(programs.map(p=>p.title),['左右节奏','稳定停留','反应与抑制','顺序记忆']);
 assert.ok(!programs.some(p=>/直拳|舒展|拳靶/.test(JSON.stringify(p))));
});
