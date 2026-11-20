const $ = id => document.getElementById(id);
const english = new URLSearchParams(location.search).get('lang') === 'en';
const t = (en, zh) => english ? en : zh;
const title = place => t(place.en, place.name);
const address = place => t(place.address_en, place.address);
const options = (entries, label) => entries.map(item => new Option(label(item), item.id));
document.documentElement.lang = t('en', 'zh-CN');
if (english) {
  document.title = 'Shanghai historic sites';
  document.querySelectorAll('[data-en]').forEach(node => node.textContent = node.dataset.en);
  document.querySelectorAll('[data-label]').forEach(node => node.setAttribute('aria-label', node.dataset.label));
}

const venues = atlasData.places;
const places = new Map(venues.map(place => [place.id, place]));
const routes = new Map(atlasData.routes.map(route => [route.id, route]));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const map = L.map('map', {
  preferCanvas: true, zoomAnimation: !reduced, fadeAnimation: !reduced, zoomSnap: .5,
  minZoom: 10, maxZoom: 19, scrollWheelZoom: false,
  maxBounds: [[31.159,121.409],[31.289,121.512]], maxBoundsViscosity: 1,
});
map.attributionControl.setPrefix(false);
map.attributionControl.addAttribution('<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors · ODbL</a>');
L.control.scale({imperial: false}).addTo(map);

const areaStyle = {park: '#e3dfcd', water: '#c2dce5', building: '#e1d9ce'};
const major = new Set(['trunk', 'primary', 'secondary', 'tertiary', 'motorway']);
const labels = new Map();
const drawing = new Map();
for (const [kind, name, en, points] of streets) {
  let group = drawing.get(kind);
  if (!group) drawing.set(kind, group = []);
  group.push(points);
  if (name && (major.has(kind) || kind === 'park' || kind === 'residential')) {
    const previous = labels.get(name);
    if (!previous || previous.points.length < points.length) labels.set(name, {name, en, points, kind});
  }
}
for (const kind of ['water','park','building']) {
  const color = areaStyle[kind];
  L.polygon((drawing.get(kind) ?? []).map(ring => [ring]), {stroke:false, fillColor:color, fillOpacity:1, interactive:false}).addTo(map);
  drawing.delete(kind);
}
for (const [kind, paths] of [...drawing].sort(([a],[b]) => Number(major.has(a)) - Number(major.has(b)))) {
  const isMajor = major.has(kind);
  const foot = ['footway','steps','path','cycleway'].includes(kind);
  const color = kind === 'shore' ? '#b5d2df' : isMajor ? '#cfbca1' : foot ? '#dfd5c6' : '#fffcf8';
  L.polyline(paths, {color, weight:isMajor ? 3.2 : foot ? 1 : 2, opacity:1, interactive:false}).addTo(map);
}
const labelLayer = L.layerGroup().addTo(map);
const labelEntries = [...labels.values()].sort((a,b) => Number(major.has(b.kind)) - Number(major.has(a.kind)));
function drawLabels() {
  labelLayer.clearLayers();
  if (map.getZoom() < 14.5) return;
  const taken = [];
  const bounds = map.getBounds();
  for (const item of labelEntries) {
    const pos = item.points[Math.floor(item.points.length / 2)];
    if (!bounds.contains(pos)) continue;
    const pixel = map.latLngToContainerPoint(pos);
    if (taken.some(p => Math.abs(p.x - pixel.x) < 112 && Math.abs(p.y - pixel.y) < 31)) continue;
    taken.push(pixel);
    const label = document.createElement('span');
    label.textContent = english && item.en ? item.en : item.name;
    L.marker(pos, {icon:L.divIcon({html:label, className:'road-label', iconSize:null}),
      interactive:false, keyboard:false, zIndexOffset:-1000}).addTo(labelLayer);
  }
}
map.on('moveend', drawLabels);

