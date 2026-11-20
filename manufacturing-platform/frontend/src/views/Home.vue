<template>
  <main class="manu-home">
    <section class="manu-hero" aria-labelledby="manu-title">
      <div class="manu-intro">
        <h1 id="manu-title">制造执行工作台</h1>
        <p>处理订单、物料预留、设备排程与生产报工。</p>
        <router-link class="manu-action primary" to="/login">
          登录工作台 <AppIcon name="arrow" />
        </router-link>
        <dl class="manu-roles">
          <div>
            <dt>工厂管理员</dt>
            <dd>接单、备料、排程和报工</dd>
          </div>
          <div>
            <dt>经销商</dt>
            <dd>提交订单，跟踪进度和交付</dd>
          </div>
        </dl>
      </div>

      <figure class="manu-preview">
        <img src="/inventory-workbench.jpg" width="1280" height="720"
          alt="制造工作台的库存对账界面，显示在库余额、收发流水余额和有效预留">
        <figcaption>
          <span>物料与 BOM · 库存对账</span>
          <a class="manu-case-link" href="/inventory-workbench.jpg" target="_blank" rel="noopener">
            查看原尺寸 <span aria-hidden="true">↗</span>
          </a>
        </figcaption>
      </figure>
    </section>

    <section class="manu-module-list" aria-labelledby="module-heading">
      <h2 id="module-heading">业务模块</h2>
      <dl>
        <div v-for="module in modules" :key="module.name">
          <AppIcon :name="module.icon" />
          <dt>{{ module.name }}</dt>
          <dd>{{ module.detail }}</dd>
        </div>
      </dl>
    </section>
  </main>
</template>

<script setup>
import AppIcon from "../components/AppIcon.vue";

const modules = [
  { icon: "orders", name: "订单执行", detail: "接单状态、生产进度和交期" },
  { icon: "grid", name: "物料与 BOM", detail: "库存、预留快照与领料" },
  { icon: "schedule", name: "设备与排程", detail: "设备占用和时段冲突" },
  { icon: "quality", name: "质量与追溯", detail: "异常处理、报工与操作流水" },
];
</script>
