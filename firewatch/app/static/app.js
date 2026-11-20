const $ = id => document.getElementById(id);
const fileInput = $('file');
const form = $('analyze-form');
const sampleButton = $('sample-image');
const openButton = document.querySelector('[data-open-image]');
const layerButtons = Array.from(document.querySelectorAll('[data-view]'));
const layerNames = {original: '原始图像', overlay: '候选区域叠加', mask: '候选区域掩膜'};
const percent = n => (n * 100).toFixed(2) + '%';
let current = null;
let previewUrl = null;
let zoom = 1;
let layer = 'overlay';
let busy = false;

function setBusy(value) {
  busy = value;
  fileInput.disabled = openButton.disabled = sampleButton.disabled = value;
  $('submit').disabled = value || !fileInput.files.length;
  form.setAttribute('aria-busy', String(value));
}
function syncZoom() {
  const active = current && layer !== 'compare';
  $('zoom-out').disabled = !active || zoom <= 1;
  $('zoom-in').disabled = !active || zoom >= 3;
  $('zoom-reset').disabled = !active || zoom === 1;
  $('zoom-label').textContent = layer === 'compare' ? '适应' : Math.round(zoom*100) + '%';
}
function setZoom(value) {
  if (!current || layer === 'compare') return;
  zoom = Math.max(1, Math.min(3, value));
  const scroll = $('single-view');
  scroll.style.setProperty('--zoom', zoom);
  if (zoom === 1) scroll.scrollTo(0, 0);
  syncZoom();
}
$('zoom-in').onclick = () => setZoom(zoom + .25);
$('zoom-out').onclick = () => setZoom(zoom - .25);
$('zoom-reset').onclick = () => setZoom(1);

function setLayer(view) {
  if (!current) return;
  layer = view;
  const compare = view === 'compare';
  $('single-view').hidden = compare;
  $('compare-view').hidden = !compare;
  if (compare) {
    $('compare-original').src = current.assets.original;
    $('compare-overlay').src = current.assets.overlay;
  } else {
    $('result-image').src = current.assets[view];
    $('result-image').alt = layerNames[view];
  }
  layerButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
  syncZoom();
}
layerButtons.forEach(button => button.onclick = () => setLayer(button.dataset.view));
openButton.onclick = () => fileInput.click();

function setFilename(name) {
  const label = $('current-file');
  label.textContent = label.title = name;
}
function releasePreview() {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  $('input-preview').removeAttribute('src');
  $('input-frame').hidden = true;
}
function preview() {
  const file = fileInput.files[0];
  if (!file || busy) return;
  releasePreview();
  previewUrl = URL.createObjectURL(file);
  $('input-preview').src = previewUrl;
  $('input-frame').hidden = false;
  $('empty').hidden = true;
  $('result').hidden = true;
  current = null;
  layer = 'overlay';
  zoom = 1;
  $('export').hidden = true;
  setFilename(file.name);
  $('canvas-meta').textContent = '用户图像';
  $('analysis-state').textContent = '待检测';
  $('status').textContent = '已打开图像 · 调整参数后运行检测';
  for (const id of ['verdict', 'area', 'elapsed']) $(id).textContent = '—';
  delete $('verdict').dataset.detected;
  $('methods').replaceChildren();
  document.querySelector('.measurement-note').textContent = '运行检测后显示算子明细。';
  document.querySelectorAll('[data-run-id]').forEach(button => button.removeAttribute('aria-current'));
  layerButtons.forEach(button => {
    button.disabled = true;
    button.setAttribute('aria-pressed', String(button.dataset.view === layer));
  });
  syncZoom();
  setBusy(false);
}
fileInput.addEventListener('change', preview);
$('brightness').addEventListener('input', event => $('brightness-value').value = event.target.value);
for (const event of ['dragover', 'dragleave', 'drop']) $('drop').addEventListener(event, e => {
  e.preventDefault();
  $('drop').classList.toggle('drag', !busy && event === 'dragover');
  if (busy || event !== 'drop' || !e.dataTransfer.files.length) return;
  const files = new DataTransfer();
  files.items.add(e.dataTransfer.files[0]);
  fileInput.files = files.files;
  preview();
});

