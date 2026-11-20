import * as THREE from 'three';

// The leather pads carry five addressable regions. Feedback meshes never participate in hit tests.
export const zoneNames=['左靶中部','右靶下部','左靶上部','右靶上部','左靶下部'];
const layouts=[
  [{index:2,offset:.28},{index:0,offset:0},{index:4,offset:-.28}],
  [{index:3,offset:.21},{index:1,offset:-.21}]
];
const ready = new THREE.Color('#8dd6fa');
const violet = new THREE.Color('#cbbafa');
const noGo = new THREE.Color('#f0a78f');
const ink = '#102d45';
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
function faceMark() {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  let last = '';

  function draw(kind, progress = 0, label = '') {
    const steps = Math.round(48 * progress);
    const key = kind + steps + label;
    if (key === last) return;
    last = key;
    ctx.clearRect(0, 0, 256, 128);
    ctx.lineJoin = ctx.lineCap = 'round';
    ctx.lineWidth = 15;
    ctx.strokeStyle = ctx.fillStyle = ink;

    if (kind === 'go') {
      // Brackets lead the eye to the contact point. The number doubles as the desktop key.
      ctx.beginPath();
      ctx.arc(128, 64, 53, 0, Math.PI * 2);
      ctx.fillStyle = '#11263a';
      ctx.fill();
      ctx.lineWidth = 8;
      ctx.strokeStyle = '#bdefff';
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(128, 64, 42, 0, Math.PI * 2);
      ctx.fillStyle = '#96dbff';
      ctx.fill();
      ctx.fillStyle = ink;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = 'bold 59px sans-serif';
      ctx.fillText(label, 128, 66);
      for (const side of [-1, 1]) {
        ctx.beginPath();
        ctx.moveTo(128 + side * 108, 43);
        ctx.lineTo(128 + side * 83, 64);
        ctx.lineTo(128 + side * 108, 85);
        ctx.lineWidth = 17;
        ctx.strokeStyle = ink;
        ctx.stroke();
        ctx.lineWidth = 8;
        ctx.strokeStyle = '#d5f3ff';
        ctx.stroke();
      }
    } else if (kind === 'hold') {
      ctx.beginPath();
      ctx.roundRect(3, 7, 250, 114, 16);
      ctx.fillStyle = '#14334f';
      ctx.fill();
      ctx.lineWidth = 10;
      ctx.strokeStyle = '#527b9b';
      ctx.beginPath();
      ctx.arc(128, 64, 43, 0, Math.PI * 2);
      ctx.stroke();
      if (steps > 0) {
        ctx.strokeStyle = '#b9ebff';
        ctx.beginPath();
        ctx.arc(128, 64, 43, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * steps / 48);
        ctx.stroke();
      }
      ctx.fillStyle = '#d6eeff';
      ctx.fillRect(114, 48, 9, 32);
      ctx.fillRect(133, 48, 9, 32);
    } else if (kind === 'number' || kind === 'watch') {
      ctx.beginPath();
      ctx.roundRect(3, 7, 250, 114, 12);
      ctx.fillStyle = kind === 'watch' ? '#d4c7ff' : '#142b45ef';
      ctx.fill();
      ctx.strokeStyle = '#a593df';
      ctx.lineWidth = 5;
      ctx.stroke();
      ctx.fillStyle = kind === 'watch' ? ink : '#e5dcff';
      ctx.font = '600 72px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, 128, 68);
    } else if (kind === 'correct' || kind === 'wrong') {
      ctx.beginPath();
      ctx.arc(128, 64, 48, 0, Math.PI * 2);
      ctx.fillStyle = kind === 'wrong' ? '#ffc8b4' : '#d0eeff';
      ctx.fill();
      ctx.beginPath();
      if (kind === 'wrong') {
        ctx.moveTo(110, 46); ctx.lineTo(146, 82);
        ctx.moveTo(146, 46); ctx.lineTo(110, 82);
      } else {
        ctx.moveTo(103, 63); ctx.lineTo(120, 79); ctx.lineTo(152, 47);
      }
      ctx.lineWidth = 12;
      ctx.stroke();
    } else if (kind === 'stop') {
      ctx.fillStyle = '#ffc0a8';
      ctx.beginPath();
      ctx.roundRect(3, 7, 250, 114, 12);
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(105, 32); ctx.lineTo(151, 78);
      ctx.moveTo(151, 32); ctx.lineTo(105, 78);
      ctx.stroke();
      ctx.fillStyle = '#8e483d';
      ctx.fillRect(21, 94, 214, 12);
      ctx.fillStyle = ink;
      ctx.fillRect(21, 94, 214 * steps / 48, 12);
    }
  }
  return { canvas, draw };
}

