<template>
  <div v-if="user" class="industrial-shell">
    <header class="industrial-header">
      <div class="industrial-brand"><span class="brand-symbol" aria-hidden="true"><i></i><i></i><i></i></span><b>MANU</b></div>
      <div class="plant-context">
        <AppIcon name="factory" />
        <div>
          <small>当前组织</small
          ><strong>{{ user.factoryName || "制造协作网络" }}</strong>
        </div>
      </div>
      <div class="industrial-user">
        <span>{{ roles[user.role] }}</span
        ><b>{{ user.realName || user.username }}</b
        ><button @click="help = true" aria-label="使用指南" title="使用指南">
          <AppIcon name="help" /></button
        ><button @click="logout" aria-label="退出登录" title="退出登录">
          <AppIcon name="logout" />
        </button>
      </div>
    </header>
    <div class="industrial-body">
      <aside class="module-rail">
        <nav aria-label="工作台模块">
          <router-link
            v-for="item in navigation"
            :key="item.id"
            :to="'/workspace/' + item.id"
            :title="item.name"
            ><AppIcon :name="item.icon" /><span>{{
              item.name
            }}</span></router-link
          >
        </nav>
      </aside>
      <div class="main-shell">
        <router-view />
      </div>
    </div>
  </div>
  <div v-else class="manu-public" :class="{ 'manu-landing': $route.name === 'home' }">
    <header class="manu-header">
      <router-link to="/" class="manu-brand" aria-label="MANU 制造协作首页">
        <span class="brand-symbol" aria-hidden="true"><i></i><i></i><i></i></span>
        <b>MANU</b><span class="manu-brand-label">制造协作</span>
      </router-link>
      <router-link v-if="$route.name === 'home'" to="/register" class="manu-header-action">创建账号</router-link>
    </header>
    <router-view />
  </div>
  <el-dialog v-model="help" title="订单执行流程" width="600px"
    ><div class="help-content">
      <h3>1. 提交与接单</h3>
      <p>经销商选择工厂、填写数量与交期；工厂在订单中心接单。</p>
      <h3>2. 排程与生产</h3>
      <p>
        为已接单订单分配设备和时间。系统检查设备归属、可用状态与时段冲突，再开始生产。
      </p>
      <h3>3. 报工与异常</h3>
      <p>
        分批记录合格及不良数量。设备维护前先暂停生产；高严重度异常需要处理后才能开始或完成。
      </p>
      <h3>4. 完成与追溯</h3>
      <p>
        合格数量达到订单量后可完成。排程、报工、异常及状态变更都保留在订单记录中。
      </p>
      <p class="muted">
        搜索订单可按 Ctrl / ⌘ K。排程使用北京时间。订单列表支持导出当前筛选结果。
      </p>
    </div></el-dialog
  >
</template>
<script>
import axios from "axios";
import AppIcon from "./components/AppIcon.vue";
import { visibleModules } from "./utils/modules";
export default {
  components: { AppIcon },
  data: () => ({
    help: false,
    roles: {
      superAdmin: "平台管理员",
      factoryAdmin: "工厂管理员",
      distributor: "经销商",
    },
  }),
  computed: {
    user() {
      return this.$store.state.user;
    },
    navigation() {
      return visibleModules(this.user.role);
    },
  },
  methods: {
    async logout() {
      try {
        await axios.post("/api/users/logout");
        this.$store.commit("setUser", null);
        this.$store.commit("setFactory", null);
        this.help = false;
        await this.$router.replace("/login");
      } catch {
        this.$message.error("退出失败，请重试");
      }
    },
  },
};
</script>
<style src="./styles/workspace.css"></style>

<style src="./styles/industrial.css"></style>

<style src="./styles/manu-public.css"></style>
