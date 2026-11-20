<template>
  <div
    ref="container"
    class="fitness-scene training-arena"
    :tabindex="preview ? -1 : 0" :class="{ 'scene-preview': preview }"
    :aria-label="preview ? previewLabel : '交互训练空间，使用数字键1至5选择目标，空格暂停'"
  >
    <div v-if="error" class="scene-error">{{ error }}</div>
    <template v-if="!preview">
    <div class="view-controls" role="group" aria-label="训练视角">
      <button type="button" :aria-pressed="viewpoint === 'front'" @click="setViewpoint('front')">正对靶面</button>
      <button type="button" :aria-pressed="viewpoint === 'room'" @click="browseRoom">训练室全景</button>
    </div>
    <div class="arena-performance">
      <span
        >连击 <b>{{ view.streak }}</b></span
      ><span
        >正确率
        <b>{{ view.accuracy === null ? "—" : view.accuracy + "%" }}</b></span
      ><span
        >积分 <b>{{ view.score }}</b></span
      >
    </div>
    <div v-if="!trackingReady" role="status" class="scene-error">追踪丢失，训练已暂停。恢复控制器后，主动点击继续。</div>
    <div ref="vrMount" class="vr-entry"></div>
    <div class="arena-cue" :class="{ resting: view.resting, 'cue-stop': active && view.cue?.avoid }">
      <template v-if="!active">
        <span>{{ readying ? "靶面准备中" : intermission ? "组间休息" : "已暂停" }}</span>
        <small v-if="!readying && !intermission && program === 'rhythm' && view.cue">继续后击打{{ zoneNames[view.cue.index] }}</small>
      </template>
      <span v-else-if="view.resting">组间休息</span>
      <template v-else-if="view.recall">
        <span v-if="view.recall.phase === 'ready'">准备观察</span>
        <span v-else-if="view.recall.phase === 'watch'">观察 · 第 {{ view.recall.step + 1 }} 个</span>
        <span v-else>按原顺序选择 · {{ view.recall.step }} / {{ view.recall.count }}</span>
        <small v-if="view.recall.phase === 'watch' && view.recall.index !== null">{{ zoneNames[view.recall.index] }} · {{ view.recall.index + 1 }}</small>
        <small v-else-if="view.recall.phase === 'recall'">{{ touchInput ? '轻点靶面上的数字' : '点击靶面数字，或用数字键' }}</small>
        <small v-else>记住亮起的顺序</small>
        <div class="sequence-steps" aria-hidden="true">
          <i v-for="n in view.recall.count" :key="n"
            :class="{filled: n <= view.recall.step, current: n === view.recall.step + 1}">
            <b v-if="n === view.recall.step + 1" :style="{width: view.recall.progress * 100 + '%'}"></b>
          </i>
        </div>
      </template>
      <template v-else-if="view.cue">
        <span>{{ view.cue.avoid ? '停手' : program === 'focus' ? (touchInput ? '按住' : '停留') : (touchInput ? '轻点' : '点击') }} · {{ zoneNames[view.cue.index] }}</span>
        <small v-if="view.cue.avoid">等靶面上的计时条走完</small>
        <small v-else-if="touchInput">{{ program === 'focus' ? '按住亮条直到进度填满' : '轻点发光靶心' }}</small>
        <small v-else>{{ program === 'focus' ? '指针停在亮条上，或按住数字键' : '点击靶心，或按数字键' }} {{ view.cue.index + 1 }}</small>
      </template>
      <div v-if="active && view.cue && program === 'rhythm'" class="up-next">下一靶 <b>{{ zoneNames[rhythmTarget(view.serial)] }}</b></div>
      <div v-if="active && !view.resting && program === 'focus'" class="hold-track">
        <i :style="{ width: view.holdProgress * 100 + '%' }"></i>
      </div>
      <small v-if="view.resting"
        >{{
          Math.ceil((25000 - (view.elapsed % 25000)) / 1000)
        }}
        秒后继续</small
      >
    </div>
    <details ref="settingsPanel" class="spatial-settings" @toggle="onSettingsToggle"><summary>训练设置</summary>
      <button type="button" :aria-pressed="sound" @click="sound = !sound">{{ sound ? "关闭提示音" : "开启提示音" }}</button>
      <p>调整后可直接预览悬靶位置。</p>
      <label>参考高度 {{ calibration.height.toFixed(2) }} m <input aria-label="目标中心高度" type="range" min="0.8" max="2" step="0.05" :disabled="active" :value="calibration.height" @input="calibrate({height:Number($event.target.value)})" /></label>
      <label>单侧范围 {{ calibration.width.toFixed(2) }} m <input aria-label="单侧横向范围" type="range" min="0.4" max="1.2" step="0.05" :disabled="active" :value="calibration.width" @input="calibrate({width:Number($event.target.value)})" /></label>
      <button @click="exportPerformance">导出本次帧间隔报告</button>
    </details>
    <p v-if="viewpoint === 'room'" class="view-tip">拖动查看训练室，继续训练后回到正面</p>
    <p v-if="feedback" class="arena-feedback" :class="{ mistake: feedback.mistake }" role="status">{{ feedback.message }}</p>
    </template>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import * as THREE from "three";
