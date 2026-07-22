import { createRouter, createWebHistory } from 'vue-router'

import HomePage from './pages/HomePage.vue'
import DashboardPage from './pages/DashboardPage.vue'

const routes = [
    { path: '/',           component: HomePage,      meta: { label: '首页',   icon: '🏠' } },
    { path: '/dashboard',  component: DashboardPage,  meta: { label: '仪表盘', icon: '📊' } },
]

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})
