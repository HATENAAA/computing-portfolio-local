const $=id=>document.getElementById(id);
let current=null,busy=false;
async function api(path,value){
 const r=await fetch(path,value===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
 const data=await r.json();if(!r.ok)throw new Error(data.error||'运行失败');return data;
}
function download(file,label,id=current.id){const a=document.createElement('a');a.href='/api/download?id='+encodeURIComponent(id)+'&file='+encodeURIComponent(file);a.textContent=label;a.download=(current?.source==='synthetic-example'?'synthetic-':'')+file;return a;}

function plot(report){
 const reference=report.source==='synthetic-example'?'合成参考水深':'上传参考水深';
 $('plot-title').textContent=reference+'与留出组预测';
 $('chart').setAttribute('aria-label',reference+'与预测散点图，单位米');
 const truth=report.test_depth_m,series=report.predictions,all=[...truth,...series.linear,...series.svr];
 // Negative predictions are diagnostic evidence and must remain inside the plot.
 const low=Math.min(0,Math.min(...all)-.3),high=Math.max(...all)+.3;
 const px=v=>55+(v-low)/(high-low)*555,py=v=>335-(v-low)/(high-low)*300;
 let html='';for(let i=0;i<=5;i++){let v=low+(high-low)*i/5;html+=`<path d="M55 ${py(v)}H610 M${px(v)} 35V335" stroke="#d9e8f0"/><text x="12" y="${py(v)+4}">${v.toFixed(1)}</text><text x="${px(v)-8}" y="355">${v.toFixed(1)}</text>`;}
 html+=`<path d="M55 335L610 35" stroke="#7195a7" stroke-dasharray="6 5"/><text x="260" y="382">${reference} / m</text><text x="12" y="18">预测水深 / m</text>`;
 for(const [name,color] of [['linear','#147ba5'],['svr','#bd6b30']])for(let i=0;i<truth.length;i++)html+=`<circle cx="${px(truth[i])}" cy="${py(series[name][i])}" r="${name==='svr'?5:3}" data-index="${i}" stroke="${color}" fill="${name==='svr'?'none':color}" opacity=".75"><title>${name}: ${reference} ${truth[i].toFixed(3)} m / 预测 ${series[name][i].toFixed(3)} m</title></circle>`;
 $('chart').innerHTML=html;
}
async function run(demo){
 if(busy)return;busy=true;current=null;
 lockInputs(true);
 $('result').hidden=true;$('empty').hidden=false;$('prediction').replaceChildren();
 $('status').textContent='正在训练并计算留出组指标…';
 try{
  const report=await api('/api/train',demo?{demo:true}:{csv:$('csv').value,units:$('units').value});
  current=report;$('predict-units').value=report.units;
  clearForecast();
  $('source').textContent=report.source==='synthetic-example'?'合成样例':'上传样本';
  $('samples').textContent=report.samples+' / '+report.group_count;
  $('groups').textContent=report.train_groups.length+' / '+report.test_groups.length;
  $('metrics').replaceChildren();
  for(const [name,values] of Object.entries(report.metrics)){
   const tr=document.createElement('tr');
   for(const v of [name==='linear'?'线性回归':'SVR',values.rmse_m,values.mae_m,values.r2]){const td=document.createElement('td');td.textContent=typeof v==='number'?v.toFixed(4):(v??'—');tr.append(td);}
   $('metrics').append(tr);
  }
  plot(report);if(report.test_rows)inspectRows(report);$('split').textContent='训练组：'+report.train_groups.join('、')+'；测试组：'+report.test_groups.join('、');
  $('downloads').replaceChildren(download('report.json','下载评价报告'),download('predictions.csv','下载留出预测 CSV'));
  $('artifacts').replaceChildren(...[['samples.csv','输入样本'],['linear.joblib','线性模型'],['svr.joblib','SVR 模型']].map(([f,l])=>download(f,l)));
  $('result').hidden=false;$('empty').hidden=true;
  const kind=demo?'合成样例':'上传样本';
  const count=report.test_depth_m.length;
  $('status').textContent=kind+' · 留出 '+report.test_groups.length+' 组、'+count+' 条样本。线性回归平均相差 '+report.metrics.linear.mae_m.toFixed(3)+' m，SVR 平均相差 '+report.metrics.svr.mae_m.toFixed(3)+' m。';
  $('model-source').textContent='当前模型来自'+kind+'，使用 '+report.train_groups.length+' 个训练组拟合。示例输入仅用于试算。';

 }catch(e){$('status').textContent='本次评价未完成：'+explain(e.message);}
 finally{busy=false;lockInputs(false);}
}
$('file').onchange=async()=>{
 const file=$('file').files[0];if(!file)return;
 if(file.size>1024*1024){$('status').textContent='CSV 最大 1MB，未替换输入内容。';$('file').value='';return;}
 try{$('csv').value=await file.text();$('status').textContent='已载入 '+file.name+'，请确认单位后运行评价。';}catch(e){$('status').textContent='读取失败：'+e.message;}
};
$('demo').onclick=()=>run(true);$('train').onclick=()=>run(false);
$('example').onclick=async()=>{
 try{const {csv}=await api('/api/example');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='bathymetry-synthetic-reflectance.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('status').textContent='已下载合成示例，单位为反射率 0–1；可查看字段格式后替换为自己的样本。';}
 catch(e){$('status').textContent='示例下载失败：'+e.message;}
};
function inspectRows(report){
 const picker=$('sample-pick'),chart=$('chart');
 picker.replaceChildren(...report.test_rows.map((row,i)=>new Option('CSV 第 '+(row+2)+' 行',String(i))));
 function show(){
  const i=Number(picker.value),reference=report.test_depth_m[i];
  const residual=name=>(report.predictions[name][i]-reference).toFixed(3);
  $('sample-residual').textContent='参考 '+reference.toFixed(3)+' m · 线性残差 '+residual('linear')+' m · SVR 残差 '+residual('svr')+' m';
  chart.querySelectorAll('[data-index]').forEach(dot=>dot.style.strokeWidth=Number(dot.dataset.index)===i?'3':'1');
 }
 picker.onchange=show;chart.onclick=event=>{const dot=event.target.closest('[data-index]');if(dot){picker.value=dot.dataset.index;show();}};show();
}

const predictExample='sample_id,B2,B3,B4,B8\nA,0.14,0.20,0.12,0.06\nB,0.32,0.28,0.18,0.12\nC,0.72,0.40,0.25,0.20\n';
let outputUrl=null;
function explain(text){
 const messages=[
  ['At least 10','至少需要 10 行含参考水深的样本。'],['At least 3','至少需要 3 个独立分组。'],
  ['Need at least two','留出组至少需要 2 条样本，请检查各组行数。'],['Temporal mismatch','光子与影像的采集日期相差超过一天。'],
  ['reflectance in','请检查波段单位，换算后的反射率须在 0–1 内。'],
  ['Input must contain','预测文件需要 B2、B3、B4 和 B8 四列。'],['depth_m must','参考水深须为非负米值。'],
  ['Invalid isoformat','日期请使用 YYYY-MM-DD。'],['could not convert','数值列包含空值或非数字。']
 ];
 return messages.find(([part])=>text.includes(part))?.[1] || text;
}
function lockInputs(locked){
 for(const id of ['demo','train','file','units','csv','train-source','predict-file','predict-units','model','predict-source'])$(id).disabled=locked;
 $('predict').disabled=locked || !current;
}
function clearForecast(){
 if(outputUrl){URL.revokeObjectURL(outputUrl);outputUrl=null;}
 $('prediction').replaceChildren();$('pred-preview').replaceChildren();
}

// Source columns can contain quoted commas, escaped quotes and line breaks.
function csvRows(text){
 const rows=[];let row=[],field='',quoted=false;
 for(let i=0;i<text.length;i++){
  const c=text[i];
  if(c==='"'){
   if(quoted && text[i+1]==='"'){field+='"';i++;}else quoted=!quoted;
  }else if(!quoted && c===','){row.push(field);field='';}
  else if(!quoted && (c==='\n'||c==='\r')){
   if(c==='\r' && text[i+1]==='\n')i++;
   row.push(field);rows.push(row);row=[];field='';
  }else field+=c;
 }
 if(field || row.length){row.push(field);rows.push(row);}
 return rows;
}
function previewPredictions(text){
 const [header,...rows]=csvRows(text);
 const idx=key=>header.indexOf(key);
 const table=document.createElement('table'), head=table.createTHead().insertRow();
 for(const title of ['样本','B2','B3','B4','B8','预测水深 / m','范围检查']){
  const th=document.createElement('th');th.textContent=title;head.append(th);
 }
 const body=table.createTBody();
 rows.slice(0,12).forEach((r,i)=>{
  const flags=[];
  if(r[idx('outside_training_range')]==='True')flags.push('超出训练波段范围');
  if(r[idx('negative_prediction')]==='True')flags.push('负水深预测');
  const tr=body.insertRow();
  for(const v of [r[idx('sample_id')] || i+1,...['B2','B3','B4','B8'].map(b=>r[idx(b)]),
         Number(r[idx('predicted_depth_m')]).toFixed(3),flags.join(' · ') || '范围内'])tr.insertCell().textContent=v;
 });
 $('pred-preview').replaceChildren(table);
}
$('predict').onclick=async()=>{
 if(busy || !current)return;
 const file=$('predict-file').files[0];
 const custom=$('predict-source').value==='file' || (!$('predict-source').value && file);
 if(custom && !file){$('prediction').textContent='请选择包含四个波段的 CSV。';return;}
 if(custom && file.size>1024*1024){$('prediction').textContent='CSV 最大 1 MB。';return;}
 const id=current.id, model=$('model').value, units=custom?$('predict-units').value:'reflectance';
 busy=true;lockInputs(true);clearForecast();
 $('prediction').textContent='正在计算逐行水深…';
 try{
  const result=await api('/api/predict',{id,model,csv:custom?await file.text():predictExample,units});
  const link=download('inference.csv','下载预测 CSV',id);
  if(result.model_sha256){
   const response=await fetch(link.href);
   if(!response.ok)throw Error('预测文件读取失败，请重新计算。');
   const blob=await response.blob();
   previewPredictions(await blob.text());
   outputUrl=URL.createObjectURL(blob);link.href=outputUrl;link.download='bathymetry-'+model+'-predictions.csv';
  }
  $('prediction').replaceChildren(document.createTextNode('已预测 '+result.count+' 条，超出训练波段范围 '+result.outside_training_range+' 条，负值 '+result.negative_predictions+' 条。 '),link);
 }catch(e){$('prediction').textContent='预测未完成：'+explain(e.message);}
 finally{busy=false;lockInputs(false);}
};
function showProfile(){
 const p=reefObservations.profiles[Number($('beam').value)], points=p.points;
 $('profile-title').textContent=p.beam+' · 轨迹段 '+p.segment;
 $('profile-summary').textContent=p.count.toLocaleString()+' 条观测，高度范围 '+p.low.toFixed(2)+' 至 '+p.high.toFixed(2)+' m，中位数 '+p.median.toFixed(2)+' m。';
 const left=62,right=622,top=32,base=217;
 const start=points[0][0],end=points.at(-1)[0];
 const low=Math.floor(p.low),high=Math.max(0,Math.ceil(p.high),low+1);
 const x=d=>left+(d-start)/(end-start||1)*(right-left);
 const y=h=>base-(h-low)/(high-low)*(base-top);
 let svg='';
 for(let i=0;i<=4;i++){
  const h=low+(high-low)*i/4,d=start+(end-start)*i/4;
  svg+='<path d="M62 '+y(h)+'H622" stroke="#d0dee7"/><text x="8" y="'+(y(h)+3)+'">'+h.toFixed(1)+'</text><text x="'+x(d)+'" y="234" text-anchor="middle">'+(d/1000).toFixed(2)+'</text>';
 }
 svg+='<text x="9" y="15">相对平均海平面高度 / m</text><text x="267" y="258">沿轨距离 / km</text>';
 for(const [d,h] of points)svg+='<circle cx="'+x(d)+'" cy="'+y(h)+'" r="2" fill="#176988" opacity=".64"/>';
 $('profile').innerHTML=svg+'<circle id="selected-point" r="5" fill="#c66324" stroke="white"/>';
 const input=$('point');input.max=points.length-1;input.value=Math.floor(points.length/2);
 function read(){
  const [d,h]=points[Number(input.value)];
  $('selected-point').setAttribute('cx',x(d));$('selected-point').setAttribute('cy',y(h));
  $('point-readout').textContent='沿轨 '+(d/1000).toFixed(3)+' km · 观测高度 '+h.toFixed(2)+' m';
 }
 input.oninput=read;read();
}
async function openView(view){
 for(const id of ['evaluation','forecast','observations'])$(id).hidden=id!==view;
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
 if(view==='forecast'){
  if(!current){$('model-source').textContent='先在「比较模型」中完成一次评价，即可使用训练好的模型。';}
  else if(!busy && $('predict-source').value==='example' && !outputUrl)await $('predict').onclick();
 }
}
function init(){
 document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>openView(b.dataset.view));
 if(typeof reefObservations!=='undefined' && reefObservations.profiles.length){
  for(const [i,p] of reefObservations.profiles.entries())$('beam').add(new Option(p.beam+' · 第 '+p.segment+' 段',i));
  $('beam').onchange=showProfile;showProfile();
 }else{
  $('profile-summary').textContent='无法载入本地观测剖面，请检查 web/plot-data.js。';
  $('point').disabled=$('beam').disabled=true;
 }
 $('train-source').onchange=()=>{
  const custom=$('train-source').value==='custom';
  $('custom-input').hidden=!custom;$('demo-input').hidden=custom;
  current=null;clearForecast();$('predict').disabled=true;$('result').hidden=true;$('empty').hidden=false;
  if(custom)$('status').textContent='选择标注 CSV，确认波段单位后计算。';else run(true);
 };
 $('predict-source').onchange=()=>{
  clearForecast();const custom=$('predict-source').value==='file';$('predict-upload').hidden=!custom;
  if(!custom && current)$('predict').onclick();
 };
 for(const key of ['predict-file','predict-units','model'])$(key).onchange=()=>{
  clearForecast();
  if(current && $('predict-source').value==='example')$('predict').onclick();
 };
 $('units').onchange=$('csv').oninput=()=>{
  if(current)$('status').textContent='输入已修改，当前显示上次评价。点击「计算我的样本」更新。';
 };
 const initialView = new URLSearchParams(location.search).get('view');
 if(initialView === 'observations')openView('observations');
 if(initialView === 'forecast'){
  openView('forecast');
  run(true).then(()=>{if(!$('forecast').hidden)openView('forecast');});
 }else run(true);
}
if(typeof window!=='undefined')init();
