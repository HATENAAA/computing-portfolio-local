<script setup>
import {ref,computed} from 'vue';
import {coachExamples,exampleConfig} from '../coach-examples.js';
import {recommend} from '../coach.js';
import {difficulties} from '../drills.js';
import {targetPositions} from '../spatial.js';
const example=ref(coachExamples[0].id),posture=ref('standing');
const current=computed(()=>coachExamples.find(e=>e.id===example.value));
const result=computed(()=>recommend(current.value.records,exampleConfig));
const calibration=computed(()=>({version:1,posture:posture.value,height:posture.value==='seated'?1.1:1.45,width:posture.value==='seated'?.65:1.1}));
const positions=computed(()=>targetPositions(calibration.value));
const label=id=>difficulties.find(d=>d.id===id)?.label;
</script>
<template><section class="project-review">
  <header><p>VRFitAI · 实现与验证</p><h1>空间交互与下一次训练建议</h1><p>面向坐姿和站姿的 WebXR 目标交互原型。当前训练记录评价选择、停留与反应表现。</p></header>
  <div class="capability-grid"><article><h2>VR：设备路径</h2><p>桌面演示与 WebXR 控制器射线共用交互引擎；支持布局校准、追踪丢失暂停及主动恢复。</p><b>桌面与手机浏览器交互验收</b></article><article><h2>Fit：训练编排</h2><p>提供左右节奏、稳定停留、反应与抑制、顺序记忆四门课程，支持分组和休息。记录有效时间、交互表现与主观用力感。</p><b>课程编排 · 有效计时 · 交互记录</b></article><article><h2>AI：两种来源</h2><p>难度调整来自 rules-1 显式规则。可选语言模型负责解释规则依据和操作问题，由用户选择是否提供上下文。</p><b>规则建议默认可用 · 用户确认调整</b></article></div>
  <section class="review-panel"><h2>空间布局与校准</h2><p>切换姿态检查目标高度和横向分布；下图为正面投影，坐标取自训练场景同一函数。</p><div class="review-buttons"><button v-for="p in ['standing','seated']" :aria-pressed="posture===p" @click="posture=p">{{p==='standing'?'站姿':'坐姿'}}</button></div>
    <svg viewBox="0 0 520 300" role="img" :aria-label="(posture==='standing'?'站姿':'坐姿')+'目标分布示意，单位米'"><path d="M20 260H500 M260 20V260" stroke="#647d8c" fill="none"/><text x="25" y="283">地面 0 m</text><g v-for="(p,i) in positions" :key="i"><circle :cx="260+p[0]*120" :cy="260-p[1]*100" r="14" fill="#b3d9e5"/><text :x="260+p[0]*120" :y="265-p[1]*100" text-anchor="middle" fill="#10283d">{{i+1}}</text></g></svg>
    <p>中心 {{calibration.height}} m · 单侧 {{calibration.width}} m · 目标距用户约 2–2.6 m，以射线选择。</p><RouterLink to="/studio">在课程中配置与体验 →</RouterLink>
  </section>
  <section class="review-panel"><h2>规则建议测试样例</h2><p>以下四组合成训练记录调用实际规则引擎，分别展示冷启动、稳定表现、疲劳及漏过情形。案例与个人档案分别保存。</p><div class="review-buttons"><button v-for="e in coachExamples" :aria-pressed="example===e.id" @click="example=e.id">{{e.title}}</button></div>
    <h3>{{current.question}}</h3><p>共同设置：左右节奏 · 标准 · 桌面 · 60 秒</p><p>合成样本 {{result.sampleCount}} 条；预期：{{current.expected}}</p>
    <dl><dt>实际输出</dt><dd>{{label(result.suggested.difficulty)}} · {{result.suggested.seconds}} 秒</dd><dt>规则解释</dt><dd>{{result.reason}}</dd><template v-if="result.basis"><dt>依据</dt><dd>正确率 {{result.basis.accuracy}}% · 响应 {{result.basis.reactionMs}} ms · 漏过 {{Math.round(result.basis.missRate*100)}}% · 用力感 {{result.basis.effort}}/10</dd></template></dl>
  </section>
  <section class="review-panel"><h2>技术实现与验证</h2><ol><li>三维交互：空间参数独立于计分规则；双手与单手输入按课程检查，悬停和追踪恢复有独立状态。</li><li>系统一致性：有效时钟驱动事件日志；完整回放由服务端重算，UUID 幂等、409 冲突和持久待传共同保留记录。</li><li>个性化：同条件历史、至少三次样本、明确阈值和调整上限；用户确认，记录依据与后续表现。</li></ol><p>自动化测试覆盖训练状态、事件回放、规则建议和中断恢复；生产构建及桌面／手机宽度界面验收已完成。</p><RouterLink to="/assistant">查看可选 AI 解释助手 →</RouterLink></section>
</section></template>
<style scoped>
.project-review{max-width:1100px;margin:0 auto;padding:20px 0 70px;color:#d5e4ef}.project-review header>p,.project-review p,.project-review li{font-size:14px;line-height:1.9;color:#a9bfce}.project-review h1{font-size:32px;font-weight:550}.project-review h2{font-size:20px;font-weight:550}.capability-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}.capability-grid article,.review-panel{padding:24px;border:1px solid #38566d;background:#12283b;border-radius:8px}.capability-grid b{font-size:12px;color:#d5bd8f}.review-panel{margin:20px 0}.review-buttons{display:flex;flex-wrap:wrap;gap:10px}.review-buttons button{padding:10px 16px;border:1px solid #51758d;background:#1d364b;color:#d3e5ed;border-radius:5px;cursor:pointer}.review-buttons button[aria-pressed=true]{background:#b3d9e5;color:#10283d}.review-panel svg{display:block;max-width:520px;width:100%;height:auto;margin:10px auto}.review-panel svg text{font-size:13px;fill:#aec4d0}.review-panel svg g text{fill:#10283d}.review-panel a{color:#b3d9e5}.review-panel dl{display:grid;grid-template-columns:90px 1fr;font-size:14px;line-height:1.8;gap:12px}.review-panel dd{margin:0}.review-panel dt{color:#8daac0}@media(max-width:760px){.capability-grid{grid-template-columns:1fr}.project-review h1{font-size:25px}.review-panel,.capability-grid article{padding:18px}}
</style>
