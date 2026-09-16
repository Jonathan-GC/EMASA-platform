import { readonly, ref } from 'vue'
import API from '@/utils/api/api'
import { Capacitor } from '@capacitor/core'
import { useAuthStore } from '@/stores/authStore'

// URL base del plataforma de estado (Astro SSR). Si la variable de entorno no
// está definida, se usa el dev server local de Astro (puerto por defecto 4321).
const MONITOR_BASE_URL = import.meta.env.VITE_HEALTH_MONITOR_URL || 'http://localhost:4321'

const INGEST_PATH = '/api/v1/ingest/frontend'
const APP_ID = 'com.mtr.online'
const HEARTBEAT_INTERVAL = 60_000
const MAX_BACKOFF = 5 * 60_000

const isRunning = ref(false)
const lastReport = ref(null)
const lastError = ref(null)

let heartbeatTimer = null
let backoffDelay = HEARTBEAT_INTERVAL
let visibilityHandler = null

// Verifica conectividad real con el backend Atlas (/api/v1/system/health/)
const probeApi = async () => {
    const started = Date.now()
    try {
        const response = await API.get(API.SYSTEM_HEALTH, {}, { timeout: 8000 })
        const data = Array.isArray(response) ? response[0] : response
        return {
            reachable: true,
            latency_ms: Date.now() - started,
            http_status: 200,
            endpoint: API.SYSTEM_HEALTH,
            status: data?.status || 'unknown'
        }
    } catch (error) {
        return {
            reachable: false,
            latency_ms: Date.now() - started,
            http_status: null,
            endpoint: API.SYSTEM_HEALTH,
            status: 'unreachable'
        }
    }
}

const buildReport = async () => {
    const api = await probeApi()
    const authStore = useAuthStore()
    return {
        service: 'Monitor_Venus',
        version: import.meta.env.VITE_BUILD_VERSION || 'dev',
        platform: Capacitor.getPlatform(),
        app_id: APP_ID,
        api,
        auth: { authenticated: authStore.isAuthenticated },
        ts: new Date().toISOString()
    }
}

const sendReport = async () => {
    const report = await buildReport()
    const controller = new AbortController()
    const timeoutSignal = setTimeout(() => controller.abort(), 8000)
    try {
        const res = await fetch(`${MONITOR_BASE_URL}${INGEST_PATH}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(report),
            signal: controller.signal,
            keepalive: true
        })
        clearTimeout(timeoutSignal)
        lastReport.value = report
        lastError.value = null
        backoffDelay = HEARTBEAT_INTERVAL
        console.log('💓 Heartbeat enviado al monitor:', res.status)
    } catch (error) {
        clearTimeout(timeoutSignal)
        lastError.value = error?.message || String(error)
        backoffDelay = Math.min(backoffDelay * 2, MAX_BACKOFF)
        console.warn('⚠️ Heartbeat falló. Reintentando en', backoffDelay, 'ms:', error?.message)
    }
}

const run = async () => {
    if (!isRunning.value) return
    await sendReport()
    clearTimeout(heartbeatTimer)
    heartbeatTimer = setTimeout(run, backoffDelay)
}

const startHeartbeat = () => {
    if (isRunning.value) return
    isRunning.value = true
    backoffDelay = HEARTBEAT_INTERVAL
    console.log('💓 Heartbeat iniciado hacia', MONITOR_BASE_URL + INGEST_PATH)
    run()
    visibilityHandler = () => {
        if (document.visibilityState === 'visible') run()
    }
    document.addEventListener('visibilitychange', visibilityHandler)
}

const stopHeartbeat = () => {
    isRunning.value = false
    clearTimeout(heartbeatTimer)
    if (visibilityHandler) {
        document.removeEventListener('visibilitychange', visibilityHandler)
        visibilityHandler = null
    }
}

export function useHealthMonitor() {
    return {
        isRunning: readonly(isRunning),
        lastReport: readonly(lastReport),
        lastError: readonly(lastError),
        startHeartbeat,
        stopHeartbeat
    }
}