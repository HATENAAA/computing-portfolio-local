for (const group of document.querySelectorAll('[data-switch]')) {
  const buttons = [...group.querySelectorAll('[data-choice]')];
  const panels = [...group.querySelectorAll('[data-panel]')];
  function select(index) {
    buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
    panels.forEach((panel, i) => { panel.hidden = i !== index; });
  }
  buttons.forEach((button, i) => button.addEventListener('click', () => select(i)));
  select(0);
  group.querySelector('.tabs').hidden = false;
}
const stopPicker = document.getElementById('stop-picker');
if (stopPicker) {
  function showStop() {
    document.querySelectorAll('[data-stop]').forEach(node => node.classList.toggle('chosen', node.dataset.stop === stopPicker.value));
    document.querySelectorAll('[data-place]').forEach(node => { node.hidden = node.dataset.place !== stopPicker.value; });
  }
  stopPicker.addEventListener('change', showStop);
  const nextStop = document.getElementById('next-stop');
  if (nextStop) {
    nextStop.hidden = false;
    nextStop.addEventListener('click', () => {
      stopPicker.selectedIndex = (stopPicker.selectedIndex + 1) % stopPicker.length;
      showStop();
    });
  }
  showStop();
}
for (const pair of document.querySelectorAll('[data-crop]')) {
  const button = pair.querySelector('button');
  button.hidden = false;
  button.onclick = () => {
    const on = pair.classList.toggle('magnified');
    button.setAttribute('aria-pressed', String(on));
  };
}
const counterpart = document.querySelector('.mast nav a');
if (counterpart) {
  function updateLanguageAnchor() {
    const target = location.hash.slice(1);
    counterpart.hash = document.getElementById(target) ? location.hash : '';
  }
  updateLanguageAnchor();
  window.addEventListener('hashchange', updateLanguageAnchor);
}

for (const workflow of document.querySelectorAll('[data-workflow-picker]')) {
  const picker = workflow.querySelector('select');
  const panels = workflow.querySelectorAll('[data-workflow-panel]');
  const steps = [...workflow.querySelectorAll('[data-workflow-step]')];
  const ledger=workflow.id==='order-replay' ? document.createElement('div') : null;
  if(ledger){
    ledger.className='order-states';
    for(const option of picker.options){
      const action=document.createElement('button');action.type='button';action.textContent=option.textContent;
      action.onclick=()=>{picker.value=option.value;showPanel();};
      ledger.append(action);
    }
    workflow.querySelector('.workflow-controls').before(ledger);
  }
  function showPanel() {
    if(ledger) [...ledger.children].forEach((node,i)=>node.setAttribute('aria-pressed',String(i===picker.selectedIndex)));
    for (const panel of panels) panel.hidden = panel.dataset.workflowPanel !== picker.value;
    for (const button of steps) {
      const nextIndex = picker.selectedIndex + Number(button.dataset.workflowStep);
      button.disabled = nextIndex < 0 || nextIndex >= picker.length;
    }
  }
  picker.addEventListener('change', showPanel);
  for (const button of steps) {
    button.addEventListener('click', () => {
      picker.selectedIndex += Number(button.dataset.workflowStep);
      showPanel();
    });
  }
  workflow.querySelector('.workflow-controls').hidden = false;
  showPanel();
}

function revealLinkedContent() {
  const target = document.getElementById(location.hash.slice(1));
  if (!target) return;
  let revealed = false;
  const selectedPanel = target.closest('[data-workflow-panel]');
  if (selectedPanel?.hidden) {
    const picker = selectedPanel.closest('[data-workflow-picker]').querySelector('select');
    picker.value = selectedPanel.dataset.workflowPanel;
    picker.dispatchEvent(new Event('change'));
    revealed = true;
  }
  for (let parent = target; parent; parent = parent.parentElement) {
    if (parent.tagName === 'DETAILS' && !parent.open) {
      parent.open = true;
      revealed = true;
    }
  }
  if (revealed) requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'instant' }));
}
document.addEventListener('click', event => {
  const link = event.target.closest('a[href^="#"]');
  if (link?.hash === location.hash) revealLinkedContent();
});
window.addEventListener('hashchange', revealLinkedContent);
revealLinkedContent();

