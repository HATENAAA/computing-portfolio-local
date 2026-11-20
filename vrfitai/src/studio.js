import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';

// One metre per scene unit. Shared architecture keeps the lobby and drill views consistent.
function surface(base, speckle, repeatX, repeatY, seams = false) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, 256, 256);
  let seed = 21;
  const noise = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  ctx.fillStyle = speckle;
  for (let i = 0; i < 8500; i++) {
    ctx.globalAlpha = .12 + noise() * .4;
    ctx.fillRect(noise() * 256, noise() * 256, 1 + noise(), 1);
  }
  if (seams) {
    ctx.globalAlpha = .65; ctx.fillStyle = '#172331';
    ctx.fillRect(0, 0, 2, 256); ctx.fillRect(0, 0, 256, 2);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(repeatX, repeatY);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}
// The cover wraps continuously around the bag; the closing seam faces the wall.
function bagCover() {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 768;
  const ctx = canvas.getContext('2d');
  const tones = ['#293d51', '#384d62', '#466079', '#405a73', '#364e66', '#273b50'];
  const panel = canvas.width / tones.length;
  const seamColor = '#182d40';
  let seed = 73;
  function random() {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 4294967296;
  }
  for (let i = 0; i < tones.length; i++) {
    const x = i * panel;
    ctx.fillStyle = tones[i];
    ctx.fillRect(x, 0, panel + 1, canvas.height);
    ctx.fillStyle = seamColor;
    ctx.fillRect(x, 0, 3, canvas.height);
    ctx.fillStyle = '#8c9ba8';
    for (let y = 0; y < canvas.height; y += 11) ctx.fillRect(x + 6, y, 1.8, 5);
  }
  for (const [y, height] of [[32, 46], [675, 50]]) {
    ctx.fillStyle = '#233548';
    ctx.fillRect(0, y, canvas.width, height);
    for (const edge of [y + 5, y + height - 6]) {
      ctx.fillStyle = '#84929d';
      for (let x = 0; x < canvas.width; x += 12) ctx.fillRect(x, edge, 6, 1.8);
    }
  }
  // Pressed rim and shallow creases near the two bound ends.
  for (const y of [30,80,673,727]) {
    ctx.fillStyle = '#182a3b';
    ctx.fillRect(0,y,1024,2);
    ctx.fillStyle = '#68798a';
    ctx.fillRect(0,y+2,1024,1);
  }
  for (let i = 0; i < 58; i++) {
    const x = random()*1024, upper = i%2 === 0;
    const y = upper ? 81 : 672, dy = (upper ? 1 : -1)*(9+random()*28);
    ctx.beginPath(); ctx.moveTo(x,y);
    ctx.quadraticCurveTo(x+4,y+dy*.35,x+11,y+dy);
    ctx.strokeStyle='rgba(8,19,32,.22)'; ctx.lineWidth=1.8; ctx.stroke();
  }
  for (let i = 0; i < 59000; i++) {
    ctx.fillStyle = i % 2 ? 'rgba(8,19,33,.20)' : 'rgba(204,216,229,.13)';
    ctx.fillRect(random()*1024, random()*768, 1 + random()*2, 1.5);
  }
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  map.wrapS = THREE.RepeatWrapping;
  map.anisotropy = 4;
  return map;
}

// Radius in the uncompressed cover; the two end profiles close at the poles.
function bagRadius(y, angle) {
  const cap = Math.max(0, (Math.abs(y) - .56) / .20);
  const shoulder = Math.exp(-((y - .56) ** 2) / .007);
  const fold = .037 * shoulder * (.5 + .5 * Math.cos(9 * angle + 3 * y)) ** 3;
  return .365 * Math.sqrt(Math.max(0, 1 - cap * cap)) * (1 - fold);
}

