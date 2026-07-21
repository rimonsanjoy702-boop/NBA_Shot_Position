import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'echarts';
// 新增导入vue-echarts
import VChart from 'vue-echarts'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)
// 全局注册v-echarts组件
app.component('v-echarts', VChart)

app.mount('#app')
