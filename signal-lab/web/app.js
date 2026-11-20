const $=id=>document.getElementById(id);let busy=false,current=null;
function message(v){$('message').textContent=v}
async function api(url,options){const r=await fetch(url,options),v=await r.json();if(!r.ok)throw new Error(v.error||'请求失败');return v}
function config(){const v={};for(const id of ['waveform','filter','band'])v[id]=$(id).value;for(const id of ['sampling_hz','samples','frequency','second_frequency','noise_std','order','ripple_db','cutoff_hz','high_hz','discard','segment_length','overlap'])v[id]=Number($(id).value);return v}
function polyline(xs,ys,xmin,xmax,ymin,ymax,w,h,color){return '<polyline fill="none" stroke="'+color+'" stroke-width="1.3" points="'+xs.map((x,i)=>(48+(w-66)*(x-xmin)/(xmax-xmin||1)).toFixed(2)+','+(h-28-(h-48)*(ys[i]-ymin)/(ymax-ymin||1)).toFixed(2)).join(' ')+'"/>'}
function chart(id,x,lines,{floor=null,cap=null,xy=false}={}){const svg=$(id),[,,w,h]=svg.getAttribute('viewBox').split(' ').map(Number);if(!x?.length||lines.some(l=>!l.values)){svg.innerHTML='<text x="30" y="70">CSV原输出未声明滤波器，因此不推断理论频响。</text>';return}let xmin=xy?Math.min(...x):x[0],xmax=xy?Math.max(...x):x.at(-1);if(xmin===xmax){xmin-=1;xmax+=1;}let ymin=floor??Math.min(...lines.flatMap(l=>l.values)),ymax=cap??Math.max(...lines.flatMap(l=>l.values));if(ymax-ymin<1e-12){ymax+=1;ymin-=1}let html='';for(let i=0;i<5;i++){const v=ymin+(ymax-ymin)*i/4,y=h-28-(h-48)*i/4;html+='<path d="M48 '+y+'H'+(w-18)+'" stroke="#1c3443"/><text x="5" y="'+(y+3)+'">'+v.toPrecision(3)+'</text>'}for(let i=0;i<6;i++){const xx=48+(w-66)*i/5;html+='<path d="M'+xx+' 20V'+(h-28)+'" stroke="#1c3443"/><text x="'+xx+'" y="'+(h-8)+'" text-anchor="middle">'+(xmin+(xmax-xmin)*i/5).toPrecision(3)+'</text>'}for(const l of lines)html+=polyline(x,l.values.map(y=>Math.max(ymin,Math.min(ymax,y))),xmin,xmax,ymin,ymax,w,h,l.color);svg.innerHTML=html}
function render(r){renderTransfer(r.transfer);const preserveScale=Boolean(current);current=r;initDisplay(r,preserveScale);$('read-fs').textContent=fmt(r.sampling_hz);$('read-nyquist').textContent=r.nyquist_hz.toFixed(1);$('read-bin').textContent=r.bin_width_hz.toFixed(3);$('read-peak').textContent=r.peak_hz.toFixed(1);drawScope();chart('fft-chart',r.plot.frequency,[{values:r.plot.input_spectrum,color:'var(--ch1)'},{values:r.plot.filtered_spectrum,color:'var(--ch2)'}],{floor:0});chart('response-chart',r.plot.response_frequency,[{values:r.plot.response_db,color:'var(--ch2)'}],{floor:-100,cap:5});$('filter-type').textContent=r.filter?r.filter.family+' · '+r.filter.band+' · 阶数 '+r.filter.order:'外部CSV输出';$('source-type').textContent=(r.source==='synthetic'?'合成信号':isRecording(r)?'PhysioNet 实录':'导入 CSV')+' · 保留 '+r.samples+' 点 · 丢弃 '+r.discarded_samples+' 点';const table=document.createElement('table'),head=document.createElement('tr');for(const s of ['请求 Hz','FFT频点 Hz','输入幅值','输出幅值','测得增益 dB','理论增益 dB','差值 dB']){const th=document.createElement('th');th.textContent=s;head.append(th)}table.append(head);for(const row of r.tones){const tr=document.createElement('tr');for(const key of ['requested_hz','bin_hz','input_amplitude','filtered_amplitude','gain_db','theoretical_gain_db','gain_difference_db']){const td=document.createElement('td');td.textContent=row[key]==null?'未定义':row[key].toFixed(4);tr.append(td)}table.append(tr)}$('tone-table').replaceChildren(table);$('measurement-note').textContent='频点幅值取最近FFT频点；非整数周期会产生谱泄漏。输入低于频谱主峰1e-6（绝对下限1e-12）时增益不可测量。指标使用全部保留样本，不替代VI或仪器实测。';if(r.power_validation){const v=r.power_validation.input;$('measurement-note').textContent+=' PSD功率守恒相对误差 '+(v.relative_error==null?'未定义':v.relative_error.toExponential(2))+'；等效噪声带宽 '+v.equivalent_noise_bandwidth_hz.toFixed(3)+' Hz。';}if(r.stationary_tone_fit){$('measurement-note').textContent+=' 声明频率的联合拟合：'+r.stationary_tone_fit.tones.map(t=>t.frequency_hz.toFixed(2)+' Hz / '+(t.gain_db==null?'不可测':t.gain_db.toFixed(3)+' dB')).join('；')+'。拟合假设为平稳正弦，详细幅值、相位与残差见报告。';}if(r.transfer){const v=r.transfer;$('measurement-note').textContent+=' H1频响：'+v.segments+'段，可靠频点'+v.reliable.filter(Boolean).length+'/'+v.reliable.length+'；增益、相位、相干性与屏蔽原因见完整报告。';}$('alias-note').textContent=r.aliases.filter(a=>a.above_nyquist).map(a=>a.requested_hz.toFixed(1)+' Hz ≥ Nyquist，折叠到 '+a.folded_hz.toFixed(1)+' Hz。').join(' ');$('hash').textContent='输入 SHA256 '+r.source_sha256+' · 实现 SHA256 '+r.implementation_sha256;for(const [id,path] of [['report-link','export'],['csv-link','csv']]){$(id).hidden=false;$(id).href='/api/'+path+'?id='+r.id}}
function renderTransfer(r) {
 const panel=$('transfer-panel');panel.hidden=!r;if(!r)return;
 const reference=r.reference_gain_db;
 $('transfer-note').textContent=r.segments+' 段 · 窗长 '+r.nperseg+' · 重叠 '+r.overlap+' · '+r.reliable.filter(Boolean).length+' / '+r.frequency_hz.length+' 个有效频点。灰底表示低激励、低相干、样本段不足或非平稳检查未通过。'+(reference?'增益实线为 H1 估计，虚线为理论响应。':'')+r.warnings.join('；');
 for(const [id,values] of [['transfer-gain',r.gain_db],['transfer-phase',r.phase_deg],['transfer-coherence',r.coherence]]) {
  const svg=$(id), finite=values.filter(Number.isFinite);
  if(!finite.length){svg.innerHTML='<text x="20" y="80">暂无有效频点，请检查激励与窗长。</text>';continue;}
  const referenceCurve=id==='transfer-gain'&&reference;
  let low=Math.min(...finite),high=Math.max(...finite);
  if(high-low<1e-9){low-=1;high+=1;}
  const x=i=>48+414*r.frequency_hz[i]/r.frequency_hz.at(-1);
  const y=v=>220-190*(v-low)/(high-low);
  const curve=series=>{
   let active=false,path='';
   series.forEach((v,i)=>{if(!Number.isFinite(v)){active=false;return;}path+=(active?'L':'M')+x(i).toFixed(2)+','+y(v).toFixed(2);active=true;});return path;
  };
  let shade='',first=-1;
  for(let i=0;i<=r.reliable.length;i++){
   const excluded=i<r.reliable.length&&!r.reliable[i];
   if(excluded&&first<0)first=i;
   if(!excluded&&first>=0){const half=207/(r.frequency_hz.length-1),left=Math.max(48,x(first)-half),right=Math.min(462,x(i-1)+half);shade+='<rect x="'+left+'" y="30" width="'+(right-left)+'" height="190" fill="#737780" opacity=".22"/>';first=-1;}
  }
  const clip='bounds-'+id;
  svg.innerHTML='<defs><clipPath id="'+clip+'"><rect x="48" y="30" width="414" height="190"/></clipPath></defs>'+shade+'<path d="M48 30V220H462" stroke="#73808a" fill="none"/><g clip-path="url(#'+clip+')">'+(referenceCurve?'<path d="'+curve(referenceCurve)+'" stroke="var(--ch2)" stroke-dasharray="6 4" fill="none"/>':'')+'<path d="'+curve(values)+'" stroke="var(--ch1)" fill="none"/></g><text x="3" y="35">'+high.toPrecision(3)+'</text><text x="3" y="220">'+low.toPrecision(3)+'</text><text x="150" y="249">频率 / Hz · 0–'+r.frequency_hz.at(-1).toFixed(1)+'</text>';
 }
}


