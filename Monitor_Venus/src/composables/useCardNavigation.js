import { useRouter } from 'vue-router'

/**
 * Controles que ya tienen su propio comportamiento. Un click dentro de alguno de
 * ellos no debe activar el item, además de la acción que el control ejecuta.
 * 'ion-button' cubre todos los botones de quickActions.vue (ver/editar/eliminar/
 * permisos/miembros) porque el click se retargetea al host del web component.
 */
const INTERACTIVE_SELECTOR =
  'ion-button, button, a, input, select, textarea, .card-actions'

/**
 * El usuario tiene texto seleccionado: está copiando, noNavigando.
 * @returns {boolean}
 */
const hasTextSelection = () => {
  if (typeof window === 'undefined' || typeof window.getSelection !== 'function') {
    return false
  }
  const selection = window.getSelection()
  return !!selection && !selection.isCollapsed && selection.toString().trim().length > 0
}

/**
 * El click ocurrió sobre un control interactivo dentro del item.
 * @param {EventTarget|null} target
 * @returns {boolean}
 */
const isInteractiveTarget = (target) => {
  if (!target || typeof target.closest !== 'function') return false
  return !!target.closest(INTERACTIVE_SELECTOR)
}

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
 * Activar una fila o card completa (equivalente al botón "ver"):
 * ```javascript
 * const { getItemActivateProps } = useCardNavigation()
 * ```
 * ```vue
 * <ion-row v-bind="getItemActivateProps(`/users/${user.id}`)" class="table-row-stylized">
 *   <!-- Los clicks en los botones de acción NO activan la fila -->
 * </ion-row>
 *
 * <ion-card v-bind="getItemActivateProps(null, { callback: () => openMachineModal(m.id) })">
 *   <!-- El "ver" de esta tabla abre un modal en vez de navegar -->
 * </ion-card>
 * ```
 *
 * Estilos requeridos para el foco de teclado (agregar al componente):
 * ```css
 * .table-row-stylized:focus-visible,
 * .clickable-card:focus-visible {
 *   outline: 2px solid var(--ion-color-primary);
 *   outline-offset: -2px;
 * }
 * ```
 *
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
 * @returns {Object} - { navigateToItem, getCardClickHandler, getCardStyles, getCardClass, getItemActivateProps }
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
      if (isInteractiveTarget(event?.target)) {
        return // No navegar si se clickeó un botón de acción
      }

      // Prevenir navegación si el usuario estaba seleccionando texto
      if (hasTextSelection()) {
        return
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

  /**
   * Ejecuta la acción de "ver" del item: navega a la ruta o invoca el callback.
   * @param {Event} event
   * @param {string|null} route
   * @param {Function|null} callback
   */
  const runViewAction = (event, route, callback) => {
    if (typeof callback === 'function') return callback(event)
    return navigateToItem(route)
  }

  /**
   * Genera los bindings de activación (click + teclado) para una fila o card
   * completa, de modo que interactuar con ella equivalga al botón "ver".
   *
   * A diferencia de getCardClickHandler, devuelve un objeto pensado para
   * `v-bind` e incluye accesibilidad por teclado (tabindex + role + Enter/Espacio).
   *
   * @param {string|null} route - Ruta destino. Omitirla si se usa `options.callback`.
   * @param {{callback?: Function, label?: string}} [options]
   * @returns {Object} - Bindings para `v-bind`
   *
   * @example
   * // Navegación (equivale al eye con :to-view)
   * <ion-row v-bind="getItemActivateProps(`/users/${user.id}`, { label: `Ver ${user.name}` })" />
   *
   * @example
   * // Modal (equivale al eye con :to-view="true" + @view-clicked)
   * <ion-row v-bind="getItemActivateProps(null, { callback: () => openMachineModal(machine.id) })" />
   */
  const getItemActivateProps = (route, options = {}) => {
    const { callback = null, label = null } = options

    const activate = (event) => {
      if (isInteractiveTarget(event?.target)) return
      if (hasTextSelection()) return
      return runViewAction(event, route, callback)
    }

    const handleKeydown = (event) => {
      const isEnter = event.key === 'Enter'
      const isSpace = event.key === ' ' || event.key === 'Spacebar'
      if (!isEnter && !isSpace) return

      // Se valida antes de llamar a preventDefault(): hacerlo aquí activaría
      // defaultPrevented y el guard compartido descartaría el evento.
      if (isInteractiveTarget(event.target)) return
      if (hasTextSelection()) return

      // Evita que el scroll de la página se dispare al activar con Espacio.
      event.preventDefault()
      return runViewAction(event, route, callback)
    }

    const props = {
      tabindex: '0',
      role: 'button',
      onClick: activate,
      onKeydown: handleKeydown,
    }

    if (label) {
      props['aria-label'] = label
    }

    return props
  }

  return {
    navigateToItem,
    getCardClickHandler,
    getCardStyles,
    getCardClass,
    getItemActivateProps,
  }
}
