import { createRouter, createWebHistory } from "vue-router";
import store from "../store";
import Home from "../views/Home.vue";
import Auth from "../views/Auth.vue";
import OperationsWorkspace from "../views/OperationsWorkspace.vue";
import { visibleModules } from "../utils/modules";

const overview = "/workspace/overview";
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes: [
    { path: "/", name: "home", component: Home, meta: { guest: true } },
    { path: "/login", name: "login", component: Auth, meta: { guest: true } },
    { path: "/register", name: "register", component: Auth, meta: { guest: true } },
    { path: "/workspace/:section", component: OperationsWorkspace, meta: { auth: true } },
    { path: "/factoryAdmin", redirect: overview },
    { path: "/distributor", redirect: overview },
    { path: "/superadmin", redirect: overview },
    { path: "/factorymanagement", redirect: "/workspace/factories" },
    { path: "/usermanagement", redirect: "/workspace/users" },
    { path: "/devicemanagement", redirect: "/workspace/equipment" },
    { path: "/add-device/:factoryName", redirect: "/workspace/equipment" },
    { path: "/Home", redirect: "/" },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

router.beforeEach(to => {
  const user = store.state.user;
  if (to.meta.guest && user) return overview;
  if (!to.meta.auth) return;
  if (!user) return { name: "login", query: { next: to.fullPath } };
  if (!visibleModules(user.role).some(module => module.id === to.params.section)) return overview;
});

export function workspaceDestination(value) {
  return typeof value === "string" && /^\/workspace\/[a-z]+(?:\?|$)/.test(value) &&
    router.resolve(value).meta.auth ? value : overview;
}
export default router;