const fields = ['waveform','sampling_hz','samples','frequency','second_frequency','noise_std','filter','band','order','ripple_db','cutoff_hz','high_hz','discard','segment_length','overlap'];
const controls = $('controls');
const presetButtons = Array.from(document.querySelectorAll('[data-preset]'));
const sampleHash = '3d7c623995741665f8baf41eb7acdd459c22eaa7bba114d405fd0c9ede9dc12c';
const labels = {filter:'双频滤波',alias:'采样混叠',h1:'测量系统频响',ecg:'分析实录波形',upload:'导入 CSV'};
const presets = {
  filter: {},
  alias: {waveform:'sine', frequency:750, band:'highpass', cutoff_hz:100},
  h1: {waveform:'noise', noise_std:0.5, samples:16384, segment_length:1024},
  ecg: {sampling_hz:360, samples:3600, frequency:5, second_frequency:40, cutoff_hz:35, discard:0, segment_length:256},
  upload: {discard:0}
};
let task = 'filter', selectedFile = null, hasOutput = false;
let fileRevision = 0;
const fmt = (n, digits=2) => Number(n.toFixed(digits)).toString();
function isRecording(r) { return r.source_sha256 === sampleHash; }
function sourceIsFile() { return task === 'ecg' || task === 'upload'; }
const scopeChannels = [
  {button: $('channel-input'), legend: $('legend-input'), key: 'input', color: 'var(--ch1)'},
  {button: $('channel-output'), legend: $('legend-output'), key: 'filtered', color: 'var(--ch2)'},
];
const timeDial = $('scale-time');
const verticalDial = $('scale-voltage');
const edge = $('trigger-edge');
let timeScales = [];
let verticalScales = [];
let fittedTime = 0;
let verticalAuto = true;

