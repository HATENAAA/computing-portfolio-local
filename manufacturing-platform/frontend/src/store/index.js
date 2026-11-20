import { createStore } from "vuex";
import axios from "axios";

const store = createStore({
  state: {
    user: null,
    factory: null,
  },
  mutations: {
    setUser(state, user) {
      state.user = user;
    },
    setFactory(state, factory) {
      state.factory = factory;
    },
  },
  actions: {
    async login({ commit, dispatch }, credentials) {
      try {
        const response = await axios.post(
          "/api/users/login",
          new URLSearchParams(credentials),
        );
        commit("setUser", response.data); // 将用户信息存入 Vuex 的 user 状态
        dispatch("fetchFactory"); // 登录成功后立即获取工厂信息
      } catch (error) {
        console.error("Error during login:", error);
        throw error;
      }
    },
    async fetchFactory({ commit, state }) {
      if (state.user && state.user.factoryName) {
        try {
          const response = await axios.get(
            `/api/factories/factoryName/${state.user.factoryName}`,
          );
          commit("setFactory", response.data); // 将工厂信息存入 Vuex 的 factory 状态
        } catch (error) {
          console.error("Error fetching factory info:", error);
          throw error;
        }
      } else {
        console.error("User not found or does not have a factory assigned.");
      }
    },
  },
  getters: {
    user: (state) => state.user,
    factory: (state) => state.factory,
  },
});

export default store;
