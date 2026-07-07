import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable para detectar el tamaño de pantalla y proporcionar
 * variables reactivas para implementar vistas responsive
 * 
 * @param {number} breakpoint - Ancho de pantalla en px para considerar móvil (default: 768)
 * @returns {Object} - { isMobile, isTablet, isDesktop, screenWidth }
 */
export function useResponsiveView(breakpoint = 768) {
  const screenWidth = ref(window.innerWidth)
  const isMobile = ref(window.innerWidth < breakpoint)
  const isTablet = ref(window.innerWidth >= breakpoint && window.innerWidth < 1024)
  const isDesktop = ref(window.innerWidth >= 1024)

  const updateScreenSize = () => {
    screenWidth.value = window.innerWidth
    isMobile.value = window.innerWidth < breakpoint
    isTablet.value = window.innerWidth >= breakpoint && window.innerWidth < 1024
    isDesktop.value = window.innerWidth >= 1024
  }

  onMounted(() => {
    window.addEventListener('resize', updateScreenSize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateScreenSize)
  })

  return {
    isMobile,
    isTablet,
    isDesktop,
    screenWidth
  }
}