function niceScales(reference, lower, upper) {
  const decade = Math.floor(Math.log10(reference));
  return Array.from({length: upper-lower+1}, (_, i) => decade+lower+i)
    .flatMap(power => [1, 2, 5].map(size => size * 10**power));
}
function unitNumber(value) {
  const magnitude = Math.abs(value);
  return magnitude && (magnitude < .001 || magnitude >= 10000) ?
    value.toExponential(1) : Number(value.toPrecision(4)).toString();
}
function timeUnit(seconds) {
  if (seconds >= 1) return [1, 's'];
  if (seconds >= 1e-3) return [1e3, 'ms'];
  if (seconds >= 1e-6) return [1e6, 'µs'];
  return [1e9, 'ns'];
}
function readDial(input, output, text) {
  input.setAttribute('aria-valuetext', text);
  input.parentElement.style.setProperty('--dial-turn', (-135 + 270 * Number(input.value) / Math.max(1, Number(input.max))) + 'deg');
  $(output).textContent = text;
}
function scaleIndex(scales, value) {
  const index = scales.findIndex(step => step >= value*(1-1e-7));
  return index < 0 ? scales.length-1 : index;
}
function initDisplay(report, preserveScale) {
  const preferredTime = timeScales[Number(timeDial.value)];
  const preferredVertical = verticalScales[Number(verticalDial.value)];
  const {time, input, filtered} = report.plot;
  const duration = time.at(-1)-time[0];
  const target = Math.min(duration, isRecording(report) ? 1 : .1)/10;
  const steps = niceScales(target, -3, Math.max(1, Math.ceil(Math.log10(duration/10/target))))
    .filter(step => step*10 >= time[1]-time[0]);
  timeScales = steps.slice(0, scaleIndex(steps,duration/10)+1);
  fittedTime = scaleIndex(timeScales,target);
  timeDial.max = timeScales.length-1;
  timeDial.value = preserveScale ? scaleIndex(timeScales,preferredTime) : fittedTime;

  const peak = Math.max(...input.map(Math.abs), ...filtered.map(Math.abs));
  const verticalTarget = peak ? peak/4 : .25;
  verticalScales = niceScales(verticalTarget, -2, 1);
  verticalDial.max = verticalScales.length-1;
  verticalDial.value = scaleIndex(verticalScales, preserveScale && !verticalAuto ? preferredVertical : verticalTarget);
}
function syncDialButtons(inactive) {
  document.querySelectorAll('[data-dial]').forEach(button => {
    const dial = $(button.dataset.dial);
    button.disabled = inactive || (Number(button.dataset.step) < 0 ? dial.value === dial.min : dial.value === dial.max);
  });
}
function zeroCrossing(times, input, mode, width) {
  let first = null;
  for (let i = 1; i < input.length; i++) {
    const a = input[i-1], b = input[i];
    const crossed = mode === 'rising' ? a < 0 && b >= 0 : a > 0 && b <= 0;
    if (!crossed) continue;
    const crossing = times[i-1] - a*(times[i]-times[i-1])/(b-a);
    first ??= crossing;
    if (crossing >= width*.2 && crossing + width*.8 <= times.at(-1)) return crossing;
  }
  return first;
}

