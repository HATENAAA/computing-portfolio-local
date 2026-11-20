import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Drill,trainingWorkMs} from '../src/drills.js';
import {RecordedDrill, verifyReplay} from '../src/replay.js';
import {RecoveryStore} from '../src/recovery.js';

test('boxing enforces sequence and controller handedness without accepting a wrong target',()=>{
 const d=new Drill('rhythm');d.advance(200);assert.equal(d.input(0,'right'),false);assert.equal(d.data.hits,0);assert.equal(d.data.mistakes,1);assert.equal(d.input(0,'left'),true);assert.equal(d.data.cue.index,1);d.advance(500);assert.equal(d.input(1,'right'),true);assert.equal(d.view().bestStreak,2);assert.equal(d.view().reactionMs,250);
});
test('focus requires uninterrupted live dwell, not clicks or a stalled clock',()=>{
 const d=new Drill('focus');const index=d.data.cue.index;assert.equal(d.input(index),false);d.advance(100,index);d.advance(200,index);d.advance(300,-1);assert.equal(d.data.cue.hold,0);d.advance(2000,index);assert.equal(d.data.hits,0);assert.equal(d.data.cue.hold,0);
 for(let t=2100;t<=3500;t+=100)d.advance(t,index);assert.equal(d.data.hits,1);assert.notEqual(d.data.cue.index,index);
});
test('paused input time never advances targets and checkpoint replay preserves cue and counters',()=>{
 const d=new Drill('rhythm','medium');d.advance(600);d.input(0);const snapshot=d.snapshot(),recovered=Drill.restore(snapshot);recovered.advance(50000,-1,false);assert.deepEqual(recovered.snapshot(),snapshot);recovered.advance(1000);d.advance(1000);assert.deepEqual(recovered.snapshot(),d.snapshot());
});
test('go/no-go rewards waiting, rejects red input, and disables interactions in rest',()=>{
 const d=new Drill('flow');for(let i=0;i<3;i++){d.advance(i*100+100);assert.equal(d.input(d.data.cue.index),true)}assert.equal(d.data.cue.avoid,true);d.advance(d.data.cue.end);assert.equal(d.data.avoided,1);d.advance(20000);assert.equal(d.resting,true);assert.equal(d.input(0),false);d.advance(25000);assert.equal(d.resting,false);assert.ok(d.data.cue);
});
test('grouped flow uses the plan rest schedule rather than adding another internal rest',()=>{
 const d=new Drill('flow');d.data.interval=false;d.advance(21000);assert.equal(d.resting,false);assert.ok(d.data.cue);
});
test('corrupt cue clocks, invalid counters and unknown courses cannot be restored',()=>{
 const d=new Drill();for(const change of [{streak:2,bestStreak:1},{cue:{...d.data.cue,end:0}},{hits:99},{program:'fake'},{seed:NaN}])assert.throws(()=>Drill.restore({...d.snapshot(),...change}));
});
test('recovery retains interaction mechanics along with the pending save payload',()=>{
 const data=new Map(),storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
 const d=new Drill();d.advance(300);d.input(0);const pending={id:'54c93f68-4ab1-4f74-bf1b-e6265e67bd1c',program:'rhythm',mode:'desktop',startedAt:'2026-11-04T00:00:00.000Z',activeSeconds:3,hits:1,interaction:d.snapshot()};new RecoveryStore(storage,()=>100).write({pending});assert.deepEqual(new RecoveryStore(storage,()=>200).read().value.pending,pending);
});

test('interval recovery is removed from effective time while ordinary courses retain active time',()=>{
 for(const [elapsed,work] of [[0,0],[19000,19000],[20000,20000],[24000,20000],[25000,20000],[30000,25000],[50000,40000]])assert.equal(trainingWorkMs('flow',elapsed),work);
 assert.equal(trainingWorkMs('flow',30000,false),30000);assert.equal(trainingWorkMs('rhythm',30000),30000);assert.throws(()=>trainingWorkMs('flow',NaN));
});

test('sequence shows distinct targets, ignores early presses, then accepts ordered recall', () => {
  for (const [difficulty, count] of [['easy', 3], ['medium', 4], ['hard', 5]]) {
    const d = new Drill('sequence', difficulty);
    const expected = [...d.data.cue.recall.order];
    assert.equal(expected.length, count);
    assert.equal(new Set(expected).size, count);
    d.advance(500);
    assert.equal(d.view().recall.index, expected[0]);
    assert.equal(d.input(expected[0]), false);
    assert.equal(d.data.mistakes, 0);

    d.advance(d.data.cue.recall.lastAt);
    assert.equal(d.view().recall.phase, 'recall');
    assert.equal(d.view().recall.index, null);
    assert.equal(d.input(expected[1]), false);
    assert.equal(d.view().recall.step, 0);
    for (const index of expected) {
      d.advance(d.data.elapsed + 300);
      assert.equal(d.input(index), true);
    }
    assert.equal(d.data.hits, count);
    assert.equal(d.data.mistakes, 1);
    assert.equal(d.view().recall.phase, 'ready');
    assert.equal(d.view().reactionMs, 300);
  }
});

test('partial sequence restores with verified replay and counts remaining targets at timeout', () => {
  const d = new RecordedDrill('sequence');
  for (let t = 0; t < 3600; t += 16) d.advance(t);
  assert.equal(d.input(d.data.cue.index), true);
  const checkpoint = d.snapshot();
  const journal = d.journal();
  assert.ok(journal.events.length < 12);
  assert.equal(verifyReplay(journal, checkpoint).status, 'verified');

  const restored = RecordedDrill.restore(checkpoint, journal);
  assert.equal(restored.view().recall.step, 1);
  restored.advance(restored.data.cue.end);
  assert.equal(restored.data.hits, 1);
  assert.equal(restored.data.missed, 2);
  assert.equal(verifyReplay(restored.journal(), restored.snapshot()).status, 'verified');
});
