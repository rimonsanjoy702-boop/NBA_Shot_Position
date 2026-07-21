import { createRouter, createWebHistory } from 'vue-router'

import StatisticsPage from './pages/DemoPage.vue'
import HomePage from './pages/HomePage.vue'
import HexbinPage from './pages/HexbinPage.vue'
import HexbinClassicPage from './pages/HexbinClassicPage.vue'

const routes = [
    { path: '/', component: HomePage },
    { path: '/demo', component: StatisticsPage },
    { path: '/hexbin-classic', component: HexbinClassicPage },
    { path: '/hexbin', component: HexbinPage },
]

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})