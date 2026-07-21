import { createRouter, createWebHistory } from 'vue-router'

import StatisticsPage from './pages/DemoPage.vue'
import HomePage from './pages/HomePage.vue'
import HexbinPage from './pages/HexbinPage.vue'

const routes = [
    { path: '/', component: HomePage },
    { path: '/demo', component: StatisticsPage },
    { path: '/hexbin', component: HexbinPage },
]

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})