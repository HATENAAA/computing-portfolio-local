import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import axios from "axios";
import ElementPlus from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import "element-plus/dist/index.css";
const raw = axios.create();
axios.interceptors.request.use(async (config) => {
  if (
    !["get", "head", "options"].includes((config.method || "get").toLowerCase())
  ) {
    const { data } = await raw.get("/api/auth/csrf");
    config.headers[data.headerName] = data.token;
  }
  return config;
});
axios.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401) {
      store.commit("setUser", null);
      store.commit("setFactory", null);
      if (router.currentRoute.value.meta.auth) {
        router.replace({ name: "login", query: { next: router.currentRoute.value.fullPath } });
      }
    }
    return Promise.reject(e);
  },
);
axios
  .get("/api/users/me")
  .then(({ data }) => store.commit("setUser", data))
  .catch(() => {})
  .finally(() =>
    createApp(App).use(router).use(store).use(ElementPlus, {locale:zhCn}).mount("#app"),
  );
