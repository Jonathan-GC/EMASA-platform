// Ionic Plugin - Main entry point
import { IonicVue } from '@ionic/vue'
import ionicConfig, { componentDefaults } from './config.js'
import { applyTheme } from './theme.js'
import { icons, getIcon } from '../icons/icons.js'

// Export icons for easy access
export { icons,  getIcon }

// Export theme utilities
export { theme, applyTheme, generateCSSVariables } from './theme.js'

// Export config
export { ionicConfig, componentDefaults } from './config.js'

/**
 * Install Ionic plugin for Vue
 * Similar to Vuetify's createVuetify()
 */
export const createIonic = (options = {}) => {
  // Merge user options with defaults
  const config = {
    ...ionicConfig,
    ...options.config,
  }
  
  return {
    install: (app) => {
      // Install IonicVue
      app.use(IonicVue, config)
      
      // Apply theme CSS variables
      if (typeof document !== 'undefined') {
        applyTheme()
      }
      
      // Provide icons globally
      app.provide('icons', icons)

      app.provide('getIcon', getIcon)
      
      // Provide theme
      app.provide('theme', options.theme || {})
      
      // Make icons available globally
      app.config.globalProperties.$icons = icons
      app.config.globalProperties.$getIcon = getIcon
    },
  }
}

// Default export
export default createIonic