import { fitStudio, setStudioView } from "../studio.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { VRButton } from "three/examples/jsm/webxr/VRButton.js";
import { instrumentPads, strikeZone, zoneNames } from "../strike-pads.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { defaultCalibration, trackedInputs, FrameProbe } from "../spatial.js";
import { bindXRVisibility } from "../xr-lifecycle.js";
import { Drill, rhythmTarget } from "../drills.js";
import { RecordedDrill } from "../replay.js";
import { getProgram } from "../catalog.js";
const props = defineProps({
  preview: Boolean,
  previewLabel: {type:String,default:"训练视角预览"},
  calibration: {type:Object,default:()=>({...defaultCalibration})},
  active: Boolean,
  readying: Boolean,
  intermission: Boolean,
  remaining: { type: Number, default: 60 },
  program: { type: String, default: "rhythm" },
  difficulty: { type: String, default: "easy" },
  compact: Boolean,
  replayCheckpoint: {type:Object,default:null},
  checkpoint: { type: Object, default: null },
  sessionKey: { type: String, default: "" },
  elapsedMs: { type: Number, default: null },
  interval: { type: Boolean, default: true },
});
const emit = defineEmits(["calibrate", "hit", "xr", "toggle", "pause", "finish", "metrics", "ready", "unavailable"]);
const container = ref(),
  vrMount = ref(),
  settingsPanel = ref(),
  error = ref(""),
  sound = ref(false),
  viewpoint = ref(props.preview ? "room" : "front"),
  touchInput = ref(window.matchMedia("(hover: none)").matches),
  hover = ref(-1),
  feedback = ref(null);
let drill,
  renderer,
  scene,
  camera,
  controls,
  observer,
  vrButton,
  hud,
  hudBoard,
  hudCanvas,
  hudContext,
  lastHud = "",
  controllers = [],
  targets = [],
  instrument,
  actions = [],
  labels = [],
  disposed = false,
  unbind = () => {},
  audio,
  lastFrame = 0,
  localElapsed = 0,
  lastEmit = 0,
  down = null,
  mousePosition = null,
  heldKey = -1,
  firstFrame = false,
  feedbackTimer,
  lastInput = -Infinity;
