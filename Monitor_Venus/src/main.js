import { createApp } from 'vue'
import { createRouter, createWebHistory } from '@ionic/vue-router'
import { createPinia } from 'pinia'
import { registerPlugins } from './plugins/plugins'
import { createIonic } from '@/plugins/ionic'
import App from './App.vue'

// Import Ionic CSS
import '@ionic/vue/css/core.css'
import '@ionic/vue/css/normalize.css'
import '@ionic/vue/css/structure.css'
import '@ionic/vue/css/typography.css'

// Import flag-icons CSS for country flags
import 'flag-icons/css/flag-icons.min.css'

// Optional: Import Ionic theme utilities
import '@ionic/vue/css/padding.css'
import '@ionic/vue/css/float-elements.css'
import '@ionic/vue/css/text-alignment.css'
import '@ionic/vue/css/text-transformation.css'
import '@ionic/vue/css/flex-utils.css'
import '@ionic/vue/css/display.css'

// Components are now auto-imported by unplugin-vue-components
// Routes are handled by the router plugin

const app = createApp(App)

// Create Pinia instance for state management
const pinia = createPinia()
app.use(pinia)

// Use Ionic plugin with centralized configuration
app.use(createIonic({
  config: {
    mode: 'md',           // Material Design mode
    rippleEffect: true,   // Enable ripple effect
    animated: true,       // Enable animations
  }
}))

registerPlugins(app)
app.mount('#app')

// Register Service Worker for browser notifications (required for mobile)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(() => console.log('Service Worker registered'))
      .catch((error) => console.error('Service Worker registration failed:', error))
  })
}
