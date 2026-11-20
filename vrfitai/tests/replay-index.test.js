import {test} from 'node:test';
import assert from 'node:assert/strict';
import {RecordedDrill,ReplayIndex,replayEvents} from '../src/replay.js';
for(const program of ['rhythm','focus','flow']) test(program+' indexed random seeks equal full prefix replay',()=>{
  const d=new RecordedDrill(program,'hard');
  for(let t=0;t<90000;t+=100){d.advance(t,d.data.cue?.index??-1);if(t%500===0)d.input(0);}
  const journal=d.journal(), index=new ReplayIndex(journal);
  for(const cursor of [journal.events.length,0,255,256,257,888,10,511,512]){
    const result=index.seek(cursor);
    assert.deepEqual(result.drill.snapshot(),replayEvents({...journal,events:journal.events.slice(0,cursor)}).drill.snapshot());
    assert.ok(result.replayedEvents<256);
    result.drill.data.hits=999999;
    assert.notEqual(index.seek(cursor).drill.data.hits,999999);
  }
  journal.events.length=0;assert.ok(index.seek(888));
  assert.throws(()=>index.seek(-1));assert.throws(()=>index.seek(1.5));
});
test('index rejects sequence errors and backwards clocks',()=>{
  const d=new RecordedDrill();d.advance(100);d.advance(200);
  const bad=d.journal();bad.events[1][2]=50;assert.throws(()=>new ReplayIndex(bad));
  assert.throws(()=>new ReplayIndex(d.journal(),0));
});
