const $ = id => document.getElementById(id);
const labels = {
  MPSNR: 'MPSNR / dB', MSSIM: 'MSSIM', CrossCorrelation: '相关系数',
  RMSE: 'RMSE', SAM_deg: 'SAM / °', ERGAS: 'ERGAS',
};
const tableMetrics = ['MPSNR', 'MSSIM', 'SAM_deg'];
const interactiveForms = ['scene-form', 'upload-form'];
let current = null;
let busy = false;
let requestToken = 0;
let bandTimer;
const sceneIndex = new Map();

function message(text) { $('message').textContent = text; }

async function api(path, options) {
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || '请求失败');
  return result;
}

function metricText(metrics, key) {
  const value = metrics[key];
  if (value == null) return key === 'MPSNR' && metrics.psnr_has_infinite_band ? '含∞波段' : '—';
  return value.toFixed(key === 'MSSIM' || key === 'CrossCorrelation' ? 4 : 3);
}

function graph(id, x, lines, low = 0, high) {
  if (!x.length) return;
  const xmin = x[0], xmax = x.at(-1);
  high ??= Math.max(1, ...lines.flatMap(line => line.values));
  let markup = '';
  for (let i = 0; i < 5; i++) {
    const value = low + (high - low) * i / 4;
    const y = 228 - 208 * i / 4;
    markup += '<path d="M53 ' + y + 'H562" stroke="#e9e3ef"/><text x="5" y="' + (y + 3) + '">' + value.toPrecision(3) + '</text>';
  }
  for (let i = 0; i < 6; i++) {
    markup += '<text x="' + (53 + 509 * i / 5) + '" y="250" text-anchor="middle">' + (xmin + (xmax - xmin) * i / 5).toPrecision(3) + '</text>';
  }
  for (const line of lines) {
    const points = x.map((value, i) => [
      (53 + (value - xmin) / (xmax - xmin || 1) * 509).toFixed(1),
      (228 - (line.values[i] - low) / (high - low || 1) * 208).toFixed(1),
    ].join(',')).join(' ');
    markup += '<polyline fill="none" stroke="' + line.color + '" stroke-width="1.8" points="' + points + '"/>';
  }
  $(id).innerHTML = markup;
}

function renderImages() {
  const {images, report, selection, error_limit: limit} = current;
  const scene = report.experiment;
  const composite = scene && $('display').value === 'composite';
  $('truth-image').src = composite ? images.composite_truth : images.truth;
  $('prediction-image').src = composite ? images.composite_prediction : images.prediction;
  $('low-panel').hidden = !scene;
  $('image-grid').classList.toggle('with-input', Boolean(scene));
  if (scene) $('low-image').src = composite ? images.composite_low : images.low;
  $('truth-meta').textContent = report.shape.slice(0, 2).join(' × ') + ' px' +
    (composite ? ' · 波段 ' + scene.rgb_bands.join(' / ') : ' · 波段 ' + selection.band);
  $('prediction-meta').textContent = report.method + ' · ×' + report.scale;
  $('low-meta').textContent = scene ? report.input_shape.slice(0, 2).join(' × ') + ' px · 像元块均值' : '';
  const sam = $('map').value === 'spectral_angle';
  $('error-image').src = sam ? images.spectral_angle : images.absolute_error;
  $('error-title').textContent = sam ? '光谱角 SAM' : '绝对误差';
  $('map-legend').textContent = sam ? '暗色 0° → 橙色 ≥30° · 灰色为未定义' :
    '波段 ' + selection.band + ' · 暗色 0 → 橙色 ≥' + limit + (scene ? ' DN' : '');
}

