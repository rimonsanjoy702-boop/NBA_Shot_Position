import { createRouter, createWebHistory } from 'vue-router'

import HomePage from './pages/HomePage.vue'
import HexbinPage from './charts/hexbin/HexbinPage.vue'
import HexbinClassicPage from './charts/hexbin/HexbinClassicPage.vue'
import FullCourtHexbinPage from './charts/hexbin/FullCourtHexbinPage.vue'
import ThreePointComparePage from './charts/three-point/ThreePointComparePage.vue'

const routes = [
    { path: '/', component: HomePage },
    { path: '/hexbin-classic', component: HexbinClassicPage },
    { path: '/hexbin-fullcourt', component: FullCourtHexbinPage },
    { path: '/hexbin', component: HexbinPage },
    { path: '/three-point-compare', component: ThreePointComparePage },
]

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})