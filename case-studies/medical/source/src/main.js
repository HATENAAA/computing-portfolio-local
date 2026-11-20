import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { getSessionStorage } from './common.js'

import 'font-awesome/css/font-awesome.min.css'

router.beforeEach((to) => {
    const publicPage = ['/', '/login', '/register'].includes(to.path);
    const token = getSessionStorage('token');
    if (!publicPage && (typeof token !== 'string' || !token.trim())) return '/login';
    return true;
});

createApp(App).use(router).mount('#app')