function renderMetrics(data) {
  const { report, selection, roi_metrics: roi, spectrum } = data;
  const table = document.createElement('table');
  const head = table.createTHead().insertRow();
  for (const name of ['重建方法', ...tableMetrics.map(key => labels[key])]) {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = name;
    head.append(th);
  }
  const body = table.createTBody();
  for (const item of [{ name: report.method, metrics: report.metrics }, ...report.comparison]) {
    const row = body.insertRow();
    const name = document.createElement('th');
    name.scope = 'row';
    name.textContent = item.name;
    row.append(name);
    if (item.method_id) {
      const show = document.createElement('button');
      show.type = 'button';
      show.textContent = '查看影像';
      show.setAttribute('aria-label', '查看' + item.name + '重建影像');
      show.onclick = () => {
        $('scene').value = report.experiment.id;
        $('experiment-scale').value = report.scale;
        $('experiment-method').value = item.method_id;
        runScene();
      };
      name.append(show);
    } else row.className = 'current-method';
    for (const key of tableMetrics) row.insertCell().textContent = metricText(item.metrics, key);
  }
  $('comparison-table').replaceChildren(table);
  $('comparison-context').textContent = report.experiment ? '全图指标 · MPSNR、MSSIM 越高越好，SAM 越低越好' : '全图指标';
  $('metrics').replaceChildren(...Object.keys(labels).map(key => {
    const tile = document.createElement('div');
    const label = document.createElement('span');
    const value = document.createElement('b');
    label.textContent = labels[key];
    value.textContent = metricText(roi, key);
    tile.append(label, value);
    return tile;
  }));
  graph('spectrum', spectrum.axis, [
    {values: spectrum.truth, color:'#684ba6'},
    {values: spectrum.prediction, color:'#b57639'},
  ], Math.min(0, ...spectrum.truth, ...spectrum.prediction), Math.max(1, ...spectrum.truth, ...spectrum.prediction));
  $('pixel-label').textContent = '行 ' + selection.row + ' / 列 ' + selection.column + ' · ' + spectrum.axis_label;
  $('band-error-unit').textContent = report.experiment ? 'DN · 当前选区' : '输入量程单位 · 当前选区';
  graph('band-error', roi.per_band_rmse.map((_, i) => i), [{values:roi.per_band_rmse,color:'#684ba6'}]);
  $('metric-note').textContent = '有效 SAM 像素 ' + roi.sam_valid_pixels + ' / ' + roi.sam_total_pixels +
    '。评价使用原始数值，显示拉伸与裁剪不影响指标。';
}

function render(data, fresh = false, syncRoi = fresh) {
  const report = data.report;
  const scene = report.experiment;
  const selection = data.selection;
  current = data;
  $('workspace').hidden = false;
  $('run-title').textContent = scene ? scene.name + ' · ' + scene.region : report.method;
  $('run-context').textContent = report.shape[2] + ' 波段 · ×' + report.scale + ' · ' +
    (scene ? scene.sensor + ' · 参考影像 ' + scene.gsd_m + ' m/像元' :
      report.source === 'synthetic-diagnostic' ? '合成诊断记录' : '已上传的重建对');
  $('display-label').hidden = !scene;
  if (fresh && scene) {
    $('display').value = 'composite';
    $('scene').value = scene.id;
    $('experiment-scale').value = report.scale;
    $('experiment-method').value = report.method_id;
    renderSource();
  }
  for (const [id, value, max] of [
    ['band',selection.band,report.shape[2]-1], ['row',selection.row,report.shape[0]-1], ['col',selection.column,report.shape[1]-1],
  ]) {
    $(id).max = max;
    $(id).value = value;
  }
  $('band-number').textContent = selection.band;
  if (syncRoi) {
    for (const [i,id] of ['roi-row','roi-col','roi-height','roi-width'].entries()) $(id).value = selection.roi[i];
  }
  $('export-link').href = '/api/export?id=' + report.id;
  $('export-cube').href = '/api/cube?kind=prediction&id=' + report.id;
  $('export-low').hidden = !scene;
  if (scene) $('export-low').href = '/api/cube?kind=low-resolution&id=' + report.id;
  renderImages();
  renderMetrics(data);
}

function setBusy(value) {
  busy = value;
  for (const form of interactiveForms) {
    for (const field of $(form).elements) field.disabled = value || (form === 'scene-form' && !sceneIndex.size);
  }
}

async function analyze(path, payload) {
  if (busy) return;
  ++requestToken;
  setBusy(true);
  message(path === '/api/experiment' ? '正在读取航测影像并运行重建…' : '正在计算评价指标…');
  try {
    render(await api(path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}), true);
    message('');
    history();
  } catch (error) {
    message(error.message);
  } finally {
    setBusy(false);
  }
}

function runScene() {
  return analyze('/api/experiment', {scene:$('scene').value, scale:Number($('experiment-scale').value), method:$('experiment-method').value});
}

function renderSource() {
  const scene = sceneIndex.get($('scene').value);
  $('scene-source').hidden = !scene;
  if (!scene) return;
  $('scene-credit').textContent = scene.credit + ' · ' + scene.license;
  $('archive-link').href = scene.archive;
  $('original-link').href = scene.original;
  $('license-link').href = scene.license_url;
}