function bagGeometry() {
  const profile = [];
  for (let i = 0; i <= 72; i++) {
    const y = (i / 72 - .5) * 1.52;
    profile.push(new THREE.Vector2(i === 0 || i === 72 ? 0 : .365, y));
  }
  const geometry = new THREE.LatheGeometry(profile, 80, Math.PI);
  const positions = geometry.attributes.position;
  const uv = geometry.attributes.uv;
  for (let i = 0; i < positions.count; i++) {
    const angle = (uv.getX(i) * 2 + 1) * Math.PI;
    const y = positions.getY(i);
    const radius = uv.getY(i) === 0 || uv.getY(i) === 1 ? 0 : bagRadius(y, angle);
    positions.setXYZ(i, Math.sin(angle)*radius, y, Math.cos(angle)*radius*.70);
  }
  geometry.computeVertexNormals();
  return geometry;
}

// Each sling follows the leather through its stitched foot, then runs taut to the swivel.
function slingGeometry(angle) {
  const vertices = [], indices = [], uvs = [];
  const tangent = .635, foot = .39, top = 1.078;
  const heights = Array.from({length:23}, (_, i) => foot + (tangent - foot) * i / 22);
  heights.push(top);
  for (const [row, y] of heights.entries()) {
    const lift = Math.max(0, (y - tangent) / (top - tangent));
    for (const [col, [edge,thickness]] of [[-1,.002],[1,.002],[1,.012],[-1,.012]].entries()) {
      const a = angle + edge * .12;
      const radius = bagRadius(Math.min(y,tangent),a) + thickness;
      const x = Math.sin(a)*radius, z = Math.cos(a)*radius*.70;
      vertices.push(THREE.MathUtils.lerp(x, .045*Math.sin(angle)+edge*.017*Math.cos(angle),lift),
        y, THREE.MathUtils.lerp(z, .045*Math.cos(angle)-edge*.017*Math.sin(angle)+thickness*.5,lift));
      uvs.push(col === 0 || col === 3 ? 0 : 1,(y-foot)/(top-foot));
      if (row) {
        const b=row*4+col, c=row*4+(col+1)%4;
        indices.push(b-4,c-4,c,b-4,c,b);
      }
    }
  }
  indices.push(0,2,1,0,3,2);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}
export const studioViews = {
  room: [[3.4,2.65,4.5],[0,1.85,-2.65]],
  pads: [[.74,2.18,.47],[0,1.92,-2.6]],
  area: [[-2.6,2.85,3.65],[.75,1.38,-2.87]]
};

export function setStudioView(camera, orbit, name='room') {
  const [eye, target] = studioViews[name];
  camera.position.fromArray(eye);
  orbit.target.fromArray(target);
  orbit.update();
}

