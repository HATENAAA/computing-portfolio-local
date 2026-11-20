<script setup>
import { watch, ref, computed, defineAsyncComponent, onMounted, nextTick } from "vue";
import { programs } from "../catalog.js";
import {deviceCapabilities} from "../capabilities.js";
import { difficulties } from "../drills.js";
const ShowcaseScene = defineAsyncComponent(() => import("./ShowcaseScene.vue"));
const props = defineProps({
  minutes: String,
  sessions: Number,
  configuration: { type: Object, required: true },
  setupOnly: Boolean,
});
const emit = defineEmits(["launch", "navigate", "configure", "explain"]);
const capability=ref(null),checkingDevice=ref(false);
async function checkDevice(){checkingDevice.value=true;capability.value=await deviceCapabilities();checkingDevice.value=false;}
onMounted(checkDevice);
const recommendation = ref(null), coachStatus=ref(''), decision=ref(null);
async function generateRecommendation(){
 coachStatus.value='正在分析';recommendation.value=null;decision.value=null;configure({recommendationId:undefined});
 try {const r=await fetch('/api/coach',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({program:selected.value.id,difficulty:difficulty.value,seconds:duration.value,mode:inputMode.value})});const v=await r.json();if(!r.ok)throw Error(v.error);recommendation.value=v;coachStatus.value='';}catch(e){coachStatus.value=e.message;}
}
async function chooseRecommendation(accepted){
 try{const r=await fetch('/api/coach/'+recommendation.value.id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision:accepted?'accepted':'declined'})});if(!r.ok)throw Error('确认失败，请重新生成建议');
 const value=accepted?recommendation.value.suggested:recommendation.value.baseline;
 configure({...value,recommendationId:recommendation.value.id});decision.value=accepted?'已采用建议':'已选择保持原设置';
 }catch(e){coachStatus.value=e.message;}
}
const inputMode=ref('desktop'), launchError=ref('');
function invalidate(){recommendation.value=null;decision.value=null;configure({recommendationId:undefined});}
const settings = ref(null);
const selected = computed(
  () =>
    programs.find((p) => p.id === props.configuration.program) || programs[0],
);
function configure(change) {
  emit("configure", { ...props.configuration, recommendationId:undefined, ...change });
}
const duration = computed({
  get: () => props.configuration.seconds,
  set: (seconds) => configure({ seconds }),
});
const difficulty = computed({
  get: () => props.configuration.difficulty,
  set: (difficulty) => configure({ difficulty }),
});
const compact = computed({
  get: () => props.configuration.compact,
  set: (compact) => configure({ compact }),
});
async function open(id) {
  configure({ program: id });
  await nextTick();
  settings.value?.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "instant"
      : "smooth",
    block: "start",
  });
  settings.value?.focus({preventScroll:true});
}
watch(() => [props.configuration.program,props.configuration.difficulty,props.configuration.seconds,props.configuration.recommendationId,inputMode.value], () => { if(props.configuration.recommendationId===recommendation.value?.id) return; decision.value=null; recommendation.value=null; });
function quickPractice() {
  emit("launch", { program:"rhythm", seconds:30, difficulty:"easy", compact:compact.value, calibration:props.configuration.calibration, mode:"desktop" });
}
async function launch() {
  launchError.value = "";
  if (inputMode.value === "vr") {
    await checkDevice();
    if (!capability.value?.available) {
      launchError.value = "当前设备无法进入 VR，请选择桌面模式。";
      return;
    }
  }
  emit("launch", {
    program: selected.value.id,
    seconds: duration.value,
    difficulty: difficulty.value,
    compact: compact.value,
    calibration: props.configuration.calibration,
    recommendationId: props.configuration.recommendationId,
    mode: inputMode.value,
  });
}
</script>
<template>
  <section class="training-lobby">
    <header class="lobby-header" v-if="!setupOnly">
      <a href="#/" aria-label="VRFitAI 首页">VRFit<span>AI</span></a
      ><span>{{ sessions || 0 }} 次训练 · {{ minutes || "0.0" }} 分钟</span>
    </header>
    <section class="lobby-positioning" v-if="!setupOnly">
      <h1>空间交互训练</h1>
      <p>初次体验可从左右节奏开始，按亮起的位置点击悬靶。</p>
      <div class="quick-practice"><button type="button" @click="quickPractice">试练 30 秒</button></div>
    </section>
    <div class="lobby-room" v-if="!setupOnly">
      <ShowcaseScene :program="selected.id" :difficulty="difficulty" :compact="compact" :calibration="configuration.calibration" />
      <div class="room-tag">训练室</div>
    </div>
    <section class="lobby-courses">
      <div class="lobby-label">
        <h1>选择训练课程</h1>
        <button @click="emit('navigate', '/workout')">自定义训练 →</button>
      </div>
      <div class="lobby-course-list">
        <button
          v-for="p in programs"
          :key="p.id"
          :class="['lobby-course', p.id]"
          :aria-pressed="selected.id === p.id"
          @click="open(p.id)"
        >
          <div>
            <h2>{{ p.title }}</h2>
            <span>{{ p.subtitle }}</span>
          </div>
          <span class="course-enter">↗</span>
        </button>
      </div>
    </section>
    <section class="inline-settings" ref="settings" tabindex="-1" aria-label="训练设置">
      <div class="settings-intro">
        <h2>{{ selected.title }}</h2>
        <p>{{ selected.caption }}</p>
        <details>
          <summary>操作说明</summary>
          <ol>
            <li v-for="step in selected.steps" :key="step">{{ step }}</li>
          </ol>
        </details>
      </div>
      <div class="settings-controls">
        <fieldset>
          <legend>训练时长</legend>
          <button
            v-for="t in [30, 60, 120, 300]"
            :key="t"
            :aria-pressed="duration === t"
            @click="duration = t"
          >
            {{ t < 60 ? t + " 秒" : t / 60 + " 分钟" }}
          </button>
        </fieldset>
        <fieldset>
          <legend>难度</legend>
          <button
            v-for="d in difficulties"
            :key="d.id"
            :aria-pressed="difficulty === d.id"
            @click="difficulty = d.id"
          >
            {{ d.label }}
          </button>
        </fieldset>
        <div v-if="inputMode === 'vr'" class="device-capability" aria-live="polite"><b>{{capability?.label||'正在检查 VR 能力'}}</b><p>{{capability?.reason}}</p><p>桌面记录点击／按键；VR 记录控制器射线选择与停留。</p><button class="capability-action" :disabled="checkingDevice" @click="checkDevice">重新检查设备</button></div>
        <fieldset><legend>输入模式</legend><button @click="invalidate();inputMode='desktop';launchError=''" :aria-pressed="inputMode==='desktop'">桌面</button><button @click="invalidate();inputMode='vr';launchError=''" :aria-pressed="inputMode==='vr'">VR</button></fieldset>
        <fieldset><legend>空间校准（进入训练后预览，暂停时可调整）</legend>
          <button v-for="posture in ['seated','standing']" :aria-pressed="configuration.calibration?.posture===posture" @click="configure({calibration:{version:1,posture,height:posture==='seated'?1.1:1.45,width:posture==='seated'?.65:1.1}})">{{ posture==='seated'?'坐姿':'站姿' }}</button>
        </fieldset>
        <label><input type="checkbox" v-model="compact" />小范围目标布局</label
        ><button class="start-inline" @click="launch">
          开始训练 ·
          {{ duration < 60 ? duration + " 秒" : duration / 60 + " 分钟" }} →
        </button>
        <p v-if="launchError" role="alert">{{ launchError }}</p>
      </div>
    </section>
    <details class="extra-guidance">
      <summary>训练建议与项目信息</summary>
    <section class="lobby-guidance" aria-live="polite">
      <div><a class="evaluation-link" href="/api/coach/evaluation" download>导出建议与后续表现</a><h2>下一次训练建议 <small>规则建议 · rules-1</small></h2>
        <p v-if="!recommendation">选择课程和难度后，根据最近同类训练及档案中的用力感生成建议。</p>
        <template v-else><p>{{ recommendation.reason }}</p>
          <p>有效样本 {{ recommendation.sampleCount }} / 至少 3 次</p>
          <p v-if="recommendation.basis">正确率 {{ recommendation.basis.accuracy }}% · 响应 {{ recommendation.basis.reactionMs }} ms · 漏过 {{ Math.round(recommendation.basis.missRate*100) }}% · 用力感 {{ recommendation.basis.effort }}/10</p>
          <button @click="emit('explain',recommendation.id)">用 AI 解释本条建议</button>
          <p>建议：{{ difficulties.find(d=>d.id===recommendation.suggested.difficulty)?.label }} · {{ recommendation.suggested.seconds }} 秒</p>
          <template v-if="!decision"><button @click="chooseRecommendation(true)">采用并填入设置</button> <button @click="chooseRecommendation(false)">保持原设置</button></template>
          <p v-else>{{ decision }}，点击开始训练以确认本次训练。</p>
        </template><p role="status">{{ coachStatus }}</p>
      </div><button @click="generateRecommendation">生成建议</button>
    </section>
      <p><RouterLink to="/project">项目能力与规则案例</RouterLink></p>
    </details>
  </section>
