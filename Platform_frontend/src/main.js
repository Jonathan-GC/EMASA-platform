import { createApp } from 'vue'
import { IonicVue } from '@ionic/vue'
import { createRouter, createWebHistory } from '@ionic/vue-router'
import { registerPlugins } from './plugins/plugins'
import App from './App.vue'

// Import Ionic CSS
import '@ionic/vue/css/core.css'
import '@ionic/vue/css/normalize.css'
import '@ionic/vue/css/structure.css'
import '@ionic/vue/css/typography.css'

// Optional: Import Ionic theme utilities
import '@ionic/vue/css/padding.css'
import '@ionic/vue/css/float-elements.css'
import '@ionic/vue/css/text-alignment.css'
import '@ionic/vue/css/text-transformation.css'
import '@ionic/vue/css/flex-utils.css'
import '@ionic/vue/css/display.css'

// Components are now auto-imported by unplugin-vue-components
// Routes are handled by the router plugin

// Define routes
/*
const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: Home },
  { path: '/about', component: About },
  { path: '/iot-monitor', component: MultiVoltageChart }
]

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes
})*/

const app = createApp(App)
registerPlugins(app)
app.use(IonicVue)
//app.use(router)
app.mount('#app')