const network = makeWalkingNetwork(walkingData, venues);
const routeLayer = L.layerGroup().addTo(map);
const directionLayer = L.layerGroup().addTo(map);
const markers = L.layerGroup().addTo(map);
const ordered = [...venues].sort((a,b) => title(a).localeCompare(title(b), t('en','zh')));
const districtOf = place => t(place.address_en.split(', ').at(-1), place.address.match(/^(.+?区)/)?.[1] ?? '');
const storageKey = 'shanghai-atlas-v2';
const aliases = {'中共一大会址':'first','中共二大会址':'second','韬奋纪念馆':'tao','孙中山故居':'sun'};
function restore(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function persist(key, ids) {
  try { localStorage.setItem(key, JSON.stringify(ids)); } catch {}
}
const previous = restore(storageKey, null);
const legacy = restore('city-favorites', []);
const saved = new Set((Array.isArray(previous) ? previous : Array.isArray(legacy) ? legacy.map(name => aliases[name] || venues.find(p => p.name === name)?.id) : []).filter(id => places.has(id)));
const customKey = 'shanghai-custom-walk';
const maxStops = 8;
const storedStops = restore(customKey, []);
let custom = Array.isArray(storedStops) ? [...new Set(storedStops)].filter(id => places.has(id)).slice(0,maxStops) : [];
let mode = 'preset';
let route = atlasData.routes[0];
let selected = places.get(route.stops[0]);
let fromId = selected.id;
let direction = null;

const formatDistance = meters => meters >= 1000 ? (meters / 1000).toFixed(2) + ' km' : Math.round(meters) + ' m';
function formatWalk(meters) {
  const minutes = Math.max(1, Math.round(meters / 75));
  return formatDistance(meters) + ' · ' + t('~' + minutes + ' min walk','步行约 ' + minutes + ' 分钟');
}
function activeStops() {
  return (mode === 'preset' ? route.stops : custom).map(id => places.get(id));
}

function drawWalk(leg, layer, color, weight) {
  L.polyline(leg.path, {color:'#fffaf4', weight:weight + 3, interactive:false}).addTo(layer);
  L.polyline(leg.path, {color, weight, opacity:.95, interactive:false}).addTo(layer);
  L.polyline(leg.approaches, {color, weight:2, dashArray:'3 4', interactive:false}).addTo(layer);
}
function fit(points, maxZoom = 16.5) {
  map.fitBounds(points, {padding:[36,36], maxZoom, animate:false});
}
function fitActive() {
  if (direction) fit([places.get(fromId).position, ...direction.path, places.get($('to').value).position]);
  else {
    const stops = activeStops();
    const points = stops.map(stop => stop.position);
    for (let i = 1; i < stops.length; i++) {
      const leg = network.plan(stops[i - 1], stops[i]);
      if (leg) points.push(...leg.path);
    }
    fit(points.length ? points : venues.map(place => place.position));
  }
}
function renderMarkers() {
  const stopNumbers = new Map(activeStops().map((place,index) => [place.id,index + 1]));
  markers.clearLayers();
  for (const place of venues) {
    const number = stopNumbers.get(place.id);
    const isSelected = selected.id === place.id;
    const endpoint = direction && (fromId === place.id ? t('S','起') : $('to').value === place.id ? t('E','终') : '');
    const lead = Boolean(number || isSelected || endpoint);
    const marker = L.marker(place.position, {
      title:title(place), alt:title(place), zIndexOffset:endpoint ? 900 : isSelected ? 800 : number ? 300 : 100,
      icon:L.divIcon({
        className:'station' + (lead ? ' route-stop' : ' other-stop') + (isSelected ? ' current' : '') + (endpoint ? ' walk-endpoint' : ''),
        html:endpoint || (number ? String(number) : ''), iconSize:lead ? [26,26] : [12,12], iconAnchor:lead ? [13,13] : [6,6],
      }),
    }).addTo(markers).on('click', () => select(place, false));
    marker.on('keypress', event => {if (event.originalEvent.key === ' ') select(place, false);});
  }
}
function renderStops() {
  const stops = activeStops();
  const list = $('stops');
  const items = [];
  let total = 0;
  let connected = true;
  routeLayer.clearLayers();
  for (const [i, place] of stops.entries()) {
    const li = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'stop-label';
    button.textContent = title(place);
    if (place.id === selected.id) button.setAttribute('aria-current','location');
    button.onclick = () => select(place, true);
    li.append(button);
    const leg = i > 0 ? network.plan(stops[i - 1], place) : null;
    if (i > 0) {
      const meta = document.createElement('small');
      meta.className = 'stop-leg';
      meta.textContent = leg ? formatDistance(leg.meters) : t('No walking connection','无可用步行路径');
      li.append(meta);
      if (leg) {
        total += leg.meters;
        if ($('lines').checked) drawWalk(leg, routeLayer, '#963f36', 4.5);
      } else connected = false;
    }
    if (mode === 'custom') {
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'remove-stop';
      remove.textContent = '×';
      remove.setAttribute('aria-label', t('Remove ', '移除') + title(place));
      remove.onclick = () => {
        custom = custom.filter(id => id !== place.id);
        updateCustom();
        const focus = $('stops').querySelectorAll('.stop-label')[Math.min(i,custom.length-1)];
        (focus || $('custom-stop')).focus();
      };
      li.append(remove);
    }
    items.push(li);
  }
  list.replaceChildren(...items);
  const summary = stops.length < 2 ? t('Add at least two sites', '添加至少两个场址') :
    connected ? stops.length + t(' stops · ', ' 站 · ') + formatWalk(total) : t('Some stops are not connected','部分站点间无可用步行路径');
  $('route-summary').textContent = summary;
  $('lines-label').hidden = stops.length < 2;
}
function renderPlace() {
  $('name').textContent = title(selected);
  $('address').textContent = address(selected);
  $('source').href = selected.source;
  $('coordinate').href = selected.osm;
  $('save').textContent = saved.has(selected.id) ? t('Saved','已收藏') : t('Save','收藏');
  $('save').setAttribute('aria-pressed', String(saved.has(selected.id)));
}
function select(place, pan) {
  if (!place) return;
  selected = place;
  renderPlace();
  const buttons = $('stops').querySelectorAll('.stop-label');
  activeStops().forEach((stop,i) => {
    if (stop === place) buttons[i]?.setAttribute('aria-current','location');
    else buttons[i]?.removeAttribute('aria-current');
  });
  if (!direction && !$('to').value) {
    fromId = place.id;
    renderDestinations();
  }
  renderMarkers();
  if (pan) {
    map.setView(place.position, Math.max(14.5,map.getZoom()), {animate:!reduced});
  }
  if ($('near').checked) renderDirectory();
}

function renderDestinations() {
  const previous = $('to').value;
  $('from').value = fromId;
  $('to').replaceChildren(new Option(t('Select destination','选择终点'),''), ...options(ordered.filter(p => p.id !== fromId),title));
  $('to').value = places.has(previous) && previous !== fromId ? previous : '';
  $('direction-fit').disabled = !$('to').value;
}
function renderDirection(zoom = false) {
  directionLayer.clearLayers();
  const destination = places.get($('to').value);
  direction = destination ? network.plan(places.get(fromId),destination) : null;
  $('direction-fit').disabled = !destination;
  $('direction-clear').hidden = !destination;
  $('distance').textContent = direction ? formatWalk(direction.meters) :
    destination ? t('No walking connection','无可用步行路径') : '';
  renderMarkers();
  if (direction) {
    drawWalk(direction, directionLayer, '#265c88', 6);
    if (zoom) fitActive();
  }
}

function renderDirectory() {
  const query = $('query').value.trim().toLowerCase();
  const district = $('district').value;
  const near = $('near').checked;
  const results = ordered.filter(p => (!$('saved').checked || saved.has(p.id)) &&
     (!district || districtOf(p) === district) &&
     [p.name,p.en,p.address,p.address_en].some(value => value.toLowerCase().includes(query)));
  if (near) results.sort((a,b) => network.distance(selected,a) - network.distance(selected,b));
  $('matches').replaceChildren(...results.map(place => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = title(place);
    if (near && place !== selected) b.textContent += ' · ' + formatDistance(network.distance(selected,place));
    b.onclick = () => select(place, true);
    return b;
  }));
  if (!results.length) $('matches').textContent = t('No matching places','无匹配地点');
  $('export').disabled = !saved.size;
}