function drawScope() {
  const xy = $('view-mode').value === 'xy';
  $('scope-mode').textContent = xy ? 'X–Y 轨迹' : '时域';
  $('wave-chart').setAttribute('aria-label', xy ? '输入与输出 X–Y 轨迹' : '时域波形');
  const inactive = !current || xy;
  for (const control of [timeDial, verticalDial, edge]) control.disabled = inactive;
  syncDialButtons(inactive);
  $('auto-scale').disabled = inactive;
  const visible = scopeChannels.filter(channel => channel.button.getAttribute('aria-pressed') === 'true');
  scopeChannels.forEach(channel => {
    channel.button.disabled = inactive || (visible.length === 1 && visible[0] === channel);
    channel.legend.hidden = xy || !visible.includes(channel);
  });
  $('scope-empty').hidden = Boolean(current);
  const trigger = $('scope-trigger');
  trigger.hidden = inactive || edge.value === 'off';
  if (!current) {
    $('wave-chart').replaceChildren();
    $('axis-note').textContent = '等待分析结果';
    return;
  }
  const plot = current.plot;
  const amplitudeUnit = isRecording(current) ? 'mV' : '幅值单位';
  if (xy) {
    chart('wave-chart', plot.input, [{values:plot.filtered, color:'var(--ch2)'}], {xy:true});
    $('axis-note').textContent = 'CH1 横轴 · CH2 纵轴 · '+amplitudeUnit;
    return;
  }

  const step = timeScales[Number(timeDial.value)];
  const width = step*10;
  const times = plot.time.map(time => time-plot.time[0]);
  const locked = edge.value === 'off' ? null : zeroCrossing(times, plot.input, edge.value, width);
  const start = locked === null ? 0 : locked-width*.2;
  const end = start+width;
  const left = Math.max(0, times.findIndex(time => time >= start)-1);
  const endIndex = times.findIndex(time => time > end);
  const right = endIndex < 0 ? times.length : endIndex+1;
  const xs = times.slice(left, right);
  const channels = visible.map(channel => ({...channel, samples:plot[channel.key].slice(left,right)}));
  const amplitude = Math.max(...channels.flatMap(channel => channel.samples.map(Math.abs)));
  if (verticalAuto) verticalDial.value = scaleIndex(verticalScales,amplitude ? amplitude/4 : .25);
  const magnitude = verticalScales[Number(verticalDial.value)];
  syncDialButtons(false);
  const range = magnitude*4;
  const [scaleMultiplier, scaleUnit] = timeUnit(step);
  const [axisMultiplier, axisUnit] = timeUnit(width);
  readDial(timeDial, 'time-value', unitNumber(step*scaleMultiplier)+' '+scaleUnit+'/格');
  readDial(verticalDial, 'vertical-value', (verticalAuto ? '自动 · ' : '')+unitNumber(magnitude)+' '+(isRecording(current) ? 'mV' : '单位')+'/格');
  const clippedTime = start < 0 || end > times.at(-1) + width*1e-7;
  $('axis-note').textContent = '横轴 '+axisUnit+' · 纵轴 '+amplitudeUnit+(clippedTime ? ' · 超出样本的区域留空' : '');
  trigger.textContent = locked === null ? '未遇到指定边沿' : 'CH1 '+(edge.value==='rising'?'上升沿':'下降沿')+'触发';
  const svg = $('wave-chart');
  const {width: w, height: h} = svg.viewBox.baseVal;
  const gridWidth = w-66, gridHeight = h-48;
  let html = '<defs><clipPath id="scope-trace-clip"><rect x="48" y="20" width="'+gridWidth+'" height="'+gridHeight+'"/></clipPath></defs>';
  for (let i=0; i<=10; i++) {
    const x = 48+gridWidth*i/10;
    html += '<path class="graticule'+(i===5?' center':'')+'" d="M'+x+' 20V'+(h-28)+'"/>';
    if (i%2===0) html += '<text x="'+x+'" y="'+(h-9)+'" text-anchor="middle">'+unitNumber((i-(locked===null?0:2))*step*axisMultiplier)+'</text>';
  }
  for (let i=0; i<=8; i++) {
    const y = 20+gridHeight*i/8;
    html += '<path class="graticule'+(i===4?' center':'')+'" d="M48 '+y+'H'+(w-18)+'"/>';
    if (i%2===0) html += '<text x="42" y="'+(y+4)+'" text-anchor="end">'+unitNumber((4-i)*magnitude)+'</text>';
  }
  if (locked !== null) {
    const x = 48+gridWidth*.2;
    html += '<path class="trigger-line" d="M'+x+' 20V'+(h-28)+'"/><path class="trigger-marker" d="M'+(x-6)+' 8h12l-6 10z"/>';
  }
  html += '<g clip-path="url(#scope-trace-clip)">';
  for (const channel of channels) html += polyline(xs,channel.samples,start,end,-range,range,w,h,channel.color);
  svg.innerHTML = html+'</g>';
}

