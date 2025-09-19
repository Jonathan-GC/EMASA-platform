// Plugin principal de iconos modular
import { navigationIcons } from './navigationIcons.js'
import { actionIcons } from './actionIcons.js'
import { hardwareIcons } from './hardwareIcons.js'
import { locationIcons } from './locationIcons.js'
import { uiIcons } from './uiIcons.js'
import { dataIcons } from './dataIcons.js'
import { communicationIcons } from './communicationIcons.js'
import { 
  alertCircleOutline,
  checkmarkCircleOutline,
  warningOutline,
  informationCircleOutline,
  closeCircleOutline,
  helpCircleOutline
} from 'ionicons/icons'

// Status icons
const statusIcons = {
  'alertCircle': alertCircleOutline,
  'success': checkmarkCircleOutline,
  'warning': warningOutline,
  'info': informationCircleOutline,
  'error': closeCircleOutline,
  'help': helpCircleOutline
}

// Combinar todos los iconos en un solo objeto
const allIcons = {
  ...navigationIcons,
  ...actionIcons,
  ...statusIcons,
  ...hardwareIcons,
  ...locationIcons,
  ...uiIcons,
  ...dataIcons,
  ...communicationIcons
}

// Función helper para obtener icono
const getIcon = (name) => {
  return allIcons[name] || null
}

// Plugin de Vue (compatible con el sistema de auto-registro)
export default (app) => {
  // Registro de iconos como propiedades globales
  app.config.globalProperties.$icons = allIcons
  app.config.globalProperties.$icon = getIcon
  
  // También disponible como provide/inject para casos especiales
  app.provide('icons', allIcons)
  app.provide('getIcon', getIcon)
}
