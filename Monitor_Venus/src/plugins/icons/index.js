// Plugin principal de iconos modular
import { icons, getIcon } from './icons.js'

// Plugin de Vue (compatible con el sistema de auto-registro)
export default (app) => {
  // Registro de iconos como propiedades globales
  app.config.globalProperties.$icons = icons
  app.config.globalProperties.$icon = getIcon

  // También disponible como provide/inject para casos especiales
  app.provide('icons', icons)
  app.provide('getIcon', getIcon)
}