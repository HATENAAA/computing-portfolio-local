const byId = id => document.getElementById(id);
const form = byId('model-form');
const sample = byId('sample');
const upload = byId('model-image');
const run = byId('run-model');
const message = byId('model-message');
const result = byId('model-result');
let examples = [];
let report = null;
let generation = 0;
let configured = false;
let running = false;

function clearResult() {
  generation++;
  report = null;
  byId('export-model').disabled = true;
  result.replaceChildren();
  byId('model-time').textContent = '';
  message.textContent = '';
}

function imagePanel(media, text) {
  const panel = document.createElement('figure');
  const caption = document.createElement('figcaption');
  caption.textContent = text;
  panel.append(media, caption);
  return panel;
}

function display(data, example) {
  const image = new Image();
  image.src = data.overlay;
  image.alt = '原图及模型预测的火焰框';
  image.className = 'model-result-image';
  const views = document.createElement('div');
  views.className = 'model-views';
  views.append(imagePanel(image, '模型预测'));
  const caption = document.createElement('p');
  caption.textContent = '模型检出 ' + data.model.boxes.length + ' 个火焰框 · 颜色／边缘规则' +
    (data.baseline.detected ? '命中' : '未命中') + ' · 规则颜色区域占比 ' +
    (data.baseline.area_ratio * 100).toFixed(2) + '%';
  result.replaceChildren(views, caption);
  if (example) {
    const label = '原始标注 · ' + example.group + ' 第 ' + example.frame + ' 帧 · ' + example.boxes.length + ' 个框';
    const canvas = document.createElement('canvas');
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', label);
    views.append(imagePanel(canvas, label));
    const original = new Image();
    original.onload = () => {
      canvas.width = original.naturalWidth;
      canvas.height = original.naturalHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(original, 0, 0);
      ctx.strokeStyle = '#59b8ff';
      ctx.lineWidth = Math.max(2, canvas.width / 300);
      for (const box of example.boxes) ctx.strokeRect(...box);
    };
    original.onerror = () => { canvas.replaceWith(document.createTextNode('无法读取原始标注图像')); };
    original.src = '/static/furg/' + example.file;
  }
  if (data.model.boxes.length) {
    const table = document.createElement('table');
    table.className = 'research-table';
    const header = table.createTHead().insertRow();
    for (const title of ['类别', '分数', '左上角 (px)', '宽 × 高 (px)']) {
      const th = document.createElement('th');
      th.textContent = title;
      header.append(th);
    }
    const body = table.createTBody();
    for (const box of data.model.boxes) {
      const row = body.insertRow();
      for (const value of [box.label, box.confidence.toFixed(3), [box.x,box.y].map(Math.round).join(', '),
          [box.width,box.height].map(Math.round).join(' × ')]) row.insertCell().textContent = value;
    }
    const scroll = document.createElement('div');
    scroll.className = 'fw-scroll';
    scroll.append(table);
    result.append(scroll);
  }
  byId('model-time').textContent = data.model.elapsed_ms.toFixed(1) + ' ms · CPU';
  const {overlay, ...record} = data;
  report = {...record, input: example || {file: upload.files[0]?.name}};
  byId('export-model').disabled = false;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (running || !configured) return;
  clearResult();
  const version = generation;
  running = true;
  run.disabled = true;
  message.textContent = '正在运行模型与规则…';
  const example = examples.find(item => item.file === sample.value);
  try {
    let file = upload.files[0];
    if (example) {
      const response = await fetch('/static/furg/' + example.file);
      if (!response.ok) throw Error('读取内置样本失败。');
      file = await response.blob();
    }
    if (!file) throw Error('请选择图像。');
    if (file.size > 10 * 1024 * 1024) throw Error('图像不能超过 10 MB。');
    const body = new FormData();
    body.append('file', file, example ? example.file : file.name);
    body.append('confidence', byId('model-confidence').value);
    body.append('iou', byId('model-iou').value);
    const response = await fetch('/api/model/analyze', {method:'POST', body});
    const data = await response.json();
    if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : '推理失败，请检查输入。');
    if (version === generation) {
      display(data, example);
      message.textContent = '对照完成';
    }
  } catch (error) {
    if (version === generation) message.textContent = error.message;
  } finally {
    running = false;
    run.disabled = !configured;
  }
});

form.addEventListener('input', clearResult);
sample.addEventListener('change', () => {
  const custom = sample.value === 'custom';
  byId('upload-label').hidden = !custom;
  upload.disabled = !custom;
  upload.required = custom;
});
byId('export-model').onclick = () => {
  if (!report) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)], {type:'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'firewatch-model-comparison.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

async function initialize() {
  try {
    const [status, catalog] = await Promise.all(['/api/model/status', '/static/furg/catalog.json'].map(async url => {
      const response = await fetch(url);
      if (!response.ok) throw Error('读取模型或样本配置失败。');
      return response.json();
    }));
    examples = catalog.examples;
    for (const item of examples) sample.add(new Option(item.title + ' · ' + item.group, item.file));
    sample.add(new Option('上传自己的图像', 'custom'));
    const params = new URLSearchParams(location.search);
    const requested = examples.find(item => item.file === params.get('sample'));
    if (requested) {
      sample.value = requested.file;
      const confidence = Number(params.get('confidence'));
      if (params.has('confidence') && Number.isFinite(confidence) && confidence >= 0 && confidence <= 1) {
        byId('model-confidence').value = confidence.toFixed(2);
      }
      const iou = Number(params.get('iou'));
      if (params.has('iou') && Number.isFinite(iou) && iou >= 0 && iou <= 1) {
        byId('model-iou').value = iou.toFixed(2);
      }
    }
    sample.disabled = false;
    upload.disabled = true;
    configured = status.configured;
    byId('model-status').textContent = configured ? '本机检测模型已就绪 · 检测类别 ' +
      status.target_classes.map(id => status.class_names[id]).join(' / ') : status.message;
    run.disabled = !configured;
    if (configured) form.requestSubmit();
  } catch (error) {
    byId('model-status').textContent = error.message;
  }
}
initialize();
