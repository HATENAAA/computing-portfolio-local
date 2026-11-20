<template>
  <main class="appointment">
    <RouterLink to="/index">← 体检服务</RouterLink>
    <h1>用户体检预约</h1>
    <p>选择体检机构、套餐和预约日期。</p>
    <RouterLink class="continue" to="/hospital">选择体检机构 →</RouterLink>
  </main>
</template>

<style scoped>
.appointment { padding:24px; color:#243d55; }
.continue { display:inline-block; margin-top:24px; padding:12px 18px; background:#225b87; color:#fff; border-radius:8px; text-decoration:none; }
</style>
