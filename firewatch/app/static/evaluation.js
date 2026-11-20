const $=id=>document.getElementById(id),percent=n=>(n*100).toFixed(1)+'%';
function cell(tr,text){const td=document.createElement('td');td.textContent=text;tr.append(td)}
const form = $('evaluation-form');
const source = $('dataset-source');
const file = form.elements.file;

function resetInput() {
  const custom = source.value === 'upload';
  file.disabled = !custom;
  file.required = custom;
  $('dataset-upload').hidden = !custom;
  $('dataset-note').hidden = custom;
  $('eval-result').hidden = true;
  $('eval-status').textContent = custom ? (file.files.length ? '已选择标注包' : '请选择标注包') : '内置评测集已就绪';
}
form.addEventListener('change', resetInput);
form.addEventListener('submit', async event => {
  event.preventDefault();
  if ($('eval-run').disabled) return;
  const builtin = source.value === 'furg';
  const body = new FormData(form);
  source.disabled = file.disabled = $('eval-run').disabled = true;
  $('eval-result').hidden = true;
  $('eval-status').textContent = '正在核对标注并逐帧运行检测…';
  try {
    if (builtin) {
      const archive = await fetch('/static/furg/furg-boxes.zip');
      if (!archive.ok) throw Error('内置标注包读取失败');
      body.set('file', await archive.blob(), 'furg-boxes.zip');
    }
    const response = await fetch('/api/evaluations', {method:'POST', body});
    const data = await response.json();
    if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : '评测失败');
    render(data);
    const hasMiss = builtin && data.test.operating.errors.some(
      error => error.type === 'missed' && error.image === 'house6-00384');
    $('eval-missed-example').hidden = !hasMiss;
    if (hasMiss) {
      const query = new URLSearchParams({sample: 'house6-00384.jpg', confidence: data.selected_threshold, iou: data.parameters.nms_iou});
      $('eval-missed-link').href = '/model?' + query;
    }
    $('eval-status').textContent = '评测完成 · ' + (builtin ? 'FURG' : body.get('file').name) +
      ' · 验证集选定阈值 ' + data.selected_threshold;
  } catch (error) {
    $('eval-status').textContent = error.message;
  } finally {
    $('eval-run').disabled = source.disabled = false;
    file.disabled = builtin;
  }
});
function render(d){$('eval-target').textContent=' / '+d.target_label;const m=d.test.operating;$('eval-result').hidden=false;$('eval-download').href='/api/evaluations/'+d.id;$('eval-metrics').replaceChildren();for(const [name,value] of [['AP50',percent(d.test.ap50)],['Precision',percent(m.precision)],['Recall',percent(m.recall)],['F1',percent(m.f1)],['TP / FP / FN',m.tp+' / '+m.fp+' / '+m.fn]]){const box=document.createElement('div'),title=document.createElement('span'),b=document.createElement('b');title.textContent=name;b.textContent=value;box.append(title,b);$('eval-metrics').append(box)}$('eval-sweep').replaceChildren();for(const row of d.validation_sweep){const tr=document.createElement('tr');if(row.threshold===d.selected_threshold)tr.className='selected-threshold';[row.threshold,percent(row.precision),percent(row.recall),percent(row.f1)].forEach(v=>cell(tr,v));$('eval-sweep').append(tr)}const labels={missed:'漏检',duplicate:'重复检测',localization:'定位偏差',background:'背景误检'};$('eval-errors').replaceChildren();for(const x of m.errors.slice(0,300)){const tr=document.createElement('tr');[x.image,labels[x.type],x.confidence?.toFixed(3)??'—',x.best_iou?.toFixed(3)??'—'].forEach(v=>cell(tr,v));$('eval-errors').append(tr)}$('error-count').textContent=m.errors.length+' 条（页面最多显示 300 条）';const svg=$('eval-curve'),ns='http://www.w3.org/2000/svg';svg.replaceChildren();function el(name,attrs){const n=document.createElementNS(ns,name);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);svg.append(n);return n}for(let i=0;i<=4;i++){const x=40+100*i,y=230-50*i;el('path',{d:`M ${x} 30 V 230 M 40 ${y} H 440`,stroke:'#3a4653','stroke-width':1});const label=(i/4).toFixed(2);el('text',{x,y:252,'text-anchor':'middle',fill:'#b3c0ce','font-size':11}).textContent=label;el('text',{x:34,y:y+4,'text-anchor':'end',fill:'#b3c0ce','font-size':11}).textContent=label}const points=d.test.curve.map(p=>(40+p.recall*400)+','+(230-p.precision*200)).join(' ');el('polyline',{points,fill:'none',stroke:'#ffb565','stroke-width':2});$('eval-provenance').textContent=d.scope+' 模型 SHA256 '+d.model.model_sha256+' · 数据集 '+d.dataset_sha256;}
