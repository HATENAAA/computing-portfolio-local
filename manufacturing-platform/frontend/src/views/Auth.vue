<template>
  <main class="manu-auth">
    <section class="manu-auth-card" aria-labelledby="auth-title">
      <h1 id="auth-title">{{ registering ? "创建账号" : "登录工作台" }}</h1>
      <p v-if="notice && !registering" class="manu-form-notice" role="status">{{ notice }}</p>
      <form ref="form" @submit.prevent="submit" @invalid.capture="revealInvalidField">
        <fieldset class="manu-fields" :disabled="busy">
          <fieldset v-if="registering" class="manu-role-choice">
            <legend>账号角色</legend>
            <div class="manu-role-options">
              <label v-for="role in roles" :key="role.value" :class="{ selected: form.role === role.value }">
                <input type="radio" name="role" :value="role.value" v-model="form.role">
                <span><b>{{ role.label }}</b><small>{{ role.description }}</small></span>
              </label>
            </div>
          </fieldset>
          <label>
            用户名
            <input v-model.trim="form.username" name="username" autocomplete="username" autocapitalize="none"
              :pattern="registering ? '[a-z0-9_\\-]{3,64}' : undefined"
              :aria-describedby="registering ? 'username-hint' : undefined" maxlength="64" required>
            <small v-if="registering" id="username-hint">3–64 位小写字母、数字、下划线或短横线</small>
          </label>
          <div class="manu-password-field">
            <label for="manu-password">密码</label>
            <span class="manu-password">
              <input id="manu-password" v-model="form.password" name="password"
                :type="showPassword ? 'text' : 'password'"
                :autocomplete="registering ? 'new-password' : 'current-password'"
                :aria-describedby="registering ? 'password-hint' : undefined" required>
              <button type="button" :aria-pressed="showPassword" @click="showPassword = !showPassword"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'">{{ showPassword ? "隐藏" : "显示" }}</button>
            </span>
            <small v-if="registering" id="password-hint">10–72 字节。英文字母、数字及标点各占 1 字节。</small>
          </div>

          <fieldset v-if="registering && form.role === 'factoryAdmin'" class="manu-factory-fields">
            <legend>工厂资料</legend>
            <label>工厂名称<input v-model.trim="form.factoryName" required maxlength="100"></label>
            <label>工厂简介<textarea v-model.trim="form.factoryDescription" required maxlength="1000" rows="2"></textarea></label>
          </fieldset>
          <details v-if="registering" class="manu-extra-fields">
            <summary>补充联系资料（选填）</summary>
            <label>姓名<input v-model.trim="form.realName" autocomplete="name" maxlength="100"></label>
            <label>联系邮箱<input v-model.trim="form.contactEmail" type="email" autocomplete="email" maxlength="200"></label>
          </details>
        </fieldset>
        <p v-if="error" ref="error" class="manu-form-error" role="alert" tabindex="-1">{{ error }}</p>
        <button class="manu-action primary manu-submit" type="submit" :disabled="busy">
          {{ busy ? (registering ? "正在创建…" : "正在登录…") : (registering ? "创建账号" : "登录") }}
        </button>
      </form>
      <p class="manu-auth-switch">
        {{ registering ? "已有账号？" : "还没有账号？" }}
        <router-link :to="switchRoute">{{ registering ? "返回登录" : "创建账号" }}</router-link>
      </p>
      <section v-if="!registering" class="manu-demo" aria-labelledby="demo-heading">
        <h2 id="demo-heading">使用演示账号</h2>
        <p v-if="demoLoading" role="status">正在检查演示账号…</p>
        <p v-else-if="demoError" role="status">暂时无法读取演示账号。<button class="manu-text-button" type="button" @click="loadDemo">重试</button></p>
        <p v-else-if="!demoReady.demo_factory && !demoReady.demo_dealer" role="status">演示账号当前不可用。</p>
        <div v-else class="manu-demo-options">
          <button v-if="demoReady.demo_factory" class="manu-action secondary" type="button" :disabled="busy" @click="demo('factory')">体验工厂工作台</button>
          <button v-if="demoReady.demo_dealer" class="manu-action secondary" type="button" :disabled="busy" @click="demo('dealer')">体验经销商工作台</button>
        </div>
      </section>
    </section>
  </main>