const fireVideo = document.querySelector('[data-fire-video]');
if (fireVideo) {
  const jumps = document.querySelector('[data-video-jumps]');
  let target=null, transfer=null, localVideo=null;
  const source=fireVideo.querySelector('source').src;
  const notice=document.createElement('span');
  notice.setAttribute('role','status');jumps.append(notice);
  async function seek(){
    if(target===null || !Number.isFinite(fireVideo.duration))return;
    const point=Math.min(target,fireVideo.duration);
    const ranges=fireVideo.seekable;
    const canSeek=point===0 || Array.from({length:ranges.length},(_,i)=>ranges.start(i)<=point && ranges.end(i)>=point).some(Boolean);
    if(canSeek || localVideo || location.protocol==='file:'){
      fireVideo.currentTime=point;target=null;notice.textContent='';return;
    }
    // Static servers can send the original MP4 without byte ranges.
    if(transfer)return;
    notice.textContent=document.documentElement.lang==='en'?'Loading video…':'正在读取视频…';
    transfer=fetch(source).then(response=>{
      if(!response.ok)throw Error('Video unavailable');
      return response.blob();
    }).then(blob=>{
      localVideo=URL.createObjectURL(blob);
      fireVideo.src=localVideo;fireVideo.load();
    }).catch(()=>{
      transfer=null;target=null;
      notice.textContent=document.documentElement.lang==='en'?'Could not seek. Use the video controls.':'跳转失败，可使用视频控件。';
    });
  }
  fireVideo.addEventListener('loadedmetadata',seek);
  for(const button of jumps.querySelectorAll('[data-video-time]')){
    button.onclick=()=>{
      target=Number(button.dataset.videoTime);
      if(fireVideo.readyState)seek();
      else if(fireVideo.preload!=='metadata'){fireVideo.preload='metadata';fireVideo.load();}
    };
  }
  jumps.hidden = false;
}

const alias=document.querySelector('[data-alias]');
if (alias) {
  const input=alias.querySelector('select');
  const zh=document.documentElement.lang.startsWith('zh');
  const dial=document.createElement('input');dial.type='range';dial.min='1';dial.max='1023';dial.step='1';dial.value='750';
  const dialLabel=document.createElement('label');dialLabel.className='frequency-dial';
  dialLabel.append(zh?'连续调频（Hz） ':'Tune frequency (Hz) ',dial);
  input.closest('label').after(dialLabel);
  const custom=new Option(zh?'自定义':'Custom','custom');custom.disabled=true;input.add(custom);
  const sampling=1024;
  const tau=2*Math.PI;
  const position=(hz,i)=>[20+i*560/120,95-60*Math.sin(tau*hz*i/(10*sampling))];
  function trace(hz) {
    return Array.from({length:121},(_,i)=>{
      const [x,y]=position(hz,i);
      return (i===0?'M':'L')+x.toFixed(1)+' '+y.toFixed(1);
    }).join(' ');
  }
  function updateAlias() {
    const frequency=Number(dial.value);
    const signed=((frequency+sampling/2)%sampling)-sampling/2;
    const folded=Math.abs(signed);
    alias.querySelector('#alias-input').setAttribute('d',trace(frequency));
    alias.querySelector('#alias-fold').setAttribute('d',trace(signed));
    const dots=Array.from({length:13},(_,i)=>{
      const [x,y]=position(frequency,10*i);
      const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');
      dot.setAttribute('cx',x);
      dot.setAttribute('cy',y);
      dot.setAttribute('r',3);
      return dot;
    });
    alias.querySelector('#alias-samples').replaceChildren(...dots);
    const message=zh
      ? '以 1024 Hz 采样，'+frequency+' Hz 的折叠频率为 '+folded+' Hz。'
      : 'At 1024 Hz sampling, '+frequency+' Hz folds to '+folded+' Hz.';
    alias.querySelector('#alias-result').textContent=frequency===512
      ? message + (zh?' 此相位下，采样值恰为零。':' At this phase, all samples are zero.')
      : message;
  }
  input.value='750';
  input.addEventListener('change',()=>{dial.value=input.value;updateAlias();});
  dial.addEventListener('input',()=>{
    input.value=[...input.options].some(option=>option.value===dial.value)?dial.value:'custom';
    updateAlias();
  });
  updateAlias();
  alias.hidden=false;
}

const places=document.querySelector('[data-place-search]');
if (places) {
  const query=places.querySelector('input');
  const entries=[...places.querySelectorAll('tbody tr, .site-register li')];
  const empty=places.querySelector('[role=status]');
  query.addEventListener('input',()=>{
    const term=query.value.trim().toLowerCase();
    for (const item of entries) item.hidden=!item.textContent.toLowerCase().includes(term);
    empty.hidden=entries.some(item=>!item.hidden);
  });
  query.parentElement.hidden=false;
}