async function prepareScenes() {
  try {
    const {scenes, scales, methods} = await api('/api/scenes');
    if (!scenes.length) throw new Error('当前没有本地航测样本。仍可评价自己的重建结果。');
    for (const scene of scenes) sceneIndex.set(scene.id, scene);
    $('scene').replaceChildren(...scenes.map(scene => new Option(scene.name + ' · ' + scene.region, scene.id)));
    $('experiment-scale').replaceChildren(...scales.map(scale => new Option('×' + scale, scale)));
    $('experiment-method').replaceChildren(...methods.map(method => new Option(method.name, method.id)));
    $('experiment-scale').value = 4;
    $('experiment-method').value = 'bicubic';
    $('experiment-button').disabled = false;
    renderSource();
    await runScene();
  } catch (error) { message(error.message); }
}

async function select(roi) {
  if (!current || busy) return;
  const token = ++requestToken;
  const query = new URLSearchParams({
    id: current.report.id, band: $('band').value, row: $('row').value, column: $('col').value,
    roi: JSON.stringify(roi || current.selection.roi),
  });
  try {
    const data = await api('/api/view?' + query);
    if (token === requestToken) { render(data, false, Boolean(roi)); message(''); }
  } catch (error) {
    if (token === requestToken) message(error.message);
  }
}

async function array64(file) {
  if (file.size > 16 * 1024 * 1024) throw new Error('单个 NPY 文件最大 16 MB');
  const bytes = new Uint8Array(await file.arrayBuffer());
  let encoded = '';
  for (let i = 0; i < bytes.length; i += 8192) encoded += String.fromCharCode(...bytes.subarray(i,i+8192));
  return btoa(encoded);
}

async function history() {
  try {
    const rows = await api('/api/history');
    $('history').replaceChildren(...rows.map(row => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = [row.scene_name, row.method, '×' + row.scale].filter(Boolean).join(' · ');
      button.onclick = async () => {
        if (busy) return;
        const token = ++requestToken;
        try {
          const view = await api('/api/view?id=' + row.id);
          if (token === requestToken) render(view, true);
        } catch (error) { if (token === requestToken) message(error.message); }
      };
      return button;
    }));
  } catch {}
}

$('scene-form').onsubmit = event => { event.preventDefault(); runScene(); };
$('scene').onchange = renderSource;
$('map').onchange = $('display').onchange = () => { if (current) renderImages(); };
$('band').oninput = () => {
  $('display').value = 'band';
  $('band-number').textContent = $('band').value;
  clearTimeout(bandTimer);
  bandTimer = setTimeout(() => select(), 180);
};
$('pixel-button').onclick = () => select();
$('roi-button').onclick = () => select(['roi-row','roi-col','roi-height','roi-width'].map(id => Number($(id).value)));
$('roi-reset').onclick = () => current && select([0,0,...current.report.shape.slice(0,2)]);
for (const id of ['truth-image','prediction-image','error-image']) $(id).onclick = event => {
  if (!current || busy) return;
  const box = event.currentTarget.getBoundingClientRect();
  const [h,w] = current.report.shape;
  $('row').value = Math.min(h-1, Math.max(0, Math.floor((event.clientY-box.top)*h/box.height)));
  $('col').value = Math.min(w-1, Math.max(0, Math.floor((event.clientX-box.left)*w/box.width)));
  document.querySelector('.inspection').open = true;
  select();
};
$('upload-form').onsubmit = async event => {
  event.preventDefault();
  if (busy) return;
  for (const id of ['truth','prediction']) if (!$(id).files.length) return;
  const wavelengths = $('wavelengths').value.trim();
  try {
    const [truth, prediction] = await Promise.all(['truth','prediction'].map(id => array64($(id).files[0])));
    await analyze('/api/analyze', {
      truth, prediction, data_range:Number($('data-range').value), scale:Number($('scale').value), method:$('method').value,
      ...(wavelengths ? {wavelengths:wavelengths.split(/[,，]/).map(Number)} : {}),
    });
  } catch (error) { message(error.message); }
};
$('export-view').onclick = () => {
  if (!current) return;
  const {images, ...report} = current;
  const file = new Blob([JSON.stringify(report,null,2)],{type:'application/json'});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(file);
  link.download = 'spectral-selection-report.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href),1000);
};
history();
prepareScenes();
