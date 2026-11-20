import {test} from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../src/utils/operations.js',import.meta.url),'utf8');
const {csvText,parseTime,beijingDate,beijingWeekStart,overdue,progress,hours}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('CSV preserves Unicode, quotes, real line breaks and BOM',()=>{assert.equal(csvText([['产品','a,"b"'],['连接件',20]]),'\uFEFF"产品","a,""b"""\r\n"连接件","20"')});
test('CSV neutralizes spreadsheet formulas and control prefixes',()=>{for(const v of ['=1+1','+SUM(A1)','-1+2','@SUM(A1)','\t=1','\r=1'])assert.ok(csvText([[v]]).startsWith('\uFEFF"\''));assert.equal(csvText([[12]]),'\uFEFF"12"')});
test('Local schedule times use Beijing while explicit offsets are respected',()=>{const t=Date.UTC(2026,10,3,0);assert.equal(parseTime('2026-11-03T08:00:00'),t);assert.equal(parseTime('2026-11-03T00:00:00Z'),t);assert.equal(parseTime('2026-11-03T08:00:00+08:00'),t);assert.equal(parseTime('2026-11-03 08:00:00'),t)});
test('Beijing date uses the correct day across UTC midnight',()=>{assert.equal(beijingDate(new Date('2026-11-02T17:00:00Z')),'2026-11-03')});
test('Only overdue open orders trigger deadline warnings',()=>{for(const status of ['PENDING','ACCEPTED','PRODUCING','PAUSED'])assert.equal(overdue({status,dueDate:'2026-11-02'},'2026-11-03'),true);for(const status of ['COMPLETED','CANCELLED'])assert.equal(overdue({status,dueDate:'2026-11-02'},'2026-11-03'),false);assert.equal(overdue({dueDate:'2026-11-03'},'2026-11-03'),false)});
test('Rejected output is excluded from delivery progress',()=>{assert.equal(progress({quantity:10,completedQuantity:3,rejectedQuantity:7}),30);assert.equal(progress({quantity:0}),0)});
test('Calendar planned hours clip to the visible date range',()=>{const p={plannedstart:'2026-11-03T08:00:00',plannedend:'2026-11-03T12:00:00'};assert.equal(hours(p),4);assert.equal(hours(p,parseTime('2026-11-03T09:00:00'),parseTime('2026-11-03T11:00:00')),2);assert.equal(hours(p,parseTime('2026-11-04T00:00:00')),0)});

test('Calendar weeks start on Monday in Beijing even across UTC Sunday', () => {
  assert.equal(beijingWeekStart(new Date('2026-11-22T15:59:00Z')), '2026-11-16');
  assert.equal(beijingWeekStart(new Date('2026-11-22T16:01:00Z')), '2026-11-23');
});