$('view-mode').addEventListener('change',drawScope);
edge.addEventListener('change',drawScope);
scopeChannels.forEach(({button}) => button.addEventListener('click', () => {
  button.setAttribute('aria-pressed', String(button.getAttribute('aria-pressed') !== 'true'));
  drawScope();
}));
timeDial.addEventListener('input',drawScope);
verticalDial.addEventListener('input',() => { verticalAuto = false; drawScope(); });
document.querySelectorAll('[data-dial]').forEach(button => button.addEventListener('click', () => {
  const dial = $(button.dataset.dial);
  // Resolve keyboard focus before the step button can become disabled at a limit.
  if (document.activeElement === button) dial.focus();
  dial.value = Number(dial.value)+Number(button.dataset.step);
  dial.dispatchEvent(new Event('input'));
}));
$('auto-scale').addEventListener('click', () => {
  verticalAuto = true;
  timeDial.value = fittedTime;
  drawScope();
});

function syncControls() {
  const csv = sourceIsFile(), wave = $('waveform').value;
  const external = task==='upload' && hasOutput;
  const inactive = {
    waveform:csv, sampling_hz:csv, samples:csv, noise_std:csv,
    frequency:!csv && wave==='noise',
    second_frequency:!csv && !['multitone','chirp'].includes(wave),
    filter:external, band:external, order:external, cutoff_hz:external,
    high_hz:external || $('band').value!=='bandpass',
    ripple_db:external || $('filter').value!=='chebyshev'
  };
  for (const id of fields) {
    $(id).disabled = busy || Boolean(inactive[id]);
    $(id).closest('label').hidden = Boolean(inactive[id]);
  }
  presetButtons.forEach(b => { b.disabled=busy; b.setAttribute('aria-pressed',String(b.dataset.preset===task)); });
  $('import-panel').hidden = task!=='upload';
  $('sample-credit').hidden = task!=='ecg';
  $('alias-preview').hidden = task!=='alias';
  $('tune-frequency').disabled = busy;
  if(task==='alias') updateTuner();
  $('csv').disabled = busy;
  $('run').disabled = busy || (task==='upload' && !selectedFile);
}