// Cache the affected vertices once per strike, then release the leather back to its rest shape.
function leatherResponse(face) {
  const positions = face.geometry.attributes.position;
  const rest = positions.array.slice();
  let weights = [];
  let lastDepth = 0;
  function press(depth) {
    if (depth === lastDepth) return;
    for (const [offset, weight] of weights)
      positions.array[offset] = rest[offset] - depth * weight;
    positions.needsUpdate = true;
    face.geometry.computeVertexNormals();
    lastDepth = depth;
  }
  function locate(x, y) {
    press(0);
    weights = [];
    for (let offset = 2; offset < rest.length; offset += 3) {
      if (rest[offset] <= 0) continue;
      const dx = rest[offset - 2] - x, dy = rest[offset - 1] - y;
      const weight = Math.exp(-55 * dx * dx - 44 * dy * dy);
      if (weight > .008) weights.push([offset, weight]);
    }
  }
  return {locate, press};
}

// The print uses the very same UVs and vertex buffer as the leather, including during indentation.
const circumference = 2 * Math.PI * .365;
const bagHeight = 1.52;
const centerV = .5 + .02 / bagHeight;

function surfacePrint(face, zones) {
  const canvas = document.createElement('canvas');
  canvas.width = 768;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.generateMipmaps = false;
  texture.minFilter = THREE.LinearFilter;
  const inkLayer = new THREE.Mesh(face.geometry, new THREE.MeshBasicMaterial({
    map:texture, transparent:true, depthWrite:false, toneMapped:false,
    polygonOffset:true, polygonOffsetFactor:-1, polygonOffsetUnits:-1,
  }));
  inkLayer.visible = false;
  face.add(inkLayer);
  const symbol = faceMark(), badge = faceMark();
  let previous = '';
  function stamp(mark, kind, u, v, width, height, label, progress=0) {
    mark.draw(kind,progress,label);
    ctx.drawImage(mark.canvas, u*circumference-width/2, (1-v)*bagHeight-height/2,width,height);
  }
  return function paint({zone,kind,progress,aimed,recall,impact,phase}) {
    inkLayer.visible = Boolean(zone || recall || impact);
    if (!inkLayer.visible) { previous = ''; return; }
    const frame = reduced.matches ? 0 : Math.round(phase*24);
    const key = [zone?.index,kind,Math.round(progress*48),aimed,recall,impact?.start,frame].join('/');
    if (key === previous) return;
    previous = key;
    ctx.setTransform(canvas.width/circumference,0,0,canvas.height/bagHeight,0,0);
    ctx.clearRect(0,0,circumference,bagHeight);
    if (recall) for (const z of zones)
      stamp(symbol,'number',.5,centerV+z.offset/bagHeight,.45,.212,String(z.index+1));
    if (zone) {
      const scale = aimed && !reduced.matches ? 1.1 : 1;
      stamp(symbol,kind,.5,centerV+zone.offset/bagHeight,.54*scale,.25*scale,String(zone.index+1),progress);
    }
    if (impact) {
      const {u,v,kind:effect} = impact;
      const x = u*circumference, y = (1-v)*bagHeight;
      ctx.save();
      ctx.globalAlpha = reduced.matches ? 1 : Math.min(1,(1-phase)*2.5);
      if (!reduced.matches && effect !== 'wrong') {
        const radius = .045+.21*(1-(1-phase)**2);
        ctx.strokeStyle = effect === 'wait' ? '#efb79f' : effect === 'sequence' ? '#d9caff' : '#c7eaff';
        ctx.lineWidth = .011*(1-phase)+.003;
        ctx.beginPath(); ctx.arc(x,y,radius,0,Math.PI*2); ctx.stroke();
        if (effect === 'strike' && phase < .40) {
          for (let i=0;i<6;i++) {
            const a = i*Math.PI/3+.32, length=radius+.034*(1-phase/.4);
            ctx.beginPath();ctx.moveTo(x+radius*Math.cos(a),y+radius*Math.sin(a));
            ctx.lineTo(x+length*Math.cos(a),y+length*Math.sin(a));ctx.stroke();
          }
        }
      }
      stamp(badge,effect === 'wrong' ? 'wrong' : 'correct',u+.035,v+.048,.21,.12,'');
      ctx.restore();
    }
    texture.needsUpdate = true;
  };
}