const readingNav = document.querySelector('[data-reading-nav]');
if (readingNav) {
  const links = [...readingNav.querySelectorAll('a')];
  const chapters = links.map(link => document.getElementById(link.hash.slice(1)));
  let scheduled = false;

  function markChapter() {
    const line = Math.max(80, readingNav.getBoundingClientRect().bottom + 15);
    let current = 0;
    chapters.forEach((chapter, index) => {
      if (chapter.getBoundingClientRect().top <= line) current = index;
    });
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 3) {
      current = chapters.length - 1;
    }
    links.forEach((link, index) => {
      if (index === current) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    scheduled = false;
  }

  function scheduleChapter() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(markChapter);
  }

  window.addEventListener('scroll', scheduleChapter, { passive: true });
  window.addEventListener('resize', scheduleChapter);
  window.addEventListener('hashchange', scheduleChapter);
  window.addEventListener('load', scheduleChapter, { once: true });
  markChapter();
}

// Open original figures in context, retaining focus and position in the project.
const figures = [...document.querySelectorAll('figure a[href]')].filter(a=>a.querySelector('img') && /\.(png|jpe?g|webp)$/i.test(a.pathname));
if (figures.length && typeof HTMLDialogElement !== 'undefined') {
  const en=document.documentElement.lang==='en';
  const viewer=document.createElement('dialog');viewer.className='figure-viewer';
  viewer.setAttribute('aria-label',en?'Image viewer':'图像查看器');
  viewer.innerHTML='<div class="viewer-tools"><button type="button" data-prev></button><button type="button" data-next></button><button type="button" data-close></button></div><figure><img alt=""><figcaption></figcaption></figure>';
  document.body.append(viewer);
  const prev=viewer.querySelector('[data-prev]'),next=viewer.querySelector('[data-next]'),close=viewer.querySelector('[data-close]');
  [prev.textContent,next.textContent,close.textContent]=en?['Previous','Next','Close']:['上一张','下一张','关闭'];
  let opener, gallery, index;
  function draw(i){
    index=i;const image=gallery[i].querySelector('img');
    viewer.querySelector('img').src=gallery[i].href;viewer.querySelector('img').alt=image.alt;
    viewer.querySelector('figcaption').textContent=image.alt;
    prev.disabled=i===0;next.disabled=i===gallery.length-1;
  }
  figures.forEach(a=>a.addEventListener('click',e=>{
    if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    e.preventDefault();opener=a;gallery=figures.filter(item=>item.getClientRects().length);draw(gallery.indexOf(a));viewer.showModal();close.focus();
  }));
  prev.onclick=()=>draw(index-1);next.onclick=()=>draw(index+1);close.onclick=()=>viewer.close();
  viewer.onkeydown=e=>{if(e.key==='ArrowLeft'&&!prev.disabled){e.preventDefault();prev.click();}if(e.key==='ArrowRight'&&!next.disabled){e.preventDefault();next.click();}};
  viewer.addEventListener('close',()=>opener?.focus({preventScroll:true}));
  viewer.addEventListener('click',e=>{if(e.target===viewer)viewer.close();});
}
for(const comparison of document.querySelectorAll('.comparison')) {
  const range=comparison.querySelector('input'), output=comparison.querySelector('output');
  range.addEventListener('input',()=>{comparison.style.setProperty('--split',range.value+'%');output.value=range.value+'%';});
}
const samples=document.querySelector('[data-depth-samples]');
if(samples){
  const values=JSON.parse(samples.dataset.depthSamples), picker=samples.querySelector('select');
  const zh=document.documentElement.lang.startsWith('zh');
  function inspect(){
    const i=Number(picker.value),[ref,linear,svr]=values[i];
    samples.querySelector('output').textContent=(zh?'参考 ':'Reference ')+ref.toFixed(2)+' m · '+(zh?'线性残差 ':'Linear residual ')+(linear-ref).toFixed(2)+' m · '+(zh?'SVR 残差 ':'SVR residual ')+(svr-ref).toFixed(2)+' m';
    samples.closest('figure').querySelectorAll('circle').forEach(c=>c.classList.toggle('inspected',Number(c.dataset.sample)===i));
  }
  const plot=samples.closest('figure').querySelector('svg');
  plot.addEventListener('click',e=>{const dot=e.target.closest('circle[data-sample]');if(dot){picker.value=dot.dataset.sample;inspect();}});
  samples.hidden=false;picker.onchange=inspect;inspect();
}

const reviewState=new URLSearchParams(location.search);
for(const link of document.querySelectorAll('.catalog-return,.mast nav a')){
  const url=new URL(link.href);
  for(const key of ['field','q'])if(reviewState.has(key))url.searchParams.set(key,reviewState.get(key));
  link.href=url.href;
}
