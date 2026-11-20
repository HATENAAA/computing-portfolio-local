<template>
  <main class="patient-home">
    <header><img src="../assets/img/menu06.png" alt="" /><span>熙心健康体检</span></header>
    <h1>体检服务</h1>
    <RouterLink to="/hospital" class="booking"><strong>预约体检</strong><span>选择体检机构、套餐和日期</span><span class="arrow" aria-hidden="true">→</span></RouterLink>
    <section aria-label="我的体检">
      <h2>我的体检</h2>
      <RouterLink to="/appointmentlist"><strong>预约记录</strong><span>查看或取消待检预约</span></RouterLink>
      <RouterLink to="/reportlist"><strong>体检报告</strong><span>查看总检结论和检查明细</span></RouterLink>
    </section>
    <Footer />
  </main>
</template>

<script setup>
import Footer from '../components/Footer.vue';
</script>

<style scoped>
.patient-home { min-height:100dvh; background:#f5f8fb; padding:24px 22px 94px; box-sizing:border-box; color:#1d3850; }
header { display:flex; gap:10px; align-items:center; font-weight:700; color:#2e587c; }
header img { width:32px; height:32px; object-fit:contain; }
h1 { margin:32px 0 18px; font-size:32px; }
h2 { margin:28px 0 10px; font-size:19px; }
a { display:grid; gap:6px; text-decoration:none; color:inherit; border-bottom:1px solid #dce6ed; padding:17px 1px; }
a span { color:#50687c; font-size:14px; }
.booking { position:relative; padding:22px 46px 22px 18px; background:#225b87; color:#fff; border:0; border-radius:12px; }
.booking strong { font-size:22px; }
.booking span { color:#e4eff8; }
.booking .arrow { position:absolute; right:18px; top:28px; font-size:23px; }
a:focus-visible { outline:3px solid #567ebf; outline-offset:3px; }
@media (hover:hover) { section a:hover { color:#215f96; } .booking:hover { background:#194a71; } }
</style>
