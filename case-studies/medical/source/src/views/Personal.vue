<template>
  <main class="profile">
    <h1>个人中心</h1>
    <div class="account">
      <img src="../assets/img/user.png" alt="">
      <div>
        <strong>{{ user?.realName }}</strong>
        <p v-if="user">手机号 {{ user.userID }}</p>
      </div>
    </div>
    <section aria-label="个人服务">
      <RouterLink to="/appointmentlist">我的预约 <span aria-hidden="true">→</span></RouterLink>
      <RouterLink to="/reportlist">体检报告 <span aria-hidden="true">→</span></RouterLink>
      <button type="button" @click="logout">退出登录</button>
    </section>
    <Footer />
  </main>
</template>

<script setup>
import { useRouter } from 'vue-router';
import Footer from '../components/Footer.vue';
import { getSessionStorage, removeSessionStorage } from '../common.js';

const router = useRouter();
const user = getSessionStorage('users');
function logout() {
  removeSessionStorage('users');
  removeSessionStorage('token');
  router.replace('/login');
}
</script>

<style scoped>
.profile { color:#1d3850; padding:24px 22px 90px; }
h1 { font-size:26px; margin-bottom:18px; }
.account { display:flex; align-items:center; gap:14px; background:#eef5fb; border-radius:10px; padding:16px; }
.account img { width:46px; height:46px; object-fit:contain; }
.account p { color:#536b7e; margin-top:4px; }
section { margin-top:12px; }
section a, section button { display:flex; width:100%; box-sizing:border-box; align-items:center; justify-content:space-between; padding:15px 4px; border:0; border-bottom:1px solid #dce6ed; background:none; color:#225b87; font:inherit; text-decoration:none; cursor:pointer; text-align:left; }
:focus-visible { outline:2px solid #567ebf; outline-offset:2px; }
</style>
