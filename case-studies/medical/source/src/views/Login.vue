<template>
  <!-- 总容器 -->
  <div class="wrapper">
    <h1>熙心健康体检</h1>
    <form @submit.prevent="login">
      <label for="login-phone">手机号</label><div class="input-box">
        <i class="fa fa-user-o"></i>
        <input id="login-phone" type="tel" autocomplete="tel" v-model="users.userID" placeholder="输入手机号" />
      </div>
      <label for="login-password">密码</label><div class="input-box">
        <i class="fa fa-lock"></i>
        <input
          id="login-password" type="password" autocomplete="current-password"
          v-model="users.password"
          placeholder="输入登录密码"
        />
      </div>
      <div class="reg-box">
        <button type="button" @click="toRegister">注册</button>
        
      </div>
      <button class="button-box" type="submit">登录</button>
      <div class="demo-entry">
        <button type="button" @click="useDemo">使用示例账号</button>
        <a href="/doctor.html">进入医生端</a>
      </div>
    </form>
    
  </div>
</template>

<script>
import { reactive, toRefs } from "vue";
import { useRouter } from "vue-router";
import { setSessionStorage, removeSessionStorage } from "../common.js";
import service from "../request.js";


export default {
  setup() {
    const router = useRouter();
    const state = reactive({
      users: {
        userID: "",
        password: "",
      },
    });

    function login() {
      if (state.users.userID == "") {
        alert("请输入手机号");
        return;
      }
      if (state.users.password == "") {
        alert("请输入密码");
        return;
      }
      service
        .post("users/login", state.users)
        .then((response) => {
          const token = response.data;
          setSessionStorage('token', token);
          return service
          .get(`users/getUserByUserID?userID=${encodeURIComponent(state.users.userID)}`, { headers: { Authorization: `Bearer ${token}` } })
          .then((response) => {
            setSessionStorage('users', response.data);
            return router.push("/index");
          }); 
          
        })
        .catch(() => {
          removeSessionStorage('token');
          removeSessionStorage('users');
          alert("手机号或密码错误");
        });
    }
    function useDemo() {
      state.users.userID = "00000000001";
      state.users.password = "Patient-demo";
      login();
    }
    function toRegister() {
      router.push("/register");
    }
    return {
      ...toRefs(state),
      login,
      toRegister,
      useDemo
    };
  },
};
</script>

<style scoped>
.demo-entry { display:flex; gap:14px; align-items:center; justify-content:center; margin:12px 0; }
.demo-entry button, .demo-entry a { font:inherit; border:0; background:none; color:#16476f; text-decoration:underline; cursor:pointer; }

/*********************** 总容器 ***********************/
.wrapper {
  width: 100%;
  height: 100%;
  background-image: linear-gradient(45deg, #266c9f, #266c9f, #73a4cd);
  overflow: hidden;
}

/*********************** 标题部分 ***********************/
h1 {
  text-align: center;
  color: #fff;
  font-size: calc(var(--medical-vw) * 9.5);
  font-weight: 500;
  margin-top: 13vh;
  margin-bottom: 3vh;
}

/*********************** 内容部分 ***********************/
form {
  width: calc(var(--medical-vw) * 86);
  margin: 0 auto;
  background-color: #fff;
  border-radius: calc(var(--medical-vw) * 2.4);

  box-sizing: border-box;
  padding: calc(var(--medical-vw) * 6);
}

form .input-box {
  width: 100%;
  height: calc(var(--medical-vw) * 12);
  border: solid 1px #ccc;
  border-radius: calc(var(--medical-vw) * 2);
  margin-top: calc(var(--medical-vw) * 5);

  display: flex;
  align-items: center;
}

form .input-box i {
  margin: 0 calc(var(--medical-vw) * 3.6);
  font-size: calc(var(--medical-vw) * 5.4);
  color: #ccc;
}

form .input-box input {
  border: none;
  outline: none;
  flex-grow: 1;
  width: 90px;
}

form .reg-box {
  width: 100%;
  display: flex;
  justify-content: space-between;
  margin-top: calc(var(--medical-vw) * 5);
  margin-bottom: calc(var(--medical-vw) * 2);
}

form .reg-box p {
  font-size: calc(var(--medical-vw) * 3.3);
  color: #2d727e;
  user-select: none;
  cursor: pointer;
}

form .button-box {
  width: 100%;
  height: calc(var(--medical-vw) * 13);
  border-radius: calc(var(--medical-vw) * 2);
  background-color: #266c9f;

  text-align: center;
  line-height: calc(var(--medical-vw) * 13);
  font-size: calc(var(--medical-vw) * 4.6);
  color: #fff;
  letter-spacing: calc(var(--medical-vw) * 1);

  user-select: none;
  cursor: pointer;
}

.send_code {
  margin-right: calc(var(--medical-vw) * 1);
  font-size: calc(var(--medical-vw) * 3.3);
  cursor: pointer;
  color: #409eff;
  padding: 0 calc(var(--medical-vw) * 0.1);
}

.time {
  margin-right: calc(var(--medical-vw) * 1);
  font-size: calc(var(--medical-vw) * 3.3);
  cursor: pointer;
  color: #409eff;
  padding: 0 calc(var(--medical-vw) * 0.1);
}

/*********************** footer部分 ***********************/
footer {
  width: calc(var(--medical-vw) * 86);
  margin: 0 auto;
  margin-top: calc(var(--medical-vw) * 72);
  font-size: calc(var(--medical-vw) * 3.8);
  color: #fff;
}

footer div {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

footer div .line {
  width: calc(var(--medical-vw) * 22);
  height: 1px;
  background-color: #fff;
}

footer > p {
  text-align: center;
  margin-top: calc(var(--medical-vw) * 2);
}
.button-box{border:0;width:100%;cursor:pointer}.reg-box button{border:none;background:none;color:#266c9f;cursor:pointer}.wrapper label{color:#354e64;font-size:14px}</style>