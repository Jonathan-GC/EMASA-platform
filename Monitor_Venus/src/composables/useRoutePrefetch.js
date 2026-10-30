import { Capacitor } from '@capacitor/core'
import { components } from '@/plugins/router/components.js'

// Orden de precarga: primero los accesos directos del menú principal.
// Las rutas de detalle pesadas (por ejemplo, mediciones con jsPDF) se dejan
// fuera y siguen cargándose de forma lazy cuando el usuario las abre.
const PREFETCH_ORDER = [
  'DEFAULT_LAYOUT',
  'HOME',
  'NOTIFICATIONS',
  'AUDIT',
  'BACKUPS',
  'TENANTS',
  'TENANT_WORKSPACES',
  'USERS',
  'ROLES',
  'TENANT_LOCATIONS',
  'GATEWAYS',
  'DEVICE_PROFILES',
  'DEVICE_TYPES',
  'APPLICATIONS',
  'MACHINES',
  'SUPPORT',
  'INBOX',
  'SUPPORT_MEMBERS',
  'CONVERSATION'
]

const BATCH_SIZE = 3

const prefetched = new Set()
let nextIndex = 0
let started = false
let cancelled = false
let idleHandle = null

function canPrefetch() {
  // En Android/iOS los chunks son assets locales: no consumen datos móviles.
  if (Capacitor.isNativePlatform()) return true
  if (typeof navigator === 'undefined') return false

  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection
  if (!connection) return true
  if (connection.saveData) return false
  if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') return false
  return true
}

function scheduleIdle(callback) {
  if (typeof window !== 'undefined' && typeof window.requestIdleCallback === 'function') {
    return window.requestIdleCallback(callback, { timeout: 1500 })
  }
  return setTimeout(callback, 700)
}

function cancelIdle(handle) {
  if (handle == null) return
  if (typeof window !== 'undefined' && typeof window.cancelIdleCallback === 'function') {
    window.cancelIdleCallback(handle)
  } else {
    clearTimeout(handle)
  }
}

async function prefetchComponent(key) {
  if (prefetched.has(key)) return

  const factory = components[key]
  if (typeof factory !== 'function') return

  prefetched.add(key)
  try {
    await factory()
  } catch (error) {
    prefetched.delete(key)
    // No interrumpir la app: el router volverá a intentar la carga al navegar.
    console.warn(`⚠️ No se pudo precargar la ruta "${key}":`, error?.message || error)
  }
}

async function prefetchBatch() {
  if (cancelled) return

  for (let i = 0; i < BATCH_SIZE && nextIndex < PREFETCH_ORDER.length; i += 1) {
    const key = PREFETCH_ORDER[nextIndex]
    nextIndex += 1
    await prefetchComponent(key)
    if (cancelled) return
  }

  if (nextIndex < PREFETCH_ORDER.length) {
    idleHandle = scheduleIdle(prefetchBatch)
  } else {
    console.log('✅ Rutas precargadas en segundo plano')
  }
}

/**
 * Precarga en segundo plano los chunks de las rutas visibles en el menú.
 * Mantiene las rutas lazy para no aumentar el bundle inicial, pero evita
 * la espera del primer clic cuando el dispositivo está inactivo.
 */
export function useRoutePrefetch() {
  const start = () => {
    if (started) return
    started = true

    if (!canPrefetch()) {
      console.log('⏭️ Precarga de rutas omitida (ahorro de datos o conexión lenta)')
      return
    }

    cancelled = false
    idleHandle = scheduleIdle(prefetchBatch)
  }

  const stop = () => {
    cancelled = true
    started = false
    cancelIdle(idleHandle)
    idleHandle = null
  }

  return { start, stop }
}