function show(result) {
  current = result;
  releasePreview();
  setFilename(result.filename);
  $('canvas-meta').textContent = result.width + ' × ' + result.height + ' px · ' + result.algorithm;
  $('empty').hidden = true;
  $('result').hidden = false;
  const native = result.algorithm === 'cpp-region-motion-v1';
  $('method-heading').textContent = native ? '局部纹理比' : '边缘邻域命中率';
  document.querySelector('.measurement-note').textContent = native ?
    '静态图像提供候选区域。视频另外检查区域内部变化。' :
    '命中率是边缘邻域内特征支持像素的占比。';
  $('analysis-state').textContent = '检测完成';
  $('verdict').textContent = result.detected ? '疑似火焰' : '未触发规则';
  $('verdict').dataset.detected = String(result.detected);
  $('area').textContent = percent(result.area_ratio);
  $('elapsed').textContent = result.elapsed_ms + ' ms';
  $('export').href = '/api/runs/' + result.id + '/report';
  $('export').hidden = false;
  $('methods').replaceChildren(...result.methods.map(method => {
    const row = document.createElement('tr');
    for (const value of [method.method, percent(method.edge_color_ratio), method.detected ? '疑似火焰' : '未触发']) {
      row.insertCell().textContent = value;
    }
    return row;
  }));
  document.querySelectorAll('[data-run-id]').forEach(button => {
    if (button.dataset.runId === result.id) button.setAttribute('aria-current', 'true');
    else button.removeAttribute('aria-current');
  });
  layerButtons.forEach(button => button.disabled = false);
  setLayer('overlay');
  setZoom(1);
}

async function updateHistory() {
  const response = await fetch('/api/runs');
  if (!response.ok) throw Error('读取历史记录失败');
  const rows = await response.json();
  if (!rows.length) { $('history-list').textContent = '暂无历史结果'; return; }
  const files = new Map();
  for (const run of rows) {
    if (!files.has(run.filename)) files.set(run.filename, []);
    files.get(run.filename).push(run);
  }
  const list = document.createDocumentFragment();
  for (const [name, runs] of files) {
    const group = document.createElement('details');
    const label = document.createElement('summary');
    label.textContent = name + ' · ' + runs.length + ' 次';
    group.append(label);
    for (const run of runs) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = new Date(run.created).toLocaleString() + (run.detected ? ' · 疑似火焰' : ' · 未触发');
      button.dataset.runId = run.id;
      if (run.id === current?.id) button.setAttribute('aria-current', 'true');
      button.onclick = () => {
        if (busy) return;
        fileInput.value = '';
        setBusy(false);
        show(run);
        $('status').textContent = '已打开历史结果 · 重新计算前请打开源图像';
      };
      group.append(button);
    }
    list.append(group);
  }
  $('history-list').replaceChildren(list);
}
function reportError(error) { $('status').textContent = error.message || '检测失败'; }

async function analyze() {
  const file = fileInput.files[0];
  if (busy || !file || !form.reportValidity()) return;
  if (file.size > 10*1024*1024) {
    $('status').textContent = '图像不能超过 10 MB。';
    return;
  }
  const body = new FormData(form);
  body.set('file', file);
  const native = $('image-engine').value === 'cpp';
  setBusy(true);
  $('status').textContent = '正在检测…';
  $('analysis-state').textContent = '处理中';
  try {
    const response = await fetch(native ? '/api/native/analyze' : '/api/analyze', {method: 'POST', body});
    const result = await response.json();
    if (!response.ok) throw Error(typeof result.detail === 'string' ? result.detail : '参数无效，请检查输入');
    show(result);
    $('status').textContent = '检测完成 · 结果已保存';
    await updateHistory().catch(reportError);
  } catch (error) {
    $('analysis-state').textContent = '检测失败';
    reportError(error);
  } finally {
    setBusy(false);
  }
}
form.addEventListener('submit', event => { event.preventDefault(); analyze(); });

const engine = $('image-engine');
function syncEngine() {
  const native = engine.value === 'cpp';
  $('edge-setting').hidden = native;
  form.elements.edge_ratio.disabled = native;
}
engine.addEventListener('change', syncEngine);
syncEngine();

sampleButton.onclick = async () => {
  if (busy) return;
  setBusy(true);
  try {
    const response = await fetch('/static/furg-Car1-7s.png');
    if (!response.ok) throw Error('样帧读取失败，请重试或打开自己的图像。');
    const files = new DataTransfer();
    files.items.add(new File([await response.blob()], 'FURG-Car1-7s.png', {type: 'image/png'}));
    fileInput.files = files.files;
  } catch (error) {
    reportError(error);
    return;
  } finally {
    setBusy(false);
  }
  preview();
  analyze();
};
updateHistory().catch(reportError);
