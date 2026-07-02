import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import VueECharts from 'vue-echarts'
import 'echarts'
import App from './App.vue'
import router from './router'
import './assets/styles/tokens.css'
import 'element-plus/theme-chalk/src/index.scss'
import './assets/styles/element-override.scss'
import './assets/styles/global.scss'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.component('v-chart', VueECharts)

app.mount('#app')
