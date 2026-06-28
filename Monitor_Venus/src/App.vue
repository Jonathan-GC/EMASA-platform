<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { IonApp, IonRouterOutlet } from '@ionic/vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { Capacitor } from '@capacitor/core'
import { App as CapApp } from '@capacitor/app'

const authStore = useAuthStore()
const router = useRouter()

let appUrlListener = null

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
  authStore.initializeAuth()

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
  }
})

onBeforeUnmount(() => {
  if (appUrlListener) appUrlListener.remove()
})
</script>