export function fitStudio(scene) {
  const material = (color, roughness = .7, metalness = 0) => new THREE.MeshStandardMaterial({color, roughness, metalness});
  const felt = material('#8998a7', .93), dark = material('#243144'), metal = material('#8795a6', .37, .58);
  const ice = material('#a5c9e0'), enamel = material('#c7d1d6');
  felt.map = surface('#f4f5f6','#acb8c2',3,2);
  const concrete = material('#ffffff');
  concrete.map = surface('#a1a8ac','#8e9499',5,2);
  const rubber = material('#ffffff', .94);
  rubber.map = surface('#303e4d','#606e7a',12,10,true);
  function mesh(geometry, mat, x, y, z) {
    const object = new THREE.Mesh(geometry,mat);
    object.position.set(x,y,z); object.castShadow = true; object.receiveShadow = true;
    scene.add(object); return object;
  }
  const box = (w,h,d,mat,x,y,z) => mesh(new THREE.BoxGeometry(w,h,d),mat,x,y,z);
  const round = (w,h,d,r,mat,x,y,z) => mesh(new RoundedBoxGeometry(w,h,d,3,r),mat,x,y,z);
  const floor = mesh(new THREE.PlaneGeometry(16,16),rubber,0,-.015,-2);
  floor.rotation.x = -Math.PI/2;
  box(15,5.6,.2,concrete,0,2.75,-5.45);
  box(15,.13,.1,metal,0,.08,-5.28);
  // A continuous upholstered backing keeps the bags legible against the rear wall.
  box(8.4,3.10,.16,dark,0,2.04,-5.29);
  for (let row=0; row<2; row++) {
    for (const x of [-1.46,1.46]) round(2.90,1.44,.14,.028,felt,x,1.27 + row*1.47,-5.14);
  }
  const oak = material('#8c8176', .83);
  const diffuser = new THREE.MeshBasicMaterial({color:'#dde8ed'});
  const fins = new THREE.InstancedMesh(new THREE.BoxGeometry(.043,2.93,.11),oak,32);
  const transform = new THREE.Matrix4();
  for (let i=0;i<32;i++) {
    const x = (i<16 ? -1 : 1) * (3.03 + (i%16)*.071);
    fins.setMatrixAt(i,transform.makeTranslation(x,2.02,-5.10));
  }
  fins.receiveShadow=true;
  scene.add(fins);
  for (const x of [-2.98,2.98]) box(.019,2.91,.026,diffuser,x,2.02,-5.015);
  box(8.42,.09,.30,metal,0,.49,-5.13);
  box(5.86,.033,.05,diffuser,0,3.51,-5.12);
  const ceiling = box(14,.12,13,enamel,0,5.04,-1.3);
  ceiling.castShadow = false;
  box(.2,5.15,12,concrete,5.6,2.57,-1.05);
  // Side windows have reveals, mullions, a sill and a graded sky behind the glazing.
  const glassCanvas=document.createElement('canvas'); glassCanvas.width=8; glassCanvas.height=128;
  const gc=glassCanvas.getContext('2d'); const gradient=gc.createLinearGradient(0,0,0,128);
  gradient.addColorStop(0,'#8ca7be'); gradient.addColorStop(.62,'#e5e9e6'); gradient.addColorStop(1,'#bac2cd');
  gc.fillStyle=gradient;gc.fillRect(0,0,8,128);
  gc.fillStyle='rgba(120,140,155,.20)';gc.fillRect(0,90,3,38);gc.fillRect(4,80,2,48);gc.fillRect(6,96,2,32);
  const glazing=new THREE.CanvasTexture(glassCanvas);glazing.colorSpace=THREE.SRGBColorSpace;
  const glass=new THREE.MeshBasicMaterial({map:glazing});
  box(.24,1.05,11,concrete,-4.85,.5,-.4);
  box(.42,.1,11,enamel,-4.77,1.05,-.4);
  for(let i=0;i<6;i++){
    const z=-4.55+i*1.7;
    box(.095,3.58,1.67,glass,-4.92,2.92,z);
    box(.16,3.7,.075,metal,-4.77,2.9,z-.84);
    box(.16,.065,1.7,metal,-4.76,3.80,z);
  }
  for(const z of [-4.4,-1.6,1.2]){
    box(11,.16,.13,dark,0,4.9,z);
    box(3.4,.055,.22,enamel,0,4.78,z);
    box(3.28,.018,.18,diffuser,0,4.742,z);
  }
  // A recessed perimeter and two standing marks define the usable training area.
  const mat = material('#64788b',.94);
  mat.map = surface('#e0e4ea','#8292a4',7,7);
  mat.bumpMap = rubber.map;
  mat.bumpScale = .0012;
  round(4.45,.035,4.65,.017,mat,0,.012,-1.38);
  const piping = material('#a5b2bd',.9);
  for (const x of [-2.12,2.12]) box(.018,.004,4.40,piping,x,.032,-1.38);
  for (const z of [-3.58,.82]) box(4.25,.004,.018,piping,0,.032,z);
  for (const x of [-.32,.32]) {
    const stance = round(.09,.005,.26,.002,piping,x,.035,-.02);
    stance.rotation.y = -Math.sign(x)*.14;
  }
  const sun=new THREE.DirectionalLight('#fff2df',2.9);
  sun.position.set(-3.7,6.4,2.6);sun.target.position.set(.3,.4,-2.5);
  sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);
  Object.assign(sun.shadow.camera,{left:-7,right:7,bottom:-6,top:6,near:.2,far:22});
  sun.shadow.intensity=.53;sun.shadow.radius=3;sun.shadow.normalBias=.022;sun.shadow.bias=-.0002;
  scene.add(sun,sun.target,new THREE.HemisphereLight('#dee9f6','#596474',1.9));
  const fill = new THREE.DirectionalLight('#d4e7ff', .75);
  fill.position.set(3.8,3.4,.6);
  fill.target.position.set(0,1.8,-2.6);
  scene.add(fill,fill.target);
  const pads=[];
  // Wall-mounted training rail with paired strike pads, stitched edges and steel brackets.
  box(4.5,.15,.18,metal,0,3.72,-2.55);
  for(const x of [-1.85,1.85])box(.13,.14,2.8,dark,x,3.72,-3.88);
  const hide = new THREE.MeshPhysicalMaterial({
    color: '#ffffff', roughness: .54, clearcoat: .14, clearcoatRoughness: .55,
  });
  hide.map = bagCover();
  hide.bumpMap = surface('#777777','#cccccc',5,4);
  hide.bumpScale = .0018;
  const binding = material('#ffffff', .90);
  binding.side = THREE.DoubleSide;
  const weave = document.createElement('canvas');
  weave.width=64; weave.height=256;
  const thread=weave.getContext('2d');
  thread.fillStyle='#384657'; thread.fillRect(0,0,64,256);
  thread.fillStyle='#2e3a48';
  for(let y=0;y<256;y+=3) thread.fillRect(0,y,64,1);
  thread.fillStyle='#a4a5a2';
  for(let y=172;y<253;y+=7) for(const x of [6,56]) thread.fillRect(x,y,2,4);
  // Box-and-cross stitching transfers the load from the webbing to the cover.
  thread.strokeStyle='#a4a5a2';
  thread.lineWidth=2.4;
  thread.setLineDash([4,3]);
  thread.strokeRect(9,183,46,58);
  thread.beginPath();
  thread.moveTo(9,183);thread.lineTo(55,241);
  thread.moveTo(55,183);thread.lineTo(9,241);
  thread.stroke();
  binding.map=new THREE.CanvasTexture(weave);
  binding.map.colorSpace=THREE.SRGBColorSpace;
  for(const [x,yaw] of [[-.88,-.10],[.88,.10]]){
    const rig=new THREE.Group();rig.position.set(x,0,-2.55);rig.rotation.y=yaw;scene.add(rig);
    const part=(g,m,px,py,pz)=>{const o=new THREE.Mesh(g,m);o.position.set(px,py,pz);o.castShadow=o.receiveShadow=true;rig.add(o);return o;};
    const hanger=part(new THREE.CylinderGeometry(.025,.025,.67,20),metal,0,3.35,0);
    const mount=part(new RoundedBoxGeometry(.19,.11,.22,3,.018),dark,0,3.675,0);
    part(new THREE.SphereGeometry(.051,20,14),metal,0,3.015,0);
    part(new THREE.CylinderGeometry(.055,.082,.052,24),dark,0,2.986,0);
    for (const angle of [.97,-.97,Math.PI-.97,Math.PI+.97])
      part(slingGeometry(angle),binding,0,1.92,0);
    const face = part(bagGeometry(), hide, 0, 1.92, 0);
    pads.push({rig, hanger, mount, face});
  }
  // Low equipment bench: upholstered seat and tubular steel frame.
  round(2.35,.16,.60,.075,dark,2.6,.53,-3.82);
  for(const x of [1.66,3.54])for(const z of [-4.02,-3.62])box(.07,.48,.07,metal,x,.24,z);
  for(const x of [2.1,2.73]) {
    const handle=mesh(new THREE.CylinderGeometry(.034,.034,.37,16),metal,x,.70,-3.84);handle.rotation.z=Math.PI/2;
    for(const dx of [-.18,.18]){
      const weight=mesh(new THREE.CylinderGeometry(.105,.105,.12,6),dark,x+dx,.70,-3.84);weight.rotation.z=Math.PI/2;
    }
  }
  // Lower shelf and folded towels sit outside the striking lane.
  for(const z of [-4.0,-3.85,-3.70]) box(2.25,.036,.092,oak,2.6,.17,z);
  const ballMaterial = material('#384c63',.84);
  const ballGeometry = new THREE.SphereGeometry(.165,20,14);
  for (const x of [2.1,2.53]) mesh(ballGeometry,ballMaterial,x,.35,-3.84);
  const linen = material('#bcc5ce',.98);
  for (let i=0;i<2;i++) round(.44,.045,.28,.018,linen,3.38-i*.018,.635+i*.05,-3.82);
  return pads;
}