const trackingReady=ref(true), probe=new FrameProbe();
function calibrate(change){if(!props.active)emit("calibrate",{...props.calibration,...change});}
function exportPerformance(){const blob=new Blob([JSON.stringify(probe.report(),null,2)],{type:"application/json"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="vrfitai-frame-report.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const view = ref(new Drill().view());
const nextZone = ["LEFT MID", "RIGHT LOW", "LEFT HIGH", "RIGHT HIGH", "LEFT LOW"];
const info = computed(() => getProgram(props.program) || getProgram("rhythm"));
const pointer = new THREE.Vector2(),
  raycaster = new THREE.Raycaster(),
  rotation = new THREE.Matrix4();
function resetDrill() {
  try {
    drill = props.checkpoint
      ? RecordedDrill.restore(props.checkpoint, props.replayCheckpoint, props.interval)
      : new RecordedDrill(props.program, props.difficulty, props.interval);
    if (
      drill.data.program !== props.program ||
      drill.data.difficulty !== props.difficulty
    )
      drill = new RecordedDrill(props.program, props.difficulty, props.interval);
  } catch {
    drill = new RecordedDrill(props.program, props.difficulty, props.interval);
  }
  drill.data.interval = props.interval;
  localElapsed = drill.data.elapsed;
  view.value = drill.view();
  lastFrame = 0;
  lastEmit = 0;
  clearAim();
  feedback.value = null;
}
watch(() => [props.program, props.difficulty, props.sessionKey], resetDrill);
resetDrill();
function publish() {
  view.value = drill.view();
  emit("metrics", drill.snapshot());
}
function update(to) {
  const { hits, avoided, missed, cue } = drill.data;
  drill.advance(to, hover.value, props.active);
  if (drill.data.hits > hits) {
    instrument?.contact(cue.index, "dwell", performance.now());
    showFeedback("停留完成");
    emit("hit");
    beep();
  } else if (cue?.avoid && drill.data.avoided > avoided) {
    instrument?.contact(cue.index, "wait", performance.now());
    showFeedback("正确等待");
  } else if (cue?.recall && drill.data.missed > missed) {
    showFeedback("时间到 · 换下一组");
  } else if (drill.data.missed > missed && drill.data.cue && !drill.data.cue.avoid && !drill.data.cue.recall) {
    showFeedback("换靶 · " + zoneNames[drill.data.cue.index]);
  }
  view.value = drill.view();
}
function flush() {
  if (props.elapsedMs !== null && trackingReady.value) update(props.elapsedMs);
  publish();
  return drill.snapshot();
}
defineExpose({ flush, journal:()=>drill.journal(), setViewpoint });
function beep() {
  if (!sound.value) return;
  try {
    audio ||= new (window.AudioContext || window.webkitAudioContext)();
    audio.resume();
    const o = audio.createOscillator(),
      g = audio.createGain();
    o.type = "sine";
    const start = audio.currentTime;
    const hold = props.program === "focus";
    const end = start + (hold ? 0.15 : 0.11);
    o.frequency.setValueAtTime(hold ? 430 : 145, start);
    o.frequency.exponentialRampToValueAtTime(hold ? 510 : 52, end);
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(hold ? 0.045 : 0.17, start + 0.006);
    g.gain.exponentialRampToValueAtTime(0.0001, end);
    o.connect(g);
    g.connect(audio.destination);
    o.start();
    o.stop(end);
  } catch {
    sound.value = false;
  }
}
function showFeedback(message, mistake = false) {
  clearTimeout(feedbackTimer);
  feedback.value = {message, mistake};
  feedbackTimer = setTimeout(() => { feedback.value = null; }, 800);
}
function input(index, hand = "", intersection, gesture) {
  if (!props.active || (renderer?.xr.isPresenting && !trackingReady.value)) return;
  const now = performance.now();
  if (now - lastInput < 100) return;
  if (props.elapsedMs !== null) update(props.elapsedMs);
  const cue = drill.data.cue;
  if (props.program === "focus" || !cue) return;
  const recall = view.value.recall;
  if (gesture && (gesture.serial !== drill.data.serial || gesture.step !== recall?.step || gesture.phase !== recall?.phase)) return;
  if (recall && recall.phase !== "recall") return;
  lastInput = now;
  const hit = drill.input(index, hand);
  instrument?.contact(index, hit ? (recall ? "sequence" : "strike") : "wrong", now, intersection);
  if (hit) {
    const message = recall ? (recall.step + 1 === recall.count ? "完成一组" : "顺序正确") : "命中";
    showFeedback(message);
    emit("hit");
    beep();
  } else {
    showFeedback(recall ? "顺序不对 · 继续回想" : cue.avoid ? "误击 · 叉号亮起时等待" : hand && props.program === "rhythm" && index === cue.index
      ? "使用亮靶同侧手柄" : "误击 · 选择亮起的位置", true);
  }
  publish();
}
function clearAim() {
  down = null;
  mousePosition = null;
  heldKey = -1;
  hover.value = -1;
}
watch(() => props.active, active => {
  clearAim();
  clearTimeout(feedbackTimer);
  feedback.value = null;
  if (active) {
    if (settingsPanel.value) settingsPanel.value.open = false;
    if (viewpoint.value === "room") setViewpoint("front");
    container.value?.focus({preventScroll:true});
  }
});
function browseRoom() {
  if (props.active) emit("pause");
  setViewpoint("room");
}
function onSettingsToggle(event) {
  if (event.currentTarget.open && props.active) emit("pause");
}
function keyDown(event) {
  if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey || renderer?.xr.isPresenting) return;
  const target = event.target instanceof Element ? event.target : null;
  if (event.key === "Escape" && settingsPanel.value?.open) {
    event.preventDefault();
    settingsPanel.value.open = false;
    settingsPanel.value.querySelector("summary")?.focus();
    return;
  }
  if (target?.closest("input, textarea, select, [contenteditable]")) return;
  if (event.key === " " && target?.closest("button, a, summary")) return;
  if ((event.key === " " || event.key === "Escape" && props.active) && !props.readying) {
    event.preventDefault();
    if (!event.repeat) emit("toggle");
    return;
  }
  if (!props.active || !/^[1-5]$/.test(event.key) || event.repeat) return;
  event.preventDefault();
  heldKey = Number(event.key) - 1;
  if (props.program !== "focus") input(heldKey);
}
function keyUp(event) {
  if (/^[1-5]$/.test(event.key) && Number(event.key) - 1 === heldKey) heldKey = -1;
}
function setViewpoint(name) {
  if (!camera || !controls || renderer.xr.isPresenting) return;
  if (viewpoint.value !== name) {
    controls.enableDamping = false;
    controls.update();
    controls.enableDamping = true;
  }
  viewpoint.value = name;
  controls.enabled = name !== 'front';
  renderer.domElement.style.touchAction = name === 'front' ? 'pan-y' : 'none';
  if (name !== 'front') {
    setStudioView(camera, controls, name);
    return;
  }
  const halfWidth = 1.58;
  const depth = Math.max(4.0, halfWidth / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect));
  const center = 1.94 + props.calibration.height - defaultCalibration.height;
  camera.position.set(0, center + .19, -2.55 + depth);
  controls.target.set(0, center, -2.55);
  controls.update();
}
function resetView() {
  setViewpoint(props.preview ? "room" : "front");
}
function adjustPads() {
  instrument?.calibrate(props.calibration, props.compact);
  if (viewpoint.value === "front") setViewpoint("front");
}
watch(()=>[props.calibration.height, props.calibration.width, props.calibration.posture, props.compact],adjustPads);
function canvasLabel(text, color = "#d8e3d8") {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 128;
  const x = c.getContext("2d");
  x.font = "600 38px sans-serif";
  x.textAlign = "center";
  x.fillStyle = color;
  x.fillText(text, 128, 80);
  const texture = new THREE.CanvasTexture(c);
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(0.55, 0.275),
    new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
    }),
  );
  labels.push(texture);
  return m;
}
function build() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color("#26394b");
  camera = new THREE.PerspectiveCamera(43, 1, 0.1, 45);
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.65));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.xr.enabled = true;
  renderer.xr.setReferenceSpaceType("local-floor");
  container.value.appendChild(renderer.domElement);
  const mat = (c, r = 0.65, m = 0) =>
    new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
  function mesh(g, m, p) {
    const o = new THREE.Mesh(g, m);
    o.position.set(...p);
    o.castShadow = true;
    scene.add(o);
    return o;
  }

  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  instrument=instrumentPads(fitStudio(scene));
  targets=instrument.targets;
  adjustPads();
  for (const [i, text, color] of [
    [0, "PAUSE", "#a5d2e1"],
    [1, "FINISH", "#dbad86"],
    [2, "EXIT VR", "#bba7d5"],
  ]) {
    const o = mesh(new RoundedBoxGeometry(.74,.24,.08,3,.035),mat("#263547",.48,.18),[2.4,.8+i*.30,-3]);
    o.userData.action = ["toggle", "finish", "exit"][i];
    const l = canvasLabel(text, color);
    l.position.copy(o.position);
    l.position.z += 0.065;
    scene.add(l);
    o.userData.label=l;
    actions.push(o);
  }
  hudCanvas = document.createElement("canvas");
  hudCanvas.width = 1024;
  hudCanvas.height = 256;
  hudContext = hudCanvas.getContext("2d");
  hud = new THREE.CanvasTexture(hudCanvas);
  hudBoard = mesh(
    new THREE.PlaneGeometry(4.3, 1.075),
    new THREE.MeshBasicMaterial({ map: hud, transparent: true }),
    [0, 3.05, -5.1],
  );
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 1.7;
  controls.minAzimuthAngle=-.62;controls.maxAzimuthAngle=.76;
  controls.minPolarAngle=.90;
  controls.maxDistance = 9;
  controls.maxPolarAngle = Math.PI * 0.50;
  observer = new ResizeObserver(() => {
    const r = container.value.getBoundingClientRect();
    camera.aspect = r.width / Math.max(1, r.height);
    camera.updateProjectionMatrix();
    renderer.setSize(r.width, Math.max(1, r.height));
    if (viewpoint.value === "front") setViewpoint("front");
  });
  observer.observe(container.value);
  resetView();
  if (!props.preview) {
    const canvas = renderer.domElement;
    canvas.addEventListener("contextmenu", event => event.preventDefault());
    canvas.addEventListener("pointermove", event => {
      if (!event.isPrimary || (event.pointerType === "touch" && down?.id !== event.pointerId)) return;
      rememberPointer(event);
      if (down && Math.hypot(event.clientX - down.x, event.clientY - down.y) > 8) down.dragged = true;
    });
    canvas.addEventListener("pointerleave", () => { mousePosition = null; });
    canvas.addEventListener("pointerdown", event => {
      if (!event.isPrimary || event.button !== 0) return;
      down = {
        id: event.pointerId, x: event.clientX, y: event.clientY, dragged: false,
        serial: drill.data.serial, step: view.value.recall?.step, phase: view.value.recall?.phase,
      };
      rememberPointer(event);
      if (viewpoint.value === "front") canvas.setPointerCapture(event.pointerId);
      container.value.focus({preventScroll:true});
    });
    canvas.addEventListener("pointerup", event => {
      if (down?.id !== event.pointerId) return;
      const gesture = down;
      const moved = down.dragged || Math.hypot(event.clientX - down.x, event.clientY - down.y) > 8;
      down = null;
      if (!moved && props.active && props.program !== "focus") {
        const hit = intersectionAt(event.clientX, event.clientY);
        const index = strikeZone(hit);
        if (index !== -1) input(index, "", hit, gesture);
        else if (props.program === "rhythm" && drill.data.cue)
          showFeedback("瞄准" + zoneNames[drill.data.cue.index] + "的数字靶心");
      }
      if (event.pointerType === "touch") mousePosition = null;
    });
    canvas.addEventListener("pointercancel", clearAim);
    canvas.addEventListener("lostpointercapture", event => {
      if (down?.id === event.pointerId) clearAim();
    });
    window.addEventListener("keydown", keyDown);
    window.addEventListener("keyup", keyUp);
    window.addEventListener("blur", clearAim);
  }
  for (let i = 0; i < 2; i++) {
    const c = renderer.xr.getController(i);
    c.userData.hand = "";
    c.addEventListener("connected", (e) => {
      c.userData.hand = e.data.handedness || "";
    });
    c.addEventListener("disconnected", () => {c.userData.hand="";hover.value=-1;emit("pause");});
    c.addEventListener("select", () => {
      if(!trackingReady.value)return;
      setControllerRay(c);
      select(raycaster, c.userData.hand);
    });
    c.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(),
          new THREE.Vector3(0, 0, -5),
        ]),
        new THREE.LineBasicMaterial({ color: "#a9d5e5" }),
      ),
    );
    controllers.push(c);
    scene.add(c);
  }
  renderer.xr.addEventListener("sessionstart", () => {
    unbind();
    unbind = bindXRVisibility(renderer.xr.getSession(), () => emit("pause"));
    controls.enabled = false;
    camera.position.set(0, 0, 0);
    emit("xr", true);
  });
  renderer.xr.addEventListener("sessionend", () => {
    unbind();
    controls.enabled = true;
    resetView();
    emit("xr", false);
  });
}
function rememberPointer(event) {
  touchInput.value = event.pointerType === "touch";
  mousePosition = [event.clientX, event.clientY];
}
function intersectionAt(x, y) {
  const bounds = renderer.domElement.getBoundingClientRect();
  if (!bounds.width || !bounds.height || x < bounds.left || x > bounds.right || y < bounds.top || y > bounds.bottom) return null;
  pointer.set((x - bounds.left) / bounds.width * 2 - 1, 1 - (y - bounds.top) / bounds.height * 2);
  camera.updateMatrixWorld();
  raycaster.setFromCamera(pointer, camera);
  return raycaster.intersectObjects(targets, false)[0];
}
function setControllerRay(c) {
  rotation.identity().extractRotation(c.matrixWorld);
  raycaster.ray.origin.setFromMatrixPosition(c.matrixWorld);
  raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
}
function select(ray, hand = "") {
  const hit = ray.intersectObjects(renderer.xr.isPresenting ? [...targets, ...actions] : targets, false)[0];
  const o = hit?.object;
  if (!o) return;
  if (o.userData.action === "exit")
    renderer.xr
      .getSession()
      ?.end()
      .catch(() => (error.value = "请使用设备按钮退出 VR"));
  else if (o.userData.action) emit(o.userData.action);
  else {
    const index = strikeZone(hit);
    if (index !== -1) input(index, hand, hit);
  }
}
function hudPrompt(v) {
  if (!props.active) return "READY / PAUSED";
  if (v.resting) return "RECOVER";
  if (v.recall?.phase === "ready") return "GET READY";
  if (v.recall?.phase === "watch") return `WATCH ${v.recall.step + 1} / ${v.recall.count}`;
  if (v.recall?.phase === "recall") return `RECALL ${v.recall.step} / ${v.recall.count}`;
  if (v.cue?.avoid) return "WAIT / NO-GO";
  if (props.program === "focus") return `HOLD ${Math.round(v.holdProgress * 100)}%`;
  if (props.program === "rhythm") return v.cue?.index % 2 === 0 ? "LEFT / COMBO" : "RIGHT / COMBO";
  return "GO / SELECT";
}
function animate(t, frame) {
  if (disposed) return;
  probe.frame(t,renderer.xr.isPresenting);
  if(renderer.xr.isPresenting){
    const ready=trackedInputs(frame,renderer.xr.getReferenceSpace(),renderer.xr.getSession().inputSources,props.program);
    const wasReady=trackingReady.value;trackingReady.value=ready;
    if(!ready){if(wasReady){probe.losses++;if(drill.data.program==="focus" && drill.data.cue)drill.advance(drill.data.elapsed,-1,true);}hover.value=-1;emit("pause");}
    trackingReady.value=ready;
  }else trackingReady.value=true;
  const dt = lastFrame ? Math.min(250, t - lastFrame) : 0;
  lastFrame = t;
  if (props.active) {
    if (props.elapsedMs === null) localElapsed += dt;
    if (renderer.xr.isPresenting) {
      hover.value = -1;
      for (const c of controllers.filter(c=>c.visible && c.userData.hand)) {
        setControllerRay(c);
        const index = strikeZone(raycaster.intersectObjects(targets, false)[0]);
        if (index === drill.data.cue?.index) hover.value = index;
      }
    }
    if (!renderer.xr.isPresenting) {
      hover.value = heldKey !== -1 ? heldKey : mousePosition && !down?.dragged ? strikeZone(intersectionAt(...mousePosition)) : -1;
      const cue = drill.data.cue;
      const pointable = view.value.recall
        ? view.value.recall.phase === "recall" && hover.value !== -1
        : cue && !cue.avoid && cue.index === hover.value;
      renderer.domElement.style.cursor = down?.dragged && viewpoint.value !== "front" ? "grabbing" :
        pointable ? (props.program === "focus" ? "crosshair" : "pointer") :
        viewpoint.value === "front" ? "default" : "grab";
    }
    if(trackingReady.value)update(props.elapsedMs === null ? localElapsed : props.elapsedMs);
  }
  if (!props.preview && t - lastEmit > 200) {
    publish();
    lastEmit = t;
  }
  hudBoard.visible=renderer.xr.isPresenting;
  actions.forEach(o=>{o.visible=renderer.xr.isPresenting;o.userData.label.visible=o.visible;});
  const v = view.value;
  let cue = props.active && !v.resting ? v.cue : null;
  let kind = cue?.avoid ? "stop" : props.program === "focus" ? "hold" : "go";
  if (v.recall) {
    cue = props.active && v.recall.index !== null ? {index: v.recall.index} : null;
    kind = "watch";
  }
  instrument.paint(t, dt, {
    cue, kind, hold: v.holdProgress, hover: hover.value,
    recall: props.active && v.recall?.phase === "recall",
    remaining: kind === "stop" ? (cue.end - v.elapsed) / (cue.end - cue.start) : 0,
  });
  const text = `${hudPrompt(v)} · ${Math.ceil(props.remaining)}s · ${v.streak} COMBO`;
  const status = feedback.value?.message || (props.program === "rhythm" && props.active
    ? "NEXT / " + nextZone[rhythmTarget(v.serial)] : "PAUSE / FINISH / EXIT VR");
  const hudKey = text + status;
  if (renderer.xr.isPresenting && hudKey !== lastHud) {
    hudContext.clearRect(0, 0, 1024, 256);
    hudContext.textAlign = "center";
    hudContext.fillStyle = "#c6e4f0";
    hudContext.font = "600 38px sans-serif";
    hudContext.fillText(info.value.english, 512, 72);
    hudContext.font = "28px sans-serif";
    hudContext.fillText(text, 512, 136);
    hudContext.font = "19px sans-serif";
    hudContext.fillText(status, 512, 194);
    hud.needsUpdate = true;
    lastHud = hudKey;
  }
  controls.update();
  renderer.render(scene, camera);
  if (!props.preview && !firstFrame) {
    firstFrame = true;
    container.value.focus({ preventScroll: true });
    emit("ready");
  }
}
onMounted(async () => {
  try {
    build();
    renderer.setAnimationLoop(animate);
    if(props.preview)return;
    const supported =
      Boolean(navigator.xr) &&
      (await navigator.xr
        .isSessionSupported("immersive-vr")
        .catch(() => false));
    if (disposed) return;
    if (supported) {
      vrButton = VRButton.createButton(renderer);
      vrMount.value.appendChild(vrButton);
    }
  } catch {
    error.value = "当前设备无法创建 3D 场景，请使用支持 WebGL 的浏览器。";
    emit("unavailable");
  }
});
onBeforeUnmount(() => {
  publish();
  disposed = true;
  clearTimeout(feedbackTimer);
  window.removeEventListener("keydown", keyDown);
  window.removeEventListener("keyup", keyUp);
  window.removeEventListener("blur", clearAim);
  unbind();
  observer?.disconnect();
  renderer?.setAnimationLoop(null);
  renderer?.xr
    .getSession()
    ?.end()
    .catch(() => {});
  controls?.dispose();
  const gs = new Set(),
    ms = new Set();
  scene?.traverse((o) => {
    if (o.geometry) gs.add(o.geometry);
    if (o.material)
      for (const m of Array.isArray(o.material) ? o.material : [o.material])
        ms.add(m);
  });
  gs.forEach((g) => g.dispose());
  const textures = new Set([...ms].flatMap(m => [m.map, m.bumpMap]).filter(Boolean));
  textures.forEach(texture => texture.dispose());
  ms.forEach((m) => m.dispose());
  labels.forEach((t) => t.dispose());
  hud?.dispose();
  audio?.close();
  renderer?.dispose();
  renderer?.domElement.remove();
  vrButton?.remove();
});
</script>

