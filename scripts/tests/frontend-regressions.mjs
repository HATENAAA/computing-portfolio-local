import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const code=readFileSync(new URL('../../bathymetry-lab/web/app.js',import.meta.url),'utf8');
function setup(handler){
 const elements=new Map();
 function element(){return {value:'',hidden:false,disabled:false,innerHTML:'',textContent:'',files:[],children:[],append(...v){this.children.push(...v);},replaceChildren(...v){this.children=v;},setAttribute(){},removeAttribute(){}};}
 const document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},createElement:element,createTextNode:text=>({textContent:text}),querySelectorAll:()=>[]};
 const calls=[];
 const context=vm.createContext({document,fetch:async(path,options)=>{const payload=options?JSON.parse(options.body):undefined;calls.push({path,payload});return handler(path,payload);},URL,Blob,setTimeout});
 vm.runInContext(code,context);
 return {elements,get:id=>document.getElementById(id),calls,run:s=>vm.runInContext(s,context)};
}
const report={id:'a'.repeat(32),units:'reflectance',source:'synthetic-example',samples:8,group_count:4,train_groups:['a','b'],test_groups:['c','d'],metrics:{linear:{rmse_m:1,mae_m:1,r2:.5},svr:{rmse_m:1,mae_m:1,r2:.5}},test_depth_m:[1,2],predictions:{linear:[-.7,2.2],svr:[.8,2]}};
const ok=data=>({ok:true,json:async()=>data});
test('negative model predictions remain visible within the chart',()=>{
 const s=setup(()=>ok(report));s.run(`plot(${JSON.stringify(report)})`);
 const points=[...s.get('chart').innerHTML.matchAll(/cx="([\d.-]+)" cy="([\d.-]+)"/g)];
 assert.equal(points.length,4);assert.ok(points.every(([,x,y])=>+x>=55&&+x<=610&&+y>=35&&+y<=335));
});
test('failed evaluation clears previous results and disables inference',async()=>{
 let failure=false;const s=setup(()=>failure?{ok:false,json:async()=>({error:'invalid CSV'})}:ok(report));
 await s.run('run(true)');assert.equal(s.get('result').hidden,false);failure=true;
 await s.run('run(false)');assert.equal(s.get('result').hidden,true);assert.equal(s.get('predict').disabled,true);assert.match(s.get('status').textContent,/invalid CSV/);
});
test('synthetic evaluation sets prediction units independently from training selector',async()=>{
 const s=setup((path)=>ok(path==='/api/train'?report:{count:1,outside_training_range:0,negative_predictions:0}));
 s.get('units').value='dn';await s.run('run(true)');assert.equal(s.get('predict-units').value,'reflectance');
 s.get('model').value='svr';s.get('predict-file').files=[{size:10,text:async()=> 'B2,B3,B4,B8\n.1,.2,.3,.4'}];
 await s.get('predict').onclick();assert.equal(s.calls.at(-1).payload.units,'reflectance');
});
test('inference locks model-changing actions and keeps its experiment id',async()=>{
 let resolvePrediction;const s=setup((path)=>path==='/api/train'?ok(report):new Promise(resolve=>{resolvePrediction=()=>resolve(ok({count:1,outside_training_range:0,negative_predictions:0}));}));
 await s.run('run(true)');s.get('model').value='svr';s.get('predict-file').files=[{size:1,text:async()=> 'a'}];
 const pending=s.get('predict').onclick();await Promise.resolve();await Promise.resolve();
 assert.equal(s.get('train').disabled,true);assert.equal(s.get('demo').disabled,true);
 await s.run('run(true)');assert.equal(s.calls.filter(c=>c.path==='/api/train').length,1);
 resolvePrediction();await pending;assert.equal(s.get('train').disabled,false);assert.ok(s.get('prediction').children.at(-1).href.includes(report.id));
});

const medicalBase=new URL('../../case-studies/medical/source/src/',import.meta.url);
test('medical storage parser treats corrupted JSON as missing session',()=>{
 const common=readFileSync(new URL('common.js',medicalBase),'utf8').replaceAll('export function','function');
 const ctx=vm.createContext({sessionStorage:{getItem:()=>'{broken'}});vm.runInContext(common,ctx);
 assert.equal(vm.runInContext("getSessionStorage('token')",ctx),null);
});
test('medical route guard redirects once for absent or invalid tokens',()=>{
 const main=readFileSync(new URL('main.js',medicalBase),'utf8').replace(/^import .*$/gm,'').split('createApp(App)')[0];
 for(const token of [null,'',{},'valid-token']){
  let guard;const ctx=vm.createContext({router:{beforeEach:f=>guard=f},getSessionStorage:()=>token});vm.runInContext(main,ctx);
  assert.equal(guard({path:'/report'}),token==='valid-token'?true:'/login');assert.equal(guard({path:'/login'}),true);
 }
});
test('medical navigation waits for profile retrieval and handles profile failures',async()=>{
 const script=readFileSync(new URL('views/Login.vue',medicalBase),'utf8').split('<script>')[1].split('</script>')[0].replace(/^import .*$/gm,'').replace('export default','var component =');
 let resolveProfile,failProfile;const saved={},navigations=[];
 const ctx=vm.createContext({reactive:x=>x,toRefs:x=>x,useRouter:()=>({push:p=>navigations.push(p)}),setSessionStorage:(k,v)=>saved[k]=v,removeSessionStorage:k=>delete saved[k],alert:()=>{},service:{post:async()=>({data:'test-token'}),get:()=>new Promise((resolve,reject)=>{resolveProfile=resolve;failProfile=reject;})}});
 vm.runInContext(script,ctx);const ui=vm.runInContext('component.setup()',ctx);ui.users.userID='test';ui.users.password='test';ui.login();await new Promise(setImmediate);
 assert.deepEqual(navigations,[]);resolveProfile({data:{sex:1}});await new Promise(setImmediate);assert.deepEqual(navigations,['/index']);assert.equal(saved.users.sex,1);
 ui.login();await new Promise(setImmediate);failProfile(new Error('offline'));await new Promise(setImmediate);assert.equal(saved.token,undefined);assert.equal(saved.users,undefined);assert.equal(navigations.length,1);
});
