<template>
  <!-- 总容器 -->
  <div class="wrapper">
    <header>
      <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
      <p>注册</p>
      <div></div>
    </header>
    <div class="top-ban"></div>
    <h1>欢迎注册</h1>
    <table>
      <tr>
        <td>手机号码</td>
        <td>
          <input
            type="text"
            v-model="users.userID"
            placeholder="请输入手机号码"
          />
        </td>
      </tr>
      <tr>
        <td>真实姓名</td>
        <td>
          <input
            type="text"
            v-model="users.realName"
            placeholder="真实姓名便于查看体检报告"
          />
        </td>
      </tr>
      <tr>
        <td>生日</td>
        <td><input type="date" v-model="users.birthday" /></td>
      </tr>
      <tr>
        <td>性别</td>
        <td>
          <input
            type="radio"
            v-model="users.sex"
            name="gender"
            value="1"
            checked
          />男
          <input type="radio" v-model="users.sex" name="gender" value="0" />女
        </td>
      </tr>
      <tr>
        <td>身份证号</td>
        <td>
          <input
            type="text"
            v-model="users.identityCard"
            placeholder="请输入身份证号"
          />
        </td>
      </tr>
      <tr>
        <td>密码</td>
        <td>
          <input
            type="password"
            v-model="users.password"
            placeholder="请输入密码"
          />
        </td>
      </tr>

      <tr>
        <td>确认密码</td>
        <td>
          <input
            type="password"
            v-model="repassword"
            placeholder="请再次输入密码"
          />
        </td>
      </tr>
    </table>
    <div class="btn" @click="register">完成</div>
  </div>
</template>

<script>
import { reactive, toRefs, ref } from "vue";
import { useRouter } from "vue-router";
import service from '@/request.js';

export default {
  setup() {
    const router = useRouter();
    const state = reactive({
      users: {
        userID: "",
        password: "",
        realName: "",
        birthday: "",
        sex: 1,
        identityCard: "",
      },
      repassword: "",
    });
    function register (){
      if (state.users.userID == "") {
        alert("请输入手机号码");
        return;
      }
      if (state.users.password == "") {
        alert("请输入密码");
        return;
      }
      if (state.repassword == "") {
        alert("请再次输入密码");
        return;
      }
      if (state.users.birthday == ""){
        alert("生日不能为空");
        return;
      }
      if (state.users.identityCard == ""){
        alert("身份证号不能为空");
        return;
      }
      if (state.users.password != state.repassword) {
        alert("两次密码不一致");
        return;
      }
      service
      .post('users/register', state.users)
      .then((response) => {

        if(response.data == 'Create successful'){
          alert("注册成功");
          router.push('/login');
          return;
        }
        else{
          alert("注册失败");
        }
      })
      .catch((error) => {
        alert(typeof error.response?.data === "string" ? error.response.data : "注册失败，请检查输入。");
      });
    }
    return {
      ...toRefs(state),
      register
    };
  },
};
</script>

<style scoped>
.wrapper {
  width: 100%;
  height: 100%;
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

header {
  width: 100%;
  height: calc(var(--medical-vw) * 15.7);
  background-color: #fff;

  position: fixed;
  left: 0;
  top: 0;

  display: flex;
  align-items: center;
  justify-content: space-between;

  box-sizing: border-box;
  padding: 0 calc(var(--medical-vw) * 3.6);
}

header .fa {
  font-size: calc(var(--medical-vw) * 8);
}

/*********************** 标题部分 ***********************/
h1 {
  font-size: calc(var(--medical-vw) * 7.4);
  font-weight: 500;
  box-sizing: border-box;
  padding: 0 calc(var(--medical-vw) * 3.6);
  margin-top: calc(var(--medical-vw) * 6);
}

/*********************** common样式 ***********************/
.top-ban {
  width: 100%;
  height: calc(var(--medical-vw) * 15.7);
}

/*********************** table ***********************/
table {
  width: calc(var(--medical-vw) * 92.8);
  margin: 0 auto;
  margin-top: calc(var(--medical-vw) * 5);
  border-collapse: collapse;

  font-size: calc(var(--medical-vw) * 4.2);
}

table tr td {
  height: calc(var(--medical-vw) * 12);
  border-bottom: solid 1px #ddd;
  width: 50px;
}

table tr td input {
  border: none;
  outline: none;
  flex-grow: 1;
  width: 160px;
}

/*********************** btn ***********************/
.btn {
  width: calc(var(--medical-vw) * 92.8);
  margin: 0 auto;
  height: calc(var(--medical-vw) * 12);
  margin-top: calc(var(--medical-vw) * 8);
  background-color: #137e92;
  border-radius: calc(var(--medical-vw) * 2);
  color: #fff;
  font-size: calc(var(--medical-vw) * 5);
  text-align: center;
  line-height: calc(var(--medical-vw) * 12);

  user-select: none;
  cursor: pointer;
}
</style>