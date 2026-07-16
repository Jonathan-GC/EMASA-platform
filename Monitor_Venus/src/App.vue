<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { IonApp, IonRouterOutlet } from '@ionic/vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { Capacitor } from '@capacitor/core'
import { App as CapApp } from '@capacitor/app'
import API from '@/utils/api/api.js'
import tokenManager from '@/utils/auth/tokenManager.js'
import { usePushNotifications } from '@composables/usePushNotifications.js'
import { useNotifications } from '@composables/useNotifications.js'

const authStore = useAuthStore()
const router = useRouter()
const { registerPush, listenForeground } = usePushNotifications()
const { showNotification } = useNotifications()

let appUrlListener = null
let removeForegroundListener = null
let appStateListener = null

async function handleAppResume() {
  const refreshToken = tokenManager.getRefreshToken()
  if (!refreshToken) return

  if (!tokenManager.hasValidToken() || tokenManager.shouldRefreshToken()) {
    console.log('🔄 App reanudada, intentando refresh silencioso...')
    try {
      const newToken = await authStore.refreshAccessToken()
      if (newToken) {
        authStore.initializeAuth()
      }
    } catch (e) {
      console.warn('⚠️ Refresh silencioso falló:', e.message)
    }
    try {
      await API.get(API.CSRF_TOKEN)
    } catch (_) {}
  }
}

function handleDeepLink(url) {
  // Native deep-link from the system browser after server-side OAuth.
  // Backend redirects to: com.mtr.online://auth/google/callback?access=...&refresh=...
  if (!url || !url.startsWith('com.mtr.online://auth/google/callback')) return
  try {
    const u = new URL(url)
    const access = u.searchParams.get('access')
    const refresh = u.searchParams.get('refresh')
    const oauthError = u.searchParams.get('error')

    if (oauthError) {
      router.replace({ name: 'login', query: { error: String(oauthError) } })
      return
    }
    if (!access) {
      router.replace({ name: 'login', query: { error: 'No access token from Google' } })
      return
    }

    const ok = authStore.login(String(access), refresh ? String(refresh) : null)
    if (!ok) {
      router.replace({ name: 'login', query: { error: 'Failed to store access token' } })
      return
    }

    authStore.fetchUserProfile().catch(() => {})

    if (authStore.needsTenantSetup) router.replace('/tenant-setup')
    else if (authStore.isSuperUser || authStore.isGlobalUser) router.replace('/tenants')
    else router.replace('/home')
  } catch (e) {
    console.error('❌ Failed to parse deep link:', e)
    router.replace({ name: 'login' })
  }
}

onMounted(async () => {
  console.log('🚀 App montada - Inicializando autenticación...')
  const isAuth = authStore.initializeAuth()

  // 🔐 Fetch CSRF token on app load (required by backend for POST/PUT/PATCH/DELETE)
  // This ensures the csrftoken cookie is set before any component makes a request.
  try {
    console.log('🔐 Fetching CSRF token on app load...')
    await API.get(API.CSRF_TOKEN)
    console.log('✅ CSRF token obtained and stored in cookies')
  } catch (error) {
    console.error('❌ Failed to fetch CSRF token on app load:', error)
    // Non-blocking: components like SignupForm / verification view have fallback
    // CSRF fetching logic, so we don't crash the app if this initial fetch fails.
  }

  // Listen for deep links on Android (when Capacitor.Browser finishes the
  // OAuth flow and redirects back to com.mtr.online://...). On iOS the
  // same listener fires via Universal Links / Custom URL Scheme.
  if (Capacitor.isNativePlatform()) {
    try {
      appUrlListener = await CapApp.addListener('appUrlOpen', ({ url }) => {
        handleDeepLink(url)
      })
    } catch (e) {
      console.warn('⚠️ Could not register appUrlOpen listener:', e)
    }

    try {
      appStateListener = await CapApp.addListener('appStateChange', ({ isActive }) => {
        if (isActive) {
          handleAppResume()
        }
      })
    } catch (e) {
      console.warn('⚠️ Could not register appStateChange listener:', e)
    }
  }
})

watch(
  () => authStore.isAuthenticated,
  async (isAuth) => {
    console.log('🔔 Auth state changed:', isAuth)
    if (isAuth) {
      try {
        const registered = await registerPush()
        console.log('🔔 registerPush result:', registered)
        if (!removeForegroundListener) {
          removeForegroundListener = await listenForeground((notification) => {
            console.log('🔔 Foreground push notification:', notification)
            showNotification(notification)
          })
        }
      } catch (e) {
        console.warn('⚠️ Push notification setup failed:', e)
      }
    }
  }
)

onBeforeUnmount(() => {
  if (appUrlListener) appUrlListener.remove()
  if (appStateListener) appStateListener.remove()
  if (removeForegroundListener) removeForegroundListener()
})
</script>