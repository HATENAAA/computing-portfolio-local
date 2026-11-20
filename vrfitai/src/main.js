import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import "./style.css";
import "./review.css";
import "./visual-theme.css";
import "./product-experience.css";
import "./console-layout.css";
import "./fitness-product.css";
import "./unified-theme.css";
import "./acceptance-fixes.css";
const routes = ["/", "/studio", "/records", "/workout", "/assistant", "/project"].map((path) => ({
  path,
  component: { template: "<span></span>" },
}));

createApp(App)
  .use(createRouter({ history: createWebHashHistory(), routes, scrollBehavior: () => ({ top: 0, left: 0 }) }))
  .mount("#app");