// UV coordinates are interpolated on the current, deformed triangle at the ray intersection.
export function strikeZone(hit) {
  if (!hit?.uv) return -1;
  const side = hit.object.userData.bagSide;
  const {x:u,y:v} = hit.uv;
  const height = (v-centerV)*bagHeight;
  if (!layouts[side] || Math.abs(u-.5) > Math.asin(.27/.365)/(2*Math.PI) || Math.abs(height) > .49)
    return -1;
  return layouts[side].reduce((a,b)=>Math.abs(a.offset-height)<Math.abs(b.offset-height) ? a : b).index;
}

export function instrumentPads(pads) {
  const instruments = pads.map(({rig,hanger,mount,face},side)=>{
    const pivotY = 3.015, swing = new THREE.Group();
    swing.position.y = pivotY;
    for (const child of [...rig.children]) {
      if (child === hanger || child === mount) continue;
      child.position.y -= pivotY;
      swing.add(child);
    }
    rig.add(swing);
    face.userData.bagSide = side;
    face.material = face.material.clone();
    return {
      rig,hanger,swing,face,pivotY,baseX:rig.position.x,angle:0,velocity:0,impact:null,
      zones:layouts[side],leather:leatherResponse(face),print:surfacePrint(face,layouts[side]),
    };
  });
  function calibrate({height,width,posture},compact){
    for (const p of instruments) {
      const spread = Math.abs(p.baseX)*(width/1.1)*(compact ? .73 : 1);
      // Keep clearance for the full diameter of both suspended bags.
      p.rig.position.x = Math.sign(p.baseX)*Math.max(.40,spread);
      p.swing.scale.y = posture==='seated' ? .84 : 1;
      p.swing.position.y = p.pivotY+height-1.45+(1.94-p.pivotY)*(1-p.swing.scale.y);
      const shaftLength=3.685-p.swing.position.y;
      p.hanger.scale.y=shaftLength/.67;
      p.hanger.position.y=3.685-shaftLength/2;
    }
  }
  function contact(index,kind,now,hit){
    const p = instruments[index%2], zone=p?.zones.find(z=>z.index===index);
    if (!zone) return;
    const local = hit && p.face.worldToLocal(hit.point.clone());
    p.leather.locate(local?.x ?? 0, local?.y ?? .02+zone.offset);
    p.impact = {kind,start:now,u:hit?.uv.x ?? .5,v:hit?.uv.y ?? centerV+zone.offset/bagHeight};
    if (kind==='strike' && !reduced.matches) p.velocity=Math.min(1.35,p.velocity+.95);
  }
  function paint(now,dt,{cue,hold,hover,kind,recall,remaining}){
    const seconds=Math.min(.035,Math.max(0,dt/1000));
    for (const p of instruments) {
      if (reduced.matches) p.angle=p.velocity=0;
      else {p.velocity+=(-95*p.angle-11*p.velocity)*seconds;p.angle+=p.velocity*seconds;}
      p.swing.rotation.x=p.angle;
      const age=p.impact ? Math.max(0,now-p.impact.start) : Infinity;
      const duration=p.impact?.kind==='dwell'?620:480;
      if (age>=duration) p.impact=null;
      p.leather.press(p.impact?.kind==='strike' && !reduced.matches && age<220 ? .082*Math.sin(Math.PI*age/220) : 0);
      const zone=p.zones.find(z=>z.index===cue?.index);
      p.face.material.emissive.copy(kind==='stop'?noGo:kind==='watch'?violet:ready);
      p.face.material.emissiveIntensity=zone?.index!==undefined ? .075 : 0;
      p.print({zone,kind,recall,aimed:zone && zone.index===hover && kind==='go',
        progress:kind==='hold'?hold:kind==='stop'?remaining:0,impact:p.impact,phase:Math.min(1,age/duration)});
    }
  }
  return {targets:instruments.map(p=>p.face),calibrate,contact,paint};
}