</template>
<script>
import axios from "axios";
import { errorMessage } from "../utils/operations";
import { workspaceDestination } from "../router";

const blankForm = () => ({
  username: "", password: "", role: "factoryAdmin", realName: "", contactEmail: "",
  factoryName: "", factoryDescription: "",
});

export default {
  data: () => ({
    form: blankForm(),
    roles: [
      { value: "factoryAdmin", label: "工厂管理员", description: "创建并管理一家工厂" },
      { value: "distributor", label: "经销商", description: "提交并跟踪订单" },
    ],
    showPassword: false,
    demoReady: {},
    demoLoading: false,
    demoError: false,
    busy: false,
    error: "",
    notice: "",
  }),
  computed: {
    registering() { return this.$route.name === "register"; },
    switchRoute() {
      return { name: this.registering ? "login" : "register", query: this.$route.query.next ? { next: this.$route.query.next } : {} };
    },
  },
  mounted() {
    if (!this.registering) this.loadDemo();
  },
  watch: {
    registering(registering) {
      this.form.password = "";
      this.showPassword = false;
      this.error = "";
      if (registering) this.notice = "";
      else this.loadDemo();
    },
  },
  beforeRouteLeave() { return !this.busy; },
  beforeRouteUpdate() { return !this.busy; },
  methods: {
    revealInvalidField(event) {
      const details = event.target.closest("details");
      if (details) details.open = true;
    },
    async loadDemo() {
      this.demoLoading = true;
      this.demoError = false;
      try {
        const { data } = await axios.get("/api/auth/demo");
        this.demoReady = data.accounts;
      } catch {
        this.demoError = true;
      } finally {
        this.demoLoading = false;
      }
    },
    demo(role) {
      const username = "demo_" + role;
      if (!this.demoReady[username]) return;
      const password = role === "factory" ? "Demo-Factory-2026" : "Demo-Dealer-2026";
      return this.authenticate({ username, password });
    },
    async submit() {
      if (!this.registering) return this.authenticate({ username: this.form.username, password: this.form.password });
      if (this.busy) return;

      const { username, password, role, realName, contactEmail, factoryName, factoryDescription } = this.form;
      const bytes = new TextEncoder().encode(password).length;
      if (bytes < 10 || bytes > 72) {
        this.error = "密码长度需为 10–72 字节。";
        this.$refs.form.querySelector("#manu-password").focus();
        return;
      }

      this.error = "";
      this.busy = true;
      let created = false;
      try {
        await axios.post("/api/users/registerUser", {
          username, password, role, realName, contactEmail,
          ...(role === "factoryAdmin" ? { factoryName, factoryDescription } : {}),
        });
        created = true;
      } catch (error) {
        this.error = error.response?.status === 409
          ? (role === "factoryAdmin" ? "用户名或工厂名称已被使用，请换一个后重试。" : "用户名已被使用，请换一个后重试。")
          : errorMessage(error);
        this.$nextTick(() => this.$refs.error?.focus());
      } finally {
        this.busy = false;
      }
      if (created) {
        this.notice = "账号已创建。请输入密码登录。";
        this.form = { ...blankForm(), username };
        await this.$router.replace(this.switchRoute);
        this.$nextTick(() => this.$refs.form?.querySelector("#manu-password")?.focus());
      }
    },
    async authenticate(credentials) {
      if (this.busy) return;
      this.busy = true;
      this.error = "";
      let user;
      try {
        const { data } = await axios.post("/api/users/login", new URLSearchParams(credentials));
        user = data;
      } catch (error) {
        this.error = error.response?.status === 401
          ? "用户名或密码不正确。" : errorMessage(error);
        this.$nextTick(() => this.$refs.error?.focus());
      } finally {
        this.busy = false;
      }
      if (user) {
        this.$store.commit("setUser", user);
        await this.$router.replace(workspaceDestination(this.$route.query.next));
      }
    },
  },
};
</script>