<style scoped>
.up-next{padding-top:5px;margin-top:5px;border-top:1px solid #58758a;color:#bbcedc;font-size:11px}
.up-next b{font-weight:500;color:#e1eaf0;margin-left:5px}
#app .arena-cue.cue-stop{background:#532d2a;border-color:#faad95}
#app .arena-cue.cue-stop span,#app .arena-cue.cue-stop small{color:#ffddce}
.sequence-steps{display:flex;gap:4px;margin-top:7px}
.sequence-steps i{flex:1;height:4px;border-radius:2px;overflow:hidden;background:#4c5775}
.sequence-steps i.filled{background:#c5b7ee}
.sequence-steps i.current b{display:block;height:100%;background:#c5b7ee}
#app .training-arena:focus-visible{outline:2px solid #9edbf7!important;outline-offset:2px}
.view-controls{position:absolute;display:flex;gap:6px;top:14px;left:14px;z-index:4}
.view-controls button,.spatial-settings summary{border:1px solid #5e8199;background:#132b40eb;color:#e4f0f7;border-radius:4px;min-height:34px;padding:7px 9px;font:inherit;font-size:12px;cursor:pointer}
.view-controls [aria-pressed=true]{background:#c5e5f4;color:#19354a;border-color:#c5e5f4}
#app .arena-performance{top:14px;left:auto;right:14px;gap:12px;padding:6px 9px;background:#132b40eb;border-radius:4px}
#app .arena-performance b{margin-top:4px;font-size:18px}
#app .arena-cue{bottom:22px;max-width:calc(100% - 28px);width:max-content;padding:8px 16px;border-radius:7px}
.arena-feedback{position:absolute;left:14px;bottom:19px;z-index:3;margin:0;padding:5px 9px;background:#d6edf7;color:#16364b;border-radius:4px;font-size:12px;pointer-events:none}
.arena-feedback.mistake{background:#f8d1c5;color:#622b28}
.view-tip{position:absolute;bottom:72px;left:14px;font-size:12px;color:#e4edf5;background:#132b40eb;padding:4px 8px;border-radius:4px;pointer-events:none}
@media(max-width:640px){
  #app .arena-performance{top:57px;left:14px;right:auto}
  .arena-feedback{bottom:80px}
}
.spatial-settings{position:absolute;z-index:5;right:14px;bottom:84px;max-width:min(292px,85%);color:#d9ecf9;border-radius:5px;font-size:12px}
.spatial-settings[open]{padding:8px;background:#13273ef5;border:1px solid #486780}
.spatial-settings summary{display:list-item}
@media(max-width:640px){.spatial-settings{top:14px;bottom:auto}}
.spatial-settings summary{cursor:pointer}.spatial-settings label{display:block;margin:12px 0}.spatial-settings input{width:100%;margin:6px 0}.spatial-settings button{padding:8px;background:#24445d;color:#fff;border:1px solid #52738c}.spatial-settings p{line-height:1.6}.scene-error{z-index:8}
.scene-preview{position:relative;display:block;width:100%;height:100%;min-height:0;overflow:hidden;background:transparent}
.scene-preview :deep(canvas){position:absolute;inset:0;display:block;width:100%;height:100%}
</style>
