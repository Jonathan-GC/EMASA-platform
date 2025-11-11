import { useRouter } from 'vue-router'

/**
 * Composable para manejar la navegación de cards clickables en vistas móviles
 * Implementa el comportamiento de "toView" similar a quickActions.vue
 * 
 * Características:
 * - Navegación al hacer click en el card completo
 * - Previene navegación cuando se hace click en botones/acciones dentro del card
 * - Proporciona estilos CSS para efectos hover y active
 * - Soporte para callbacks personalizados antes de navegar
 * 
 * Uso básico:
 * ```javascript
 * import { useCardNavigation } from '@composables/useCardNavigation.js'
 * 
 * const { getCardClickHandler, getCardClass } = useCardNavigation()
 * ```
 * 
 * En el template:
 * ```vue
 * <ion-card 
 *   :class="getCardClass(true)"
 *   @click="getCardClickHandler(`/items/${item.id}`)"
 * >
 *   <!-- Card content -->
 *   <div class="card-actions">
 *     <!-- Los clicks aquí NO navegan -->
 *     <ion-button>Editar</ion-button>
 *   </div>
 * </ion-card>
 * ```
 * 
 * Estilos requeridos (agregar al componente):
 * ```css
 * .clickable-card {
 *   cursor: pointer;
 *   transition: transform 0.2s ease, box-shadow 0.2s ease;
 *   user-select: none;
 * }
 * .clickable-card:hover {
 *   transform: translateY(-2px);
 *   box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
 * }
 * .clickable-card:active {
 *   transform: translateY(0);
 *   box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
 * }
 * ```
 * 
 * @returns {Object} - { navigateToItem, getCardClickHandler, getCardStyles, getCardClass }
 */
export function useCardNavigation() {
  const router = useRouter()

  /**
   * Navega a la vista de detalle de un item
   * @param {string} route - La ruta a la que navegar (ej: '/tenants/123')
   */
  const navigateToItem = (route) => {
    if (route) {
      router.push(route)
    }
  }

  /**
   * Genera un manejador de click para un card
   * @param {string} route - La ruta a la que navegar
   * @param {Function} callback - Callback opcional a ejecutar antes de navegar
   * @returns {Function} - Función manejadora del click
   */
  const getCardClickHandler = (route, callback = null) => {
    return (event) => {
      // Prevenir navegación si se hizo click en botones/acciones dentro del card
      const clickedElement = event.target
      const isActionButton = clickedElement.closest('ion-button') || 
                            clickedElement.closest('.card-actions') ||
                            clickedElement.closest('button')
      
      if (isActionButton) {
        return // No navegar si se clickeó un botón de acción
      }

      // Ejecutar callback si existe
      if (callback && typeof callback === 'function') {
        callback(event)
      }

      // Navegar a la ruta
      navigateToItem(route)
    }
  }

  /**
   * Obtiene los estilos CSS para hacer un card clickable
   * @param {boolean} clickable - Si el card es clickable
   * @returns {Object} - Objeto de estilos CSS
   */
  const getCardStyles = (clickable = true) => {
    if (!clickable) return {}
    
    return {
      cursor: 'pointer',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    }
  }

  /**
   * Clase CSS para hover effect en cards clickables
   * @param {boolean} clickable - Si el card es clickable
   * @returns {string} - Nombre de la clase CSS
   */
  const getCardClass = (clickable = true) => {
    return clickable ? 'clickable-card' : ''
  }

  return {
    navigateToItem,
    getCardClickHandler,
    getCardStyles,
    getCardClass
  }
}
