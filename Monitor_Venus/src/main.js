import { createApp } from 'vue'
import { createRouter, createWebHistory } from '@ionic/vue-router'
import { createPinia } from 'pinia'
import { registerPlugins } from './plugins/plugins'
import { createIonic } from '@/plugins/ionic'
import { initTheme } from '@/composables/useTheme.js'
import App from './App.vue'

// Import Ionic CSS
import '@ionic/vue/css/core.css'
import '@ionic/vue/css/normalize.css'
import '@ionic/vue/css/structure.css'
import '@ionic/vue/css/typography.css'

// Ionic dark palette - activated by the `.ion-palette-dark` class on <html>
import '@ionic/vue/css/palettes/dark.class.css'

// Import flag-icons CSS for country flags
import 'flag-icons/css/flag-icons.min.css'

// Import Leaflet CSS
import 'leaflet/dist/leaflet.css'

// Optional: Import Ionic theme utilities
import '@ionic/vue/css/padding.css'
import '@ionic/vue/css/float-elements.css'
import '@ionic/vue/css/text-alignment.css'
import '@ionic/vue/css/text-transformation.css'
import '@ionic/vue/css/flex-utils.css'
import '@ionic/vue/css/display.css'

// Components are now auto-imported by unplugin-vue-components
// Routes are handled by the router plugin

// Apply the saved theme before anything renders (avoids a light flash)
initTheme()

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

registerPlugins(app).then(() => {
  app.mount('#app')
})
