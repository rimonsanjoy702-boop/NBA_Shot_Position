import { createRouter, createWebHistory } from 'vue-router'

import HomePage from './pages/HomePage.vue'
import HexbinPage from './charts/hexbin/HexbinPage.vue'
import HexbinClassicPage from './charts/hexbin/HexbinClassicPage.vue'
import FullCourtHexbinPage from './charts/hexbin/FullCourtHexbinPage.vue'
import ThreePointComparePage from './charts/three-point/ThreePointComparePage.vue'
import SankeyDemoPage from './charts/sankey/SankeyDemoPage.vue'

const routes = [
    // 主页面路由 (带 GlobalNavBar)
    { path: '/',            redirect: '/space' },
    { path: '/space',       component: () => import('./pages/SpaceExplorerPage.vue'),   meta: { label: '空间探索', icon: '🏀' } },
    { path: '/evolution',   component: () => import('./pages/EvolutionTrendsPage.vue'), meta: { label: '演化趋势', icon: '📈' } },
    { path: '/structure',   component: () => import('./pages/ShotStructurePage.vue'),   meta: { label: '投篮结构', icon: '🔀' } },

    // 图表单独页面路由
    { path: '/hexbin-classic', component: HexbinClassicPage },
    { path: '/hexbin-fullcourt', component: FullCourtHexbinPage },
    { path: '/hexbin', component: HexbinPage },
    { path: '/three-point-compare', component: ThreePointComparePage },
    { path: '/sankey', component: SankeyDemoPage },
]

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})