function setup(next) {
  task = next;
  current = null;
  verticalAuto = true;
  fileRevision++;
  controls.reset();
  selectedFile=null;
  hasOutput=false;
  $('csv').value='';
  Object.entries(presets[next]).forEach(([id,value]) => $(id).value=value);
  $('view-mode').value='time';
  edge.value='off';
  scopeChannels.forEach(({button}) => button.setAttribute('aria-pressed','true'));
  drawScope();
  $('task-title').textContent = labels[next];
  syncControls();
}

function describe(r) {
  const tone = t => fmt(t.bin_hz)+' Hz 的实测增益为 '+(t.gain_db==null?'不可测':t.gain_db.toFixed(2)+' dB');
  if (task==='h1' && r.transfer) {
    const h=r.transfer, valid=h.reliable.filter(Boolean).length;
    return '输入与输出分成 '+h.segments+' 个重叠片段；'+h.frequency_hz.length+' 个频点中有 '+valid+' 个通过激励与相干性检查。可在下方比较实测和理论增益。';
  }
  const alias = r.aliases.find(a=>a.above_nyquist);
  if (task==='alias' && alias) return '输入 '+fmt(alias.requested_hz)+' Hz 超过奈奎斯特频率 '+fmt(r.nyquist_hz)+' Hz，折叠到 '+fmt(alias.folded_hz)+' Hz；输入频谱的实测主峰为 '+fmt(r.peak_hz)+' Hz。';
  if (sourceIsFile()) {
    const n=r.samples+r.discarded_samples;
    const filtered=r.filter ? '按当前滤波器计算输出' : '使用文件中的输出列';
    return (isRecording(r)?'记录 100 的 MLII 导联':'采样记录')+'共 '+n+' 点，按时间列测得 '+fmt(r.sampling_hz)+' Hz。'+filtered+'，输入和输出的均方根幅值分别为 '+fmt(r.rms_input,3)+' 和 '+fmt(r.rms_filtered,3)+(isRecording(r)?' mV。':'。');
  }
  if (['sine','multitone'].includes(r.waveform) && r.tones.length) return r.tones.map(tone).join('，')+'。可在频谱中比较同一频点的输入与输出。';
  return '输入频谱主峰为 '+fmt(r.peak_hz)+' Hz，滤波前后均方根幅值分别为 '+fmt(r.rms_input,3)+' 和 '+fmt(r.rms_filtered,3)+'。';
}

function showResult(r) {
  $('workspace').hidden=false;
  render(r);
  $('finding-text').textContent=describe(r);
  $('measurement-note').closest('section').hidden = task==='h1';
  const panel=$('transfer-panel'), area=$('workspace');
  area.insertBefore(panel, task==='h1' ? area.querySelector('.dual-plots') : area.querySelector('.measurement-panel'));
  message('');
}

async function encoded(blob) {
  const bytes=new Uint8Array(await blob.arrayBuffer());
  let binary='';
  for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
  return btoa(binary);
}