function updateCustom(message = '') {
  persist(customKey, custom);
  const available = ordered.filter(place => !custom.includes(place.id));
  $('custom-stop').replaceChildren(new Option(t('Select a site','选择场址'),''), ...options(available,title));
  $('custom-stop').disabled = custom.length >= maxStops;
  $('add-stop').disabled = true;
  $('optimize').disabled = custom.length < 3;
  $('custom-status').textContent = message || t(custom.length + ' of ' + maxStops + ' stops', '已选 ' + custom.length + ' / ' + maxStops + ' 站');
  renderStops();
  renderMarkers();
}
function showMode(next) {
  mode = next;
  $('preset-mode').setAttribute('aria-pressed', String(next === 'preset'));
  $('custom-mode').setAttribute('aria-pressed', String(next === 'custom'));
  $('preset-picker').hidden = next !== 'preset';
  $('custom-picker').hidden = next !== 'custom';
  if (next === 'custom') updateCustom();
  else {
    renderStops();
    renderMarkers();
  }
  fitActive();
}

$('coverage').textContent = t(venues.length + ' sites · ' + routes.size + ' walks', venues.length + ' 处场址 · ' + routes.size + ' 条主题路线');
$('route').replaceChildren(...options([...routes.values()],title));
$('route').onchange = () => {
  route = routes.get($('route').value);
  $('to').value = '';
  renderDirection();
  renderStops();
  select(places.get(route.stops[0]),false);
  fitActive();
};
$('from').replaceChildren(...options(ordered,title));
$('from').onchange = () => {
  fromId = $('from').value;
  renderDestinations();
  renderDirection();
};
$('to').onchange = () => renderDirection(true);
$('direction-fit').onclick = () => {
  renderDirection(true);
  if (matchMedia('(max-width: 640px)').matches) {
    $('map').scrollIntoView({block:'start',behavior:reduced ? 'instant' : 'smooth'});
  }
};
$('direction-clear').onclick = () => {$('to').value = ''; renderDirection();};
$('fit').onclick = fitActive;
$('fit-sites').onclick = () => fit(venues.map(place => place.position));
$('lines').onchange = renderStops;
$('preset-mode').onclick = () => showMode('preset');
$('custom-mode').onclick = () => showMode('custom');
$('custom-stop').onchange = () => {$('add-stop').disabled = !$('custom-stop').value;};
$('add-stop').onclick = () => {
  const place = places.get($('custom-stop').value);
  if (!place || custom.includes(place.id) || custom.length >= maxStops) return;
  custom.push(place.id);
  updateCustom();
  select(place,false);
  fitActive();
};
$('optimize').onclick = () => {
  const improved = network.optimize(activeStops()).map(p => p.id);
  const changed = custom.some((id,i) => id !== improved[i]);
  custom = improved;
  updateCustom(changed ? t('Stops reordered. Start kept fixed.', '已调整站序，保留起点。')
    : t('This order already minimizes the walk.', '当前站序已是最短步行路线。'));
  fitActive();
};

$('district').replaceChildren(new Option(t('All districts','全部区'),''), ...[...new Set(venues.map(districtOf))].sort().map(name => new Option(name,name)));
$('query').oninput = renderDirectory;
for (const id of ['district','saved','near']) $(id).onchange = renderDirectory;
$('save').onclick = () => {
  if (saved.has(selected.id)) saved.delete(selected.id);
  else saved.add(selected.id);
  persist(storageKey,[...saved]);
  renderPlace();
  renderDirectory();
};
$('export').onclick = () => {
  const items = [...saved].map(id => places.get(id)).map(({id,name,en,address,address_en,position,source,osm}) =>
    ({id,name,en,address,address_en,position,source,osm}));
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([JSON.stringify(items,null,2)],{type:'application/json'}));
  link.download = 'shanghai-saved-places.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
};

renderStops();
renderDestinations();
renderPlace();
renderDirectory();
renderMarkers();
fitActive();
new ResizeObserver(() => map.invalidateSize({pan:false})).observe($('map'));
