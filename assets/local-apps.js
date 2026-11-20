/* Injected by the local hub. The public catalogue never loads this file. */
const appPorts = {hsi: 8782, vrfitai: 8780, manufacturing: 8081, firewatch: 8765,
  signal: 8783, city: 8766, bathymetry: 8784, medical: 8086};
const projectTitles = {hsi: '高光谱影像重建', vrfitai: 'VRFitAI', manufacturing: '制造订单与库存管理系统',
  firewatch: '视觉火焰检测与事件分析系统', signal: '虚拟仪器与信号分析系统',
  city: '上海红色文化地图', bathymetry: '卫星测深回归分析', medical: '熙心健康体检预约与报告系统'};
const appLinks = [...document.querySelectorAll('[data-app]')];
const statuses = [...document.querySelectorAll('[data-service]')];
const englishUi = document.documentElement.lang === 'en';

for (const element of document.querySelectorAll('[data-local-only]')) element.hidden = false;

function appUrl(project, path = '') {
  const base = new URL('http://127.0.0.1:' + appPorts[project] + '/');
  const target = new URL(path, base);
  return target.origin === base.origin ? target.href : base.href;
}

async function localStatus() {
  const response = await fetch('/api/services', {cache: 'no-store'});
  if (!response.ok) throw new Error('Service status unavailable');
  const ports=await response.json();
  for(const key of Object.keys(appPorts))if(Number.isInteger(ports[key]))appPorts[key]=ports[key];
  return Object.fromEntries(Object.keys(appPorts).map(key=>[key,Number.isInteger(ports[key])]));

}

async function refreshStatus() {
  let status = {};
  try { status = await localStatus(); } catch {}
  for (const node of statuses) {
    const ready = status[node.dataset.service] === true;
    node.dataset.state = ready ? 'ready' : 'offline';
    node.textContent = englishUi ? (ready ? 'Ready' : 'Stopped') : (ready ? '服务就绪' : '未启动');
  }
  for (const link of appLinks) {
    const project = link.dataset.app;
    link.dataset.fallback ??= link.getAttribute('href');
    link.href = status[project] === true && appPorts[project]
      ? appUrl(project, link.dataset.appPath) : link.dataset.fallback;
  }
}

if (appLinks.length || statuses.length) {
  refreshStatus();
  window.addEventListener('focus', refreshStatus);
}

const offline = document.getElementById('offline-project');
if (offline) {
  const params = new URLSearchParams(location.search);
  const id = params.get('project');
  const exists = Object.hasOwn(appPorts, id);
  offline.textContent = exists ? projectTitles[id] : '本地应用';
  if (exists) document.getElementById('offline-detail').href = id + '.html';
  document.getElementById('retry-service').onclick = async () => {
    const message = document.getElementById('offline-state');
    let status = {};
    try { status = await localStatus(); } catch {}
    if (exists && status[id] === true) {
      location.href = appUrl(id, params.get('path') || '');
    } else {
      message.textContent = '服务尚未就绪。请先双击启动文件，再检查。';
    }
  };
}
