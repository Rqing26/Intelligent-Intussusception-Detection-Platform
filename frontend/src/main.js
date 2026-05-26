import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as Icons from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/theme.css'
import { initTheme } from './utils/theme'

initTheme()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
for (const [k, v] of Object.entries(Icons)) app.component(k, v)
app.mount('#app')