async function runAnalysis() {
  if (busy || !controls.reportValidity()) return;
  const cfg=config();
  cfg.experiment=task;
  if (task==='upload' && !selectedFile) return;
  busy=true; syncControls();
  message('正在计算波形、频谱与测量结果…');
  try {
    const payload={config:cfg};
    if (task==='ecg') {
      const response=await fetch('/mitdb-100-10s.csv');
      if(!response.ok)throw Error('读取本地实录波形失败。');
      const source=await response.blob();
      payload.csv_base64=await encoded(source);
      cfg.dataset={title:'MIT-BIH Arrhythmia Database 1.0.0',record:'100',channel:'MLII',unit:'mV',seconds:10,source:'https://physionet.org/content/mitdb/1.0.0/'};
    } else if (task==='upload') {
      payload.csv_base64=await encoded(selectedFile);
    }
    const r=await api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(task==='ecg' && !isRecording(r))throw Error('实录 CSV 与来源校验值不符，请检查本地文件。');
    showResult(r);
    await history();
  } catch(e) { if(!current)$('finding-text').textContent='请检查输入并重新计算。'; message('本次计算未完成。'+e.message); }
  finally {busy=false;syncControls();}
}
function clearOutput() {
  current=null;
  $('workspace').hidden=true;
  for (const id of ['read-fs','read-nyquist','read-bin','read-peak']) $(id).textContent='—';
  drawScope();
  $('report-link').hidden=$('csv-link').hidden=true;
  message('');
}
function choose(next) {
  clearOutput();
  setup(next);
  $('finding-text').textContent = next==='upload' ? '选择含时间与输入列的 CSV，可比较已有双通道波形，也可给单通道信号加滤波。' : '正在读取实验输入…';
  if(next!=='upload')runAnalysis();
}
presetButtons.forEach(b=>b.onclick=()=>choose(b.dataset.preset));
controls.onsubmit=e=>{e.preventDefault();runAnalysis();};
controls.addEventListener('input',()=>{
  syncControls();
  if(current)message('参数已修改，图表和下载仍对应上一次计算。点击「应用参数并计算」更新。');
});
function updateTuner() {
  const fs=Number($('sampling_hz').value), f=Number($('frequency').value);
  if(!(fs>0 && f>0))return;
  $('tune-frequency').max=Math.min(100000, Math.ceil(Math.max(fs,f)));
  $('tune-frequency').value=f;
  const remainder=f%fs;
  $('tune-value').textContent=fmt(f)+' Hz 输入 · 折叠预览 '+fmt(Math.min(remainder,fs-remainder))+' Hz';
}
$('tune-frequency').oninput=()=>{
  $('waveform').value='sine';
  $('frequency').value=$('tune-frequency').value;
  updateTuner();
};
$('tune-frequency').onchange=runAnalysis;
$('csv').onchange=async()=>{
  const version=++fileRevision;
  const file=$('csv').files[0];
  clearOutput();selectedFile=null;hasOutput=false;syncControls();
  $('finding-text').textContent='选择 CSV 后自动分析。';
  if(!file)return;
  if(file.size>8*1024*1024){message('文件超过 8 MB，请截取较短的记录。');return;}
  try {
    const lines=(await file.text()).trim().split(/\r?\n/).filter(line=>line.trim());
    if(version!==fileRevision)return;
    const cols=line=>line.split(',').map(x=>x.trim().replace(/^"|"$/g,''));
    const keys=cols(lines[0]), ti=keys.indexOf('time_s'), n=lines.length-1;
    if(ti<0 || !keys.includes('input') || n<128 || n>32768)throw Error('需要 time_s、input 两列，以及 128 至 32768 行样本。');
    const dt=Number(cols(lines[2])[ti])-Number(cols(lines[1])[ti]);
    if(!(dt>0))throw Error('time_s 应按秒递增。');
    hasOutput=keys.includes('filtered');
    const fs=1/dt;
    $('cutoff_hz').value=Number(Math.min(100, fs/4).toPrecision(6));
    $('high_hz').value=Number((fs*0.4).toPrecision(6));
    $('discard').value=0;
    $('segment_length').value=Math.min(512,Math.floor(n/4));
    selectedFile=file;
    $('finding-text').textContent=file.name+' · '+n+' 点 · '+(hasOutput?'已识别输入与输出两列。':'已识别输入列，将按当前设置计算滤波输出。');
    syncControls();
    await runAnalysis();
  }catch(e){message(e.message);}
};

async function history(){
  try {
    const rows=await api('/api/history');
    $('history').replaceChildren();
    for(const row of rows){
      const b=document.createElement('button');
      b.type='button';b.textContent=new Date(row.created).toLocaleString()+' · '+fmt(row.sampling_hz)+' Hz · '+row.samples+' 点';
      b.onclick=async()=>{
        if(busy)return;
        busy=true;syncControls();
        try{
          const r=await api('/api/report?id='+row.id);
          const next=isRecording(r)?'ecg':r.source==='uploaded-csv'?'upload':Object.hasOwn(labels,r.configuration?.experiment)?r.configuration.experiment:'filter';
          setup(next);
          for(const id of fields)if(r.configuration?.[id]!=null)$(id).value=r.configuration[id];
          hasOutput=next==='upload' && !r.filter;
          showResult(r);
          message(next==='upload'?'已打开历史报告。要重新计算，请选择原始 CSV。':'已恢复该次分析的参数和结果。');
        }catch(e){message(e.message);}
        finally{busy=false;syncControls();}
      };
      $('history').append(b);
    }
  }catch(e){message('读取历史记录失败。'+e.message);}
}
const initialPreset = new URLSearchParams(location.search).get('preset');
choose(['alias', 'h1', 'ecg'].includes(initialPreset) ? initialPreset : 'filter');