</template>

<style scoped>
.extra-guidance{grid-column:1/-1;border-top:1px solid #29435f;padding:12px 0;color:#adcadf}
.extra-guidance summary{cursor:pointer;padding:7px 0}
.extra-guidance a{color:#c2e4fa}

.training-lobby {
  max-width: 1400px;
  margin: auto;
  padding: 0 42px 34px;
  color: #e9efed;
  background: #142321;
  min-height: 100vh;
}
.lobby-header {
  height: 86px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ffffff18;
}
.lobby-header > a {
  font-size: 28px;
  letter-spacing: -1px;
  font-weight: 750;
  color: #fff;
  text-decoration: none;
}
.lobby-header > a > span {
  color: #b5d98f;
}
.lobby-header > span {
  color: #99aaa6;
  font-size: 12px;
}
.lobby-room {
  height: clamp(280px, 43vh, 440px);
  position: relative;
  margin-top: 20px;
  overflow: hidden;
  border-radius: 3px;
  background: #ced6ca;
}
.lobby-room :deep(.showcase-scene) {
  height: 100%;
  min-height: 0;
}
.room-tag {
  position: absolute;
  left: 22px;
  bottom: 19px;
  display: flex;
  gap: 80px;
  align-items: center;
  color: #34493e;
  background: #f0f4e7de;
  padding: 10px 14px;
  font-size: 12px;
  backdrop-filter: blur(8px);
  border-radius: 2px;
}
.room-tag > span {
  font-variant-numeric: tabular-nums;
  color: #71856d;
}
.lobby-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 27px 0 18px;
}
.lobby-label h1 {
  font-size: 20px;
  letter-spacing: 0;
  font-weight: 550;
}
.lobby-label button {
  border: 0;
  color: #b7c7bf;
  background: none;
  font-size: 12px;
  cursor: pointer;
}
.lobby-course-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.lobby-course {
  display: flex;
  align-items: center;
  gap: 15px;
  text-align: left;
  padding: 24px 20px;
  background: #21332f;
  border: 1px solid #3b4d45;
  border-radius: 3px;
  color: #fff;
  cursor: pointer;
  transition:
    background 0.2s,
    transform 0.2s;
}
.lobby-course:hover {
  background: #30473b;
  transform: translateY(-2px);
}
.lobby-course.focus {
  background: #283637;
  border-color: #425452;
}
.lobby-course.flow {
  background: #363831;
  border-color: #55574b;
}
.course-number {
  font: 12px monospace;
  color: #9bb799;
  align-self: flex-start;
  margin-top: 5px;
}
.lobby-course h2 {
  font-size: 18px;
  font-weight: 550;
  margin: 0 0 8px;
}
.lobby-course div > span {
  font-size: 11px;
  color: #b4c1b9;
}
.course-enter {
  margin-left: auto;
  font-size: 23px;
  color: #c0dba7;
}
#app .lobby-course.sequence .course-enter { color: #d2c3f6; }
@media (min-width: 801px) and (max-width: 1100px) {
  #app .lobby-course-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.lobby-course:focus-visible {
  outline: 2px solid #c9e7a8;
  outline-offset: 3px;
}
@media (max-width: 760px) {
  .training-lobby {
    padding: 0 20px 110px;
  }
  .lobby-header {
    height: 67px;
  }
  .lobby-header > a {
    font-size: 25px;
  }
  .lobby-room {
    height: 290px;
  }
  .lobby-course-list {
    grid-template-columns: 1fr;
  }
  .lobby-course {
    padding: 18px;
  }
  .lobby-label {
    margin-top: 24px;
  }
  .lobby-course h2 {
    font-size: 17px;
  }
}
</style>

<style scoped>
.lobby-guidance {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: space-between;
  padding: 19px 0 15px;
  border-bottom: 1px solid #ffffff14;
  margin-top: 8px;
}
.lobby-guidance h2 {
  font-size: 13px;
  font-weight: 550;
  margin: 0 0 8px;
  color: #c4d4c8;
}
.lobby-guidance h2 small {
  font-size: 10px;
  color: #869e8d;
  font-weight: 400;
  margin-left: 14px;
}
.lobby-guidance p {
  font-size: 12px;
  color: #a7b9af;
  margin: 0;
  line-height: 1.7;
}
.lobby-guidance button {
  border: 1px solid #52654e;
  background: transparent;
  color: #c6d9b5;
  white-space: nowrap;
  padding: 9px 14px;
  border-radius: 2px;
  font-size: 11px;
  cursor: pointer;
}
.lobby-instructions {
  font-size: 10px;
  color: #92a59a;
  line-height: 1.8;
  margin: 14px 0 65px;
}
.training-lobby {
  padding-bottom: 95px;
}
.lobby-room {
  height: clamp(250px, 36vh, 380px);
}
@media (max-width: 760px) {
  .lobby-guidance {
    gap: 12px;
  }
  .lobby-guidance h2 small {
    display: block;
    margin: 5px 0;
  }
  .lobby-instructions {
    margin-bottom: 25px;
  }
  .lobby-room {
    height: 250px;
  }
}
</style>

<style scoped>
.inline-settings {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 35px;
  background: #13273e;
  border: 1px solid #304863;
  border-radius: 5px;
  margin: 24px 0 15px;
  padding: 25px;
  color: #cdddea;
}
.settings-intro h2 {
  font-size: 19px;
  font-weight: 500;
  margin: 0 0 12px;
}
.settings-intro p,
.settings-intro details {
  font-size: 12px;
  color: #92aabd;
  line-height: 1.9;
}
.settings-intro summary {
  cursor: pointer;
  color: #b2cbdc;
}
.settings-intro ol {
  padding-left: 18px;
}
.settings-controls fieldset {
  border: 0;
  margin: 0 0 15px;
  padding: 0;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.settings-controls legend {
  font-size: 11px;
  color: #92aabd;
  margin-bottom: 9px;
}
.settings-controls button {
  border: 1px solid #3b5676;
  background: #162b44;
  color: #bdd4e2;
  border-radius: 3px;
  padding: 9px 14px;
  font-size: 12px;
  cursor: pointer;
}
.settings-controls button[aria-pressed="true"] {
  border-color: #9bcedb;
  background: #28485d;
  color: #fff;
}
.settings-controls label {
  font-size: 11px;
  color: #94b1c3;
  display: block;
  margin: 10px 0 16px;
}
.settings-controls .start-inline {
  background: #b3d9e5;
  color: #173247;
  border: 0;
  width: 100%;
  font-weight: 600;
  padding: 13px;
}
.lobby-course[aria-pressed="true"] {
  outline: 2px solid #9ac9db;
  outline-offset: -2px;
}
@media (max-width: 760px) {
  .inline-settings {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 20px;
    margin-bottom: 70px;
  }
}
</style>
