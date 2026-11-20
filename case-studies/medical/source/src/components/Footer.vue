<template>
  <footer aria-label="用户端导航">
    <RouterLink to="/index">体检服务</RouterLink>
    <RouterLink to="/appointmentlist">预约记录</RouterLink>
    <RouterLink to="/reportlist">体检报告</RouterLink>
    <RouterLink to="/personal">我的</RouterLink>
  </footer>
</template>

<style scoped>
footer { position:fixed; z-index:2; bottom:0; left:0; right:0; height:clamp(52px,14.2vw,68px); background:#fff; border-top:1px solid #dce6ed; display:grid; grid-template-columns:repeat(4,1fr); }
a { display:grid; place-items:center; text-align:center; text-decoration:none; font-size:13px; color:#43566f; }
a.router-link-active { color:#185884; font-weight:700; background:#edf5fc; }
a:focus-visible { outline:3px solid #567ebf; outline-offset:-4px; }
</style>
