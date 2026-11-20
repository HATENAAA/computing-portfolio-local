import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { fitStudio, setStudioView } from './studio.js';
const en=new URLSearchParams(location.search).get('lang')==='en';
document.documentElement.lang=en?'en':'zh-CN';
const mount=document.getElementById('view'), buttons=[...document.querySelectorAll('button')];
if(en) buttons.forEach((b,i)=>b.textContent=['Room','Strike pads','Training area'][i]);
try {
  const renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.65));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  mount.append(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color('#26394b');
  fitStudio(scene);
  const camera=new THREE.PerspectiveCamera(43,1,.1,45);
  const orbit=new OrbitControls(camera,renderer.domElement);
  orbit.enablePan=false;orbit.enableZoom=false;
  orbit.minAzimuthAngle=-.62;orbit.maxAzimuthAngle=.76;orbit.maxPolarAngle=Math.PI*.50;orbit.minPolarAngle=.90;
  const viewpoints=['room','pads','area'];
  const paint=()=>renderer.render(scene,camera);
  function select(index){setStudioView(camera,orbit,viewpoints[index]);paint();buttons.forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));}
  buttons.forEach((b,i)=>b.onclick=()=>select(i));
  orbit.addEventListener('change',paint);
  orbit.addEventListener('start',()=>buttons.forEach(b=>b.setAttribute('aria-pressed','false')));
  new ResizeObserver(()=>{const w=mount.clientWidth,h=mount.clientHeight;camera.aspect=w/Math.max(h,1);camera.updateProjectionMatrix();renderer.setSize(w,h);paint();}).observe(mount);
  select(0);document.querySelector('nav').hidden=false;
} catch {document.querySelector('nav').remove();document.getElementById('error').textContent=en?'WebGL unavailable · studio photograph from the desktop demo':'WebGL 不可用 · 显示桌面场景实拍';}
