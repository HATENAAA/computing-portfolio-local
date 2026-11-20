<script setup>
import {
  ref,
  computed,
  onMounted,
  onBeforeUnmount,
  watch,
  defineAsyncComponent,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import { Outbox } from "./outbox.js";
import { defaultCalibration } from "./spatial.js";
import UiIcon from "./components/UiIcon.vue";
import { Drill, difficulties, trainingWorkMs } from "./drills.js";
import { programs, getProgram } from "./catalog.js";
import { TrainingSession } from "./session.js";
import { RecoveryStore } from "./recovery.js";
const ProjectView=defineAsyncComponent(()=>import("./components/ProjectView.vue"));
const explanationId=ref(null),includeRecommendation=ref(false),responseModel=ref("");
function explain(id){explanationId.value=id;includeRecommendation.value=true;message.value="请解释这条规则建议的依据、调整幅度和局限。";router.push("/assistant");}
const DiscoverView = defineAsyncComponent(
  () => import("./components/DiscoverView.vue"),
);
function launchCourse(value) {
  if (preparing.value || ["running", "paused"].includes(engine.state) || pendingSave.value) {
    router.push("/studio");
    status.value = "请先完成当前训练，再开始新课程。";
    return;
  }
  chosen.value = value.program;
  duration.value = value.seconds;
  difficulty.value = value.difficulty || "easy";
  compact.value = !!value.compact;
  calibration.value = value.calibration || {...defaultCalibration};
  recommendationId.value = value.recommendationId;
  expectedMode.value = value.mode || "desktop";
  courseSelection.value = {
    program: chosen.value,
    seconds: duration.value,
    difficulty: difficulty.value,
    compact: compact.value,
    calibration:{...calibration.value},
  };
  state.value = "idle";
  preparing.value = true;
  sceneLoaded.value = false;
  sceneFailed.value = false;
  status.value = "";
  router.push("/studio");
}
const ProgressView = defineAsyncComponent(
  () => import("./components/ProgressView.vue"),
);
const WorkoutView = defineAsyncComponent(
  () => import("./components/WorkoutView.vue"),
);
const FitnessScene = defineAsyncComponent(
  () => import("./components/FitnessScene.vue"),
);
const route = useRoute(),
  router = useRouter();
const page = computed(() => route.path);
const courseSelection = ref({
  program: "rhythm",
  seconds: 120,
  difficulty: "easy",
  compact: false,
  calibration: {...defaultCalibration},
});
const chosen = ref("rhythm"),
  duration = ref(120),
  records = ref([]),
  analytics = ref({ allTime: { sessions: 0, seconds: 0, hits: 0 }, daily: [] }),
  loadingRecords = ref(false),
  status = ref(""),
  health = ref({ aiConfigured: false }),
  state = ref("idle"),
  seconds = ref(0),
  hits = ref(0),
  xr = ref(false),
  pendingSave = ref(null),
  saving = ref(false),
  message = ref(""),
  busy = ref(false),
  chat = ref([]),
  includeSummary = ref(false),
  chatError = ref("");
const engine = new TrainingSession();
const preparing = ref(false), sceneLoaded = ref(false), sceneFailed = ref(false);
const calibration=ref({...defaultCalibration}), recommendationId=ref(), expectedMode=ref("desktop");
const difficulty = ref("easy"),
  compact = ref(false),
  elapsedMs = ref(0),
  drillState = ref(null),
  replayState = ref(null),
  sceneRef = ref(null);
const performanceSummary = computed(() => {
  try {
    return drillState.value ? Drill.restore(drillState.value).view() : null;
  } catch {
    return null;
  }
});
function onMetrics(value) {
  drillState.value = value;
}
let timer,
  usedXR = false;
let recovery, outbox, syncing=false,
  lastPersist = 0;
function persist() {
  if (!recovery) return;
  try {
    if (engine.state === "running" || engine.state === "paused") {
      const checkpoint = sceneRef.value?.flush();
      if (checkpoint) {
        drillState.value = checkpoint;
        engine.hits = checkpoint.hits;
      }
    }
    const snapshot = engine.snapshot();
    replayState.value = sceneRef.value?.journal() || replayState.value;
    recovery.write({
      draft: snapshot
        ? {
            program: chosen.value,
            mode: usedXR ? "vr" : "desktop",
            ...(drillState.value ? { interaction: drillState.value } : {}),
            ...(replayState.value ? { replay: replayState.value } : {}),
            calibration: calibration.value,
            ...(recommendationId.value?{recommendationId:recommendationId.value}:{}),
            compact: compact.value,
            session: snapshot,
          }
        : null,
      pending: pendingSave.value,
    });
  } catch {
    status.value = "临时保存不可用，刷新前请先结束并保存训练。";
  }
}
function restore() {
  try {
    recovery = new RecoveryStore(window.sessionStorage);
    const { value, error } = recovery.read();
    if (error) status.value = error;
    if (!value) return;
    if (value.pending) {
      pendingSave.value = value.pending;
      state.value = "finished";
      drillState.value = value.pending.interaction || null;
      chosen.value = value.pending.program;
      seconds.value = value.pending.activeSeconds;
      hits.value = value.pending.hits;
      status.value = "已恢复待保存记录，请点击重试保存。";
    } else if (value.draft) {
      engine.restore(value.draft.session);
      drillState.value = value.draft.interaction || null;
      replayState.value = value.draft.replay || null;
      difficulty.value = drillState.value?.difficulty || "easy";
      compact.value = !!value.draft.compact;
      calibration.value=value.draft.calibration || {...defaultCalibration};
      recommendationId.value=value.draft.recommendationId;
      expectedMode.value=value.draft.mode;
      elapsedMs.value = value.draft.session.elapsedMs;
      chosen.value = value.draft.program;
      if (!drillState.value) {
        const d = new Drill(chosen.value, difficulty.value);
        d.data.hits = engine.hits;
        d.data.serial = engine.hits + 1;
        d.data.elapsed = value.draft.session.elapsedMs;
        d.spawn(d.data.elapsed);
        drillState.value = d.snapshot();
      }
      duration.value = value.draft.session.durationSeconds;
      usedXR = value.draft.mode === "vr";
      state.value = engine.state;
      elapsedMs.value = engine.milliseconds();
      seconds.value = Math.floor(elapsedMs.value / 1000);
      hits.value = engine.hits;
      status.value = "已恢复上次训练，点击继续；离开页面的时间不计入训练。";
    }
  } catch {
    status.value = "浏览器未允许临时保存，刷新前请先结束并保存训练。";
  }
}
function leave() {
  if (engine.state === "running") {
    engine.pause();
    state.value = engine.state;
  }
  persist();
}
const selected = computed(() => getProgram(chosen.value));
const remaining = computed(() =>
  state.value === "finished" ? 0 : Math.max(0, duration.value - seconds.value),
);
const totalMinutes = computed(() =>
  (analytics.value.allTime.seconds / 60).toFixed(1),
);
const sevenDays = computed(() =>
  analytics.value.daily.map((d) => ({
    label: d.day.slice(5),
    value: d.seconds / 60,
  })),
);
const active = computed(() => state.value === "running");
async function request(url, options) {
  let response;
  try{response=await fetch(url,options);}catch{throw new Error("无法连接服务，请检查连接后重试。");}
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "请求失败");
  return data;
}
async function loadRecords() {
  const [page, stats] = await Promise.all([
    request("/api/session-page"),
    request("/api/journal"),
  ]);
  records.value = page.items;
  analytics.value = { allTime: stats.totals, daily: stats.daily };
}
async function loadMoreRecords() {
  if (loadingRecords.value) return;
  loadingRecords.value = true;
  try {
    const page = await request(
      `/api/session-page?offset=${records.value.length}`,
    );
    const known = new Set(records.value.map((r) => r.id));
    records.value.push(...page.items.filter((r) => !known.has(r.id)));
  } catch (e) {
    status.value = e.message;
  } finally {
    loadingRecords.value = false;
  }
}
onMounted(async () => {
  restore();
  try{outbox=new Outbox(window.localStorage);}catch{status.value="长期离线保存不可用，请保留当前页面。";}
  retryOnline();
  if (["running", "paused"].includes(state.value))
    courseSelection.value = {
      program: chosen.value,
      seconds: duration.value,
      difficulty: difficulty.value,
      compact: compact.value,
      calibration: {...calibration.value},
    };
  timer = setInterval(() => {
    if (["running", "paused"].includes(engine.state)) {
      elapsedMs.value = engine.milliseconds();
      seconds.value = Math.floor(elapsedMs.value / 1000);
      hits.value = engine.hits;
    }
    if (engine.state === "running" && engine.milliseconds() >= engine.duration)
      finish();
    if (Date.now() - lastPersist >= 1000) {
      persist();
      lastPersist = Date.now();
    }
  }, 150);
  document.addEventListener("visibilitychange", visibility);
  window.addEventListener("pagehide", leave);
  window.addEventListener("online", retryOnline);
  try {
    health.value = await request("/api/health");
    await loadRecords();
  } catch (e) {
    status.value = "服务连接失败：" + e.message;
  }
});
onBeforeUnmount(() => {
  leave();
  clearInterval(timer);
  document.removeEventListener("visibilitychange", visibility);
  window.removeEventListener("pagehide", leave);
  window.removeEventListener("online", retryOnline);
});
async function retryOnline(){
 if(syncing)return;syncing=true;
 try{if(pendingSave.value)await save();
 for(const row of outbox?.entries()||[]){if(row.id===pendingSave.value?.id)continue;
 try{await request('/api/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(row)});outbox.remove(row.id);}catch(e){status.value='离线记录仍待补传：'+e.message;break;}}
 }finally{syncing=false;}
}
function visibility() {
  if (document.hidden && active.value) {
    engine.pause();
    state.value = engine.state;
    persist();
  }
}
function select(p) {
  if (["running", "paused"].includes(state.value)) return;
  chosen.value = p.id;
  duration.value = p.seconds;
}
function sceneReady() {
  sceneLoaded.value = true;
  if (preparing.value && expectedMode.value === "desktop" && !document.hidden) start();
}
function start() {
  if (preparing.value && (!sceneLoaded.value || expectedMode.value === "vr" && !xr.value)) return;

  if (pendingSave.value) {
    status.value = "请先保存上一条训练记录。";
    return;
  }
  if (engine.state === "paused") {
    engine.resume();
  } else if (engine.state !== "running") {
    engine.start(duration.value);
    const fresh = new Drill(chosen.value, difficulty.value);
    fresh.data.interval = true;
    drillState.value = fresh.snapshot();
    replayState.value = null;
    elapsedMs.value = 0;
    seconds.value = 0;
    hits.value = 0;
    usedXR = xr.value;
  }
  preparing.value = false;
  state.value = engine.state;
  status.value = "";
  persist();
  router.push("/studio");
}
function toggle() {
  if (engine.state === "running") engine.pause();
  else if (engine.state === "paused") engine.resume();
  else {
    start();
    return;
  }
  state.value = engine.state;
  persist();
}
function pauseFromXR() {
  if (engine.state !== "running") return;
  engine.pause();
  state.value = engine.state;
  persist();
}
function onHit() {
  engine.hit();
  hits.value = engine.hits;
}
function onXR(value) {
  xr.value = value;
  if (value) {
    usedXR = true;
    if (preparing.value && expectedMode.value === "vr") start();
  }
  if (!value && active.value) toggle();
}
async function finish() {
  const checkpoint = sceneRef.value?.flush();
  replayState.value = sceneRef.value?.journal() || replayState.value;
  if (checkpoint) {
    drillState.value = checkpoint;
    engine.hits = checkpoint.hits;
  }
  const result = engine.finish();
  if (result && chosen.value === "flow") {
    result.activeSeconds = Math.round(
      trainingWorkMs(chosen.value, engine.elapsed) / 1000,
    );
  }
  if (!result) return;
  state.value = engine.state;
  seconds.value = result.activeSeconds;
  if (result.activeSeconds < 1) {
    status.value = "练习不足 1 秒，未保存记录。";
    persist();
    return;
  }
  pendingSave.value = {
    ...result,
    ...(drillState.value ? { interaction: drillState.value } : {}),
    ...(replayState.value ? { replay: replayState.value } : {}),
    id: crypto.randomUUID(),
    program: chosen.value,
    mode: usedXR ? "vr" : "desktop",
    calibration:calibration.value,
    ...(recommendationId.value && expectedMode.value===(usedXR?"vr":"desktop")?{recommendationId:recommendationId.value}:{}),
  };
  persist();
  await save();
}
async function save() {
  if (!pendingSave.value || saving.value) return;
  saving.value = true;
  try {
    try{outbox?.put(pendingSave.value);}catch(e){status.value="离线保存不可用："+e.message;}
    await request("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pendingSave.value),
    });
    try{outbox?.remove(pendingSave.value.id);}catch{}
    pendingSave.value = null;
    persist();
    status.value = "训练记录已保存。";
    try {
      await loadRecords();
    } catch {
      status.value = "训练记录已保存，列表刷新失败，请稍后重试。";
    }
  } catch (e) {
    status.value = "保存失败，可重试：" + e.message;
  } finally {
    saving.value = false;
  }
}
watch(page, (value) => {
  if (status.value === "训练记录已保存。") status.value = "";
  if (value !== "/studio") {
    preparing.value = false;
    if (active.value) toggle();
  }
  if (value === "/assistant") refreshAIConfig();
  if (value === "/") loadRecords().catch((e) => (status.value = e.message));
});
async function refreshAIConfig() {
  try {health.value=await request("/api/health");chatError.value="";}
  catch(e){chatError.value="无法读取AI配置："+e.message;}
}
async function send() {
  const text = message.value.trim();
  if (!text || busy.value) return;
  busy.value = true;
  chatError.value = "";
  const messages = [...chat.value, { role: "user", content: text }].slice(-12);
  while (
    messages.reduce((n, m) => n + m.content.length, 0) > 7000 &&
    messages.length > 1
  )
    messages.shift();
  const last = records.value[0];
  const payload = { messages };
  if(includeRecommendation.value && explanationId.value)payload.recommendationId=explanationId.value;
  if (includeSummary.value && last)
    payload.summary = {
      program: last.program,
      activeSeconds: last.seconds,
      hits: last.hits,
    };
  try {
    const r = await request("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    responseModel.value=r.model;
    chat.value = [...messages, { role: "assistant", content: r.message }];
    message.value = "";
  } catch (e) {
    chatError.value = e.message;
  } finally {
    busy.value = false;
  }
}
function ask(text) {
  message.value = text;
  router.push("/assistant");
}
</script>
<template>
  <div
    class="shell"
    :class="{
      'discovery-shell': page === '/',
      'training-shell': page === '/studio',
    }"
  >
    <nav class="vr-dock" aria-label="训练功能">
      <RouterLink to="/" :class="{ current: page === '/' }"
        ><UiIcon name="courses" /><span>课程</span></RouterLink
      >
      <RouterLink to="/studio" :class="{ current: page === '/studio' }"
        ><UiIcon name="studio" /><span>训练</span></RouterLink
      >
      <RouterLink to="/workout"
        ><UiIcon name="plan" /><span>计划</span></RouterLink
      >
      <RouterLink to="/assistant"><UiIcon name="ai" /><span>助手</span></RouterLink>
      <RouterLink to="/records"
        ><UiIcon name="records" /><span>档案</span></RouterLink
      >
    </nav>
    <main>
      <div class="vr-identity" v-if="page !== '/'">
        <RouterLink to="/" aria-label="返回训练大厅"
          ><UiIcon name="back" /></RouterLink
        ><span
          >{{
            page === "/studio"
              ? state === "idle" && !preparing
                ? "选择训练"
                : selected.title
              : "VRFit"
          }}<small v-if="page !== '/studio'">AI</small></span
        ><span></span>
      </div>
      <ProjectView v-if="page === '/project'" />
      <section v-else-if="page === '/assistant'" class="model-workspace">
        <p>VRFitAI · 可选语言模型</p><h1>规则解释与使用助手</h1>
        <p>课程难度由规则计算。此处的模型可解释依据、回答操作问题；回复供你参考，采用设置仍需在课程页确认。</p>
        <p role="status" class="model-config-status">{{health.aiConfigured ? '模型服务已配置；实际可用性以请求结果为准。' : '尚未配置API Key。保存密钥后点击重新检查配置。'}}<button type="button" @click="refreshAIConfig">重新检查配置</button></p>
        <details class="model-setup" :open="!health.aiConfigured"><summary>如何启用DeepSeek助手</summary><ol><li>在DeepSeek开放平台创建API Key。</li><li>在 VRFitAI 项目目录的 .env 中设置 AI_API_KEY，重启本地服务。</li><li>保存后返回此页，点击“重新检查配置”。</li></ol></details>
        <p v-if="health.aiConfigured">服务配置模型：{{health.model}}</p>
        <div class="model-context"><label><input type="checkbox" v-model="includeSummary" :disabled="!records.length" />向模型提供最近一次训练的课程、有效秒数与命中次数</label>
        <label v-if="explanationId"><input type="checkbox" v-model="includeRecommendation" />向模型提供本条规则建议的统计依据和阈值说明</label><p>勾选的内容随消息发送给所配置的模型服务；默认不读取全部历史。取消勾选只影响后续请求，先前对话内容仍会随对话发送。</p></div>
        <div class="model-messages" aria-live="polite"><article v-for="(m,i) in chat" :key="i" :class="m.role"><b>{{m.role==='user'?'你':'模型解释'}}</b><p>{{m.content}}</p></article></div>
        <p v-if="responseModel">最近回复模型：{{responseModel}} · 解释不会自动改变训练设置</p>
        <form @submit.prevent="send"><label>你的问题<textarea v-model="message" rows="3" maxlength="2000" placeholder="例如：停留课程怎样才算完成？" /></label><button class="primary" :disabled="busy || !health.aiConfigured || !message.trim()">{{busy?'正在请求模型…':'发送给模型'}}</button></form>
        <p v-if="chatError" role="alert">{{chatError}}；你仍可返回课程使用规则建议。</p><RouterLink to="/">返回课程与规则建议 →</RouterLink>
      </section>
      <WorkoutView v-else-if="page === '/workout'" />
      <DiscoverView
        v-else-if="page === '/' || (page === '/studio' && state === 'idle' && !preparing)"
        :configuration="courseSelection"
        :setup-only="page === '/studio'"
        @configure="courseSelection = $event"
        @explain="explain"
        :minutes="totalMinutes"
        :sessions="analytics.allTime.sessions"
        @launch="launchCourse"
        @navigate="router.push($event)"
      />
      <template v-else-if="page === '/studio'"
        ><section class="greeting compact">
          <h1>{{ selected.title }}</h1>
          <p>{{ selected.description }}</p>
        </section>
        <section v-if="state === 'finished'" class="session-recap">
          <span>训练已结束</span>
          <h2>训练完成</h2>
          <div>
            <strong>{{ seconds }}<small>有效秒数</small></strong
            ><strong>{{ hits }}<small>目标命中</small></strong>
            <p>
              {{
                pendingSave
                  ? "记录等待保存，请使用下方重试。"
                  : seconds < 1
                    ? "本次不足1秒，未生成训练记录。"
                    : "本次练习已结束，可在训练档案回顾。"
              }}
            </p>
            <RouterLink to="/" class="recap-next">返回课程</RouterLink
            ><button @click="router.push('/records')">查看训练档案 ↗</button>
          </div>
          <div v-if="performanceSummary" class="recap-metrics">
            <span
              ><b>{{
                performanceSummary.accuracy === null
                  ? "—"
                  : performanceSummary.accuracy + "%"
              }}</b
              >交互正确率</span
            ><span
              ><b>{{ performanceSummary.bestStreak }}</b
              >最长连击</span
            ><span
              ><b
                >{{ performanceSummary.mistakes }} /
                {{ performanceSummary.missed }}</b
              >误选 / 漏过</span
            ><span
              ><b>{{
                performanceSummary.reactionMs === null
                  ? "—"
                  : performanceSummary.reactionMs + " ms"
              }}</b
              >{{
                chosen === "focus" ? "目标完成中位时长" : "响应中位时长"
              }}</span
            ><span v-if="chosen === 'flow'"
              ><b>{{ performanceSummary.avoided }}</b
              >正确等待红色提示</span
            >
          </div>
          <p class="recap-note">
            以上为交互表现，不是动作质量或身体能力评分。{{
              chosen === "flow" ? "有效秒数已扣除课内恢复时间。" : ""
            }}
          </p>
        </section>
        <div class="studio-grid" v-if="state !== 'finished' || pendingSave">
          <div class="stage" v-if="state!=='finished'">
            <p v-if="preparing && !sceneLoaded && !sceneFailed" class="stage-loading" role="status">正在加载训练室…</p>
            <FitnessScene
              :key="chosen"
              ref="sceneRef"
              :session-key="engine.startedAt || 'ready'"
              :difficulty="difficulty"
              :calibration="calibration"
              @calibrate="calibration=$event;persist()"
              :compact="compact"
              :checkpoint="drillState"
              :replay-checkpoint="replayState"
              :elapsed-ms="elapsedMs"
              @metrics="onMetrics"
              :active="active"
              :readying="preparing"
              @ready="sceneReady"
              @unavailable="sceneFailed = true"
              :remaining="remaining"
              :program="chosen"
              @hit="onHit"
              @xr="onXR"
              @toggle="toggle"
              @pause="pauseFromXR"
              @finish="finish"
            />
          </div>
          <section
            class="card session-controls"
            :class="{ 'session-live': ['running', 'paused'].includes(state) }"
          >
            <span class="pill">{{
              state === "running"
                ? "正在训练"
                : state === "paused"
                  ? "已暂停"
                  : state === "finished"
                    ? "本次已结束"
                    : preparing ? (sceneFailed ? "场景不可用" : sceneLoaded && expectedMode === "vr" ? "等待进入 VR" : "准备训练室") : "准备开始"
            }}</span>
            <div class="timer">
              {{ String(Math.floor(remaining / 60)).padStart(2, "0") }}:{{
                String(remaining % 60).padStart(2, "0")
              }}
            </div>
            <p>课程剩余时间</p>
            <div class="hit-stat">
              <strong>{{ hits }}</strong
              ><span>命中</span>
            </div>
            <div class="session-course-info">
              <span
                >{{
                  duration < 60 ? duration + " 秒" : duration / 60 + " 分钟"
                }}
                ·
                {{ difficulties.find((d) => d.id === difficulty)?.label }}</span
              >
            </div>
            <template v-if="preparing">
              <button v-if="sceneLoaded && expectedMode === 'desktop'" class="primary" type="button" @click="start">开始训练</button>
              <p v-if="sceneLoaded && expectedMode === 'vr'">选择训练室里的 VR 按钮进入头显。</p>
              <button class="secondary" type="button" @click="router.push('/')">返回课程</button>
            </template>
            <template v-else-if="['running', 'paused'].includes(state)">
              <button class="primary" @click="toggle">
                {{ active ? "暂停训练" : "继续训练" }}</button
              ><button class="secondary" @click="finish">
                结束并保存
              </button></template
            ><button
              v-if="pendingSave"
              class="secondary"
              :disabled="saving"
              @click="save"
            >
              重试保存
            </button>
            <p class="micro">
              记录计时与交互命中，不测量姿势或运动强度。体验不适时请停止。
            </p>
          </section>
        </div></template
      >
      <ProgressView v-else-if="page === '/records'" />
      <p v-if="status" class="status" role="status">{{ status }}</p>
    </main>
  </div>
</template>

<style>
.training-shell .stage{position:relative}
.stage-loading{position:absolute;z-index:4;inset:0;display:grid;place-items:center;margin:0;color:#d2e6f1;pointer-events:none}
@media(max-width:760px){
  #app .training-shell .stage {height:clamp(380px,53svh,530px);min-height:380px}
}
</style>
